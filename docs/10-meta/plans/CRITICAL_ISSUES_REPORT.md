# Critical Issues Report - November 4, 2025

## Priority 1: Backend Authentication Endpoint Missing

### Issue
The frontend is calling `/api/v1/users/me/profile` but getting 403 Forbidden errors.

### Root Cause
1. The endpoint exists in `apps/backend/api/v1/endpoints/user_profile.py`
2. It requires authentication via JWT token
3. The login is succeeding but the token may not be properly stored or sent

### Status
- ✅ Endpoint registered: `/api/v1/users`
- ✅ JWT handler is working
- ❌ Token not being sent with profile request

### Fix Required
Check frontend token storage and axios configuration

---

## Priority 2: CORS Issues (Render Backend)

### Issue
```
Access to fetch at 'https://toolboxai-backend.onrender.com/health' from origin 'http://localhost:5179' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```

### Root Cause
Backend CORS is not configured to accept requests from localhost during development.

### Status
- ❌ Render backend missing CORS origin for localhost:5179

### Fix Required
Add localhost origins to Render environment variables:
```
BACKEND_CORS_ORIGINS=["https://toolboxai-dashboard.vercel.app","http://localhost:5179","http://127.0.0.1:5179"]
```

---

## Priority 3: SVG Attribute Errors (Non-blocking)

### Issue
```
Error: <svg> attribute width: Expected length, "calc(1rem * var(…"
```

### Root Cause
React doesn't support CSS calc() in SVG attributes. Mantine icons using CSS variables.

### Status
- ⚠️ Warning only - doesn't break functionality
- Affects: Mail, Lock, Check, AlertCircle icons

### Fix Required (Optional)
Update icon usage or suppress warnings

---

## Priority 4: Clerk Provider Errors

### Issue
```
Error: useUser can only be used within the <ClerkProvider /> component
```

### Root Cause
DevRoleSwitcher and RoleBasedRouter components trying to use Clerk hooks when Clerk is not initialized.

### Status
- ❌ Clerk integration not properly configured
- Components: DevRoleSwitcher, RoleBasedRouter

### Fix Required
Either:
1. Remove Clerk dependencies (recommended for custom auth)
2. Or properly initialize ClerkProvider

---

## Priority 5: Python Type Hints (Backend)

### Issue
```python
TypeError: unsupported operand type(s) for |: 'type' and 'type'
# Line: user_id: str | UUID
```

### Root Cause
Python 3.9 doesn't support PEP 604 union syntax (str | UUID).
Must use: `Union[str, UUID]`

### Status
- ❌ Multiple files affected
- Python version: 3.9

### Fix Required
Replace all `X | Y` with `Union[X, Y]`

---

## Priority 6: Missing Python Dependencies

### Issue
Multiple module import errors:
- `No module named 'numpy'`
- `No module named 'scipy'`
- `No module named 'opentelemetry'`
- `No module named 'langgraph'`
- `No module named 'stripe'`
- `No module named 'aiohttp'`
- `No module named 'psutil'`

### Status
- ❌ Requirements.txt incomplete

### Fix Required
Install missing packages (already provided command)

---

## Action Plan

### Immediate (Must Fix)
1. ✅ Fix Python 3.9 type hints (Union syntax)
2. ✅ Install missing Python dependencies
3. ⏳ Configure CORS for Render backend
4. ⏳ Remove or fix Clerk provider issues
5. ⏳ Fix frontend auth token handling

### Short Term (Should Fix)
6. Fix database connection string format
7. Add proper error handling for auth failures
8. Update frontend error suppression

### Long Term (Nice to Have)
9. Upgrade to Python 3.10+ for modern syntax
10. Add comprehensive logging
11. Set up proper monitoring

---

## Environment Configuration Needed

### Render Backend
```bash
# Add to Render dashboard environment variables
BACKEND_CORS_ORIGINS=["https://toolboxai-dashboard.vercel.app","http://localhost:5179","http://127.0.0.1:5179","https://toolboxai-backend.onrender.com"]
```

### Vercel Frontend
```bash
# Verify these are set
VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
VITE_API_BASE_URL_LOCAL=http://localhost:8009
```

---

## Testing Checklist

After fixes:
- [ ] Login with test credentials works
- [ ] Profile endpoint returns 200
- [ ] Dashboard loads without errors
- [ ] No CORS errors in console
- [ ] Backend health check passes
- [ ] Token refresh works
- [ ] Logout works properly

---

## Notes

- Backend is running on localhost:8009 ✅
- Frontend is running on localhost:5179 ✅
- Local communication works ✅
- Render backend needs CORS update
- Some features disabled due to missing dependencies (non-critical)

