#!/bin/bash
#
# Render Backend Deployment Verification Script
# Verifies deployment status, health, and API accessibility
#
# Usage: ./verify_backend_deployment.sh [RENDER_API_KEY]
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
RENDER_SERVICE_ID="srv-d479pmali9vc738itjng"
BACKEND_URL="https://toolboxai-backend.onrender.com"
RENDER_API_URL="https://api.render.com/v1/services/${RENDER_SERVICE_ID}"

# Get API key from argument or environment
RENDER_API_KEY="${1:-$RENDER_API_KEY}"

if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${RED}✗${NC} RENDER_API_KEY not provided"
    echo "Usage: $0 [RENDER_API_KEY]"
    echo "Or set RENDER_API_KEY environment variable"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Render Backend Deployment Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# ============================================
# Check 1: Render Service Status
# ============================================
echo -e "${CYAN}ℹ${NC} Step 1: Checking Render service status..."
echo

response=$(curl -s -w "\n%{http_code}" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${RENDER_API_KEY}" \
    "${RENDER_API_URL}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC} Render API accessible"

    # Extract service details
    service_name=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('service', {}).get('name', 'N/A'))" 2>/dev/null || echo "N/A")
    service_status=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('service', {}).get('state', 'N/A'))" 2>/dev/null || echo "N/A")
    service_url=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('service', {}).get('serviceDetails', {}).get('url', 'N/A'))" 2>/dev/null || echo "N/A")

    echo -e "  Service Name: ${CYAN}${service_name}${NC}"
    echo -e "  Service Status: ${CYAN}${service_status}${NC}"
    echo -e "  Service URL: ${CYAN}${service_url}${NC}"
    echo

    if [ "$service_status" != "available" ]; then
        echo -e "${YELLOW}⚠${NC} Service is not in 'available' state"
        echo -e "  Current state: ${service_status}"
        echo
    fi
else
    echo -e "${RED}✗${NC} Failed to fetch Render service status (HTTP ${http_code})"
    echo "$body" | head -20
    echo
fi

# ============================================
# Check 2: Backend Health Endpoint
# ============================================
echo -e "${CYAN}ℹ${NC} Step 2: Checking backend health endpoint..."
echo

health_response=$(curl -s -f -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" 2>&1 || echo "failed")

if [ "$health_response" = "200" ]; then
    echo -e "${GREEN}✓${NC} Backend health check passed"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/health${NC}"
    echo -e "  Status: ${GREEN}OK (HTTP 200)${NC}"
    echo
elif [ "$health_response" = "failed" ]; then
    echo -e "${RED}✗${NC} Backend health endpoint unreachable"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/health${NC}"
    echo -e "  Error: Connection failed"
    echo
else
    echo -e "${YELLOW}⚠${NC} Backend health check returned unexpected status"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/health${NC}"
    echo -e "  Status: ${YELLOW}HTTP ${health_response}${NC}"
    echo
fi

# ============================================
# Check 3: API Root Endpoint
# ============================================
echo -e "${CYAN}ℹ${NC} Step 3: Checking API root endpoint..."
echo

root_response=$(curl -s -f -o /dev/null -w "%{http_code}" "${BACKEND_URL}/" 2>&1 || echo "failed")

if [ "$root_response" = "200" ]; then
    echo -e "${GREEN}✓${NC} API root endpoint accessible"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/${NC}"
    echo -e "  Status: ${GREEN}OK (HTTP 200)${NC}"
    echo
elif [ "$root_response" = "failed" ]; then
    echo -e "${RED}✗${NC} API root endpoint unreachable"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/${NC}"
    echo -e "  Error: Connection failed"
    echo
else
    echo -e "${YELLOW}⚠${NC} API root endpoint returned unexpected status"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/${NC}"
    echo -e "  Status: ${YELLOW}HTTP ${root_response}${NC}"
    echo
fi

# ============================================
# Check 4: API Documentation
# ============================================
echo -e "${CYAN}ℹ${NC} Step 4: Checking API documentation..."
echo

docs_response=$(curl -s -f -o /dev/null -w "%{http_code}" "${BACKEND_URL}/docs" 2>&1 || echo "failed")

if [ "$docs_response" = "200" ]; then
    echo -e "${GREEN}✓${NC} API documentation accessible"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/docs${NC}"
    echo -e "  Status: ${GREEN}OK (HTTP 200)${NC}"
    echo
elif [ "$docs_response" = "failed" ]; then
    echo -e "${YELLOW}⚠${NC} API documentation unreachable"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/docs${NC}"
    echo -e "  Note: This may be expected if docs are disabled in production"
    echo
else
    echo -e "${YELLOW}⚠${NC} API documentation returned unexpected status"
    echo -e "  URL: ${CYAN}${BACKEND_URL}/docs${NC}"
    echo -e "  Status: ${YELLOW}HTTP ${docs_response}${NC}"
    echo
fi

# ============================================
# Summary
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Verification Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Determine overall status
overall_status=0

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC} Render Service Status: OK"
else
    echo -e "${RED}✗${NC} Render Service Status: FAILED"
    overall_status=1
fi

if [ "$health_response" = "200" ]; then
    echo -e "${GREEN}✓${NC} Health Endpoint: OK"
else
    echo -e "${RED}✗${NC} Health Endpoint: FAILED"
    overall_status=1
fi

if [ "$root_response" = "200" ]; then
    echo -e "${GREEN}✓${NC} API Root Endpoint: OK"
else
    echo -e "${RED}✗${NC} API Root Endpoint: FAILED"
    overall_status=1
fi

if [ "$docs_response" = "200" ]; then
    echo -e "${GREEN}✓${NC} API Documentation: OK"
else
    echo -e "${YELLOW}⚠${NC} API Documentation: Not accessible (may be intentional)"
fi

echo
if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}✅ Backend deployment verification PASSED${NC}"
    echo
    exit 0
else
    echo -e "${RED}❌ Backend deployment verification FAILED${NC}"
    echo
    echo -e "${CYAN}ℹ${NC} Troubleshooting:"
    echo "  1. Check Render dashboard: https://dashboard.render.com/"
    echo "  2. Review deployment logs"
    echo "  3. Verify environment variables are set correctly"
    echo "  4. Check for recent code changes that might have broken the deployment"
    echo
    exit 1
fi
