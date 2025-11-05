# ToolBoxAI Error Resolution Action Plan
**Generated:** November 4, 2025  
**Status:** Critical Issues Identified  
**Priority:** High

---

## Executive Summary

The application has multiple critical issues preventing proper functionality:
1. **CORS Policy Errors** - Backend not responding with proper CORS headers
2. **Authentication Errors** - 403/404 errors on login and profile endpoints
3. **Clerk Provider Errors** - Components used outside ClerkProvider context
4. **SVG Rendering Errors** - Invalid CSS calc() in SVG attributes
5. **Console Error Suppressor Issues** - JavaScript strict mode violations

---

## 🔴 CRITICAL ISSUES (Must Fix Immediately)

### 1. CORS Policy Failures
**Symptoms:**
```
Access to fetch at 'https://toolboxai-backend.onrender.com/health' from origin 
'http://localhost:5179' has been blocked by CORS policy: Response to preflight 
request doesn't pass access control check: No 'Access-Control-Allow-Origin' 
header is present on the requested resource.
```

**Root Cause:**
- Backend CORS middleware not properly configured for frontend origin
- Missing CORS headers in OPTIONS preflight responses
- Render.com backend may not be running or responding

**Action Items:**
1. ✅ **Verify Backend is Running**
   ```bash
   # Check Render backend status
   curl -I https://toolboxai-backend.onrender.com/health
   ```

2. ✅ **Update CORS Configuration**
   - File: `apps/backend/core/security/cors.py`
   - Add frontend origins to allowed list:
     ```python
     self.allowed_origins = [
         "http://localhost:5179",
         "http://127.0.0.1:5179",
         "https://toolboxai-dashboard.vercel.app",
         "https://toolboxai.vercel.app",
         # Add other Vercel preview URLs pattern
     ]
     ```

3. ✅ **Update Environment Variables**
   - Add to `.env` and Render environment:
     ```
     CORS_ALLOWED_ORIGINS=http://localhost:5179,http://127.0.0.1:5179,https://toolboxai-dashboard.vercel.app
     CORS_ALLOW_CREDENTIALS=true
     CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS,PATCH
     CORS_ALLOWED_HEADERS=*
     ```

4. ✅ **Restart Backend Service**
   ```bash
   # On Render.com dashboard, trigger manual deploy or restart
   ```

---

### 2. Authentication Endpoint Issues
**Symptoms:**
```
POST http://localhost:8009/api/v1/auth/login 404 (Not Found)
GET http://localhost:8009/api/v1/users/me/profile 403 (Forbidden)
```

**Root Cause:**
- Auth router not properly registered in FastAPI app
- JWT token not being sent with requests
- Profile endpoint requires authentication but receiving unauthenticated requests

**Action Items:**
1. ✅ **Verify Auth Router Registration**
   - File: `apps/backend/api/routers/__init__.py`
   - Ensure auth_router is included:
     ```python
     from apps.backend.api.v1.endpoints.auth import auth_router
     app.include_router(auth_router, prefix="/api/v1")
     ```

2. ✅ **Fix Profile Endpoint Authentication**
   - File: `apps/backend/api/v1/endpoints/users.py`
   - Check current_user dependency is working:
     ```python
     @router.get("/me/profile")
     async def get_my_profile(
         current_user: User = Depends(get_current_user)
     ):
         # Return profile
     ```

3. ✅ **Update Frontend API Client**
   - File: `apps/dashboard/src/services/api.ts`
   - Ensure JWT token is included in headers:
     ```typescript
     const token = localStorage.getItem('token');
     if (token) {
       config.headers.Authorization = `Bearer ${token}`;
     }
     ```

4. ✅ **Test Login Flow**
   - Credentials: `admin@toolboxai.com` / `Admin123!`
   - Verify token is stored in localStorage
   - Verify token is sent with subsequent requests

---

### 3. Clerk Provider Context Errors
**Symptoms:**
```
Error: useUser can only be used within the <ClerkProvider /> component.
Components: RoleBasedRouter, DevRoleSwitcher
```

**Root Cause:**
- Components using Clerk hooks are rendered outside ClerkProvider wrapper
- Conditional rendering breaks React context hierarchy

**Action Items:**
1. ✅ **Fix ClerkProviderWrapper Rendering**
   - File: `apps/dashboard/src/main.tsx`
   - Ensure ClerkProvider always wraps the entire app when enabled:
     ```typescript
     const RootApp = () => {
       if (isClerkEnabled && clerkPubKey) {
         return (
           <Provider store={store}>
             <ClerkProviderWrapper>
               <ClerkAuthProvider>
                 <LegacyAuthProvider>
                   <App />
                 </LegacyAuthProvider>
               </ClerkAuthProvider>
             </ClerkProviderWrapper>
           </Provider>
         );
       }
       
       return (
         <Provider store={store}>
           <LegacyAuthProvider>
             <App />
           </LegacyAuthProvider>
         </Provider>
       );
     };
     ```

2. ✅ **Update RoleBasedRouter**
   - File: `apps/dashboard/src/components/auth/RoleBasedRouter.tsx`
   - Add conditional check before using Clerk hooks:
     ```typescript
     const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';
     const { isLoaded, user } = isClerkEnabled ? useUser() : { isLoaded: true, user: null };
     ```

3. ✅ **Update DevRoleSwitcher**
   - File: `apps/dashboard/src/components/dev/DevRoleSwitcher.tsx`
   - Wrap with conditional check:
     ```typescript
     if (!isClerkEnabled) return null;
     ```

4. ✅ **Disable Clerk Temporarily (If Needed)**
   - Update `.env`:
     ```
     VITE_ENABLE_CLERK_AUTH=false
     ```
   - This will use legacy auth while Clerk integration is fixed

---

### 4. SVG Rendering Errors
**Symptoms:**
```
Error: <svg> attribute width: Expected length, "calc(1rem * var(…".
Error: <svg> attribute height: Expected length, "calc(1rem * var(…".
```

**Root Cause:**
- CSS calc() with CSS variables not supported in SVG attributes
- Mantine/Lucide icons using invalid CSS values

**Action Items:**
1. ✅ **Fix Icon Sizing**
   - File: `apps/dashboard/src/components/icons/*`
   - Replace calc() in SVG attributes:
     ```typescript
     // BEFORE:
     <svg width="calc(1rem * var(--mantine-scale))" />
     
     // AFTER:
     <svg width="1rem" />
     // OR use style prop:
     <svg style={{ width: 'var(--icon-size)' }} />
     ```

2. ✅ **Update Mantine Icon Props**
   - Use size prop instead of width/height:
     ```typescript
     <Mail size={16} />
     <Lock size={16} />
     <AlertCircle size={18} />
     ```

3. ✅ **Add Global Icon Style Fix**
   - File: `apps/dashboard/src/theme/global-styles.css`
   - Add CSS override:
     ```css
     svg[width*="calc"],
     svg[height*="calc"] {
       width: 1em !important;
       height: 1em !important;
     }
     ```

---

## 🟡 HIGH PRIORITY ISSUES (Fix After Critical)

### 5. Error Suppressor JavaScript Issues
**Symptoms:**
```
TypeError: 'caller', 'callee', and 'arguments' properties may not be accessed 
on strict mode functions
```

**Root Cause:**
- Error suppressor trying to access restricted properties in strict mode
- Attempting to read function.caller

**Action Items:**
1. ✅ **Fix Error Suppressor**
   - File: `apps/dashboard/public/error-suppressor-preload.js`
   - Remove strict mode violations:
     ```javascript
     // REMOVE:
     const caller = arguments.callee.caller;
     
     // REPLACE WITH:
     const caller = null; // Cannot access in strict mode
     ```

2. ✅ **Simplify Error Suppression**
   - Use simpler approach without introspection:
     ```javascript
     const originalError = console.error;
     console.error = function(...args) {
       const message = String(args[0]);
       if (shouldSuppress(message)) return;
       originalError.apply(console, args);
     };
     ```

---

### 6. Backend Module Import Errors
**Symptoms:**
```
WARNING - Could not load router auth_router from apps.backend.api.v1.endpoints.auth: 
No module named 'jose'
WARNING - Could not load router classes_router: No module named 'passlib'
WARNING - Could not load router lessons_router: No module named 'jwt'
```

**Root Cause:**
- Missing Python dependencies
- Requirements.txt incomplete or not installed

**Action Items:**
1. ✅ **Update requirements.txt**
   ```
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4
   PyJWT==2.8.0
   bcrypt==4.1.2
   python-multipart==0.0.6
   email-validator==2.1.0
   asyncpg==0.29.0
   redis==5.0.1
   celery==5.3.4
   pusher==3.3.2
   stripe==7.8.0
   httpx==0.25.2
   aiohttp==3.9.1
   psutil==5.9.6
   brotli==1.1.0
   prometheus-fastapi-instrumentator==6.1.0
   ```

2. ✅ **Install Dependencies**
   ```bash
   cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
   python3 -m pip install -r requirements.txt
   ```

3. ✅ **Restart Backend**
   ```bash
   python3 -m uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8009
   ```

---

### 7. Database Connection Issues
**Symptoms:**
```
ERROR - Failed to initialize database engine: The asyncio extension requires 
an async driver to be used. The loaded 'psycopg2' is not async.
```

**Root Cause:**
- Using synchronous psycopg2 instead of async asyncpg
- Database URL not configured for async driver

**Action Items:**
1. ✅ **Install Async Database Driver**
   ```bash
   pip install asyncpg
   ```

2. ✅ **Update Database Connection**
   - File: `apps/backend/core/db_optimization.py`
   - Use asyncpg URL:
     ```python
     # Change from postgresql:// to postgresql+asyncpg://
     DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
         "postgresql://", 
         "postgresql+asyncpg://"
     )
     ```

---

### 8. Redis Configuration Errors
**Symptoms:**
```
ERROR - Failed to initialize Redis connection: Port out of range 0-65535
WARNING - Redis connection failed: Port out of range 0-65535. Using in-memory storage.
```

**Root Cause:**
- Redis port not properly configured
- Invalid Redis URL format

**Action Items:**
1. ✅ **Fix Redis Configuration**
   - File: `.env`
   - Update Redis URL:
     ```
     REDIS_URL=redis://127.0.0.1:6379/0
     REDIS_HOST=127.0.0.1
     REDIS_PORT=6379
     REDIS_DB=0
     ```

2. ✅ **Update Redis Connection Code**
   - File: `apps/backend/core/cache.py`
   - Add proper error handling:
     ```python
     try:
         redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
         redis_client = redis.from_url(redis_url)
         redis_client.ping()
     except Exception as e:
         logger.warning(f"Redis unavailable: {e}. Using in-memory cache.")
         redis_client = None
     ```

---

## 🟢 MEDIUM PRIORITY ISSUES (Fix After High Priority)

### 9. Chrome Extension Errors (Non-Critical)
**Symptoms:**
```
GET chrome-extension://pejdijmoenmkgeppbflobdenhhabjlaj/utils.js net::ERR_FILE_NOT_FOUND
```

**Root Cause:**
- Browser extension trying to inject scripts
- Not an application error

**Action Items:**
- ✅ **Ignore** - This is a browser extension issue, not app issue
- Or add error suppression pattern if needed

---

### 10. MutationObserver Errors (Non-Critical)
**Symptoms:**
```
TypeError: Failed to execute 'observe' on 'MutationObserver': parameter 1 is 
not of type 'Node'.
```

**Root Cause:**
- Third-party library trying to observe invalid DOM node
- Likely from React DevTools or extension

**Action Items:**
- ✅ **Add Error Boundary**
- ✅ **Update to latest React DevTools**
- Or suppress error in error-suppressor-preload.js

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Backend Fixes (Critical)
- [ ] Verify Render backend is running and accessible
- [ ] Update CORS configuration with frontend origins
- [ ] Install missing Python dependencies (jose, passlib, etc.)
- [ ] Fix database connection to use asyncpg
- [ ] Fix Redis configuration
- [ ] Verify auth router is registered
- [ ] Test /health endpoint returns 200
- [ ] Test /api/v1/auth/login endpoint
- [ ] Deploy backend to Render

### Phase 2: Frontend Fixes (Critical)
- [ ] Fix Clerk Provider wrapper conditional rendering
- [ ] Update RoleBasedRouter to check Clerk availability
- [ ] Update DevRoleSwitcher to check Clerk availability
- [ ] Fix SVG icon sizing (remove calc() from attributes)
- [ ] Fix error suppressor strict mode violations
- [ ] Test login flow with admin credentials
- [ ] Verify JWT token storage and transmission

### Phase 3: Testing & Validation
- [ ] Test backend health endpoint from browser
- [ ] Test CORS preflight requests
- [ ] Test login with admin account
- [ ] Test profile fetch after login
- [ ] Verify no console errors on login page
- [ ] Verify dashboard loads after authentication
- [ ] Test Clerk auth flow (if enabled)
- [ ] Test role-based routing

### Phase 4: Deployment
- [ ] Deploy backend to Render with updated env vars
- [ ] Deploy frontend to Vercel with updated env vars
- [ ] Verify production CORS configuration
- [ ] Monitor error logs for 24 hours
- [ ] Document any remaining issues

---

## 🛠️ QUICK FIX COMMANDS

### Start Local Development
```bash
# Terminal 1 - Backend
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
python3 -m pip install -r requirements.txt
python3 -m uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8009

# Terminal 2 - Frontend
cd apps/dashboard
npm install
npm run dev
```

### Test Backend Health
```bash
# Local
curl http://localhost:8009/health

# Render
curl https://toolboxai-backend.onrender.com/health
```

### Test CORS
```bash
curl -X OPTIONS http://localhost:8009/api/v1/auth/login \
  -H "Origin: http://localhost:5179" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

### Test Login
```bash
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@toolboxai.com","password":"Admin123!"}' \
  -v
```

---

## 📊 PRIORITY MATRIX

| Issue | Severity | Impact | Effort | Priority |
|-------|----------|--------|--------|----------|
| CORS Errors | Critical | High | Low | **P0** |
| Auth 404/403 | Critical | High | Medium | **P0** |
| Clerk Context | Critical | High | Low | **P0** |
| SVG Errors | High | Medium | Low | **P1** |
| Error Suppressor | Medium | Low | Low | **P2** |
| Missing Dependencies | High | High | Low | **P1** |
| Database Async | High | High | Medium | **P1** |
| Redis Config | Medium | Medium | Low | **P2** |

---

## 📝 NOTES

1. **Disable Clerk Temporarily**: Set `VITE_ENABLE_CLERK_AUTH=false` to use legacy auth while fixing Clerk integration
2. **CORS Must Match Exactly**: Ensure backend CORS origins match frontend URL exactly (including port)
3. **JWT Token Required**: Profile endpoint requires valid JWT token in Authorization header
4. **Render Cold Start**: Render free tier may take 30-60 seconds to wake up from sleep
5. **Local Backend First**: Get local backend working before debugging Render deployment

---

## 🎯 SUCCESS CRITERIA

✅ Backend `/health` endpoint returns 200  
✅ No CORS errors in browser console  
✅ Login succeeds and returns JWT token  
✅ Profile fetch succeeds with valid token  
✅ No Clerk Provider errors  
✅ No SVG attribute errors  
✅ Dashboard loads after successful login  
✅ All backend routers registered and working  

---

## 📞 NEXT STEPS

1. **Start with Backend**: Fix CORS and verify endpoints work
2. **Install Dependencies**: Ensure all Python packages installed
3. **Test Locally**: Get everything working on localhost first
4. **Fix Frontend**: Resolve Clerk and SVG issues
5. **Deploy**: Push to Render/Vercel with proper environment variables
6. **Monitor**: Watch logs for any remaining issues

---

**Last Updated:** November 4, 2025  
**Document Version:** 1.0  
**Status:** Ready for Implementation

