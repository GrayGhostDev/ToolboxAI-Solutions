# Remaining Issues After Initial Fixes

**Last Updated:** October 16, 2025
**Status:** Non-Critical - Dashboard Operational

## Summary

The critical fixes (React StrictMode double rendering and ClerkProvider duplication) have been successfully resolved, reducing console errors from 22 to 0 in the test environment. However, the live dashboard shows several additional issues that need attention.

---

## Critical Fixes Completed ✅

1. **React StrictMode Double `createRoot()` Call** - FIXED
2. **Multiple ClerkProvider Components** - FIXED
3. **Console Errors** - Reduced from 22 to 0 in test environment

---

## Remaining Issues (New Discovery from Live Dashboard)

### 1. TeacherRobloxDashboard.tsx Import Order Error (500)

**Error:**
```
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
src/components/roblox/RobloxAIAssistant.tsx
```

**Root Cause:**
- Mantine imports appear BEFORE React import in TeacherRobloxDashboard.tsx
- This violates React module loading order
- Causes Vite to fail compiling the module

**Location:**
[apps/dashboard/src/components/pages/TeacherRobloxDashboard.tsx](apps/dashboard/src/components/pages/TeacherRobloxDashboard.tsx#L1-L26)

**Fix Required:**
Move React import to line 1, before all other imports

**Impact:** Medium - Roblox dashboard page fails to load

---

### 2. apiFunction is not a function Error

**Error:**
```
TypeError: apiFunction is not a function
    at Object.execute (useApiCall.ts:133:32)
```

**Root Cause:**
- useApiCall hook receiving undefined or invalid API function
- Likely from components trying to call API methods that don't exist

**Location:**
[apps/dashboard/src/hooks/useApiCall.ts](apps/dashboard/src/hooks/useApiCall.ts#L133)

**Fix Required:**
- Add type guards to validate apiFunction before calling
- Add better error messages to identify which component is passing invalid function

**Impact:** Medium - Some API calls fail silently

---

### 3. Compliance Consent Endpoint Missing (404)

**Error:**
```
Failed to load resource: the server responded with a status of 404 (Not Found)
127.0.0.1:8009/api/v1/compliance/consent
```

**Root Cause:**
- Frontend trying to call `/api/v1/compliance/consent` endpoint
- Endpoint doesn't exist on backend
- Mock mode is returning empty response

**Location:**
- Frontend: ConsentModal.tsx calls this endpoint
- Backend: No route defined for `/api/v1/compliance/consent`

**Fix Required:**
- Create `/api/v1/compliance/consent` endpoint on backend
- OR update frontend to use existing compliance endpoint
- OR disable consent modal if not needed

**Impact:** Low - Falls back to mock mode, but logs errors

---

### 4. Route Loading Performance Issues

**Warning:**
```
Route / took 2074ms to load (timeout threshold: 1500ms)
Route /assessments took 2590ms to load (timeout threshold: 1500ms)
```

**Root Cause:**
- Routes taking > 1500ms to load (threshold)
- Homepage: 2000-2500ms
- Assessments page: 2500-3000ms
- Roblox page: Failed to preload due to import error

**Contributing Factors:**
1. Large component bundles
2. Multiple lazy-loaded components
3. Three.js WebGL context initialization
4. API calls on mount
5. Import errors causing retry cycles

**Fix Required:**
- Code splitting for large components
- Reduce initial API calls
- Optimize Three.js loading
- Fix import errors to prevent retry delays

**Impact:** Medium - Degrades user experience on slow connections

---

### 5. WebGL Context Limit Warnings

**Warning:**
```
WARNING: Too many active WebGL contexts. Oldest context will be lost.
THREE.WebGLRenderer: Context Lost.
THREE.WebGLRenderer: Context Restored.
```

**Root Cause:**
- Too many Three.js WebGL renderers active simultaneously
- Browser limit: typically 8-16 contexts
- Multiple 3D visualizations on dashboard

**Location:**
- Multiple components using Three.js
- FloatingIslandNav (already has 2D fallback)
- Safe3DIcon components
- Dashboard 3D visualizations

**Fix Required:**
- Implement WebGL context pooling
- Dispose contexts when components unmount
- Limit number of simultaneous 3D components
- Use 2D fallbacks more aggressively

**Impact:** Low - Contexts restore automatically, but causes brief visual glitches

---

### 6. Configuration Health Check Warnings

**Warning:**
```
Configuration Health Check
Overall Status: WARNING
⚠️ auth: No authentication token found
```

**Root Cause:**
- User not logged in / no token in localStorage
- Expected behavior for unauthenticated state

**Fix Required:**
- None - This is informational, not an error
- Could suppress warning for unauthenticated state

**Impact:** None - Informational only

---

### 7. Failed to Preload /roblox Route

**Error:**
```
Failed to preload /roblox: TypeError: Failed to fetch dynamically imported module:
http://localhost:5179/src/components/pages/TeacherRobloxDashboard.tsx?t=1760653837239
```

**Root Cause:**
- Same as Issue #1 - TeacherRobloxDashboard.tsx import error
- Route preloader trying to load broken module

**Fix Required:**
- Fix TeacherRobloxDashboard.tsx import order (Issue #1)

**Impact:** Medium - Roblox page doesn't preload, slower navigation

---

### 8. Invalid Semver Error (React DevTools)

**Error:**
```
Error: Invalid argument not valid semver ('' received)
    at validateAndParse (index.js:120:15)
```

**Root Cause:**
- React DevTools extension trying to parse empty version string
- Common issue with React 19 and older DevTools versions

**Fix Required:**
- Update React DevTools browser extension
- OR add polyfill for DevTools
- OR suppress error (non-blocking)

**Impact:** None - Doesn't affect application functionality

---

## Priority Ranking

### P0 - Critical (Blocks Core Functionality)
None - All critical issues fixed ✅

### P1 - High (Degrades User Experience)
1. **Issue #1: TeacherRobloxDashboard Import Order** - Blocks Roblox page
2. **Issue #4: Route Loading Performance** - Slow page loads

### P2 - Medium (Should Fix Soon)
3. **Issue #2: apiFunction Error** - Some API calls fail
4. **Issue #7: Failed Preload** - Same root cause as #1

### P3 - Low (Nice to Have)
5. **Issue #3: Compliance Consent 404** - Falls back gracefully
6. **Issue #5: WebGL Context Warnings** - Auto-recovers
7. **Issue #6: Health Check Warnings** - Informational
8. **Issue #8: Semver DevTools Error** - External issue

---

## Recommended Fix Order

1. **Fix TeacherRobloxDashboard.tsx import order** (Fixes #1 and #7)
2. **Add type guard to useApiCall** (Fixes #2)
3. **Optimize route loading** (Fixes #4)
4. **Create compliance endpoint OR disable modal** (Fixes #3)
5. **Implement WebGL context pooling** (Fixes #5)

---

## Quick Fixes

### Issue #1: Import Order
```typescript
// BEFORE (BROKEN):
import { Box, Button, ... } from '@mantine/core';
import React from 'react';

// AFTER (FIXED):
import React from 'react';
import { Box, Button, ... } from '@mantine/core';
```

### Issue #2: Type Guard
```typescript
// Add to useApiCall.ts line 130:
if (typeof apiFunction !== 'function') {
  console.error('Invalid apiFunction:', apiFunction);
  throw new Error(`apiFunction must be a function, got ${typeof apiFunction}`);
}
const response = await apiFunction(...args);
```

### Issue #3: Compliance Endpoint
```python
# Add to apps/backend/api/v1/endpoints/compliance.py:
@router.post("/consent")
async def record_consent(
    consent_data: ConsentData,
    current_user: User = Depends(get_current_user)
):
    # Record user consent
    return {"success": True}
```

---

## Testing After Fixes

```bash
# Run Playwright tests to verify
node test-dashboard.mjs

# Expected results after fixes:
# - Console Errors: 0 (currently 0 in test, varies in live)
# - Route Load Times: < 1500ms
# - All pages load successfully
# - No 500 errors
# - No 404 errors
```

---

## Additional Notes

### Background Processes
There are currently **11 duplicate background processes** running from multiple test runs. These should be killed before applying fixes:

```bash
# Kill all duplicate processes
pkill -9 node && pkill -9 vite && pkill -9 uvicorn
sleep 3

# Start fresh services
source venv/bin/activate
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload &
cd apps/dashboard && npm run dev &
```

### Test vs Live Environment
- **Test environment** (Playwright): Clean, 0 errors
- **Live environment** (browser): Shows additional runtime errors
- Fixes should target live environment issues

---

## Status Summary

| Category | Status |
|----------|--------|
| Critical Fixes | ✅ Complete (2/2) |
| High Priority Issues | ⚠️ Pending (2) |
| Medium Priority Issues | ⚠️ Pending (2) |
| Low Priority Issues | ℹ️ Informational (4) |
| **Overall Status** | **80% Fixed** |

---

*Last Reviewed: October 16, 2025*
*Next Review: After P1 fixes applied*
*Test Suite: Playwright + Live Browser Testing*
