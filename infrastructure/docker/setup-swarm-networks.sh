#!/usr/bin/env bash

# ============================================
# Create Docker Swarm Networks
# ============================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Creating Docker Swarm overlay networks...${NC}"

# Create networks with proper swarm scope
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

for network in "${networks[@]}"; do
    if docker network inspect "$network" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Network exists: $network"
    else
        # Extract network name without stack prefix for internal flag
        base_name="${network#toolboxai_}"

        # Create network
        if [[ "$base_name" == "database" || "$base_name" == "cache" || "$base_name" == "mcp" ]]; then
            # Internal networks (no external access)
            docker network create \
                --driver overlay \
                --attachable \
                --internal \
                "$network"
        else
            # External networks
            docker network create \
                --driver overlay \
                --attachable \
                "$network"
        fi
        echo -e "${GREEN}✓${NC} Created network: $network"
    fi
done

echo ""
echo -e "${GREEN}All networks created successfully!${NC}"
echo ""
echo "You can now deploy with:"
echo "  docker stack deploy -c infrastructure/docker/compose/docker-compose.yml -c infrastructure/docker/compose/docker-compose.swarm.yml toolboxai"
