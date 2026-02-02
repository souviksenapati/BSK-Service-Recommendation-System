# 🚀 BSK-SER One-Command Deployment Guide

## ✅ **Prerequisites**

- Docker Desktop installed and running
- 20GB+ free disk space
- Port 8000 available

---

## 📦 **Quick Start (Fresh System)**

### **Step 1: Get the Project**

```bash
# Clone or extract project
cd /path/to/BSK-Service-Recommendation-System
```

### **Step 2: Configure Environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials (REQUIRED!)
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Minimum required settings:**
```env
DB_PASSWORD=YourSecurePassword123
ADMIN_API_KEY=your-admin-key-here
SECRET_KEY=your-secret-key-here
```

### **Step 3: Deploy (One Command!)**

```bash
docker-compose up -d
```

**That's it!** 🎉

---

## ⏱️ **What Happens Next**

### **First Run (5-10 minutes):**

```bash
# Monitor the setup process
docker-compose logs -f api
```

**You'll see:**
```
[1/3] Waiting for PostgreSQL...
      PostgreSQL is ready!

[2/3] Checking database initialization...
      First run detected - initializing database...
      This will take 5-10 minutes (importing 117 MB data)
      
      📥 Importing ml_citizen_master.csv (16.6M rows)...
      ✅ Imported successfully
      
      📥 Importing ml_provision.csv (16.5M rows)...
      ✅ Imported successfully
      
      Database setup complete!

[3/3] Starting API Server...
      BSK-SER API Server Ready
```

### **Subsequent Runs (Instant!):**

```bash
docker-compose up -d
# ⚡ Starts in ~30 seconds!
```

---

## 🌐 **Access the Application**

Once you see "API Server Ready" in logs:

- **API Docs**: http://localhost:8000/docs
- **API Base**: http://localhost:8000/api
- **Health Check**: http://localhost:8000/api/admin/scheduler-status

---

## 🔧 **Common Commands**

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Check status
docker-compose ps

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Complete cleanup (removes volumes!)
docker-compose down -v
```

---

## 🔍 **Verify Deployment**

```bash
# Check containers are running
docker-compose ps
# Should show: bsk-postgres (healthy), bsk-api (healthy)

# Test API
curl http://localhost:8000/api/admin/scheduler-status

# Check database
docker-compose exec database psql -U postgres -d bsk -c "SELECT COUNT(*) FROM ml_citizen_master;"
# Should show: 16,600,000+
```

---

## 🚨 **Troubleshooting**

### **Container exits immediately:**
```bash
docker-compose logs api
# Check for errors
```

### **Database connection fails:**
```bash
# Verify .env file has DB_PASSWORD set
cat .env | grep DB_PASSWORD
```

### **Rebuild from scratch:**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### **Reset database (fresh import):**
```bash
# Remove marker file
rm data/.db_initialized

# Restart
docker-compose restart api

# Watch re-initialization
docker-compose logs -f api
```

---

## 📊 **What Gets Installed**

- **PostgreSQL 15** with 16.6M+ citizen records
- **FastAPI** application with 4 Gunicorn workers
- **Automated scheduler** for weekly data sync
- **15 database tables** with indexes
- **117 MB** of CSV data imported
- **Pre-computed recommendations** ready to use

---

## 🎯 **Success Checklist**

- [ ] Docker Desktop running
- [ ] `.env` file created with credentials
- [ ] Ran `docker-compose up -d`
- [ ] Waited 5-10 minutes for first-run setup
- [ ] http://localhost:8000/docs accessible
- [ ] API endpoints respond
- [ ] Database has data

---

## 🌟 **Production Deployment**

Same process on any system!

```bash
# On production server
cd /opt/bsk-ser
cp .env.example .env
nano .env  # Set production credentials
docker-compose up -d
docker-compose logs -f api  # Wait for setup
# Done!
```

---

**No manual database setup needed - everything is automatic!** 🚀
