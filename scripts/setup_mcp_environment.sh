#!/bin/bash

# ToolboxAI MCP Environment Setup Script
# This script sets up the complete MCP environment for Cursor integration

set -e
# shellcheck source=common/lib.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common/lib.sh" 2>/dev/null || true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory (computed dynamically; override with PROJECT_ROOT env var)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ROBLOX_ENV="$PROJECT_ROOT/ToolboxAI-Roblox-Environment"
VENV_PATH="$ROBLOX_ENV/venv_clean"

echo -e "${BLUE}🚀 Setting up ToolboxAI MCP Environment${NC}"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/README.md" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/scripts/pids"
mkdir -p "$PROJECT_ROOT/config"

# Check Python version
echo -e "${YELLOW}🐍 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo -e "${GREEN}✅ Python $python_version is compatible${NC}"
else
    echo -e "${RED}❌ Python $python_version is not compatible. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    cd "$ROBLOX_ENV"
    python3 -m venv venv_clean
    cd "$PROJECT_ROOT"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment activated: $VIRTUAL_ENV${NC}"

# Upgrade pip
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
"$VENV_PATH/bin/pip" install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
if [ -f "$ROBLOX_ENV/requirements.txt" ]; then
    "$VENV_PATH/bin/pip" install -r "$ROBLOX_ENV/requirements.txt"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, installing basic dependencies...${NC}"
    "$VENV_PATH/bin/pip" install fastapi uvicorn flask websockets pydantic langchain langchain-openai
fi

# Install additional MCP dependencies
echo -e "${YELLOW}🔧 Installing MCP-specific dependencies...${NC}"
"$VENV_PATH/bin/pip" install websockets asyncio-mqtt redis sqlalchemy alembic

# Check for required API keys
echo -e "${YELLOW}🔑 Checking API keys...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set. Please set it in your environment:${NC}"
    echo "export OPENAI_API_KEY='your-openai-api-key'"
    echo ""
    echo -e "${BLUE}💡 You can add this to your ~/.zshrc or ~/.bashrc file${NC}"
fi

if [ -z "$LANGCHAIN_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  LANGCHAIN_API_KEY not set (optional for tracing)${NC}"
fi

# Create environment file template
echo -e "${YELLOW}📝 Creating environment file template...${NC}"
cat > "$PROJECT_ROOT/.env.template" << EOF
# ToolboxAI Environment Configuration
# Copy this file to .env and fill in your values

# Core Configuration
DEBUG=true
ENVIRONMENT=development

# Server Configuration
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8008
FLASK_HOST=127.0.0.1
FLASK_PORT=5001

# AI Configuration
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# MCP Configuration
MCP_HOST=localhost
MCP_PORT=9876
MCP_MAX_CONTEXT_TOKENS=128000

# Database & Cache
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./toolboxai_roblox.db

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production

# LMS Integration (Optional)
SCHOOLOGY_KEY=your-schoology-key
SCHOOLOGY_SECRET=your-schoology-secret
CANVAS_TOKEN=your-canvas-token

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
EOF

# Check if .env exists, if not copy from template
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}📋 Creating .env file from template...${NC}"
    cp "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env"
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual API keys${NC}"
fi

# Test imports
echo -e "${YELLOW}🧪 Testing imports...${NC}"
"$VENV_PATH/bin/python" -c "
try:
    import fastapi
    import flask
    import websockets
    import pydantic
    import langchain
    print('✅ All required packages imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Create a simple test script
# Run the test (optional)
echo -e "${YELLOW}🧪 Running setup tests...${NC}"
cd "$PROJECT_ROOT"
if [ -f "scripts/mcp/test_mcp_setup.py" ]; then
  "$VENV_PATH/bin/python" scripts/mcp/test_mcp_setup.py || true
else
  echo -e "${YELLOW}⚠️  Test script not found at scripts/mcp/test_mcp_setup.py${NC}"
fi


echo ""
echo -e "${GREEN}🎉 MCP Environment Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "=============="
echo "1. Set your API keys in the .env file"
echo "2. Start MCP servers: ./scripts/start_mcp_servers.sh"
echo "3. Check status: ./scripts/check_mcp_status.sh"
echo "4. Configure Cursor to use mcpServers.json"
echo ""
echo -e "${BLUE}🔗 Useful URLs:${NC}"
echo "==============="
echo "FastAPI Server: http://$API_HOST:$FASTAPI_PORT"
echo "API Documentation: http://$API_HOST:$FASTAPI_PORT/docs"
echo "Flask Bridge: http://$API_HOST:$FLASK_PORT"
echo "MCP WebSocket: ws://$API_HOST:$MCP_PORT"
echo ""
echo -e "${GREEN}✨ Ready for Cursor MCP integration!${NC}"
