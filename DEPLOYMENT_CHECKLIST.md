# 🚀 BSK-SER Deployment Checklist

## 📦 Files Required for Deployment

When transferring project to a new system, ensure ALL these files are included:

### **Required Files:**
```
✅ Dockerfile
✅ docker-compose.yml
✅ docker-entrypoint.sh              ← Bash entrypoint (Unix LF format!)
✅ .dockerignore
✅ .gitattributes                    ← Ensures correct line endings
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
ls docker-entrypoint.sh         # ← Must exist (Unix LF format!)
ls setup_database_complete.py
ls .env.example
ls backend
ls data
```

---

## 🔧 If `docker-entrypoint.sh` is Missing:

**CRITICAL: Must have Unix (LF) line endings, not Windows (CRLF)!**

**Copy from development machine:**
```powershell
# After copying, convert line endings:
dos2unix docker-entrypoint.sh

# OR using PowerShell:
(Get-Content docker-entrypoint.sh -Raw) -replace "`r`n", "`n" | Set-Content docker-entrypoint.sh -NoNewline
```

**Then rebuild:**
```powershell
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

See `LINE_ENDINGS_FIX.md` for details.

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

- ❌ Missing `docker-entrypoint.sh` → Copy from dev system (convert to Unix LF!)
- ❌ Missing `data/` folder → Copy all CSV files
- ❌ Missing `backend/` folder → Copy entire backend directory
- ⚠️ Wrong line endings on `.sh` files → Run `dos2unix docker-entrypoint.sh`

---

## ✅ File Size Check:

```powershell
# data/ folder should be ~117 MB
Get-ChildItem data -Recurse | Measure-Object -Property Length -Sum
```
