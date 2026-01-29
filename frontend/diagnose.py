#!/usr/bin/env python3
"""
Diagnostic script to check Python environment and pandas installation
"""
import sys
import os

print("=== Python Environment Diagnostic ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[:3]}...")

print("\n=== Checking pandas installation ===")
try:
    import pandas as pd
    print(f"✅ Pandas {pd.__version__} found at: {pd.__file__}")
except ImportError as e:
    print(f"❌ Pandas not found: {e}")
    print("Installing pandas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])

print("\n=== Checking streamlit installation ===")
try:
    import streamlit as st
    print(f"✅ Streamlit found")
except ImportError as e:
    print(f"❌ Streamlit not found: {e}")
    print("Installing streamlit...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

print("\n=== Testing streamlit app imports ===")
try:
    # Test the actual imports from streamlit_app.py
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.inference.district import get_top_services_for_district_from_csv
    from backend.inference.item import find_similar_services_from_csv
    from backend.inference.demo import recommend_services_2
    print("✅ All backend imports successful")
except Exception as e:
    print(f"❌ Backend imports failed: {e}")

print("\n=== Testing data files ===")
data_files = [
    "../data/grouped_df.csv",
    "../data/services.csv",
    "../data/final_df.csv"
]

for file_path in data_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path} exists")
    else:
        print(f"❌ {file_path} missing")

print("\n=== Environment Summary ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
print("To run streamlit, use:")
print(f"  {sys.executable} -m streamlit run streamlit_app.py")
