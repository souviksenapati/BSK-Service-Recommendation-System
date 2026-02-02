#!/bin/bash
# ==============================================================================
# BSK-SER API Startup Script (Linux/Mac)
# ==============================================================================
# This script handles first-time setup and subsequent starts
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "======================================================================"
echo "  BSK-SER (Government Service Recommendation System)"
echo "  Starting API Server..."
echo "======================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# Step 1: Check/Activate Virtual Environment
# ------------------------------------------------------------------------------
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[1/5] Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}      Virtual environment created successfully${NC}"
else
    echo -e "${BLUE}[1/5] Virtual environment found${NC}"
fi

echo "      Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to activate virtual environment${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Step 2: Install/Update Dependencies
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/5] Checking dependencies...${NC}"

# Check if this is first run
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "      Installing dependencies (this may take a few minutes)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to install dependencies${NC}"
        exit 1
    fi
    touch venv/.dependencies_installed
    echo -e "${GREEN}      Dependencies installed successfully${NC}"
else
    echo "      Dependencies already installed (run 'pip install -r requirements.txt' to update)"
fi

# ------------------------------------------------------------------------------
# Step 3: Check Environment Configuration
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/5] Checking environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}      WARNING: .env file not found!${NC}"
    if [ -f ".env.example" ]; then
        echo "      Creating from .env.example..."
        cp .env.example .env
        echo ""
        echo "      ============================================================"
        echo -e "${YELLOW}      IMPORTANT: Please edit .env file with your credentials:${NC}"
        echo "      - DB_PASSWORD"
        echo "      - ADMIN_API_KEY"
        echo "      - SECRET_KEY"
        echo "      ============================================================"
        echo ""
        read -p "      Press Enter after editing .env file..."
    else
        echo -e "${RED}      ERROR: .env.example not found!${NC}"
        echo "      Please create .env file manually"
        exit 1
    fi
else
    echo "      Environment configuration found"
fi

# ------------------------------------------------------------------------------
# Step 4: Database Setup (First Run Only)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/5] Checking database setup...${NC}"

if [ ! -f "venv/.database_setup_complete" ]; then
    echo "      Database not initialized. Running setup..."
    echo ""
    echo "      ============================================================"
    echo "      This will create the database and import all data."
    echo "      Make sure PostgreSQL is running and .env is configured!"
    echo "      ============================================================"
    echo ""
    read -p "      Run database setup now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python setup_database_complete.py
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${RED}      ERROR: Database setup failed!${NC}"
            echo "      Please check your database credentials in .env"
            echo "      and ensure PostgreSQL is running."
            exit 1
        fi
        touch venv/.database_setup_complete
    else
        echo "      Skipping database setup. You can run it manually:"
        echo "      python setup_database_complete.py"
    fi
else
    echo "      Database already initialized"
fi

# ------------------------------------------------------------------------------
# Step 5: Start API Server
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/5] Starting API server...${NC}"
echo ""
echo "======================================================================"
echo -e "${GREEN}  Server starting on http://localhost:8000${NC}"
echo "  API Documentation: http://localhost:8000/docs"
echo "  Admin Panel: http://localhost:8000/api/admin/scheduler-status"
echo "======================================================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m backend.main_api

# ------------------------------------------------------------------------------
# Cleanup on Exit
# ------------------------------------------------------------------------------
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Server failed to start!${NC}"
    echo "Check the error messages above."
    exit 1
fi
