# Backend CORS Configuration Guide

## Overview

This document provides instructions for configuring Cross-Origin Resource Sharing (CORS) to allow the ToolBoxAI Dashboard frontend (deployed on Vercel) to communicate with the FastAPI backend (deployed on Render).

## Current Configuration

The backend uses environment variables to configure allowed CORS origins. The configuration is managed in `apps/backend/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5179"],
        description="Allowed CORS origins"
    )
```

## Production Setup (Render Deployment)

### 1. Add Vercel Domain to CORS_ORIGINS

In your Render dashboard:

1. Navigate to your backend service
2. Go to **Environment** tab
3. Add/Update the `CORS_ORIGINS` environment variable:

```bash
# Format: Comma-separated list of origins
CORS_ORIGINS=https://toolboxai-dashboard.vercel.app,https://www.toolboxai.com,http://localhost:5179
```

**Important Notes:**
- Include both production and development origins
- Do NOT include trailing slashes
- Use HTTPS for production domains
- Keep localhost for local development

### 2. Verify Domain Names

Ensure you're using the correct Vercel deployment URLs:

- **Production**: `https://[your-project].vercel.app`
- **Custom Domain**: `https://your-custom-domain.com` (if configured)
- **Preview Deployments**: `https://[your-project]-[hash].vercel.app`

### 3. Restart Backend Service

After updating environment variables:
1. Go to Render dashboard
2. Click **Manual Deploy** → **Clear build cache & deploy**
3. Wait for deployment to complete

## Development Setup (Local Testing)

### 1. Update `.env.local` in Backend

```bash
# Backend .env.local
CORS_ORIGINS=http://localhost:5179,http://127.0.0.1:5179
```

### 2. Verify Frontend API URL

Ensure frontend is pointing to correct backend:

```bash
# Frontend apps/dashboard/.env.local
VITE_API_URL=https://toolboxai-backend.onrender.com  # Production
# OR
VITE_API_URL=http://127.0.0.1:8009                    # Local backend
```

## Testing CORS Configuration

### 1. Browser DevTools Check

Open browser DevTools (F12) and check Console for CORS errors:

```
❌ Access to fetch at 'https://backend.onrender.com/api/...' from origin 'https://dashboard.vercel.app'
   has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.

✅ No CORS errors = Configuration correct
```

### 2. Network Tab Verification

Check Network tab for OPTIONS preflight requests:

```
Request URL: https://toolboxai-backend.onrender.com/api/v1/...
Request Method: OPTIONS
Status Code: 200 OK

Response Headers:
  Access-Control-Allow-Origin: https://toolboxai-dashboard.vercel.app
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
  Access-Control-Allow-Headers: Content-Type, Authorization
```

### 3. Health Check Test

Test the health endpoint from frontend:

```javascript
// Should work without CORS errors
const response = await fetch('https://toolboxai-backend.onrender.com/health');
const data = await response.json();
console.log('Backend status:', data);
```

## Common Issues and Solutions

### Issue 1: CORS Error Despite Correct Configuration

**Symptoms:**
- CORS errors in browser console
- OPTIONS requests returning 403/404

**Solutions:**
1. Verify environment variable format (comma-separated, no spaces)
2. Check for trailing slashes in URLs
3. Ensure backend service restarted after config change
4. Clear browser cache and hard reload (Cmd+Shift+R)

### Issue 2: Multiple CORS Origins Not Working

**Problem:** Only first origin in list works

**Solution:**
```bash
# ❌ Wrong format
CORS_ORIGINS="https://app1.com, https://app2.com"  # Spaces cause issues

# ✅ Correct format
CORS_ORIGINS=https://app1.com,https://app2.com
```

### Issue 3: Preview Deployments Not Working

**Problem:** Vercel preview deployments have dynamic URLs

**Solutions:**

**Option A:** Wildcard subdomain (if backend supports)
```python
CORS_ORIGINS=["https://*.vercel.app"]
```

**Option B:** Allow all Vercel deployments
```python
# In backend code (config.py)
if origin.endswith('.vercel.app'):
    return True
```

**Option C:** Disable CORS for specific routes
```python
# Only for non-authenticated health checks
@app.get("/health")
async def health_check():
    return {"status": "ok"}
# No CORS needed for public routes
```

## Security Best Practices

### 1. Production-Only Origins

Never use wildcard `*` in production:

```python
# ❌ NEVER DO THIS IN PRODUCTION
CORS_ORIGINS=["*"]  # Allows any origin - security risk

# ✅ Explicit whitelist
CORS_ORIGINS=[
    "https://toolboxai-dashboard.vercel.app",
    "https://www.toolboxai.com"
]
```

### 2. Development vs Production

Use different configurations:

```python
# config.py
import os

class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")

    @property
    def cors_origins(self) -> list[str]:
        if self.ENVIRONMENT == "production":
            return [
                "https://toolboxai-dashboard.vercel.app",
                "https://www.toolboxai.com"
            ]
        else:
            return [
                "http://localhost:5179",
                "http://127.0.0.1:5179"
            ]
```

### 3. Credentials Support

For authenticated requests:

```python
# Backend CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```javascript
// Frontend fetch configuration
const response = await fetch(url, {
    credentials: 'include',  // Send cookies with request
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Deployment Checklist

Before deploying to production:

- [ ] Update `CORS_ORIGINS` in Render environment variables
- [ ] Include all required domains (production + custom domain)
- [ ] Remove development origins from production config
- [ ] Restart backend service on Render
- [ ] Deploy frontend to Vercel
- [ ] Test health endpoint from production frontend
- [ ] Verify no CORS errors in browser console
- [ ] Test authenticated API calls
- [ ] Check preview deployment behavior

## Environment Variable Reference

### Backend (Render)

```bash
# Required
CORS_ORIGINS=https://toolboxai-dashboard.vercel.app,https://www.toolboxai.com

# Optional - for development
CORS_ORIGINS=https://toolboxai-dashboard.vercel.app,http://localhost:5179
```

### Frontend (Vercel)

```bash
# Production
VITE_API_URL=https://toolboxai-backend.onrender.com

# Development
VITE_API_URL=http://127.0.0.1:8009
```

## Monitoring and Debugging

### Enable CORS Logging

Add logging to backend:

```python
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_cors_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"CORS request from origin: {origin}")

    response = await call_next(request)

    if "access-control-allow-origin" in response.headers:
        logger.info(f"CORS allowed for: {origin}")
    else:
        logger.warning(f"CORS denied for: {origin}")

    return response
```

### Health Monitoring

The dashboard now includes automatic backend health monitoring:

- **Frontend Hook**: `useBackendHealth` polls `/health` every 30 seconds
- **Visual Feedback**: Banner appears when backend is offline
- **Auto-Recovery**: Banner dismisses when backend reconnects

---

**Last Updated:** 2025-11-03
**Maintained By:** ToolBoxAI Development Team
**Related Docs:**
- Frontend API Configuration: `apps/dashboard/docs/API_CONFIGURATION.md`
- Deployment Guide: `docs/DEPLOYMENT.md`
