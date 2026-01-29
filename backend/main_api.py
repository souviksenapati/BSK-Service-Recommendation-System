from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import sync, generate, recommend
from .database.connection import engine
from sqlalchemy import text, inspect
import uvicorn
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BSK-SER PostgreSQL Backend", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event - Database Verification
@app.on_event("startup")
async def verify_database():
    """Verify database connection and tables on every startup/reload"""
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

# Include Routers
app.include_router(sync.router, prefix="/api", tags=["Sync"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])
app.include_router(recommend.router, prefix="/api", tags=["Recommend"])

@app.get("/")
def root():
    return {"message": "BSK-SER PostgreSQL API Server Running"}

if __name__ == "__main__":
    uvicorn.run("backend.main_api:app", host="0.0.0.0", port=8000, reload=True)
