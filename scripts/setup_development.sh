#!/bin/bash
# ToolboxAI Solutions - Development Environment Setup Script
# Ensures proper use of venv_clean environment and installs all dependencies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ToolboxAI Solutions - Development Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "src" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Check if venv_clean exists
VENV_PATH="ToolboxAI-Roblox-Environment/venv_clean"
if [ ! -f "${VENV_PATH}/bin/activate" ]; then
    echo -e "${RED}❌ venv_clean environment not found at ${VENV_PATH}${NC}"
    echo -e "${YELLOW}   Please create the venv_clean environment first:${NC}"
    echo -e "${YELLOW}   cd ToolboxAI-Roblox-Environment${NC}"
    echo -e "${YELLOW}   python -m venv venv_clean${NC}"
    echo -e "${YELLOW}   source venv_clean/bin/activate${NC}"
    echo -e "${YELLOW}   pip install --upgrade pip wheel setuptools${NC}"
    exit 1
fi

# Activate venv_clean
echo -e "${YELLOW}🐍 Activating venv_clean environment...${NC}"
source "${VENV_PATH}/bin/activate"

# Verify activation
if [[ "$VIRTUAL_ENV" != *"venv_clean"* ]]; then
    echo -e "${RED}❌ Failed to activate venv_clean environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ venv_clean activated: ${VIRTUAL_ENV}${NC}"
echo -e "${GREEN}   Python: $(which python)${NC}"
echo -e "${GREEN}   Pip: $(which pip)${NC}"
echo ""

# Upgrade pip and essential tools
echo -e "${BLUE}📦 Upgrading pip and essential tools...${NC}"
pip install --upgrade pip wheel setuptools

# Install main requirements
echo -e "${BLUE}📦 Installing main Python dependencies...${NC}"
pip install -r src/roblox-environment/requirements.txt

# Install AI-specific requirements if they exist
if [ -f "src/roblox-environment/requirements-ai.txt" ]; then
    echo -e "${BLUE}🧠 Installing AI/ML dependencies...${NC}"
    pip install -r src/roblox-environment/requirements-ai.txt
fi

# Install coordinator requirements
if [ -f "src/roblox-environment/coordinators/requirements.txt" ]; then
    echo -e "${BLUE}🔧 Installing coordinator dependencies...${NC}"
    pip install -r src/roblox-environment/coordinators/requirements.txt
fi

# Install ghost backend requirements
if [ -f "src/api/ghost-backend/requirements.txt" ]; then
    echo -e "${BLUE}👻 Installing ghost backend dependencies...${NC}"
    pip install -r src/api/ghost-backend/requirements.txt
fi

# Install dashboard backend requirements
if [ -f "src/dashboard/backend/requirements.txt" ]; then
    echo -e "${BLUE}📊 Installing dashboard backend dependencies...${NC}"
    pip install -r src/dashboard/backend/requirements.txt
fi

# Install development and testing tools
echo -e "${BLUE}🛠️  Installing development tools...${NC}"
pip install \
    pytest pytest-asyncio pytest-cov pytest-mock \
    black flake8 mypy isort \
    pip-audit safety bandit \
    pre-commit

# Install Node.js dependencies
echo -e "${BLUE}🟢 Installing Node.js dependencies...${NC}"
if command -v npm &> /dev/null; then
    npm install
    if [ -f "package.json" ] && npm run install:all --if-present; then
        echo -e "${GREEN}✅ Node.js workspace dependencies installed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  npm not found - skipping Node.js dependencies${NC}"
fi

# Set up pre-commit hooks
echo -e "${BLUE}🪝 Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠️  pre-commit not installed - skipping hooks setup${NC}"
fi

# Database setup
if [ -f "database/setup_database.py" ]; then
    echo -e "${BLUE}🗄️  Setting up database...${NC}"
    cd database
    python setup_database.py
    cd ..
    echo -e "${GREEN}✅ Database setup completed${NC}"
else
    echo -e "${YELLOW}⚠️  Database setup script not found - skipping${NC}"
fi

# Run security audit
echo -e "${BLUE}🔒 Running security audit...${NC}"
if [ -x "scripts/security_audit.sh" ]; then
    ./scripts/security_audit.sh || echo -e "${YELLOW}⚠️  Security audit found issues - please review${NC}"
else
    echo -e "${YELLOW}⚠️  Security audit script not found - skipping${NC}"
fi

# Verify installation
echo -e "${BLUE}🧪 Verifying installation...${NC}"

# Test Python imports
echo -e "${YELLOW}  Testing key Python imports...${NC}"
python -c "
try:
    import fastapi
    import sqlalchemy
    import langchain
    import pydantic
    print('  ✅ FastAPI:', fastapi.__version__)
    print('  ✅ SQLAlchemy:', sqlalchemy.__version__)
    print('  ✅ LangChain:', langchain.__version__)
    print('  ✅ Pydantic:', pydantic.__version__)
except ImportError as e:
    print(f'  ❌ Import error: {e}')
    exit(1)
"

# Test basic functionality
echo -e "${YELLOW}  Testing basic functionality...${NC}"
if [ -f "tests/test_settings.py" ]; then
    python -m pytest tests/test_settings.py -v || echo -e "${YELLOW}    ⚠️  Some tests failed${NC}"
else
    echo -e "${YELLOW}    ⚠️  Settings test not found - skipping${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Development environment setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "${YELLOW}  1. Start the FastAPI server:${NC}"
echo -e "${YELLOW}     cd src/roblox-environment${NC}"
echo -e "${YELLOW}     python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8008${NC}"
echo ""
echo -e "${YELLOW}  2. Start the dashboard:${NC}"
echo -e "${YELLOW}     npm run dev:dashboard${NC}"
echo ""
echo -e "${YELLOW}  3. Run tests:${NC}"
echo -e "${YELLOW}     python -m pytest tests/${NC}"
echo -e "${YELLOW}     npm test${NC}"
echo ""
echo -e "${BLUE}📚 Remember to always activate venv_clean before working:${NC}"
echo -e "${YELLOW}   source ${VENV_PATH}/bin/activate${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"