# ==============================================================================
# BSK-SER Docker Deployment Guide
# ==============================================================================

## Quick Start

### 1. Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 20GB disk space

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your actual credentials
nano .env

# REQUIRED: Set these variables:
# - DB_PASSWORD
# - ADMIN_API_KEY
# - SECRET_KEY
# - OPENAI_API_KEY (optional)
```

### 3. Build and Start Services

```bash
# Build images
docker-compose build

# Start all services (database + API)
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 4. Initialize Database

```bash
# Run database setup script inside container
docker-compose exec api python setup_database_complete.py
```

### 5. Verify Deployment

```bash
# Check service health
docker-compose ps

# Test API
curl http://localhost:8000/api/admin/scheduler-status

# View API docs
open http://localhost:8000/docs
```

## Service Details

### Database Service
- **Container**: `bsk-postgres`
- **Image**: `postgres:15-alpine`
- **Port**: 5432 (configurable via .env)
- **Data**: Persisted in `postgres_data` volume

### API Service
- **Container**: `bsk-api`
- **Port**: 8000 (configurable via .env)
- **Workers**: 4 Gunicorn workers with Uvicorn
- **Logs**: Persisted in `api_logs` volume

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f [service_name]

# Execute commands in container
docker-compose exec api python -m backend.main_api

# Access database
docker-compose exec database psql -U postgres -d bsk

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

### 1. Security Hardening

```bash
# Generate secure keys
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Update .env:
DEBUG=false
API_RELOAD=false
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=WARNING
```

### 2. Resource Limits

Add to docker-compose.yml under each service:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### 3. Backup Strategy

```bash
# Backup database
docker-compose exec database pg_dump -U postgres bsk > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v bsk-ser_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 4. SSL/TLS (Nginx Reverse Proxy)

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/admin/scheduler-status

# Database health
docker-compose exec database pg_isready
```

### Logs

```bash
# API logs (inside container)
docker-compose exec api tail -f /var/log/bsk-ser/access.log
docker-compose exec api tail -f /var/log/bsk-ser/error.log

# Docker logs
docker-compose logs --tail=100 -f api
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps database

# Check database logs
docker-compose logs database

# Test connection
docker-compose exec api python -c "from backend.database.connection import engine; print(engine.connect())"
```

### API Not Starting

```bash
# Check logs
docker-compose logs api

# Check environment variables
docker-compose exec api env | grep DB_

# Rebuild container
docker-compose build --no-cache api
docker-compose up -d api
```

### Port Already in Use

```bash
# Change port in .env
API_PORT=8001

# Restart
docker-compose down
docker-compose up -d
```

## Scaling

### Horizontal Scaling

```bash
# Scale API workers
docker-compose up -d --scale api=3

# Use load balancer (Nginx/HAProxy)
```

### Vertical Scaling

Update docker-compose.yml:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
```

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild
docker-compose build

# Restart with zero downtime
docker-compose up -d --no-deps --build api
```

### Database Migration

```bash
# Create backup first!
docker-compose exec database pg_dump -U postgres bsk > backup.sql

# Run migrations
docker-compose exec api psql -U postgres -d bsk -f migrations/your_migration.sql
```

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: Deletes all data!)
docker-compose down -v

# Remove images
docker rmi bsk-ser-api

# Complete cleanup
docker system prune -a --volumes
```
