#!/bin/bash

# Start ToolboxAI Docker Services
set -e

COMPOSE_FILE="docker-compose.dev.yml"
PROJECT_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
DOCKER_DIR="$PROJECT_DIR/infrastructure/docker"

echo "🚀 Starting ToolboxAI Docker Services..."
cd "$DOCKER_DIR"

# Function to check service health
check_health() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $service to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if docker compose -f $COMPOSE_FILE ps | grep $service | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "❌ $service failed to become healthy"
    return 1
}

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker compose -f $COMPOSE_FILE down 2>/dev/null || true

# Start databases first
echo "📦 Starting database services..."
docker compose -f $COMPOSE_FILE up -d postgres redis 2>&1 | grep -v "variable is not set" || true

# Wait for databases to be healthy
check_health "postgres"
check_health "redis"

# Build and start backend services
echo "🔨 Building backend services..."
docker compose -f $COMPOSE_FILE build fastapi-main 2>&1 | grep -v "variable is not set" || true

echo "🚀 Starting FastAPI backend..."
docker compose -f $COMPOSE_FILE up -d fastapi-main 2>&1 | grep -v "variable is not set" || true

# Build and start MCP server
echo "🤖 Building MCP server..."
docker compose -f $COMPOSE_FILE build mcp-server 2>&1 | grep -v "variable is not set" || true

echo "🚀 Starting MCP server..."
docker compose -f $COMPOSE_FILE up -d mcp-server 2>&1 | grep -v "variable is not set" || true

# Build and start agent coordinator
echo "🎯 Building Agent Coordinator..."
docker compose -f $COMPOSE_FILE build agent-coordinator 2>&1 | grep -v "variable is not set" || true

echo "🚀 Starting Agent Coordinator..."
docker compose -f $COMPOSE_FILE up -d agent-coordinator 2>&1 | grep -v "variable is not set" || true

# Start agent pools
echo "👥 Starting Agent Pools..."
docker compose -f $COMPOSE_FILE up -d educational-agents 2>&1 | grep -v "variable is not set" || true

# Start other services
echo "🌐 Starting Flask Bridge..."
docker compose -f $COMPOSE_FILE up -d flask-bridge 2>&1 | grep -v "variable is not set" || true

echo "🎨 Starting Dashboard Backend..."
docker compose -f $COMPOSE_FILE up -d dashboard-backend 2>&1 | grep -v "variable is not set" || true

echo "🖥️ Starting Dashboard Frontend..."
docker compose -f $COMPOSE_FILE up -d dashboard-frontend 2>&1 | grep -v "variable is not set" || true

echo "👻 Starting Ghost CMS..."
docker compose -f $COMPOSE_FILE up -d ghost-backend 2>&1 | grep -v "variable is not set" || true

# Show final status
echo ""
echo "📊 Service Status:"
docker compose -f $COMPOSE_FILE ps

echo ""
echo "🔍 Service URLs:"
echo "  - PostgreSQL: localhost:5434"
echo "  - Redis: localhost:6381"
echo "  - FastAPI Backend: http://localhost:8008"
echo "  - MCP Server: ws://localhost:9877"
echo "  - Agent Coordinator: http://localhost:8888"
echo "  - Flask Bridge: http://localhost:5001"
echo "  - Dashboard Backend: http://localhost:8001"
echo "  - Dashboard Frontend: http://localhost:5176"
echo "  - Ghost CMS: http://localhost:8000"

echo ""
echo "📝 View logs: docker compose -f $COMPOSE_FILE logs -f [service-name]"
echo "🛑 Stop all: docker compose -f $COMPOSE_FILE down"