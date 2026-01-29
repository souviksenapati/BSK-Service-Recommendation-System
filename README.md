# 🏛️ Government Service Recommendation System

A production-grade AI-powered service recommendation system for government services, featuring multi-engine recommendations using demographic clustering, district-based recommendations, and content-based filtering.

## ✨ Key Features

- **📱 Multi-Mode Input**: Phone lookup and manual entry modes
- **🎯 Smart Recommendations**: Three-engine recommendation system (district, demographic, content-based)
- **🗄️ Intelligent Data Management**: Smart database connectivity with automatic CSV fallback
- **⏰ Automated Scheduling**: Background tasks for data management and conversion
- **🚀 Production Ready**: FastAPI backend with comprehensive API documentation
- **📊 Real-time Analytics**: Live data processing and recommendation generation
- **🔧 Flexible Deployment**: Multiple operational modes (Database, Hybrid, CSV-only)

## 🗄️ **Database Connection & Setup**

**⚠️ IMPORTANT**: The system now features **intelligent database connectivity** that automatically detects database availability and switches modes accordingly.

### **🔄 Operational Modes**

The system operates in three intelligent modes:

1. **🗄️ Database Mode** (Recommended for Production)
   - Direct database connections for real-time data
   - All 4 required tables available: `ml_citizen_master`, `ml_district`, `ml_provision`, `ml_service_master`
   - Optimal performance and scalability

2. **🔀 Hybrid Mode** (Partial Database)
   - Some database tables available, others fall back to CSV
   - Automatic detection and graceful degradation
   - Good for migration scenarios

3. **📁 CSV-Only Mode** (Development/Fallback)
   - Uses CSV files exclusively
   - Automatic fallback when database unavailable
   - Safe mode to avoid connection errors

### **📋 Database Requirements**

**Required Tables:**
```sql
-- Required table names (must match exactly)
ml_citizen_master   -- Citizen demographics and phone data
ml_district         -- District information and mappings  
ml_provision        -- Service provision history
ml_service_master   -- Service catalog and definitions
```

**Database Configuration:**
```env
# Required in backend/.env
DATABASE_URL=postgresql://username:password@host:port/database_name

# Example configurations:
DATABASE_URL=postgresql://postgres:4790@localhost:5432/dbo
DATABASE_URL=postgresql://admin:secret123@192.168.1.100:5432/govt_services
DATABASE_URL=postgresql://user:pass@db.company.com:5432/recommendations
```

### **🚀 Quick Database Setup**

**Step 1: Configure Database Connection**
```bash
# Create/update backend/.env file
echo "DATABASE_URL=postgresql://your_username:your_password@localhost:5432/your_database" > backend/.env
```

**Step 2: Test Database Connection**
```bash
# Test database availability
python test_database_availability.py
```

**Step 3: Setup Database Tables (if needed)**
```bash
# Create tables and import data
python backend/setup_database.py
```

**Step 4: Verify System Status**
```bash
# Check operational mode
curl -X GET "http://localhost:8000/database-status"
```

---

## 🧪 **API Testing & Examples**

### **🚀 Start the Server**
```bash
cd f:\recomm
python -m uvicorn backend.main:app --reload
```

### **📍 Main Endpoints**

#### **1. Recommendation Endpoint**
**POST** `/recommend` - Core recommendation functionality

**Phone Number Mode Example:**
```bash
curl -X POST "http://localhost:8000/recommend" \
-H "Content-Type: application/js## 🔧 Configuration

### Environment Variables
Set these in `backend/.env`:

**Required:**
- `OPENAI_API_KEY` - OpenAI API key for embeddings (get from platform.openai.com)

**Optional:**
- `DATABASE_URL` - Database connection string (for production deployment)
- `MAX_RECOMMENDATIONS` - Maximum number of recommendations per engine (default: 5)
- `SCHEDULER_TIMEZONE` - Timezone for cron jobs (default: local timezone)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### MAX_RECOMMENDATIONS Configuration

The `MAX_RECOMMENDATIONS` setting controls the maximum number of recommendations returned by each recommendation engine:

**Examples:**
```env
# Conservative recommendations
MAX_RECOMMENDATIONS=3

# Standard setup (default)
MAX_RECOMMENDATIONS=5

# More comprehensive recommendations  
MAX_RECOMMENDATIONS=10
```

**Impact:**
- **District recommendations**: Max services recommended for the user's district
- **Demographic recommendations**: Max services based on user's demographic cluster
- **Content-based recommendations**: Max similar services per selected service

**Testing different values:**
```bash
# Update .env file
echo "MAX_RECOMMENDATIONS=7" >> backend/.env

# Restart server
python -m uvicorn backend.main:app --reload

# Test with new limit
curl -X POST "http://localhost:8000/recommend" \
-H "Content-Type: application/json" \
-d '{"mode": "manual", "district_id": 1, "gender": "Male", "caste": "General", "age": 30, "religion": "Hindu", "selected_service_id": 101}'
```  "mode": "phone",
  "phone": "7001337407",
  "selected_service_id": 101
}'
```

**Manual Entry Mode Example:**
```bash
curl -X POST "http://localhost:8000/recommend" \
-H "Content-Type: application/json" \
-d '{
  "mode": "manual",
  "district_id": 2,
  "gender": "Male",
  "caste": "General",
  "age": 30,
  "religion": "Hindu",
  "selected_service_id": 101
}'
```

**Expected Response Format:**
```json
{
  "district_recommendations": [
    "Birth Certificate",
    "Ration Card",
    "Voter ID Card",
    "Pan Card",
    "Passport"
  ],
  "demographic_recommendations": [
    "Education Scholarship",
    "Employment Certificate",
    "Income Certificate",
    "Caste Certificate",
    "Domicile Certificate"
  ],
  "item_recommendations": {
    "Birth Certificate": [
      "Death Certificate",
      "Marriage Certificate", 
      "Age Certificate",
      "Character Certificate",
      "Domicile Certificate"
    ]
  }
}
```

#### **2. Data Management Endpoints**

**Check Data Status:**
```bash
curl -X GET "http://localhost:8000/data-status"
```

**Convert Database to CSV:**
```bash
curl -X POST "http://localhost:8000/convert-database-to-csv"
```

**Generate Demo CSVs:**
```bash
curl -X POST "http://localhost:8000/generate-demo-csvs"
```

**Generate District CSVs:**
```bash
curl -X POST "http://localhost:8000/generate-district-csvs"
```

#### **3. Scheduler Management**

**Check Scheduler Status:**
```bash
curl -X GET "http://localhost:8000/scheduler-status"
```

**Manual Trigger - Demo CSVs:**
```bash
curl -X POST "http://localhost:8000/trigger-nightly-csvs"
```

**Manual Trigger - District CSVs:**
```bash
curl -X POST "http://localhost:8000/trigger-monthly-csvs"
```

**Manual Trigger - All CSVs:**
```bash
curl -X POST "http://localhost:8000/trigger-all-csvs"
```

### **🔍 Testing Scenarios**

#### **Scenario 1: New User Phone Lookup**
```json
{
  "mode": "phone",
  "phone": "9876543210"
}
```

#### **Scenario 2: Manual Entry with Content Recommendations** 
```json
{
  "mode": "manual",
  "district_id": 1,
  "gender": "Female", 
  "caste": "SC",
  "age": 25,
  "religion": "Hindu",
  "selected_service_id": 205
}
```

#### **Scenario 3: Test Database Conversion**
```bash
# First check what's available
curl -X GET "http://localhost:8000/data-status"

# Convert database tables to CSV
curl -X POST "http://localhost:8000/convert-database-to-csv"

# Verify conversion worked
curl -X GET "http://localhost:8000/data-status"
```

### **🛠️ Testing with FastAPI Docs**
1. Open browser: `http://localhost:8000/docs`
2. Click on any endpoint to test interactively
3. Use "Try it out" to send test requests
4. View responses directly in the interface

---

## ⏰ **Automated Scheduling & Data Management**

The system includes comprehensive automated task scheduling using APScheduler for data management:

### **📅 Scheduled Tasks**

#### **🔄 Database-to-CSV Conversion:**
- **Full Database Export**: Daily at 2:00 AM (02:00) 
  - Converts all database tables to CSV files automatically
  - Saves to `data_backup/` directory for validation
  - Includes validation and error reporting

#### **📊 Analysis Data Generation:**
- **Demo CSVs**: Daily at 11:00 PM (21:00)
  - Generates aggregated demo datasets
  - Updates service usage statistics
- **District CSVs**: Monthly on 1st at 3:00 AM (03:00)
  - Creates district-level analytics
  - Updates regional service preferences

### **🎛️ Manual Triggers**
All scheduled tasks can be triggered manually via API endpoints:

| Endpoint | Purpose | Schedule |
|----------|---------|----------|
| `POST /convert/all` | **Database-to-CSV conversion** | **Daily 2:00 AM** |
| `POST /trigger-nightly-csvs` | Demo CSV generation | Daily 11:00 PM |
| `POST /trigger-monthly-csvs` | District CSV generation | Monthly 1st, 3:00 AM |
| `POST /trigger-all-csvs` | Both analysis tasks | Combined execution |
| `GET /scheduler-status` | Check scheduler status | Real-time monitoring |

### **⚙️ Scheduler Configuration**

#### **Environment Variables:**
```env
# Scheduler timezone (optional)
SCHEDULER_TIMEZONE=Asia/Kolkata

# Database connection for scheduled tasks
DATABASE_URL=postgresql://postgres:4790@localhost:5432/dbo
```

#### **Code Configuration:**
Update schedule times in `backend/main.py`:
```python
# Database-to-CSV conversion (NEW)
scheduler.add_job(
    func=scheduled_database_to_csv_conversion,
    trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM daily
    id='daily_database_csv_conversion',
    timezone=pytz.timezone(SCHEDULER_TIMEZONE)
)

# Analysis data generation
scheduler.add_job(
    func=scheduled_generate_demo_csvs,
    trigger=CronTrigger(hour=21, minute=0),  # 11:00 PM daily
    id='nightly_demo_csv_generation'
)

scheduler.add_job(
    func=scheduled_generate_district_csvs,
    trigger=CronTrigger(day=1, hour=3, minute=0),  # 1st of month at 3:00 AM
    id='monthly_district_csv_generation'
)
```

### **🔍 Scheduler Monitoring**

**Check Status:**
```bash
curl -X GET "http://localhost:8000/scheduler-status"
```

**Expected Response:**
```json
{
  "scheduler_running": true,
  "timezone": "Asia/Kolkata",
  "jobs": [
    {
      "id": "daily_database_csv_conversion",
      "next_run": "2024-01-15 02:00:00",
      "trigger": "cron[hour=2,minute=0]"
    },
    {
      "id": "nightly_demo_csv_generation", 
      "next_run": "2024-01-14 21:00:00",
      "trigger": "cron[hour=21,minute=0]"
    },
    {
      "id": "monthly_district_csv_generation",
      "next_run": "2024-02-01 03:00:00", 
      "trigger": "cron[day=1,hour=3,minute=0]"
    }
  ]
}
```

---

## 🚀 Features

Multi-engine recommendation system using demographic clustering, district-based recommendations, and content-based filtering.

---

## 🏗️ Project Structure

```
recomm/
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── frontend/                        # Frontend components
│   └── streamlit_app.py             # Main Streamlit web application
├── backend/                         # Backend services
│   ├── __init__.py
│   ├── .env                         # Environment variables
│   ├── main.py                      # Backend main entry point (FastAPI)
│   ├── inference/                   # Recommendation engines
│   │   ├── __init__.py
│   │   ├── demo.py                  # Demographic recommendations
│   │   ├── district.py              # District-based recommendations
│   │   └── content.py               # Content-based recommendations (was item.py)
│   └── helpers/                     # Helper functions
│       ├── __init__.py
│       ├── demo_helper.py           # Demographic processing utilities
│       ├── district_helper.py       # District processing utilities
│       └── content_helper.py        # Content processing utilities
├── notebooks/                       # Jupyter notebooks for analysis
│   ├── eda.ipynb
│   ├── main.ipynb
│   └── openai_service_embeddings.ipynb
└── data/                            # Data files
    ├── ml_citizen_master.csv
    ├── ml_provision.csv
    ├── grouped_df.csv
    ├── cluster_service_map.pkl
    ├── service_id_with_name.csv
    ├── services.csv
    ├── final_df.csv
    ├── district_top_services.csv
    ├── service_with_domains.csv
    ├── openai_similarity_matrix.csv
    ├── service_master.csv
    ├── ml_district.csv
    └── service_master_enhanced.csv
```

---

## � **Database Integration & Conversion**

The system supports flexible data loading with CSV-first, database-fallback strategy for production deployments.

### **🎯 Key Features**
- **Flexible Loading**: Automatically tries CSV files first, falls back to database
- **Database Conversion**: Convert PostgreSQL tables to CSV files via API endpoints
- **Data Validation**: Integrity checking for converted files
- **Status Monitoring**: Real-time availability checking for all data sources

### **📋 Quick Setup**

#### **1. Environment Configuration**
Create `backend/.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/recomm_db
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
```

#### **2. Database Setup (Optional)**
```bash
cd backend
python setup_database.py
```

### **🔧 Database Conversion API**

**Convert Database to CSV:**
```bash
curl -X POST "http://localhost:8000/convert-database-to-csv"
```

**Check Data Availability:**
```bash
curl -X GET "http://localhost:8000/data-status"
```

**Batch Convert with Validation:**
```bash
curl -X POST "http://localhost:8000/batch-convert-with-validation"
```

### **🗺️ Data Mappings**

| CSV File | Database Table | Purpose |
|----------|----------------|---------|
| `ml_citizen_master.csv` | `ml_citizen_master` | User demographics |
| `ml_provision.csv` | `ml_provision` | Service usage history |
| `ml_district.csv` | `ml_district` | District information |
| `service_master.csv` | `ml_service_master` | Service catalog |

---

## �🚀 Features

### 1. **Demographic Recommendations**
- Uses age, gender, caste, religion, and district for clustering
- PyArrow-free implementation for better compatibility
- Handles missing data gracefully

### 2. **District-based Recommendations**
- Provides popular services within user's district
- Based on district historical usage patterns
- Configurable number of recommendations

### 3. **Content-based Recommendations**
- Uses OpenAI embeddings for semantic similarity
- Cosine similarity for service matching
- Filters out inappropriate services

### 4. **Web Interface**
- Streamlit-based user interface
- Phone number lookup and manual entry modes
- Real-time recommendations
- Service filtering (birth/death certificates blocked)

---

## 🚀 Quick Start Guide

### **📋 Prerequisites**
- Python 3.8+
- PostgreSQL database (for production) OR CSV files (for development)
- OpenAI API key (optional, for content-based recommendations)

### **⚡ Fast Setup**

1. **Clone and install dependencies**
   ```bash
   git clone <repository>
   cd recomm
   pip install -r requirements.txt
   ```

2. **🗄️ Database Configuration** *(Critical Step)*
   ```bash
   # Create environment configuration
   echo "DATABASE_URL=postgresql://username:password@host:port/database" > backend/.env
   
   # Test database connection
   python test_database_availability.py
   ```

3. **📊 Setup Data Sources**

   **Option A: Database Mode (Recommended)**
   ```bash
   # Ensure all 4 tables exist in your database:
   # ml_citizen_master, ml_district, ml_provision, ml_service_master
   python backend/setup_database.py
   ```

   **Option B: CSV Mode (Development)**
   ```bash
   # Copy required CSV files to data/ folder
   cp data_backup/*.csv data/
   ```

4. **🔧 Configure API Settings**
   ```bash
   # Add to backend/.env (optional)
   echo "MAX_RECOMMENDATIONS=5" >> backend/.env
   echo "OPENAI_API_KEY=your_openai_api_key" >> backend/.env
   ```

5. **🚀 Start the server**
   ```bash
   # FastAPI Backend
   cd backend
   python -m uvicorn main:app --reload --port 8000
   
   # The system will automatically detect operational mode:
   # ✓ Database Mode: All tables found
   # ⚠️ Hybrid Mode: Some tables found  
   # 📁 CSV Mode: No database/tables found
   ```

6. **🧪 Test the system**
   ```bash
   # Check system status
   curl -X GET "http://localhost:8000/database-status"
   
   # Test recommendations
   curl -X POST "http://localhost:8000/recommend" \
   -H "Content-Type: application/json" \
   -d '{"mode": "phone", "phone": "1234567890"}'
   ```

### **🔍 Verify Setup**

The system performs automatic startup checks:

```bash
INFO - Checking database table availability...
INFO - Database connection: ✓  
INFO - All required tables: ✓
INFO - Operational mode: DATABASE
```

**If you see warnings:**
- ⚠️ Missing tables → Run `python backend/setup_database.py`
- ❌ Connection failed → Check `DATABASE_URL` in backend/.env
- 📁 CSV mode → Ensure CSV files exist in data/ folder

### For New Users
### **📋 Legacy Setup (CSV-only Mode)**

1. **Prepare Data**: Ensure you have the 4 Category 1 CSV files from your database
2. **Copy Configuration Files**: Copy the 3 files from `data_backup/` to `data/` folder:
   - `services.csv`
   - `service_with_domains.csv` 
   - `openai_similarity_matrix.csv`
3. **Install Dependencies**: Run `pip install -r requirements.txt`
4. **Configure Environment**: Set up `backend/.env` with your OpenAI API key
5. **Generate Initial CSVs**: Run demographic and district helper functions to create processing files
6. **Start Services**: Launch FastAPI backend and Streamlit frontend
7. **Test Recommendations**: Try both phone lookup and manual entry modes

### **✅ Setup Verification Checklist**
- [ ] **Database connection tested** (`python test_database_availability.py`)
- [ ] **Required tables present** (`ml_citizen_master`, `ml_district`, `ml_provision`, `ml_service_master`)
- [ ] **Operational mode confirmed** (Database/Hybrid/CSV)
- [ ] **Environment variables configured** (`backend/.env`)
- [ ] **Python dependencies installed** (`pip install -r requirements.txt`)
- [ ] **Backend API running** (Port 8000)
- [ ] **Database status endpoint working** (`GET /database-status`)
- [ ] **Recommendations tested** (Phone lookup and manual entry)
- [ ] **Scheduler running** (`GET /scheduler-status`)

---

## 🔧 **Advanced Configuration & Optimization**

### **🚀 Performance Optimization**

The system offers multiple optimization strategies:

**Database-to-CSV Hybrid Approach:**
```python
# Custom optimization: Convert database to intermediate CSV tables
# This provides best of both worlds - database consistency + CSV speed

# Option 1: Scheduled CSV generation from database
POST /convert-database-to-csv  # Convert all tables daily

# Option 2: Selective table conversion
POST /convert/citizens         # Convert only citizen data
POST /convert/districts        # Convert only district data  

# Option 3: Memory optimization
MAX_RECOMMENDATIONS=3          # Reduce memory usage
BATCH_SIZE=1000               # Process in smaller chunks
```

**Production Optimizations:**
- **Database Indexing**: Create indexes on `citizen_id`, `district_id`, `service_id` columns
- **Connection Pooling**: Use PostgreSQL connection pooling for high traffic
- **Caching Strategy**: Cache frequently accessed district/demographic data
- **CSV Preloading**: Pre-generate CSV files during low-traffic periods

### **🔄 Operational Mode Switching**

**Dynamic Mode Management:**
```bash
# Check current mode
curl -X GET "http://localhost:8000/database-status"

# Force CSV fallback mode (for maintenance)
export FORCE_CSV_MODE=true

# Re-enable database mode
export FORCE_CSV_MODE=false
```

**Mode-Specific Endpoints:**
- **Database Mode**: All endpoints available
- **Hybrid Mode**: Limited database operations, CSV fallback active
- **CSV Mode**: Database endpoints return 400 (Bad Request)

---

## 📚 **Repository Commit Guide**

This repository contains multiple implementation approaches across different commits:

### **🏷️ Key Commits & Versions**

**📁 Commit #1: Pure CSV Implementation**
- **Branch/Tag**: `csv-only-mode`
- **Description**: Complete CSV-based system with fallback error handling
- **Use Case**: Development, testing, environments without database access
- **Features**: File-based data loading, error-tolerant CSV processing
- **Best For**: Quick setup, development environments, demo purposes

**🗄️ Commit #2: Database Setup Version** 
- **Branch/Tag**: `database-setup`  
- **Description**: Database connectivity with CSV conversion capabilities
- **Use Case**: Production setup with database-to-CSV conversion workflow
- **Features**: Database schema creation, data migration tools, CSV export
- **Best For**: Initial database setup, data migration scenarios

**🔀 Commit #3: Hybrid Implementation**
- **Branch/Tag**: `hybrid-mode`
- **Description**: Smart database connectivity with automatic CSV fallback
- **Use Case**: Production with graceful degradation capabilities  
- **Features**: Intelligent mode detection, automatic fallback, error resilience
- **Best For**: Production environments, high availability requirements

**⚡ Commit #4: Direct Database Mode** *(Current)*
- **Branch/Tag**: `main` / `direct-database`
- **Description**: Direct database connections with CSV as fallback only
- **Use Case**: Full production deployment with real-time database access
- **Features**: Real-time queries, optimal performance, database-first approach
- **Best For**: Production systems, real-time requirements, scalable deployments

### **🎯 Choosing the Right Version**

**For Development:** Use **Commit #1** (CSV-only)
```bash
git checkout csv-only-mode
# Fast setup, no database required
```

**For Migration:** Use **Commit #2** (Database Setup)
```bash  
git checkout database-setup
# Perfect for setting up database schema
```

**For Staging:** Use **Commit #3** (Hybrid Mode)
```bash
git checkout hybrid-mode  
# Best for testing database connectivity
```

**For Production:** Use **Commit #4** (Direct Database) *(Current)*
```bash
git checkout main
# Optimal performance and scalability
```

### **🔄 Migration Path**

**Recommended Migration Sequence:**
1. **Start with CSV** → Commit #1 for proof-of-concept
2. **Setup Database** → Commit #2 for schema creation  
3. **Test Hybrid** → Commit #3 for connectivity validation
4. **Deploy Production** → Commit #4 for full implementation

---

## ⚙️ System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended for large datasets)
- **Storage**: 10GB free space (more for large similarity matrices)
- **CPU**: Multi-core processor recommended for parallel processing

### Production Requirements
- **Database**: PostgreSQL/MySQL for production data storage
- **Cloud Storage**: AWS S3/Azure Blob for large file storage
- **Server**: Linux-based server with cron job support
- **API Keys**: Valid OpenAI API key with sufficient credits

### Network Requirements
- **Internet Access**: Required for OpenAI API calls
- **Database Connection**: Stable connection to client database
- **Port Access**: Port 8000 for FastAPI, Port 8501 for Streamlit

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd recomm
   ```

2. **Copy required configuration files**
   ```bash
   # Copy Category 2 files from data_backup to data folder
   cp data_backup/services.csv data/
   cp data_backup/service_with_domains.csv data/
   cp data_backup/openai_similarity_matrix.csv data/
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy and edit the .env file in backend folder
   cp backend/.env.example backend/.env
   # Note: OpenAI API key is optional if using provided similarity matrix
   ```

5. **Run the backend API**
   ```bash
   uvicorn backend.main:app --reload
   ```

6. **Run the frontend app**
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```

---

## 📊 Data Management & Database Integration

### **🔄 Data Loading Strategy**

The system uses a **CSV-first with database fallback** approach for optimal performance:

1. **Development Mode**: Loads from CSV files in `data/` directory for fast iteration
2. **Production Mode**: Falls back to database queries when CSV files are unavailable  
3. **Hybrid Mode**: Uses both CSV cache and live database connections

### **🗄️ Database-to-CSV Conversion System**

Convert your PostgreSQL database tables to CSV files for development and backup:

#### **📋 Supported Table Mappings:**
| Database Table | CSV Output | Purpose |
|---------------|------------|---------|
| `ml_citizen_master` | `ml_citizen_master.csv` | Citizen demographics & history |
| `ml_district` | `ml_district.csv` | District information |
| `ml_provision` | `ml_provision.csv` | Service provision records |
| `ml_service_master` | `service_master.csv` | Service definitions |

#### **🚀 Quick Conversion Commands:**

**Convert All Tables:**
```bash
python test_database_conversion.py
# OR via API:
curl -X POST "http://localhost:8000/convert/all"
```

**Convert Individual Tables:**
```bash
curl -X POST "http://localhost:8000/convert/citizens"
curl -X POST "http://localhost:8000/convert/districts"  
curl -X POST "http://localhost:8000/convert/provisions"
curl -X POST "http://localhost:8000/convert/services"
```

**Batch Processing:**
- Processes large tables (765K+ records) in configurable chunks
- Automatic data validation and error handling
- Progress monitoring and detailed logging
- Output saved to `data_backup/` for verification

#### **⚙️ Database Configuration**

Set up your database connection in `backend/.env`:

```env
# PostgreSQL Database Connection
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Example:
DATABASE_URL=postgresql://postgres:4790@localhost:5432/dbo
```

#### **🔍 Conversion Validation**

The system provides comprehensive validation:

```json
{
  "conversion_summary": {
    "ml_citizen_master": {
      "status": "success",
      "records_converted": 765767,
      "file_path": "data_backup/ml_citizen_master.csv"
    },
    "ml_district": {
      "status": "success", 
      "records_converted": 138,
      "file_path": "data_backup/ml_district.csv"
    }
  }
}
```

---

## 📊 Data Requirements

The system requires different categories of data files organized as follows:

### 📋 **Category 1: Raw Database Files** *(Required from Client Database)*
These files must be provided from the client's existing database and updated regularly:

- **`ml_citizen_master.csv`** - Citizen demographic data (phone, age, gender, caste, religion, district)
- **`ml_provision.csv`** - Service provision history (citizen_id, service_id, timestamps)
- **`ml_district.csv`** - District information and metadata
- **`service_master.csv`** - Basic service information from client database

> **⚠️ Production Deployment Note**: For production deployment, these 4 CSV files should be replaced with direct database connections. Update the data loading logic in the inference modules to connect to your database instead of reading CSV files.

### 🛠️ **Category 2: System-Provided Configuration Files** *(Pre-configured by Our Development Team)*
These files are provided by our development team and contain enhanced service metadata:

**📁 Files to Copy from `data_backup/` to `data/` folder:**

- **`services.csv`** - Service eligibility criteria (age, religion, gender, caste filters)
  - Defines who can access which services based on demographic criteria
  - Used for filtering inappropriate service recommendations
  - **Action Required**: Copy from `data_backup/services.csv` to `data/services.csv`

- **`service_with_domains.csv`** - Service descriptions for similarity calculations
  - Enhanced service descriptions with domain categorization
  - Pre-processed for content-based recommendations
  - **Action Required**: Copy from `data_backup/service_with_domains.csv` to `data/service_with_domains.csv`

- **`openai_similarity_matrix.csv`** - Pre-computed service similarity matrix
  - Ready-to-use similarity matrix to save OpenAI API costs
  - Contains cosine similarity scores between all services
  - **Action Required**: Copy from `data_backup/openai_similarity_matrix.csv` to `data/openai_similarity_matrix.csv`
  - **Cost Benefit**: Using this pre-computed matrix saves OpenAI API costs and processing time

> **📝 Setup Instructions**: 
> 1. Copy all three files from `data_backup/` folder to `data/` folder
> 2. These files are maintained by the development team and updated when service catalog changes
> 3. Using the provided `openai_similarity_matrix.csv` eliminates the need for initial OpenAI API calls

### 🔄 **Category 3: Auto-Generated Processing Files** *(Generated Automatically)*
These files are automatically generated by the system when APIs are called:

**Generated by Demographic Helper:**
- `grouped_df.csv` - Demographic clusters
- `cluster_service_map.pkl` - Cluster to service mapping  
- `service_id_with_name.csv` - Service ID to name mapping
- `final_df.csv` - Processed citizen data with service encoding

**Generated by District Helper:**
- `district_top_services.csv` - Popular services by district

**Generated by Content Helper:**
- `service_with_domains.csv` - Service descriptions for similarity
- `openai_similarity_matrix.csv` - Service similarity matrix (stored in cloud storage for production)

### ☁️ **Production Storage Recommendations**
- **OpenAI Similarity Matrix**: Store in cloud storage bucket (S3/Azure Blob) due to large file size
- **Cluster Service Map**: Can be stored in database or cloud storage
- **Generated CSV files**: Convert to database tables for better performance and scalability

---

## 🗄️ **Production Database Conversion**

### **For Production Deployment**
The current CSV-based system is designed for development and testing. For production deployment, follow these conversion guidelines:

#### **CSV to Database Table Conversion Required:**

**Raw Database Files (Category 1):**
- `ml_citizen_master.csv` → `citizens` table
- `ml_provision.csv` → `service_provisions` table  
- `ml_district.csv` → `districts` table
- `service_master.csv` → `services` table

**Generated Processing Files (Category 3):**
- `grouped_df.csv` → `demographic_clusters` table
- `final_df.csv` → `processed_citizens` table
- `district_top_services.csv` → `district_popular_services` table
- `service_id_with_name.csv` → Can be integrated into `services` table

#### **Files to Keep as Storage/Cache:**
- `cluster_service_map.pkl` → Store in cloud storage or Redis cache
- `openai_similarity_matrix.csv` → Store in cloud storage bucket (S3/Azure Blob)

#### **Code Modification Requirements:**
1. Update all data loading functions in `backend/inference/` modules
2. Replace `pd.read_csv()` calls with database queries
3. Update helper functions in `backend/helpers/` to work with database connections
4. Modify scheduler functions to update database tables instead of generating CSV files

> **⚠️ Critical**: Test all recommendation engines thoroughly after database conversion to ensure data consistency and performance.

---

## 🕐 Automated Data Refresh (Cron Jobs)

The system includes automated background tasks to keep recommendation data fresh:

### **Daily Demographic Refresh**
- **Schedule**: Every day at 9:00 PM (21:00) - configured in `backend/main.py`
- **Purpose**: Refreshes demographic clusters and citizen service provisions
- **Triggers**: `scheduled_generate_demo_csvs()` function
- **Updates**: `grouped_df.csv`, `cluster_service_map.pkl`, `service_id_with_name.csv`, `services.csv`, `final_df.csv`
- **Rationale**: Keeps demographic recommendations current with new citizen registrations and service provisions

### **Monthly District Refresh**  
- **Schedule**: 1st of every month at 3:00 AM (03:00) - configured in `backend/main.py`
- **Purpose**: Updates popular services by district based on historical usage patterns
- **Triggers**: `scheduled_generate_district_csvs()` function
- **Updates**: `district_top_services.csv`
- **Rationale**: District service popularity changes more slowly, monthly updates are sufficient

### **Manual Content Refresh**
- **Schedule**: On-demand (triggered manually by admin/developer)
- **When to Trigger**: 
  - When service descriptions are modified or enhanced
  - When new services are added to the system
  - When existing services are removed or deprecated
  - When OpenAI embeddings need to be regenerated
- **How to Trigger**: `POST /generate-content-csvs` endpoint
- **Updates**: `service_with_domains.csv`, `openai_similarity_matrix.csv`
- **Note**: This process involves OpenAI API calls and can be time-intensive for large service catalogs

> **⚠️ Important**: Content refresh should be done carefully as it regenerates the entire similarity matrix. Plan for system downtime during large content updates.

> **Note**: The automated refresh ensures recommendations stay current with changing usage patterns and new citizen registrations.

---

## � Security Considerations

### Data Privacy
- **Citizen Data**: Contains sensitive personal information (phone, demographics)
- **Access Control**: Implement proper authentication for production deployment
- **Data Encryption**: Encrypt sensitive data at rest and in transit
- **Audit Logging**: Log all recommendation requests for compliance

### API Security
- **Rate Limiting**: Implement rate limiting for public endpoints
- **Input Validation**: Validate all user inputs to prevent injection attacks
- **HTTPS**: Use HTTPS in production for encrypted communication
- **Environment Variables**: Keep API keys and secrets in secure environment files

### Production Hardening
- **Database Security**: Use connection pooling and prepared statements
- **File Permissions**: Restrict access to data files and configuration
- **Server Security**: Regular security updates and monitoring
- **Backup Strategy**: Regular backups of critical data and configurations

---

## �🔧 Configuration

### Environment Variables
Set these in `backend/.env`:

**Required:**
- `OPENAI_API_KEY` - OpenAI API key for embeddings (get from platform.openai.com)

**Optional:**
- `DATABASE_URL` - Database connection string (for production deployment)
- `CLOUD_STORAGE_BUCKET` - Cloud storage bucket name for large files
- `MAX_RECOMMENDATIONS` - Maximum number of recommendations per engine (default: 5)
- `SCHEDULER_TIMEZONE` - Timezone for cron jobs (default: local timezone)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

**Example .env file:**
```
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/recomm_db
CLOUD_STORAGE_BUCKET=my-recomm-storage
MAX_RECOMMENDATIONS=5
SCHEDULER_TIMEZONE=Asia/Kolkata
LOG_LEVEL=INFO
```

### Service Filtering
The system automatically filters out:
- Birth and death certificate services
- Caste-specific services for General category users
- Age-inappropriate services

---

## 📈 Usage

### Phone Number Lookup
1. Enter phone number (e.g., 7001337407)
2. System finds citizen demographics
3. Generates personalized recommendations

### Manual Entry
1. Enter demographic information
2. Select target service
3. Get recommendations across all three engines

---

## 🚀 Backend API (FastAPI)

### Start the API server

```sh
uvicorn backend.main:app --reload
```

### Main Endpoint: `/recommend`

#### Request Examples

**Phone Number Mode**
```json
POST /recommend
{
  "mode": "phone",
  "phone": "7602690034",
  "selected_service_id": 101
}
```

**Manual Entry Mode**
```json
POST /recommend
{
  "mode": "manual",
  "district_id": 2,
  "gender": "Male",
  "caste": "General",
  "age": 30,
  "religion": "Hindu",
  "selected_service_id": 101
}
```

#### Response Example

```json
{
  "district_recommendations": ["Service A", "Service B", "..."],
  "demographic_recommendations": ["Service X", "Service Y", "..."],
  "item_recommendations": {
    "Service 101": ["Similar Service 1", "Similar Service 2", "..."]
  }
}
```

- `district_recommendations`: Top services for the district.
- `demographic_recommendations`: Services recommended based on demographic data.
- `item_recommendations`: Dictionary mapping the selected service to a list of similar services.

---

### CSV Generation Endpoints

The backend provides endpoints to generate all required CSVs for inference modules:

#### **Automatic Generation**
- **Demographic CSVs**: Automatically generated daily at 9:00 PM
- **District CSVs**: Automatically generated monthly on 1st at 3:00 AM

#### **Manual Generation Endpoints**
- `POST /generate-district-csvs` → Generates district-related CSV files (see `backend/helpers/district_helper.py`)
- `POST /generate-demo-csvs` → Generates demographic-related CSV files (see `backend/helpers/demo_helper.py`)  
- `POST /generate-content-csvs` → Generates content-related CSV files (see `backend/helpers/content_helper.py`)

#### **Scheduler Management Endpoints**
- `GET /scheduler-status` → Check scheduler status and next run times
- `POST /trigger-nightly-csvs` → Manually trigger demographic CSV generation
- `POST /trigger-monthly-csvs` → Manually trigger district CSV generation
- `POST /trigger-all-csvs` → Manually trigger both demographic and district CSV generation

Each returns a status and a list of generated files or error details.

---

## 🛠️ Helper Functions

The `backend/helpers/` directory contains scripts to generate all required CSVs from the main data files in `data/`.

### Main Data Files

- `data/service_master.csv` - Service information
- `data/ml_district.csv` - District information
- `data/ml_provision.csv` - Service provision records
- `data/ml_citizen_master.csv` - Citizen information

### Helper Scripts

- `demo_helper.py` &rarr; Generates:
  - `grouped_df.csv`
  - `cluster_service_map.pkl`
  - `service_id_with_name.csv`
  - `services.csv`
  - `final_df.csv`
- `district_helper.py` &rarr; Generates:
  - `district_top_services.csv`
- `content_helper.py` &rarr; Generates:
  - `service_master_enhanced.csv`
  - `openai_similarity_matrix.csv`

#### Example Usage

```python
from backend.helpers.demo_helper import generate_demo_csv_files
from backend.helpers.district_helper import generate_district_csv_files
from backend.helpers.content_helper import main as generate_content_csv_files

generate_demo_csv_files()
generate_district_csv_files()
generate_content_csv_files()
```

---

## 📋 Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all functions
- Keep functions focused and small

---

## � **Production Deployment Guide**

### **📋 Development vs Production**

**Development Setup (CSV-only):**
- All data files stored as CSV in `data/` folder
- Direct file reading for fast development
- No database required

**Production Setup (Database Integration):**
- Primary data in PostgreSQL/MySQL database
- CSV files as backup/cache
- Flexible loading strategy (CSV first, database fallback)

### **🔄 Migration Steps: CSV to Database**

#### **Step 1: Database Preparation**
```bash
# 1. Set up PostgreSQL database
# 2. Create tables matching your CSV structure
# 3. Update DATABASE_URL in .env file
```

#### **Step 2: Environment Configuration**
```env
# Production .env file
DATABASE_URL=postgresql://user:password@prod-server:5432/recomm_db
OPENAI_API_KEY=your_production_openai_key
MAX_RECOMMENDATIONS=5
LOG_LEVEL=INFO
```

#### **Step 3: Table Creation**
```bash
# Use the setup script to create tables
cd backend
python setup_database.py
```

#### **Step 4: Data Migration**
```bash
# Option A: Load existing CSV data into database
python setup_database.py  # Choose option 2 or 3

# Option B: Convert database to CSV (if database already has data)
curl -X POST "http://your-prod-server/convert-database-to-csv"
```

#### **Step 5: Validation**
```bash
# Check data availability
curl -X GET "http://your-prod-server/data-status"

# Test recommendations
curl -X POST "http://your-prod-server/recommend" \
-H "Content-Type: application/json" \
-d '{"mode": "manual", "district_id": 1, "gender": "Male", "caste": "General", "age": 30, "religion": "Hindu", "selected_service_id": 101}'
```

### **📊 Database Table Requirements**

Your PostgreSQL database should have these exact table names:
- `ml_citizen_master` - Contains citizen demographics
- `ml_provision` - Contains service usage history  
- `ml_district` - Contains district information
- `ml_service_master` - Contains service catalog

### **🔧 Production Configuration**

#### **Process Management**
```bash
# Using systemd (Linux)
sudo systemctl enable recomm-api
sudo systemctl start recomm-api

# Using Docker
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/recomm \
  -e MAX_RECOMMENDATIONS=5 \
  recomm-api:latest
```

#### **Logging Configuration**
```python
# Production logging in backend/main.py
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/recomm-api.log'),
        logging.StreamHandler()
    ]
)
```

#### **Security Considerations**
- Use environment variables for all secrets
- Implement API authentication for production
- Secure database connections with SSL
- Restrict file permissions on CSV files
- Use HTTPS for API endpoints

### **⚡ Performance Optimization**

#### **Database Indexing**
```sql
-- Recommended indexes for better performance
CREATE INDEX idx_citizen_phone ON ml_citizen_master(citizen_phone);
CREATE INDEX idx_citizen_district ON ml_citizen_master(district_id);
CREATE INDEX idx_provision_citizen ON ml_provision(customer_id);
CREATE INDEX idx_provision_service ON ml_provision(service_id);
```

#### **Connection Pooling**
```python
# Update DATABASE_URL for connection pooling
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=10&max_overflow=20
```

#### **Caching Strategy**
- Cache frequently requested recommendations
- Use Redis for session storage
- Implement API response caching for static data

---

## �🔍 Troubleshooting

### Common Issues

**File Path Issues:**
- Ensure all paths are relative to project root
- Check file permissions for read/write access to `data/` folder
- Verify working directory is set to project root when running scripts

**Missing Data:**
- Verify all required CSV files exist in `data/` directory
- Check file formats and encodings (should be UTF-8)
- Ensure Category 1 files are provided by client before first run

**Scheduler Issues:**
- Check if scheduler is running: `GET /scheduler-status`
- Verify cron job timing in `backend/main.py`
- Check server timezone settings for correct scheduling
- Monitor scheduler logs for execution failures

**API Response Issues:**
- Verify all CSV files are generated before calling `/recommend`
- Check OpenAI API key is valid in `.env` file
- Ensure sufficient OpenAI API credits for content-based recommendations
- Validate input data format matches expected schema

**Performance Issues:**
- Large similarity matrix files may cause memory issues
- Consider using cloud storage for `openai_similarity_matrix.csv`
- Monitor server resources during scheduled CSV generation
- Database queries may be slower than CSV reads during development

**Dependency Issues:**
- Run `pip install -r requirements.txt` to ensure all packages are installed
- Check for NumPy/SciPy compatibility warnings (non-critical)
- Verify Python version compatibility (3.8+)

**Database Connection Issues:**
- If experiencing persistent database connectivity problems, consider reverting to the previous CSV-only version
- This current commit includes database integration; the previous commit was purely CSV-based
- To revert: `git checkout <previous-commit-hash>` where the system worked entirely with CSV files
- Change the csv to database connection.
- Alternative: Replace database calls with direct CSV loading in your code if you prefer database-free operation

---



## ⚡ Performance Optimization

### For Large Datasets
- **Similarity Matrix**: Store in cloud storage and cache frequently used portions
- **Database Indexing**: Create indexes on frequently queried columns (citizen_id, service_id, district_id)
- **Batch Processing**: Process recommendations in batches for bulk operations
- **Caching Strategy**: Implement Redis caching for frequently requested recommendations

### Memory Management
- **Large File Handling**: Stream large CSV files instead of loading entirely into memory
- **Pickle Files**: Use compression for cluster_service_map.pkl files
- **Garbage Collection**: Explicit cleanup after processing large datasets

### API Optimization
- **Response Caching**: Cache recommendation results for repeated requests
- **Async Processing**: Use asynchronous processing for I/O operations
- **Connection Pooling**: Use database connection pools for production
- **Load Balancing**: Distribute requests across multiple server instances

### Scalability Enhancement
For maximum scalability, implement microservices architecture by separating recommendation engines into independent services with message queue communication. Additionally, utilize horizontal database sharding and implement distributed caching with Redis clusters to handle high-throughput production workloads.

---


