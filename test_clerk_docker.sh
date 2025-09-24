#!/bin/bash

# Test Clerk Authentication in Docker Environment
echo "=== Testing Clerk Authentication in Docker ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if containers are running
echo "1. Checking Docker containers..."
if docker ps | grep -q toolboxai-dashboard-frontend; then
    echo -e "${GREEN}✓ Dashboard container is running${NC}"
else
    echo -e "${RED}✗ Dashboard container is not running${NC}"
    exit 1
fi

if docker ps | grep -q toolboxai-fastapi; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
else
    echo -e "${RED}✗ Backend container is not running${NC}"
    exit 1
fi

echo ""
echo "2. Checking Clerk dependencies in container..."
if docker exec toolboxai-dashboard-frontend ls /app/node_modules/@clerk/clerk-react >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Clerk React SDK is installed${NC}"
else
    echo -e "${RED}✗ Clerk React SDK is not installed${NC}"
    echo "  Installing Clerk..."
    docker exec toolboxai-dashboard-frontend npm install @clerk/clerk-react --legacy-peer-deps
fi

echo ""
echo "3. Checking environment variables..."
CLERK_KEY=$(docker exec toolboxai-dashboard-frontend printenv VITE_CLERK_PUBLISHABLE_KEY)
if [ -n "$CLERK_KEY" ]; then
    echo -e "${GREEN}✓ Clerk publishable key is set${NC}"
else
    echo -e "${YELLOW}⚠ Clerk publishable key is not set${NC}"
fi

echo ""
echo "4. Checking dashboard accessibility..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5179/)
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Dashboard is accessible (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}✗ Dashboard returned HTTP $HTTP_STATUS${NC}"
fi

echo ""
echo "5. Checking backend API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8009/health)
if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Backend API is healthy (HTTP $API_STATUS)${NC}"
else
    echo -e "${RED}✗ Backend API returned HTTP $API_STATUS${NC}"
fi

echo ""
echo "6. Checking Clerk webhook endpoint..."
WEBHOOK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8009/api/webhooks/clerk \
    -H "Content-Type: application/json" \
    -H "svix-signature: sha256=invalid" \
    -d '{"type":"test","data":{}}')
if [ "$WEBHOOK_STATUS" = "401" ]; then
    echo -e "${GREEN}✓ Clerk webhook endpoint is protected (HTTP 401 for invalid signature)${NC}"
elif [ "$WEBHOOK_STATUS" = "404" ]; then
    echo -e "${RED}✗ Clerk webhook endpoint not found (HTTP 404)${NC}"
else
    echo -e "${YELLOW}⚠ Clerk webhook returned HTTP $WEBHOOK_STATUS${NC}"
fi

echo ""
echo "7. Checking for errors in container logs..."
ERROR_COUNT=$(docker logs toolboxai-dashboard-frontend 2>&1 | grep -c "ERROR" | tail -1)
if [ "$ERROR_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✓ No errors in dashboard logs${NC}"
else
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT errors in dashboard logs${NC}"
    echo "  Recent errors:"
    docker logs toolboxai-dashboard-frontend 2>&1 | grep "ERROR" | tail -3
fi

echo ""
echo "=== Test Summary ==="
echo ""
echo "Dashboard URL: http://localhost:5179"
echo "Sign-in URL: http://localhost:5179/sign-in"
echo "Backend API: http://localhost:8009"
echo ""
echo "To view live logs:"
echo "  docker logs -f toolboxai-dashboard-frontend"
echo "  docker logs -f toolboxai-fastapi"
echo ""
echo -e "${GREEN}Clerk authentication is configured and ready for testing!${NC}"