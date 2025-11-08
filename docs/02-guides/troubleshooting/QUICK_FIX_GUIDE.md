# Quick Reference: Dashboard Error Fixes

## 🚨 If You're Seeing Errors

### Service Worker Errors in Console?

**Symptoms:**
```
sw.js:214 Uncaught (in promise) TypeError: Failed to fetch
sw.js:202 Error: Both cache and network failed
```

**Quick Fix:**
1. Hard reload: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. Open DevTools Console and run:
   ```javascript
   window.unregisterServiceWorkers()
   ```
3. Reload page again

---

### "apiFunction is not a function" Error?

**Symptoms:**
```
useApiCall.ts:133 TypeError: apiFunction is not a function
```

**Quick Fix:**
The hook has been updated to handle this gracefully. If you see this error:

1. **Check your component** - You're calling `useApiCall()` without passing a function:
   ```typescript
   // ❌ Wrong
   const { execute } = useApiCall();
   
   // ✅ Correct
   const { execute } = useApiCall(api.deleteAssessment);
   
   // ✅ Or provide function later
   const { execute } = useApiCall();
   // ... then call execute with a direct API call
   await execute(() => api.deleteAssessment(id));
   ```

2. **For temporary/mock implementations:**
   ```typescript
   const { execute } = useApiCall(undefined, { 
     mockEndpoint: '/assessments' 
   });
   ```

---

### WebSocket Connection Failed?

**Symptoms:**
```
WebSocket connection to 'ws://localhost:24678' failed
[vite] failed to connect to websocket
```

**Quick Fix:**
1. Restart the dev server:
   ```bash
   cd apps/dashboard
   npm run dev
   ```

2. Check if port 24678 is available:
   ```bash
   lsof -i :24678
   ```

3. If port is in use, kill the process or change the HMR port in `vite.config.js`

**Note:** These errors are non-critical. Hot Module Replacement may not work, but the app will function normally. Just manually refresh to see changes.

---

## 🔧 For Developers

### Using useApiCall Hook (Updated)

The hook now accepts an optional `apiFunction` parameter:

```typescript
import { useApiCall } from '@hooks/useApiCall';
import { api } from '@services/api';

// Option 1: Provide function upfront
const { execute, loading, error, data } = useApiCall(api.getData);

// Option 2: Call without function (for dynamic APIs)
const { execute, loading, error } = useApiCall();

// Then use execute with inline function
const handleDelete = async (id: string) => {
  try {
    await execute(() => api.deleteItem(id));
  } catch (error) {
    // Error handled automatically by hook
  }
};

// Option 3: With mock data for development
const { execute, data } = useApiCall(undefined, {
  mockEndpoint: '/my-endpoint',
  showNotification: true
});
```

### Components That Need Updates

These components are currently calling `useApiCall()` without functions but now work correctly. Consider updating them to use proper API functions:

1. **Assessments.tsx** (Line 91)
   ```typescript
   // Current (works but not ideal)
   const { execute: deleteAssessmentApi } = useApiCall();
   
   // Recommended
   const { execute: deleteAssessmentApi } = useApiCall(api.deleteAssessment);
   ```

2. **CreateLessonDialog.tsx** (Line 40)
   ```typescript
   // Current (works but not ideal)
   const { execute: createLesson, loading } = useApiCall();
   
   // Recommended
   const { execute: createLesson, loading } = useApiCall(api.createLesson);
   ```

3. **Missions.tsx** (Lines 117-119)
   ```typescript
   // Current (works but not ideal)
   const { execute: startMissionApi } = useApiCall();
   const { execute: claimRewardApi } = useApiCall();
   const { execute: joinChallengeApi } = useApiCall();
   
   // Recommended
   const { execute: startMissionApi } = useApiCall(api.startMission);
   const { execute: claimRewardApi } = useApiCall(api.claimReward);
   const { execute: joinChallengeApi } = useApiCall(api.joinChallenge);
   ```

---

## 📝 What Changed?

### Files Modified

1. **useApiCall.ts**
   - Made `apiFunction` parameter optional
   - Added validation to prevent "is not a function" errors
   - Better error messages for debugging

2. **main.tsx**
   - Added automatic service worker cleanup on dev startup
   - Prevents cached service worker errors

3. **vite.config.js**
   - Enhanced HMR error handling
   - Increased WebSocket timeout
   - Better file watching configuration

4. **sw.js** (new)
   - Self-unregistering service worker
   - Clears all caches on activation

5. **serviceWorkerCleanup.ts** (new)
   - Utility functions for manual cleanup
   - Available in browser console: `window.unregisterServiceWorkers()`

---

## 🎯 Testing Your Changes

After making changes to components using `useApiCall`:

1. **Check Console** - No "apiFunction is not a function" errors
2. **Test API Calls** - Verify CRUD operations work
3. **Check Loading States** - Ensure loading indicators appear
4. **Verify Error Handling** - Errors show proper notifications

---

## 💡 Best Practices

### DO ✅
- Pass API functions to `useApiCall` when possible
- Use TypeScript types for better type safety
- Handle errors gracefully with try-catch
- Use mock endpoints during development

### DON'T ❌
- Call `execute` without checking if `apiFunction` exists (hook does this now)
- Ignore TypeScript warnings about optional parameters
- Use service workers without proper testing
- Deploy without clearing browser cache

---

## 🆘 Still Having Issues?

1. **Clear everything:**
   ```bash
   # Stop dev server
   # Then clear caches
   rm -rf apps/dashboard/node_modules/.vite
   rm -rf apps/dashboard/dist
   
   # Restart
   npm run dev
   ```

2. **Check browser:**
   - Open DevTools → Application → Service Workers (should be empty)
   - Open DevTools → Application → Storage → Clear Site Data
   - Hard reload

3. **Verify environment:**
   ```bash
   node --version  # Should be >=22
   npm --version   # Should be >=10
   ```

4. **Check the detailed documentation:**
   - `DASHBOARD_ERROR_FIXES_2025-10-26.md` - Full technical details
   - `APPLICATION_REVIEW_2025.md` - Architecture overview

---

**Last Updated:** October 26, 2025  
**Status:** ✅ All fixes applied and tested

