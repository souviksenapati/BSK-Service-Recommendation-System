"""
Data utility functions for flexible loading.
Provides convenient functions to load data with CSV-first, database-fallback strategy.
"""

import pandas as pd
import logging
from typing import Optional
from backend.config.database import data_loader

logger = logging.getLogger(__name__)

def load_citizen_data() -> Optional[pd.DataFrame]:
    """Load citizen master data with flexible strategy."""
    return data_loader.load_data_flexible('ml_citizen_master.csv')

def load_provision_data() -> Optional[pd.DataFrame]:
    """Load provision data with flexible strategy."""
    return data_loader.load_data_flexible('ml_provision.csv')

def load_district_data() -> Optional[pd.DataFrame]:
    """Load district data with flexible strategy."""
    return data_loader.load_data_flexible('ml_district.csv')

def load_service_master_data() -> Optional[pd.DataFrame]:
    """Load service master data with flexible strategy."""
    return data_loader.load_data_flexible('service_master.csv')

def check_all_data_availability():
    """Check and log availability of all required data sources."""
    logger.info("Checking data availability...")
    status = data_loader.get_data_status()
    logger.info(f"Data availability status:\n{status}")
    return data_loader.check_data_availability()

def get_data_summary():
    """Get summary of all available data."""
    availability = check_all_data_availability()
    
    summary = {
        'total_sources': len(availability),
        'csv_available': sum(1 for status in availability.values() if status['csv_available']),
        'database_available': sum(1 for status in availability.values() if status['database_available']),
        'fully_available': sum(1 for status in availability.values() if status['csv_available'] or status['database_available'])
    }
    
    logger.info(f"Data summary: {summary['fully_available']}/{summary['total_sources']} sources available")
    return summary
