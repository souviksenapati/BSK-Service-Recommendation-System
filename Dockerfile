# ==============================================================================
# BSK-SER (Government Service Recommendation System) - Production Dockerfile
# ==============================================================================
# Multi-stage build for optimized production image
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

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import http.client; h = http.client.HTTPConnection('localhost:8000'); h.request('GET', '/api/admin/scheduler-status'); r = h.getresponse(); exit(0 if r.status == 200 else 1)"

# Run application with Gunicorn for production
CMD ["gunicorn", "backend.main_api:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--access-logfile", "/var/log/bsk-ser/access.log", \
     "--error-logfile", "/var/log/bsk-ser/error.log", \
     "--log-level", "info"]
