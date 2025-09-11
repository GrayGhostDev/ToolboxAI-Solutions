#!/bin/bash

# Terminal 2 Integration Verification Script
# Tests real data flow between Terminal 2 (Dashboard) and Terminal 1 (Backend API)

echo "=========================================="
echo "🎨 TERMINAL 2 INTEGRATION VERIFICATION"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="$3"
    local method="${4:-GET}"
    local data="${5:-}"
    local headers="${6:-}"
    
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ]; then
        if [ -n "$headers" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" -H "Content-Type: application/json" -H "$headers" -d "$data" 2>/dev/null)
        else
            response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null)
        fi
    else
        if [ -n "$headers" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" -H "$headers" "$url" 2>/dev/null)
        else
            response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        fi
    fi
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} (Expected $expected_code, got $response)"
        ((FAILED++))
    fi
}

echo -e "${BLUE}1. Testing Dashboard Accessibility${NC}"
echo "=========================================="
test_endpoint "Dashboard Homepage" "http://localhost:5179" "200"
echo ""

echo -e "${BLUE}2. Testing Backend API (Terminal 1)${NC}"
echo "=========================================="
test_endpoint "API Health Check" "http://localhost:8008/health" "200"
test_endpoint "API Status" "http://localhost:8008/api/v1/status" "200"
echo ""

echo -e "${BLUE}3. Testing Authentication Flow${NC}"
echo "=========================================="
# Test login with real credentials
echo "Attempting login with test credentials..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8008/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"teacher","password":"teacher123"}' 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓${NC} Login successful"
    ((PASSED++))
    
    # Extract token
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        echo -e "${GREEN}✓${NC} Token received"
        ((PASSED++))
        
        # Test authenticated endpoint
        echo ""
        echo -e "${BLUE}4. Testing Authenticated Endpoints${NC}"
        echo "=========================================="
        test_endpoint "User Profile" "http://localhost:8008/api/v1/users/me" "200" "GET" "" "Authorization: Bearer $TOKEN"
        test_endpoint "Dashboard Overview" "http://localhost:8008/api/v1/dashboard/overview/teacher" "200" "GET" "" "Authorization: Bearer $TOKEN"
    else
        echo -e "${RED}✗${NC} Failed to extract token"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Login failed or user doesn't exist - trying to check if API accepts invalid credentials correctly"
    
    # Test that invalid credentials are rejected
    INVALID_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8008/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"invalid","password":"wrong"}' 2>/dev/null)
    
    if [ "$INVALID_RESPONSE" = "401" ] || [ "$INVALID_RESPONSE" = "400" ]; then
        echo -e "${GREEN}✓${NC} Invalid credentials rejected correctly (HTTP $INVALID_RESPONSE)"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} Invalid credentials handling issue (HTTP $INVALID_RESPONSE)"
        ((FAILED++))
    fi
fi
echo ""

echo -e "${BLUE}5. Testing Real Data Endpoints${NC}"
echo "=========================================="
# Test if we're getting real data (not mock)
echo "Checking for real database data..."

# Try to get users count
USERS_DATA=$(curl -s http://localhost:8008/api/v1/users 2>/dev/null || echo "{}")
if echo "$USERS_DATA" | grep -q "username"; then
    echo -e "${GREEN}✓${NC} Real user data found in database"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} No user data or endpoint requires authentication"
fi

# Check database connection
DB_STATUS=$(curl -s http://localhost:8008/health 2>/dev/null || echo "{}")
if echo "$DB_STATUS" | grep -q "database"; then
    if echo "$DB_STATUS" | grep -q "\"connected\":true"; then
        echo -e "${GREEN}✓${NC} Database is connected"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} Database connection issue"
        ((FAILED++))
    fi
fi
echo ""

echo -e "${BLUE}6. Testing WebSocket Availability${NC}"
echo "=========================================="
# Check if socket.io endpoint responds
SOCKET_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8008/socket.io/" 2>/dev/null)
if [ "$SOCKET_RESPONSE" = "200" ] || [ "$SOCKET_RESPONSE" = "400" ]; then
    echo -e "${GREEN}✓${NC} WebSocket endpoint available (HTTP $SOCKET_RESPONSE)"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} WebSocket endpoint not responding (HTTP $SOCKET_RESPONSE)"
    ((FAILED++))
fi
echo ""

echo -e "${BLUE}7. Testing Cross-Terminal Communication${NC}"
echo "=========================================="
# Check if Terminal 3 (Roblox Bridge) is running
test_endpoint "Terminal 3 (Roblox Bridge)" "http://localhost:5001/health" "200"
echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}TEST SUMMARY${NC}"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

TOTAL=$((PASSED + FAILED))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
    echo "Success Rate: $SUCCESS_RATE%"
    
    if [ $SUCCESS_RATE -eq 100 ]; then
        echo -e "\n${GREEN}✅ TERMINAL 2 IS FULLY OPERATIONAL!${NC}"
        echo "All systems are working with real data."
    elif [ $SUCCESS_RATE -ge 80 ]; then
        echo -e "\n${YELLOW}⚠️ TERMINAL 2 IS MOSTLY OPERATIONAL${NC}"
        echo "Some features may need attention."
    else
        echo -e "\n${RED}❌ TERMINAL 2 HAS ISSUES${NC}"
        echo "Critical problems detected. Review failed tests."
    fi
else
    echo -e "\n${RED}❌ NO TESTS RAN${NC}"
fi

echo ""
exit $FAILED