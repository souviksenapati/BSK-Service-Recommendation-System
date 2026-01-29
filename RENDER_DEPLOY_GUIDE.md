# 🚀 Deploy to Render - Step by Step Guide

## Quick Deploy (5 Minutes)

### Step 1: Go to Render
1. Visit [Render Dashboard](https://dashboard.render.com)
2. Sign up or log in with GitHub

### Step 2: Create New Web Service
1. Click **"New"** button (top right)
2. Select **"Web Service"**

### Step 3: Connect Repository
1. Click **"Connect account"** if not connected
2. Search for: `amitkarmakar07/BSK-SER-FASTAPI`
3. Click **"Connect"**

### Step 4: Configure Service
Render will auto-fill most fields. Verify:

**Basic Settings:**
- **Name**: `bangla-sahayata-kendra` (or your choice)
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`

**Build & Deploy:**
- **Build Command**: 
  ```bash
  pip install -r api/requirements.txt
  ```

- **Start Command**:
  ```bash
  cd api && uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- **Free** (for testing)
- **Starter** ($7/month - recommended for production)

### Step 5: Environment Variables
No environment variables needed! Click **"Create Web Service"**

### Step 6: Wait for Deployment
- Render will build and deploy (3-5 minutes)
- Watch the logs for progress
- Look for: `✅ All data loaded successfully`

### Step 7: Access Your App
- Your app will be live at: `https://your-app-name.onrender.com`
- Frontend: `https://your-app-name.onrender.com/`
- API Docs: `https://your-app-name.onrender.com/docs`

---

## ✅ Verification Steps

### Test Frontend
1. Visit `https://your-app-name.onrender.com`
2. You should see "Bangla Sahayata Kendra" header
3. Try phone number: `9800361474`
4. Click "Search Citizen"

### Test API
```bash
# Health check
curl https://your-app-name.onrender.com/api/health

# Get districts
curl https://your-app-name.onrender.com/api/districts

# Get services
curl https://your-app-name.onrender.com/api/services
```

---

## 🎯 Expected Results

### Successful Deployment Logs
```
==> Building...
==> Installing dependencies from api/requirements.txt
Successfully installed fastapi uvicorn pandas numpy...
==> Starting service...
✅ All data loaded successfully
Uvicorn running on http://0.0.0.0:10000
```

### Live Application
- Frontend loads instantly
- Professional UI with Government branding
- Both input modes work (Phone & Manual)
- All three recommendation types display

---

## ⚙️ Configuration Reference

### render.yaml (Optional - already configured)
If you want to use Infrastructure as Code:

```yaml
services:
  - type: web
    name: bangla-sahayata-kendra
    env: python
    region: oregon
    buildCommand: pip install -r api/requirements.txt
    startCommand: cd api && uvicorn main:app --host 0.0.0.0 --port $PORT
    plan: free
```

---

## 🔧 Troubleshooting

### Issue: Build Fails
**Solution**: Check build logs for missing dependencies
```bash
# In Render logs, look for:
ERROR: Could not find a version that satisfies...

# Fix: Update api/requirements.txt with correct versions
```

### Issue: Application Won't Start
**Solution**: Check start command
```bash
# Correct start command:
cd api && uvicorn main:app --host 0.0.0.0 --port $PORT

# NOT:
python main.py  # This won't use Render's PORT
```

### Issue: Static Files Not Loading
**Solution**: Verify file structure
```bash
# Must have:
api/
  static/
    index.html
    styles.css
    script.js
```

### Issue: Data Files Missing
**Solution**: Check if data/ folder is in repo
```bash
# Required files in data/:
- ml_citizen_master.csv
- ml_provision.csv
- services.csv
- district_top_services.csv
- openai_similarity_matrix.csv
- cluster_service_map.pkl
```

---

## 🚀 Performance on Render

### Free Tier
- ✅ Perfect for testing
- ⏱️ Spins down after 15 min inactivity
- 🔄 Cold start: 30-60 seconds
- 💾 512 MB RAM

### Starter Tier ($7/month)
- ✅ Always running
- ⚡ No cold starts
- 💾 512 MB RAM
- 🌐 Custom domain support
- 📊 Better for production

---

## 📈 Next Steps After Deployment

### 1. Custom Domain (Optional)
1. Go to your service settings
2. Click "Custom Domain"
3. Add your domain (e.g., `bsk.westbengal.gov.in`)
4. Follow DNS instructions

### 2. HTTPS (Automatic)
Render provides free SSL certificates automatically!

### 3. Monitoring
- View logs in Render dashboard
- Set up health check alerts
- Monitor response times

### 4. Updates
To update your app:
```bash
git add .
git commit -m "Update"
git push fastapi main
```
Render auto-deploys on push!

---

## 💰 Cost Estimate

### Free Tier
- **Cost**: $0
- **Limitations**: Spins down, 15 min timeout
- **Best for**: Testing, demos

### Starter Tier
- **Cost**: $7/month
- **Limitations**: None for this app
- **Best for**: Production, always-on

### Professional Tier
- **Cost**: $25/month
- **Benefits**: More RAM, faster builds
- **Best for**: Heavy traffic

---

## 🎉 Success Checklist

- [ ] Repository pushed to GitHub
- [ ] Render account created
- [ ] Web service created
- [ ] Build completed successfully
- [ ] App is live and accessible
- [ ] Frontend loads correctly
- [ ] Phone search works
- [ ] Manual entry works
- [ ] All recommendations display
- [ ] API docs accessible at `/docs`

---

## 📞 Getting Help

### Render Support
- [Render Docs](https://render.com/docs)
- [Render Community](https://community.render.com)

### This Project
- [GitHub Issues](https://github.com/amitkarmakar07/BSK-SER-FASTAPI/issues)
- [API Documentation](https://your-app.onrender.com/docs)

---

## 🌟 Pro Tips

1. **Use Environment Variables**: For future API keys or configs
2. **Enable Auto-Deploy**: Automatic deployment on git push
3. **Set Up Notifications**: Get alerts when deployment fails
4. **Use Pull Request Previews**: Test changes before merging
5. **Monitor Logs**: Watch for errors or performance issues

---

**🏛️ Bangla Sahayata Kendra**  
*Deployed on Render - Fast, Reliable, Secure*

---

**Your app is now live! 🎉**  
Share it with users: `https://your-app-name.onrender.com`
