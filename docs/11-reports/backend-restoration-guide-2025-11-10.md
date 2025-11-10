# Backend Restoration Guide

**Date:** November 10, 2025
**Issue:** Render backend service returning 502 Bad Gateway
**Status:** Action Required
**Priority:** P0 BLOCKER

---

## Table of Contents

1. [Issue Summary](#issue-summary)
2. [Root Cause Analysis](#root-cause-analysis)
3. [Restoration Steps](#restoration-steps)
4. [Environment Configuration](#environment-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Issue Summary

### Problem
The ToolBoxAI backend service deployed on Render is returning **502 Bad Gateway** for all endpoints, including `/health`, `/docs`, and API routes.

### Impact
- **Severity:** P0 BLOCKER
- **Affected Service:** `toolboxai-backend` (Render)
- **URL:** https://toolboxai-backend-8j12.onrender.com
- **Consequence:** Entire platform non-functional (frontend cannot communicate with backend)

### Service Configuration
- **Service Name:** `toolboxai-backend`
- **Service ID:** `srv-[CHECK_RENDER_DASHBOARD]`
- **Region:** Oregon (US West)
- **Plan:** Starter (Free tier - sleeps after 15min inactivity)
- **Runtime:** Python 3.12
- **Start Command:** Gunicorn with Uvicorn workers

---

## Root Cause Analysis

### Potential Causes (in order of likelihood)

#### 1. Service Sleeping (Render Free Tier) - MOST LIKELY
**Probability:** 90%

Render's free tier services automatically sleep after 15 minutes of inactivity. The 502 error is consistent with a sleeping service.

**Evidence:**
- 502 errors on all endpoints (including `/health`)
- Service has been inactive (no recent deployments)
- Free tier plan configured

**Resolution:** Wake service by making HTTP request (30-60 second spin-up time)

#### 2. Missing Critical Environment Variables - HIGH PROBABILITY
**Probability:** 70%

The backend requires several P0 environment variables to start successfully. Missing any will cause startup failure.

**Evidence:**
- `.env.example` shows extensive required configuration
- `render.production.yaml` references `toolboxai-secrets` env var group
- Many variables marked `sync: false` (must be manually configured)

**Required P0 Variables:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DATABASE_URL` (or `DATABASE_URL`)
- `JWT_SECRET_KEY`
- `SECRET_KEY`
- `OPENAI_API_KEY` (if AI features enabled)

**Resolution:** Configure all P0 variables in Render Dashboard

#### 3. Build/Deployment Failure - MEDIUM PROBABILITY
**Probability:** 30%

The build or deployment may have failed due to dependency issues, Python version mismatch, or configuration errors.

**Evidence:**
- Would be visible in Render deploy logs
- Would show build errors in dashboard

**Resolution:** Check Render deploy logs, fix build errors, redeploy

#### 4. Application Startup Error - MEDIUM PROBABILITY
**Probability:** 25%

The FastAPI application may fail to start due to:
- Database connection failure (Supabase unreachable)
- Redis connection failure
- Import errors
- Configuration validation errors

**Evidence:**
- Would appear in application logs
- Health check would fail repeatedly

**Resolution:** Check application logs, fix startup errors, ensure database connectivity

---

## Restoration Steps

### Step 1: Check Service Status

#### A. Access Render Dashboard
1. Go to https://dashboard.render.com
2. Navigate to your `toolboxai-backend` service
3. Check the status indicator:
   - **Green "Live"**: Service is running (skip to Step 3)
   - **Yellow "Deploying"**: Wait for deployment to complete
   - **Red "Build failed"**: Check logs for build errors
   - **Gray "Suspended"**: Service is sleeping (proceed to Step 1B)

#### B. Wake Sleeping Service
If service is sleeping (most likely scenario):

```bash
# Method 1: Use health check script (recommended)
cd /path/to/ToolBoxAI-Solutions
./scripts/check-backend-health.sh

# Method 2: Manual wake with curl
curl -v https://toolboxai-backend-8j12.onrender.com/health

# Wait 30-60 seconds for service to spin up
# Expected: HTTP 200 after spin-up completes
```

#### C. Check Logs
In Render Dashboard → `toolboxai-backend` → Logs tab:

Look for:
- ✅ **Success**: `Application startup complete`, `Uvicorn running`
- ❌ **Errors**: `ModuleNotFoundError`, `Connection refused`, `Authentication failed`

---

### Step 2: Verify Environment Variables

#### A. Check Configured Variables
In Render Dashboard → `toolboxai-backend` → Environment:

**Verify P0 Variables Exist:**
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_ROLE_KEY`
- [ ] `SUPABASE_DATABASE_URL`
- [ ] `JWT_SECRET_KEY`
- [ ] `SECRET_KEY`
- [ ] `ENCRYPTION_KEY`

**Verify Auto-Populated Variables:**
- [ ] `REDIS_URL` (auto-populated from Redis service)
- [ ] `PORT` (auto-populated by Render)

#### B. Add Missing Variables
If any P0 variables are missing:

1. Generate secrets locally:
   ```bash
   cd /path/to/ToolBoxAI-Solutions
   ./scripts/generate-secrets.sh > .env.secrets
   ```

2. Open `.env.secrets` and copy generated values

3. In Render Dashboard → Environment → Add Secret:
   - Add each missing variable
   - Use values from `.env.secrets`
   - Click "Save Changes"

4. **Important:** Service will automatically redeploy after saving environment changes

#### C. Configure Environment Variable Group
The `toolboxai-secrets` group should contain all secrets.

**To create/update the group:**
1. Render Dashboard → Environment Groups
2. Find or create `toolboxai-secrets`
3. Add all secrets from [Environment Configuration](#environment-configuration) section
4. Link group to `toolboxai-backend` service

---

### Step 3: Verify Supabase Connection

#### A. Get Supabase Credentials
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Settings → API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY` (for frontend)
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (for backend)

5. Go to **Settings → Database**
6. Copy **Connection string** (Pooler):
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:6543/postgres?sslmode=require
   ```
   This is your `SUPABASE_DATABASE_URL`

#### B. Test Database Connection
From local machine (to verify credentials work):

```bash
# Install psql if needed
brew install postgresql  # macOS
# or
apt-get install postgresql-client  # Linux

# Test connection (replace with your actual URL)
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:6543/postgres?sslmode=require" \
  -c "SELECT version();"

# Expected: PostgreSQL version output
# If connection fails, check credentials and network
```

#### C. Configure in Render
1. Render Dashboard → `toolboxai-backend` → Environment
2. Add or update:
   - `SUPABASE_URL` = `https://[PROJECT].supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY` = `eyJ...` (JWT token)
   - `SUPABASE_DATABASE_URL` = `postgresql://...`
3. Set `DATABASE_URL` = `${SUPABASE_DATABASE_URL}` (reference)
4. Save Changes

---

### Step 4: Configure CORS for Frontend

The backend must allow requests from the Vercel-deployed frontend.

#### A. Identify Frontend URLs
From `vercel.json` and deployment:
- **Primary**: `https://toolboxai-dashboard.vercel.app` (production)
- **Preview**: `https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app`
- **Pattern**: `https://*.vercel.app` (all Vercel deployments)

#### B. Configure ALLOWED_ORIGINS in Render
1. Render Dashboard → `toolboxai-backend` → Environment
2. Find or add `ALLOWED_ORIGINS`
3. Set value to:
   ```
   https://toolboxai-dashboard.vercel.app,https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app,https://*.vercel.app
   ```
4. Also set `TRUSTED_HOSTS`:
   ```
   toolboxai-backend-8j12.onrender.com,localhost,127.0.0.1
   ```
5. Save Changes

**Note:** Wildcard `https://*.vercel.app` allows all Vercel preview deployments.

---

### Step 5: Trigger Manual Deploy (if needed)

If service is not deploying automatically:

#### A. Manual Deploy via Dashboard
1. Render Dashboard → `toolboxai-backend`
2. Click **Manual Deploy** button
3. Select branch: `main`
4. Click **Deploy**
5. Monitor logs for errors

#### B. Manual Deploy via API (for CI/CD)
```bash
# Set your API key and service ID
export RENDER_API_KEY="rnd_your_api_key_here"
export RENDER_SERVICE_ID="srv_your_service_id_here"

# Trigger deploy
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys
```

#### C. Deploy via Git Push
```bash
# Commit any changes
git add .
git commit -m "fix: update environment configuration"

# Push to main branch
git push origin main

# Render will auto-deploy (if auto-deploy enabled)
```

---

### Step 6: Verify Service Health

Once deployed and running:

```bash
# Run comprehensive health check
cd /path/to/ToolBoxAI-Solutions
./scripts/check-backend-health.sh

# Expected output:
# ✓ Basic health endpoint
# ✓ OpenAPI docs
# ✓ Database connectivity
# ✓ CORS headers
# ✓ SSL certificate
```

If health check passes, service is restored!

---

## Environment Configuration

### Complete P0 Variable List (Render Backend)

Configure these in **Render Dashboard → Environment → toolboxai-secrets group**:

```bash
# Database & Cache
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:6543/postgres?sslmode=require
DATABASE_URL=${SUPABASE_DATABASE_URL}  # Reference to above
# REDIS_URL is auto-populated by Render Redis service

# Security & Authentication
JWT_SECRET_KEY=[64-char hex string from generate-secrets.sh]
JWT_REFRESH_SECRET_KEY=[64-char hex string]
SECRET_KEY=[64-char hex string]
ENCRYPTION_KEY=[32-char hex string]
SESSION_SECRET_KEY=[64-char hex string]
CSRF_SECRET_KEY=[64-char hex string]

# AI Services (P0 if AI features enabled)
OPENAI_API_KEY=sk-proj-...

# Clerk Authentication (if using Clerk)
CLERK_SECRET_KEY=sk_live_...
CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_WEBHOOK_SIGNING_SECRET=whsec_...
CLERK_JWKS_URL=https://[domain].clerk.accounts.dev/.well-known/jwks.json

# Pusher (Real-time features)
PUSHER_APP_ID=[from Pusher dashboard]
PUSHER_KEY=[from Pusher dashboard]
PUSHER_SECRET=[from Pusher dashboard]
PUSHER_CLUSTER=us2

# CORS & Security
ALLOWED_ORIGINS=https://toolboxai-dashboard.vercel.app,https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app,https://*.vercel.app
TRUSTED_HOSTS=toolboxai-backend-8j12.onrender.com,localhost,127.0.0.1

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=info
```

### P1 Variables (Highly Recommended)

```bash
# LangChain/LangSmith (AI Observability)
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=ToolboxAI-Solutions
LANGCHAIN_TRACING_V2=true

# Sentry (Error Tracking)
SENTRY_DSN=https://[key]@[org].ingest.sentry.io/[project]
SENTRY_ENVIRONMENT=production
```

### Frontend Variables (Vercel Dashboard)

Configure these in **Vercel → Settings → Environment Variables → Production**:

```bash
VITE_SUPABASE_URL=https://[PROJECT].supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_API_URL=https://toolboxai-backend-8j12.onrender.com
VITE_PUSHER_KEY=[same as PUSHER_KEY]
VITE_PUSHER_CLUSTER=us2
VITE_CLERK_PUBLISHABLE_KEY=pk_live_...
VITE_ENVIRONMENT=production
```

---

## Verification

### Full Verification Checklist

After completing restoration steps:

```bash
# 1. Check service is awake
curl -I https://toolboxai-backend-8j12.onrender.com/health
# Expected: HTTP/2 200

# 2. Run comprehensive health check
./scripts/check-backend-health.sh
# Expected: All tests pass

# 3. Verify API documentation
curl https://toolboxai-backend-8j12.onrender.com/docs
# Expected: HTML page with Swagger UI

# 4. Test CORS from frontend domain
curl -H "Origin: https://toolboxai-dashboard.vercel.app" \
     -I https://toolboxai-backend-8j12.onrender.com/health
# Expected: Access-Control-Allow-Origin header present

# 5. Validate environment configuration
python scripts/validate-env.py --check-render
# Expected: All P0 variables validated

# 6. Test frontend connectivity
# Open https://toolboxai-dashboard.vercel.app in browser
# Check browser console for successful API calls
# No CORS errors should appear
```

### Success Criteria

- [ ] Backend returns HTTP 200 on `/health`
- [ ] OpenAPI docs accessible at `/docs`
- [ ] CORS headers present for Vercel origins
- [ ] All P0 environment variables configured
- [ ] Frontend can make API calls without errors
- [ ] No errors in Render logs
- [ ] Database connectivity confirmed
- [ ] SSL certificate valid

---

## Troubleshooting

### Issue: Service Still Returns 502

**Possible causes:**
1. Service hasn't finished spinning up (wait 60 seconds)
2. Build failed (check deploy logs)
3. Application crashed on startup (check logs)

**Actions:**
```bash
# Wait and retry
sleep 60
curl https://toolboxai-backend-8j12.onrender.com/health

# Check Render logs
# Dashboard → toolboxai-backend → Logs
# Look for: "Application startup complete"
```

### Issue: Database Connection Failed

**Symptoms:**
- Logs show `Connection refused` or `Authentication failed`
- Health check fails

**Actions:**
1. Verify `SUPABASE_DATABASE_URL` is correct
2. Test connection from local machine (see Step 3B)
3. Check Supabase project is active (not paused)
4. Verify connection pooler is enabled (port 6543)
5. Check firewall/IP allowlist in Supabase settings

### Issue: CORS Errors in Frontend

**Symptoms:**
- Browser console shows `CORS policy` errors
- Frontend cannot make API requests

**Actions:**
1. Verify `ALLOWED_ORIGINS` includes Vercel URL
2. Check backend logs for CORS middleware errors
3. Test CORS headers:
   ```bash
   curl -H "Origin: https://toolboxai-dashboard.vercel.app" \
        -v https://toolboxai-backend-8j12.onrender.com/health
   ```
4. Ensure wildcard `https://*.vercel.app` is included

### Issue: Missing Environment Variable Errors

**Symptoms:**
- Logs show `KeyError` or `Environment variable not found`
- Application fails to start

**Actions:**
1. Run validation script:
   ```bash
   python scripts/validate-env.py --check-render
   ```
2. Add missing variables to Render Dashboard
3. Redeploy service
4. Check logs for startup success

### Issue: Build Failures

**Symptoms:**
- Deploy fails during build phase
- Logs show dependency installation errors

**Actions:**
1. Check `requirements.txt` is up-to-date
2. Verify Python version (3.12) matches `render.production.yaml`
3. Check for dependency conflicts:
   ```bash
   pip check
   ```
4. Review build command in `render.production.yaml`:
   ```yaml
   buildCommand: |
     pip install --upgrade pip setuptools wheel
     pip install -r requirements.txt
   ```

### Issue: Service Won't Wake from Sleep

**Symptoms:**
- Consistently returns 502 even after waiting
- Free tier service

**Actions:**
1. **Upgrade to paid plan** (prevents sleeping):
   - Render Dashboard → toolboxai-backend → Settings
   - Change plan from "Starter" to "Standard" ($7/month)
   - Prevents sleep, guarantees uptime

2. **Use wake-up automation** (keep free tier):
   - Setup UptimeRobot or similar service
   - Ping `/health` every 10 minutes
   - Keeps service alive during business hours

3. **Accept sleep behavior** (development only):
   - Document that first request takes 60 seconds
   - Acceptable for staging/development
   - NOT acceptable for production

---

## Additional Resources

### Scripts Created
- **Generate Secrets:** `scripts/generate-secrets.sh`
- **Health Check:** `scripts/check-backend-health.sh`
- **Validate Environment:** `scripts/validate-env.py`

### Documentation
- **Environment Configuration:** `docs/10-security/ENV_FILES_DOCUMENTATION.md`
- **CORS Configuration:** `docs/11-reports/cors-configuration-guide-2025-11-10.md`
- **Deployment Guide:** `docs/08-operations/deployment/`

### External Links
- **Render Dashboard:** https://dashboard.render.com
- **Supabase Dashboard:** https://supabase.com/dashboard
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Render Documentation:** https://render.com/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com

---

## Summary

The backend 502 error is most likely due to the service sleeping (Render free tier). The restoration process is:

1. **Wake service** by making HTTP request (60s spin-up)
2. **Verify environment variables** (P0 critical variables configured)
3. **Configure Supabase connection** (DATABASE_URL set correctly)
4. **Set CORS origins** (allow Vercel frontend domains)
5. **Verify health** (run health check script)

If these steps don't resolve the issue, the service may have build/startup errors visible in Render logs.

**Quick Recovery Command:**
```bash
# Run all verification steps
./scripts/check-backend-health.sh && \
python scripts/validate-env.py --check-render
```

---

**Report Generated:** November 10, 2025
**Next Review:** After backend restoration
**Status:** Action Required - Follow restoration steps
