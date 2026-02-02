#!/bin/bash
# ==============================================================================
# BSK-SER Docker Entrypoint Script
# ==============================================================================
# Handles automatic database initialization on first run
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
echo -e "${BLUE}BSK-SER API Server - Docker Container Starting...${NC}"
echo "======================================================================"
echo ""

# ------------------------------------------------------------------------------
# Wait for PostgreSQL to be ready
# ------------------------------------------------------------------------------
echo -e "${BLUE}[1/3] Waiting for PostgreSQL to be ready...${NC}"

max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}      PostgreSQL is ready!${NC}"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "      Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}ERROR: PostgreSQL did not become ready in time${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Check if database needs initialization
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/3] Checking database initialization status...${NC}"

# Use a marker file in a persistent volume to track initialization
MARKER_FILE="/app/data/.db_initialized"

if [ -f "$MARKER_FILE" ]; then
    echo -e "${GREEN}      Database already initialized - skipping setup${NC}"
    echo "      Last initialized: $(cat $MARKER_FILE)"
else
    echo -e "${YELLOW}      First run detected - initializing database...${NC}"
    echo ""
    echo "======================================================================"
    echo "  Database Setup Starting"
    echo "  This will take 5-10 minutes to import all data (117 MB)"
    echo "======================================================================"
    echo ""
    
    # Run the database setup script
    python setup_database_complete.py --skip-confirmation || {
        echo -e "${RED}ERROR: Database setup failed!${NC}"
        exit 1
    }
    
    # Create marker file with timestamp
    echo "$(date -u +"%Y-%m-%d %H:%M:%S UTC")" > "$MARKER_FILE"
    
    echo ""
    echo "======================================================================"
    echo -e "${GREEN}  Database Setup Complete!${NC}"
    echo "======================================================================"
    echo ""
fi

# ------------------------------------------------------------------------------
# Start the API Server
# ------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/3] Starting API Server...${NC}"
echo ""
echo "======================================================================"
echo -e "${GREEN}  BSK-SER API Server${NC}"
echo "  - Server: http://0.0.0.0:8000"
echo "  - API Docs: http://0.0.0.0:8000/docs"
echo "  - Admin Panel: http://0.0.0.0:8000/api/admin/scheduler-status"
echo "  - Workers: 4 (Gunicorn + Uvicorn)"
echo "======================================================================"
echo ""

# Execute the main command (Gunicorn)
exec "$@"
