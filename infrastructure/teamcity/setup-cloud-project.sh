#!/bin/bash
# ============================================
# TEAMCITY CLOUD PROJECT SETUP
# ============================================
# Sets up TeamCity Cloud project from repository
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
TEAMCITY_URL="https://grayghost-toolboxai.teamcity.com"
GITHUB_REPO="https://github.com/GrayGhostDev/ToolboxAI-Solutions.git"
PROJECT_NAME="ToolBoxAI Solutions"
BRANCH="chore/remove-render-worker-2025-09-20"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          TeamCity Cloud Project Setup                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ----------------------------------------
# Instructions for manual setup
# ----------------------------------------
echo -e "${YELLOW}📝 Manual Setup Instructions:${NC}"
echo ""
echo -e "${BLUE}Step 1: Access TeamCity Cloud${NC}"
echo "  1. Open: ${GREEN}${TEAMCITY_URL}${NC}"
echo "  2. Login with username: ${GREEN}GrayGhostDev${NC}"
echo ""

echo -e "${BLUE}Step 2: Create New Project${NC}"
echo "  1. Click '+ New Project' button"
echo "  2. Select 'From repository URL'"
echo "  3. Enter repository: ${GREEN}${GITHUB_REPO}${NC}"
echo "  4. Select branch: ${GREEN}${BRANCH}${NC}"
echo "  5. Name the project: ${GREEN}${PROJECT_NAME}${NC}"
echo ""

echo -e "${BLUE}Step 3: TeamCity will detect .teamcity/settings.kts${NC}"
echo "  1. TeamCity will automatically find the Kotlin DSL configuration"
echo "  2. Review the detected build configurations:"
echo "     • Dashboard (React + Vite)"
echo "     • Backend (FastAPI)"
echo "     • MCP Server"
echo "     • Agent Coordinator"
echo "     • Integration Tests"
echo "     • Deploy to Production"
echo "  3. Click 'Create' to import all configurations"
echo ""

echo -e "${BLUE}Step 4: Configure Credentials${NC}"
echo "  1. Go to Project Settings → Connections & Credentials"
echo "  2. Add the following credentials:"
echo ""
echo "     ${YELLOW}Docker Registry Credentials:${NC}"
echo "     • ID: ${GREEN}teamcity-cloud-docker${NC}"
echo "     • Type: Password"
echo "     • Username: ${GREEN}thegrayghost23${NC}"
echo "     • Password: [Your Docker Hub password]"
echo ""
echo "     ${YELLOW}API Keys (as environment parameters):${NC}"
echo "     • ${GREEN}OPENAI_API_KEY${NC}: [Your OpenAI key]"
echo "     • ${GREEN}ANTHROPIC_API_KEY${NC}: [Your Anthropic key]"
echo "     • ${GREEN}PUSHER_APP_ID${NC}: [Your Pusher App ID]"
echo "     • ${GREEN}PUSHER_KEY${NC}: [Your Pusher Key]"
echo "     • ${GREEN}PUSHER_SECRET${NC}: [Your Pusher Secret]"
echo ""

echo -e "${BLUE}Step 5: Configure Cloud Agents${NC}"
echo "  1. Go to Agents → Cloud"
echo "  2. Verify cloud builder is available:"
echo "     • Builder: ${GREEN}cloud://thegrayghost23/jetbrains_linux-amd64${NC}"
echo "     • Status: Connected"
echo "  3. If not connected, authorize the agent"
echo ""

echo -e "${BLUE}Step 6: Test the Pipeline${NC}"
echo "  1. Go to the project overview"
echo "  2. Click 'Run' on 'Dashboard Build'"
echo "  3. Monitor the build progress"
echo "  4. Check build logs for any issues"
echo ""

# ----------------------------------------
# Automated verification
# ----------------------------------------
echo -e "${YELLOW}🔍 Verifying setup prerequisites...${NC}"

# Check if token exists
if [ -z "$TEAMCITY_PIPELINE_ACCESS_TOKEN" ]; then
    if grep -q "TEAMCITY_PIPELINE_ACCESS_TOKEN" ../../.env 2>/dev/null; then
        echo -e "${GREEN}✅ TeamCity token found in .env${NC}"
        source ../../.env
    else
        echo -e "${RED}❌ TeamCity token not found${NC}"
        echo "Please ensure TEAMCITY_PIPELINE_ACCESS_TOKEN is set in .env"
    fi
else
    echo -e "${GREEN}✅ TeamCity token is set${NC}"
fi

# Check if repository is accessible
if git ls-remote ${GITHUB_REPO} &>/dev/null; then
    echo -e "${GREEN}✅ GitHub repository is accessible${NC}"
else
    echo -e "${RED}❌ Cannot access GitHub repository${NC}"
    echo "Please check repository permissions"
fi

# Check if Kotlin DSL exists
if [ -f "../../.teamcity/settings.kts" ]; then
    echo -e "${GREEN}✅ TeamCity Kotlin DSL configuration found${NC}"
else
    echo -e "${RED}❌ TeamCity configuration not found${NC}"
    echo "Please ensure .teamcity/settings.kts exists"
fi

# ----------------------------------------
# Quick API test (if token is available)
# ----------------------------------------
if [ ! -z "$TEAMCITY_PIPELINE_ACCESS_TOKEN" ]; then
    echo ""
    echo -e "${YELLOW}🔍 Testing TeamCity API connection...${NC}"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TEAMCITY_PIPELINE_ACCESS_TOKEN" \
        "${TEAMCITY_URL}/app/rest/server")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ TeamCity API is accessible${NC}"

        # Try to list projects
        echo ""
        echo -e "${YELLOW}📋 Existing projects:${NC}"
        curl -s \
            -H "Authorization: Bearer $TEAMCITY_PIPELINE_ACCESS_TOKEN" \
            -H "Accept: application/json" \
            "${TEAMCITY_URL}/app/rest/projects" | \
            python3 -m json.tool 2>/dev/null | grep '"name"' | head -5 || echo "Could not list projects"
    else
        echo -e "${RED}❌ Cannot connect to TeamCity API (HTTP $response)${NC}"
        echo "Please verify your token and try again"
    fi
fi

# ----------------------------------------
# Next steps
# ----------------------------------------
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Next Steps                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}After completing the manual setup:${NC}"
echo ""
echo "1. ${YELLOW}Monitor first build:${NC}"
echo "   ${GREEN}${TEAMCITY_URL}/buildConfiguration/${PROJECT_NAME}_DashboardBuild${NC}"
echo ""
echo "2. ${YELLOW}View pipeline status:${NC}"
echo "   ${GREEN}${TEAMCITY_URL}/pipelines${NC}"
echo ""
echo "3. ${YELLOW}Check Docker images:${NC}"
echo "   ${GREEN}docker images | grep build-cloud.docker.com${NC}"
echo ""
echo "4. ${YELLOW}Trigger builds via API:${NC}"
echo "   ${GREEN}./trigger-build.sh DashboardBuild${NC}"
echo ""
echo -e "${GREEN}✨ TeamCity Cloud setup instructions complete!${NC}"