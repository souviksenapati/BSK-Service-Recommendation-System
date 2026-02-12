# 🏛️ BSK-SER: Government Service Recommendation System

> **Production-grade AI-powered service recommendation system for BSK (Bangla Shasya Kendriya) Government Services in West Bengal**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)

---

## 🌟 Features

- 🎯 **Multi-Engine Recommendations**: District-based, demographic clustering, and content-based filtering
- 🔄 **Automated Weekly Sync**: Scheduled data synchronization from external BSK server
- 🛡️ **JWT Authentication**: Secure API communication with government servers
- 📊 **Real-time Analytics**: Dynamic service recommendations based on citizen demographics
- ⚡ **Production-Ready**: FastAPI backend with connection pooling and error handling
- 🔒 **Privacy-First**: Name masking and secure credential management
- 📅 **Automated Regeneration**: Weekly static file regeneration for recommendation engines

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [System Architecture](#-system-architecture)
- [Database Setup](#-database-setup)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Scheduler](#-automated-scheduler)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- **Option A: Docker Deployment (Recommended)**
  - Docker Desktop 20.10+
  - 8GB+ RAM, 20GB+ disk space
  - See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for complete instructions

- **Option B: Manual Setup**
  - Python 3.8+
  - PostgreSQL 13+
  - Git (for cloning repository)

### Docker Deployment (Quick!)

```bash
# 1. Clone repository
git clone <repository-url>
cd BSK-SER

# 2. Create environment file
cp .env.example .env
# Edit .env with your credentials

# 3. Convert line endings (Windows only)
dos2unix docker-entrypoint.sh

# 4. Deploy!
docker-compose up -d

# 5. Monitor initialization (5-10 minutes first run)
docker-compose logs -f api

# 6. Access API
# http://localhost:8000/docs
```

📖 **For detailed deployment guide, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd BSK-SER

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# 4. Setup database
python setup_database_complete.py

# 5. Start the server
python -m backend.main_api
```

**Server will be running at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   External BSK Server                        │
│          (https://bsk-server.gov.in/api/sync)               │
└─────────────┬───────────────────────────────────────────────┘
              │ JWT Auth + Pagination
              ↓
┌─────────────────────────────────────────────────────────────┐
│                  BSK-SER Backend (FastAPI)                   │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │  Sync Service  │  │  Recommender   │  │  Admin Panel  │ │
│  │  (Weekly Auto) │  │  (3 Engines)   │  │  (Manual)     │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (12 Tables)                 │
│  Master Data │ Derived Tables │ Service Catalog │ Metadata  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Data Sync Engine** (`backend/api/sync.py`)
   - Weekly automated sync from government server
   - JWT authentication and token management
   - Pagination and error handling

2. **Recommendation Engine** (`backend/api/recommend.py`)
   - **District Engine**: Top services by district
   - **Demographic Engine**: Clustering by age, gender, caste, religion
   - **Content Engine**: OpenAI embeddings for service similarity

3. **Scheduler** (`backend/scheduler/sync_scheduler.py`)
   - Weekly data synchronization (Sunday 12 AM)
   - Automatic static file regeneration
   - Error recovery and logging

4. **Admin API** (`backend/api/admin.py`)
   - Manual sync triggers
   - Scheduler status monitoring
   - Static file regeneration

---

## 🗄️ Database Setup

### Automatic Setup (Recommended)

```bash
python setup_database_complete.py
```

**This will:**
- ✅ Create PostgreSQL database (`bsk`)
- ✅ Create all 12 tables with proper schemas
- ✅ Create 15+ performance indexes
- ✅ Import all CSV data from `/data` directory
- ✅ Generate `services_eligibility` from `services.csv`
- ✅ Initialize sync metadata
- ✅ Verify all imports

**Expected Output:**
```
======================================================================
  🚀 BSK-SER COMPLETE DATABASE SETUP
======================================================================

[1/7] Creating Database
   ✅ Created database 'bsk'

[2/7] Creating Tables
   ✅ All tables created successfully

[3/7] Creating Indexes
   ✅ All indexes created successfully

[4/7] Importing CSV Data
   📥 Importing ml_citizen_master.csv → ml_citizen_master
   ✅ Imported 450,230 rows into ml_citizen_master
   ... (continues for all tables)

[5/7] Initializing Sync Metadata
   ✅ Initialized metadata for 4 tables

[6/7] Verifying Database
   📊 Table Verification Report:
   ✅ ml_citizen_master          :      450,230 rows
   ✅ ml_provision               :    1,284,500 rows
   ✅ services                   :        1,234 rows
   ... (shows all 12 tables)

[7/7] Setup Complete!
   🎉 Database is ready to use!
```

### Database Schema

#### **Master Tables** (Synced from External API)
- `ml_citizen_master` - Citizen demographics (450K+ rows)
- `ml_provision` - Service provision history (1.2M+ rows)
- `ml_district` - District information (23 rows)
- `ml_bsk_master` - BSK center details (3,450 rows)

#### **Service Catalog**
- `services` - Service definitions
- `services_eligibility` - Eligibility rules (age, caste, gender, religion)

#### **Derived Tables** (Auto-generated for Recommendations)
- `grouped_df` - Demographic clusters
- `cluster_service_map` - Cluster-to-service mappings
- `district_top_services` - District-wise rankings
- `block_wise_top_services` - Block-wise rankings
- `openai_similarity_matrix` - Service similarity scores

#### **System Tables**
- `sync_metadata` - Synchronization tracking

---

## ⚙️ Configuration

All configuration is managed through environment variables in `.env` file:

### Required Variables

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-password-here          # ⚠️ REQUIRED
DB_NAME=bsk

# External BSK Server API
EXTERNAL_SYNC_URL=https://bsk-server.gov.in/api/sync
EXTERNAL_LOGIN_URL=https://bsk-server.gov.in/api/auth/login
JWT_USERNAME=StateCouncil
JWT_PASSWORD=Council@2531

# Admin Security
ADMIN_API_KEY=generate-secure-random-key  # ⚠️ REQUIRED
```

### Optional Variables

```bash
# OpenAI (for content-based recommendations)
OPENAI_API_KEY=sk-your-key-here

# Application Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true                    # Auto-reload on code changes

# CORS Settings
CORS_ORIGINS=*                     # Comma-separated origins

# Scheduler Configuration
SCHEDULER_TIMEZONE=Asia/Kolkata
SYNC_DAY_OF_WEEK=sun              # mon, tue, wed, thu, fri, sat, sun
SYNC_HOUR=0                       # 0-23 (24-hour format)
SYNC_MINUTE=0
STATIC_REGEN_DELAY_HOURS=1        # Hours after sync to regenerate files

# Performance
MAX_RECOMMENDATIONS=10
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Debug
DEBUG=false
LOG_LEVEL=INFO
ECHO_SQL=false                     # Print SQL queries
```

### Generate Secure Keys

```bash
# Generate ADMIN_API_KEY
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_urlsafe(32))"

# Generate SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

---

## 🔌 API Endpoints

### Recommendation API

#### **POST /api/recommend**
Get service recommendations for a citizen.

**Request Body:**
```json
{
  "phone": "9876543210",
  "district_id": 1,
  "gender": "Male",
  "caste": "General",
  "age": 30,
  "religion": "Hindu",
  "selected_service_id": 101
}
```

**Response:**
```json
{
  "total_recommendations": 15,
  "recommendations": [
    "Kanyashree Prakalpa",
    "Old Age Pension",
    "Ration Card",
    "Birth Certificate",
    ...
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "district_id": 1,
    "gender": "Male",
    "caste": "General",
    "age": 30,
    "religion": "Hindu"
  }'
```

---

### Data Sync API

#### **POST /api/sync**
Sync data from external BSK server.

**Request Body:**
```json
{
  "target_table": "ml_citizen_master",
  "from_date": "2024-01-01"
}
```

**Supported Tables:**
- `ml_citizen_master`
- `ml_provision`
- `ml_district`
- `ml_bsk_master`

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "target_table": "ml_citizen_master",
    "from_date": "2024-01-01"
  }'
```

---

### Regeneration APIs

#### **5.1 Overview**

**Purpose:** Regenerate pre-computed recommendation files from database

**When to Use:**
- After syncing new data from external server
- After manual database updates
- To refresh recommendation caches

---

#### **5.2 Regenerate Specific Types**

**Endpoint:** `POST /api/regenerate/{type}`

**Path Parameters:**
- `district` - Regenerate district-based recommendations only
- `block` - Regenerate block-wise recommendations only
- `demographic` - Regenerate demographic clustering files only
- `all` - Regenerate all recommendation files

**Request:**
```bash
# Regenerate all files
curl -X POST "http://localhost:8000/api/regenerate/all"

# Regenerate only district recommendations
curl -X POST "http://localhost:8000/api/regenerate/district"

# Regenerate only block recommendations
curl -X POST "http://localhost:8000/api/regenerate/block"

# Regenerate only demographic clustering
curl -X POST "http://localhost:8000/api/regenerate/demographic"
```

**Response (type=all):**
```json
{
  "status": "success",
  "message": "All files regenerated successfully",
  "district_files": ["district_top_services"],
  "block_files": ["block_top_services"],
  "demographic_files": [
    "grouped_df",
    "final_df",
    "cluster_service_map.pkl"
  ],
  "timestamp": "2026-02-04T10:30:00+05:30"
}
```

**Response (type=district):**
```json
{
  "status": "success",
  "message": "District files regenerated successfully",
  "district_files": ["district_top_services"],
  "timestamp": "2026-02-04T10:30:00+05:30"
}
```

**Response (type=block):**
```json
{
  "status": "success",
  "message": "Block files regenerated successfully",
  "block_files": ["block_top_services"],
  "timestamp": "2026-02-04T10:30:00+05:30"
}
```

**Response (type=demographic):**
```json
{
  "status": "success",
  "message": "Demographic files regenerated successfully",
  "demographic_files": [
    "grouped_df",
    "final_df",
    "cluster_service_map.pkl"
  ],
  "timestamp": "2026-02-04T10:30:00+05:30"
}
```

**Generated Files:**

| Type | Files | Purpose |
|------|-------|---------|
| **District** | `district_top_services` | Top services by district |
| **Block** | `block_top_services` | Top services by block |
| **Demographic** | `grouped_df`<br>`final_df`<br>`cluster_service_map.pkl` | Demographic clustering<br>Final clustered data<br>Cluster-to-service mapping |

---

### Admin API

#### **GET /api/admin/scheduler-status**
Check scheduler status and scheduled jobs.

```bash
curl http://localhost:8000/api/admin/scheduler-status
```

**Response:**
```json
{
  "scheduler_running": true,
  "timezone": "Asia/Kolkata",
  "jobs": [
    {
      "id": "weekly_sync",
      "name": "Weekly Data Sync (SUN 00:00)",
      "next_run": "2024-02-04 00:00:00+05:30"
    }
  ]
}
```

#### **POST /api/admin/trigger-sync**
Manually trigger data synchronization.

```bash
curl -X POST http://localhost:8000/api/admin/trigger-sync
```

> **Note:** For manual static file regeneration, use the `/api/regenerate/{type}` endpoint instead (see [Regeneration APIs](#regeneration-apis) section above).

---

## 📅 Automated Scheduler

### Weekly Sync Schedule

**Default Schedule:** Sunday at 12:00 AM (IST)

**What it does:**
1. Syncs `ml_citizen_master` (citizens)
2. Syncs `ml_provision` (service history)
3. Syncs `ml_district` (districts)
4. Syncs `ml_bsk_master` (BSK centers)
5. Waits 1 hour
6. Regenerates all derived tables

**Configure Schedule:**
```bash
# Edit .env
SYNC_DAY_OF_WEEK=mon     # Change to Monday
SYNC_HOUR=2              # Change to 2 AM
STATIC_REGEN_DELAY_HOURS=2  # Wait 2 hours instead of 1
```

### Error Handling

- ✅ Continues syncing remaining tables if one fails
- ✅ Logs all errors to `sync_metadata` table
- ✅ Sends summary after all syncs complete
- ✅ Only regenerates if at least one sync succeeds

---

## 📁 Project Structure

```
BSK-SER/
├── .env                          # Configuration (NOT in git)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── setup_database_complete.py    # Automated database setup
├── README.md                     # This file
│
├── backend/
│   ├── main_api.py              # FastAPI application
│   │
│   ├── api/                     # API endpoints
│   │   ├── sync.py              # Data sync endpoint
│   │   ├── recommend.py         # Recommendation endpoint
│   │   ├── generate.py          # Static file generation
│   │   └── admin.py             # Admin endpoints
│   │
│   ├── database/                # Database layer
│   │   ├── models.py            # SQLAlchemy models
│   │   └── connection.py        # Database connection
│   │
│   ├── scheduler/               # Task scheduler
│   │   └── sync_scheduler.py    # Weekly sync scheduler
│   │
│   └── utils/                   # Utilities
│       └── jwt_auth.py          # JWT authentication
│
└── data/                        # CSV data files
    ├── ml_citizen_master.csv    # Required
    ├── ml_provision.csv         # Required
    ├── ml_district.csv          # Required
    ├── ml_bsk_master.csv        # Required
    ├── services.csv             # Required
    ├── grouped_df.csv           # Generated
    └── ...
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Update `.env` with production credentials
- [ ] Set `DEBUG=false` and `API_RELOAD=false`
- [ ] Generate strong `ADMIN_API_KEY` and `SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` with specific domains
- [ ] Set up database backups
- [ ] Configure reverse proxy (Nginx/Apache)
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring and logging
- [ ] Test scheduler is running
- [ ] Verify all API endpoints

### Running in Production

```bash
# Use Gunicorn with multiple workers
gunicorn backend.main_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/bsk-ser/access.log \
  --error-logfile /var/log/bsk-ser/error.log
```

### Systemd Service (Linux)

Create `/etc/systemd/system/bsk-ser.service`:

```ini
[Unit]
Description=BSK-SER API Server
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/bsk-ser
Environment="PATH=/opt/bsk-ser/venv/bin"
ExecStart=/opt/bsk-ser/venv/bin/gunicorn backend.main_api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable bsk-ser
sudo systemctl start bsk-ser
sudo systemctl status bsk-ser
```

---

## 🐛 Troubleshooting

### Database Connection Failed

**Error:** `Connection refused` or `Authentication failed`

**Solutions:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify credentials in `.env`
3. Test connection: `psql -U postgres -h localhost -d bsk`
4. Check firewall settings

---

### Scheduler Not Running

**Error:** No scheduled jobs

**Solutions:**
1. Check scheduler status: `GET /api/admin/scheduler-status`
2. Verify `ENABLE_SCHEDULER=true` in `.env`
3. Check logs for errors
4. Restart application

---

### JWT Authentication Failed

**Error:** 401 Unauthorized from external API

**Solutions:**
1. Verify `JWT_USERNAME` and `JWT_PASSWORD` in `.env`
2. Test manual login to external API
3. Check token expiry (auto-refreshes after 1 hour)

---

### Data Not Syncing

**Error:** Sync completes but no data updated

**Solutions:**
1. Check `sync_metadata` table for errors
2. Verify `from_date` is correct
3. Check external API is accessible
4. Review application logs

---

## 📊 Monitoring

### Check System Health

```bash
# Database status
curl http://localhost:8000/api/admin/scheduler-status

# Recent sync status
psql -U postgres -d bsk -c "SELECT * FROM sync_metadata ORDER BY last_sync_timestamp DESC LIMIT 5;"

# Table row counts
psql -U postgres -d bsk -c "SELECT schemaname, tablename, n_live_tup as rows FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
```

### Logs

```bash
# Application logs (if LOG_FILE is set)
tail -f /var/log/bsk-ser/app.log

# Database connections
psql -U postgres -d bsk -c "SELECT count(*) FROM pg_stat_activity WHERE datname='bsk';"
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Environment Config Guide**: See `env_quick_reference.md`
- **Database Setup Guide**: See `database_setup_guide.md`
- **Scheduler Documentation**: See `scheduler_documentation.md`

---

## 📝 License

[Your License Here]

---

## 👥 Contributors

<a href="https://github.com/DSMLCoEWB/SysRecoBatch4/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=DSMLCoEWB/SysRecoBatch4" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

---

## 📧 Support

For issues and questions:
- Create an issue in the repository

---

**Last Updated:** February 12, 2026
**Version:** 2.0.0
