#!/usr/bin/env python3
"""
Script to run Streamlit with the correct virtual environment
"""
import sys
import os
import subprocess

# Get the virtual environment Python path
venv_python = r"C:\Users\Soumyadeep\OneDrive\Desktop\py\preprocessing\venv\python.exe"

# Check if we're using the correct Python
if sys.executable.lower() != venv_python.lower():
    print(f"⚠️  Wrong Python environment detected!")
    print(f"Current: {sys.executable}")
    print(f"Expected: {venv_python}")
    print(f"Switching to virtual environment...")
    
    # Run streamlit with the correct Python
    cmd = [venv_python, "-m", "streamlit", "run", "streamlit_app.py"]
    subprocess.run(cmd)
else:
    print(f"✅ Using correct Python environment: {sys.executable}")
    
    # Test imports
    try:
        import pandas as pd
        print(f"✅ Pandas {pd.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        sys.exit(1)
    
    try:
        import streamlit as st
        print(f"✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        sys.exit(1)
    
    # Run streamlit
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "streamlit_app.py"]
    stcli.main()
