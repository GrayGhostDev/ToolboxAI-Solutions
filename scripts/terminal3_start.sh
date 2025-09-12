#!/usr/bin/env sh

# Terminal 3 - Roblox Integration Startup Script
# Coordinates with all terminals and launches Roblox Studio integration
set -eu
# shellcheck source=common/lib.sh
. "$(cd "$(dirname "$0")"/.. && pwd -P)/scripts/common/lib.sh" 2>/dev/null || \
  . "$(cd "$(dirname "$0")"/.. && pwd -P)/common/lib.sh"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd -P)}"
SYNC_DIR="$PROJECT_ROOT/scripts/terminal_sync"
ROBLOX_DIR="$PROJECT_ROOT/ToolboxAI-Roblox-Environment/Roblox"
SCRIPTS_DIR="$ROBLOX_DIR/Scripts/ModuleScripts"

echo "🎮 Terminal 3 - Roblox Integration Startup"
echo "=========================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local url=$1
    local name=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is not responding${NC}"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo "⏳ Waiting for $name..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready${NC}"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Timeout waiting for $name${NC}"
    return 1
}

# Check dependencies
echo "🔍 Checking dependencies..."
echo ""

# Check Terminal 1 (Backend)
if ! wait_for_service "http://$API_HOST:$FLASK_PORT/health" "Terminal 1 (Flask Bridge)"; then
    echo -e "${RED}ERROR: Terminal 1 services not running${NC}"
    echo "Please start Terminal 1 first with the Flask bridge"
    exit 1
fi

# Check FastAPI backend
check_service "http://$API_HOST:$FASTAPI_PORT/health" "FastAPI Backend"

# Check Terminal 2 (Dashboard) - may not be required
if check_service "http://$API_HOST:$DASHBOARD_PORT" "Terminal 2 (Dashboard)"; then
    echo "Dashboard is available for integration"
else
    echo -e "${YELLOW}⚠️ Dashboard not running - some features may be limited${NC}"
fi

# Check MCP WebSocket
if nc -z "$API_HOST" "$MCP_PORT" 2>/dev/null; then
    echo -e "${GREEN}✅ MCP WebSocket server is listening${NC}"
else
    echo -e "${YELLOW}⚠️ MCP WebSocket not available${NC}"
fi

echo ""
echo "✅ All required services are ready"
echo ""

# Create status file
mkdir -p "$SYNC_DIR/status"
# Ensure scripts directory exists for monitor script
mkdir -p "$SYNC_DIR/scripts"
cat > "$SYNC_DIR/status/terminal3.json" << EOF
{
    "terminal": "terminal3",
    "status": "initializing",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "services": {
        "flask_bridge": "connected",
        "fastapi": "connected",
        "dashboard": "checking",
        "mcp_websocket": "checking"
    }
}
EOF

# Test Flask Bridge integration
echo "🧪 Testing Flask Bridge integration..."
echo ""

# Test health endpoint
if curl -s "http://$API_HOST:$FLASK_PORT/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Flask Bridge health check passed${NC}"
else
    echo -e "${YELLOW}⚠️ Flask Bridge health check returned unexpected response${NC}"
fi

# Test plugin registration
echo "Testing plugin registration..."
PLUGIN_ID="terminal3_test_$(date +%s)"
REGISTRATION_RESPONSE=$(curl -s -X POST http://localhost:5001/register_plugin \
    -H "Content-Type: application/json" \
    -d "{\"plugin_id\": \"$PLUGIN_ID\", \"version\": \"1.0.0\", \"capabilities\": [\"content\", \"quiz\", \"terrain\"]}" 2>/dev/null)

if echo "$REGISTRATION_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Plugin registration successful${NC}"
else
    echo -e "${YELLOW}⚠️ Plugin registration may have issues${NC}"
fi

echo ""

# Create Roblox monitoring script
echo "📝 Creating Roblox monitoring script..."
cat > "$SYNC_DIR/scripts/terminal3_monitor.lua" << 'EOFLUA'
-- Terminal 3 Roblox Studio Monitor Script
-- Run this in Roblox Studio to verify integration

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

print("🎮 Terminal 3 Integration Monitor")
print("=================================")

-- Configuration
local FLASK_URL = "http://127.0.0.1:5001"
local FASTAPI_URL = "http://127.0.0.1:8008"

-- Check Flask Bridge
local function checkFlaskBridge()
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_URL .. "/health",
            Method = "GET"
        })
    end)
    
    if success and response.StatusCode == 200 then
        print("✅ Flask Bridge: Connected")
        return true
    else
        warn("❌ Flask Bridge: Not responding")
        return false
    end
end

-- Check FastAPI
local function checkFastAPI()
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FASTAPI_URL .. "/health",
            Method = "GET"
        })
    end)
    
    if success and response.StatusCode == 200 then
        print("✅ FastAPI: Connected")
        return true
    else
        warn("❌ FastAPI: Not responding")
        return false
    end
end

-- Register plugin
local function registerPlugin()
    local pluginData = {
        plugin_id = game.PlaceId or "test_place",
        version = "1.0.0",
        timestamp = os.time()
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = FLASK_URL .. "/register_plugin",
            Method = "POST",
            Headers = {["Content-Type"] = "application/json"},
            Body = HttpService:JSONEncode(pluginData)
        })
    end)
    
    if success and response.StatusCode == 200 then
        print("✅ Plugin registered successfully")
        return true
    else
        warn("❌ Plugin registration failed")
        return false
    end
end

-- Run checks
print("\n🔍 Running integration checks...")
local flaskOk = checkFlaskBridge()
local apiOk = checkFastAPI()

if flaskOk and apiOk then
    print("\n✅ All systems operational")
    registerPlugin()
    
    -- Load Terminal Bridge module
    local success, TerminalBridge = pcall(function()
        return require(script.Parent.TerminalBridge)
    end)
    
    if success then
        print("✅ TerminalBridge module loaded")
        local bridge = TerminalBridge.new()
    else
        warn("⚠️ TerminalBridge module not found")
    end
else
    warn("\n⚠️ Some integration issues detected")
end

print("\n📊 Integration check complete")
EOFLUA

echo -e "${GREEN}✅ Monitor script created${NC}"
echo ""

# Open Roblox Studio if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🎮 Launching Roblox Studio..."
    open -a "Roblox Studio" 2>/dev/null || echo -e "${YELLOW}⚠️ Please open Roblox Studio manually${NC}"
else
    echo "📝 Please open Roblox Studio manually"
fi

echo ""
echo "📋 Next Steps for Roblox Studio:"
echo "1. Open Roblox Studio"
echo "2. Go to File → Settings → Security"
echo "3. Enable 'Allow HTTP Requests'"
echo "4. Create a new place or open existing"
echo "5. In ServerScriptService, create a new Script"
echo "6. Copy the monitor script from: $SYNC_DIR/scripts/terminal3_monitor.lua"
echo "7. Run the script to verify integration"
echo ""

# Update status to ready
cat > "$SYNC_DIR/status/terminal3.json" << EOF
{
    "terminal": "terminal3",
    "status": "ready",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "services": {
        "flask_bridge": "connected",
        "fastapi": "connected",
        "dashboard": "$(check_service "http://$API_HOST:$DASHBOARD_PORT" 'Dashboard' && echo 'connected' || echo 'not_available')",
        "mcp_websocket": "$(nc -z "$API_HOST" "$MCP_PORT" 2>/dev/null && echo 'connected' || echo 'not_available')",
        "roblox_studio": "waiting_for_launch"
    },
    "modules": {
        "TerminalBridge": "created",
        "ContentDeployer": "created",
        "PerformanceMonitor": "created",
        "IntegrationTests": "created"
    }
}
EOF

# Send status to debugger
if [ -f "$SYNC_DIR/sync.sh" ]; then
    "$SYNC_DIR/sync.sh" terminal3 status "Ready - All Roblox modules created, waiting for Studio" 2>/dev/null
fi

echo -e "${GREEN}✅ Terminal 3 initialization complete${NC}"
echo ""
echo "📊 Created Modules:"
echo "  - TerminalBridge.lua   : Inter-terminal communication"
echo "  - ContentDeployer.lua  : Educational content deployment"
echo "  - PerformanceMonitor.lua : Performance tracking"
echo "  - IntegrationTests.lua : Comprehensive testing"
echo ""
echo "🔄 Monitoring integration status..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor loop
while true; do
    # Check Flask Bridge periodically
    if curl -s "http://$API_HOST:$FLASK_PORT/health" > /dev/null 2>&1; then
        echo -n "."
    else
        echo ""
        echo -e "${YELLOW}⚠️ Flask Bridge disconnected, checking...${NC}"
        sleep 5
        if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
            echo -e "${RED}❌ Flask Bridge down, please restart Terminal 1${NC}"
            
            # Update status
            cat > "$SYNC_DIR/status/terminal3.json" << EOF
{
    "terminal": "terminal3",
    "status": "error",
    "error": "Flask Bridge disconnected",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
        fi
    fi
    
    sleep 10
done

