import os
import pandas as pd
import json
import pickle
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from backend.database.connection import engine
from backend.database.models import Base, District, BSKMaster, Provision, CitizenMaster, Service, ServiceEligibility, \
    GroupedDF, ClusterServiceMap, DistrictTopService, BlockTopService, OpenAISimilarity

# Load database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/bsk_db")

def create_tables():
    """Create all tables defined in models.py"""
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("✓ All tables created successfully")

def import_csv_data():
    """Import data from CSV files"""
    
    # Define CSV to table mappings
    # Format: (csv_filename, table_name, model_class, preprocessing_function)
    csv_mappings = [
        # Core tables
        ("ml_citizen_master.csv", "ml_citizen_master", CitizenMaster, None),
        ("ml_bsk_master.csv", "ml_bsk_master", BSKMaster, None),
        ("ml_district.csv", "ml_district", District, None),
        ("ml_provision.csv", "ml_provision", Provision, None),
        
        # Service tables
        ("services.csv", "services", Service, None),
        ("services_updated22.csv", "services_eligibility", ServiceEligibility, None),
        
        # Derived/aggregated tables (initially imported from CSV, can be regenerated via API)
        ("grouped_df.csv", "grouped_df", GroupedDF, None),
        ("district_top_services.csv", "district_top_services", DistrictTopService, None),
        ("block_wise_top_services.csv", "block_wise_top_services", BlockTopService, None),
    ]
    
    data_dir = "data"
    
    for csv_file, table_name, model, preprocess_fn in csv_mappings:
        csv_path = os.path.join(data_dir, csv_file)
        
        if not os.path.exists(csv_path):
            print(f"⚠ Warning: {csv_path} not found, skipping...")
            continue
            
        print(f"\n📥 Importing {csv_file} into {table_name}...")
        
        try:
            # Read CSV with proper encoding handling
            try:
                df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
            except UnicodeDecodeError:
                print(f"  ⚠ UTF-8 failed, trying latin-1 encoding...")
                df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
            
            print(f"  Read {len(df)} rows with {len(df.columns)} columns from CSV")
            
            # Apply preprocessing if needed
            if preprocess_fn:
                df = preprocess_fn(df)
            
            # Clean column names (make them SQL-safe)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
            
            # Import ALL columns directly - no filtering
            print(f"  💾 Writing {len(df.columns)} columns to database...")
            df.to_sql(
                table_name,
                engine,
                if_exists='replace',
                index=False,
                method='multi',
                chunksize=1000
            )
            
            print(f"  ✓ Successfully imported {len(df)} rows into {table_name}")
            
        except Exception as e:
            print(f"  ✗ Error importing {csv_file}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

def import_cluster_service_map():
    """Import cluster_service_map from PKL file"""
    pkl_path = "data/cluster_service_map.pkl"
    
    if not os.path.exists(pkl_path):
        print(f"\n⚠ Warning: {pkl_path} not found, skipping cluster_service_map import...")
        return
    
    print(f"\n📥 Importing cluster_service_map from PKL file...")
    
    try:
        # Load pickle file
        print(f"  📦 Loading PKL file...")
        with open(pkl_path, 'rb') as f:
            cluster_map = pickle.load(f)
        
        # Convert to DataFrame
        # Expected format: dict with cluster_id as key, list of (service_id, rank, usage_count) tuples as value
        # OR DataFrame already
        
        if isinstance(cluster_map, dict):
            print(f"  🔄 Converting dict to DataFrame...")
            rows = []
            for cluster_id, services in cluster_map.items():
                if isinstance(services, list):
                    for service_data in services:
                        if isinstance(service_data, (list, tuple)) and len(service_data) >= 2:
                            rows.append({
                                'cluster_id': cluster_id,
                                'service_id': service_data[0],
                                'rank': service_data[1] if len(service_data) > 1 else None,
                                'usage_count': service_data[2] if len(service_data) > 2 else None
                            })
            df = pd.DataFrame(rows)
        elif isinstance(cluster_map, pd.DataFrame):
            df = cluster_map
        else:
            print(f"  ✗ Unexpected format for cluster_service_map.pkl: {type(cluster_map)}")
            return
        
        print(f"  Read {len(df)} rows from PKL")
        
        # Import to database
        print(f"  💾 Writing to database...")
        df.to_sql(
            'cluster_service_map',
            engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        print(f"  ✓ Successfully imported {len(df)} rows into cluster_service_map")
        
    except Exception as e:
        print(f"  ✗ Error importing cluster_service_map.pkl: {str(e)}")

def import_openai_similarity_matrix():
    """Import OpenAI similarity matrix from CSV with special handling for wide format"""
    csv_path = "data/openai_similarity_matrix.csv"
    
    if not os.path.exists(csv_path):
        print(f"\n⚠ Warning: {csv_path} not found, skipping similarity matrix import...")
        return
    
    print(f"\n📥 Importing openai_similarity_matrix (wide format)...")
    
    try:
        # Read CSV with encoding handling
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            print(f"  ⚠ UTF-8 failed, trying latin-1 encoding...")
            df = pd.read_csv(csv_path, encoding='latin-1')
        
        print(f"  Read {len(df)} rows with {len(df.columns)} columns")
        
        # The CSV format is: service_id, 0, 1, 2, ..., N
        # where each row represents similarity scores for that service_id to all other services
        
        # Convert wide format to narrow format: store top N similar services per service_id
        rows = []
        
        # Get service IDs from first column
        service_id_col = df.columns[0]
        
        print(f"  🔄 Converting wide format to JSON...")
        for idx, row in df.iterrows():
            service_id = row[service_id_col]
            
            # Get all similarity scores (excluding the service_id column)
            similarity_scores = row.drop(service_id_col).values
            
            # Create a dict of {similar_service_id: score}
            # Columns are named 0, 1, 2, ..., N representing service IDs
            similar_services = {}
            for col_idx, col_name in enumerate(df.columns[1:]):
                # Column name is the similar service ID
                similar_service_id = int(col_name)
                score = float(similarity_scores[col_idx])
                similar_services[similar_service_id] = score
            
            # Store as JSON string in the database
            rows.append({
                'service_id': int(service_id),
                'similar_services': json.dumps(similar_services)
            })
        
        similarity_df = pd.DataFrame(rows)
        
        # Import to database
        print(f"  💾 Writing to database...")
        similarity_df.to_sql(
            'openai_similarity_matrix',
            engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=100
        )
        
        print(f"  ✓ Successfully imported {len(similarity_df)} service similarity records")
        
    except Exception as e:
        print(f"  ✗ Error importing openai_similarity_matrix.csv: {str(e)}")


def verify_imports():
    """Verify that data was imported correctly"""
    
    print("\n" + "="*60)
    print("📊 VERIFICATION REPORT")
    print("="*60)
    
    tables_to_check = [
        'ml_citizen_master',
        'ml_bsk_master',
        'ml_district',
        'ml_provision',
        'services',
        'services_eligibility',
        'grouped_df',
        'cluster_service_map',
        'district_top_services',
        'block_wise_top_services',
        'openai_similarity_matrix'
    ]
    
    with engine.connect() as conn:
        for table in tables_to_check:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                status = "✓" if count > 0 else "⚠"
                print(f"{status} {table:30s} : {count:>8,} rows")
            except Exception as e:
                print(f"✗ {table:30s} : ERROR - {str(e)}")
    
    print("="*60)


def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🚀 BSK-SER DATABASE SETUP")
    print("="*60)
    
    print("\nSelect an option:")
    print("1. Create tables only")
    print("2. Import data only")
    print("3. Create tables AND import data (recommended for first run)")
    print("4. Verify imports")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        create_tables()
    elif choice == "2":
        import_csv_data()
        import_cluster_service_map()
        import_openai_similarity_matrix()
    elif choice == "3":
        create_tables()
        import_csv_data()
        import_cluster_service_map()
        import_openai_similarity_matrix()
        verify_imports()
    elif choice == "4":
        verify_imports()
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\n✅ Setup complete!")


if __name__ == "__main__":
    main()
