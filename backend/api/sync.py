import os
import requests
import math
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import BigInteger, Integer, Float, Numeric, Date, Boolean, String, Text
from sqlalchemy import insert, update, select, and_, or_, tuple_, text
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

# ──────────────────────────────────────────────────────────────────────────────
# API PATTERN CLASSIFICATION (verified via exhaustive endpoint testing)
#
# PATTERN A – "Dump-All" tables:
#   API returns ALL records in a single call regardless of parameters.
#   Dates, Page, Pagesize are ALL IGNORED by the external API.
#   Response: {success, table_name, total_records, records: [...]}
#   Strategy: TRUNCATE existing data + INSERT all records atomically.
#
# PATTERN B – "Paginated" tables:
#   Step 1 (Meta):  POST {start_date, end_date}
#       → {success, flow:"meta", table_name, total_no_of_records, date_range}
#   Step 2 (Pages): POST {start_date, end_date, Page:N, Pagesize:M}
#       → {success, flow:"pagination", table_name, Page, Pagesize, records:[...]}
#   End condition: len(records) == 0  (citizen_master has no "fetched" field)
#   Strategy: UPSERT (citizen_master) or INSERT (provision) per page.
# ──────────────────────────────────────────────────────────────────────────────
DIRECT_TABLES = {"bsk_master", "service_master", "district"}
PAGINATED_TABLES = {"provision", "citizen_master"}
# Also available from API but NOT synced (no DB models yet):
# "deo_master" (7,047 records), "block-municipality" (482 records)
ALL_SYNCABLE_TABLES = DIRECT_TABLES | PAGINATED_TABLES

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
    - Converts empty strings to None for non-string columns
    - Attempts type coercion for string numbers
    """
    sanitized_data = []
    for record in data:
        clean_record = {}
        for k, v in record.items():
            if k not in table.columns:
                continue

            col_type = table.columns[k].type
            
            # Check if column is string type
            is_string_type = isinstance(col_type, (String, Text))
            if not is_string_type:
                try:
                    if issubclass(col_type.python_type, str):
                        is_string_type = True
                except:
                    pass
            
            # Data Sanitization Logic
            if v == "":
                # Empty string handling
                if not is_string_type:
                    v = None
            elif isinstance(v, str) and not is_string_type:
                # Type coercion for string numbers
                try:
                    if isinstance(col_type, (BigInteger, Integer)):
                        v = int(v)
                    elif isinstance(col_type, Float):
                        v = float(v)
                    elif isinstance(col_type, Boolean):
                        # Handle boolean strings
                        if v.lower() in ('true', '1', 'yes'):
                            v = True
                        elif v.lower() in ('false', '0', 'no'):
                            v = False
                        else:
                            v = None
                except (ValueError, AttributeError):
                    # Let database handle invalid values
                    pass
            
            clean_record[k] = v
        
        if clean_record:
            sanitized_data.append(clean_record)
            
    return sanitized_data

def insert_only(db: Session, table, data):
    """
    INSERT ONLY (no TRUNCATE) - for paginated data streaming.
    Used after table has already been truncated.
    """
    if not data:
        return 0
    
    insert_success = 0
    insert_failed = 0
    
    for record in data:
        savepoint = db.begin_nested()
        try:
            db.execute(insert(table).values(record))
            db.flush()
            savepoint.commit()
            insert_success += 1
        except Exception as e:
            savepoint.rollback()
            insert_failed += 1
            logger.error(f"Failed to insert record: {str(e)[:200]}")
    
    if insert_failed > 0:
        logger.warning(f"⚠️  {insert_failed}/{len(data)} inserts failed")
    
    return insert_success

def manual_upsert(db: Session, model, table, pk_cols, data):
    """
    Performs Manual Upsert with ROW-LEVEL FAULT TOLERANCE:
    1. Identify existing records by PK (supports Composite Keys).
    2. Split into Inserts (New) and Updates (Existing).
    3. Execute operations with per-record error handling using SAVEPOINTS.
    If one record fails, others continue processing.
    """
    if not data:
        return 0

    # Handle Composite keys correctly
    pk_columns = [table.columns[k] for k in pk_cols]
    
    # helper for composite key tuple creation with NULL validation
    def make_key(item):
        key = tuple(item.get(k) for k in pk_cols)
        # CRITICAL: Reject records with NULL in primary key
        if None in key:
            key_dict = dict(zip(pk_cols, key))
            raise ValueError(f"NULL value in primary key: {key_dict}")
        return key

    incoming_keys = []
    invalid_records = 0
    
    for item in data:
        try:
            incoming_keys.append(make_key(item))
        except ValueError as e:
            invalid_records += 1
            logger.warning(f"Skipping invalid record: {e}")
    
    if invalid_records > 0:
        logger.warning(f"Skipped {invalid_records} records with invalid/NULL primary keys")
    
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
            existing_keys.update((r,) for r in result)
        else:
            stmt = select(*pk_columns).where(tuple_(*pk_columns).in_(chunk))
            result = db.execute(stmt).all()
            existing_keys.update(result)
        
    to_insert = []
    to_update = []
    
    # Filter data to only valid records (those with valid keys)
    for item in data:
        try:
            key = make_key(item)
            if key in existing_keys:
                to_update.append(item)
            else:
                to_insert.append(item)
        except ValueError:
            # Already logged above, skip
            pass
    
    # Track success/failure counts
    insert_success = 0
    insert_failed = 0
    update_success = 0
    update_failed = 0
    
    # ROW-LEVEL FAULT TOLERANCE: Insert with SAVEPOINTS
    if to_insert:
        logger.info(f"   - Inserting {len(to_insert)} new records...")
        for record in to_insert:
            # Create savepoint for this record
            savepoint = db.begin_nested()
            try:
                db.execute(insert(table).values(record))
                db.flush()  # Flush to detect errors immediately
                savepoint.commit()  # Commit savepoint (keeps this record)
                insert_success += 1
            except Exception as e:
                savepoint.rollback()  # Rollback ONLY this savepoint
                insert_failed += 1
                pk_val = {k: record.get(k) for k in pk_cols}
                logger.error(f"Failed to insert record {pk_val}: {str(e)[:200]}")
        
        if insert_failed > 0:
            logger.warning(f"⚠️ {insert_failed}/{len(to_insert)} inserts failed")
    
    # ROW-LEVEL FAULT TOLERANCE: Update with SAVEPOINTS
    if to_update:
        logger.info(f"   - Updating {len(to_update)} existing records...")
        for record in to_update:
            # Create savepoint for this record
            savepoint = db.begin_nested()
            try:
                # CRITICAL: Validate complete PK exists (prevent partial key updates)
                pk_filter = {}
                for k in pk_cols:
                    if k not in record:
                        raise ValueError(f"Missing primary key column '{k}' in update record")
                    pk_filter[k] = record[k]
                
                update_data = {k: v for k, v in record.items() if k not in pk_cols}
                
                if not update_data:
                    # Record has only PK columns, nothing to update
                    # This is valid - commit as successful no-op
                    savepoint.commit()
                    update_success += 1
                else:
                    # Perform actual update
                    stmt = update(table).where(
                        *[table.columns[k] == pk_filter[k] for k in pk_cols]
                    ).values(**update_data)
                    db.execute(stmt)
                    db.flush()
                    savepoint.commit()  # Commit savepoint (keeps this record)
                    update_success += 1
            except Exception as e:
                savepoint.rollback()  # Rollback ONLY this savepoint
                update_failed += 1
                pk_val = {k: record.get(k) for k in pk_cols}
                logger.error(f"Failed to update record {pk_val}: {str(e)[:200]}")
        
        if update_failed > 0:
            logger.warning(f"⚠️ {update_failed}/{len(to_update)} updates failed")
    
    # Log final summary
    total_success = insert_success + update_success
    total_failed = insert_failed + update_failed
    
    if total_failed > 0:
        logger.warning(f"📊 Sync Summary: {total_success} succeeded, {total_failed} failed")
    
    return total_success

def upsert_data(db: Session, table_name: str, data: list, skip_commit: bool = False):
    """
    Upsert data into the database.
    Strategy varies by table type:
    - citizen_master: Manual UPSERT (check + insert/update)
    - bsk_master, district, service_master: INSERT ONLY (used after TRUNCATE)
    - provision: Pure INSERT (no checking, preserve historical data)
    - Other tables: Pure INSERT
    
    Args:
        skip_commit: If True, don't commit (caller manages transaction)
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
            if len(data) > 0:
                logger.warning(f"🚨 All {len(data)} records filtered out during sanitization for {table_name}")
            return 0

        # --- STRATEGY 1: MANUAL UPSERT (citizen_master only) ---
        if table_name in ["ml_citizen_master", "citizen_master"]:
            logger.info(f"Using Manual Upsert for {table_name} on PK: {pk_cols}")
            total = manual_upsert(db, model, table, pk_cols, clean_data)
            if not skip_commit:
                db.commit()
            return total

        # --- STRATEGY 2: INSERT ONLY (for master tables after TRUNCATE) ---
        if table_name in ["bsk_master", "ml_bsk_master", "district", "ml_district", 
                          "service_master", "services"]:
            # TRUNCATE is done in sync_table_paginated, this just INSERTs
            total = insert_only(db, table, clean_data)
            if not skip_commit:
                db.commit()
            return total

        # --- STRATEGY 3: PURE INSERT (all other tables) ---
        logger.info(f"Using Pure Insert for {table_name}")
        
        # Use row-level fault tolerance with pure inserts
        insert_success = 0
        insert_failed = 0
        
        for record in clean_data:
            savepoint = db.begin_nested()
            try:
                db.execute(insert(table).values(record))
                db.flush()
                savepoint.commit()
                insert_success += 1
            except Exception as e:
                savepoint.rollback()
                insert_failed += 1
                # Log PK values for debugging
                pk_vals = {k: record.get(k) for k in pk_cols}
                logger.error(f"Failed to insert {table_name} record {pk_vals}: {str(e)[:200]}")
        
        if insert_failed > 0:
            logger.warning(f"⚠️  {insert_failed}/{len(clean_data)} inserts failed for {table_name}")
        
        # FIX #4: Respect skip_commit parameter
        if not skip_commit:
            db.commit()
        return insert_success

    except Exception as e:
        db.rollback()
        logger.error(f"Upsert failed for {table_name}: {e}")
        raise

def sync_table_paginated(db: Session, table_name: str, start_date: str, end_date: str):
    """
    Sync data from external BSK API. Handles TWO verified API response patterns:
    
    PATTERN A - Direct "Dump-All" (bsk_master, district, service_master, deo_master, block-municipality):
      - API ignores ALL parameters (dates, Page, Pagesize).
      - Always returns ALL records in a single response.
      - Response: {success, table_name, total_records, records: [...]}
      - Strategy: TRUNCATE + INSERT atomically.
    
    PATTERN B - Paginated (provision, citizen_master):
      - Requires start_date & end_date (400 error without them).
      - Meta call (dates only)  → {flow:"meta", total_no_of_records: N}
      - Page call (dates+Page+Pagesize) → {flow:"pagination", records: [...]}
      - End condition: len(records) == 0
      - Strategy: INSERT (provision) or UPSERT (citizen_master) per page.
    """
    
    # =========================================================================
    # PATTERN A: Direct "Dump-All" tables
    # =========================================================================
    if table_name in DIRECT_TABLES:
        logger.info(f"🔄 Syncing Direct Table: {table_name} (Pattern A — all records in one call)")
        
        # Send empty payload — API ignores all parameters anyway
        response = call_sync_api(table_name, {})
        records = response.get("records", [])
        
        if not records:
            logger.warning(f"⚠️  {table_name}: API returned 0 records!")
            return 0
        
        logger.info(f"📦 {table_name}: received {len(records)} records")
        
        # Atomic TRUNCATE + INSERT with advisory lock
        model = get_model_class(table_name)
        table = model.__table__
        lock_id = hash(table.name) % 2147483647
        
        logger.info(f"   🔒 Acquiring advisory lock for {table.name}...")
        db.execute(text(f"SELECT pg_advisory_lock({lock_id})"))
        
        try:
            truncate_savepoint = db.begin_nested()
            try:
                logger.info(f"   🗑️  TRUNCATE {table.name}...")
                db.execute(table.delete())
                db.flush()
                
                total_inserted = upsert_data(db, table_name, records, skip_commit=True)
                truncate_savepoint.commit()
                
                logger.info(f"   ✅ {table.name}: {total_inserted}/{len(records)} records replaced")
                return total_inserted
            except Exception as e:
                truncate_savepoint.rollback()
                logger.error(f"   ❌ TRUNCATE + INSERT failed for {table.name}: {e}")
                raise
        finally:
            db.execute(text(f"SELECT pg_advisory_unlock({lock_id})"))
            logger.info(f"   🔓 Released lock for {table.name}")
    
    # =========================================================================
    # PATTERN B: Paginated tables (provision, citizen_master)
    # =========================================================================
    elif table_name in PAGINATED_TABLES:
        logger.info(f"🔄 Syncing Paginated Table: {table_name} ({start_date} → {end_date})")
        
        # Step 1: Meta call — get total record count
        meta_payload = {"start_date": start_date, "end_date": end_date}
        meta_response = call_sync_api(table_name, meta_payload)
        
        flow = meta_response.get("flow", "")
        if flow != "meta":
            logger.error(f"❌ Expected 'meta' flow for {table_name}, got '{flow}'. Response: {list(meta_response.keys())}")
            raise ValueError(f"Unexpected API response for {table_name}: flow={flow}")
        
        total_records = meta_response.get("total_no_of_records", 0)
        if not isinstance(total_records, int) or total_records < 0:
            logger.warning(f"Invalid total_no_of_records: {total_records}, defaulting to 0")
            total_records = 0
        
        logger.info(f"📊 {table_name} meta: {total_records} records in [{start_date} → {end_date}]")
        
        if total_records == 0:
            logger.info(f"   ℹ️  No records for {table_name} in this date range")
            return 0
        
        # Step 2: Paginate through all records
        page_size = SYNC_PAGE_SIZE
        max_pages = math.ceil(total_records / page_size)
        logger.info(f"   📄 Paginating: ~{max_pages} pages × {page_size} per page")
        
        total_upserted = 0
        consecutive_empty = 0
        MAX_CONSECUTIVE_EMPTY = 3  # Safety: stop after 3 consecutive empty pages
        
        for page in range(1, max_pages + 2):  # +2 for safety margin
            logger.info(f"   📥 Page {page}/{max_pages}...")
            
            page_payload = {
                "start_date": start_date,
                "end_date": end_date,
                "Page": page,
                "Pagesize": page_size
            }
            
            page_response = call_sync_api(table_name, page_payload)
            records = page_response.get("records", [])
            
            if not records or len(records) == 0:
                consecutive_empty += 1
                logger.info(f"      ⚠️  Empty page {page} ({consecutive_empty}/{MAX_CONSECUTIVE_EMPTY})")
                if consecutive_empty >= MAX_CONSECUTIVE_EMPTY:
                    logger.info(f"   🏁 {MAX_CONSECUTIVE_EMPTY} consecutive empty pages — pagination complete")
                    break
                continue
            
            consecutive_empty = 0  # Reset on non-empty page
            inserted_count = upsert_data(db, table_name, records)
            total_upserted += inserted_count
            logger.info(f"      ✅ {inserted_count} records (Total: {total_upserted}/{total_records})")
            
            # Natural end: got fewer records than page size
            if len(records) < page_size:
                logger.info(f"   🏁 Last page (got {len(records)} < {page_size}) — pagination complete")
                break
        
        logger.info(f"📊 {table_name} DONE: {total_upserted}/{total_records} records synced")
        return total_upserted
    
    # =========================================================================
    # UNKNOWN TABLE
    # =========================================================================
    else:
        logger.error(f"❌ Unknown table '{table_name}' — not in DIRECT_TABLES or PAGINATED_TABLES")
        raise ValueError(f"Unknown sync table: {table_name}. Valid tables: {ALL_SYNCABLE_TABLES}")

# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@router.post("/sync")
async def sync_data(request: SyncRequest, db: Session = Depends(get_db)):
    """
    Sync data from external server to local PostgreSQL.
    
    Pattern A tables (bsk_master, district, service_master):
      Dates are irrelevant — API always returns all records.
      TRUNCATE + INSERT atomically.
    
    Pattern B tables (provision, citizen_master):
      Require valid start_date and end_date.
      Uses meta call → paginated fetch → UPSERT/INSERT per page.
    """
    target_table = request.target_table
    external_table_name = target_table.replace("ml_", "") if target_table.startswith("ml_") else target_table
    if target_table == "services": external_table_name = "service_master"

    # Validate table name
    if external_table_name not in ALL_SYNCABLE_TABLES:
        raise HTTPException(status_code=400, detail=f"Unknown table: {external_table_name}. Valid: {sorted(ALL_SYNCABLE_TABLES)}")

    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # ── Date logic depends on API pattern ──
    if external_table_name in DIRECT_TABLES:
        # Pattern A: Dates are irrelevant (API ignores them)
        from_date = "N/A"
        end_date = "N/A"
        logger.info(f"📋 Direct table ({external_table_name}) — dates ignored, fetching all records")
    else:
        # Pattern B: Dates are REQUIRED
        end_date = request.end_date if request.end_date else today_str
        from_date = request.start_date
        
        metadata = db.query(SyncMetadata).filter(SyncMetadata.table_name == target_table).first()
        
        if not from_date and metadata and not request.force_full:
            from_date = str(metadata.last_sync_from_date)
        
        if not from_date:
            from_date = "2024-01-01"
        
        logger.info(f"📋 Paginated table ({external_table_name}) — date range: {from_date} → {end_date}")
    
    try:
        total_processed = sync_table_paginated(db, external_table_name, from_date, end_date)
        
        metadata = db.query(SyncMetadata).filter(SyncMetadata.table_name == target_table).first()
        if not metadata:
            metadata = SyncMetadata(table_name=target_table)
            db.add(metadata)
        
        metadata.last_sync_timestamp = datetime.now()
        metadata.total_records = total_processed
        metadata.last_sync_status = "SUCCESS"
        
        # Only update last_sync_from_date for paginated tables
        if external_table_name in PAGINATED_TABLES:
            metadata.last_sync_from_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        db.commit()
        
        return {
            "status": "success", 
            "table": target_table,
            "external_table": external_table_name,
            "pattern": "A-direct" if external_table_name in DIRECT_TABLES else "B-paginated",
            "total_records_processed": total_processed,
            "date_range": {"start": from_date, "end": end_date}
        }

    except Exception as e:
        # Update metadata to track failure
        try:
            metadata = db.query(SyncMetadata).filter(SyncMetadata.table_name == target_table).first()
            if metadata:
                metadata.last_sync_status = "FAILED"
                metadata.last_sync_timestamp = datetime.now()
                db.commit()
        except:
            db.rollback()
        
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
