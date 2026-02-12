from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import sync, generate, recommend
from .database.connection import engine
from .scheduler import start_scheduler, shutdown_scheduler
from sqlalchemy import text, inspect
import uvicorn
import os
import fcntl
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BSK-SER PostgreSQL Backend", version="2.0")

# CORS Configuration
# Get allowed origins from environment (comma-separated list)
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event - Database Verification
@app.on_event("startup")
async def verify_database():
    """Verify database connection and tables on every startup/reload (runs once across all workers)"""
    
    # ── Single-instance guard (same pattern as scheduler) ──
    lock_file = "/tmp/bsk_db_verify.lock"
    try:
        # Use O_CREAT | O_RDWR to avoid truncation race condition
        _fd = os.open(lock_file, os.O_CREAT | os.O_RDWR, 0o644)
        _verify_lock = os.fdopen(_fd, 'r+')
        fcntl.flock(_verify_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _verify_lock.seek(0)
        _verify_lock.truncate()
        _verify_lock.write(str(os.getpid()))
        _verify_lock.flush()
    except (IOError, OSError):
        # Another worker already running verification - skip silently
        logger.info(f"⏭️  DB verification already running on another worker - skipping (PID: {os.getpid()})")
        # Still start scheduler (it has its own lock)
        try:
            start_scheduler()
        except Exception as e:
            logger.error(f"❌ Scheduler startup failed: {e}")
        return
    
    logger.info("="*70)
    logger.info("🔍 BSK-SER STARTUP VERIFICATION")
    logger.info("="*70)
    
    # Required tables
    required_tables = [
        'ml_citizen_master',
        'ml_provision',
        'ml_bsk_master',
        'ml_district',
        'services',
        'services_eligibility',
        'grouped_df',
        'district_top_services',
        'block_wise_top_services',
        'openai_similarity_matrix'
    ]
    
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL connection successful")
        
        # Check tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"\n📊 Database Tables ({len(existing_tables)} total):")
        logger.info("-"*70)
        
        all_present = True
        total_rows = 0
        
        with engine.connect() as conn:
            for table in required_tables:
                if table in existing_tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        total_rows += count
                        status = "✅" if count > 0 else "⚠️ "
                        logger.info(f"{status} {table:35s} : {count:>12,} rows")
                        if count == 0:
                            all_present = False
                    except Exception as e:
                        logger.error(f"❌ {table:35s} : ERROR - {str(e)[:50]}")
                        all_present = False
                else:
                    logger.error(f"❌ {table:35s} : MISSING")
                    all_present = False
        
        logger.info("-"*70)
        logger.info(f"Total Rows: {total_rows:,}")
        logger.info("-"*70)
        
        if all_present:
            logger.info("✅ All tables verified - System ready!")
        else:
            logger.warning("⚠️  Some tables missing or empty - Check database")
            
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        logger.warning("⚠️  Server starting anyway - Fix database issues")
    
    logger.info("="*70)
    
    # Release verification lock (one-time check, not persistent)
    try:
        fcntl.flock(_verify_lock, fcntl.LOCK_UN)
        _verify_lock.close()
        os.remove(lock_file)
    except Exception:
        pass
    
    # Start the automated sync scheduler
    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"❌ Scheduler startup failed: {e}")
        logger.warning("⚠️  Server starting anyway - Scheduler disabled")

# Shutdown Event - Stop Scheduler
@app.on_event("shutdown")
async def shutdown_scheduler_handler():
    """Gracefully shutdown scheduler on app termination"""
    logger.info("🛑 Shutting down application...")
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.error(f"❌ Scheduler shutdown error: {e}")

# Include Routers
app.include_router(sync.router, prefix="/api", tags=["Sync"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])
app.include_router(recommend.router, prefix="/api", tags=["Recommend"])

# Import admin router
from .api import admin
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "BSK-SER PostgreSQL API Server Running"}

if __name__ == "__main__":
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "backend.main_api:app", 
        host=API_HOST, 
        port=API_PORT, 
        reload=API_RELOAD
    )
