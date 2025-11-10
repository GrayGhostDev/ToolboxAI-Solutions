# Render Deployment Fix - Start Command Error

**Issue:** Deployment failing with error: `Error: No such option: --worker-class Did you mean --workers?`

**Root Cause:** The start command in Render Dashboard is using `uvicorn` directly with `--worker-class`, which is a Gunicorn-only option.

---

## ✅ Solution: Update Start Command

### Go to Render Dashboard:
1. Navigate to: https://dashboard.render.com
2. Select service: **toolboxai-backend**
3. Go to: **Settings** tab
4. Find: **Start Command** field

### Replace with ONE of these commands:

#### **Option 1: Gunicorn with Uvicorn Workers (RECOMMENDED - Production Ready)**

```bash
gunicorn apps.backend.main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --worker-connections 500 --max-requests 5000 --max-requests-jitter 500 --timeout 30 --keep-alive 5 --graceful-timeout 30 --backlog 1024 --access-logfile - --error-logfile - --log-level info
```

**Benefits:**
- ✅ Graceful worker restarts
- ✅ Better process management
- ✅ Worker recycling (prevents memory leaks)
- ✅ Production-ready with 2 workers

---

#### **Option 2: Pure Uvicorn (SIMPLER - Good for Starter Plan)**

```bash
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT --workers 2 --loop uvloop --access-log --timeout-keep-alive 5 --limit-concurrency 500 --limit-max-requests 5000 --backlog 1024
```

**Benefits:**
- ✅ Simpler configuration
- ✅ Lower memory footprint
- ✅ Works well for Render Starter plan

---

#### **Option 3: Single Worker (MINIMAL - For Free/Starter Tier)**

```bash
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT --loop uvloop --access-log
```

**Benefits:**
- ✅ Lowest resource usage
- ✅ Good for testing/development
- ⚠️ No process management

---

## 📋 After Updating Start Command:

### Step 1: Save Changes
Click **"Save Changes"** in Render Dashboard

### Step 2: Trigger Manual Deploy
Click **"Manual Deploy"** → **"Deploy latest commit"**

### Step 3: Monitor Deployment
Watch the logs for:
```
==> Starting service with command: cd apps/backend && gunicorn main:app...
[INFO] Listening at: http://0.0.0.0:XXXX (PID)
[INFO] Using worker: uvicorn.workers.UvicornWorker
[INFO] Booting worker with pid: XXXX
```

### Step 4: Verify Deployment Success
Once deployment completes (5-10 minutes), test:

```bash
curl https://toolboxai-backend-8j12.onrender.com/health
```

**Expected Response:**
```json
{"status": "healthy", "service": "toolboxai-api"}
```

---

## 🔍 Why This Happened

Your `render.production.yaml` should use a root-level module path and avoid changing directories:
```yaml
startCommand: |
  gunicorn apps.backend.main:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    ...
```

If the Render Dashboard has a manual override, ensure it does not use invalid options, e.g.:
```bash
python -m uvicorn main:app --worker-class uvicorn.workers.UvicornWorker  # ❌ ERROR
```

**The Fix:**
1. Use fully-qualified module paths (e.g., `apps.backend.main:app`).
2. Do not `cd` into subdirectories in start commands (breaks imports like `from apps...`).
3. Prefer keeping the command in `render.production.yaml` over dashboard overrides.

---

## 🎯 Recommended Action

**Use Option 1 (Gunicorn with Uvicorn Workers)** because:
- ✅ Matches your `render.production.yaml` configuration
- ✅ Production-ready with proper process management
- ✅ Already configured with optimal settings
- ✅ Handles graceful shutdowns and worker recycling

After deployment succeeds, you can proceed with Phase 3 integration testing!

---

## 📝 Commands Comparison

| Command | Use Case | Pros | Cons |
|---------|----------|------|------|
| **Gunicorn + Uvicorn** | Production | Process management, graceful restarts | Slightly higher memory |
| **Pure Uvicorn (multi-worker)** | Starter/Small | Simple, lower memory | No process management |
| **Pure Uvicorn (single)** | Dev/Testing | Minimal resources | No concurrency |

---

**Created:** 2025-11-10
**Issue:** Render deployment failing with invalid uvicorn option
**Status:** Ready to deploy with corrected command
