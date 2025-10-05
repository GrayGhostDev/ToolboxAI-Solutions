#!/bin/bash

# ToolBoxAI Complete Application Launcher
# =======================================

set -e

echo "🚀 ToolBoxAI Complete Application Startup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $1 is available${NC}"
        return 0
    fi
}

# Function to stop existing services
stop_existing_services() {
    echo -e "${YELLOW}🛑 Stopping any existing services...${NC}"

    # Stop any existing docker compose services
    docker compose -f docker-compose.complete.yml down 2>/dev/null || true
    docker compose -f infrastructure/docker/compose/docker-compose.yml down 2>/dev/null || true

    # Stop TeamCity agents if running
    docker compose -f TeamCity/docker-compose.agents.yml down 2>/dev/null || true

    echo -e "${GREEN}✅ Existing services stopped${NC}"
}

# Check required ports
echo -e "${BLUE}📋 Checking required ports...${NC}"
PORTS=(5432 6379 8009 5179 8010 8888 9090 3001 8200 80 443)
PORT_NAMES=(
    "PostgreSQL"
    "Redis"
    "Backend API"
    "Dashboard"
    "MCP Server"
    "Coordinator"
    "Prometheus"
    "Grafana"
    "Vault"
    "Nginx HTTP"
    "Nginx HTTPS"
)

all_ports_available=true
for i in "${!PORTS[@]}"; do
    echo -n "  ${PORT_NAMES[$i]} (${PORTS[$i]}): "
    if ! check_port ${PORTS[$i]}; then
        all_ports_available=false
    fi
done

if [ "$all_ports_available" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some ports are in use. Would you like to stop existing services? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        stop_existing_services
    else
        echo -e "${RED}❌ Cannot start application with ports in use. Exiting.${NC}"
        exit 1
    fi
fi

# Create necessary directories
echo ""
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
echo -e "${GREEN}✅ Directories created${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created - Please update with your values${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env.example found. Creating minimal .env${NC}"
        cat > .env << EOL
# Database
POSTGRES_USER=eduplatform
POSTGRES_PASSWORD=eduplatform2024
POSTGRES_DB=educational_platform_dev

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# Pusher (Optional - for realtime)
PUSHER_APP_ID=
PUSHER_KEY=
PUSHER_SECRET=
PUSHER_CLUSTER=mt1

# OpenAI (Optional - for AI features)
OPENAI_API_KEY=

# Sentry (Optional - for error tracking)
SENTRY_DSN=
EOL
        echo -e "${GREEN}✅ Basic .env file created${NC}"
    fi
fi

# Build and start services
echo ""
echo -e "${BLUE}🔨 Building Docker images...${NC}"
docker compose -f docker-compose.complete.yml build

echo ""
echo -e "${BLUE}🚀 Starting all services...${NC}"
docker compose -f docker-compose.complete.yml up -d

# Wait for services to be healthy
echo ""
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f $url > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo -e "${RED}❌ $service failed to start${NC}"
    return 1
}

# Check each service
echo -n "  PostgreSQL"
sleep 5
docker exec toolboxai-postgres pg_isready -U eduplatform > /dev/null 2>&1 && echo -e " ${GREEN}✅${NC}" || echo -e " ${RED}❌${NC}"

echo -n "  Redis"
docker exec toolboxai-redis redis-cli ping > /dev/null 2>&1 && echo -e " ${GREEN}✅${NC}" || echo -e " ${RED}❌${NC}"

echo -n "  Backend API"
check_service "Backend" "http://localhost:8009/health"

echo -n "  Dashboard"
check_service "Dashboard" "http://localhost:5179"

# Show service URLs
echo ""
echo -e "${GREEN}🎉 ToolBoxAI Application is running!${NC}"
echo ""
echo -e "${BLUE}📍 Service URLs:${NC}"
echo "  • Dashboard:    http://localhost:5179"
echo "  • Backend API:  http://localhost:8009"
echo "  • API Docs:     http://localhost:8009/docs"
echo "  • Prometheus:   http://localhost:9090"
echo "  • Grafana:      http://localhost:3001 (admin/admin)"
echo "  • TeamCity:     http://localhost:8111"
echo ""
echo -e "${BLUE}🔍 Useful Commands:${NC}"
echo "  • View logs:       docker compose -f docker-compose.complete.yml logs -f [service]"
echo "  • Stop all:        docker compose -f docker-compose.complete.yml down"
echo "  • Restart service: docker compose -f docker-compose.complete.yml restart [service]"
echo "  • Shell access:    docker exec -it toolboxai-backend bash"
echo ""
echo -e "${GREEN}✨ Happy coding!${NC}"