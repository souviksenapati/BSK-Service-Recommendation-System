# 🚀 BSK-SER Deployment Checklist

## 📦 Files Required for Deployment

When transferring project to a new system, ensure ALL these files are included:

### **Required Files:**
```
✅ Dockerfile
✅ docker-compose.yml
✅ docker-entrypoint.sh          ← CRITICAL!
✅ .dockerignore
✅ requirements.txt
✅ setup_database_complete.py
✅ .env.example
✅ backend/ (entire folder)
✅ data/ (entire folder with CSV files - 117 MB)
```

### **Quick Verification:**

```powershell
# Check all required files exist
ls Dockerfile
ls docker-compose.yml
ls docker-entrypoint.sh         # ← Must exist!
ls setup_database_complete.py
ls .env.example
ls backend
ls data
```

---

## 🔧 If `docker-entrypoint.sh` is Missing:

**Copy from development machine OR create it manually:**

Create file: `docker-entrypoint.sh` with the exact content from development system.

**Then rebuild:**
```powershell
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📋 Complete Deployment Steps:

1. **Transfer all files** ✅
2. **Verify files exist** (see above)
3. **Create .env file**
   ```powershell
   cp .env.example .env
   notepad .env  # Edit credentials
   ```
4. **Build & Start**
   ```powershell
   docker-compose build
   docker-compose up -d
   ```
5. **Monitor logs**
   ```powershell
   docker-compose logs -f api
   ```

---

## ⚠️ Common Transfer Issues:

- ❌ Missing `docker-entrypoint.sh` → Copy from dev system
- ❌ Missing `data/` folder → Copy all CSV files
- ❌ Missing `backend/` folder → Copy entire backend directory
- ❌ Wrong line endings (CRLF vs LF) → Git autocrlf issue

---

## ✅ File Size Check:

```powershell
# data/ folder should be ~117 MB
Get-ChildItem data -Recurse | Measure-Object -Property Length -Sum
```
