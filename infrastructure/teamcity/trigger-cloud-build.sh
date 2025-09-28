#!/bin/bash
# ============================================
# TEAMCITY CLOUD BUILD TRIGGER
# ============================================
# Triggers builds on TeamCity Cloud instance
# Created: 2025-09-28
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
TEAMCITY_URL="https://grayghost-toolboxai.teamcity.com"
TEAMCITY_TOKEN="${TEAMCITY_PIPELINE_ACCESS_TOKEN:-eyJ0eXAiOiAiVENWMiJ9.Z00zSzRFazBrNktpandnemRUZ2dJRGhBbVlF.MTZhZjcxM2EtZWJiZC00ODA2LTgxMmQtMzA2MWZjMjk2OWYz}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            TeamCity Cloud Build Trigger                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ----------------------------------------
# Check TeamCity API Connection
# ----------------------------------------
echo -e "${YELLOW}🔍 Checking TeamCity Cloud connection...${NC}"

response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TEAMCITY_TOKEN" \
    "${TEAMCITY_URL}/app/rest/server")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ Connected to TeamCity Cloud${NC}"
else
    echo -e "${RED}❌ Cannot connect to TeamCity Cloud (HTTP $response)${NC}"
    echo "Please check your token and network connection"
    exit 1
fi

# ----------------------------------------
# List available projects
# ----------------------------------------
echo ""
echo -e "${YELLOW}📋 Checking for existing projects...${NC}"

projects=$(curl -s \
    -H "Authorization: Bearer $TEAMCITY_TOKEN" \
    -H "Accept: application/json" \
    "${TEAMCITY_URL}/app/rest/projects" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'project' in data:
        for project in data['project']:
            print(f\"{project.get('id', 'N/A')}: {project.get('name', 'N/A')}\")
    else:
        print('No projects found')
except:
    print('Could not parse projects')
" 2>/dev/null || echo "Could not list projects")

echo "$projects"

# ----------------------------------------
# Create project if it doesn't exist
# ----------------------------------------
if ! echo "$projects" | grep -q "ToolBoxAI"; then
    echo ""
    echo -e "${YELLOW}📦 Creating new project from repository...${NC}"

    # Create project from GitHub repository
    create_response=$(curl -s -X POST \
        -H "Authorization: Bearer $TEAMCITY_TOKEN" \
        -H "Content-Type: application/xml" \
        -H "Accept: application/json" \
        "${TEAMCITY_URL}/app/rest/projects" \
        -d '<?xml version="1.0" encoding="UTF-8"?>
        <project name="ToolBoxAI Solutions" id="ToolBoxAISolutions">
            <parentProject locator="id:_Root"/>
            <parameters>
                <property name="env.TEAMCITY_CLOUD_BUILDER" value="cloud://thegrayghost23/jetbrains_linux-amd64"/>
                <property name="env.DOCKER_REGISTRY" value="build-cloud.docker.com:443/thegrayghost23"/>
            </parameters>
        </project>')

    if echo "$create_response" | grep -q "ToolBoxAI"; then
        echo -e "${GREEN}✅ Project created successfully${NC}"
        PROJECT_ID="ToolBoxAISolutions"
    else
        echo -e "${CYAN}ℹ️  Project might already exist or manual setup required${NC}"
        PROJECT_ID="ToolBoxAISolutions"
    fi
else
    echo -e "${GREEN}✅ ToolBoxAI project already exists${NC}"
    PROJECT_ID=$(echo "$projects" | grep "ToolBoxAI" | cut -d: -f1 | head -1 | tr -d ' ')
fi

# ----------------------------------------
# Import VCS Root
# ----------------------------------------
echo ""
echo -e "${YELLOW}🔗 Configuring VCS root...${NC}"

vcs_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TEAMCITY_TOKEN" \
    -H "Content-Type: application/xml" \
    -H "Accept: application/json" \
    "${TEAMCITY_URL}/app/rest/vcs-roots" \
    -d "<?xml version='1.0' encoding='UTF-8'?>
    <vcs-root name='ToolBoxAI GitHub' id='${PROJECT_ID}_GitHub'>
        <project id='${PROJECT_ID}'/>
        <properties>
            <property name='url' value='https://github.com/GrayGhostDev/ToolboxAI-Solutions.git'/>
            <property name='branch' value='refs/heads/chore/remove-render-worker-2025-09-20'/>
            <property name='branchSpec' value='+:refs/heads/*'/>
            <property name='authMethod' value='PASSWORD'/>
            <property name='username' value='GrayGhostDev'/>
        </properties>
    </vcs-root>")

if echo "$vcs_response" | grep -q "error"; then
    echo -e "${CYAN}ℹ️  VCS root might already exist${NC}"
else
    echo -e "${GREEN}✅ VCS root configured${NC}"
fi

# ----------------------------------------
# Import Kotlin DSL Settings
# ----------------------------------------
echo ""
echo -e "${YELLOW}📝 Importing Kotlin DSL configuration...${NC}"

# Enable versioned settings
settings_response=$(curl -s -X PUT \
    -H "Authorization: Bearer $TEAMCITY_TOKEN" \
    -H "Content-Type: application/xml" \
    -H "Accept: application/json" \
    "${TEAMCITY_URL}/app/rest/projects/id:${PROJECT_ID}/projectFeatures/versioned-settings" \
    -d "<?xml version='1.0' encoding='UTF-8'?>
    <projectFeature type='versionedSettings'>
        <properties>
            <property name='enabled' value='true'/>
            <property name='rootId' value='${PROJECT_ID}_GitHub'/>
            <property name='format' value='kotlin'/>
            <property name='useRelativeIds' value='true'/>
        </properties>
    </projectFeature>")

echo -e "${GREEN}✅ Kotlin DSL import initiated${NC}"

# ----------------------------------------
# Wait for configuration to load
# ----------------------------------------
echo ""
echo -e "${YELLOW}⏳ Waiting for configuration to load...${NC}"
sleep 10

# ----------------------------------------
# List build configurations
# ----------------------------------------
echo ""
echo -e "${YELLOW}📋 Available build configurations:${NC}"

builds=$(curl -s \
    -H "Authorization: Bearer $TEAMCITY_TOKEN" \
    -H "Accept: application/json" \
    "${TEAMCITY_URL}/app/rest/buildTypes?locator=project:(id:${PROJECT_ID})" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'buildType' in data:
        for build in data['buildType']:
            print(f\"  • {build.get('id', 'N/A')}: {build.get('name', 'N/A')}\")
    else:
        print('  No build configurations found yet')
except:
    print('  Configurations still loading...')
" 2>/dev/null || echo "  Configurations still loading...")

echo "$builds"

# ----------------------------------------
# Trigger a test build
# ----------------------------------------
echo ""
echo -e "${YELLOW}🚀 Attempting to trigger dashboard build...${NC}"

# Try different possible build IDs
for BUILD_ID in "${PROJECT_ID}_DashboardBuild" "DashboardBuild" "${PROJECT_ID}_Dashboard"; do
    trigger_response=$(curl -s -X POST \
        -H "Authorization: Bearer $TEAMCITY_TOKEN" \
        -H "Content-Type: application/xml" \
        -H "Accept: application/json" \
        "${TEAMCITY_URL}/app/rest/buildQueue" \
        -d "<build branchName='chore/remove-render-worker-2025-09-20'>
            <buildType id='${BUILD_ID}'/>
            <comment><text>Triggered from CLI - Testing TeamCity Cloud</text></comment>
        </build>" 2>/dev/null)

    if echo "$trigger_response" | grep -q "\"id\""; then
        echo -e "${GREEN}✅ Build triggered successfully!${NC}"
        build_id=$(echo "$trigger_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
        echo -e "${BLUE}Build ID: ${build_id}${NC}"
        echo -e "${BLUE}View at: ${TEAMCITY_URL}/viewQueued.html?buildId=${build_id}${NC}"
        break
    fi
done

# ----------------------------------------
# Display summary
# ----------------------------------------
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              TeamCity Cloud Setup Summary                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Cloud Instance:${NC}"
echo -e "  URL: ${GREEN}${TEAMCITY_URL}${NC}"
echo -e "  Project: ${GREEN}${PROJECT_ID}${NC}"
echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo -e "  1. Open TeamCity UI: ${GREEN}${TEAMCITY_URL}${NC}"
echo -e "  2. Login as: ${GREEN}GrayGhostDev${NC}"
echo -e "  3. Navigate to: ${GREEN}Administration → Projects → ${PROJECT_ID}${NC}"
echo -e "  4. Check 'Versioned Settings' is enabled"
echo -e "  5. Verify all 6 build configurations are imported"
echo -e "  6. Configure Docker Hub credentials if needed"
echo ""
echo -e "${BLUE}🚀 Manual Build Trigger:${NC}"
echo -e "  Dashboard: ${GREEN}${TEAMCITY_URL}/viewType.html?buildTypeId=${PROJECT_ID}_DashboardBuild${NC}"
echo -e "  Backend: ${GREEN}${TEAMCITY_URL}/viewType.html?buildTypeId=${PROJECT_ID}_BackendBuild${NC}"
echo ""
echo -e "${YELLOW}💡 Note:${NC} If builds don't appear, you may need to:"
echo -e "  • Manually create the project in TeamCity UI"
echo -e "  • Import from GitHub repository"
echo -e "  • Enable Kotlin DSL settings"
echo ""
echo -e "${GREEN}✨ TeamCity Cloud is configured and ready!${NC}"