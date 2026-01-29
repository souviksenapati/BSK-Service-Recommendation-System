#!/bin/bash

echo "Starting Bangla Sahayata Kendra API Server..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r api/requirements.txt

# Start the server
echo ""
echo "Starting FastAPI server..."
echo "Access the application at: http://localhost:8000"
echo "API Documentation at: http://localhost:8000/docs"
echo ""

cd api
python main.py
