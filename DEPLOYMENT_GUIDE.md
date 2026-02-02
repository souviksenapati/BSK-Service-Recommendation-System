# 🚀 BSK-SER Docker Deployment Guide

**Complete guide for deploying BSK-SER (Government Service Recommendation System) using Docker**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [File Transfer](#file-transfer)
3. [Environment Setup](#environment-setup)
4. [Building & Deployment](#building--deployment)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## 1. Prerequisites

### **System Requirements**

- **Operating System**: Windows 10/11, Linux, or macOS
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: 20GB+ free space
- **CPU**: 2+ cores recommended

### **Software Requirements**

**Install Docker Desktop:**
- **Windows/Mac**: Download from https://www.docker.com/products/docker-desktop/
- **Linux**: Install `docker` and `docker-compose`

**Verify Installation:**
```bash
docker --version
# Expected: Docker version 20.10.0 or higher

docker-compose --version
# Expected: Docker Compose version 2.0.0 or higher
```

**Ensure Docker Desktop is Running:**
- Windows/Mac: Check system tray for Docker whale icon (should be steady, not animated)
- Linux: `systemctl status docker`

---

## 2. File Transfer

### **Method A: Complete Project Transfer (Recommended)**

**On Development Machine:**
```bash
# Create deployment package
cd d:\Projects\get-github-user-details-master\BSK-SER
$files = @(
    "Dockerfile",
    "docker-compose.yml",
    "docker-entrypoint.sh",
    ".dockerignore",
    ".gitattributes",
    "requirements.txt",
    "setup_database_complete.py",
    ".env.example",
    "backend",
    "data"
)
Compress-Archive -Path $files -DestinationPath "C:\BSK-Deploy.zip" -Force
```

**On Deployment Machine:**
```bash
# Extract to deployment location
Expand-Archive -Path "C:\BSK-Deploy.zip" -DestinationPath "C:\Docker\BSK-SER" -Force
cd C:\Docker\BSK-SER
```

### **Method B: Git Clone**

```bash
git clone https://github.com/your-org/BSK-Service-Recommendation-System.git
cd BSK-Service-Recommendation-System
```

### **Critical: Fix Line Endings (Windows Only)**

**If transferring from Windows, convert shell scripts to Unix format:**

```powershell
# Option 1: Using dos2unix (if installed)
dos2unix docker-entrypoint.sh

# Option 2: Using PowerShell
(Get-Content docker-entrypoint.sh -Raw) -replace "`r`n", "`n" | Set-Content docker-entrypoint.sh -NoNewline
```

**Verify Files Exist:**
```bash
ls Dockerfile
ls docker-compose.yml
ls docker-entrypoint.sh
ls setup_database_complete.py
ls backend
ls data
# All should be present
```

---

## 3. Environment Setup

### **Step 1: Create Environment File**

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

### **Step 2: Configure Required Variables**

**Minimum Required (MUST be set):**

```env
# Database Password
DB_PASSWORD=YourSecurePassword123!

# Admin API Key (generate with: openssl rand -base64 32)
ADMIN_API_KEY=your-admin-key-here

# Secret Key (generate with: openssl rand -base64 32)
SECRET_KEY=your-secret-key-here
```

**Optional (External Integrations):**

```env
# External BSK Server Sync
EXTERNAL_SYNC_URL=https://bsk-server.gov.in/api/sync
EXTERNAL_LOGIN_URL=https://bsk-server.gov.in/api/login
JWT_USERNAME=your-username
JWT_PASSWORD=your-password

# OpenAI API (for content-based recommendations)
OPENAI_API_KEY=sk-your-openai-key-here
```

### **Step 3: Generate Secure Keys**

**Using PowerShell (Windows):**
```powershell
# Generate random keys
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

**Using OpenSSL (Linux/Mac):**
```bash
openssl rand -base64 32
```

---

## 4. Building & Deployment

### **Step 1: Clean Any Previous Installation**

```bash
# Stop and remove existing containers
docker-compose down -v

# Clean Docker system (optional, frees space)
docker system prune -af
```

### **Step 2: Build Docker Images**

```bash
# Build from scratch (no cache)
docker-compose build --no-cache
```

**Expected Output:**
```
[+] Building 180.5s (19/19) FINISHED
 => [stage-1  7/11] COPY docker-entrypoint.sh /app/
 => [stage-1  8/11] RUN chmod +x /app/docker-entrypoint.sh
 => exporting to image
Successfully tagged bsk-ser-api:latest
```

**Build Time:** ~3-5 minutes

### **Step 3: Start Services**

```bash
docker-compose up -d
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Network bsk-network      Created
 ✔ Container bsk-postgres   Started
 ✔ Container bsk-api        Started
```

### **Step 4: Monitor First-Run Setup**

```bash
# Watch initialization logs (CRITICAL for first run!)
docker-compose logs -f api
```

**What You'll See (First Run - 5-10 minutes):**

```
bsk-api | ======================================================================
bsk-api | BSK-SER API Server - Docker Container Starting...
bsk-api | ======================================================================
bsk-api | 
bsk-api | [1/3] Waiting for PostgreSQL to be ready...
bsk-api |       PostgreSQL is ready!
bsk-api | 
bsk-api | [2/3] Checking database initialization status...
bsk-api |       First run detected - initializing database...
bsk-api |       This will take 5-10 minutes to import all data (117 MB)
bsk-api | 
bsk-api | 📥 Importing ml_citizen_master.csv (16.6M rows)...
bsk-api |    ✅ Imported 16,600,000 rows into ml_citizen_master
bsk-api | 
bsk-api | 📥 Importing ml_provision.csv (16.5M rows)...
bsk-api |    ✅ Imported 16,500,000 rows into ml_provision
bsk-api | 
bsk-api |       Database setup complete!
bsk-api | 
bsk-api | [3/3] Starting API Server...
bsk-api | 
bsk-api | ======================================================================
bsk-api |   BSK-SER API Server Ready
bsk-api |   - Server: http://0.0.0.0:8000
bsk-api |   - API Docs: http://0.0.0.0:8000/docs
bsk-api |   - Workers: 4 (Gunicorn + Uvicorn)
bsk-api | ======================================================================
```

**Wait for:** `"BSK-SER API Server Ready"` message

**Subsequent Runs:** ~30 seconds (skips database setup)

---

## 5. Verification

### **Step 1: Check Container Status**

```bash
docker-compose ps
```

**Expected:**
```
NAME           IMAGE               STATUS         PORTS
bsk-postgres   postgres:15-alpine  Up (healthy)   0.0.0.0:5432->5432/tcp
bsk-api        bsk-ser-api         Up (healthy)   0.0.0.0:8000->8000/tcp
```

Both should show `Up (healthy)`

### **Step 2: Access API Documentation**

**Open browser:**
```
http://localhost:8000/docs
```

**Should see:** Interactive FastAPI Swagger UI with all endpoints

### **Step 3: Test Health Endpoint**

```bash
# Using curl
curl http://localhost:8000/api/admin/scheduler-status

# Using PowerShell
Invoke-WebRequest http://localhost:8000/api/admin/scheduler-status | Select-Object StatusCode, Content
```

**Expected Response:**
```json
{
  "status": "running",
  "next_sync": "2026-02-08 00:00:00+05:30",
  "last_sync": null
}
```

### **Step 4: Verify Database Data**

```bash
# Connect to database
docker-compose exec database psql -U postgres -d bsk

# Check tables
\dt

# Count citizen records
SELECT COUNT(*) FROM ml_citizen_master;
# Expected: 16,600,000+

# Count provision records
SELECT COUNT(*) FROM ml_provision;
# Expected: 16,500,000+

# Exit
\q
```

### **Step 5: Test Recommendation API**

**Using curl:**
```bash
curl http://localhost:8000/api/recommend/1
```

**Using browser:**
```
http://localhost:8000/api/recommend/1
```

**Expected:** JSON response with service recommendations

---

## 6. Troubleshooting

### **Issue 1: "exec format error" on docker-entrypoint.sh**

**Cause:** Windows line endings (CRLF) instead of Unix (LF)

**Fix:**
```powershell
# Convert line endings
dos2unix docker-entrypoint.sh

# OR using PowerShell
(Get-Content docker-entrypoint.sh -Raw) -replace "`r`n", "`n" | Set-Content docker-entrypoint.sh -NoNewline

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Issue 2: "Docker daemon not running"**

**Symptoms:**
```
error during connect: open //./pipe/docker_engine: The system cannot find the file specified
```

**Fix:**
1. Start Docker Desktop
2. Wait for whale icon to be steady (not spinning)
3. Retry command

### **Issue 3: Container Exits Immediately**

**Check logs:**
```bash
docker-compose logs api
```

**Common Causes:**
- Missing `.env` file → Create from `.env.example`
- Wrong DB_PASSWORD → Check `.env` file
- Port 8000 already in use → Stop other services or change `API_PORT` in `.env`

### **Issue 4: Database Connection Failed**

**Verify PostgreSQL is healthy:**
```bash
docker-compose ps
# bsk-postgres should show "healthy"

# Check database logs
docker-compose logs database

# Test connection
docker-compose exec database pg_isready -U postgres
```

### **Issue 5: Slow First-Run Setup**

**This is NORMAL!** Importing 16.6M+ records takes 5-10 minutes.

**Monitor progress:**
```bash
docker-compose logs -f api
```

**If stuck for >15 minutes:**
```bash
# Check container resources
docker stats

# Restart
docker-compose restart api
```

### **Issue 6: API Returns 500 Error**

**Check logs:**
```bash
docker-compose logs api | tail -50
```

**Common fixes:**
```bash
# Restart API container
docker-compose restart api

# Full restart
docker-compose down
docker-compose up -d

# Rebuild if code changed
docker-compose build --no-cache
docker-compose up -d
```

### **Issue 7: "bind: address already in use"**

**Port 8000 or 5432 is taken**

**Option 1: Stop conflicting service**
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill process
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

**Option 2: Change port in `.env`**
```env
API_PORT=8080
DB_PORT=5433
```

---

## 7. Maintenance

### **Viewing Logs**

```bash
# Real-time logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# All services
docker-compose logs

# Since timestamp
docker-compose logs --since="2026-02-02T10:00:00"
```

### **Stopping Services**

```bash
# Stop (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove EVERYTHING including data
docker-compose down -v
```

### **Restarting Services**

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart database
```

### **Updating Application**

```bash
# 1. Pull latest code
git pull

# 2. Rebuild
docker-compose build --no-cache

# 3. Restart
docker-compose up -d

# 4. Verify
docker-compose logs -f api
```

### **Database Backup**

```bash
# Create backup
docker-compose exec database pg_dump -U postgres bsk > bsk_backup_$(date +%Y%m%d).sql

# Restore backup
cat bsk_backup_20260202.sql | docker-compose exec -T database psql -U postgres bsk
```

### **Resetting Database (Fresh Import)**

```bash
# Delete marker file
docker-compose exec api rm /app/data/.db_initialized

# Restart (will re-import data)
docker-compose restart api

# Monitor re-initialization
docker-compose logs -f api
```

### **Accessing Container Shell**

```bash
# Access API container
docker-compose exec api bash

# Access database
docker-compose exec database psql -U postgres -d bsk

# View files
docker-compose exec api ls -la /app/data
```

### **Disk Space Management**

```bash
# Check Docker disk usage
docker system df

# Clean up unused images/containers
docker system prune -a

# Remove specific unused volumes
docker volume prune
```

---

## 📊 Quick Reference

### **Essential Commands**

| Task | Command |
|------|---------|
| **Start services** | `docker-compose up -d` |
| **Stop services** | `docker-compose down` |
| **View logs** | `docker-compose logs -f api` |
| **Check status** | `docker-compose ps` |
| **Restart API** | `docker-compose restart api` |
| **Rebuild** | `docker-compose build --no-cache` |
| **Access database** | `docker-compose exec database psql -U postgres -d bsk` |
| **Access API shell** | `docker-compose exec api bash` |

### **Important URLs**

| Service | URL |
|---------|-----|
| **API Documentation** | http://localhost:8000/docs |
| **API Base** | http://localhost:8000/api |
| **Scheduler Status** | http://localhost:8000/api/admin/scheduler-status |
| **Recommendations** | http://localhost:8000/api/recommend/{citizen_id} |

### **Default Ports**

| Service | Port | Customizable in .env |
|---------|------|---------------------|
| **API** | 8000 | `API_PORT=8000` |
| **PostgreSQL** | 5432 | `DB_PORT=5432` |

---

## ✅ Success Checklist

- [ ] Docker Desktop installed and running
- [ ] All files transferred to deployment directory
- [ ] `.env` file created with credentials
- [ ] Line endings fixed (`dos2unix docker-entrypoint.sh`)
- [ ] Containers built successfully (`docker-compose build`)
- [ ] Containers running (`docker-compose ps` shows healthy)
- [ ] Database initialized (check logs)
- [ ] API accessible at http://localhost:8000/docs
- [ ] Database has 16M+ records
- [ ] Recommendation API returns results

---

## 🆘 Support

If issues persist after following this guide:

1. Check logs: `docker-compose logs api`
2. Verify `.env` configuration
3. Ensure Docker Desktop has sufficient resources (Settings → Resources)
4. Review `LINE_ENDINGS_FIX.md` for line-ending issues
5. Check `TROUBLESHOOTING.md` for common problems

---

**🎉 Deployment Complete!**

Your BSK-SER system is now running at **http://localhost:8000**
