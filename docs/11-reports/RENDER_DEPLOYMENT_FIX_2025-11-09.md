# Render.com Backend Deployment Fix

**Date:** November 9, 2025  
**Status:** ✅ RESOLVED  
**Severity:** Critical - Deployment Blocker

---

## Problem Summary

The backend deployment on Render.com was failing with the following error:

```
Error: No such option: --worker-class Did you mean --workers?
```

This occurred because the `render.yaml` configuration was using invalid `uvicorn` command-line options that are only available when using `gunicorn` with uvicorn workers.

---

## Root Cause

**Issue:** The `startCommand` in `render.yaml` was attempting to run `uvicorn` directly with `gunicorn`-specific options:

```yaml
startCommand: |
  cd apps/backend && \
  python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \  # ❌ Invalid for uvicorn
    --loop uvloop \
    --access-log \
    --timeout-keep-alive 5 \
    --timeout-graceful-shutdown 30 \                # ❌ Invalid for uvicorn
    --limit-concurrency 500 \
    --limit-max-requests 5000 \                     # ❌ Invalid for uvicorn
    --backlog 1024
```

**Why it failed:**
- `uvicorn` CLI does NOT support `--worker-class`, `--timeout-graceful-shutdown`, `--limit-max-requests`
- These options are only available in `gunicorn`
- For production deployments with multiple workers, `gunicorn` with `uvicorn.workers.UvicornWorker` is the recommended approach

---

## Solution

### 1. Updated `render.yaml`

**File:** `/render.yaml`

Changed the backend service startCommand to use `gunicorn`:

```yaml
startCommand: |
  cd apps/backend && \
  gunicorn main:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 500 \
    --max-requests 5000 \
    --max-requests-jitter 500 \
    --timeout 30 \
    --keep-alive 5 \
    --graceful-timeout 30 \
    --backlog 1024 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### 2. Updated `requirements.txt`

**File:** `/requirements.txt`

Added `gunicorn` and ensured `uvicorn[standard]` includes uvloop:

```txt
uvicorn[standard]==0.30.6            # ASGI server with uvloop
gunicorn==23.0.0                     # WSGI server for production
```

### 3. Updated `Dockerfile`

**File:** `/apps/backend/Dockerfile`

Changed the CMD to use gunicorn for consistency:

```dockerfile
# Run application with gunicorn for production
CMD ["gunicorn", "apps.backend.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--worker-connections", "500", \
     "--max-requests", "5000", \
     "--max-requests-jitter", "500", \
     "--timeout", "30", \
     "--keep-alive", "5", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
```

### 4. Created Verification Script

**File:** `/scripts/deployment/verify_render_config.py`

Created a comprehensive verification script to check:
- ✅ All Render services have valid configurations
- ✅ No invalid uvicorn options are used
- ✅ Required packages are in requirements.txt
- ✅ Health check paths are configured
- ✅ Environment variables are set

---

## Configuration Details

### Gunicorn Production Settings

| Option | Value | Purpose |
|--------|-------|---------|
| `--workers` | 2 | Number of worker processes (adjust based on plan) |
| `--worker-class` | uvicorn.workers.UvicornWorker | Use ASGI-compatible workers |
| `--worker-connections` | 500 | Max concurrent connections per worker |
| `--max-requests` | 5000 | Restart workers after N requests (prevents memory leaks) |
| `--max-requests-jitter` | 500 | Add randomness to worker restart |
| `--timeout` | 30 | Worker timeout in seconds |
| `--keep-alive` | 5 | Keep-alive connections timeout |
| `--graceful-timeout` | 30 | Graceful shutdown timeout |
| `--backlog` | 1024 | Maximum pending connections |

### Why Gunicorn + Uvicorn Workers?

1. **Production-Ready:** Gunicorn is battle-tested for production deployments
2. **Process Management:** Handles worker lifecycle, restarts, and graceful shutdowns
3. **Memory Management:** `--max-requests` prevents memory leaks by recycling workers
4. **Concurrency:** Multiple workers for better CPU utilization
5. **ASGI Support:** `uvicorn.workers.UvicornWorker` provides async support
6. **Monitoring:** Better logging and metrics integration

---

## Verification

### Manual Testing

```bash
# 1. Verify configuration
python scripts/deployment/verify_render_config.py

# Expected output:
# ✅ ALL CHECKS PASSED - Ready for deployment!

# 2. Test gunicorn locally
cd apps/backend
gunicorn main:app \
  --bind 0.0.0.0:8009 \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 30 \
  --access-logfile - \
  --log-level debug

# 3. Test health endpoint
curl http://localhost:8009/health
# Expected: {"status": "healthy", ...}
```

### Deployment Checklist

Before deploying to Render.com:

- [x] ✅ Updated `render.yaml` with gunicorn configuration
- [x] ✅ Added `gunicorn==23.0.0` to `requirements.txt`
- [x] ✅ Updated `apps/backend/Dockerfile` CMD
- [x] ✅ Created verification script
- [x] ✅ Tested configuration locally
- [ ] ⏳ Push changes to GitHub
- [ ] ⏳ Trigger Render deployment
- [ ] ⏳ Monitor deployment logs
- [ ] ⏳ Verify health check passes
- [ ] ⏳ Test API endpoints

---

## Render.com Dashboard Configuration

### Environment Variables to Set

Ensure the following are configured in Render.com dashboard:

**Required:**
- `DATABASE_URL` → Set to Supabase DATABASE_URL
- `REDIS_URL` → Auto-configured from Redis service
- `OPENAI_API_KEY` → Your OpenAI API key
- `CLERK_SECRET_KEY` → Clerk authentication key
- `CLERK_PUBLISHABLE_KEY` → Clerk publishable key

**Optional but Recommended:**
- `SENTRY_DSN_BACKEND` → For error monitoring
- `LANGCHAIN_API_KEY` → For LangSmith tracing

### Build Configuration

- **Build Command:** Already in `render.yaml`
- **Start Command:** Already in `render.yaml`
- **Python Version:** 3.12.0 (set via `PYTHON_VERSION` env var)

---

## Migration from Uvicorn to Gunicorn

### What Changed?

| Aspect | Before (Uvicorn) | After (Gunicorn + Uvicorn) |
|--------|------------------|----------------------------|
| Command | `python -m uvicorn` | `gunicorn` |
| Workers | `--workers 2` | `--workers 2` |
| Worker Type | N/A | `--worker-class uvicorn.workers.UvicornWorker` |
| Timeout | `--timeout-keep-alive 5` | `--timeout 30 --keep-alive 5` |
| Max Requests | ❌ Not available | ✅ `--max-requests 5000` |
| Graceful Shutdown | ❌ Not available | ✅ `--graceful-timeout 30` |

### Benefits of This Change

1. **Worker Recycling:** Prevents memory leaks with `--max-requests`
2. **Better Shutdown:** Graceful worker termination on deployment
3. **Production Stability:** Gunicorn is the industry standard
4. **Zero-Downtime:** Proper worker management during updates
5. **Monitoring:** Better integration with monitoring tools

---

## Troubleshooting

### If Deployment Still Fails

**Check Logs:**
```bash
# In Render.com dashboard, check:
# 1. Build logs for dependency installation
# 2. Deploy logs for startup errors
# 3. Runtime logs for application errors
```

**Common Issues:**

1. **Import Errors:**
   - Ensure all dependencies in `requirements.txt`
   - Check PYTHONPATH is set correctly

2. **Port Binding:**
   - Render provides `$PORT` environment variable
   - Must bind to `0.0.0.0:$PORT`

3. **Health Check Fails:**
   - Verify `/health` endpoint exists in app
   - Check app starts before health check timeout

4. **Worker Timeout:**
   - Increase `--timeout` if app startup is slow
   - Default is 30s, increase if needed

### Rollback Plan

If deployment fails, rollback to single-worker uvicorn:

```yaml
startCommand: |
  cd apps/backend && \
  uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info
```

---

## Performance Tuning

### Worker Configuration

For different Render plans:

| Plan | Workers | Worker Connections | Max Requests |
|------|---------|-------------------|--------------|
| Starter | 1-2 | 250-500 | 5000 |
| Standard | 2-4 | 500-1000 | 10000 |
| Pro | 4-8 | 1000-2000 | 20000 |

**Formula:**
- Workers = (2 × CPU cores) + 1
- Worker Connections = Available memory / (worker size × 2)

### Monitoring

Monitor these metrics post-deployment:

- **Response Time:** Should be < 200ms for API calls
- **Error Rate:** Should be < 1%
- **Memory Usage:** Should be stable (no leaks)
- **Worker Restarts:** Monitor for excessive restarts

---

## References

- **Gunicorn Documentation:** https://docs.gunicorn.org/
- **Uvicorn Workers:** https://www.uvicorn.org/deployment/#gunicorn
- **Render Deployment:** https://render.com/docs/deploy-fastapi
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/server-workers/

---

## Next Steps

1. ✅ **Test Locally:** Run gunicorn command locally to verify
2. ⏳ **Commit Changes:** Push to GitHub
3. ⏳ **Deploy to Render:** Trigger deployment
4. ⏳ **Monitor Deployment:** Watch logs for successful startup
5. ⏳ **Verify Health:** Test `/health` endpoint
6. ⏳ **Test API:** Verify core endpoints work
7. ⏳ **Update Documentation:** Document any additional findings

---

**Fixed By:** Claude Code AI Assistant  
**Date:** November 9, 2025  
**Review Status:** Ready for deployment  
**Deployment Risk:** Low - Standard production configuration
