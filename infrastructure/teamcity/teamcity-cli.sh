#!/bin/bash
# ============================================
# TEAMCITY CLI - MANAGE WITHOUT UI
# ============================================
# Control TeamCity Cloud via command line
# Created: 2025-09-28
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
TEAMCITY_URL="https://grayghost-toolboxai.teamcity.com"
TEAMCITY_TOKEN="${TEAMCITY_PIPELINE_ACCESS_TOKEN:-eyJ0eXAiOiAiVENWMiJ9.Z00zSzRFazBrNktpandnemRUZ2dJRGhBbVlF.MTZhZjcxM2EtZWJiZC00ODA2LTgxMmQtMzA2MWZjMjk2OWYz}"

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -z "$data" ]; then
        curl -s -X $method \
            -H "Authorization: Bearer $TEAMCITY_TOKEN" \
            -H "Accept: application/json" \
            "${TEAMCITY_URL}/app/rest${endpoint}"
    else
        curl -s -X $method \
            -H "Authorization: Bearer $TEAMCITY_TOKEN" \
            -H "Accept: application/json" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${TEAMCITY_URL}/app/rest${endpoint}"
    fi
}

# Main menu
show_menu() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              TeamCity CLI Management Tool                   ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Select an option:${NC}"
    echo ""
    echo "  1) Check server status"
    echo "  2) List projects"
    echo "  3) Create ToolBoxAI project"
    echo "  4) List build configurations"
    echo "  5) Trigger Dashboard build"
    echo "  6) Trigger Backend build"
    echo "  7) View build queue"
    echo "  8) View recent builds"
    echo "  9) Setup project from GitHub"
    echo "  0) Exit"
    echo ""
    read -p "Enter choice: " choice
}

# Check server status
check_status() {
    echo -e "${YELLOW}🔍 Checking TeamCity server status...${NC}"
    response=$(api_call GET "/server")

    if echo "$response" | grep -q "version"; then
        echo -e "${GREEN}✅ Server is online${NC}"
        echo "$response" | python3 -m json.tool | head -10
    else
        echo -e "${RED}❌ Cannot connect to server${NC}"
    fi
}

# List projects
list_projects() {
    echo -e "${YELLOW}📋 Listing projects...${NC}"
    response=$(api_call GET "/projects")

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'project' in data:
    for p in data['project']:
        print(f\"• {p.get('id', 'N/A')}: {p.get('name', 'N/A')}\")
else:
    print('No projects found')
" 2>/dev/null || echo "Error parsing projects"
}

# Create project
create_project() {
    echo -e "${YELLOW}📦 Creating ToolBoxAI project...${NC}"

    data='{
        "name": "ToolBoxAI Solutions",
        "id": "ToolBoxAISolutions",
        "parentProject": {"locator": "id:_Root"},
        "parameters": {
            "property": [
                {"name": "env.TEAMCITY_CLOUD_BUILDER", "value": "cloud://thegrayghost23/jetbrains_linux-amd64"},
                {"name": "env.DOCKER_REGISTRY", "value": "build-cloud.docker.com:443/thegrayghost23"}
            ]
        }
    }'

    response=$(api_call POST "/projects" "$data")

    if echo "$response" | grep -q "ToolBoxAI"; then
        echo -e "${GREEN}✅ Project created successfully${NC}"
    else
        echo -e "${CYAN}ℹ️  Project might already exist${NC}"
    fi

    # Setup VCS root
    echo -e "${YELLOW}🔗 Setting up GitHub repository...${NC}"

    vcs_data='{
        "name": "ToolBoxAI GitHub",
        "id": "ToolBoxAISolutions_GitHub",
        "vcsName": "jetbrains.git",
        "project": {"id": "ToolBoxAISolutions"},
        "properties": {
            "property": [
                {"name": "url", "value": "https://github.com/GrayGhostDev/ToolboxAI-Solutions.git"},
                {"name": "branch", "value": "refs/heads/chore/remove-render-worker-2025-09-20"},
                {"name": "authMethod", "value": "PASSWORD"},
                {"name": "username", "value": "GrayGhostDev"}
            ]
        }
    }'

    api_call POST "/vcs-roots" "$vcs_data" > /dev/null 2>&1
    echo -e "${GREEN}✅ VCS root configured${NC}"

    # Enable versioned settings
    echo -e "${YELLOW}📝 Enabling Kotlin DSL settings...${NC}"

    settings_data='{
        "type": "versionedSettings",
        "properties": {
            "property": [
                {"name": "enabled", "value": "true"},
                {"name": "rootId", "value": "ToolBoxAISolutions_GitHub"},
                {"name": "format", "value": "kotlin"},
                {"name": "useRelativeIds", "value": "true"}
            ]
        }
    }'

    api_call PUT "/projects/id:ToolBoxAISolutions/projectFeatures/versioned-settings" "$settings_data" > /dev/null 2>&1
    echo -e "${GREEN}✅ Kotlin DSL enabled${NC}"
}

# List build configurations
list_builds() {
    echo -e "${YELLOW}🏗️  Listing build configurations...${NC}"
    response=$(api_call GET "/buildTypes?locator=project:(id:ToolBoxAISolutions)")

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'buildType' in data:
    for b in data['buildType']:
        print(f\"• {b.get('id', 'N/A')}: {b.get('name', 'N/A')}\")
else:
    print('No build configurations found')
" 2>/dev/null || echo "No builds found yet"
}

# Trigger build
trigger_build() {
    local build_type=$1
    local build_name=$2

    echo -e "${YELLOW}🚀 Triggering $build_name build...${NC}"

    data="{
        \"buildType\": {\"id\": \"$build_type\"},
        \"branchName\": \"chore/remove-render-worker-2025-09-20\",
        \"comment\": {\"text\": \"Triggered from CLI\"}
    }"

    response=$(api_call POST "/buildQueue" "$data")

    if echo "$response" | grep -q "\"id\""; then
        build_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
        echo -e "${GREEN}✅ Build triggered successfully!${NC}"
        echo -e "${BLUE}Build ID: $build_id${NC}"
        echo -e "${BLUE}View at: ${TEAMCITY_URL}/viewQueued.html?buildId=$build_id${NC}"
    else
        echo -e "${RED}❌ Failed to trigger build${NC}"
        echo "Response: $response"
    fi
}

# View build queue
view_queue() {
    echo -e "${YELLOW}📋 Build queue:${NC}"
    response=$(api_call GET "/buildQueue")

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'build' in data and data['count'] > 0:
    for b in data['build']:
        print(f\"• Build {b.get('id', 'N/A')}: {b.get('buildTypeId', 'N/A')} - {b.get('state', 'N/A')}\")
else:
    print('Queue is empty')
" 2>/dev/null || echo "Error reading queue"
}

# View recent builds
view_recent() {
    echo -e "${YELLOW}📊 Recent builds:${NC}"
    response=$(api_call GET "/builds?locator=project:(id:ToolBoxAISolutions),count:5")

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'build' in data:
    for b in data['build']:
        status = '✅' if b.get('status') == 'SUCCESS' else '❌'
        print(f\"{status} Build {b.get('number', 'N/A')}: {b.get('buildTypeId', 'N/A')} - {b.get('statusText', 'N/A')}\")
else:
    print('No recent builds')
" 2>/dev/null || echo "No builds found"
}

# Main loop
while true; do
    show_menu

    case $choice in
        1) check_status ;;
        2) list_projects ;;
        3) create_project ;;
        4) list_builds ;;
        5) trigger_build "ToolBoxAISolutions_DashboardBuild" "Dashboard" ;;
        6) trigger_build "ToolBoxAISolutions_BackendBuild" "Backend" ;;
        7) view_queue ;;
        8) view_recent ;;
        9) create_project ;;
        0) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
    clear
done