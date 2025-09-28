# 🚨 TERMINAL 1: CRITICAL BACKEND CORS & WEBSOCKET FIX

**STATUS: CRITICAL - BLOCKING ALL OTHER TERMINALS**
**Priority: EXECUTE IMMEDIATELY**
**Time Required: 30 minutes**

## 🔴 CRITICAL ISSUES TO FIX

1. **CORS Policy Blocking ALL API Requests** from frontend (localhost:5179)
2. **Socket.IO Not Properly Mounted** at /socket.io/
3. **Token Verification Import Error** causing "server error"
4. **OPTIONS Preflight Requests** returning 400 errors

## 📋 PRE-FLIGHT CHECKLIST

```bash
# 1. Verify you're in the correct directory
pwd
# Should be: /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions

# 2. Check if backend is currently running (and kill it)
lsof -i :8008
# If running, note the PID and kill it:
kill -9 [PID]

# 3. Activate Python environment
cd ToolboxAI-Roblox-Environment
source venv_clean/bin/activate

# 4. Install required packages
pip install python-socketio[asyncio_server] python-socketio[asyncio_client] fastapi-cors
```

## 🛠️ STEP 1: BACKUP EXISTING FILES

```bash
# Create backup directory
mkdir -p ../backups/$(date +%Y%m%d_%H%M%S)

# Backup current main.py
cp server/main.py ../backups/$(date +%Y%m%d_%H%M%S)/main.py.backup

# Backup auth.py
cp server/auth.py ../backups/$(date +%Y%m%d_%H%M%S)/auth.py.backup

echo "✅ Backups created in ../backups/"
```

## 🛠️ STEP 2: FIX CORS CONFIGURATION

```bash
# Apply the CORS fix to main.py
cat > /tmp/cors_fix.py << 'EOF'
import sys
import re

# Read the main.py file
with open('server/main.py', 'r') as f:
    content = f.read()

# Find CORS middleware section
cors_pattern = r'app\.add_middleware\(\s*CORSMiddleware.*?\)'
cors_replacement = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5179",
        "http://127.0.0.1:5179",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)'''

# Replace CORS configuration
content = re.sub(cors_pattern, cors_replacement, content, flags=re.DOTALL)

# Add OPTIONS handler for preflight requests if not exists
if '@app.options("/auth/verify")' not in content:
    # Find where to insert (after the auth/verify POST endpoint)
    insert_point = content.find('@app.post("/auth/verify")')
    if insert_point != -1:
        # Find the end of the auth/verify function
        func_end = content.find('\n\n', insert_point)
        if func_end != -1:
            options_handler = '''

@app.options("/auth/verify")
async def options_auth_verify():
    """Handle preflight requests for auth verification."""
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5179",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"
        }
    )'''
            content = content[:func_end] + options_handler + content[func_end:]

# Fix the token verification import
content = content.replace('from auth import verify_token', 'from .auth import JWTManager')
content = re.sub(r'verify_token\(', 'JWTManager.verify_token(', content)

# Write back
with open('server/main.py', 'w') as f:
    f.write(content)

print("✅ CORS configuration fixed")
print("✅ OPTIONS handler added")
print("✅ Token verification import fixed")
EOF

python /tmp/cors_fix.py
```

## 🛠️ STEP 3: FIX SOCKET.IO MOUNTING

```bash
# Fix Socket.IO mounting in main.py
cat > /tmp/socketio_fix.py << 'EOF'
import sys

# Read the main.py file
with open('server/main.py', 'r') as f:
    lines = f.readlines()

# Find the Socket.IO initialization
modified = False
for i, line in enumerate(lines):
    if 'socketio.AsyncServer' in line and 'cors_allowed_origins' in line:
        # Ensure port 5179 is included
        if '5179' not in line:
            lines[i] = line.replace('cors_allowed_origins=[', 
                'cors_allowed_origins=["http://localhost:5179", "http://127.0.0.1:5179", ')
            modified = True
    
    # Fix the uvicorn.run line to use socketio_app
    if 'uvicorn.run(app,' in line:
        lines[i] = line.replace('uvicorn.run(app,', 'uvicorn.run(socketio_app,')
        modified = True

# Ensure Socket.IO is properly mounted
socket_mounted = False
for line in lines:
    if 'socketio_app = socketio.ASGIApp(sio, app)' in line:
        socket_mounted = True
        break

if not socket_mounted:
    # Find where to add it (after sio initialization)
    for i, line in enumerate(lines):
        if 'sio = socketio.AsyncServer' in line:
            # Add mounting after initialization
            lines.insert(i+1, 'socketio_app = socketio.ASGIApp(sio, app, socketio_path="/socket.io/")\n')
            modified = True
            break

# Write back
with open('server/main.py', 'w') as f:
    f.writelines(lines)

if modified:
    print("✅ Socket.IO mounting fixed")
else:
    print("ℹ️ Socket.IO already properly configured")
EOF

python /tmp/socketio_fix.py
```

## 🛠️ STEP 4: CREATE MINIMAL TEST SERVER

```bash
# Create a minimal test server to verify CORS is working
cat > server/test_cors.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime

app = FastAPI(title="CORS Test Server")

# Add CORS middleware with explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5179",
        "http://127.0.0.1:5179"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.options("/health")
async def options_health():
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5179",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

if __name__ == "__main__":
    print("🚀 Starting CORS test server on http://127.0.0.1:8008")
    print("📝 Test with: curl -I -X OPTIONS http://localhost:8008/health -H 'Origin: http://localhost:5179'")
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="info")
EOF

echo "✅ Test server created"
```

## 🛠️ STEP 5: TEST CORS CONFIGURATION

```bash
# Test the CORS configuration
echo "Testing CORS configuration..."

# Start test server in background
python server/test_cors.py &
TEST_PID=$!
sleep 3

# Test OPTIONS request
echo "Testing OPTIONS request..."
curl -s -I -X OPTIONS http://localhost:8008/health \
  -H "Origin: http://localhost:5179" \
  -H "Access-Control-Request-Method: GET" | grep "Access-Control"

# Test GET request
echo "Testing GET request..."
curl -s http://localhost:8008/health -H "Origin: http://localhost:5179" | jq .

# Kill test server
kill $TEST_PID

echo "✅ CORS test complete"
```

## 🛠️ STEP 6: START FIXED BACKEND

```bash
# Start the fixed backend server
echo "🚀 Starting fixed backend server..."

# Use the verification script if it exists
if [ -f "../fixes/TERMINAL1_CORS_WEBSOCKET_FIX.py" ]; then
    echo "Using pre-built fix file..."
    cp ../fixes/TERMINAL1_CORS_WEBSOCKET_FIX.py server/main_fixed.py
    python server/main_fixed.py &
else
    echo "Starting main server..."
    python server/main.py &
fi

BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for server to start
sleep 5

# Save PID for later
echo $BACKEND_PID > ../scripts/pids/backend.pid
```

## 🛠️ STEP 7: VERIFY ALL ENDPOINTS

```bash
# Run comprehensive verification
cat > /tmp/verify_backend.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8008"
DASHBOARD_ORIGIN = "http://localhost:5179"

def colored_print(status, message):
    if status:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

tests = [
    ("Health Check", "GET", "/health", None),
    ("API Status", "GET", "/api/v1/status", None),
    ("Auth Verify OPTIONS", "OPTIONS", "/auth/verify", None),
    ("Socket.IO Polling", "GET", "/socket.io/?EIO=4&transport=polling", None),
]

print("=" * 60)
print("BACKEND VERIFICATION REPORT")
print("=" * 60)
print(f"Time: {datetime.now().isoformat()}")
print(f"Backend URL: {BACKEND_URL}")
print(f"Testing from origin: {DASHBOARD_ORIGIN}")
print()

passed = 0
failed = 0

for test_name, method, endpoint, data in tests:
    try:
        headers = {"Origin": DASHBOARD_ORIGIN}
        if method == "OPTIONS":
            headers["Access-Control-Request-Method"] = "POST"
            headers["Access-Control-Request-Headers"] = "Content-Type, Authorization"
        
        if method == "GET":
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=2)
        elif method == "OPTIONS":
            response = requests.options(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=2)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(f"{BACKEND_URL}{endpoint}", headers=headers, json=data or {}, timeout=2)
        
        if response.status_code in [200, 201]:
            colored_print(True, f"{test_name}: {response.status_code}")
            passed += 1
            
            # Check CORS headers
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            if cors_origin and (cors_origin == "*" or DASHBOARD_ORIGIN in cors_origin):
                colored_print(True, f"  └─ CORS headers present")
            else:
                colored_print(False, f"  └─ CORS headers missing or incorrect: {cors_origin}")
        else:
            colored_print(False, f"{test_name}: {response.status_code}")
            failed += 1
    except Exception as e:
        colored_print(False, f"{test_name}: {str(e)}")
        failed += 1

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("🎉 ALL TESTS PASSED - Backend is ready!")
else:
    print("⚠️ Some tests failed - Review the errors above")
print("=" * 60)
EOF

python /tmp/verify_backend.py
```

## 🛠️ STEP 8: CREATE MONITORING SCRIPT

```bash
# Create ongoing monitoring script
cat > monitor_backend.sh << 'EOF'
#!/bin/bash

while true; do
    clear
    echo "==================================="
    echo "BACKEND HEALTH MONITOR"
    echo "Time: $(date)"
    echo "==================================="
    
    # Check if backend is running
    if lsof -i :8008 > /dev/null; then
        echo "✅ Backend is running on port 8008"
        
        # Check health endpoint
        if curl -s http://localhost:8008/health > /dev/null; then
            echo "✅ Health endpoint responding"
        else
            echo "❌ Health endpoint not responding"
        fi
        
        # Check CORS
        cors_header=$(curl -s -I http://localhost:8008/health -H "Origin: http://localhost:5179" | grep "Access-Control-Allow-Origin")
        if [[ -n "$cors_header" ]]; then
            echo "✅ CORS headers present: $cors_header"
        else
            echo "❌ CORS headers missing"
        fi
        
        # Check Socket.IO
        if curl -s http://localhost:8008/socket.io/?EIO=4 | grep -q "0{"; then
            echo "✅ Socket.IO endpoint responding"
        else
            echo "❌ Socket.IO endpoint not responding"
        fi
    else
        echo "❌ Backend is NOT running on port 8008"
        echo "Run: python server/main.py"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit monitoring"
    sleep 5
done
EOF

chmod +x monitor_backend.sh
echo "✅ Monitoring script created: ./monitor_backend.sh"
```

## 📊 SUCCESS CRITERIA

After completing all steps, verify:

- [ ] ✅ Backend running on http://127.0.0.1:8008
- [ ] ✅ CORS headers present for localhost:5179
- [ ] ✅ OPTIONS requests return 200 OK
- [ ] ✅ Socket.IO available at /socket.io/
- [ ] ✅ No "server error" on Socket.IO connection
- [ ] ✅ Health endpoint returns JSON response
- [ ] ✅ No import errors in logs

## 🚨 TROUBLESHOOTING

### If CORS still failing:
```bash
# Check the actual headers being sent
curl -v -X OPTIONS http://localhost:8008/health \
  -H "Origin: http://localhost:5179" \
  -H "Access-Control-Request-Method: GET" 2>&1 | grep -i "access-control"
```

### If Socket.IO not working:
```bash
# Test Socket.IO directly
curl http://localhost:8008/socket.io/?EIO=4&transport=polling

# Should return something like: 0{"sid":"...","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":5000}
```

### If import errors persist:
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Ensure auth.py exists
ls -la server/auth.py

# Check imports
python -c "from server.auth import JWTManager; print('Import successful')"
```

## 📝 FINAL VERIFICATION

Run the complete test suite:
```bash
python ../fixes/TERMINAL1_CORS_WEBSOCKET_FIX.py
```

Expected output:
```
============================================================
TERMINAL 1 - Dashboard-Backend Integration Verification
============================================================
Testing Health Endpoint... ✅ PASSED
Testing CORS Preflight... ✅ PASSED
Testing Socket.IO Endpoint... ✅ PASSED
Testing Auth Verify... ✅ PASSED
Testing API Status... ✅ PASSED

============================================================
✅ ALL TESTS PASSED - Integration Fixed!
============================================================
```

## 🎯 NEXT STEPS

Once all tests pass:

1. **Notify Terminal 2** that backend is ready
2. **Keep backend running** - DO NOT stop it
3. **Monitor logs** for any errors: `tail -f logs/backend.log`
4. **Save verification results**: Copy test output to `terminal1_verification.txt`

## 📞 COORDINATION

Post in coordination channel:
```
TERMINAL 1 STATUS: ✅ COMPLETE
- CORS fixed for localhost:5179
- Socket.IO mounted at /socket.io/
- All endpoints responding
- Backend running on PID: [YOUR_PID]
- Ready for Terminal 2 to connect
```

---

**REMEMBER**: This is the MOST CRITICAL fix. Without this, NO other terminal can proceed. Take your time and verify each step carefully!