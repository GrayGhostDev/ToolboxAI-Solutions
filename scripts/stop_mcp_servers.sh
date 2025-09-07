#!/bin/bash

# ToolboxAI MCP Servers and Agents Stop Script
# This script stops all running MCP servers and agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
PIDS_DIR="$PROJECT_ROOT/scripts/pids"

echo -e "${BLUE}🛑 Stopping ToolboxAI MCP Servers and Agents${NC}"
echo "=================================================="

# Function to stop a service
stop_service() {
    local service_name="$1"
    local pid_file="$PIDS_DIR/$service_name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}🔄 Stopping $service_name (PID: $pid)...${NC}"
            kill $pid
            sleep 1
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force stopping $service_name...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Stop all services
stop_service "MCP-Server"
stop_service "Agent-Orchestrator"
stop_service "Content-Agent"
stop_service "Quiz-Agent"
stop_service "Terrain-Agent"
stop_service "Script-Agent"
stop_service "Review-Agent"
stop_service "SPARC-Manager"
stop_service "Swarm-Controller"
stop_service "Main-Coordinator"
stop_service "FastAPI-Server"
stop_service "Flask-Bridge"

# Clean up any remaining Python processes related to our services
echo -e "${YELLOW}🧹 Cleaning up any remaining processes...${NC}"
pkill -f "mcp/server.py" 2>/dev/null || true
pkill -f "agents/orchestrator.py" 2>/dev/null || true
pkill -f "agents/content_agent.py" 2>/dev/null || true
pkill -f "agents/quiz_agent.py" 2>/dev/null || true
pkill -f "agents/terrain_agent.py" 2>/dev/null || true
pkill -f "agents/script_agent.py" 2>/dev/null || true
pkill -f "agents/review_agent.py" 2>/dev/null || true
pkill -f "sparc/state_manager.py" 2>/dev/null || true
pkill -f "swarm/swarm_controller.py" 2>/dev/null || true
pkill -f "coordinators/main_coordinator.py" 2>/dev/null || true
pkill -f "server/main.py" 2>/dev/null || true
pkill -f "server/roblox_server.py" 2>/dev/null || true

echo ""
echo -e "${GREEN}🎉 All MCP servers and agents stopped successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo "=================="
echo "All services: STOPPED"
echo ""
echo -e "${YELLOW}💡 To restart services, run: $PROJECT_ROOT/scripts/start_mcp_servers.sh${NC}"
