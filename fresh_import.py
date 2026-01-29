"""
Fresh database import from D:\Projects\Data
Drops all existing tables and imports all required CSVs directly
"""
import os
import pandas as pd
import json
import pickle
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Database connection
DEFAULT_DB_URL = 'postgresql://postgres:Souvik%402004%23@localhost:5432/bsk'
DATABASE_URL = os.getenv('DATABASE_URL', DEFAULT_DB_URL)
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)

# Source data directory
DATA_DIR = r"D:\Projects\Data"

def drop_all_tables():
    """Drop all existing tables in the database"""
    print("\n🗑️  Dropping all existing tables...")
    
    with engine.connect() as conn:
        # Get all tables
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        tables = [row[0] for row in result]
        
        if not tables:
            print("  ℹ️  No tables found")
            return
        
        print(f"  Found {len(tables)} tables: {', '.join(tables)}")
        
        # Drop all tables with CASCADE
        for table in tables:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                conn.commit()
                print(f"  ✓ Dropped {table}")
            except Exception as e:
                print(f"  ✗ Error dropping {table}: {e}")
        
        print("  ✅ All tables dropped successfully")


def import_csv_to_postgres(csv_file, table_name, chunksize=10000):
    """Import CSV file directly to PostgreSQL"""
    csv_path = os.path.join(DATA_DIR, csv_file)
    
    if not os.path.exists(csv_path):
        print(f"  ⚠️  {csv_file} not found, skipping...")
        return False
    
    print(f"\n📥 Importing {csv_file} → {table_name}")
    file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    print(f"  📦 File size: {file_size_mb:.1f} MB")
    
    try:
        # Read CSV with encoding handling
        print(f"  📖 Reading CSV...")
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            print(f"  ⚠️  UTF-8 failed, trying latin-1...")
            df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
        
        print(f"  ✓ Read {len(df):,} rows × {len(df.columns)} columns")
        
        # Clean column names (SQL-safe)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
        
        # Import to database in chunks
        print(f"  💾 Writing to PostgreSQL (chunks of {chunksize:,})...")
        
        for i, start_idx in enumerate(range(0, len(df), chunksize)):
            chunk = df.iloc[start_idx:start_idx + chunksize]
            chunk.to_sql(
                table_name,
                engine,
                if_exists='append' if i > 0 else 'replace',
                index=False,
                method='multi'
            )
            print(f"  ⏳ Progress: {min(start_idx + chunksize, len(df)):,}/{len(df):,} rows", end='\r')
        
        print(f"\n  ✅ Successfully imported {len(df):,} rows into {table_name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def import_all_tables():
    """Import all required tables"""
    
    # Define import order (core tables first, then derived)
    imports = [
        # Core master data
        ("ml_bsk_master.csv", "ml_bsk_master", 5000),
        ("merged_citizen_master.csv", "ml_citizen_master", 10000),  # Large file
        ("merged_ml_provision.csv", "ml_provision", 10000),  # Very large file
        
        # Service data
        ("services_updated22.csv", "services_eligibility", 5000),
        
        # Derived/aggregated data
        ("grouped_df.csv", "grouped_df", 5000),
        ("district_top_services.csv", "district_top_services", 5000),
        ("block_wise_top_services.csv", "block_wise_top_services", 5000),
        
        # AI/ML data
        ("openai_similarity_matrix.csv", "openai_similarity_matrix", 1000),
    ]
    
    success_count = 0
    for csv_file, table_name, chunk_size in imports:
        if import_csv_to_postgres(csv_file, table_name, chunk_size):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Import completed: {success_count}/{len(imports)} tables")
    print(f"{'='*60}")


def verify_imports():
    """Verify imported data"""
    print(f"\n{'='*60}")
    print("📊 VERIFICATION REPORT")
    print(f"{'='*60}")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
        for table in tables:
            try:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                status = "✅" if count > 0 else "⚠️"
                print(f"{status} {table:35s} : {count:>12,} rows")
            except Exception as e:
                print(f"❌ {table:35s} : ERROR - {str(e)}")
    
    print(f"{'='*60}")


def main():
    print("\n" + "="*60)
    print("🚀 FRESH DATABASE IMPORT FROM D:\\Projects\\Data")
    print("="*60)
    
    response = input("\n⚠️  This will DROP ALL existing tables. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Import cancelled")
        return
    
    # Step 1: Drop all tables
    drop_all_tables()
    
    # Step 2: Import all CSVs
    import_all_tables()
    
    # Step 3: Verify
    verify_imports()
    
    print("\n✅ Fresh import complete!")


if __name__ == "__main__":
    main()
