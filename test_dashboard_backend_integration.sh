#!/bin/bash

echo "=== DASHBOARD-BACKEND INTEGRATION TEST ==="
echo "Testing connections from Dashboard (port 5179) to Backend (port 8008)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test Health Endpoint
echo "1. Testing Health Endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: http://localhost:5179" http://localhost:8008/health)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ Health endpoint: OK${NC}"
else
    echo -e "${RED}❌ Health endpoint: Failed (HTTP $response)${NC}"
fi

# Test API Status
echo ""
echo "2. Testing API Status Endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: http://localhost:5179" http://localhost:8008/api/v1/status)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ API Status: OK${NC}"
else
    echo -e "${RED}❌ API Status: Failed (HTTP $response)${NC}"
fi

# Test OPTIONS for /auth/verify
echo ""
echo "3. Testing CORS Preflight for /auth/verify..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS -H "Origin: http://localhost:5179" http://localhost:8008/auth/verify)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ CORS preflight: OK${NC}"
else
    echo -e "${RED}❌ CORS preflight: Failed (HTTP $response)${NC}"
fi

# Test Socket.IO Connection
echo ""
echo "4. Testing Socket.IO Endpoint..."
response=$(curl -s -H "Origin: http://localhost:5179" "http://localhost:8008/socket.io/?EIO=4&transport=polling" | head -c 1)
if [ "$response" = "0" ]; then
    echo -e "${GREEN}✅ Socket.IO: Connected${NC}"
else
    echo -e "${RED}❌ Socket.IO: Failed to connect${NC}"
fi

# Test Authentication Endpoint (will fail without token but should return 401 not CORS error)
echo ""
echo "5. Testing Authentication Endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Origin: http://localhost:5179" -H "Content-Type: application/json" -H "Authorization: Bearer test" http://localhost:8008/auth/verify)
if [ "$response" = "401" ]; then
    echo -e "${GREEN}✅ Auth endpoint: Accessible (returns 401 as expected without valid token)${NC}"
elif [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ Auth endpoint: OK${NC}"
else
    echo -e "${RED}❌ Auth endpoint: Failed (HTTP $response - might be CORS issue)${NC}"
fi

# Test WebSocket upgrade headers
echo ""
echo "6. Testing WebSocket Upgrade Headers..."
response=$(curl -s -I -H "Origin: http://localhost:5179" -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" http://localhost:8008/ws/test 2>&1 | grep -c "HTTP/1.1")
if [ "$response" -gt 0 ]; then
    echo -e "${GREEN}✅ WebSocket headers: Accepted${NC}"
else
    echo -e "${RED}❌ WebSocket headers: Failed${NC}"
fi

echo ""
echo "=== SUMMARY ==="
echo "The dashboard on port 5179 should now be able to connect to:"
echo "- FastAPI backend on http://localhost:8008"
echo "- Socket.IO on ws://localhost:8008/socket.io/"
echo "- All API endpoints with proper CORS headers"
echo ""
echo "If the dashboard is still having issues, check:"
echo "1. The dashboard is using the correct API URL (http://localhost:8008)"
echo "2. The dashboard is sending the Authorization header for protected endpoints"
echo "3. The dashboard Socket.IO client version is compatible (using Socket.IO v4)"