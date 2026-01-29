# Docker deployment for Bangla Sahayata Kendra API
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY api/requirements.txt /app/api/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Copy application code
COPY . /app/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
