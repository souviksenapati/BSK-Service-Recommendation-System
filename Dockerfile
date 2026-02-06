# ============================================================================
# BSK-SER - Production Dockerfile for VPS Deployment
# ============================================================================
# Government Service Recommendation System
# Optimized for production VPS environment with PostgreSQL integration
# ============================================================================

FROM python:3.10-slim

# =============================================================================
# System dependencies
# =============================================================================
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    postgresql-client \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Create non-root user for security
# =============================================================================
RUN useradd -m -u 1000 appuser

# =============================================================================
# Set project directory
# =============================================================================
WORKDIR /home/bsk_ser

# =============================================================================
# Create virtualenv INSIDE the project directory
# =============================================================================
ENV VENV_PATH=/home/bsk_ser/venv

RUN python -m venv ${VENV_PATH}

# Always use the venv
ENV PATH="${VENV_PATH}/bin:$PATH"

# =============================================================================
# Install Python dependencies into the venv
# =============================================================================
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Copy application source
# =============================================================================
COPY backend/ /home/bsk_ser/backend/
COPY data/ /home/bsk_ser/data/
COPY setup_database_complete.py /home/bsk_ser/
COPY docker-entrypoint.sh /home/bsk_ser/

# =============================================================================
# Create required directories & permissions
# =============================================================================
RUN mkdir -p \
    /var/log/bsk-ser \
    /home/bsk_ser/data \
    && chmod +x /home/bsk_ser/docker-entrypoint.sh \
    && chown -R appuser:appuser /home/bsk_ser \
    && chown -R appuser:appuser /var/log/bsk-ser

# Switch to non-root user
USER appuser

# =============================================================================
# Environment variables
# =============================================================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/bsk_ser \
    PORT=8000

# =============================================================================
# Volumes for persistent data
# =============================================================================
VOLUME ["/home/bsk_ser/data", "/var/log/bsk-ser"]

# =============================================================================
# Healthcheck
# =============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/admin/scheduler-status || exit 1

# =============================================================================
# Expose & run
# =============================================================================
EXPOSE 8000

# Set entrypoint for database initialization
ENTRYPOINT ["/home/bsk_ser/docker-entrypoint.sh"]

# Run application with Gunicorn for production
CMD ["gunicorn", "backend.main_api:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--access-logfile", "/var/log/bsk-ser/access.log", \
     "--error-logfile", "/var/log/bsk-ser/error.log", \
     "--log-level", "info"]
