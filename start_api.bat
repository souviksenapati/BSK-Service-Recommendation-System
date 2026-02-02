@echo off
REM ==============================================================================
REM BSK-SER API Startup Script (Windows)
REM ==============================================================================
REM This script handles first-time setup and subsequent starts
REM ==============================================================================

setlocal enabledelayedexpansion

echo.
echo ======================================================================
echo   BSK-SER (Government Service Recommendation System)
echo   Starting API Server...
echo ======================================================================
echo.

cd /d "%~dp0"

REM ------------------------------------------------------------------------------
REM Step 1: Check/Activate Virtual Environment
REM ------------------------------------------------------------------------------
if not exist "venv\" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo       Virtual environment created successfully
) else (
    echo [1/5] Virtual environment found
)

echo       Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM ------------------------------------------------------------------------------
REM Step 2: Install/Update Dependencies
REM ------------------------------------------------------------------------------
echo.
echo [2/5] Checking dependencies...

REM Check if this is first run by looking for a marker file
if not exist "venv\.dependencies_installed" (
    echo       Installing dependencies (this may take a few minutes)...
    pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo       Dependencies installed > venv\.dependencies_installed
    echo       Dependencies installed successfully
) else (
    echo       Dependencies already installed (use 'pip install -r requirements.txt' to update)
)

REM ------------------------------------------------------------------------------
REM Step 3: Check Environment Configuration
REM ------------------------------------------------------------------------------
echo.
echo [3/5] Checking environment configuration...

if not exist ".env" (
    echo       WARNING: .env file not found!
    echo       Creating from .env.example...
    if exist ".env.example" (
        copy .env.example .env > nul
        echo.
        echo       ============================================================
        echo       IMPORTANT: Please edit .env file with your credentials:
        echo       - DB_PASSWORD
        echo       - ADMIN_API_KEY
        echo       - SECRET_KEY
        echo       ============================================================
        echo.
        echo       Press any key after editing .env file...
        pause > nul
    ) else (
        echo       ERROR: .env.example not found!
        echo       Please create .env file manually
        pause
        exit /b 1
    )
) else (
    echo       Environment configuration found
)

REM ------------------------------------------------------------------------------
REM Step 4: Database Setup (First Run Only)
REM ------------------------------------------------------------------------------
echo.
echo [4/5] Checking database setup...

if not exist "venv\.database_setup_complete" (
    echo       Database not initialized. Running setup...
    echo.
    echo       ============================================================
    echo       This will create the database and import all data.
    echo       Make sure PostgreSQL is running and .env is configured!
    echo       ============================================================
    echo.
    choice /C YN /M "       Run database setup now"
    if errorlevel 2 (
        echo       Skipping database setup. You can run it manually:
        echo       python setup_database_complete.py
    ) else (
        python setup_database_complete.py
        if errorlevel 1 (
            echo.
            echo       ERROR: Database setup failed!
            echo       Please check your database credentials in .env
            echo       and ensure PostgreSQL is running.
            pause
            exit /b 1
        )
        echo       Database setup complete > venv\.database_setup_complete
    )
) else (
    echo       Database already initialized
)

REM ------------------------------------------------------------------------------
REM Step 5: Start API Server
REM ------------------------------------------------------------------------------
echo.
echo [5/5] Starting API server...
echo.
echo ======================================================================
echo   Server starting on http://localhost:8000
echo   API Documentation: http://localhost:8000/docs
echo   Admin Panel: http://localhost:8000/api/admin/scheduler-status
echo ======================================================================
echo.
echo Press Ctrl+C to stop the server
echo.

python -m backend.main_api

REM ------------------------------------------------------------------------------
REM Cleanup on Exit
REM ------------------------------------------------------------------------------
if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start!
    echo Check the error messages above.
    pause
)

endlocal
