# Dashboard Error Fix Plan - November 4, 2025

## Executive Summary
Analysis of console errors reveals several critical issues preventing dashboard login and operation:
1. **CORS Configuration** - Backend not accepting frontend requests
2. **SVG Attribute Errors** - React/Lucide icon compatibility issues
3. **Authentication Flow** - 403 errors on profile endpoint
4. **Error Suppressor Issues** - Console error handling conflicts
5. **Missing Dependencies** - Several Python packages not installed

## Error Categories

### 🔴 CRITICAL (Must Fix Immediately)

#### 1. CORS Policy Errors
**Error**: `Access to fetch at 'https://toolboxai-backend.onrender.com/health' from origin 'http://localhost:5179' has been blocked by CORS policy`

**Root Cause**: Backend CORS middleware not configured to accept localhost:5179

**Fix**: Update CORS configuration in `apps/backend/core/security/cors.py`
```python
# Add to allowed_origins in development mode:
"http://localhost:5179",
"http://127.0.0.1:5179",
```

**Status**: ✅ Already configured correctly - verify .env file

#### 2. Authentication 403 Errors
**Error**: `GET http://localhost:8009/api/v1/users/me/profile 403 (Forbidden)`

**Root Cause**: Token not being sent with request OR invalid token

**Fix**: 
- Verify JWT token is stored and sent in Authorization header
- Check token expiration logic
- Ensure `get_current_user` dependency works correctly

**Status**: ⚠️ Needs investigation - endpoint exists but returns 403

#### 3. Error Suppressor Conflicts
**Error**: `TypeError: 'caller', 'callee', and 'arguments' properties may not be accessed on strict mode functions`

**Root Cause**: Error suppressor trying to access restricted function properties

**Fix**: Update error-suppressor-preload.js to avoid strict mode violations
```javascript
// Remove or refactor code accessing function.caller
// Use error.stack for stack traces instead
```

**Status**: 🔧 Needs fixing

### 🟠 HIGH (Fix Soon)

#### 4. SVG Attribute Warnings
**Error**: `Error: <svg> attribute width: Expected length, "calc(1rem * var(…"`

**Root Cause**: Lucide-react icons using CSS custom properties in SVG attributes

**Fix**: Update to latest lucide-react version or use wrapper component:
```bash
npm update lucide-react
```

**Status**: ⚠️ Low priority - doesn't break functionality

#### 5. Missing Python Dependencies
**Error**: Multiple "No module named" warnings in backend logs

**Packages Needed**:
- `python-jose[cryptography]` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `bcrypt` - Bcrypt algorithm
- `asyncpg` - PostgreSQL async driver
- `redis` - Redis cache
- `celery` - Task queue
- `pusher` - Realtime events
- `stripe` - Payment processing
- `httpx` - HTTP client
- `aiohttp` - Async HTTP
- `psutil` - System monitoring
- `langgraph` - LangChain graphs
- `scipy` - Scientific computing
- `numpy` - Numerical computing

**Fix**:
```bash
pip install python-jose[cryptography] passlib[bcrypt] PyJWT bcrypt asyncpg redis celery pusher stripe httpx aiohttp psutil langgraph scipy numpy email-validator
```

**Status**: 🔧 Needs installation

### 🟡 MEDIUM (Fix When Possible)

#### 6. Clerk Provider Error
**Error**: `Error: useUser can only be used within the <ClerkProvider /> component`

**Root Cause**: Clerk authentication components used outside provider context

**Fix**: Either:
- Wrap entire app in ClerkProvider
- OR remove Clerk components (DevRoleSwitcher, RoleBasedRouter)

**Status**: ⚠️ Review authentication strategy

#### 7. Database Driver Issues
**Error**: `The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.`

**Root Cause**: Using sync psycopg2 with async SQLAlchemy

**Fix**: Install and configure asyncpg:
```bash
pip install asyncpg
```

Update database URL in .env:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

**Status**: 🔧 Needs fixing

#### 8. Redis Configuration
**Error**: `Port out of range 0-65535`

**Root Cause**: Invalid Redis port in environment variables

**Fix**: Update .env file:
```
REDIS_PORT=6379
REDIS_HOST=localhost
```

**Status**: 🔧 Needs fixing

### 🟢 LOW (Nice to Have)

#### 9. Service Worker Cleanup
**Status**: ✅ Working correctly

#### 10. Cache Management
**Status**: ✅ Working correctly

## Implementation Steps

### Phase 1: Backend Fixes (30 minutes)

1. **Install Missing Dependencies**
   ```bash
   cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
   pip install python-jose[cryptography] passlib[bcrypt] PyJWT bcrypt asyncpg redis celery pusher stripe httpx aiohttp psutil email-validator
   ```

2. **Fix Database Configuration**
   - Update DATABASE_URL to use asyncpg driver
   - Verify PostgreSQL is running

3. **Fix Redis Configuration**
   - Set correct REDIS_PORT and REDIS_HOST
   - OR disable Redis if not needed

4. **Verify CORS Configuration**
   - Check allowed origins include localhost:5179
   - Test with curl or Postman

5. **Fix Authentication Endpoint**
   - Debug why /api/v1/users/me/profile returns 403
   - Check JWT token validation
   - Verify TokenData parsing

### Phase 2: Frontend Fixes (20 minutes)

1. **Fix Error Suppressor**
   - Remove strict mode violations
   - Update error handling logic

2. **Update Lucide Icons** (Optional)
   ```bash
   cd apps/dashboard
   npm update lucide-react
   ```

3. **Remove/Fix Clerk Components**
   - Either add ClerkProvider wrapper
   - OR remove DevRoleSwitcher and RoleBasedRouter

4. **Test Authentication Flow**
   - Login with test credentials
   - Verify token storage
   - Check profile loading

### Phase 3: Testing (15 minutes)

1. **Backend Health Check**
   ```bash
   curl http://localhost:8009/health
   ```

2. **CORS Test**
   ```bash
   curl -X OPTIONS http://localhost:8009/api/v1/auth/login \
     -H "Origin: http://localhost:5179" \
     -H "Access-Control-Request-Method: POST"
   ```

3. **Login Test**
   ```bash
   curl -X POST http://localhost:8009/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@toolboxai.com","password":"Admin123!"}'
   ```

4. **Profile Test** (with token)
   ```bash
   curl http://localhost:8009/api/v1/users/me/profile \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### Phase 4: Verification (10 minutes)

1. Start backend: `python3 -m uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8009`
2. Start frontend: `cd apps/dashboard && npm run dev`
3. Open browser: http://localhost:5179
4. Test login with: admin@toolboxai.com / Admin123!
5. Verify dashboard loads without errors

## Quick Command Reference

### Backend
```bash
# Install dependencies
pip install python-jose[cryptography] passlib[bcrypt] PyJWT bcrypt asyncpg redis celery pusher stripe httpx aiohttp psutil email-validator

# Start backend
python3 -m uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8009

# Check backend logs
tail -f apps/backend/logs/*.log
```

### Frontend
```bash
# Install/update dependencies
cd apps/dashboard
npm install
npm update lucide-react

# Start frontend
npm run dev

# Build for production
npm run build
```

### Testing
```bash
# Backend health
curl http://localhost:8009/health

# Login test
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@toolboxai.com","password":"Admin123!"}'
```

## Environment Variables Checklist

### Backend (.env)
```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
JWT_SECRET_KEY=<your-secret-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional but recommended
REDIS_HOST=localhost
REDIS_PORT=6379
ALLOWED_ORIGINS=["http://localhost:5179","http://127.0.0.1:5179"]
ENVIRONMENT=development
```

### Frontend (apps/dashboard/.env.local)
```bash
VITE_API_URL=http://localhost:8009
VITE_APP_ENV=development
```

## Success Criteria

✅ Backend starts without critical errors
✅ Frontend starts and loads login page
✅ CORS allows frontend requests
✅ Login succeeds and returns token
✅ Profile endpoint returns user data
✅ Dashboard loads with user info
✅ No critical console errors

## Next Steps After Fixes

1. **Security Hardening**
   - Run security scanner
   - Fix any critical vulnerabilities
   - Update dependencies

2. **Performance Optimization**
   - Enable Redis caching
   - Optimize database queries
   - Add request rate limiting

3. **Monitoring Setup**
   - Configure Sentry error tracking
   - Set up Prometheus metrics
   - Add health check endpoints

4. **Documentation**
   - Update API documentation
   - Create deployment guide
   - Write testing procedures

## Notes

- Most errors are warnings and don't break functionality
- Focus on CRITICAL and HIGH priority issues first
- Test thoroughly after each fix
- Keep error logs for reference

## Estimated Time to Complete

- Phase 1 (Backend): 30 minutes
- Phase 2 (Frontend): 20 minutes
- Phase 3 (Testing): 15 minutes
- Phase 4 (Verification): 10 minutes

**Total: ~75 minutes to working dashboard**

