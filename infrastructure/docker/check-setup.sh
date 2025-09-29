#!/bin/bash
# Quick setup check script for ToolBoxAI Docker environment

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
COMPOSE_FILE="infrastructure/docker/docker-compose.dev.yml"

cd "$PROJECT_ROOT"

echo -e "${GREEN}ToolBoxAI Docker Setup Check${NC}"
echo "=================================="

# Check Docker
echo -n "Docker: "
if docker --version > /dev/null 2>&1; then
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${RED}✗ Not running${NC}"
        echo "Please start Docker Desktop"
        exit 1
    fi
else
    echo -e "${RED}✗ Not installed${NC}"
    exit 1
fi

# Check .env file
echo -n ".env file: "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Missing${NC}"
    exit 1
fi

# Check compose file
echo -n "Docker Compose file: "
if [ -f "$COMPOSE_FILE" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Missing${NC}"
    exit 1
fi

# Check Dockerfiles
echo -n "Dockerfiles: "
missing_dockerfiles=0
dockerfiles=(
    "infrastructure/docker/Dockerfile.backend"
    "infrastructure/docker/dashboard.dev.Dockerfile"
    "infrastructure/docker/mcp-server.Dockerfile"
    "infrastructure/docker/agent-coordinator.Dockerfile"
    "infrastructure/docker/educational-agents.Dockerfile"
    "infrastructure/docker/flask-bridge.Dockerfile"
)

for dockerfile in "${dockerfiles[@]}"; do
    if [ ! -f "$dockerfile" ]; then
        missing_dockerfiles=$((missing_dockerfiles + 1))
    fi
done

if [ $missing_dockerfiles -eq 0 ]; then
    echo -e "${GREEN}✓ All found${NC}"
else
    echo -e "${RED}✗ $missing_dockerfiles missing${NC}"
fi

# Check ports
echo -n "Port conflicts: "
conflicts=0
ports=(8009 5179 5434 6381 8888 9877 5001 8000)
for port in "${ports[@]}"; do
    if lsof -i ":$port" > /dev/null 2>&1; then
        conflicts=$((conflicts + 1))
    fi
done

if [ $conflicts -eq 0 ]; then
    echo -e "${GREEN}✓ No conflicts${NC}"
else
    echo -e "${YELLOW}⚠ $conflicts ports in use${NC}"
fi

# Check required env vars
echo -n "Environment variables: "
missing_vars=0
vars=("POSTGRES_PASSWORD" "JWT_SECRET_KEY" "PUSHER_KEY" "PUSHER_SECRET" "PUSHER_APP_ID")
for var in "${vars[@]}"; do
    if ! grep -q "^${var}=" ".env" || [ -z "$(grep "^${var}=" ".env" | cut -d'=' -f2)" ]; then
        missing_vars=$((missing_vars + 1))
    fi
done

if [ $missing_vars -eq 0 ]; then
    echo -e "${GREEN}✓ All set${NC}"
else
    echo -e "${RED}✗ $missing_vars missing/empty${NC}"
    exit 1
fi

echo "=================================="
echo -e "${GREEN}✓ Setup looks good!${NC}"
echo ""
echo "To start all services, run:"
echo "  ./infrastructure/docker/start-docker-dev.sh"
echo ""
echo "Or start manually with:"
echo "  docker-compose -f $COMPOSE_FILE up -d"
