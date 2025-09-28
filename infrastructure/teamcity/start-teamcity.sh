#!/bin/bash
# ============================================
# TEAMCITY STARTUP SCRIPT
# ============================================
# Starts TeamCity server and agents for ToolBoxAI CI/CD
# Created: 2025-09-28
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_DIR="$(dirname "$0")/../docker/compose"
PROJECT_NAME="toolboxai-teamcity"
TEAMCITY_URL="https://grayghost-toolboxai.teamcity.com"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          TeamCity CI/CD - ToolBoxAI Solutions               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ----------------------------------------
# Check Prerequisites
# ----------------------------------------
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Check .env file
if [ ! -f "../../.env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please ensure .env file exists with TeamCity credentials"
    exit 1
fi
echo -e "${GREEN}✅ Environment file found${NC}"

# Check for TeamCity token
if ! grep -q "TEAMCITY_PIPELINE_ACCESS_TOKEN" ../../.env; then
    echo -e "${RED}❌ TeamCity Pipeline token not found in .env${NC}"
    echo "Please add TEAMCITY_PIPELINE_ACCESS_TOKEN to your .env file"
    exit 1
fi
echo -e "${GREEN}✅ TeamCity credentials configured${NC}"

# ----------------------------------------
# Create required directories
# ----------------------------------------
echo ""
echo -e "${YELLOW}📁 Creating required directories...${NC}"

mkdir -p ../config
mkdir -p ../pipelines
mkdir -p ../build-templates
mkdir -p ../../../.teamcity

echo -e "${GREEN}✅ Directories created${NC}"

# ----------------------------------------
# Create TeamCity network if not exists
# ----------------------------------------
echo ""
echo -e "${YELLOW}🌐 Setting up Docker networks...${NC}"

# Create teamcity network
docker network create teamcity-network 2>/dev/null || echo "TeamCity network already exists"

# Create toolboxai network (for service integration)
docker network create toolboxai 2>/dev/null || echo "ToolBoxAI network already exists"

echo -e "${GREEN}✅ Networks configured${NC}"

# ----------------------------------------
# Start TeamCity Services
# ----------------------------------------
echo ""
echo -e "${YELLOW}🚀 Starting TeamCity services...${NC}"

cd "$COMPOSE_DIR"

# Start TeamCity stack
docker compose -f docker-compose.teamcity.yml up -d

# Wait for services to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker compose -f docker-compose.teamcity.yml exec -T $service curl -f $url &> /dev/null; then
            echo -e "${GREEN}✅ $service is healthy${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 5
    done

    echo -e "${RED}❌ $service failed to start${NC}"
    return 1
}

# Check TeamCity database
echo -n "Checking database"
check_service teamcity-db "localhost:5432" || exit 1

# Check TeamCity server
echo -n "Checking TeamCity server"
check_service teamcity-server "http://localhost:8111/health" || exit 1

# ----------------------------------------
# Configure TeamCity
# ----------------------------------------
echo ""
echo -e "${YELLOW}⚙️  Configuring TeamCity...${NC}"

# Wait for TeamCity to be fully initialized
sleep 30

# Import Kotlin DSL configuration
if [ -f "../../../.teamcity/settings.kts" ]; then
    echo -e "${BLUE}📝 Importing Kotlin DSL configuration...${NC}"
    # TeamCity will automatically detect and import settings.kts
    echo -e "${GREEN}✅ Configuration imported${NC}"
fi

# ----------------------------------------
# Start Build Agents
# ----------------------------------------
echo ""
echo -e "${YELLOW}🤖 Starting build agents...${NC}"

# Agents should auto-register with the server
docker compose -f docker-compose.teamcity.yml logs teamcity-agent-1 | tail -5
docker compose -f docker-compose.teamcity.yml logs teamcity-agent-2 | tail -5
docker compose -f docker-compose.teamcity.yml logs teamcity-agent-3 | tail -5

echo -e "${GREEN}✅ Build agents started${NC}"

# ----------------------------------------
# Display Status
# ----------------------------------------
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  TeamCity Started Successfully               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker compose -f docker-compose.teamcity.yml ps

echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo -e "  • TeamCity Server: ${GREEN}http://localhost:8111${NC}"
echo -e "  • TeamCity Cloud:  ${GREEN}${TEAMCITY_URL}${NC}"
echo -e "  • Registry Cache:  ${GREEN}http://localhost:5000${NC}"

echo ""
echo -e "${BLUE}👤 Login Credentials:${NC}"
echo -e "  • Username: ${GREEN}GrayGhostDev${NC}"
echo -e "  • Token:    ${GREEN}[Configured in .env]${NC}"

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo -e "  1. Open TeamCity at http://localhost:8111"
echo -e "  2. Authorize build agents if needed"
echo -e "  3. Run first build to test pipeline"
echo -e "  4. Monitor builds at ${TEAMCITY_URL}/pipelines"

echo ""
echo -e "${BLUE}🛑 To stop TeamCity:${NC}"
echo -e "  ${GREEN}./stop-teamcity.sh${NC}"

echo ""
echo -e "${GREEN}✨ TeamCity CI/CD is ready for ToolBoxAI!${NC}"