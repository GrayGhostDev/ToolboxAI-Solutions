#!/bin/bash

# ToolboxAI MCP Servers and Agents Startup Script
# This script starts all MCP servers and agents for Cursor integration

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
ROBLOX_ENV="$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
VENV_PATH="$ROBLOX_ENV/venv_clean"

echo -e "${BLUE}🚀 Starting ToolboxAI MCP Servers and Agents${NC}"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
    echo "Please run the setup script first."
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Set environment variables
export PYTHONPATH="$ROBLOX_ENV:$PROJECT_ROOT/src/shared"
export MCP_HOST="localhost"
export MCP_PORT="9876"
export MCP_MAX_CONTEXT_TOKENS="128000"

# Check for required API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set. Some agents may not work properly.${NC}"
fi

# Function to start a service in background
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="$3"
    
    echo -e "${YELLOW}🔄 Starting $service_name...${NC}"
    
    # Start service in background
    nohup bash -c "$command" > "$log_file" 2>&1 &
    local pid=$!
    
    # Wait a moment and check if process is still running
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
        echo "$pid" > "$PROJECT_ROOT/scripts/pids/$service_name.pid"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        return 1
    fi
}

# Create pids directory
mkdir -p "$PROJECT_ROOT/scripts/pids"

# Start MCP Server
start_service "MCP-Server" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/mcp/server.py\"" \
    "$PROJECT_ROOT/logs/mcp_server.log"

# Start Agent Orchestrator
start_service "Agent-Orchestrator" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/agents/orchestrator.py\"" \
    "$PROJECT_ROOT/logs/agent_orchestrator.log"

# Start Content Agent
start_service "Content-Agent" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/agents/content_agent.py\"" \
    "$PROJECT_ROOT/logs/content_agent.log"

# Start Quiz Agent
start_service "Quiz-Agent" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/agents/quiz_agent.py\"" \
    "$PROJECT_ROOT/logs/quiz_agent.log"

# Start Terrain Agent
start_service "Terrain-Agent" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/agents/terrain_agent.py\"" \
    "$PROJECT_ROOT/logs/terrain_agent.log"

# Start Script Agent
start_service "Script-Agent" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/agents/script_agent.py\"" \
    "$PROJECT_ROOT/logs/script_agent.log"

# Start Review Agent
start_service "Review-Agent" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/agents/review_agent.py\"" \
    "$PROJECT_ROOT/logs/review_agent.log"

# Start SPARC Manager
start_service "SPARC-Manager" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/sparc/state_manager.py\"" \
    "$PROJECT_ROOT/logs/sparc_manager.log"

# Start Swarm Controller
start_service "Swarm-Controller" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/swarm/swarm_controller.py\"" \
    "$PROJECT_ROOT/logs/swarm_controller.log"

# Start Main Coordinator
start_service "Main-Coordinator" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/coordinators/main_coordinator.py\"" \
    "$PROJECT_ROOT/logs/main_coordinator.log"

# Start FastAPI Server
start_service "FastAPI-Server" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/server/main.py\"" \
    "$PROJECT_ROOT/logs/fastapi_server.log"

# Start Flask Bridge Server
start_service "Flask-Bridge" \
    "source \"$VENV_PATH/bin/activate\" && python \"$ROBLOX_ENV/server/roblox_server.py\"" \
    "$PROJECT_ROOT/logs/flask_bridge.log"

echo ""
echo -e "${GREEN}🎉 All MCP servers and agents started successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo "=================="
echo "MCP Server: ws://localhost:9876"
echo "FastAPI Server: http://127.0.0.1:8008"
echo "Flask Bridge: http://127.0.0.1:5001"
echo "API Documentation: http://127.0.0.1:8008/docs"
echo ""
echo -e "${YELLOW}📝 Logs are available in: $PROJECT_ROOT/logs/${NC}"
echo -e "${YELLOW}🛑 To stop all services, run: $PROJECT_ROOT/scripts/stop_mcp_servers.sh${NC}"
echo ""
echo -e "${GREEN}✨ Cursor MCP integration is now ready!${NC}"
