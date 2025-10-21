# Render.com Configuration Guide

## Complete Backend Deployment Setup

This guide provides the **exact configuration** needed for your Render.com service based on your deployment screenshot.

---

## 🚀 Service Configuration

### Basic Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **Service Name** | `toolboxai-solutions-backend` | Unique identifier for your service |
| **Project** | ToolboxAI-Solutions-backend | Keep existing project |
| **Environment** | Production | Deployment environment |
| **Language** | Python 3 | Runtime environment |
| **Branch** | `main` | Deploy from main branch (or `feat/supabase-backend-enhancement` for testing) |
| **Region** | **Oregon (US West)** | ⚠️ CHANGE from Ohio - Better latency to Vercel (also in US West) |

### Build Configuration

```bash
# Root Directory
# Leave EMPTY - code is at repository root

# Build Command
pip install -r requirements.txt

# Start Command (⚠️ CRITICAL - UPDATE THIS)
uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT
```

**❌ INCORRECT (shown in screenshot):**
```bash
uvicorn your_application.main  # This will fail!
```

**✅ CORRECT:**
```bash
uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT
```

---

## 💰 Instance Type Selection

### Recommended Plans

| Plan | RAM | CPU | Price | Use Case |
|------|-----|-----|-------|----------|
| **Starter** | 512 MB | 0.5 CPU | $7/month | ✅ Initial deployment, testing |
| **Standard** | 2 GB | 1 CPU | $25/month | 🎯 Production (recommended) |
| **Pro** | 4 GB | 2 CPU | $85/month | High traffic |
| **Pro Plus** | 8 GB | 4 CPU | $175/month | Enterprise scale |

**Start with Starter**, upgrade to Standard when you have users.

---

## 🔧 Environment Variables Configuration

Click **"+ Add Environment Variable"** for each variable below:

### 🗄️ Database - Supabase (REQUIRED)

Get these from: **https://app.supabase.com/project/YOUR_PROJECT/settings/api**

```bash
NAME_OF_VARIABLE: SUPABASE_URL
value: https://xyzcompany.supabase.co

NAME_OF_VARIABLE: SUPABASE_ANON_KEY
value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...

NAME_OF_VARIABLE: SUPABASE_SERVICE_ROLE_KEY
value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...

NAME_OF_VARIABLE: DATABASE_URL
value: postgresql://postgres:[YOUR-PASSWORD]@db.xyzcompany.supabase.co:5432/postgres
```

**Note:** Get DATABASE_URL from Supabase → Settings → Database → Connection String (URI)

### 🔐 Authentication - Clerk (REQUIRED)

Get these from: **https://dashboard.clerk.com/apps/YOUR_APP/api-keys**

```bash
NAME_OF_VARIABLE: CLERK_SECRET_KEY
value: sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

NAME_OF_VARIABLE: CLERK_PUBLISHABLE_KEY
value: pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**For Production:** Replace `sk_test_` with `sk_live_` and `pk_test_` with `pk_live_`

### 🔒 JWT Security (REQUIRED)

Generate a secure secret key:

```bash
# Run this command locally to generate:
openssl rand -hex 32
```

Then add to Render:

```bash
NAME_OF_VARIABLE: JWT_SECRET_KEY
value: [OUTPUT_FROM_OPENSSL_COMMAND]

NAME_OF_VARIABLE: JWT_ALGORITHM
value: HS256

NAME_OF_VARIABLE: JWT_ACCESS_TOKEN_EXPIRE_MINUTES
value: 60
```

### 📡 Real-time - Pusher (REQUIRED)

Get these from: **https://dashboard.pusher.com/apps/YOUR_APP/keys**

```bash
NAME_OF_VARIABLE: PUSHER_APP_ID
value: 1234567

NAME_OF_VARIABLE: PUSHER_KEY
value: xxxxxxxxxxxxxxxx

NAME_OF_VARIABLE: PUSHER_SECRET
value: xxxxxxxxxxxxxxxx

NAME_OF_VARIABLE: PUSHER_CLUSTER
value: us2
```

### 🌐 CORS Configuration (REQUIRED)

```bash
NAME_OF_VARIABLE: CORS_ORIGINS
value: https://toolbox-production-final.vercel.app,https://toolbox-production-final-*.vercel.app
```

**After custom domain setup:**
```bash
value: https://app.toolboxai.com,https://toolbox-production-final.vercel.app
```

### ⚙️ System Configuration (REQUIRED)

```bash
NAME_OF_VARIABLE: ENVIRONMENT
value: production

NAME_OF_VARIABLE: DEBUG
value: false

NAME_OF_VARIABLE: PYTHONPATH
value: /opt/render/project/src

NAME_OF_VARIABLE: PYTHON_VERSION
value: 3.12.0
```

### 🤖 AI Services (OPTIONAL - Add only if using)

```bash
# OpenAI GPT
NAME_OF_VARIABLE: OPENAI_API_KEY
value: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic Claude
NAME_OF_VARIABLE: ANTHROPIC_API_KEY
value: sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 📧 Email Service (OPTIONAL - SendGrid)

Get from: **https://app.sendgrid.com/settings/api_keys**

```bash
NAME_OF_VARIABLE: SENDGRID_API_KEY
value: SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

NAME_OF_VARIABLE: SENDGRID_FROM_EMAIL
value: noreply@toolboxai.com
```

### 📊 Monitoring (OPTIONAL - Sentry)

Get from: **https://sentry.io/settings/YOUR_ORG/projects/YOUR_PROJECT/keys/**

```bash
NAME_OF_VARIABLE: SENTRY_DSN
value: https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@o123456.ingest.sentry.io/123456
```

---

## 🔍 Advanced Configuration

### Health Check Path

```
/health
```

✅ **Already configured correctly in screenshot**

This endpoint returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T20:15:30Z",
  "database": "connected",
  "version": "1.0.0"
}
```

### Pre-Deploy Command

```
[Leave Empty]
```

Database migrations will run automatically on application startup if needed.

### Auto-Deploy

```
✅ On Commit (Enabled)
```

**Behavior:**
- Automatically deploys when you push to the selected branch
- Recommended for `main` branch
- Disable for `feat/*` branches if testing locally first

### Build Filters (Optional)

**Included Paths:**
```
apps/backend/**
core/**
database/**
toolboxai_settings/**
toolboxai_utils/**
requirements.txt
```

**Ignored Paths:**
```
apps/dashboard/**
docs/**
tests/**
*.md
```

This prevents rebuilds when only frontend or docs change.

---

## ✅ Deployment Checklist

### Before Clicking "Create Web Service"

- [ ] Service name is `toolboxai-backend`
- [ ] Region is **Oregon (US West)**
- [ ] Branch is `main` (or your deployment branch)
- [ ] Start command is `uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT`
- [ ] All REQUIRED environment variables added:
  - [ ] Supabase (4 variables)
  - [ ] Clerk (2 variables)
  - [ ] JWT (3 variables)
  - [ ] Pusher (4 variables)
  - [ ] CORS (1 variable)
  - [ ] System (4 variables)
- [ ] Health check path is `/health`
- [ ] Instance type selected (Starter recommended)

### After Deployment

1. **Wait for build** (3-5 minutes)
2. **Check logs** for errors
3. **Test health endpoint:**
   ```bash
   curl https://toolboxai-backend.onrender.com/health
   ```
4. **Verify database connection:**
   ```bash
   curl https://toolboxai-backend.onrender.com/api/v1/health/db
   ```
5. **Update Vercel environment variables** with backend URL

---

## 🐛 Troubleshooting

### Build Fails

**Error:** `ModuleNotFoundError: No module named 'apps'`

**Solution:** Ensure `PYTHONPATH=/opt/render/project/src` is set in environment variables

---

**Error:** `Could not find a version that satisfies the requirement...`

**Solution:** Check `requirements.txt` is in repository root and contains all dependencies

---

### Service Starts But Health Check Fails

**Error:** Health check returns 404

**Solution:** Verify start command is exact:
```bash
uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT
```

---

**Error:** Health check returns 500

**Solution:** Check logs for database connection errors. Verify `DATABASE_URL` is correct.

---

### Database Connection Errors

**Error:** `could not connect to server: Connection refused`

**Solution:**
1. Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/db`
2. Check Supabase project is active
3. Verify Supabase allows connections from Render IPs (usually auto-configured)

---

### CORS Errors

**Error:** Frontend can't connect - CORS policy blocked

**Solution:**
1. Verify `CORS_ORIGINS` includes your Vercel domain
2. Include both `https://domain.vercel.app` and `https://domain-*.vercel.app` (for previews)
3. No trailing slashes

---

## 📝 Next Steps After Successful Deployment

1. **Note your backend URL:**
   ```
   https://toolboxai-backend.onrender.com
   ```

2. **Update Vercel environment variables:**
   ```bash
   VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
   VITE_WS_URL=wss://toolboxai-backend.onrender.com
   ```

3. **Configure Clerk webhook:**
   - URL: `https://toolboxai-backend.onrender.com/api/v1/auth/clerk/webhook`
   - Events: `user.created`, `user.updated`, `user.deleted`

4. **Test complete flow:**
   - Frontend → Backend → Database
   - Authentication with Clerk
   - Real-time updates with Pusher

5. **Monitor deployment:**
   - Check logs regularly
   - Set up Sentry for error tracking
   - Configure uptime monitoring

---

## 🔗 Quick Links

- **Render Dashboard:** https://dashboard.render.com/
- **Service Logs:** https://dashboard.render.com/web/YOUR_SERVICE_ID/logs
- **Environment Variables:** https://dashboard.render.com/web/YOUR_SERVICE_ID/env
- **Metrics:** https://dashboard.render.com/web/YOUR_SERVICE_ID/metrics

---

**Last Updated:** October 21, 2025
**Configuration Version:** 1.0.0
**Based on:** Production deployment screenshot
