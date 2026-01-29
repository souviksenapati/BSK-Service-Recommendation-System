#!/usr/bin/env python3
"""
Test script to verify streamlit app dependencies are working
"""
import sys
import os

# Add parent directory to path for backend imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Testing Streamlit App Dependencies ===")

# Test 1: Basic imports
try:
    import streamlit as st
    print("✅ Streamlit import successful")
except ImportError as e:
    print(f"❌ Streamlit import failed: {e}")

try:
    import pandas as pd
    print("✅ Pandas import successful")
except ImportError as e:
    print(f"❌ Pandas import failed: {e}")

# Test 2: Backend imports
try:
    from backend.inference.district import get_top_services_for_district_from_csv
    print("✅ Backend district import successful")
except ImportError as e:
    print(f"❌ Backend district import failed: {e}")

try:
    from backend.inference.item import find_similar_services_from_csv
    print("✅ Backend item import successful")
except ImportError as e:
    print(f"❌ Backend item import failed: {e}")

try:
    from backend.inference.demo import recommend_services_2
    print("✅ Backend demo import successful")
except ImportError as e:
    print(f"❌ Backend demo import failed: {e}")

# Test 3: Data file access
data_files = [
    "../data/grouped_df.csv",
    "../data/services.csv", 
    "../data/final_df.csv",
    "../data/cluster_service_map.pkl",
    "../data/service_id_with_name.csv",
    "../data/ml_citizen_master.csv",
    "../data/ml_provision.csv",
    "../data/district_top_services.csv"
]

print("\n=== Testing Data File Access ===")
for file_path in data_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path} exists")
    else:
        print(f"❌ {file_path} missing")

# Test 4: Loading data files
try:
    grouped_df = pd.read_csv("../data/grouped_df.csv", encoding="utf-8")
    print(f"✅ Loaded grouped_df: {grouped_df.shape}")
except Exception as e:
    print(f"❌ Failed to load grouped_df: {e}")

try:
    service_df = pd.read_csv("../data/services.csv", encoding="utf-8")
    print(f"✅ Loaded service_df: {service_df.shape}")
except Exception as e:
    print(f"❌ Failed to load service_df: {e}")

try:
    final_df = pd.read_csv("../data/final_df.csv", encoding="utf-8")
    print(f"✅ Loaded final_df: {final_df.shape}")
except Exception as e:
    print(f"❌ Failed to load final_df: {e}")

try:
    import pickle
    with open("../data/cluster_service_map.pkl", "rb") as f:
        cluster_service_map = pickle.load(f)
    print(f"✅ Loaded cluster_service_map: {len(cluster_service_map)} clusters")
except Exception as e:
    print(f"❌ Failed to load cluster_service_map: {e}")

print("\n=== All Tests Complete ===")
print("If all tests pass, the streamlit app should run successfully!")
