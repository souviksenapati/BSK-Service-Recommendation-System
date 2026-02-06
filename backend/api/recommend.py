import logging
import math
import json
import os
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date

from ..database.connection import get_db
from ..database.models import (
    CitizenMaster, Provision, District, BSKMaster, Service, 
    ServiceEligibility, DistrictTopService, BlockTopService,
    GroupedDF, ClusterServiceMap
)

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Pydantic Models for Request/Response ---

class RecommendRequest(BaseModel):
    phone: Optional[str] = Field(default="9740781204", example="9740781204", description="Citizen's phone number")
    age: int = Field(default=32, example=32, description="Age in years")
    gender: str = Field(default="Male", example="Male", description="Gender: Male/Female")
    caste: str = Field(default="General", example="General", description="Caste category")
    district_name: str = Field(example="PURBA MEDINIPUR", description="District name (required)")
    block_name: Optional[str] = Field(default="EGRA I", example="EGRA I", description="Block/Municipality name (optional)")
    religion: str = Field(default="Hindu", example="Hindu", description="Religion")
    selected_service_name: Optional[str] = Field(default="Application for Income Certificates", example="Application for Income Certificates", description="Previously used service (optional)")

# --- Helper Functions (Engines) ---

def block_service_filter(service_name: str, caste: str) -> bool:
    """Filter out birth/death and caste-specific services for General."""
    if not service_name:
        return False
    s = service_name.lower()
    if "birth" in s or "death" in s:
        return False
    if caste and caste.lower() == "general" and "caste" in s:
        return False
    return True

def check_eligibility(db: Session, service_name: str, age: int, gender: str, caste: str, religion: str) -> bool:
    """Check service eligibility against services_eligibility table."""
    # Find service rules
    # Note: services_eligibility might have multiple entries or map by name. 
    # Ideally link by ID but Streamlit used Name. Using Name for consistency with legacy.
    rule = db.query(ServiceEligibility).filter(
        func.lower(ServiceEligibility.service_name) == func.lower(service_name)
    ).first()
    
    if not rule:
        return True # Default to allow if no specific rules found
        
    # 1. Age Check
    if rule.min_age is not None and age < rule.min_age: return False
    if rule.max_age is not None and age > rule.max_age: return False
    
    # 2. Universal Check
    if rule.for_all: return True
    
    # 3. Caste Check
    if caste == 'SC' and not rule.is_sc: return False
    if caste == 'ST' and not rule.is_st: return False
    if caste == 'OBC-A' and not rule.is_obc_a: return False
    if caste == 'OBC-B' and not rule.is_obc_b: return False
    if caste == 'General':
        # General cannot take caste-specific schemes
        if rule.is_sc or rule.is_st or rule.is_obc_a or rule.is_obc_b: return False
        
    # 4. Gender Check
    if gender == 'Female' and not rule.is_female: return False # Assuming is_female means ONLY female? Verification needed. 
    # Streamlit Logic: if user=Male and is_female=1 -> False.
    if gender == 'Male' and rule.is_female: return False 
    
    # 5. Religion Check
    is_minority = religion not in ['Hindu']
    if not is_minority and rule.is_minority: return False # Hindu user, Minority scheme
    if is_minority and not rule.is_minority: return False # Warning: This logic assumes non-minority schemes are Hindu only? 
    # Streamlit Logic: if is_minority and rule.is_minority==0 -> False. 
    # This implies schemes are either for Minority or Not (Hindu). 
    
    return True

def get_citizen_by_phone(db: Session, phone: str):
    try:
        phone_int = int(phone)
        return db.query(CitizenMaster).filter(CitizenMaster.citizen_phone == phone_int).first()
    except:
        return None

def get_block_id_from_history(db: Session, citizen_id: str):
    """Try to find block_id from provision > bsk_master linkage"""
    last_provision = db.query(Provision).filter(
        Provision.customer_id == citizen_id
    ).order_by(desc(Provision.prov_date)).first()
    
    if last_provision and last_provision.bsk_id:
        bsk = db.query(BSKMaster).filter(BSKMaster.bsk_id == last_provision.bsk_id).first()
        if bsk:
            return bsk.block_mun_id
    return None

def get_district_id_by_name(db: Session, district_name: str) -> Optional[int]:
    """Convert district name to district_id"""
    district = db.query(District).filter(
        func.lower(District.district_name) == func.lower(district_name)
    ).first()
    return district.district_id if district else None

def get_block_id_by_name(db: Session, block_name: str) -> Optional[int]:
    """Convert block name to block_id"""
    if not block_name or block_name.lower() == "none":
        return None
    bsk = db.query(BSKMaster).filter(
        func.lower(BSKMaster.block_municipalty_name) == func.lower(block_name)
    ).first()
    return bsk.block_mun_id if bsk else None

def get_service_id_by_name(db: Session, service_name: str) -> Optional[int]:
    """Convert service name to service_id"""
    if not service_name:
        return None
    service = db.query(Service).filter(
        func.lower(Service.service_name) == func.lower(service_name)
    ).first()
    return service.service_id if service else None

# --- Main Engines ---

def engine_district(db: Session, district_id: int, caste: str, limit: int = 5) -> List[str]:
    recs = db.query(DistrictTopService.service_name).filter(
        DistrictTopService.district_id == district_id
    ).order_by(DistrictTopService.rank_in_district).all()
    
    results = []
    for (name,) in recs:
        if block_service_filter(name, caste):
            results.append(name)
        if len(results) >= limit: break
    return results

def engine_block(db: Session, block_id: int, caste: str, limit: int = 5) -> List[str]:
    if not block_id: return []
    recs = db.query(BlockTopService.service_name).filter(
        BlockTopService.block_id == block_id
    ).order_by(BlockTopService.rank_in_block).all()
    
    results = []
    for (name,) in recs:
        if block_service_filter(name, caste):
            results.append(name)
        if len(results) >= limit: break
    return results

def engine_demographic(db: Session, district_id: int, gender: str, caste: str, age: int, religion: str, limit: int = 5) -> List[str]:
    # Age Groups
    # Static CSV paths
    DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    if age < 18:
        # Read from static CSV
        try:
            csv_path = os.path.join(DATA_DIR, "under18_top_services.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                return df['service_name'].tolist()
        except Exception as e:
            logger.error(f"Error reading under18 CSV: {e}")
        return ["Student Credit Card", "Kanyashree", "Aikyasree", "Sikshashree", "Pre Matric Scholarship"] 
        
    elif age >= 60:
        # Read from static CSV
        try:
            csv_path = os.path.join(DATA_DIR, "above60_top_services.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                return df['service_name'].tolist()
        except Exception as e:
            logger.error(f"Error reading above60 CSV: {e}")
        return ["Old Age Pension", "Widow Pension", "Lakshmir Bhandar", "Swasthya Sathi", "Jai Bangla"]
    
    age_group = 'youth' if age < 60 else 'elderly'
    religion_group = 'Hindu' if religion == 'Hindu' else 'Minority'
    
    # 1. Find Cluster
    cluster = db.query(GroupedDF).filter(
        GroupedDF.district_id == district_id,
        GroupedDF.gender == gender,
        GroupedDF.caste == caste,
        GroupedDF.age_group == age_group,
        GroupedDF.religion_group == religion_group
    ).first()
    
    if not cluster:
        return []
        
    # 2. Get Services for Cluster
    services = db.query(Service.service_name).join(
        ClusterServiceMap, ClusterServiceMap.service_id == Service.service_id
    ).filter(
        ClusterServiceMap.cluster_id == cluster.cluster_id
    ).order_by(ClusterServiceMap.rank).all()
    
    results = []
    for (name,) in services:
        if block_service_filter(name, caste):
            results.append(name)
        if len(results) >= limit: break
    return results

def engine_content(db: Session, service_history_ids: List[int], selected_service_id: Optional[int], caste: str, limit: int = 5) -> Dict[str, List[str]]:
    # Combine history and selection
    target_ids = list(service_history_ids)
    if selected_service_id and selected_service_id not in target_ids:
        target_ids.append(selected_service_id)
        
    results = {}
    
    # Simple Content Logic: Fetch similar from DB (Placeholder for now)
    # Real logic: Query OpenAISimilarity table
    # Since we defined OpenAISimilarity with a JSON string, we'd need to parse it. 
    # For MVP without real data in that table, we skip or use dummy.
    
    return results

# --- Main Endpoint ---

@router.post("/recommend")
async def recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    # 0. Resolve Names to IDs
    district_id = get_district_id_by_name(db, req.district_name)
    if not district_id:
        raise HTTPException(status_code=400, detail=f"District '{req.district_name}' not found")
    
    block_id = get_block_id_by_name(db, req.block_name) if req.block_name else None
    selected_service_id = get_service_id_by_name(db, req.selected_service_name) if req.selected_service_name else None
    
    # 1. Citizen Lookup
    citizen_exists = False
    citizen_id = None
    if req.phone:
        citizen_row = get_citizen_by_phone(db, req.phone)
        if citizen_row:
            citizen_exists = True
            citizen_id = citizen_row.citizen_id
            # Override inputs with DB data
            req.age = citizen_row.age if citizen_row.age else req.age
            req.gender = citizen_row.gender if citizen_row.gender else req.gender
            req.caste = citizen_row.caste if citizen_row.caste else req.caste
            req.religion = citizen_row.religion if citizen_row.religion else req.religion
            if not block_id:
                block_id = get_block_id_from_history(db, citizen_id)

    # 2. Service History
    history_ids = []
    service_history = []
    if citizen_exists:
        logging.info(f"Querying provisions for citizen_id: {citizen_id}")
        provisions = db.query(Provision).filter(Provision.customer_id == citizen_id).order_by(desc(Provision.prov_date)).limit(10).all()
        logging.info(f"Found {len(provisions)} provisions for citizen {citizen_id}")
        for p in provisions:
            history_ids.append(p.service_id)
            service_history.append({"service": p.service_name, "date": str(p.prov_date)})
        if len(provisions) == 0:
            logging.warning(f"No provisions found for citizen_id={citizen_id}, but citizen exists in citizen_master")
            
    # 3. Engines Execution
    district_recs = engine_district(db, district_id, req.caste)
    block_recs = engine_block(db, block_id, req.caste)
    demo_recs = engine_demographic(db, district_id, req.gender, req.caste, req.age, req.religion)
    content_recs = engine_content(db, history_ids, selected_service_id, req.caste)
    
    # 4. Consolidation & Eligibility
    all_recs_set = set()
    all_recs_set.update(district_recs)
    all_recs_set.update(block_recs)
    all_recs_set.update(demo_recs)
    for sublist in content_recs.values():
        all_recs_set.update(sublist)
        
    eligible_recs = []
    for s_name in all_recs_set:
        if check_eligibility(db, s_name, req.age, req.gender, req.caste, req.religion):
            eligible_recs.append(s_name)
            
    # Format: [count, service1, service2, ...]
    recommendations_with_count = [len(eligible_recs)] + eligible_recs
    
    return {
        "citizen_exists": citizen_exists,
        "citizen_id": citizen_id,
        "demographics": {
            "age": req.age, "gender": req.gender, "caste": req.caste
        },
        "service_history": service_history,
        "recommendations": recommendations_with_count
    }
