@echo off
echo Activating virtual environment...
call C:\Users\Soumyadeep\OneDrive\Desktop\py\preprocessing\venv\Scripts\activate.bat

echo Checking Python and pandas...
python -c "import sys; print('Python:', sys.executable)"
python -c "import pandas as pd; print('Pandas:', pd.__version__)"

echo Starting Streamlit...
streamlit run streamlit_app.py

pause
