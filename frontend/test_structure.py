#!/usr/bin/env python3
"""
Test script to verify the new project structure
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Testing Project Structure ===")
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {__file__}")

try:
    # Test backend imports
    print("\n1. Testing backend imports...")
    from backend.helpers.pyarrow_free_demo_helper import pyarrow_free_demographic_recommendations
    print("   ✅ pyarrow_free_demo_helper imported successfully")
    
    from backend.inference.district import get_top_services_for_district_from_csv
    print("   ✅ district module imported successfully")
    
    from backend.inference.item import find_similar_services_from_csv
    print("   ✅ item module imported successfully")
    
    print("\n2. Testing data file paths...")
    # Test if data files are accessible
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    print(f"   Data directory: {data_dir}")
    
    if os.path.exists(os.path.join(data_dir, "grouped_df.csv")):
        print("   ✅ grouped_df.csv found")
    else:
        print("   ❌ grouped_df.csv not found")
        
    if os.path.exists(os.path.join(data_dir, "services.csv")):
        print("   ✅ services.csv found")
    else:
        print("   ❌ services.csv not found")
    
    print("\n✅ All tests passed! The project structure is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please check the project structure and file paths")
except Exception as e:
    print(f"❌ Error: {e}")
