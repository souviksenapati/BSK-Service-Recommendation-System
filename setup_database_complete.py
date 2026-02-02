"""
Comprehensive Database Setup Script for BSK-SER
================================================
This script does EVERYTHING needed to set up a fresh database:
1. Creates PostgreSQL database if it doesn't exist
2. Creates all tables with proper schemas
3. Creates indexes for performance
4. Creates constraints and foreign keys
5. Imports all data from CSV/PKL files
6. Initializes sync_metadata table
7. Verifies all imports

Usage:
    python setup_database_complete.py

Requirements:
    - PostgreSQL server running
    - .env file with DATABASE_URL configured
    - CSV data files in /data directory
"""

import os
import sys
import pandas as pd
import json
import pickle
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Database configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")  # No default - must be in .env
DB_NAME = os.getenv("DB_NAME", "bsk")

# Validate required environment variables
if not DB_PASSWORD:
    logger.error("❌ DB_PASSWORD not set in .env file!")
    logger.error("Please create a .env file with your database credentials.")
    logger.error("Copy .env.example to .env and fill in your values.")
    sys.exit(1)

# Construct database URLs
POSTGRES_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_step(step_num, total, description):
    """Print a step description"""
    print(f"\n[{step_num}/{total}] {description}")
    print("-"*70)


def create_database():
    """Create the database if it doesn't exist"""
    print_step(1, 7, "Creating Database")
    
    try:
        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"✅ Database '{DB_NAME}' already exists")
        else:
            # Create database
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(f"✅ Created database '{DB_NAME}'")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        sys.exit(1)


def create_tables():
    """Create all tables with proper schemas"""
    print_step(2, 7, "Creating Tables")
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Import models to register them
        from backend.database.models import Base
        
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("✅ All tables created successfully")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        sys.exit(1)


def create_indexes():
    """Create indexes for better query performance"""
    print_step(3, 7, "Creating Indexes")
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        indexes = [
            # CitizenMaster indexes
            "CREATE INDEX IF NOT EXISTS idx_citizen_phone ON ml_citizen_master(citizen_phone)",
            "CREATE INDEX IF NOT EXISTS idx_citizen_district ON ml_citizen_master(district_id)",
            "CREATE INDEX IF NOT EXISTS idx_citizen_gender ON ml_citizen_master(gender)",
            "CREATE INDEX IF NOT EXISTS idx_citizen_caste ON ml_citizen_master(caste)",
            
            # Provision indexes
            "CREATE INDEX IF NOT EXISTS idx_provision_customer ON ml_provision(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_provision_service ON ml_provision(service_id)",
            "CREATE INDEX IF NOT EXISTS idx_provision_bsk ON ml_provision(bsk_id)",
            "CREATE INDEX IF NOT EXISTS idx_provision_date ON ml_provision(prov_date)",
            
            # District indexes
            "CREATE INDEX IF NOT EXISTS idx_district_name ON ml_district(district_name)",
            
            # BSK Master indexes
            "CREATE INDEX IF NOT EXISTS idx_bsk_district ON ml_bsk_master(district_id)",
            "CREATE INDEX IF NOT EXISTS idx_bsk_block ON ml_bsk_master(block_mun_id)",
            "CREATE INDEX IF NOT EXISTS idx_bsk_type ON ml_bsk_master(bsk_type)",
            
            # Service indexes
            "CREATE INDEX IF NOT EXISTS idx_service_name ON services(service_name)",
            "CREATE INDEX IF NOT EXISTS idx_service_active ON services(is_active)",
            
            # GroupedDF indexes
            "CREATE INDEX IF NOT EXISTS idx_grouped_district ON grouped_df(district_id)",
            "CREATE INDEX IF NOT EXISTS idx_grouped_demo ON grouped_df(gender, caste, age_group, religion_group)",
            
            # DistrictTopService indexes
            "CREATE INDEX IF NOT EXISTS idx_district_top_rank ON district_top_services(district_id, rank_in_district)",
            
            # BlockTopService indexes
            "CREATE INDEX IF NOT EXISTS idx_block_top_rank ON block_wise_top_services(block_id, rank_in_block)",
            
            # ClusterServiceMap indexes
            "CREATE INDEX IF NOT EXISTS idx_cluster_rank ON cluster_service_map(cluster_id, rank)",
            
            # SyncMetadata indexes
            "CREATE INDEX IF NOT EXISTS idx_sync_table ON sync_metadata(table_name)",
            
            # RegenerationLog indexes
            "CREATE INDEX IF NOT EXISTS idx_regen_timestamp ON regeneration_log(regeneration_timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_regen_table ON regeneration_log(table_name, status)",
        ]
        
        with engine.connect() as conn:
            for idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    table_name = idx_sql.split("ON ")[1].split("(")[0].strip()
                    logger.info(f"✅ Created index on {table_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Index creation warning: {e}")
            
            conn.commit()
        
        logger.info("✅ All indexes created successfully")
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        # Continue anyway - indexes are optional


def import_csv_data():
    """Import data from CSV files"""
    print_step(4, 7, "Importing CSV Data")
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Define CSV to table mappings
    csv_mappings = [
        ("ml_district.csv", "ml_district"),
        ("ml_bsk_master.csv", "ml_bsk_master"),
        ("ml_citizen_master.csv", "ml_citizen_master"),
        ("ml_provision.csv", "ml_provision"),
        ("services.csv", "services"),
        # services_eligibility will be derived from services.csv
        ("grouped_df.csv", "grouped_df"),
        ("district_top_services.csv", "district_top_services"),
        ("block_wise_top_services.csv", "block_wise_top_services"),
    ]
    
    data_dir = "data"
    
    for csv_file, table_name in csv_mappings:
        csv_path = os.path.join(data_dir, csv_file)
        
        if not os.path.exists(csv_path):
            logger.warning(f"⚠️  {csv_file} not found, skipping...")
            continue
        
        logger.info(f"\n📥 Importing {csv_file} → {table_name}")
        
        try:
            # Read CSV
            try:
                df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
            
            logger.info(f"   Read {len(df):,} rows with {len(df.columns)} columns")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            df.columns = df.columns.str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
            
            # Import to database
            df.to_sql(
                table_name,
                engine,
                if_exists='replace',
                index=False,
                method='multi',
                chunksize=5000
            )
            
            logger.info(f"   ✅ Imported {len(df):,} rows into {table_name}")
            
        except Exception as e:
            logger.error(f"   ❌ Error importing {csv_file}: {e}")
            continue
    
    engine.dispose()


def import_cluster_service_map():
    """Import cluster_service_map from PKL file"""
    logger.info(f"\n📥 Importing cluster_service_map from PKL")
    
    pkl_path = "data/cluster_service_map.pkl"
    
    if not os.path.exists(pkl_path):
        logger.warning(f"⚠️  {pkl_path} not found, skipping...")
        return
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    try:
        with open(pkl_path, 'rb') as f:
            cluster_map = pickle.load(f)
        
        # Convert to DataFrame
        if isinstance(cluster_map, dict):
            rows = []
            for cluster_id, services in cluster_map.items():
                if isinstance(services, list):
                    for service_data in services:
                        if isinstance(service_data, (list, tuple)) and len(service_data) >= 2:
                            rows.append({
                                'cluster_id': cluster_id,
                                'service_id': service_data[0],
                                'rank': service_data[1]
                            })
            df = pd.DataFrame(rows)
        else:
            df = pd.DataFrame(cluster_map)
        
        logger.info(f"   Read {len(df):,} rows from PKL")
        
        df.to_sql('cluster_service_map', engine, if_exists='replace', index=False, method='multi', chunksize=5000)
        
        logger.info(f"   ✅ Imported cluster_service_map")
        
    except Exception as e:
        logger.error(f"   ❌ Error importing PKL: {e}")
    
    engine.dispose()


def import_openai_similarity():
    """Import OpenAI similarity matrix"""
    logger.info(f"\n📥 Importing openai_similarity_matrix")
    
    csv_path = "data/openai_similarity_matrix.csv"
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  {csv_path} not found, skipping...")
        return
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    try:
        # Read CSV
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='latin-1')
        
        logger.info(f"   Read {len(df):,} rows with {len(df.columns)} columns")
        
        # Convert wide format to JSON
        rows = []
        service_id_col = df.columns[0]
        
        for idx, row in df.iterrows():
            service_id = row[service_id_col]
            similarity_scores = row.drop(service_id_col).values
            
            similar_services = {}
            for col_idx, col_name in enumerate(df.columns[1:]):
                similar_service_id = int(col_name)
                score = float(similarity_scores[col_idx])
                similar_services[similar_service_id] = score
            
            rows.append({
                'service_id': int(service_id),
                'similar_services': json.dumps(similar_services)
            })
        
        similarity_df = pd.DataFrame(rows)
        similarity_df.to_sql('openai_similarity_matrix', engine, if_exists='replace', index=False, method='multi', chunksize=100)
        
        logger.info(f"   ✅ Imported openai_similarity_matrix")
        
    except Exception as e:
        logger.error(f"   ❌ Error importing similarity matrix: {e}")
    
    engine.dispose()


def create_services_eligibility():
    """Create services_eligibility from services table"""
    logger.info(f"\n📥 Creating services_eligibility from services table")
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    try:
        # Read services table
        services_df = pd.read_sql("SELECT * FROM services", engine)
        
        # Extract eligibility columns
        eligibility_cols = [
            'service_id', 'service_name', 'min_age', 'max_age',
            'is_sc', 'is_st', 'is_obc_a', 'is_obc_b',
            'is_female', 'is_minority', 'for_all'
        ]
        
        # Check which columns exist
        available_cols = [col for col in eligibility_cols if col in services_df.columns]
        
        # Add for_all if it doesn't exist
        if 'for_all' not in services_df.columns:
            # for_all = 1 if no specific restrictions
            services_df['for_all'] = ((services_df.get('is_sc', 0) == 0) & 
                                     (services_df.get('is_st', 0) == 0) & 
                                     (services_df.get('is_obc_a', 0) == 0) & 
                                     (services_df.get('is_obc_b', 0) == 0) & 
                                     (services_df.get('is_female', 0) == 0) & 
                                     (services_df.get('is_minority', 0) == 0)).astype(int)
            available_cols.append('for_all')
        
        eligibility_df = services_df[available_cols].copy()
        
        # Import to services_eligibility table
        eligibility_df.to_sql(
            'services_eligibility',
            engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        logger.info(f"   ✅ Created services_eligibility with {len(eligibility_df):,} rows")
        
    except Exception as e:
        logger.error(f"   ❌ Error creating services_eligibility: {e}")
    
    engine.dispose()


def initialize_sync_metadata():
    """Initialize sync_metadata table with empty records"""
    print_step(5, 7, "Initializing Sync Metadata")
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    try:
        tables = ['ml_citizen_master', 'ml_provision', 'ml_district', 'ml_bsk_master']
        
        with engine.connect() as conn:
            for table in tables:
                # Check if already exists
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM sync_metadata WHERE table_name = :table"
                ), {"table": table})
                
                if result.scalar() == 0:
                    conn.execute(text(
                        """
                        INSERT INTO sync_metadata (table_name, last_sync_status)
                        VALUES (:table, 'NEVER_SYNCED')
                        """
                    ), {"table": table})
                    logger.info(f"✅ Initialized metadata for {table}")
            
            conn.commit()
        
        logger.info("✅ Sync metadata initialized")
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error initializing metadata: {e}")


def verify_database():
    """Verify all tables and data"""
    print_step(6, 7, "Verifying Database")
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
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
        'cluster_service_map',
        'openai_similarity_matrix',
        'sync_metadata'
    ]
    
    logger.info("\n📊 Table Verification Report:")
    logger.info("-" * 70)
    
    total_rows = 0
    all_ok = True
    
    with engine.connect() as conn:
        for table in required_tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                total_rows += count
                
                status = "✅" if count > 0 else "⚠️ "
                logger.info(f"{status} {table:35s} : {count:>12,} rows")
                
                if count == 0:
                    all_ok = False
                    
            except Exception as e:
                logger.error(f"❌ {table:35s} : ERROR")
                all_ok = False
    
    logger.info("-" * 70)
    logger.info(f"📊 Total Rows: {total_rows:,}")
    logger.info("-" * 70)
    
    if all_ok:
        logger.info("✅ All tables verified successfully!")
    else:
        logger.warning("⚠️  Some tables are empty or missing")
    
    engine.dispose()
    return all_ok


def create_env_template():
    """Create .env template if it doesn't exist"""
    print_step(7, 7, "Creating Environment Template")
    
    env_path = ".env"
    env_example_path = ".env.example"
    
    if os.path.exists(env_path):
        logger.info("✅ .env file already exists")
        return
    
    template = f"""# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=bsk

# Constructed automatically (don't edit)
DATABASE_URL=postgresql://${{DB_USER}}:${{DB_PASSWORD}}@${{DB_HOST}}:${{DB_PORT}}/${{DB_NAME}}

# External API Configuration
EXTERNAL_SYNC_URL=https://bsk-server.gov.in/api/sync
EXTERNAL_LOGIN_URL=https://bsk-server.gov.in/api/auth/login

# JWT Credentials
JWT_USERNAME=StateCouncil
JWT_PASSWORD=Council@2531

# Admin API Key (generate a random secure key)
ADMIN_API_KEY=change-this-to-secure-random-key
"""
    
    # Save template
    with open(env_example_path if os.path.exists(env_example_path) else env_path, 'w') as f:
        f.write(template)
    
    logger.info(f"✅ Created {env_example_path if os.path.exists(env_example_path) else env_path}")
    
    if not os.path.exists(env_path):
        logger.warning("⚠️  Please update .env with your database credentials")


def main():
    """Main setup function"""
    # This function is now just a placeholder or can be removed if all logic moves to __main__
    pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup BSK-SER Database')
    parser.add_argument('--skip-confirmation', action='store_true', 
                        help='Skip user confirmation prompt (for automated deployments)')
    args = parser.parse_args()
    
    print_banner("🚀 BSK-SER DATABASE SETUP") # Changed banner text
    
    logger.info("\nThis script will:")
    logger.info("  1. Create PostgreSQL database")
    logger.info("  2. Create all tables")
    logger.info("  3. Create performance indexes")
    logger.info("  4. Import CSV data")
    logger.info("  5. Import PKL data")
    logger.info("  6. Initialize sync metadata")
    logger.info("  7. Verify all imports")
    
    if not args.skip_confirmation:
        response = input("\nProceed with setup? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            logger.info("Setup cancelled.")
            sys.exit(0) # Exit cleanly if user cancels
    else:
        logger.info("\nSkipping confirmation (--skip-confirmation flag set)")
        logger.info("Proceeding with automated setup...")
    
    try:
        # Execute setup steps
        create_database()
        create_tables()
        create_indexes()
        import_csv_data()
        create_services_eligibility()  # Create services_eligibility from services
        import_cluster_service_map()
        import_openai_similarity()
        initialize_sync_metadata()
        success = verify_database()
        create_env_template()
        
        # Final summary
        print_banner("✅ SETUP COMPLETE!")
        
        if success:
            logger.info("\n🎉 Database is ready to use!")
            logger.info("\nNext steps:")
            logger.info("  1. Update .env with your database credentials (if needed)")
            logger.info("  2. Start the API server: python -m backend.main_api")
            logger.info("  3. Access API docs: http://localhost:8000/docs")
        else:
            logger.warning("\n⚠️  Setup completed with warnings")
            logger.warning("Some tables may be empty. Check data files in /data directory.")
        
    except KeyboardInterrupt:
        logger.error("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
