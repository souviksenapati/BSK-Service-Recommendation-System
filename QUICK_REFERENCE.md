# 🚀 Quick Reference - Bangla Sahayata Kendra API

## Start the Application

### Windows
```bash
start_api.bat
```

### Linux/Mac
```bash
./start_api.sh
```

### Manual
```bash
cd api
python main.py
```

---

## Access URLs

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## API Endpoints Quick Reference

### GET Endpoints
```
GET  /                                    # Frontend HTML
GET  /api/health                         # Health check
GET  /api/districts                      # List districts
GET  /api/services                       # List services
GET  /api/citizen/phone/{phone}          # Search by phone
GET  /api/citizen/{citizen_id}/services  # Get citizen services
```

### POST Endpoints
```
POST /api/recommend/phone                # Phone search recommendations
POST /api/recommend/manual               # Manual entry recommendations
```

---

## Sample API Requests

### Search Citizen
```bash
curl http://localhost:8000/api/citizen/phone/9800361474
```

### Get Recommendations (Phone)
```bash
curl -X POST http://localhost:8000/api/recommend/phone \
  -H "Content-Type: application/json" \
  -d '{"citizen_id": "GRPA_12369567", "selected_service_id": 124}'
```

### Get Recommendations (Manual)
```bash
curl -X POST http://localhost:8000/api/recommend/manual \
  -H "Content-Type: application/json" \
  -d '{
    "district_id": 1,
    "gender": "Male",
    "caste": "General",
    "age": 30,
    "religion": "Hindu",
    "selected_service_id": 124
  }'
```

---

## File Structure

```
api/
├── main.py              # FastAPI app
├── requirements.txt     # Dependencies
├── runtime.txt          # Python version
└── static/
    ├── index.html      # Frontend
    ├── styles.css      # Styling
    └── script.js       # Logic
```

---

## Deployment Commands

### Railway
```bash
railway login
railway init
railway up
```

### Render
- Just connect GitHub repo
- Auto-detects configuration

### Heroku
```bash
heroku create bangla-sahayata-kendra
git push heroku main
```

### Docker
```bash
docker build -t bsk-api .
docker run -p 8000:8000 bsk-api
```

### Docker Compose
```bash
docker-compose up -d
```

---

## Troubleshooting

### Port in Use
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Module Not Found
```bash
pip install -r api/requirements.txt
```

### Data Files Missing
- Ensure `data/` folder exists
- Check all CSV files are present

---

## Key Files to Edit

### Update CORS (Production)
File: `api/main.py`
```python
allow_origins=["https://yourdomain.com"]  # Change from ["*"]
```

### Update Branding
Files: `api/static/index.html`, `api/static/styles.css`

---

## Sample Test Data

### Phone Numbers
- 9800361474
- 8293058992
- 9845120211

### Manual Entry Sample
- District: Any from dropdown
- Gender: Male/Female
- Age: 30
- Caste: General
- Religion: Hindu
- Service: Select from dropdown

---

## Important Notes

✅ Original Streamlit app untouched  
✅ Backend and frontend separated  
✅ Production-ready code  
✅ Professional UI with branding  
✅ All features preserved  
✅ Multiple deployment options  

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Full Guide**: See `DEPLOYMENT_GUIDE.md`
- **Summary**: See `API_PROJECT_SUMMARY.md`
- **GitHub**: https://github.com/amitkarmakar07/BSK-SER

---

**🏛️ Bangla Sahayata Kendra**  
*Service Recommendation System*
