"""
Database configuration and connection management.
Provides flexible data loading with CSV-first, database-fallback strategy.
"""

import os
import pandas as pd
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/recomm_db')

# Table mappings for flexible data loading
TABLE_MAPPING = {
    'ml_citizen_master': 'ml_citizen_master',
    'ml_provision': 'ml_provision', 
    'ml_district': 'ml_district',
    'service_master': 'ml_service_master'
}

class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = None
        
    def get_engine(self):
        """Get or create SQLAlchemy engine."""
        if self.engine is None:
            try:
                self.engine = create_engine(self.database_url)
                logger.info("Database engine created successfully")
            except Exception as e:
                logger.error(f"Failed to create database engine: {e}")
                raise
        return self.engine
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

class DataLoader:
    """Flexible data loading with CSV-first, database-fallback strategy."""
    
    def __init__(self, data_dir: str = None, db_config: DatabaseConfig = None):
        self.data_dir = data_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
        self.db_config = db_config or DatabaseConfig()
        
    def load_from_csv(self, filename: str) -> Optional[pd.DataFrame]:
        """Load data from CSV file."""
        try:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, encoding="utf-8")
                logger.info(f"Successfully loaded {filename} from CSV ({len(df)} rows)")
                return df
            else:
                logger.warning(f"CSV file not found: {filepath}")
                return None
        except Exception as e:
            logger.error(f"Error loading CSV {filename}: {e}")
            return None
    
    def load_from_database(self, table_name: str, filename: str) -> Optional[pd.DataFrame]:
        """Load data from database table."""
        try:
            if not self.db_config.test_connection():
                logger.warning("Database connection failed, cannot load from database")
                return None
                
            engine = self.db_config.get_engine()
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, engine)
            logger.info(f"Successfully loaded {filename} from database table {table_name} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Error loading from database table {table_name}: {e}")
            return None
    
    def load_data_flexible(self, filename: str) -> Optional[pd.DataFrame]:
        """
        Load data with flexible strategy: CSV first, then database fallback.
        """
        # Try CSV first
        df = self.load_from_csv(filename)
        if df is not None:
            return df
        
        # Fallback to database if CSV not available
        csv_key = filename.replace('.csv', '')
        if csv_key in TABLE_MAPPING:
            table_name = TABLE_MAPPING[csv_key]
            logger.info(f"CSV not available for {filename}, trying database table {table_name}")
            df = self.load_from_database(table_name, filename)
            if df is not None:
                return df
        
        logger.error(f"Could not load {filename} from CSV or database")
        return None
    
    def check_data_availability(self) -> Dict[str, Dict[str, bool]]:
        """Check availability of all data sources."""
        availability = {}
        
        for csv_file, table_name in TABLE_MAPPING.items():
            csv_filename = f"{csv_file}.csv"
            availability[csv_file] = {
                'csv_available': os.path.exists(os.path.join(self.data_dir, csv_filename)),
                'database_available': False
            }
            
            # Check database availability
            try:
                if self.db_config.test_connection():
                    engine = self.db_config.get_engine()
                    with engine.connect() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.scalar()
                        availability[csv_file]['database_available'] = count > 0
            except Exception as e:
                logger.debug(f"Database check failed for {table_name}: {e}")
                availability[csv_file]['database_available'] = False
                
        return availability
    
    def get_data_status(self) -> str:
        """Get human-readable data status summary."""
        availability = self.check_data_availability()
        status_lines = []
        
        for csv_file, status in availability.items():
            csv_status = "✓" if status['csv_available'] else "✗"
            db_status = "✓" if status['database_available'] else "✗"
            status_lines.append(f"{csv_file}: CSV {csv_status} | Database {db_status}")
            
        return "\n".join(status_lines)

# Global data loader instance
data_loader = DataLoader()

def convert_database_to_csv():
    """
    Convert all database tables to CSV files.
    This is the main function you need for database-to-CSV conversion.
    """
    logger.info("Starting database to CSV conversion...")
    converted_files = []
    errors = []
    
    try:
        db_config = DatabaseConfig()
        if not db_config.test_connection():
            raise Exception("Cannot connect to database")
        
        engine = db_config.get_engine()
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        for csv_file, table_name in TABLE_MAPPING.items():
            try:
                logger.info(f"Converting {table_name} to {csv_file}.csv...")
                
                # Load data from database
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(query, engine)
                
                # Save to CSV
                csv_path = os.path.join(data_dir, f"{csv_file}.csv")
                df.to_csv(csv_path, index=False, encoding="utf-8")
                
                converted_files.append({
                    'table': table_name,
                    'csv_file': f"{csv_file}.csv", 
                    'rows': len(df),
                    'path': csv_path
                })
                logger.info(f"Successfully converted {table_name} -> {csv_file}.csv ({len(df)} rows)")
                
            except Exception as e:
                error_msg = f"Failed to convert {table_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Database to CSV conversion completed. {len(converted_files)} files converted, {len(errors)} errors")
        return {
            'status': 'completed',
            'converted_files': converted_files,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Database to CSV conversion failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'converted_files': converted_files,
            'errors': errors
        }

def batch_convert_with_validation():
    """
    Convert database to CSV with validation and backup.
    """
    logger.info("Starting batch conversion with validation...")
    
    # First, check what's available
    loader = DataLoader()
    availability = loader.check_data_availability()
    
    logger.info("Data availability check:")
    for csv_file, status in availability.items():
        logger.info(f"  {csv_file}: CSV={'Yes' if status['csv_available'] else 'No'}, DB={'Yes' if status['database_available'] else 'No'}")
    
    # Convert database to CSV
    result = convert_database_to_csv()
    
    # Validate converted files
    if result['status'] == 'completed':
        logger.info("Validating converted files...")
        for file_info in result['converted_files']:
            csv_path = file_info['path']
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    logger.info(f"Validation passed: {file_info['csv_file']} ({len(df)} rows)")
                except Exception as e:
                    logger.error(f"Validation failed: {file_info['csv_file']} - {e}")
    
    return result
