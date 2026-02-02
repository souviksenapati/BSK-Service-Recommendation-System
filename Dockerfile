# ==============================================================================
# BSK-SER (Government Service Recommendation System) - Production Dockerfile
# ==============================================================================
# Multi-stage build with embedded initialization (no external entrypoint file)
# ==============================================================================

FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Production stage
# ==============================================================================
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY setup_database_complete.py /app/

# Create directories for logs and data
RUN mkdir -p /var/log/bsk-ser /app/data

# Create inline entrypoint script directly in Dockerfile
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "======================================================================"\n\
echo "BSK-SER API Server - Starting..."\n\
echo "======================================================================"\n\
echo ""\n\
echo "[1/3] Waiting for PostgreSQL..."\n\
\n\
max_attempts=30\n\
attempt=0\n\
while [ $attempt -lt $max_attempts ]; do\n\
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then\n\
        echo "      PostgreSQL is ready!"\n\
        break\n\
    fi\n\
    attempt=$((attempt + 1))\n\
    echo "      Waiting... (attempt $attempt/$max_attempts)"\n\
    sleep 2\n\
done\n\
\n\
if [ $attempt -eq $max_attempts ]; then\n\
    echo "ERROR: PostgreSQL timeout"\n\
    exit 1\n\
fi\n\
\n\
echo ""\n\
echo "[2/3] Checking database initialization..."\n\
MARKER_FILE="/app/data/.db_initialized"\n\
\n\
if [ -f "$MARKER_FILE" ]; then\n\
    echo "      Database already initialized - skipping setup"\n\
    echo "      Last initialized: $(cat $MARKER_FILE)"\n\
else\n\
    echo "      First run detected - initializing database..."\n\
    echo "      This will take 5-10 minutes (importing 117 MB data)"\n\
    echo ""\n\
    \n\
    python setup_database_complete.py --skip-confirmation || {\n\
        echo "ERROR: Database setup failed!"\n\
        exit 1\n\
    }\n\
    \n\
    date -u +"%Y-%m-%d %H:%M:%S UTC" > "$MARKER_FILE"\n\
    echo ""\n\
    echo "      Database setup complete!"\n\
fi\n\
\n\
echo ""\n\
echo "[3/3] Starting API Server..."\n\
echo ""\n\
echo "======================================================================"\n\
echo "  BSK-SER API Server Ready"\n\
echo "  - Server: http://0.0.0.0:8000"\n\
echo "  - API Docs: http://0.0.0.0:8000/docs"\n\
echo "  - Workers: 4 (Gunicorn + Uvicorn)"\n\
echo "======================================================================"\n\
echo ""\n\
\n\
exec "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import http.client; h = http.client.HTTPConnection('localhost:8000'); h.request('GET', '/api/admin/scheduler-status'); r = h.getresponse(); exit(0 if r.status == 200 else 1)"

# Set entrypoint (now created inline, always exists)
ENTRYPOINT ["/app/entrypoint.sh"]

# Run application with Gunicorn for production
CMD ["gunicorn", "backend.main_api:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--access-logfile", "/var/log/bsk-ser/access.log", \
     "--error-logfile", "/var/log/bsk-ser/error.log", \
     "--log-level", "info"]
