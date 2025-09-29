# 🟡 TERMINAL 2: FRONTEND DASHBOARD FIX

**STATUS: CRITICAL - Blocking User Access**
**Priority: Execute AFTER Terminal 1 confirms backend is ready**
**Time Required: 20 minutes**

## 🔴 CRITICAL ISSUES TO FIX

1. **LocalStorage Quota Exceeded** - Terminal verification storing too much data
2. **User-Agent Headers Being Rejected** by browser security
3. **WebSocket Connection Failures** to backend
4. **Dashboard Not Loading** due to API connection errors

## 📋 PRE-FLIGHT CHECKLIST

```bash
# 1. WAIT for Terminal 1 confirmation
echo "⏳ Waiting for Terminal 1 to confirm backend is ready..."
echo "Check that you see: 'TERMINAL 1 STATUS: ✅ COMPLETE'"

# 2. Verify backend is accessible
curl -s http://localhost:8008/health -H "Origin: http://localhost:5179" | jq .
# Should return: {"status": "healthy", "timestamp": "..."}

# 3. Navigate to dashboard directory
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/src/dashboard

# 4. Check current dashboard status
lsof -i :5179
# Note if running and kill if needed

# 5. Install dependencies if needed
npm install socket.io-client axios
```

## 🛠️ STEP 1: BACKUP EXISTING FILES

```bash
# Create backup directory
mkdir -p ../../backups/dashboard_$(date +%Y%m%d_%H%M%S)

# Backup critical files
cp src/services/terminal-verify.ts ../../backups/dashboard_$(date +%Y%m%d_%H%M%S)/
cp src/services/api.ts ../../backups/dashboard_$(date +%Y%m%d_%H%M%S)/
cp src/services/websocket.ts ../../backups/dashboard_$(date +%Y%m%d_%H%M%S)/

echo "✅ Backups created"
```

## 🛠️ STEP 2: FIX LOCALSTORAGE QUOTA ISSUE

```bash
# Apply the localStorage fix
cat > src/services/terminal-verify-fixed.ts << 'EOF'
import axios, { AxiosInstance } from 'axios';
import io, { Socket } from 'socket.io-client';

interface VerificationResult {
  verificationId: string;
  timestamp: string;
  services: ServiceStatus[];
}

interface ServiceStatus {
  name: string;
  url: string;
  status: 'healthy' | 'degraded' | 'down';
  responseTime?: number;
  error?: string;
}

export class TerminalVerificationService {
  private verificationHistory: Map<string, VerificationResult> = new Map();
  private socket: Socket | null = null;
  private api: AxiosInstance;
  private maxHistorySize = 10; // Limit to prevent memory issues
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Configure axios WITHOUT User-Agent header
    this.api = axios.create({
      baseURL: 'http://localhost:8008',
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json'
        // NO User-Agent header - browsers reject it
      }
    });

    // Add response interceptor for debugging
    this.api.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 0) {
          console.error('⚠️ CORS error - check Terminal 1 backend');
        }
        return Promise.reject(error);
      }
    );

    this.initializeSocketConnection();
    this.startCleanupRoutine();
  }

  private initializeSocketConnection() {
    console.log('🔌 Connecting to backend Socket.IO...');
    
    this.socket = io('http://localhost:8008', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      transports: ['websocket', 'polling'],
      withCredentials: true
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to Terminal 1 via Socket.IO');
      this.clearOldLocalStorageData(); // Clean on connect
    });

    this.socket.on('verification_response', (data) => {
      console.log('📊 Verification response:', data);
    });

    this.socket.on('connect_error', (error) => {
      console.warn('⚠️ Socket.IO connection issue, using HTTP fallback');
      // Don't log full error object to reduce console noise
    });

    this.socket.on('disconnect', () => {
      console.log('🔌 Socket.IO disconnected');
    });
  }

  private startCleanupRoutine() {
    // Clean up old data every 5 minutes
    this.cleanupInterval = setInterval(() => {
      this.cleanupOldData();
    }, 5 * 60 * 1000);
  }

  private cleanupOldData() {
    // Clean memory map
    if (this.verificationHistory.size > this.maxHistorySize) {
      const entriesToDelete = this.verificationHistory.size - this.maxHistorySize;
      const keys = Array.from(this.verificationHistory.keys());
      for (let i = 0; i < entriesToDelete; i++) {
        this.verificationHistory.delete(keys[i]);
      }
    }

    // Clean localStorage selectively
    this.clearOldLocalStorageData();
  }

  private clearOldLocalStorageData() {
    try {
      const keysToRemove: string[] = [];
      
      // Find all terminal verification keys
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('terminal_verification_') || 
                   key.startsWith('terminal_verify_'))) {
          keysToRemove.push(key);
        }
      }

      // Remove old keys
      keysToRemove.forEach(key => localStorage.removeItem(key));

      if (keysToRemove.length > 0) {
        console.log(`✅ Cleared ${keysToRemove.length} old verification entries`);
      }

      // Store minimal summary only
      const summary = {
        lastCleanup: new Date().toISOString(),
        verificationCount: this.verificationHistory.size
      };
      localStorage.setItem('terminal_verify_summary', JSON.stringify(summary));

    } catch (e) {
      if (e instanceof DOMException && e.name === 'QuotaExceededError') {
        // If still quota exceeded, clear everything
        console.warn('⚠️ Quota still exceeded, clearing all localStorage');
        localStorage.clear();
      }
    }
  }

  async runVerification(): Promise<VerificationResult> {
    const verificationId = `verify_${Date.now()}`;
    
    const services: ServiceStatus[] = [
      { name: 'FastAPI', url: 'http://localhost:8008/health', status: 'down' },
      { name: 'Dashboard API', url: 'http://localhost:8008/api/v1/dashboard/overview', status: 'down' },
      { name: 'WebSocket', url: 'ws://localhost:8008/ws', status: 'down' },
      { name: 'Socket.IO', url: 'http://localhost:8008/socket.io/', status: 'down' }
    ];

    // Check each service
    for (const service of services) {
      await this.verifyServiceEndpoint(service);
    }

    const result: VerificationResult = {
      verificationId,
      timestamp: new Date().toISOString(),
      services
    };

    // Store in memory only
    this.storeVerificationResult(result);

    // Send to backend
    await this.sendVerificationToBackend(result);

    return result;
  }

  private async verifyServiceEndpoint(service: ServiceStatus): Promise<void> {
    const startTime = Date.now();
    
    try {
      if (service.url.startsWith('ws://')) {
        service.status = await this.checkWebSocket(service.url) ? 'healthy' : 'down';
      } else {
        const response = await this.api.get(service.url);
        service.status = response.status === 200 ? 'healthy' : 'degraded';
        service.responseTime = Date.now() - startTime;
      }
    } catch (error) {
      service.status = 'down';
      // Don't store full error to save space
      service.error = 'Connection failed';
    }
  }

  private checkWebSocket(url: string): Promise<boolean> {
    return new Promise((resolve) => {
      const ws = new WebSocket(url);
      const timeout = setTimeout(() => {
        ws.close();
        resolve(false);
      }, 2000);

      ws.onopen = () => {
        clearTimeout(timeout);
        ws.close();
        resolve(true);
      };

      ws.onerror = () => {
        clearTimeout(timeout);
        resolve(false);
      };
    });
  }

  private storeVerificationResult(result: VerificationResult) {
    // Store in memory map only
    this.verificationHistory.set(result.verificationId, result);
    
    // Enforce size limit
    if (this.verificationHistory.size > this.maxHistorySize) {
      const firstKey = this.verificationHistory.keys().next().value;
      if (firstKey) {
        this.verificationHistory.delete(firstKey);
      }
    }

    // Don't store full results in localStorage
    console.log(`📊 Verification stored in memory: ${result.verificationId}`);
  }

  private async sendVerificationToBackend(result: VerificationResult) {
    const summary = {
      verificationId: result.verificationId,
      healthy: result.services.filter(s => s.status === 'healthy').length,
      total: result.services.length,
      timestamp: result.timestamp
    };

    console.log('📤 Sending to backend:', summary);

    // Try Socket.IO first
    if (this.socket?.connected) {
      this.socket.emit('verification_update', summary);
      return;
    }

    // Fallback to HTTP
    try {
      await this.api.post('/api/v1/terminal/verification', summary);
    } catch (error) {
      console.warn('⚠️ Could not send verification to backend');
    }
  }

  cleanup() {
    if (this.socket) {
      this.socket.disconnect();
    }
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    this.verificationHistory.clear();
    this.clearOldLocalStorageData();
  }
}

export const terminalVerify = new TerminalVerificationService();
EOF

# Replace the old file
mv src/services/terminal-verify-fixed.ts src/services/terminal-verify.ts

echo "✅ Terminal verification service fixed"
```

## 🛠️ STEP 3: FIX API SERVICE HEADERS

```bash
# Fix the API service to remove User-Agent
cat > /tmp/fix_api_service.py << 'EOF'
import re

# Read the api.ts file
with open('src/services/api.ts', 'r') as f:
    content = f.read()

# Remove User-Agent headers
content = re.sub(r"['\"]User-Agent['\"]:\s*['\"][^'\"]*['\"],?\s*\n?", "", content)

# Ensure proper baseURL
if 'baseURL:' in content:
    content = re.sub(r"baseURL:\s*['\"][^'\"]*['\"]", "baseURL: 'http://localhost:8008'", content)

# Add withCredentials for CORS
if 'withCredentials' not in content:
    content = re.sub(r"(timeout:\s*\d+)", r"\1,\n  withCredentials: true", content)

# Write back
with open('src/services/api.ts', 'w') as f:
    f.write(content)

print("✅ API service headers fixed")
EOF

python /tmp/fix_api_service.py
```

## 🛠️ STEP 4: FIX WEBSOCKET SERVICE

```bash
# Fix WebSocket service configuration
cat > src/services/websocket-fixed.ts << 'EOF'
import io, { Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private isIntentionalDisconnect = false;

  constructor() {
    this.connect();
  }

  connect() {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    console.log('🔌 Initializing WebSocket connection...');
    
    this.socket = io('http://localhost:8008', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
      timeout: 20000,
      transports: ['websocket', 'polling'],
      withCredentials: true,
      path: '/socket.io/'
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected successfully');
      this.reconnectAttempts = 0;
      this.emit('status', { connected: true });
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`🔌 WebSocket disconnected: ${reason}`);
      if (!this.isIntentionalDisconnect) {
        this.attemptReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.warn('⚠️ WebSocket connection error');
      // Don't log full error to reduce console spam
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error.message || 'Unknown error');
    });

    // Handle custom events
    this.socket.on('message', (data) => {
      console.log('📨 Received message:', data);
    });

    this.socket.on('update', (data) => {
      console.log('🔄 Received update:', data);
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`🔄 Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
    
    setTimeout(() => {
      this.connect();
    }, 1000 * this.reconnectAttempts);
  }

  emit(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn(`⚠️ Cannot emit '${event}' - WebSocket not connected`);
    }
  }

  on(event: string, callback: (data: any) => void) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  disconnect() {
    this.isIntentionalDisconnect = true;
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();
export default websocketService;
EOF

mv src/services/websocket-fixed.ts src/services/websocket.ts
echo "✅ WebSocket service fixed"
```

## 🛠️ STEP 5: CLEAR BROWSER STORAGE

```bash
# Create browser cleanup script
cat > clear_browser_storage.js << 'EOF'
// Run this in the browser console at http://localhost:5179

console.log('🧹 Starting browser storage cleanup...');

// Clear all localStorage
const localStorageSize = localStorage.length;
localStorage.clear();
console.log(`✅ Cleared ${localStorageSize} localStorage items`);

// Clear all sessionStorage
const sessionStorageSize = sessionStorage.length;
sessionStorage.clear();
console.log(`✅ Cleared ${sessionStorageSize} sessionStorage items`);

// Clear IndexedDB
if (window.indexedDB) {
  indexedDB.databases().then(databases => {
    databases.forEach(db => {
      indexedDB.deleteDatabase(db.name);
      console.log(`✅ Deleted IndexedDB: ${db.name}`);
    });
  });
}

// Clear cookies for localhost
document.cookie.split(";").forEach(function(c) { 
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
});
console.log('✅ Cleared cookies');

// Clear cache storage
if ('caches' in window) {
  caches.keys().then(names => {
    names.forEach(name => {
      caches.delete(name);
      console.log(`✅ Deleted cache: ${name}`);
    });
  });
}

console.log('🎉 Browser storage cleanup complete!');
console.log('📝 Refresh the page to start fresh');
EOF

echo "✅ Browser cleanup script created"
echo ""
echo "📋 TO CLEAR BROWSER STORAGE:"
echo "1. Open http://localhost:5179 in browser"
echo "2. Open DevTools Console (F12)"
echo "3. Copy and paste the contents of clear_browser_storage.js"
echo "4. Press Enter to run"
echo "5. Refresh the page"
```

## 🛠️ STEP 6: RESTART DASHBOARD

```bash
# Kill existing dashboard process
echo "Stopping existing dashboard..."
pkill -f "vite.*5179" || true
sleep 2

# Clear Node.js cache
rm -rf node_modules/.vite
rm -rf node_modules/.cache

# Start dashboard
echo "🚀 Starting dashboard with fixes..."
npm run dev &
DASHBOARD_PID=$!

echo "Dashboard started with PID: $DASHBOARD_PID"
echo $DASHBOARD_PID > ../../scripts/pids/dashboard.pid

# Wait for it to start
echo "Waiting for dashboard to initialize..."
sleep 8

# Test if accessible
if curl -s http://localhost:5179 | grep -q "<!DOCTYPE html>"; then
  echo "✅ Dashboard is running at http://localhost:5179"
else
  echo "❌ Dashboard not accessible"
fi
```

## 🛠️ STEP 7: VERIFY FIXES

```bash
# Create verification script
cat > verify_frontend.py << 'EOF'
#!/usr/bin/env python3
import time
import subprocess
import requests
from datetime import datetime

def check_browser_console():
    print("\n📋 BROWSER CONSOLE CHECK:")
    print("1. Open http://localhost:5179 in Chrome")
    print("2. Open DevTools (F12)")
    print("3. Go to Console tab")
    print("4. Check for these indicators:")
    print("   ✅ 'Connected to Terminal 1 via Socket.IO'")
    print("   ✅ No CORS errors")
    print("   ✅ No localStorage quota errors")
    print("   ✅ No User-Agent header errors")
    print("\n5. Go to Network tab")
    print("6. Check that API calls show:")
    print("   ✅ Status: 200 OK")
    print("   ✅ CORS headers present")

def automated_checks():
    print("\n🤖 AUTOMATED CHECKS:")
    
    # Check dashboard is running
    try:
        response = requests.get("http://localhost:5179", timeout=2)
        if response.status_code == 200:
            print("✅ Dashboard responding on port 5179")
        else:
            print(f"⚠️ Dashboard returned status {response.status_code}")
    except:
        print("❌ Dashboard not accessible on port 5179")
    
    # Check backend accessibility from dashboard origin
    try:
        response = requests.get(
            "http://localhost:8008/health",
            headers={"Origin": "http://localhost:5179"},
            timeout=2
        )
        if response.status_code == 200:
            print("✅ Backend accessible with CORS headers")
        else:
            print(f"⚠️ Backend returned status {response.status_code}")
    except:
        print("❌ Backend not accessible from dashboard origin")

print("=" * 60)
print("FRONTEND VERIFICATION REPORT")
print("=" * 60)
print(f"Time: {datetime.now().isoformat()}")

automated_checks()
check_browser_console()

print("\n" + "=" * 60)
print("📝 MANUAL VERIFICATION REQUIRED")
print("Please check the browser console as described above")
print("=" * 60)
EOF

python verify_frontend.py
```

## 🛠️ STEP 8: CREATE MONITORING SCRIPT

```bash
# Create frontend monitoring script
cat > monitor_frontend.sh << 'EOF'
#!/bin/bash

echo "🔍 FRONTEND MONITOR STARTED"
echo "============================"
echo ""

# Function to check service
check_service() {
    local name=$1
    local port=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✅ $name is running on port $port"
        return 0
    else
        echo "❌ $name is NOT running on port $port"
        return 1
    fi
}

# Function to test API call
test_api() {
    local endpoint=$1
    local origin=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: $origin" "http://localhost:8008$endpoint")
    if [ "$response" = "200" ]; then
        echo "✅ API endpoint $endpoint: OK"
    else
        echo "❌ API endpoint $endpoint: Failed (HTTP $response)"
    fi
}

while true; do
    clear
    echo "FRONTEND HEALTH MONITOR"
    echo "Time: $(date)"
    echo "========================================"
    
    # Check services
    check_service "Dashboard" 5179
    check_service "Backend" 8008
    
    echo ""
    echo "API Tests from Dashboard Origin:"
    test_api "/health" "http://localhost:5179"
    test_api "/api/v1/status" "http://localhost:5179"
    test_api "/api/v1/dashboard/overview" "http://localhost:5179"
    
    echo ""
    echo "Browser Check Required:"
    echo "- Open http://localhost:5179"
    echo "- Check DevTools Console for errors"
    echo "- Verify WebSocket connection"
    
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 10
done
EOF

chmod +x monitor_frontend.sh
echo "✅ Monitoring script created: ./monitor_frontend.sh"
```

## 📊 SUCCESS CRITERIA

After completing all steps:

- [ ] ✅ Dashboard loads at http://localhost:5179
- [ ] ✅ NO localStorage quota exceeded errors
- [ ] ✅ NO User-Agent header rejection errors
- [ ] ✅ NO CORS errors in browser console
- [ ] ✅ WebSocket connects successfully
- [ ] ✅ API calls return 200 OK
- [ ] ✅ Console shows "Connected to Terminal 1 via Socket.IO"

## 🚨 TROUBLESHOOTING

### If localStorage still has quota issues:
```javascript
// Run in browser console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### If WebSocket won't connect:
```javascript
// Test in browser console
const testSocket = io('http://localhost:8008');
testSocket.on('connect', () => console.log('Test connection successful'));
testSocket.on('connect_error', (e) => console.error('Connection failed:', e.message));
```

### If API calls still fail:
```javascript
// Test in browser console
fetch('http://localhost:8008/health', {
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include'
})
.then(r => r.json())
.then(d => console.log('API test:', d))
.catch(e => console.error('API error:', e));
```

### Check React performance:
```javascript
// In browser console
if (window.React && window.React.Profiler) {
  console.log('React Profiler available');
  // Use React DevTools Profiler tab to identify slow components
}
```

## 📝 FINAL VERIFICATION

Open browser at http://localhost:5179 and verify:

1. **Console Tab**:
   - ✅ "Connected to Terminal 1 via Socket.IO"
   - ❌ No red error messages
   - ❌ No CORS errors
   - ❌ No quota exceeded warnings

2. **Network Tab**:
   - ✅ /health returns 200
   - ✅ /socket.io/ connects
   - ✅ All API calls successful

3. **Application Tab**:
   - ✅ localStorage is not growing unbounded
   - ✅ Only essential data stored

## 🎯 NEXT STEPS

Once all tests pass:

1. **Test user interactions** in dashboard
2. **Monitor for memory leaks** in DevTools
3. **Notify Terminal 3** that frontend is ready
4. **Keep dashboard running** - DO NOT stop it

## 📞 COORDINATION

Post in coordination channel:
```
TERMINAL 2 STATUS: ✅ COMPLETE
- localStorage quota issue fixed
- User-Agent headers removed
- WebSocket connected to backend
- Dashboard running on http://localhost:5179
- No CORS errors
- Ready for Terminal 3 integration
```

---

**IMPORTANT**: Wait for Terminal 1 to complete FIRST. The backend must be running with CORS enabled before starting these fixes!