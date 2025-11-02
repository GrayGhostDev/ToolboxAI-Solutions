#!/bin/bash
# ============================================
# Start Development Environment
# ============================================
# This script starts all ToolboxAI services in development mode
# with proper secret handling from .env file
# ============================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting ToolboxAI Development Environment${NC}"

# Find project root (3 levels up from compose directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Function to read value from .env file
get_env_value() {
    local key="$1"
    local value=$(grep "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d '=' -f2- | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//")
    echo "$value"
}

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ .env file not found at: $ENV_FILE${NC}"
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        echo -e "${YELLOW}⚠️  Please edit $ENV_FILE with your actual values${NC}"
        exit 1
    else
        echo -e "${RED}❌ No .env.example found. Cannot proceed.${NC}"
        exit 1
    fi
fi

# Create secrets directory
mkdir -p .secrets

echo -e "${GREEN}📝 Loading secrets from .env file...${NC}"

# Read secrets from .env and write to files
get_env_value "POSTGRES_PASSWORD" > .secrets/db_password.txt
get_env_value "REDIS_PASSWORD" > .secrets/redis_password.txt
get_env_value "DATABASE_URL" > .secrets/database_url.txt
get_env_value "REDIS_URL" > .secrets/redis_url.txt
get_env_value "JWT_SECRET_KEY" > .secrets/jwt_secret.txt
get_env_value "OPENAI_API_KEY" > .secrets/openai_api_key.txt
get_env_value "ANTHROPIC_API_KEY" > .secrets/anthropic_api_key.txt
get_env_value "ROBLOX_API_KEY" > .secrets/roblox_api_key.txt
get_env_value "ROBLOX_CLIENT_SECRET" > .secrets/roblox_client_secret.txt
get_env_value "LANGCACHE_API_KEY" > .secrets/langcache_api_key.txt
get_env_value "BACKUP_ENCRYPTION_KEY" > .secrets/backup_encryption_key.txt

echo -e "${GREEN}✅ Secrets loaded from .env${NC}"

# Start services
echo -e "${GREEN}Starting Docker Compose services...${NC}"
docker compose \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    up -d

echo -e "${GREEN}✅ Services started successfully!${NC}"
echo ""
echo "Access points:"
echo "  - Backend API:     http://localhost:8009"
echo "  - Dashboard:       http://localhost:5179"
echo "  - Flower:          http://localhost:5555 (admin/admin)"
echo "  - Adminer:         http://localhost:8080"
echo "  - Redis Commander: http://localhost:8081"
echo ""
echo "Logs: docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f [service]"
echo "Stop: docker compose -f docker-compose.yml -f docker-compose.dev.yml down"
