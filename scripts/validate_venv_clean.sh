#!/bin/bash
# ToolboxAI Solutions - Validate venv_clean Environment
# Ensures venv_clean is properly configured and secure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 ToolboxAI Solutions - venv_clean Validation${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Check current directory
if [ ! -f "README.md" ] || [ ! -d "src" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Check if venv_clean exists
VENV_PATH="ToolboxAI-Roblox-Environment/venv_clean"
if [ ! -f "${VENV_PATH}/bin/activate" ]; then
    echo -e "${RED}❌ venv_clean environment not found at ${VENV_PATH}${NC}"
    echo -e "${YELLOW}   Creating venv_clean environment...${NC}"
    
    # Create the directory if it doesn't exist
    mkdir -p ToolboxAI-Roblox-Environment
    
    # Create venv_clean
    cd ToolboxAI-Roblox-Environment
    python3 -m venv venv_clean
    source venv_clean/bin/activate
    pip install --upgrade pip wheel setuptools
    cd ..
    
    echo -e "${GREEN}✅ venv_clean environment created${NC}"
else
    echo -e "${GREEN}✅ venv_clean environment found at ${VENV_PATH}${NC}"
fi

# Activate venv_clean
echo -e "${YELLOW}🐍 Activating venv_clean environment...${NC}"
source "${VENV_PATH}/bin/activate"

# Verify activation
if [[ "$VIRTUAL_ENV" != *"venv_clean"* ]]; then
    echo -e "${RED}❌ Failed to activate venv_clean environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ venv_clean activated successfully${NC}"
echo -e "${BLUE}   Virtual Environment: ${VIRTUAL_ENV}${NC}"
echo -e "${BLUE}   Python: $(which python)${NC}"
echo -e "${BLUE}   Python Version: $(python --version)${NC}"
echo -e "${BLUE}   Pip: $(which pip)${NC}"
echo -e "${BLUE}   Pip Version: $(pip --version)${NC}"
echo ""

# Check if core dependencies are installed
echo -e "${BLUE}🔍 Checking core dependencies...${NC}"

# List of critical packages to check
declare -a critical_packages=(
    "fastapi"
    "sqlalchemy" 
    "requests"
    "aiohttp"
    "pydantic"
    "langchain"
    "openai"
    "pytest"
)

all_installed=true
for package in "${critical_packages[@]}"; do
    if python -c "import $package; print('✅ $package:', $package.__version__)" 2>/dev/null; then
        echo -e "${GREEN}  ✅ $package installed${NC}"
    else
        echo -e "${RED}  ❌ $package NOT INSTALLED${NC}"
        all_installed=false
    fi
done

echo ""

if [ "$all_installed" = true ]; then
    echo -e "${GREEN}✅ All critical dependencies are installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some dependencies missing - run dependency update:${NC}"
    echo -e "${YELLOW}   ./scripts/update_security_dependencies.sh${NC}"
fi

# Security tool check
echo -e "${BLUE}🔒 Checking security tools...${NC}"

declare -a security_tools=(
    "pip-audit"
    "safety"
    "bandit"
)

for tool in "${security_tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo -e "${GREEN}  ✅ $tool available${NC}"
    else
        echo -e "${YELLOW}  ⚠️  $tool not installed${NC}"
        pip install "$tool" --quiet
        if command -v "$tool" &> /dev/null; then
            echo -e "${GREEN}    ✅ $tool installed successfully${NC}"
        else
            echo -e "${RED}    ❌ Failed to install $tool${NC}"
        fi
    fi
done

echo ""

# Run quick security check
echo -e "${BLUE}🛡️  Running quick security check...${NC}"

# Check one main requirements file
main_req_file="src/roblox-environment/requirements.txt"
if [ -f "$main_req_file" ]; then
    echo -e "${YELLOW}  🔍 Auditing $main_req_file...${NC}"
    
    if pip-audit --requirement "$main_req_file" --format text 2>/dev/null | head -10; then
        echo -e "${GREEN}  ✅ No critical vulnerabilities found${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Some vulnerabilities found - run full audit${NC}"
    fi
else
    echo -e "${RED}  ❌ Main requirements file not found${NC}"
fi

echo ""

# Check Python path and environment
echo -e "${BLUE}🔍 Environment Validation Summary${NC}"
echo -e "${BLUE}==================================${NC}"
echo -e "${YELLOW}Virtual Environment Path: ${VIRTUAL_ENV}${NC}"
echo -e "${YELLOW}Python Executable: $(which python)${NC}"
echo -e "${YELLOW}Python Version: $(python --version)${NC}"
echo -e "${YELLOW}Pip Version: $(pip --version)${NC}"
echo -e "${YELLOW}Working Directory: $(pwd)${NC}"
echo ""

# Final status
if [ "$all_installed" = true ]; then
    echo -e "${GREEN}🎉 venv_clean environment is properly configured and ready for development!${NC}"
    echo ""
    echo -e "${BLUE}📋 Quick Commands:${NC}"
    echo -e "${YELLOW}  Activate environment: source ${VENV_PATH}/bin/activate${NC}"
    echo -e "${YELLOW}  Start FastAPI server: cd src/roblox-environment && python -m uvicorn server.main:app --reload${NC}"
    echo -e "${YELLOW}  Run tests: python -m pytest tests/${NC}"
    echo -e "${YELLOW}  Security audit: ./scripts/security_audit.sh${NC}"
    echo -e "${YELLOW}  Update dependencies: ./scripts/update_security_dependencies.sh${NC}"
else
    echo -e "${YELLOW}⚠️  venv_clean environment needs dependency updates${NC}"
    echo -e "${YELLOW}   Run: ./scripts/update_security_dependencies.sh${NC}"
fi

echo ""
echo -e "${BLUE}✨ Happy coding with secure dependencies! 🔒${NC}"