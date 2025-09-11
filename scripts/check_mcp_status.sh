#!/usr/bin/env sh
# shellcheck shell=sh
set -eu
# shellcheck source=common/lib.sh
. "$(cd "$(dirname "$0")" && pwd -P)/common/lib.sh" 2>/dev/null || true

# ToolboxAI MCP Servers and Agents Status Check Script
# This script checks the status of all MCP servers and agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory (computed dynamically; override with PROJECT_ROOT env var)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PIDS_DIR="$PROJECT_ROOT/scripts/pids"

echo -e "${BLUE}📊 ToolboxAI MCP Servers and Agents Status${NC}"
echo "=============================================="

# Function to check service status
check_service() {
    local service_name="$1"
    local port="$2"
    local pid_file="$PIDS_DIR/$service_name.pid"
    
    echo -n "🔍 $service_name: "
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${GREEN}✅ RUNNING (PID: $pid)${NC}"
            
            # Check if port is listening (if specified)
            if [ ! -z "$port" ]; then
                if lsof -i :$port >/dev/null 2>&1; then
                    echo -e "   📡 Port $port: ${GREEN}LISTENING${NC}"
                else
                    echo -e "   📡 Port $port: ${RED}NOT LISTENING${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ STOPPED (stale PID file)${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  NOT STARTED${NC}"
    fi
}

# Check all services
echo -e "${BLUE}🤖 Agent Services:${NC}"
check_service "MCP-Server" "$MCP_PORT"
check_service "Agent-Orchestrator" ""
check_service "Content-Agent" ""
check_service "Quiz-Agent" ""
check_service "Terrain-Agent" ""
check_service "Script-Agent" ""
check_service "Review-Agent" ""

echo ""
echo -e "${BLUE}🏗️  Framework Services:${NC}"
check_service "SPARC-Manager" ""
check_service "Swarm-Controller" ""
check_service "Main-Coordinator" ""

echo ""
echo -e "${BLUE}🌐 Server Services:${NC}"
check_service "FastAPI-Server" "8008"
check_service "Flask-Bridge" "5001"

echo ""
echo -e "${BLUE}🔗 Connection Tests:${NC}"

# Test MCP Server WebSocket connection
echo -n "🔌 MCP WebSocket (ws://$API_HOST:$MCP_PORT): "
if curl -s --connect-timeout 2 "http://$API_HOST:$MCP_PORT" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ CONNECTED${NC}"
else
    echo -e "${RED}❌ NOT CONNECTED${NC}"
fi

# Test FastAPI Server
echo -n "🌐 FastAPI Server (http://$API_HOST:$FASTAPI_PORT/health): "
if curl -s --connect-timeout 2 "http://$API_HOST:$FASTAPI_PORT/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

# Test Flask Bridge Server
echo -n "🌉 Flask Bridge (http://$API_HOST:$FLASK_PORT/status): "
if curl -s --connect-timeout 2 "http://$API_HOST:$FLASK_PORT/status" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo ""
echo -e "${BLUE}📝 Recent Logs:${NC}"
echo "==============="

# Show recent log entries
if [ -d "$PROJECT_ROOT/logs" ]; then
    echo -e "${YELLOW}📄 Last 5 log entries from each service:${NC}"
    for log_file in "$PROJECT_ROOT/logs"/*.log; do
        if [ -f "$log_file" ]; then
            service_name=$(basename "$log_file" .log)
            echo -e "${BLUE}📋 $service_name:${NC}"
            tail -5 "$log_file" 2>/dev/null | sed 's/^/   /' || echo "   No recent logs"
            echo ""
        fi
    done
else
    echo -e "${YELLOW}⚠️  No logs directory found${NC}"
fi

echo ""
echo -e "${BLUE}🛠️  Management Commands:${NC}"
echo "========================"
echo "Start all services: $PROJECT_ROOT/scripts/start_mcp_servers.sh"
echo "Stop all services:  $PROJECT_ROOT/scripts/stop_mcp_servers.sh"
echo "Check status:       $PROJECT_ROOT/scripts/check_mcp_status.sh"
echo ""
echo -e "${GREEN}✨ Status check complete!${NC}"
