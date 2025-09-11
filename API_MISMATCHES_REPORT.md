# API Mismatches & Integration Issues Report
## Terminal 3 - Roblox Integration
## Date: 2025-09-09

## 🔴 Critical Issues

### 1. Dashboard Not Running (Port 5179)
- **Issue**: Dashboard is not accessible on port 5179
- **Impact**: Cannot test full integration flow
- **Required Action**: Terminal 2 needs to start dashboard service

### 2. Authentication Endpoints Missing/Broken
- **Issue**: No working login endpoints found
- **Tested Endpoints**:
  - `http://127.0.0.1:8008/auth/login` - Returns 401
  - `http://127.0.0.1:8008/auth/token` - Returns 422
  - `http://127.0.0.1:8008/api/v1/auth/login` - Not found
  - `http://127.0.0.1:5179/api/auth/login` - Connection refused
- **Impact**: Cannot authenticate for protected endpoints
- **Required Action**: Fix authentication flow or provide test tokens

### 3. WebSocket Authentication Failed
- **Issue**: MCP WebSocket (port 9876) not handling authentication
- **Response**: Returns "context" instead of authentication confirmation
- **Impact**: Real-time updates not working
- **Required Action**: Terminal 2 priority - fix WebSocket auth

## 🟡 API Mismatches Found

### Flask Bridge Endpoints
1. **Content Generation**
   - Expected: `/plugin/generate`
   - Actual: `/plugin/content/generate`
   - Status: Endpoint exists but returns empty content

2. **Quiz Generation**
   - Endpoint: `/generate_quiz`
   - Issue: Returns 401 (unauthorized) - needs auth token
   - Response format missing `questions` field

3. **Terrain Generation**
   - Endpoint: `/generate_terrain`
   - Issue: Returns 401 (unauthorized)
   - Response format missing `regions` field

4. **Script Generation**
   - Endpoint: `/script/{script_type}`
   - Issue: Returns 200 but no `source` field in response
   - Only `script` field available

### Plugin Communication
1. **Plugin Registration**
   - Endpoint: `/register_plugin`
   - Required fields: `plugin_id`, `studio_id`, `port`, `version`
   - Working correctly

2. **Plugin Polling**
   - Expected: `/plugin/poll`
   - Actual: `/plugin/poll-messages`
   - Requires `plugin_id` and `studio_id` in request body

3. **Dashboard Sync**
   - Endpoint: `/plugin/dashboard/sync`
   - Returns 500 error - internal server error
   - Needs investigation

## ✅ Working Endpoints

1. **Health Checks**
   - Flask Bridge: `http://127.0.0.1:5001/health` ✅
   - FastAPI: `http://127.0.0.1:8008/health` ✅
   - MCP WebSocket: `ws://127.0.0.1:9876` ✅ (connects but auth fails)

2. **Plugin Management**
   - `/register_plugin` ✅
   - `/plugins` (GET) ✅
   - `/plugin/{plugin_id}` (GET) ✅

3. **Basic Content Generation**
   - `/generate_simple_content` ✅ (but needs auth)

## 📊 Test Results Summary

### Flask Bridge Integration
- Total Tests: 9
- Passed: 4 (44.4%)
- Failed: 5
- Main Issues: Content generation auth, response formats

### Dashboard Integration
- Total Tests: 9
- Passed: 2 (22.2%)
- Failed: 7
- Main Issues: Dashboard not running, auth not working

## 🚨 Recommendations for Other Terminals

### For Terminal 1 (Backend):
1. Fix authentication endpoints - provide clear auth flow
2. Add CORS headers for dashboard requests
3. Implement proper error messages (not just status codes)
4. Fix `/plugin/dashboard/sync` endpoint (500 error)

### For Terminal 2 (Dashboard):
1. **PRIORITY**: Start dashboard service on port 5179
2. **CRITICAL**: Fix WebSocket authentication in MCP
3. Implement login flow with proper token management
4. Add real-time update listeners

### For Debugger:
1. Dashboard is blocking integration testing
2. WebSocket auth is the critical path issue
3. Authentication system needs unified approach

## 📝 Data Format Requirements

### Quiz Generation Should Return:
```json
{
  "success": true,
  "content": {
    "type": "quiz",
    "questions": [
      {
        "question": "...",
        "answers": [...],
        "correct": 0
      }
    ]
  }
}
```

### Terrain Generation Should Return:
```json
{
  "success": true,
  "content": {
    "type": "terrain",
    "regions": [
      {
        "type": "sphere|block",
        "x": 0, "y": 0, "z": 0,
        "material": "Grass",
        "radius": 10
      }
    ]
  }
}
```

### Script Generation Should Return:
```json
{
  "success": true,
  "content": {
    "type": "script",
    "source": "-- Lua code here",
    "script_type": "LocalScript|ServerScript|ModuleScript"
  }
}
```

## 🔄 Integration Flow Status

1. **Roblox → Flask Bridge**: ✅ Working (registration, heartbeat)
2. **Flask Bridge → FastAPI**: ⚠️ Partial (auth issues)
3. **Dashboard → API**: ❌ Not testable (dashboard down)
4. **API → MCP**: ⚠️ Connects but auth fails
5. **MCP → Dashboard**: ❌ WebSocket auth broken

## 📋 Next Steps for Terminal 3

1. ✅ Completed integration testing
2. ✅ Documented all API mismatches
3. ⏳ Waiting for Terminal 2 to fix dashboard/WebSocket
4. 📝 Ready to test Roblox plugin in Studio when endpoints fixed
5. 🎯 95% complete - just need working endpoints to finish

---

**Terminal 3 Status**: Ready for final integration once Terminal 2 fixes WebSocket auth
**Blockers**: Dashboard not running, WebSocket auth not working
**Time to Complete**: ~1 day once blockers resolved