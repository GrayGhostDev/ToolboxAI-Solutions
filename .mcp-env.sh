#!/bin/bash
# MCP Environment Variables Loader
# This script loads environment variables from .env for MCP servers
# Usage: source .mcp-env.sh

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -a  # Automatically export all variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
else
    echo "Warning: .env file not found in $SCRIPT_DIR"
    exit 1
fi
set +a

# Verify critical variables
REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET_KEY"
    "OPENAI_API_KEY"
    "ROBLOX_API_KEY"
    "GITHUB_TOKEN"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "Warning: Missing environment variables: ${MISSING_VARS[*]}"
    echo "Please configure these in your .env file"
fi

echo "✅ MCP environment variables loaded successfully"
echo "   DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "   REDIS_URL: ${REDIS_URL:0:30}..."
echo "   JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:10}..."
echo "   OPENAI_API_KEY: ${OPENAI_API_KEY:0:15}..."
echo "   ROBLOX_API_KEY: ${ROBLOX_API_KEY:0:15}..."
echo "   GITHUB_TOKEN: ${GITHUB_TOKEN:0:15}..."
