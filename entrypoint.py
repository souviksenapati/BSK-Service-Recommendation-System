#!/usr/bin/env python3
"""
BSK-SER Docker Entrypoint Script
Auto-initializes database on first run, then starts API server
"""
import subprocess
import sys
import time
import os
from datetime import datetime

print("=" * 70)
print("BSK-SER API Server - Starting...")
print("=" * 70)
print()

# [1/3] Wait for PostgreSQL
print("[1/3] Waiting for PostgreSQL...")
max_attempts = 30
for attempt in range(1, max_attempts + 1):
    result = subprocess.run(
        ["pg_isready", "-h", os.getenv("DB_HOST"), "-p", os.getenv("DB_PORT"), "-U", os.getenv("DB_USER")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode == 0:
        print("      PostgreSQL is ready!")
        break
    print(f"      Waiting... (attempt {attempt}/{max_attempts})")
    time.sleep(2)
else:
    print("ERROR: PostgreSQL timeout")
    sys.exit(1)

print()

# [2/3] Database initialization
print("[2/3] Checking database initialization...")
marker_file = "/app/data/.db_initialized"

if os.path.exists(marker_file):
    print("      Database already initialized - skipping setup")
    with open(marker_file) as f:
        print(f"      Last initialized: {f.read().strip()}")
else:
    print("      First run detected - initializing database...")
    print("      This will take 5-10 minutes (importing 117 MB data)")
    print()
    
    result = subprocess.run(["python", "setup_database_complete.py", "--skip-confirmation"])
    if result.returncode != 0:
        print("ERROR: Database setup failed!")
        sys.exit(1)
    
    with open(marker_file, "w") as f:
        f.write(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    
    print()
    print("      Database setup complete!")

print()

# [3/3] Start API Server
print("[3/3] Starting API Server...")
print()
print("=" * 70)
print("  BSK-SER API Server Ready")
print("  - Server: http://0.0.0.0:8000")
print("  - API Docs: http://0.0.0.0:8000/docs")
print("  - Workers: 4 (Gunicorn + Uvicorn)")
print("=" * 70)
print()

# Execute the command passed to the entrypoint
os.execvp(sys.argv[1], sys.argv[1:])
