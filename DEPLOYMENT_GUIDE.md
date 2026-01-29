# Bangla Sahayata Kendra - Complete Deployment Guide

## 🚀 Quick Start

### Local Development (Windows)
```bash
# Double-click or run:
start_api.bat

# Or manually:
cd api
pip install -r requirements.txt
python main.py
```

### Local Development (Linux/Mac)
```bash
chmod +x start_api.sh
./start_api.sh

# Or manually:
cd api
pip install -r requirements.txt
python main.py
```

Access at: **http://localhost:8000**

---

## 📁 Project Structure

```
SysReco/
├── api/                          # FastAPI Backend & Frontend
│   ├── main.py                  # FastAPI application
│   ├── requirements.txt         # Python dependencies
│   ├── runtime.txt              # Python version
│   ├── README.md                # API documentation
│   ├── __init__.py
│   └── static/                  # Frontend files
│       ├── index.html          # Main page
│       ├── styles.css          # Styling
│       └── script.js           # JavaScript
├── backend/                      # Inference logic (used by API)
│   ├── inference/
│   │   ├── content.py
│   │   ├── demo.py
│   │   └── district.py
│   └── ...
├── data/                         # CSV & Pickle files
│   ├── services.csv
│   ├── ml_citizen_master.csv
│   ├── ml_provision.csv
│   └── ...
├── frontend/                     # Original Streamlit app (kept separate)
│   └── streamlit_app.py
├── start_api.bat                # Windows startup script
├── start_api.sh                 # Linux/Mac startup script
├── Dockerfile                   # Docker deployment
├── docker-compose.yml           # Docker Compose
├── Procfile                     # Heroku/Railway
└── vercel.json                  # Vercel deployment
```

---

## 🌐 Deployment Options

### Option 1: Railway (Recommended - Easiest)

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Configure**
   - Railway will auto-detect the Procfile
   - Set root directory to `/api` if needed
   - Add environment variable: `PORT=8000`

4. **Done!** Railway will provide a URL

---

### Option 2: Render

1. Go to [render.com](https://render.com)
2. Create new **Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name**: bangla-sahayata-kendra
   - **Root Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.8+

5. Click **Create Web Service**

---

### Option 3: Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create bangla-sahayata-kendra
   ```

3. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy API"
   git push heroku main
   ```

4. **Scale**
   ```bash
   heroku ps:scale web=1
   ```

---

### Option 4: DigitalOcean App Platform

1. Go to [DigitalOcean](https://cloud.digitalocean.com/apps)
2. Create new **App**
3. Connect GitHub repository
4. Configure:
   - **Source Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `uvicorn main:app --host 0.0.0.0 --port 8080`
   - **HTTP Port**: 8080

5. Click **Launch App**

---

### Option 5: Docker Deployment

#### Build and Run Locally
```bash
# Build image
docker build -t bangla-sahayata-kendra .

# Run container
docker run -p 8000:8000 bangla-sahayata-kendra
```

#### Using Docker Compose
```bash
docker-compose up -d
```

#### Deploy to Cloud with Docker
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean Container Registry**

---

### Option 6: Vercel (Serverless)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

3. **Configure**
   - Vercel will use `vercel.json` automatically
   - Python runtime is supported

**Note**: Vercel has size limits; ensure data files are optimized

---

### Option 7: AWS EC2

1. **Launch EC2 Instance** (Ubuntu 20.04+)

2. **SSH into instance**
   ```bash
   ssh ubuntu@your-ec2-ip
   ```

3. **Setup**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python 3.8+
   sudo apt install python3 python3-pip -y
   
   # Clone repository
   git clone https://github.com/amitkarmakar07/BSK-SER.git
   cd BSK-SER
   
   # Install dependencies
   pip3 install -r api/requirements.txt
   
   # Run with screen or tmux
   screen -S api
   cd api
   python3 main.py
   # Press Ctrl+A, D to detach
   ```

4. **Configure Security Group**
   - Allow inbound port 8000

5. **Access**: http://your-ec2-ip:8000

---

### Option 8: Azure App Service

1. Go to [Azure Portal](https://portal.azure.com)
2. Create **Web App**
3. Configure:
   - **Runtime**: Python 3.8+
   - **Deployment**: GitHub Actions or Local Git

4. **Deploy using Azure CLI**
   ```bash
   az webapp up --name bangla-sahayata-kendra --runtime "PYTHON:3.8"
   ```

---

## 🔧 Production Configuration

### Environment Variables
```bash
# Optional - defaults are fine for most deployments
PORT=8000
HOST=0.0.0.0
```

### CORS Configuration
Edit `api/main.py` for production CORS:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Change from ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Data Files
Ensure all CSV files in `data/` are committed:
- ✅ `services.csv`
- ✅ `ml_citizen_master.csv`
- ✅ `ml_provision.csv`
- ✅ `district_top_services.csv`
- ✅ `service_with_domains.csv`
- ✅ `openai_similarity_matrix.csv`
- ✅ `cluster_service_map.pkl`
- ✅ `service_id_with_name.csv`
- ✅ `grouped_df.csv`
- ✅ `final_df.csv`

---

## 📊 System Requirements

### Minimum
- **CPU**: 1 vCPU
- **RAM**: 512 MB
- **Storage**: 500 MB
- **Python**: 3.8+

### Recommended
- **CPU**: 2 vCPUs
- **RAM**: 1 GB
- **Storage**: 1 GB
- **Python**: 3.8 - 3.10

---

## 🧪 Testing

### API Health Check
```bash
curl http://localhost:8000/api/health
```

### Test Endpoints
```bash
# Get districts
curl http://localhost:8000/api/districts

# Get services
curl http://localhost:8000/api/services

# Search citizen
curl http://localhost:8000/api/citizen/phone/9800361474
```

---

## 📱 Frontend Features

✅ **Phone Number Search** - Find citizens by mobile  
✅ **Manual Entry** - Enter demographics manually  
✅ **District Recommendations** - Popular services in area  
✅ **Demographic Recommendations** - Based on age/gender/caste/religion  
✅ **Content-based Recommendations** - Similar services using AI  
✅ **Responsive Design** - Works on all devices  
✅ **Professional UI** - Government of West Bengal branding  

---

## 🔐 Security Checklist

- [x] Citizen names masked for privacy
- [x] Birth/death services filtered
- [x] Input validation on all endpoints
- [x] CORS configured (update for production)
- [ ] Add rate limiting (optional)
- [ ] Add authentication (if needed)
- [ ] Enable HTTPS in production

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Module Not Found
```bash
pip install -r api/requirements.txt
```

### Data Files Missing
Ensure you're running from project root and `data/` folder exists with all CSV files.

### CORS Errors
Update `allow_origins` in `api/main.py` to include your frontend domain.

---

## 📈 Performance Optimization

1. **Data Caching**: All data loaded once on startup
2. **Async Operations**: FastAPI handles concurrent requests
3. **Static File Serving**: Efficient static file delivery
4. **Pandas Optimization**: DataFrames cached in memory

---

## 🔄 Updates & Maintenance

### Update Code
```bash
git pull origin main
pip install -r api/requirements.txt
# Restart server
```

### Monitor Logs
```bash
# Check application logs
tail -f api.log

# Or use deployment platform's dashboard
```

---

## 📞 Support

- **API Docs**: http://your-domain/docs
- **GitHub**: https://github.com/amitkarmakar07/BSK-SER
- **Issues**: Report on GitHub Issues

---

## 🎯 Next Steps

1. ✅ Choose a deployment platform
2. ✅ Deploy the application
3. ✅ Test all endpoints
4. ✅ Configure production CORS
5. ✅ Set up monitoring (optional)
6. ✅ Enable HTTPS
7. ✅ Share URL with users!

---

**🏛️ Bangla Sahayata Kendra**  
*Government of West Bengal*  
*Powered by AI-driven Service Recommendation System*

---

## 🆚 Deployment Comparison

| Platform | Ease | Cost | Performance | Best For |
|----------|------|------|-------------|----------|
| **Railway** | ⭐⭐⭐⭐⭐ | Free tier | Fast | Quick deployments |
| **Render** | ⭐⭐⭐⭐⭐ | Free tier | Fast | Beginners |
| **Heroku** | ⭐⭐⭐⭐ | Paid | Good | Established apps |
| **DigitalOcean** | ⭐⭐⭐⭐ | $5+/mo | Great | Scalability |
| **AWS EC2** | ⭐⭐⭐ | Variable | Excellent | Full control |
| **Docker** | ⭐⭐⭐ | Variable | Excellent | Portability |
| **Vercel** | ⭐⭐⭐⭐ | Free tier | Fast | Serverless |

**Recommended**: Start with **Railway** or **Render** for easiest deployment!
