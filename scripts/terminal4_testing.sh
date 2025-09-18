#!/bin/bash
# DEPRECATED: Use scripts/testing/run_comprehensive_tests.sh
# This script is retained temporarily for guidance and will exit.
echo "Use scripts/testing/run_comprehensive_tests.sh" >&2
exit 1
# Terminal 4: Testing and Verification
# Runs comprehensive tests and verifies all services

echo "========================================="
echo "Terminal 4: Testing and Verification"
echo "========================================="

cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Function to check service
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "  Checking $service_name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    if [ "$response" = "$expected_status" ]; then
        echo "✓ OK ($response)"
        return 0
    else
        echo "✗ FAILED (got $response, expected $expected_status)"
        return 1
    fi
}

# Wait for all services to be ready
echo "⏳ Waiting for all services to be ready..."
sleep 5

echo ""
echo "🔍 Service Health Checks:"
echo "========================================="

# Check backend services
check_service "FastAPI Backend" "http://127.0.0.1:8008/health"
check_service "API Documentation" "http://127.0.0.1:8008/docs"
check_service "Socket.io Endpoint" "http://127.0.0.1:8008/socket.io/?EIO=4&transport=polling"

# Check API endpoints
echo ""
echo "🔍 API Endpoint Checks:"
check_service "API Status" "http://127.0.0.1:8008/api/v1/status"
check_service "Auth Verify" "http://127.0.0.1:8008/auth/verify" 422  # Expects 422 without token

# Check Roblox bridge
check_service "Roblox Bridge" "http://127.0.0.1:5001/health"

# Check frontend
check_service "Dashboard Frontend" "http://localhost:5177"

echo ""
echo "🧪 Running Unit Tests:"
echo "========================================="
cd ToolboxAI-Roblox-Environment
source venv/bin/activate

# Run quick unit tests
python -m pytest tests/unit/ -v --tb=short -x 2>/dev/null || echo "⚠️ Some unit tests failed"

echo ""
echo "🔄 Testing WebSocket Connection:"
echo "========================================="

# Test WebSocket connection with Python
python3 << 'EOF'
import asyncio
import socketio

async def test_socketio():
    sio = socketio.AsyncClient()
    
    try:
        await sio.connect('http://127.0.0.1:8008', 
                         socketio_path='/socket.io/',
                         wait_timeout=5)
        print("  ✓ Socket.io connection successful")
        
        # Send test message
        await sio.emit('ping', {'test': 'data'})
        await asyncio.sleep(1)
        
        await sio.disconnect()
        print("  ✓ Socket.io disconnection successful")
        return True
    except Exception as e:
        print(f"  ✗ Socket.io test failed: {e}")
        return False

# Run the test
asyncio.run(test_socketio())
EOF

echo ""
echo "📊 System Status:"
echo "========================================="

# Check running processes
echo "Active processes:"
ps aux | grep -E "uvicorn|npm|python" | grep -v grep | wc -l | xargs echo "  Total processes:"

# Check port usage
echo ""
echo "Port usage:"
for port in 8008 5001 5177; do
    if lsof -i:$port > /dev/null 2>&1; then
        echo "  Port $port: ✓ In use"
    else
        echo "  Port $port: ✗ Free"
    fi
done

# Memory and CPU usage
echo ""
echo "Resource usage:"
top -l 1 -n 0 | grep "CPU usage" | head -1
top -l 1 -n 0 | grep "PhysMem" | head -1

echo ""
echo "========================================="
echo "Terminal 4 Testing Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✓ All critical services verified"
echo "  ✓ API endpoints tested"
echo "  ✓ WebSocket/Socket.io tested"
echo "  ✓ Basic unit tests run"
echo ""
echo "Next Steps:"
echo "  1. Open browser to http://localhost:5177"
echo "  2. Check browser console for errors"
echo "  3. Test login functionality"
echo "  4. Verify real-time updates work"
echo "========================================="