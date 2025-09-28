#!/bin/bash
# ============================================
# TEAMCITY STOP SCRIPT
# ============================================
# Gracefully stops TeamCity server and agents
# Created: 2025-09-28
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

COMPOSE_DIR="$(dirname "$0")/../docker/compose"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Stopping TeamCity CI/CD Services                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$COMPOSE_DIR"

# ----------------------------------------
# Stop running builds gracefully
# ----------------------------------------
echo -e "${YELLOW}⏸️  Stopping running builds...${NC}"

# Send stop signal to agents (they will finish current builds)
docker compose -f docker-compose.teamcity.yml kill -s SIGTERM teamcity-agent-1 teamcity-agent-2 teamcity-agent-3 2>/dev/null || true

# Wait for builds to complete (max 5 minutes)
echo -e "${YELLOW}⏳ Waiting for builds to complete (max 5 minutes)...${NC}"
timeout=300
elapsed=0

while [ $elapsed -lt $timeout ]; do
    # Check if any builds are still running
    if docker compose -f docker-compose.teamcity.yml logs teamcity-agent-1 2>/dev/null | tail -1 | grep -q "Build.*running"; then
        echo -n "."
        sleep 10
        elapsed=$((elapsed + 10))
    else
        break
    fi
done

echo ""
echo -e "${GREEN}✅ Builds stopped${NC}"

# ----------------------------------------
# Stop TeamCity services
# ----------------------------------------
echo ""
echo -e "${YELLOW}🛑 Stopping TeamCity services...${NC}"

# Stop all services
docker compose -f docker-compose.teamcity.yml stop

echo -e "${GREEN}✅ Services stopped${NC}"

# ----------------------------------------
# Optional: Remove containers
# ----------------------------------------
echo ""
read -p "$(echo -e ${YELLOW}Remove containers? [y/N]: ${NC})" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🗑️  Removing containers...${NC}"
    docker compose -f docker-compose.teamcity.yml down
    echo -e "${GREEN}✅ Containers removed${NC}"
fi

# ----------------------------------------
# Optional: Remove volumes
# ----------------------------------------
read -p "$(echo -e ${YELLOW}Remove data volumes? (This will delete all TeamCity data) [y/N]: ${NC})" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}⚠️  WARNING: This will delete all TeamCity data!${NC}"
    read -p "$(echo -e ${RED}Are you sure? Type 'DELETE' to confirm: ${NC})" confirm

    if [ "$confirm" = "DELETE" ]; then
        echo -e "${YELLOW}🗑️  Removing volumes...${NC}"
        docker compose -f docker-compose.teamcity.yml down -v
        echo -e "${GREEN}✅ Volumes removed${NC}"
    else
        echo -e "${YELLOW}Cancelled - volumes preserved${NC}"
    fi
fi

# ----------------------------------------
# Display status
# ----------------------------------------
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                TeamCity Stopped Successfully                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${BLUE}📊 Container Status:${NC}"
docker compose -f docker-compose.teamcity.yml ps

echo ""
echo -e "${BLUE}💾 Volume Status:${NC}"
docker volume ls | grep teamcity || echo "No TeamCity volumes found"

echo ""
echo -e "${BLUE}🔄 To restart TeamCity:${NC}"
echo -e "  ${GREEN}./start-teamcity.sh${NC}"

echo ""
echo -e "${GREEN}✨ TeamCity services stopped cleanly${NC}"