#!/bin/bash
# ============================================
# ToolboxAI System Health Verification Script
# ============================================
# Comprehensive health check for backend and frontend
# Usage: ./verify-system-health.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          ToolboxAI System Health Verification             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if process is running
check_process() {
    local process_name=$1
    local port=$2

    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $process_name${NC} running on port ${BLUE}$port${NC}"
        return 0
    else
        echo -e "${RED}❌ $process_name${NC} NOT running on port $port"
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local name=$1
    local url=$2

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo -e "${GREEN}✅ $name${NC} responding at ${BLUE}$url${NC}"
        return 0
    else
        echo -e "${RED}❌ $name${NC} NOT responding at $url"
        return 1
    fi
}

# Check Backend
echo -e "${YELLOW}🔍 Checking Backend...${NC}"
check_process "Backend (uvicorn)" 8009
check_http "Backend API" "http://127.0.0.1:8009/health"

# Get detailed backend health
echo ""
echo -e "${YELLOW}📊 Backend Health Details:${NC}"
curl -s http://127.0.0.1:8009/health | python3 -m json.tool || echo "Could not parse health response"

echo ""
echo -e "${YELLOW}🔍 Checking Dashboard...${NC}"
check_process "Dashboard (Vite)" 5179
check_http "Dashboard" "http://localhost:5179"

# Check for common issues
echo ""
echo -e "${YELLOW}🔍 Checking for Common Issues...${NC}"

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis${NC} responding"
else
    echo -e "${YELLOW}⚠️  Redis${NC} not responding (optional service)"
fi

# Check PostgreSQL
if pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL${NC} ready"
else
    echo -e "${YELLOW}⚠️  PostgreSQL${NC} not ready (optional for local dev)"
fi

# Check for known error patterns in backend logs
echo ""
echo -e "${YELLOW}🔍 Checking Backend Logs (last 20 lines)...${NC}"
if [ -f backend.log ]; then
    echo -e "${BLUE}Recent log entries:${NC}"
    tail -20 backend.log | grep -E "(ERROR|WARNING|✅)" || echo "No errors or warnings found"
else
    echo -e "${YELLOW}⚠️  backend.log not found${NC}"
fi

# System Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    System Summary                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Count issues
issues=0
check_process "Backend" 8009 > /dev/null 2>&1 || ((issues++))
check_process "Dashboard" 5179 > /dev/null 2>&1 || ((issues++))

if [ $issues -eq 0 ]; then
    echo -e "${GREEN}✅ All critical services operational!${NC}"
    echo ""
    echo -e "${GREEN}🚀 Access Points:${NC}"
    echo -e "   • Dashboard: ${BLUE}http://localhost:5179${NC}"
    echo -e "   • Backend API: ${BLUE}http://127.0.0.1:8009${NC}"
    echo -e "   • API Docs: ${BLUE}http://127.0.0.1:8009/docs${NC}"
    echo ""
    echo -e "${YELLOW}📝 Notes:${NC}"
    echo -e "   • Browser extension errors are normal (harmless)"
    echo -e "   • SVG calc() warnings are cosmetic (Mantine UI)"
    echo -e "   • Pusher and Agents disabled (optional services)"
else
    echo -e "${RED}⚠️  $issues critical service(s) not running${NC}"
    echo ""
    echo -e "${YELLOW}💡 To start services:${NC}"
    echo -e "   • Backend: ${BLUE}cd /Volumes/G-DRIVE\\ ArmorATD/Development/Clients/ToolBoxAI-Solutions && source venv/bin/activate && uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload${NC}"
    echo -e "   • Dashboard: ${BLUE}cd apps/dashboard && npm run dev${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
