@echo off
echo Starting Bangla Sahayata Kendra API Server...
echo.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update dependencies
echo Installing dependencies...
pip install -r api\requirements.txt

REM Start the server
echo.
echo Starting FastAPI server...
echo Access the application at: http://localhost:8000
echo API Documentation at: http://localhost:8000/docs
echo.

cd api
python main.py

pause
