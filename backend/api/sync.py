import os
import requests
import math
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..database.connection import get_db
from ..database.models import SyncMetadata, CitizenMaster, Provision, District, BSKMaster
from ..utils.jwt_auth import jwt_manager  # JWT authentication manager

router = APIRouter()
logger = logging.getLogger(__name__)

# External API Configuration
EXTERNAL_SYNC_URL = os.getenv('EXTERNAL_SYNC_URL', 'https://bsk-server.gov.in/api/sync')

class SyncRequest(BaseModel):
    target_table: str
    from_date: Optional[str] = None
    force_full: bool = False

def call_external_api(target_table: str, page: int, from_date: Optional[str], flag: bool) -> Dict[str, Any]:
    """
    Call the external BSK server API with JWT authentication.
    Automatically handles token refresh on expiry.
    """
    
    # Request payload
    payload = {
        "body_params": {
            "page": page,
            "target_table": target_table
        },
        "from_date": from_date,
        "incremental": True,
        "flag": flag
    }
    
    # Get JWT token and build headers
    headers = jwt_manager.get_auth_header()
    
    try:
        logger.debug(f"Calling external API: table={target_table}, page={page}, flag={flag}")
        response = requests.post(EXTERNAL_SYNC_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        # Handle token expiry (401 Unauthorized)
        if e.response.status_code == 401:
            logger.warning("Token expired or invalid, refreshing token...")
            
            # Refresh token and retry
            headers = jwt_manager.refresh_token()
            headers = jwt_manager.get_auth_header()
            
            logger.info("Retrying with refreshed token...")
            response = requests.post(EXTERNAL_SYNC_URL, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        else:
            # Other HTTP errors
            logger.error(f"External API error: {e}")
            raise
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

def get_model_class(table_name: str):
    if table_name == "ml_citizen_master":
        return CitizenMaster
    elif table_name == "ml_provision":
        return Provision
    elif table_name == "ml_district":
        return District
    elif table_name == "ml_bsk_master":
        return BSKMaster
    else:
        raise ValueError(f"Unknown table: {table_name}")

def upsert_data(db: Session, table_name: str, data: list):
    """
    Upsert data (Insert or Update) into the database.
    """
    if not data:
        return 0, 0
        
    model = get_model_class(table_name)
    table = model.__table__
    
    # Identify primary key
    pk_col = list(table.primary_key.columns)[0]
    
    inserted = 0
    updated = 0
    
    for record in data:
        stmt = insert(table).values(record)
        
        # Prepare update dict (all columns except PK)
        update_dict = {c.name: c for c in stmt.excluded if c.name != pk_col.name}
        
        if update_dict:
            # Do update on conflict
            stmt = stmt.on_conflict_do_update(
                index_elements=[pk_col],
                set_=update_dict
            )
        else:
            # Do nothing on conflict (if no updateable columns)
            stmt = stmt.on_conflict_do_nothing(index_elements=[pk_col])
            
        result = db.execute(stmt)
        if result.rowcount > 0:
            if result.rowcount == 1: # Could be insert or update depending on dialect return
                 updated += 1 # Approximation
        
    db.commit()
    return len(data), len(data) # Simply returning processed count

@router.post("/sync")
async def sync_data(request: SyncRequest, db: Session = Depends(get_db)):
    """
    Sync data from external server to local PostgreSQL.
    """
    try:
        # 1. Get last sync metadata
        metadata = db.query(SyncMetadata).filter(SyncMetadata.table_name == request.target_table).first()
        
        from_date = request.from_date
        if not from_date and metadata and not request.force_full:
            from_date = str(metadata.last_sync_from_date)
            
        logger.info(f"Starting sync for {request.target_table} from {from_date}")
        
        # 2. First Call - Get Total Count
        first_resp = call_external_api(
            target_table=request.target_table,
            page=1,
            from_date=from_date,
            flag=True
        )
        
        total_records = first_resp.get("total_count", 0)
        PAGE_SIZE = 10000
        max_pages = math.ceil(total_records / PAGE_SIZE) if total_records > 0 else 0
        
        logger.info(f"Total records to sync: {total_records} ({max_pages} pages)")
        
        total_upserted = 0
        
        # 3. Fetch Pages
        for page in range(1, max_pages + 1):
            logger.info(f"Fetching page {page}/{max_pages}...")
            resp = call_external_api(
                target_table=request.target_table,
                page=page,
                from_date=from_date,
                flag=False
            )
            
            page_data = resp.get("data", [])
            
            # 4. Upsert Data
            if page_data:
                upsert_data(db, request.target_table, page_data)
                total_upserted += len(page_data)
                
        # 5. Update Metadata
        if not metadata:
            metadata = SyncMetadata(table_name=request.target_table)
            db.add(metadata)
        
        metadata.last_sync_timestamp = datetime.now()
        metadata.last_sync_from_date = datetime.now().date() # Next sync from today
        metadata.total_records = total_upserted
        metadata.last_sync_status = "SUCCESS"
        
        db.commit()
        
        return {
            "status": "success",
            "table": request.target_table,
            "total_records_processed": total_upserted,
            "pages_processed": max_pages,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
