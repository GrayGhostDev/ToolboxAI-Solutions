# 🚀 ToolBoxAI Solutions - Production Deployment Guide

## Overview

This guide covers the complete deployment process for ToolBoxAI Solutions with:
- **Frontend**: Vercel (React/Vite dashboard)
- **Backend**: Render (FastAPI Python services)
- **Database**: Supabase (Managed PostgreSQL)
- **Monitoring**: Sentry (Error tracking & performance)
- **CI/CD**: TeamCity (Build & deployment automation)
- **CDN**: Cloudflare (Optional static asset delivery)

---

## 📋 Prerequisites

### Required Accounts
- [x] Vercel account (for frontend)
- [x] Render account (for backend)
- [x] Supabase account (for database)
- [x] Sentry account (for monitoring)
- [x] TeamCity server (for CI/CD)
- [ ] Cloudflare account (optional, for CDN)

### Required Tools
```bash
# Install deployment tools
npm install -g vercel
npm install -g @sentry/cli
pip install render-cli
```

---

## 🔐 Environment Variables Setup

### 1. Supabase Configuration

Create a Supabase project at https://supabase.com

```bash
# Get these from Supabase Dashboard > Settings > API
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### 2. Sentry Configuration

Create projects at https://sentry.io

```bash
# Frontend project
VITE_SENTRY_DSN=https://xxx@o123456.ingest.sentry.io/xxx
SENTRY_PROJECT_FRONTEND=frontend

# Backend project
SENTRY_DSN_BACKEND=https://yyy@o123456.ingest.sentry.io/yyy
SENTRY_PROJECT_BACKEND=backend

# Shared
SENTRY_AUTH_TOKEN=sntrys_...
SENTRY_ORG=toolboxai
```

### 3. Vercel Configuration

```bash
# Get from Vercel Dashboard > Settings
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=team_xxx
VERCEL_PROJECT_ID=prj_xxx
```

### 4. Render Configuration

```bash
# Get from Render Dashboard > Account Settings
RENDER_API_KEY=rnd_xxx
RENDER_SERVICE_ID=srv-xxx  # Backend service ID
```

---

## 🏗️ Deployment Steps

### Step 1: Backend Deployment to Render

#### A. Configure Render Service

1. **Create New Web Service** in Render Dashboard
   - Repository: Link your GitHub repo
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd apps/backend && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4`

2. **Add Environment Variables** in Render Dashboard:
   ```
   ENVIRONMENT=production
   PYTHON_VERSION=3.12.0
   DATABASE_URL=[from Supabase]
   REDIS_URL=[from Render Redis]
   SENTRY_DSN_BACKEND=[from Sentry]
   SUPABASE_URL=[from Supabase]
   SUPABASE_SERVICE_ROLE_KEY=[from Supabase]
   ```

3. **Deploy via CLI** (alternative):
   ```bash
   # From project root
   curl -X POST \
     -H "Authorization: Bearer $RENDER_API_KEY" \
     -H "Content-Type: application/json" \
     "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys"
   ```

#### B. Verify Backend Deployment

```bash
# Health check
curl https://toolboxai-backend.onrender.com/health

# Expected response:
{"status": "healthy", "timestamp": 1699000000}
```

---

### Step 2: Frontend Deployment to Vercel

#### A. Configure Vercel Project

1. **Link Project**:
   ```bash
   cd apps/dashboard
   vercel link
   ```

2. **Set Environment Variables**:
   ```bash
   # Production environment variables
   vercel env add VITE_API_URL production
   # Enter: https://toolboxai-backend.onrender.com
   
   vercel env add VITE_SENTRY_DSN production
   # Enter: [your frontend Sentry DSN]
   
   vercel env add VITE_SUPABASE_URL production
   # Enter: [your Supabase URL]
   
   vercel env add VITE_SUPABASE_ANON_KEY production
   # Enter: [your Supabase anon key]
   ```

#### B. Deploy to Production

```bash
cd apps/dashboard

# Deploy to production
vercel --prod

# Or use npm script
npm run deploy:frontend
```

#### C. Verify Frontend Deployment

```bash
# Open in browser
open https://toolboxai.vercel.app

# Check API connectivity
curl https://toolboxai.vercel.app/health
```

---

### Step 3: Database Setup (Supabase)

#### A. Run Migrations

```bash
# Install psql client
brew install postgresql  # macOS
# or
sudo apt install postgresql-client  # Linux

# Connect to Supabase
psql $SUPABASE_DATABASE_URL

# Run migration scripts
\i database/migrations/001_initial_schema.sql
```

#### B. Configure Database Security

In Supabase Dashboard:
1. **Authentication** > Enable Email/Password
2. **Database** > Policies > Create RLS policies
3. **API** > Configure CORS origins

---

### Step 4: Monitoring Setup (Sentry)

#### A. Upload Sourcemaps

Frontend:
```bash
cd apps/dashboard

# Build with sourcemaps
npm run build

# Upload to Sentry
export SENTRY_AUTH_TOKEN=your_token
export SENTRY_ORG=toolboxai
export SENTRY_PROJECT=frontend

sentry-cli releases new $COMMIT_SHA
sentry-cli releases files $COMMIT_SHA upload-sourcemaps ./dist
sentry-cli releases finalize $COMMIT_SHA
sentry-cli releases deploys $COMMIT_SHA new -e production
```

Backend:
```bash
export SENTRY_AUTH_TOKEN=your_token
export SENTRY_ORG=toolboxai
export SENTRY_PROJECT=backend

sentry-cli releases new $COMMIT_SHA
sentry-cli releases deploys $COMMIT_SHA new -e production
```

#### B. Configure Alerts

In Sentry Dashboard:
1. **Alerts** > Create New Alert
2. Set conditions (e.g., error rate > 1%)
3. Configure notifications (Slack, email)

---

### Step 5: TeamCity CI/CD Configuration

#### A. Configure Build Parameters

In TeamCity Project Settings:

```kotlin
// Environment Variables
VERCEL_TOKEN=***
RENDER_API_KEY=***
SENTRY_AUTH_TOKEN=***
SUPABASE_URL=***
```

#### B. Trigger Deployment

Manual:
```bash
# Via TeamCity UI
Build > Run > Deploy to Production
```

Automatic (on push to main):
```bash
git push origin main
# TeamCity automatically triggers build
```

---

## 🐳 Docker Deployment (Alternative)

### Local Testing

```bash
# Build production images
npm run docker:build:prod

# Start all services
npm run docker:up:prod

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

### Deploy to Docker Registry

```bash
# Build and tag
docker build -f infrastructure/docker/Dockerfile.backend -t registry.render.com/toolboxai-backend:latest .
docker build -f infrastructure/docker/Dockerfile.dashboard -t registry.render.com/toolboxai-dashboard:latest .

# Push to registry
docker push registry.render.com/toolboxai-backend:latest
docker push registry.render.com/toolboxai-dashboard:latest
```

---

## ✅ Post-Deployment Verification

### Automated Health Checks

```bash
# Run health check script
./scripts/health-check.sh

# Or manually
curl https://toolboxai-backend.onrender.com/health
curl https://toolboxai.vercel.app/
```

### Monitor Application

1. **Sentry Dashboard**: Check for errors
   - https://sentry.io/organizations/toolboxai/issues/

2. **Render Dashboard**: Check service status
   - https://dashboard.render.com/

3. **Vercel Dashboard**: Check deployment status
   - https://vercel.com/dashboard

4. **Supabase Dashboard**: Monitor database performance
   - https://supabase.com/dashboard/

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Backend Health Check Fails
```bash
# Check logs
render logs toolboxai-backend --tail 100

# Common fixes:
# - Verify DATABASE_URL is set
# - Check REDIS_URL connection
# - Verify all env vars are set
```

#### 2. Frontend Can't Connect to Backend
```bash
# Check CORS settings in backend
# Verify VITE_API_URL is correct
# Check network tab in browser DevTools
```

#### 3. Database Connection Issues
```bash
# Test connection
psql $SUPABASE_DATABASE_URL -c "SELECT 1;"

# Check Supabase IP allowlist
# Verify connection string format
```

#### 4. Sentry Not Receiving Events
```bash
# Verify DSN is correct
# Check environment variable is set
# Test with manual error:
sentry-cli send-event -m "Test event"
```

---

## 📊 Monitoring & Maintenance

### Daily
- [x] Check Sentry for new errors
- [x] Review Render logs for issues
- [x] Monitor Supabase performance metrics

### Weekly
- [x] Review deployment metrics
- [x] Check database backup status
- [x] Update dependencies

### Monthly
- [x] Review and optimize database queries
- [x] Analyze bundle size
- [x] Update documentation

---

## 🔄 Rollback Procedure

### Vercel Rollback
```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

### Render Rollback
```bash
# Via dashboard: Deploys > Previous Deploy > Deploy
# Or via API:
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys/[deploy-id]/rollback"
```

---

## 📞 Support

- **Documentation**: `/docs/deployment/`
- **Issues**: GitHub Issues
- **Team Chat**: Slack #deployments
- **On-Call**: PagerDuty rotation

---

## 🎉 Deployment Complete!

Your application is now live at:
- **Frontend**: https://toolboxai.vercel.app
- **Backend API**: https://toolboxai-backend.onrender.com
- **Documentation**: https://toolboxai.vercel.app/docs

**Next Steps**:
1. Monitor Sentry for errors
2. Set up alerts in Render/Vercel
3. Configure domain (optional)
4. Enable SSL/HTTPS
5. Set up CDN (optional)

