# AUTO-GENERATED models.py from ACTUAL database schema
# Generated: 2026-01-29 10:54 - FINAL CORRECTED VERSION
# VERIFIED AGAINST POSTGRESQL DATABASE - MANUAL VERIFICATION
from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, ForeignKey, BigInteger, Numeric, Float
from sqlalchemy.sql import func  
from .connection import Base

class CitizenMaster(Base):
    """ml_citizen_master - 14 columns"""
    __tablename__ = "ml_citizen_master"

    citizen_id = Column(String, primary_key=True)
    citizen_phone = Column(BigInteger)
    citizen_name = Column(String)
    alt_phone = Column(Float)
    email = Column(String)
    guardian_name = Column(String)
    district_id = Column(Float)
    sub_div_id = Column(Float)
    gp_id = Column(Float)
    gender = Column(String)
    dob = Column(String)
    age = Column(Float)
    caste = Column(String)
    religion = Column(String)

class Provision(Base):
    """ml_provision - 10 columns, NO provision_id"""
    __tablename__ = "ml_provision"

    # Composite primary key (no single ID column exists)
    bsk_id = Column(BigInteger, primary_key=True)
    customer_id = Column(String, primary_key=True)
    service_id = Column(BigInteger, primary_key=True)
    prov_date = Column(String, primary_key=True)
    bsk_name = Column(String)
    customer_name = Column(String)
    customer_phone = Column(BigInteger)
    service_name = Column(String)
    docket_no = Column(BigInteger)
    bsk_type = Column(String)

class BSKMaster(Base):
    """ml_bsk_master - 24 columns"""
    __tablename__ = "ml_bsk_master"

    bsk_id = Column(BigInteger, primary_key=True)
    bsk_name = Column(String)
    district_name = Column(String)
    sub_division_name = Column(String)
    block_municipalty_name = Column(String)  # Note: typo preserved from CSV
    gp_ward = Column(String)
    gp_ward_distance = Column(Float)
    bsk_type = Column(String)
    bsk_sub_type = Column(String)
    bsk_code = Column(String)
    no_of_deos = Column(BigInteger)
    is_aadhar_center = Column(BigInteger)
    bsk_address = Column(String)
    bsk_lat = Column(Float)
    bsk_long = Column(Float)
    bsk_account_no = Column(Float)
    bsk_landline_no = Column(Float)
    is_saturday_open = Column(String)
    is_active = Column(String)
    district_id = Column(BigInteger)
    block_mun_id = Column(BigInteger)
    gp_id = Column(BigInteger)
    sub_div_id = Column(BigInteger)
    pin = Column(BigInteger)

class District(Base):
    """ml_district - 4 columns"""
    __tablename__ = "ml_district"

    district_id = Column(BigInteger, primary_key=True)
    district_name = Column(String)
    district_code = Column(BigInteger)
    grp = Column(String)

class Service(Base):
    """services - 25 columns (has is_recurrent1 duplicate)"""
    __tablename__ = "services"

    service_id = Column(BigInteger, primary_key=True)
    is_recurrent = Column(BigInteger)
    service_name = Column(String)
    common_name = Column(String)
    action_name = Column(String)
    service_link = Column(String)
    department_id = Column(Float)
    department_name = Column(String)
    is_new = Column(BigInteger)
    service_type = Column(String)
    is_active = Column(BigInteger)
    is_paid_service = Column(Boolean)
    service_desc = Column(String)
    how_to_apply = Column(String)
    eligibility_criteria = Column(String)
    required_doc = Column(String)
    min_age = Column(BigInteger)
    max_age = Column(BigInteger)
    is_sc = Column(BigInteger)
    is_st = Column(BigInteger)
    is_obc_a = Column(BigInteger)
    is_obc_b = Column(BigInteger)
    is_female = Column(BigInteger)
    is_minority = Column(BigInteger)
    is_recurrent1 = Column(BigInteger)  # Duplicate column in database

class ServiceEligibility(Base):
    """services_eligibility - 11 columns, NO id"""
    __tablename__ = "services_eligibility"

    # Composite primary key (no id column exists)
    service_id = Column(BigInteger, primary_key=True)
    service_name = Column(String, primary_key=True)
    min_age = Column(BigInteger)
    max_age = Column(BigInteger)
    is_sc = Column(BigInteger)
    is_st = Column(BigInteger)
    is_obc_a = Column(BigInteger)
    is_obc_b = Column(BigInteger)
    is_female = Column(BigInteger)
    is_minority = Column(BigInteger)
    for_all = Column(BigInteger)

# NOTE: grouped_df has 267 columns in DB, but only first 6 are used for queries
# The other 261 columns (service_1, service_2, etc.) are not modeled

class GroupedDF(Base):
    """grouped_df - only 6 metadata columns modeled (267 total in DB)"""
    __tablename__ = "grouped_df"

    cluster_id = Column(BigInteger, primary_key=True)
    district_id = Column(BigInteger)
    gender = Column(String)
    caste = Column(String)
    age_group = Column(String)
    religion_group = Column(String)
    # Note: 261 service columns (service_1, service_2, etc.) exist but are not modeled

# NOTE: openai_similarity_matrix is NOT modeled - use CSV directly (442 columns!)

class ClusterServiceMap(Base):
    """cluster_service_map - 3 columns, NO usage_count"""
    __tablename__ = "cluster_service_map"

    cluster_id = Column(BigInteger, primary_key=True)
    service_id = Column(BigInteger, primary_key=True)
    rank = Column(BigInteger)

class DistrictTopService(Base):
    """district_top_services - 7 columns, NO id"""
    __tablename__ = "district_top_services"

    # Composite primary key (no id column)
    district_id = Column(BigInteger, primary_key=True)
    service_id = Column(BigInteger, primary_key=True)
    district_name = Column(String)
    service_name = Column(String)
    unique_citizen_count = Column(BigInteger)
    citizen_percentage = Column(Float)
    rank_in_district = Column(BigInteger)

class BlockTopService(Base):
    """block_wise_top_services - 4 columns ONLY"""
    __tablename__ = "block_wise_top_services"

    # Composite primary key
    block_id = Column(BigInteger, primary_key=True)
    service_name = Column(String, primary_key=True)
    block_name = Column(String)
    rank_in_block = Column(BigInteger)

class SyncMetadata(Base):
    """sync_metadata - for tracking API syncs"""
    __tablename__ = "sync_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), unique=True)
    last_sync_timestamp = Column(TIMESTAMP)
    last_sync_from_date = Column(Date)
    total_records = Column(Integer)
    last_sync_status = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class RegenerationLog(Base):
    """regeneration_log - for tracking static file regeneration history"""
    __tablename__ = "regeneration_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    regeneration_timestamp = Column(TIMESTAMP, server_default=func.now())
    table_name = Column(String(100))  # Which table was regenerated
    rows_generated = Column(Integer)  # How many rows were created
    duration_seconds = Column(Float)  # How long it took
    status = Column(String(50))  # 'success' or 'failed'
    error_message = Column(String(500))  # Error details if failed
    triggered_by = Column(String(50))  # 'scheduler', 'manual', 'admin'
    created_at = Column(TIMESTAMP, server_default=func.now())
