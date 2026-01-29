"""
Database Table Availability Checker

This module checks if the required database tables exist before attempting
database operations, preventing NumPy and other errors by falling back to CSV mode.
"""

import os
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required database tables for the recommendation system
REQUIRED_TABLES = [
    'ml_citizen_master',
    'ml_district', 
    'ml_provision',
    'ml_service_master'
]

class DatabaseTableChecker:
    """Checks database table availability and manages fallback modes."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the database checker."""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.engine = None
        self._connection_tested = False
        self._connection_available = False
        self._tables_checked = False
        self._available_tables = []
        
    def test_database_connection(self) -> bool:
        """Test if database connection is available."""
        if self._connection_tested:
            return self._connection_available
            
        if not self.database_url:
            logger.warning("No DATABASE_URL provided - switching to CSV mode")
            self._connection_available = False
            self._connection_tested = True
            return False
            
        try:
            self.engine = create_engine(self.database_url)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✓ Database connection successful")
            self._connection_available = True
            
        except SQLAlchemyError as e:
            logger.warning(f"✗ Database connection failed: {e}")
            self._connection_available = False
            
        except Exception as e:
            logger.warning(f"✗ Unexpected database error: {e}")
            self._connection_available = False
            
        self._connection_tested = True
        return self._connection_available
    
    def check_required_tables(self) -> Dict[str, bool]:
        """Check if all required tables exist in the database."""
        if not self.test_database_connection():
            return {table: False for table in REQUIRED_TABLES}
            
        if self._tables_checked:
            return {table: table in self._available_tables for table in REQUIRED_TABLES}
            
        table_status = {}
        
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            for table in REQUIRED_TABLES:
                exists = table in existing_tables
                table_status[table] = exists
                
                if exists:
                    self._available_tables.append(table)
                    logger.info(f"✓ Table '{table}' found")
                else:
                    logger.warning(f"✗ Table '{table}' not found")
                    
        except Exception as e:
            logger.error(f"Error checking tables: {e}")
            return {table: False for table in REQUIRED_TABLES}
            
        self._tables_checked = True
        return table_status
    
    def get_missing_tables(self) -> List[str]:
        """Get list of missing required tables."""
        table_status = self.check_required_tables()
        return [table for table, exists in table_status.items() if not exists]
    
    def all_tables_available(self) -> bool:
        """Check if all required tables are available."""
        table_status = self.check_required_tables()
        return all(table_status.values())
    
    def get_availability_summary(self) -> Dict[str, any]:
        """Get comprehensive availability summary."""
        connection_ok = self.test_database_connection()
        table_status = self.check_required_tables()
        all_tables_ok = self.all_tables_available()
        missing_tables = self.get_missing_tables()
        
        return {
            "database_connection": connection_ok,
            "all_tables_available": all_tables_ok,
            "table_status": table_status,
            "missing_tables": missing_tables,
            "available_tables": self._available_tables,
            "recommendation": "database" if all_tables_ok else "csv_fallback",
            "can_use_database_conversion": connection_ok and len(self._available_tables) > 0
        }
    
    def should_use_database_mode(self) -> bool:
        """Determine if database mode should be used."""
        return self.all_tables_available()
    
    def should_use_csv_fallback(self) -> bool:
        """Determine if CSV fallback mode should be used."""
        return not self.all_tables_available()
    
    def get_operational_mode(self) -> str:
        """Get the recommended operational mode."""
        if self.should_use_database_mode():
            return "database"
        elif self.test_database_connection():
            return "hybrid"  # Some tables available
        else:
            return "csv_only"

# Global instance for the application
db_checker = DatabaseTableChecker()

def check_database_availability() -> Dict[str, any]:
    """
    Quick function to check database and table availability.
    Returns summary for use in application startup.
    """
    return db_checker.get_availability_summary()

def can_use_database_operations() -> bool:
    """
    Quick function to determine if database operations are available.
    Use this before attempting database-to-CSV conversions.
    """
    return db_checker.should_use_database_mode()

def should_skip_database_operations() -> bool:
    """
    Quick function to determine if database operations should be skipped.
    Use this to avoid NumPy and other errors by falling back to CSV.
    """
    return db_checker.should_use_csv_fallback()

def get_operational_mode() -> str:
    """
    Get the current operational mode for the application.
    Returns: 'database', 'hybrid', or 'csv_only'
    """
    return db_checker.get_operational_mode()

if __name__ == "__main__":
    """Test the database checker."""
    print("Testing Database Table Availability...")
    print("=" * 50)
    
    # Load environment variables for testing
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    checker = DatabaseTableChecker()
    summary = checker.get_availability_summary()
    
    print(f"Database Connection: {'✓' if summary['database_connection'] else '✗'}")
    print(f"All Tables Available: {'✓' if summary['all_tables_available'] else '✗'}")
    print(f"Operational Mode: {summary['recommendation'].upper()}")
    
    print("\nTable Status:")
    for table, status in summary['table_status'].items():
        print(f"  {table}: {'✓' if status else '✗'}")
    
    if summary['missing_tables']:
        print(f"\nMissing Tables: {', '.join(summary['missing_tables'])}")
    
    print(f"\nRecommendation: Use {summary['recommendation'].replace('_', ' ').title()} Mode")
