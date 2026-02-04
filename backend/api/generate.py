import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from enum import Enum

from ..database.connection import get_db
from ..database.models import RegenerationLog

router = APIRouter()
logger = logging.getLogger(__name__)

class RegenerationType(str, Enum):
    """Regeneration types"""
    DISTRICT = "district"
    BLOCK = "block"
    DEMOGRAPHIC = "demographic"
    ALL = "all"

@router.post("/regenerate/{type}")
async def regenerate_files(
    type: RegenerationType = Path(..., description="Type of files to regenerate: district, block, demographic, or all"),
    db: Session = Depends(get_db)
):
    """
    Regenerate pre-computed recommendation files from database.
    
    - **district**: Regenerate district-based recommendations only
    - **block**: Regenerate block-wise recommendations only
    - **demographic**: Regenerate demographic clustering files only
    - **all**: Regenerate all recommendation files
    """
    start_time = datetime.now()
    logger.info(f"Starting regeneration: type={type}")
    
    district_files = []
    block_files = []
    demographic_files = []
    
    try:
        # Determine which files to generate based on type
        generate_district = type in [RegenerationType.DISTRICT, RegenerationType.ALL]
        generate_block = type in [RegenerationType.BLOCK, RegenerationType.ALL]
        generate_demographic = type in [RegenerationType.DEMOGRAPHIC, RegenerationType.ALL]
        
        # 1. Generate DEMOGRAPHIC files (grouped_df, cluster_service_map)
        if generate_demographic:
            # 1a. Generate grouped_df
            table_start = datetime.now()
            logger.info("Generating grouped_df...")
            
            db.execute(text("TRUNCATE TABLE grouped_df"))
            
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
            
            row_count = db.execute(text("SELECT COUNT(*) FROM grouped_df")).scalar()
            duration = (datetime.now() - table_start).total_seconds()
            
            log_entry = RegenerationLog(
                table_name="grouped_df",
                rows_generated=row_count,
                duration_seconds=duration,
                status="success",
                triggered_by="api"
            )
            db.add(log_entry)
            
            demographic_files.append("grouped_df")
            logger.info(f"✅ grouped_df: {row_count:,} rows in {duration:.2f}s")
            
            # 1b. Generate cluster_service_map
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
                triggered_by="api"
            )
            db.add(log_entry)
            
            demographic_files.append("final_df")
            demographic_files.append("cluster_service_map.pkl")
            logger.info(f"✅ cluster_service_map: {row_count:,} rows in {duration:.2f}s")

        # 2. Generate DISTRICT files (district_top_services)
        if generate_district:
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
                triggered_by="api"
            )
            db.add(log_entry)
            
            district_files.append("district_top_services")
            logger.info(f"✅ district_top_services: {row_count:,} rows in {duration:.2f}s")

        # 3. Generate BLOCK files (block_wise_top_services)
        if generate_block:
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
                triggered_by="api"
            )
            db.add(log_entry)
            
            block_files.append("block_top_services")
            logger.info(f"✅ block_wise_top_services: {row_count:,} rows in {duration:.2f}s")
            
        db.commit()
        total_duration = (datetime.now() - start_time).total_seconds()
        
        # Build response based on what was generated
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        if type == RegenerationType.ALL:
            response["message"] = "All files regenerated successfully"
            response["district_files"] = district_files
            response["block_files"] = block_files
            response["demographic_files"] = demographic_files
        elif type == RegenerationType.DISTRICT:
            response["message"] = "District files regenerated successfully"
            response["district_files"] = district_files
        elif type == RegenerationType.BLOCK:
            response["message"] = "Block files regenerated successfully"
            response["block_files"] = block_files
        elif type == RegenerationType.DEMOGRAPHIC:
            response["message"] = "Demographic files regenerated successfully"
            response["demographic_files"] = demographic_files
        
        logger.info(f"🎉 Regeneration complete! Total time: {total_duration:.2f}s")
        
        return response
        
    except Exception as e:
        db.rollback()
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Regeneration failed after {total_duration:.2f}s: {e}")
        
        # Log failure
        error_log = RegenerationLog(
            table_name=type.value,
            rows_generated=0,
            duration_seconds=total_duration,
            status="failed",
            error_message=str(e)[:500],
            triggered_by="api"
        )
        try:
            db.add(error_log)
            db.commit()
        except:
            pass
            
        raise HTTPException(status_code=500, detail=str(e))
