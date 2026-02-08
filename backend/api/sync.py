import os
import requests
import math
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import BigInteger, Integer, Float, Numeric, Date, Boolean, String, Text
from sqlalchemy import insert, update, select, and_, or_, tuple_
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ..database.connection import get_db
from ..database.models import SyncMetadata, CitizenMaster, Provision, District, BSKMaster, Service, ServiceEligibility
from ..utils.jwt_auth import jwt_manager

# Initialize Router and Logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Configuration
EXTERNAL_SYNC_BASE_URL = os.getenv("EXTERNAL_SYNC_URL", "https://bsk.wb.gov.in/aiapi/api/sync")
SYNC_PAGE_SIZE = int(os.getenv("SYNC_PAGE_SIZE", "1000"))

# Request Model
class SyncRequest(BaseModel):
    target_table: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    force_full: bool = False

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def call_sync_api(url_suffix: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to make authenticated POST requests to the sync API"""
    if url_suffix.startswith("/"):
        url_suffix = url_suffix[1:]
        
    url = f"{EXTERNAL_SYNC_BASE_URL}/{url_suffix}"
    headers = jwt_manager.get_auth_header()
    session = jwt_manager.session
    
    try:
        logger.debug(f"Calling External Sync API: {url} | Payload: {payload}")
        response = session.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.warning("Token expired during sync call, refreshing...")
            jwt_manager.refresh_token()
            headers = jwt_manager.get_auth_header()
            response = session.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        raise
    except Exception as e:
        logger.error(f"Sync API call failed: {e}")
        raise

def get_model_class(table_name: str):
    """Map external table identifiers to SQLAlchemy models."""
    if table_name == "citizen_master": return CitizenMaster
    elif table_name == "provision": return Provision
    elif table_name == "district": return District
    elif table_name == "bsk_master": return BSKMaster
    elif table_name == "service_master": return Service
    elif table_name == "services_eligibility": return ServiceEligibility
    
    elif table_name == "ml_citizen_master": return CitizenMaster
    elif table_name == "ml_provision": return Provision
    elif table_name == "ml_district": return District
    elif table_name == "ml_bsk_master": return BSKMaster
    elif table_name == "services": return Service
    
    else:
        raise ValueError(f"Unknown table or no model defined: {table_name}")

def sanitize_data(table, data):
    """
    Sanitize data before insertion/update.
    Converts empty strings to None for non-string columns.
    """
    sanitized_data = []
    for record in data:
        clean_record = {}
        for k, v in record.items():
            if k not in table.columns:
                continue

            # Data Sanitization Logic
            if v == "":
                try:
                    col_type = table.columns[k].type
                    
                    # Check if it's a numeric or other non-string type
                    is_string_type = isinstance(col_type, (String, Text))
                    if not is_string_type:
                        # Fallback for wrapped types
                        try:
                            if issubclass(col_type.python_type, str):
                                is_string_type = True
                        except:
                            pass
                    
                    if not is_string_type:
                        v = None
                except Exception:
                    pass
            
            clean_record[k] = v
        
        if clean_record:
            sanitized_data.append(clean_record)
            
    return sanitized_data

def manual_upsert(db: Session, table, pk_cols, data):
    """
    Performs Manual Upsert:
    1. Identify existing records by PK (supports Composite Keys).
    2. Split into Inserts (New) and Updates (Existing).
    3. Execute bulk operations.
    Needed when DB lacks UNIQUE constraints required for ON CONFLICT.
    """
    if not data:
        return 0

    # Handle Composite keys correctly
    pk_columns = [table.columns[k] for k in pk_cols]
    
    # helper for composite key tuple creation
    def make_key(item):
        return tuple(item.get(k) for k in pk_cols)

    incoming_keys = [make_key(item) for item in data]
    
    if not incoming_keys:
        return 0

    existing_keys = set()
    chunk_size = 500
    
    # Process chunks to query existing keys
    for i in range(0, len(incoming_keys), chunk_size):
        chunk = incoming_keys[i:i + chunk_size]
        
        # Build query for composite or single keys
        if len(pk_cols) == 1:
            # Single PK Optimization
            pk_col = pk_columns[0]
            # Unwrap tuples for single column IN clause
            keys_for_query = [k[0] for k in chunk]
            stmt = select(pk_col).where(pk_col.in_(keys_for_query))
            result = db.execute(stmt).scalars().all()
            # Wrap back to tuple for consistency
            existing_keys.update((r,) for r in result)
        else:
            # Composite Key requires tuple_ logic or AND/OR construction
            # SQLAlchemy tuple_ support varies by backend/version, so using explicit OR is safer but verbose.
            # However, for PG + SQLAlchemy tuple_ usually works.
            # Using tuple_ for clarity and standard support in modern SA/PG
            
            stmt = select(*pk_columns).where(tuple_(*pk_columns).in_(chunk))
            result = db.execute(stmt).all()
            existing_keys.update(result) # result is already tuples of values
        
    to_insert = []
    to_update = []
    
    for item in data:
        key = make_key(item)
        if key in existing_keys:
            to_update.append(item)
        else:
            to_insert.append(item)
            
    # Bulk Insert
    if to_insert:
        db.execute(insert(table), to_insert)
        
    # Bulk Update
    if to_update:
        # For updates, we need to bind parameters correctly.
        # SQLAlchemy Core 'update' with list of dicts requires the WHERE clause to match solely based on PKs in the dict.
        # Standard approach: execute scalar updates based on PK if generic bulk update is tricky with composite keys in partial support.
        # But Postgres + SQLA 1.4+ supports this usually via executemany.
        
        # Fallback to per-row update for maximum safety if bulk update proves fragile with missing constraints?
        # No, let's try mappings. 
        # Crucial: The dicts in `to_update` MUST contain the PKs for the UPDATE statement to find the row.
        # And they do, because they are the full records.
        
        db.execute(update(table), to_update)

    return len(data)

def upsert_data(db: Session, table_name: str, data: list):
    """
    Upsert data into the database.
    """
    if not data:
        return 0
        
    try:
        model = get_model_class(table_name)
        table = model.__table__
        pk_cols = [c.name for c in table.primary_key.columns]
        
        if not pk_cols:
             raise ValueError(f"Table {table_name} has no primary key defined.")
             
        # Normalize/Sanitize Data first
        clean_data = sanitize_data(table, data)
        if not clean_data:
            return 0

        upserted_count = 0

        # --- SPECIAL HANDLING FOR PROVISION (PURE INSERT) ---
        if table_name in ["ml_provision", "provision"]:
            logger.info(f"Using Pure Insert for {table_name}")
            db.execute(insert(table), clean_data)
            db.commit()
            return len(clean_data)

        # --- MANUAL UPSERT FOR MASTER TABLES (Missing Constraints) ---
        # User confirmed to check first then update for citizen_master
        # Assuming Master Tables might lack constraints, Manual Upsert is safer
        # Explicit list of tables known or suspected to lack constraints
        manual_upsert_tables = [
             "ml_citizen_master", "citizen_master", 
             "ml_bsk_master", "bsk_master", 
             "ml_district", "district",
             "ml_service_master", "service_master", "services"
        ]
        
        if table_name in manual_upsert_tables:
            logger.info(f"Using Manual Upsert for {table_name} on PK: {pk_cols}")
            total = manual_upsert(db, table, pk_cols, clean_data)
            db.commit()
            return total

        # --- FALLBACK: STANDARD POSTGRESQL UPSERT ---
        logger.info(f"Using Standard Upsert for {table_name}")
        stmt = insert(table).values(clean_data)
        update_dict = {c.name: c for c in stmt.excluded if c.name not in pk_cols}
        
        if update_dict:
            stmt = stmt.on_conflict_do_update(index_elements=pk_cols, set_=update_dict)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
            
        db.execute(stmt)
        db.commit()
        return len(clean_data)

    except Exception as e:
        db.rollback()
        logger.error(f"Upsert failed for {table_name}: {e}")
        raise

def sync_table_paginated(db: Session, table_name: str, start_date: str, end_date: str):
    """
    Standard Sync Strategy: Meta Check -> Pagination Loop
    Applies to ALL tables.
    """
    logger.info(f"🔄 Syncing Table: {table_name} ({start_date} to {end_date})")
    
    meta_payload = {"start_date": start_date, "end_date": end_date}
    meta_response = call_sync_api(table_name, meta_payload)
    
    total_records = meta_response.get("total_no_of_records", 0)
    logger.info(f"📊 Meta Check [{table_name}]: Found {total_records} records.")
    
    if total_records == 0:
        return 0
    
    total_upserted = 0
    page_size = SYNC_PAGE_SIZE
    max_pages = math.ceil(total_records / page_size)
    
    logger.info(f"   Splitting into {max_pages} pages of size {page_size}")
    
    for page in range(1, max_pages + 1):
        logger.info(f"   Downloading page {page}/{max_pages}...")
        
        page_payload = {
            "start_date": start_date,
            "end_date": end_date,
            "Page": page,
            "Pagesize": page_size
        }
        
        page_response = call_sync_api(table_name, page_payload)
        records = page_response.get("records", [])
        
        if records:
            upsert_data(db, table_name, records)
            total_upserted += len(records)
            
    return total_upserted

# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@router.post("/sync")
async def sync_data(request: SyncRequest, db: Session = Depends(get_db)):
    """
    Sync data from external server to local PostgreSQL.
    """
    target_table = request.target_table
    external_table_name = target_table.replace("ml_", "") if target_table.startswith("ml_") else target_table
    if target_table == "services": external_table_name = "service_master"

    today_str = datetime.now().strftime("%Y-%m-%d")
    end_date = request.end_date if request.end_date else today_str
    from_date = request.start_date
    
    metadata = db.query(SyncMetadata).filter(SyncMetadata.table_name == target_table).first()
    
    if not from_date and metadata and not request.force_full:
        from_date = str(metadata.last_sync_from_date)
    
    if not from_date:
        from_date = "2024-01-01" 
    
    try:
        total_processed = sync_table_paginated(db, external_table_name, from_date, end_date)
            
        if not metadata:
            metadata = SyncMetadata(table_name=target_table)
            db.add(metadata)
        
        metadata.last_sync_timestamp = datetime.now()
        metadata.last_sync_from_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        metadata.total_records = total_processed
        metadata.last_sync_status = "SUCCESS"
        db.commit()
        
        return {
            "status": "success", 
            "table": target_table,
            "external_table": external_table_name,
            "total_records_processed": total_processed,
            "date_range": {"start": from_date, "end": end_date}
        }

    except Exception as e:
        logger.error(f"Sync failed for {target_table}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-auth")
def test_auth_token():
    try:
        logger.info("🔧 Manual Auth Test Triggered")
        token = jwt_manager.login()
        return {
            "status": "success", 
            "message": "Authentication successful",
            "token_preview": f"{token[:15]}...",
            "expires_at": jwt_manager.token_expiry,
            "login_url": jwt_manager.login_url
        }
    except Exception as e:
        logger.error(f"Auth Test Failed: {e}")
        return {
            "status": "failed", 
            "error": str(e),
            "login_url": jwt_manager.login_url
        }

@router.post("/test-sync-fetch/{table_name}")
def test_sync_fetch(table_name: str, payload: Dict[str, Any]):
    try:
        logger.info(f"🔧 Manual Fetch Test: {table_name} | Payload: {payload}")
        headers = jwt_manager.get_auth_header()
        url = f"{EXTERNAL_SYNC_BASE_URL}/{table_name}"
        session = jwt_manager.session 
        response = session.post(url, json=payload, headers=headers, timeout=60)
        return {
            "status": "success" if response.ok else "error",
            "status_code": response.status_code,
            "url": url,
            "response_data": response.json() if response.content else response.text
        }
    except Exception as e:
        logger.error(f"Fetch Test Failed: {e}")
        return {"status": "failed", "error": str(e)}
