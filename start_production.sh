#!/bin/bash

# ============================================
# ToolBoxAI Production Startup Script
# ============================================
# This script initializes all production services
# Backend runs on port 8009 (verified)
# Uses venv Python environment

set -e

echo "🚀 Starting ToolBoxAI Production Environment"
echo "============================================"

# Set working directory
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Load production environment
if [ -f .env.production ]; then
    echo "✅ Loading production environment variables"
    set -a
    source .env.production
    set +a
else
    echo "⚠️ Warning: .env.production not found, using defaults"
fi

# Verify Docker services
echo ""
echo "📦 Checking Docker services..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep toolboxai || echo "⚠️ Some Docker services may not be running"

# Check backend health (port 8009)
echo ""
echo "🔍 Checking backend API health (port 8009)..."
if curl -s http://localhost:8009/health | grep -q "healthy"; then
    echo "✅ Backend API is healthy on port 8009"
else
    echo "⚠️ Backend API may not be fully operational"
fi

# Activate Python environment
echo ""
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate
echo "✅ Using Python: $(which python)"
echo "   Python version: $(python --version)"

# Initialize MCP servers (if not in Docker)
echo ""
echo "🔌 Initializing MCP servers..."

# Start MCP orchestrator in background
if ! pgrep -f "core/mcp/server.py" > /dev/null; then
    echo "Starting MCP orchestrator on port 9877..."
    nohup python core/mcp/server.py \
        --port 9877 \
        --backend-port 8009 \
        > logs/mcp_orchestrator.log 2>&1 &
    echo "✅ MCP orchestrator started (PID: $!)"
else
    echo "✅ MCP orchestrator already running"
fi

# Initialize agent registry
echo ""
echo "🤖 Initializing Agent System..."
if ! pgrep -f "agent_registry.py" > /dev/null; then
    echo "Starting agent registry..."
    nohup python core/agents/agent_registry.py \
        --backend-url http://localhost:8009 \
        > logs/agent_registry.log 2>&1 &
    echo "✅ Agent registry started (PID: $!)"
else
    echo "✅ Agent registry already running"
fi

# Start monitoring (optional)
echo ""
echo "📊 Monitoring setup..."
if command -v prometheus &> /dev/null; then
    echo "✅ Prometheus available"
else
    echo "ℹ️ Prometheus not installed (optional)"
fi

# Check Redis
echo ""
echo "🔴 Checking Redis..."
if redis-cli -h localhost -p 6381 ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis is operational on port 6381"
else
    echo "⚠️ Redis may not be accessible on port 6381"
fi

# Check PostgreSQL
echo ""
echo "🐘 Checking PostgreSQL..."
if PGPASSWORD=eduplatform2024 psql -h localhost -p 5434 -U eduplatform -d educational_platform_dev -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is operational on port 5434"
else
    echo "⚠️ PostgreSQL may not be accessible on port 5434"
fi

# Display service URLs
echo ""
echo "============================================"
echo "🎯 Service URLs:"
echo "============================================"
echo "📱 Dashboard:        http://localhost:5179"
echo "🔧 Backend API:      http://localhost:8009"
echo "📚 API Docs:         http://localhost:8009/docs"
echo "🔌 MCP Orchestrator: ws://localhost:9877"
echo "🔴 Redis:            localhost:6381"
echo "🐘 PostgreSQL:       localhost:5434"
echo "============================================"

# Display logs location
echo ""
echo "📝 Logs location:"
echo "   MCP: logs/mcp_orchestrator.log"
echo "   Agents: logs/agent_registry.log"
echo "   Backend: Docker logs toolboxai-fastapi"

# Health check summary
echo ""
echo "============================================"
echo "🏥 Health Check Summary:"
echo "============================================"

# Function to check service
check_service() {
    local name=$1
    local check_cmd=$2

    if eval "$check_cmd" > /dev/null 2>&1; then
        echo "✅ $name"
    else
        echo "❌ $name"
    fi
}

check_service "Backend API (8009)" "curl -s http://localhost:8009/health | grep -q healthy"
check_service "Dashboard (5179)" "curl -s http://localhost:5179 | grep -q '<title>'"
check_service "PostgreSQL (5434)" "PGPASSWORD=eduplatform2024 psql -h localhost -p 5434 -U eduplatform -d educational_platform_dev -c 'SELECT 1'"
check_service "Redis (6381)" "redis-cli -h localhost -p 6381 ping"
check_service "MCP Server" "pgrep -f 'core/mcp/server.py'"
check_service "Agent Registry" "pgrep -f 'agent_registry.py'"

echo "============================================"
echo ""
echo "✨ ToolBoxAI Production Environment Ready!"
echo "   Backend running on port 8009"
echo "   Using venv Python environment"
echo ""
echo "To stop services:"
echo "   docker-compose down"
echo "   pkill -f 'core/mcp/server.py'"
echo "   pkill -f 'agent_registry.py'"
echo "============================================"