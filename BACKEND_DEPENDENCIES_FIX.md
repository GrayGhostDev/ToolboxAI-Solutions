# Backend Dependencies Fix - Action Required

## What I've Done

✅ **Added missing dependencies to requirements.txt**

The following packages were added to the existing requirements.txt file:

```
python-jose[cryptography]>=3.3.0
PyJWT>=2.8.0
pydantic[email]>=2.0.0
psutil>=5.9.0
httpx>=0.24.0
asyncpg>=0.29.0
pusher>=3.3.0
langchain-core>=0.1.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
prometheus-fastapi-instrumentator>=6.1.0
eval-type-backport>=0.1.0
```

## What You Need To Do

### Step 1: Install Missing Dependencies

Run this command in your terminal:

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Install all missing packages
python3 -m pip install --user python-jose[cryptography] PyJWT pydantic[email] psutil httpx asyncpg pusher langchain-core opentelemetry-api opentelemetry-sdk prometheus-fastapi-instrumentator eval-type-backport
```

**OR** install from the updated requirements.txt:

```bash
python3 -m pip install --user -r requirements.txt
```

### Step 2: Start Backend Server

After dependencies are installed:

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Start the backend
python3 -m uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8009
```

### Step 3: Verify Backend Is Running

In another terminal:

```bash
# Check if backend is running
curl http://localhost:8009/health

# Should return something like:
# {"status":"degraded","version":"1.0.0",...}
```

### Step 4: Test Login

Once backend is running, test the login endpoint:

```bash
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@toolboxai.com","password":"Admin123!"}'
```

Should return a JWT token if successful.

### Step 5: Test Dashboard

1. Open browser to: `http://localhost:5179/`
2. Hard refresh: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)
3. Try logging in with:
   - Email: `admin@toolboxai.com`
   - Password: `Admin123!`

---

## Error Analysis

### From Backend Logs - All Resolved By Installing Packages:

1. ❌ `No module named 'jose'` → ✅ Install `python-jose[cryptography]`
2. ❌ `No module named 'jwt'` → ✅ Install `PyJWT`
3. ❌ `email-validator is not installed` → ✅ Install `pydantic[email]`
4. ❌ `No module named 'psutil'` → ✅ Install `psutil`
5. ❌ `No module named 'httpx'` → ✅ Install `httpx`
6. ❌ `No module named 'asyncpg'` → ✅ Install `asyncpg`
7. ❌ `pusher package is not installed` → ✅ Install `pusher`
8. ❌ `No module named 'langchain_core'` → ✅ Install `langchain-core`
9. ❌ `No module named 'opentelemetry'` → ✅ Install `opentelemetry-api` + `opentelemetry-sdk`
10. ❌ `No module named 'prometheus_fastapi_instrumentator'` → ✅ Install `prometheus-fastapi-instrumentator`
11. ❌ `install the eval_type_backport package` → ✅ Install `eval-type-backport`

### Warnings That Are OK (Non-Critical):

- ⚠️ Sentry initialization issues (can be ignored in development)
- ⚠️ OpenSSL/LibreSSL warning (urllib3 works fine)
- ⚠️ LangChain/Anthropic/OpenAI warnings (optional features)
- ⚠️ Master key not provided (local development doesn't need encryption)

---

## Expected Behavior After Fix

### Backend Logs Should Show:

```
INFO:     Uvicorn running on http://127.0.0.1:8009
INFO:     Application startup complete.
```

Followed by fewer warnings (only optional services like Pusher, Sentry, etc.)

### Critical Endpoint That Must Work:

```
✅ /health - Health check
✅ /api/v1/auth/login - Authentication
```

---

## Quick Reference

### Test Credentials:

**Admin:**
- Email: `admin@toolboxai.com`
- Password: `Admin123!`

**Teacher:**
- Email: `jane.smith@school.edu`
- Password: `Teacher123!`

**Student:**
- Email: `alex.johnson@student.edu`
- Password: `Student123!`

### Port Configuration:

- **Backend**: http://localhost:8009
- **Dashboard**: http://localhost:5179

---

## Files Modified:

1. ✅ `requirements.txt` - Added 12 missing dependencies
2. ✅ `apps/dashboard/public/error-suppressor-preload.js` - Fixed strict mode error
3. ✅ `apps/dashboard/.env.local` - Set to localhost:8009

---

## Troubleshooting

### If "pip install" Takes Too Long:

Try installing packages one at a time:

```bash
python3 -m pip install --user python-jose
python3 -m pip install --user PyJWT
python3 -m pip install --user pydantic[email]
# etc...
```

### If Backend Still Shows Errors:

Check which packages are actually installed:

```bash
python3 -m pip list | grep -E "jose|jwt|pydantic|psutil|httpx|asyncpg|pusher|langchain|telemetry|prometheus"
```

### If Login Still Returns 404:

Check if the auth router is loaded:

```bash
curl http://localhost:8009/docs
# Should show OpenAPI documentation with /api/v1/auth/login endpoint
```

---

**Status**: Dependencies added to requirements.txt, awaiting manual installation by user.

**Next**: Install packages → Start backend → Test login → Hard refresh dashboard

**Last Updated**: November 4, 2025, 11:15 PM EST

