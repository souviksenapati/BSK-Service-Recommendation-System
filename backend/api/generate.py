import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from ..database.connection import get_db
from ..database.models import RegenerationLog

router = APIRouter()
logger = logging.getLogger(__name__)

class GenerateRequest(BaseModel):
    generate_all: bool = True
    files: Optional[List[str]] = None
    triggered_by: str = "manual"  # 'manual', 'scheduler', 'admin'

@router.post("/generate-static-files")
async def generate_static_files(request: GenerateRequest, db: Session = Depends(get_db)):
    """
    Regenerate derived static tables used for recommendations.
    Logs each regeneration event to regeneration_log table.
    """
    start_time = datetime.now()
    logger.info(f"Starting static file generation. All={request.generate_all}, Triggered by={request.triggered_by}")
    
    generated = []
    
    try:
        # 1. Generate grouped_df (Demographic Clusters)
        if request.generate_all or (request.files and "grouped_df" in request.files):
            table_start = datetime.now()
            logger.info("Generating grouped_df...")
            
            # Clear existing
            db.execute(text("TRUNCATE TABLE grouped_df"))
            
            # Insert new groups
            query = text("""
                INSERT INTO grouped_df (cluster_id, district_id, gender, caste, age_group, religion_group)
                SELECT 
                    ROW_NUMBER() OVER () as cluster_id,
                    district_id,
                    gender,
                    caste,
                    CASE 
                        WHEN age < 18 THEN 'child'
                        WHEN age < 60 THEN 'youth'
                        ELSE 'elderly'
                    END as age_group,
                    CASE 
                        WHEN religion = 'Hindu' THEN 'Hindu'
                        ELSE 'Minority'
                    END as religion_group
                FROM ml_citizen_master
                GROUP BY 
                    district_id,
                    gender,
                    caste,
                    CASE 
                        WHEN age < 18 THEN 'child'
                        WHEN age < 60 THEN 'youth'
                        ELSE 'elderly'
                    END,
                    CASE 
                        WHEN religion = 'Hindu' THEN 'Hindu'
                        ELSE 'Minority'
                    END;
            """)
            db.execute(query)
            
            # Get row count
            row_count = db.execute(text("SELECT COUNT(*) FROM grouped_df")).scalar()
            duration = (datetime.now() - table_start).total_seconds()
            
            # Log regeneration
            log_entry = RegenerationLog(
                table_name="grouped_df",
                rows_generated=row_count,
                duration_seconds=duration,
                status="success",
                triggered_by=request.triggered_by
            )
            db.add(log_entry)
            
            generated.append("grouped_df")
            logger.info(f"✅ grouped_df: {row_count:,} rows in {duration:.2f}s")
            
        # 2. Generate district_top_services
        if request.generate_all or (request.files and "district_top_services" in request.files):
            table_start = datetime.now()
            logger.info("Generating district_top_services...")
            
            db.execute(text("TRUNCATE TABLE district_top_services"))
            
            query = text("""
                INSERT INTO district_top_services (district_id, district_name, service_id, service_name, unique_citizen_count, citizen_percentage, rank_in_district)
                WITH district_service_counts AS (
                    SELECT 
                        c.district_id,
                        d.district_name,
                        p.service_id,
                        p.service_name,
                        COUNT(DISTINCT p.customer_id) as unique_citizen_count
                    FROM ml_provision p
                    JOIN ml_citizen_master c ON p.customer_id = c.citizen_id
                    JOIN ml_district d ON c.district_id = d.district_id
                    GROUP BY c.district_id, d.district_name, p.service_id, p.service_name
                ),
                district_totals AS (
                    SELECT district_id, COUNT(DISTINCT customer_id) as total_citizens
                    FROM ml_provision p
                    JOIN ml_citizen_master c ON p.customer_id = c.citizen_id
                    GROUP BY c.district_id
                )
                SELECT 
                    dsc.district_id,
                    dsc.district_name,
                    dsc.service_id,
                    dsc.service_name,
                    dsc.unique_citizen_count,
                    COALESCE(ROUND((dsc.unique_citizen_count::DECIMAL /NULLIF(dt.total_citizens, 0)) * 100, 2), 0) as citizen_percentage,
                    RANK() OVER (PARTITION BY dsc.district_id ORDER BY dsc.unique_citizen_count DESC) as rank_in_district
                FROM district_service_counts dsc
                JOIN district_totals dt ON dsc.district_id = dt.district_id;
            """)
            db.execute(query)
            
            row_count = db.execute(text("SELECT COUNT(*) FROM district_top_services")).scalar()
            duration = (datetime.now() - table_start).total_seconds()
            
            log_entry = RegenerationLog(
                table_name="district_top_services",
                rows_generated=row_count,
                duration_seconds=duration,
                status="success",
                triggered_by=request.triggered_by
            )
            db.add(log_entry)
            
            generated.append("district_top_services")
            logger.info(f"✅ district_top_services: {row_count:,} rows in {duration:.2f}s")

        # 3. Generate block_wise_top_services (4 columns ONLY)
        # Table schema: block_id, service_name, block_name, rank_in_block
        if request.generate_all or (request.files and "block_wise_top_services" in request.files):
            table_start = datetime.now()
            logger.info("Generating block_wise_top_services...")
            
            db.execute(text("TRUNCATE TABLE block_wise_top_services"))
            
            query = text("""
                INSERT INTO block_wise_top_services (block_id, service_name, block_name, rank_in_block)
                WITH block_service_counts AS (
                    SELECT 
                        b.block_mun_id as block_id,
                        b.block_municipalty_name as block_name,
                        p.service_name,
                        COUNT(DISTINCT p.customer_id) as unique_citizen_count
                    FROM ml_provision p
                    JOIN ml_bsk_master b ON p.bsk_id = b.bsk_id
                    WHERE b.block_mun_id IS NOT NULL
                    GROUP BY b.block_mun_id, b.block_municipalty_name, p.service_name
                )
                SELECT 
                    bsc.block_id,
                    bsc.service_name,
                    bsc.block_name,
                    RANK() OVER (PARTITION BY bsc.block_id ORDER BY bsc.unique_citizen_count DESC) as rank_in_block
                FROM block_service_counts bsc;
            """)
            db.execute(query)
            
            row_count = db.execute(text("SELECT COUNT(*) FROM block_wise_top_services")).scalar()
            duration = (datetime.now() - table_start).total_seconds()
            
            log_entry = RegenerationLog(
                table_name="block_wise_top_services",
                rows_generated=row_count,
                duration_seconds=duration,
                status="success",
                triggered_by=request.triggered_by
            )
            db.add(log_entry)
            
            generated.append("block_wise_top_services")
            logger.info(f"✅ block_wise_top_services: {row_count:,} rows in {duration:.2f}s")

        # 4. Generate cluster_service_map (3 columns ONLY)
        # Table schema: cluster_id, service_id, rank (NO usage_count)
        if request.generate_all or (request.files and "cluster_service_map" in request.files):
            table_start = datetime.now()
            logger.info("Generating cluster_service_map...")
            
            db.execute(text("TRUNCATE TABLE cluster_service_map"))
            
            query = text("""
                INSERT INTO cluster_service_map (cluster_id, service_id, rank)
                WITH cluster_services AS (
                    SELECT 
                        g.cluster_id,
                        p.service_id,
                        COUNT(*) as usage_count
                    FROM grouped_df g
                    JOIN ml_citizen_master c ON 
                        c.district_id = g.district_id AND
                        c.gender = g.gender AND
                        c.caste = g.caste AND
                        (CASE WHEN c.age < 18 THEN 'child' WHEN c.age < 60 THEN 'youth' ELSE 'elderly' END) = g.age_group AND
                        (CASE WHEN c.religion = 'Hindu' THEN 'Hindu' ELSE 'Minority' END) = g.religion_group
                    JOIN ml_provision p ON c.citizen_id = p.customer_id
                    GROUP BY g.cluster_id, p.service_id
                )
                SELECT 
                    cluster_id,
                    service_id,
                    RANK() OVER (PARTITION BY cluster_id ORDER BY usage_count DESC) as rank
                FROM cluster_services;
            """)
            db.execute(query)
            
            row_count = db.execute(text("SELECT COUNT(*) FROM cluster_service_map")).scalar()
            duration = (datetime.now() - table_start).total_seconds()
            
            log_entry = RegenerationLog(
                table_name="cluster_service_map",
                rows_generated=row_count,
                duration_seconds=duration,
                status="success",
                triggered_by=request.triggered_by
            )
            db.add(log_entry)
            
            generated.append("cluster_service_map")
            logger.info(f"✅ cluster_service_map: {row_count:,} rows in {duration:.2f}s")
            
        db.commit()
        total_duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"🎉 All generations complete! Total time: {total_duration:.2f}s")
        
        return {
            "status": "success", 
            "generated_files": generated,
            "total_duration_seconds": round(total_duration, 2),
            "message": f"Static generation completed successfully in {total_duration:.2f}s"
        }
        
    except Exception as e:
        db.rollback()
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Generation failed after {total_duration:.2f}s: {e}")
        
        # Log failure
        error_log = RegenerationLog(
            table_name="ALL",
            rows_generated=0,
            duration_seconds=total_duration,
            status="failed",
            error_message=str(e)[:500],
            triggered_by=request.triggered_by
        )
        try:
            db.add(error_log)
            db.commit()
        except:
            pass  # Don't fail if we can't log the error
            
        raise HTTPException(status_code=500, detail=str(e))
