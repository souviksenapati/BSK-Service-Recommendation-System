# ==============================================================================
# BSK-SER Production Dockerfile - Python Entrypoint (Cross-Platform)
# ==============================================================================

FROM python:3.10-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Production stage
# ==============================================================================
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY setup_database_complete.py /app/

# Create directories
RUN mkdir -p /var/log/bsk-ser /app/data

# Create Python-based entrypoint (no bash, no line-ending issues!)
RUN python3 -c "import sys; sys.stdout.write('''#!/usr/bin/env python3
import subprocess
import sys
import time
import os
from datetime import datetime

print(\"=\"*70)
print(\"BSK-SER API Server - Starting...\")
print(\"=\"*70)
print()

# [1/3] Wait for PostgreSQL
print(\"[1/3] Waiting for PostgreSQL...\")
max_attempts = 30
for attempt in range(1, max_attempts + 1):
    result = subprocess.run(
        [\"pg_isready\", \"-h\", os.getenv(\"DB_HOST\"), \"-p\", os.getenv(\"DB_PORT\"), \"-U\", os.getenv(\"DB_USER\")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode == 0:
        print(\"      PostgreSQL is ready!\")
        break
    print(f\"      Waiting... (attempt {attempt}/{max_attempts})\")
    time.sleep(2)
else:
    print(\"ERROR: PostgreSQL timeout\")
    sys.exit(1)

print()

# [2/3] Database initialization
print(\"[2/3] Checking database initialization...\")
marker_file = \"/app/data/.db_initialized\"

if os.path.exists(marker_file):
    print(\"      Database already initialized - skipping setup\")
    with open(marker_file) as f:
        print(f\"      Last initialized: {f.read().strip()}\")
else:
    print(\"      First run detected - initializing database...\")
    print(\"      This will take 5-10 minutes (importing 117 MB data)\")
    print()
    
    result = subprocess.run([\"python\", \"setup_database_complete.py\", \"--skip-confirmation\"])
    if result.returncode != 0:
        print(\"ERROR: Database setup failed!\")
        sys.exit(1)
    
    with open(marker_file, \"w\") as f:
        f.write(datetime.utcnow().strftime(\"%Y-%m-%d %H:%M:%S UTC\"))
    
    print()
    print(\"      Database setup complete!\")

print()

# [3/3] Start API Server
print(\"[3/3] Starting API Server...\")
print()
print(\"=\"*70)
print(\"  BSK-SER API Server Ready\")
print(\"  - Server: http://0.0.0.0:8000\")
print(\"  - API Docs: http://0.0.0.0:8000/docs\")
print(\"  - Workers: 4 (Gunicorn + Uvicorn)\")
print(\"=\"*70)
print()

# Execute the command passed to the entrypoint
os.execvp(sys.argv[1], sys.argv[1:])
''')" > /app/entrypoint.py && chmod +x /app/entrypoint.py

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import http.client; h = http.client.HTTPConnection('localhost:8000'); h.request('GET', '/api/admin/scheduler-status'); r = h.getresponse(); exit(0 if r.status == 200 else 1)"

# Use Python entrypoint (works on all platforms!)
ENTRYPOINT ["python3", "/app/entrypoint.py"]

CMD ["gunicorn", "backend.main_api:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--access-logfile", "/var/log/bsk-ser/access.log", \
     "--error-logfile", "/var/log/bsk-ser/error.log", \
     "--log-level", "info"]
