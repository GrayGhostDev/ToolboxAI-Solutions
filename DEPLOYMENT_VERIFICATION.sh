#!/bin/bash
# ============================================
# Deployment Verification Script
# ============================================
# Tests production backend and frontend after deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Deployment Verification Script                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get URLs from user
read -p "Enter your Render backend URL (e.g., https://your-app.onrender.com): " BACKEND_URL
read -p "Enter your Vercel frontend URL (e.g., https://your-app.vercel.app): " FRONTEND_URL

echo ""
echo -e "${YELLOW}🔍 Testing Backend Deployment...${NC}"
echo ""

# Test backend health
echo -e "${BLUE}1. Testing /health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/health")
echo "$HEALTH_RESPONSE" | python3 -m json.tool

# Check Pusher status in health
PUSHER_STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['checks']['pusher'])")
if [ "$PUSHER_STATUS" = "True" ]; then
    echo -e "${GREEN}✅ Pusher is ENABLED${NC}"
else
    echo -e "${RED}❌ Pusher is NOT ENABLED${NC}"
    echo -e "${YELLOW}💡 Check environment variables in Render dashboard${NC}"
fi

echo ""
echo -e "${BLUE}2. Testing /pusher/status endpoint...${NC}"
curl -s "${BACKEND_URL}/pusher/status" | python3 -m json.tool

echo ""
echo -e "${YELLOW}🔍 Testing Frontend Deployment...${NC}"
echo ""

# Test frontend
echo -e "${BLUE}3. Testing dashboard HTTP response...${NC}"
FRONTEND_STATUS=$(curl -I -s "${FRONTEND_URL}" | head -1)
echo "$FRONTEND_STATUS"

if echo "$FRONTEND_STATUS" | grep -q "200"; then
    echo -e "${GREEN}✅ Dashboard is accessible${NC}"
else
    echo -e "${RED}❌ Dashboard returned non-200 status${NC}"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   Deployment Summary                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Summary
echo -e "${BLUE}Backend URL:${NC} $BACKEND_URL"
echo -e "${BLUE}Frontend URL:${NC} $FRONTEND_URL"
echo ""

if [ "$PUSHER_STATUS" = "True" ]; then
    echo -e "${GREEN}🎉 Deployment Successful!${NC}"
    echo ""
    echo -e "${GREEN}✅ Backend is healthy${NC}"
    echo -e "${GREEN}✅ Pusher is enabled${NC}"
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo -e "   1. Test login flow on $FRONTEND_URL"
    echo -e "   2. Check Pusher dashboard for connections"
    echo -e "   3. Monitor logs for any errors"
    echo -e "   4. Review Dependabot security alerts"
else
    echo -e "${YELLOW}⚠️  Deployment Needs Attention${NC}"
    echo ""
    echo -e "${YELLOW}Issues Found:${NC}"
    echo -e "   - Pusher not enabled in health check"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo -e "   1. Check Render environment variables"
    echo -e "   2. Verify PUSHER_ENABLED=true (not 'True')"
    echo -e "   3. Check build logs for pusher package installation"
    echo -e "   4. Review deployment logs for errors"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
