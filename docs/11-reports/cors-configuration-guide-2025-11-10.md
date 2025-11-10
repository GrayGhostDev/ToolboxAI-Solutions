# CORS Configuration Guide

**Date:** November 10, 2025
**Issue:** Cross-Origin Resource Sharing (CORS) between Vercel frontend and Render backend
**Status:** Configuration Required
**Priority:** P0 CRITICAL

---

## Table of Contents

1. [CORS Overview](#cors-overview)
2. [Current Architecture](#current-architecture)
3. [Required Configuration](#required-configuration)
4. [Testing CORS](#testing-cors)
5. [Troubleshooting](#troubleshooting)

---

## CORS Overview

### What is CORS?

Cross-Origin Resource Sharing (CORS) is a security mechanism that allows web applications running on one domain to access resources on another domain.

### Why We Need CORS

Our architecture has:
- **Frontend:** Hosted on Vercel (`https://toolboxai-dashboard.vercel.app`)
- **Backend:** Hosted on Render (`https://toolboxai-backend-8j12.onrender.com`)

Without CORS configuration, browsers will block the frontend from making API requests to the backend.

### CORS Error Example

```
Access to fetch at 'https://toolboxai-backend-8j12.onrender.com/api/v1/users'
from origin 'https://toolboxai-dashboard.vercel.app' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

---

## Current Architecture

### Frontend URLs (Vercel)

```
Production:
  https://toolboxai-dashboard.vercel.app

Preview Deployments:
  https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app
  https://toolboxai-solutions-[HASH]-grayghostdevs-projects.vercel.app

Development:
  http://localhost:5179
  http://127.0.0.1:5179
```

### Backend URL (Render)

```
Production:
  https://toolboxai-backend-8j12.onrender.com

Local Development:
  http://localhost:8009
  http://127.0.0.1:8009
```

### CORS Flow

```
┌─────────────────────────────────────────────┐
│  Browser (User)                             │
├─────────────────────────────────────────────┤
│  1. Load frontend from Vercel               │
│     https://toolboxai-dashboard.vercel.app  │
└──────────────┬──────────────────────────────┘
               │
               │ 2. Make API request
               │
               v
┌─────────────────────────────────────────────┐
│  Backend (Render)                           │
│  https://toolboxai-backend-8j12.onrender.com│
├─────────────────────────────────────────────┤
│  3. Check ALLOWED_ORIGINS                   │
│     ✓ Is origin in allowed list?           │
│     ✓ If yes, add CORS headers              │
│     ✗ If no, reject request                 │
└──────────────┬──────────────────────────────┘
               │
               │ 4. Response with CORS headers
               │
               v
┌─────────────────────────────────────────────┐
│  Browser validates response                 │
│  ✓ CORS headers present → Allow            │
│  ✗ No CORS headers → Block                 │
└─────────────────────────────────────────────┘
```

---

## Required Configuration

### Backend Configuration (Render)

#### Environment Variables

Configure these in **Render Dashboard → toolboxai-backend → Environment**:

```bash
# CORS Origins (comma-separated, no spaces after commas recommended)
ALLOWED_ORIGINS=https://toolboxai-dashboard.vercel.app,https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app,https://*.vercel.app,http://localhost:5179,http://127.0.0.1:5179

# Alternative: More readable multi-line (if Render supports)
ALLOWED_ORIGINS="
  https://toolboxai-dashboard.vercel.app,
  https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app,
  https://*.vercel.app,
  http://localhost:5179,
  http://127.0.0.1:5179
"

# Trusted Hosts (for HTTPS redirect and security)
TRUSTED_HOSTS=toolboxai-backend-8j12.onrender.com,api.yourdomain.com,localhost,127.0.0.1

# CORS Credentials (allow cookies/auth headers)
CORS_ALLOW_CREDENTIALS=true

# CORS Methods (allowed HTTP methods)
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS

# CORS Headers (allowed request headers)
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers

# Security Settings
HTTPS_ONLY=true
SECURE_COOKIES=true
```

#### Explanation of Origins

| Origin | Purpose | When Used |
|--------|---------|-----------|
| `https://toolboxai-dashboard.vercel.app` | Production frontend | Production deployments |
| `https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app` | Vercel preview deployment | Preview PRs |
| `https://*.vercel.app` | All Vercel deployments | Any Vercel URL (production + previews) |
| `http://localhost:5179` | Local development | Frontend dev server |
| `http://127.0.0.1:5179` | Local development (IP) | Frontend dev server (alternative) |

**Note:** The wildcard `https://*.vercel.app` allows all Vercel preview deployments but is **more permissive**. For production, prefer explicit URLs.

### FastAPI Backend Code

Verify CORS middleware is configured in `apps/backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="ToolBoxAI Solutions API",
    version="1.0.0"
)

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

# Fallback for development
if not allowed_origins:
    allowed_origins = [
        "http://localhost:5179",
        "http://127.0.0.1:5179",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # From environment variable
    allow_credentials=True,  # Allow cookies and auth headers
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all response headers
)

@app.get("/health")
async def health():
    return {"status": "healthy", "allowed_origins": allowed_origins}
```

**Important:** The `/health` endpoint above returns configured origins for debugging.

### Frontend Configuration (Vercel)

#### Environment Variables

Configure in **Vercel → Settings → Environment Variables → Production**:

```bash
# API Base URL (backend)
VITE_API_URL=https://toolboxai-backend-8j12.onrender.com

# API Base URL for rewrites (used in vercel.json)
VITE_API_BASE_URL=https://toolboxai-backend-8j12.onrender.com

# Environment
VITE_ENVIRONMENT=production
```

#### Vercel Configuration (`vercel.json`)

The current `vercel.json` has API rewrites configured:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "$VITE_API_BASE_URL/api/:path*"
    }
  ]
}
```

**Note:** This rewrites `/api/*` requests through Vercel's proxy, which can help with CORS but adds latency.

**Recommendation for Production:**
- Direct API calls to `https://toolboxai-backend-8j12.onrender.com` (faster)
- Rely on CORS headers instead of Vercel proxy
- Keep proxy for development/testing only

#### Frontend API Client Configuration

Verify API client uses correct base URL in `apps/dashboard/src/config/api.ts`:

```typescript
// apps/dashboard/src/config/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8009';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // Important: Send cookies/auth headers
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## Testing CORS

### Test 1: Manual CORS Preflight Request

```bash
# Test OPTIONS preflight request (what browser sends before actual request)
curl -X OPTIONS \
  -H "Origin: https://toolboxai-dashboard.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v \
  https://toolboxai-backend-8j12.onrender.com/api/v1/users

# Expected response headers:
# Access-Control-Allow-Origin: https://toolboxai-dashboard.vercel.app
# Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization, ...
# Access-Control-Allow-Credentials: true
```

### Test 2: GET Request with Origin Header

```bash
# Test actual GET request from frontend origin
curl -H "Origin: https://toolboxai-dashboard.vercel.app" \
  -v \
  https://toolboxai-backend-8j12.onrender.com/health

# Expected response headers:
# Access-Control-Allow-Origin: https://toolboxai-dashboard.vercel.app
# Access-Control-Allow-Credentials: true
```

### Test 3: Browser DevTools

1. Open frontend in browser: https://toolboxai-dashboard.vercel.app
2. Open DevTools (F12) → Network tab
3. Make an API request (login, fetch data, etc.)
4. Click the request in Network tab
5. Check **Response Headers**:
   ```
   access-control-allow-origin: https://toolboxai-dashboard.vercel.app
   access-control-allow-credentials: true
   ```

6. Check **Request Headers**:
   ```
   origin: https://toolboxai-dashboard.vercel.app
   ```

7. If **Console** shows CORS error:
   ```
   CORS policy: No 'Access-Control-Allow-Origin' header...
   ```
   → Backend CORS configuration is incorrect

### Test 4: Automated Test Script

Create `scripts/test-cors.sh`:

```bash
#!/bin/bash
# Test CORS configuration

BACKEND_URL="https://toolboxai-backend-8j12.onrender.com"
FRONTEND_ORIGIN="https://toolboxai-dashboard.vercel.app"

echo "Testing CORS for $FRONTEND_ORIGIN → $BACKEND_URL"
echo ""

# Test 1: Health endpoint
echo "Test 1: Health endpoint"
response=$(curl -s -H "Origin: $FRONTEND_ORIGIN" -I "$BACKEND_URL/health" | grep -i "access-control-allow-origin")
if [ -n "$response" ]; then
  echo "✓ CORS header present: $response"
else
  echo "✗ CORS header missing"
fi
echo ""

# Test 2: OPTIONS preflight
echo "Test 2: OPTIONS preflight"
response=$(curl -s -X OPTIONS \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -I "$BACKEND_URL/api/v1/users" | grep -i "access-control-allow-origin")
if [ -n "$response" ]; then
  echo "✓ Preflight CORS header present: $response"
else
  echo "✗ Preflight CORS header missing"
fi
echo ""

# Test 3: Check allowed methods
echo "Test 3: Allowed methods"
response=$(curl -s -X OPTIONS \
  -H "Origin: $FRONTEND_ORIGIN" \
  -I "$BACKEND_URL/health" | grep -i "access-control-allow-methods")
if [ -n "$response" ]; then
  echo "✓ Methods: $response"
else
  echo "✗ Methods not specified"
fi
echo ""

echo "Testing complete"
```

---

## Troubleshooting

### Problem: CORS Error in Browser Console

**Error message:**
```
Access to fetch at 'https://toolboxai-backend-8j12.onrender.com/api/v1/users'
from origin 'https://toolboxai-dashboard.vercel.app' has been blocked by CORS policy
```

**Root causes:**
1. `ALLOWED_ORIGINS` not configured in Render
2. Frontend origin not in `ALLOWED_ORIGINS` list
3. CORS middleware not configured in FastAPI
4. Backend service not running (502 error)

**Solutions:**

1. **Verify ALLOWED_ORIGINS in Render:**
   ```bash
   # Render Dashboard → toolboxai-backend → Environment
   # Check ALLOWED_ORIGINS includes:
   https://toolboxai-dashboard.vercel.app
   ```

2. **Test manually:**
   ```bash
   curl -H "Origin: https://toolboxai-dashboard.vercel.app" \
     -I https://toolboxai-backend-8j12.onrender.com/health
   # Should return Access-Control-Allow-Origin header
   ```

3. **Check backend logs:**
   ```
   Render Dashboard → toolboxai-backend → Logs
   Look for: CORS middleware initialized with origins: [...]
   ```

4. **Verify FastAPI code:**
   - Check `apps/backend/main.py` has `CORSMiddleware`
   - Verify `allow_origins` reads from `ALLOWED_ORIGINS` env var

### Problem: Preflight Request Fails (OPTIONS)

**Error message:**
```
Response to preflight request doesn't pass access control check
```

**Root cause:**
FastAPI not handling OPTIONS requests for CORS preflight.

**Solution:**
Verify CORS middleware allows OPTIONS method:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # ← Must include OPTIONS
    allow_headers=["*"],
)
```

### Problem: Credentials Not Sent

**Error message:**
```
The value of the 'Access-Control-Allow-Credentials' header in the response is ''
which must be 'true' when the request's credentials mode is 'include'
```

**Root cause:**
Backend not allowing credentials (cookies, auth headers).

**Solution:**
1. Backend: Set `allow_credentials=True` in CORS middleware
2. Frontend: Set `withCredentials: true` in axios config
3. Render: Ensure `CORS_ALLOW_CREDENTIALS=true` if using env var

### Problem: Wildcard (*) Not Working

**Error message:**
```
The value of the 'Access-Control-Allow-Origin' header in the response must not be
the wildcard '*' when the request's credentials mode is 'include'
```

**Root cause:**
Cannot use `*` wildcard with `allow_credentials=true`.

**Solution:**
Use explicit origins instead of `*`:
```bash
# DON'T:
ALLOWED_ORIGINS=*

# DO:
ALLOWED_ORIGINS=https://toolboxai-dashboard.vercel.app,https://*.vercel.app
```

### Problem: CORS Works Locally But Not in Production

**Root cause:**
Different `ALLOWED_ORIGINS` configuration between local `.env` and Render environment.

**Solution:**
1. Check local `.env`:
   ```bash
   cat .env | grep ALLOWED_ORIGINS
   ```

2. Check Render environment:
   ```
   Render Dashboard → toolboxai-backend → Environment → ALLOWED_ORIGINS
   ```

3. Ensure both include production frontend URL:
   ```
   https://toolboxai-dashboard.vercel.app
   ```

---

## Production Checklist

Before deploying to production, verify:

- [ ] **Backend (Render)**
  - [ ] `ALLOWED_ORIGINS` configured with production frontend URL
  - [ ] `ALLOWED_ORIGINS` includes `https://toolboxai-dashboard.vercel.app`
  - [ ] `ALLOWED_ORIGINS` includes `https://*.vercel.app` for previews
  - [ ] `CORS_ALLOW_CREDENTIALS=true` (if using auth)
  - [ ] `TRUSTED_HOSTS` includes backend domain
  - [ ] CORS middleware configured in `main.py`

- [ ] **Frontend (Vercel)**
  - [ ] `VITE_API_URL` points to production backend
  - [ ] `withCredentials: true` in API client
  - [ ] API calls use correct base URL

- [ ] **Testing**
  - [ ] Manual CORS test with curl passes
  - [ ] Browser DevTools shows CORS headers
  - [ ] No CORS errors in console
  - [ ] Authentication works (cookies/tokens sent)

- [ ] **Documentation**
  - [ ] CORS configuration documented
  - [ ] Troubleshooting guide available
  - [ ] Environment variables documented

---

## Quick Reference

### Backend CORS Configuration (Render)

```bash
ALLOWED_ORIGINS=https://toolboxai-dashboard.vercel.app,https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app,https://*.vercel.app,http://localhost:5179
CORS_ALLOW_CREDENTIALS=true
```

### Frontend API Configuration (Vercel)

```bash
VITE_API_URL=https://toolboxai-backend-8j12.onrender.com
```

### Test Command

```bash
curl -H "Origin: https://toolboxai-dashboard.vercel.app" \
  -v https://toolboxai-backend-8j12.onrender.com/health
```

### Expected Response Headers

```
Access-Control-Allow-Origin: https://toolboxai-dashboard.vercel.app
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: *
```

---

**Report Generated:** November 10, 2025
**Next Review:** After CORS configuration
**Status:** Configuration Required - Follow setup steps
