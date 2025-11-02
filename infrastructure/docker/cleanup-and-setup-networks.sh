#!/usr/bin/env bash

# ============================================
# Cleanup and Recreate Docker Swarm Networks
# ============================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Cleaning up and recreating Docker Swarm networks...${NC}"
echo ""

# Remove existing toolboxai stack if running
if docker stack ls --format "{{.Name}}" | grep -q "^toolboxai$"; then
    echo -e "${YELLOW}⚠${NC} Removing existing toolboxai stack..."
    docker stack rm toolboxai
    echo -e "${YELLOW}⚠${NC} Waiting 15 seconds for cleanup..."
    sleep 15
fi

# List of networks to manage
networks=(
    "toolboxai_toolboxai-network"
    "toolboxai_frontend"
    "toolboxai_backend"
    "toolboxai_database"
    "toolboxai_cache"
    "toolboxai_mcp"
    "toolboxai_monitoring"
    "toolboxai_roblox"
)

# Remove existing networks
echo -e "${BLUE}Removing existing networks...${NC}"
for network in "${networks[@]}"; do
    if docker network inspect "$network" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Removing network: $network"
        docker network rm "$network" 2>/dev/null || echo -e "${RED}✗${NC} Could not remove $network (might be in use)"
    fi
done

echo ""
echo -e "${BLUE}Creating fresh Swarm overlay networks...${NC}"

# Create networks with proper swarm scope
for network in "${networks[@]}"; do
    # Extract network name without stack prefix for internal flag
    base_name="${network#toolboxai_}"

    # Create network
    if [[ "$base_name" == "database" || "$base_name" == "cache" || "$base_name" == "mcp" ]]; then
        # Internal networks (no external access)
        echo -e "${GREEN}✓${NC} Creating internal network: $network"
        docker network create \
            --driver overlay \
            --attachable \
            --internal \
            "$network"
    else
        # External networks
        echo -e "${GREEN}✓${NC} Creating external network: $network"
        docker network create \
            --driver overlay \
            --attachable \
            "$network"
    fi
done

echo ""
echo -e "${GREEN}✓ All networks created successfully!${NC}"
echo ""
echo -e "${BLUE}Verifying network configurations:${NC}"
docker network ls --filter name=toolboxai --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"

echo ""
echo -e "${GREEN}Ready to deploy!${NC}"
echo ""
echo "Deploy with:"
echo "  docker stack deploy -c infrastructure/docker/compose/docker-compose.yml -c infrastructure/docker/compose/docker-compose.swarm.yml --with-registry-auth toolboxai"
