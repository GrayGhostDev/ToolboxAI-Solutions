#!/bin/bash

# ToolBoxAI-Solutions Reference Update Script
# Updates import paths, configuration references, and file paths after reorganization

set -e

# Determine project root dynamically (allow override)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

echo "🔗 Starting reference updates..."
echo "Project root: $PROJECT_ROOT"

# Function to update file references
update_file_references() {
    local file_path="$1"
    local old_path="$2"
    local new_path="$3"
    
    if [[ -f "$file_path" ]]; then
        echo "📝 Updating references in: $file_path"
        # Use sed to replace old paths with new paths
        sed -i.bak "s|$old_path|$new_path|g" "$file_path"
        rm "$file_path.bak" 2>/dev/null || true
        echo "   ✅ Updated successfully"
    fi
}

# Function to update Python import paths
update_python_imports() {
    local file_path="$1"
    
    if [[ -f "$file_path" && "$file_path" == *.py ]]; then
        echo "🐍 Updating Python imports in: $file_path"
        
        # Update common import patterns
        sed -i.bak 's|from toolboxai_settings|from src.shared.settings|g' "$file_path"
        sed -i.bak 's|from toolboxai_utils|from src.shared.utils|g' "$file_path"
        sed -i.bak 's|import toolboxai_settings|import src.shared.settings|g' "$file_path"
        sed -i.bak 's|import toolboxai_utils|import src.shared.utils|g' "$file_path"
        
        # Update relative imports
        sed -i.bak 's|from \.\.toolboxai_settings|from ...src.shared.settings|g' "$file_path"
        sed -i.bak 's|from \.\.toolboxai_utils|from ...src.shared.utils|g' "$file_path"
        
        rm "$file_path.bak" 2>/dev/null || true
        echo "   ✅ Python imports updated"
    fi
}

echo ""
echo "📋 Phase 1: Updating configuration files..."

# Update pyproject.toml
if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    echo "📝 Updating pyproject.toml..."
    
    # Update test paths
    sed -i.bak 's|"tests"|"tests/unit"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"ToolboxAI-Roblox-Environment/tests"|"tests/integration"|g' "$PROJECT_ROOT/pyproject.toml"
    
    # Update extra paths
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment"|"./src/roblox-environment"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/server"|"./src/roblox-environment/server"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/agents"|"./src/roblox-environment/agents"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/mcp"|"./src/roblox-environment/mcp"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/coordinators"|"./src/roblox-environment/coordinators"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/swarm"|"./src/roblox-environment/swarm"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/sparc"|"./src/roblox-environment/sparc"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./ToolboxAI-Roblox-Environment/toolboxai_utils"|"./src/shared/utils"|g' "$PROJECT_ROOT/pyproject.toml"
    sed -i.bak 's|"./API/GhostBackend/src"|"./src/api/ghost-backend/src"|g' "$PROJECT_ROOT/pyproject.toml"
    
    # Update venv path (replace any venvPath pointing to ToolboxAI-Roblox-Environment with src/roblox-environment)
    sed -i.bak 's|venvPath\s*=\s*"[^"]*ToolboxAI-Roblox-Environment"|venvPath = "./src/roblox-environment"|g' "$PROJECT_ROOT/pyproject.toml"

    rm "$PROJECT_ROOT/pyproject.toml.bak" 2>/dev/null || true
    echo "   ✅ pyproject.toml updated"
fi

# Update package.json
if [[ -f "$PROJECT_ROOT/package.json" ]]; then
    echo "📝 Updating package.json..."
    
    # Update workspace paths
    sed -i.bak 's|"ToolboxAI-Roblox-Environment"|"src/roblox-environment"|g' "$PROJECT_ROOT/package.json"
    sed -i.bak 's|"Dashboard/ToolboxAI-Dashboard"|"src/dashboard"|g' "$PROJECT_ROOT/package.json"
    
    # Update script paths
    sed -i.bak 's|cd ToolboxAI-Roblox-Environment|cd src/roblox-environment|g' "$PROJECT_ROOT/package.json"
    sed -i.bak 's|cd Dashboard/ToolboxAI-Dashboard|cd src/dashboard|g' "$PROJECT_ROOT/package.json"
    
    rm "$PROJECT_ROOT/package.json.bak" 2>/dev/null || true
    echo "   ✅ package.json updated"
fi

echo ""
echo "📋 Phase 2: Updating Python files..."

# Find and update all Python files (excluding virtual environments)
find "$PROJECT_ROOT/src" -name "*.py" -type f -not -path "*/venv_clean/*" -not -path "*/venv/*" -not -path "*/.venv/*" | while read -r file; do
    update_python_imports "$file"
done

echo ""
echo "📋 Phase 3: Updating documentation files..."

# Update README files
find "$PROJECT_ROOT" -name "README.md" -type f | while read -r file; do
    update_file_references "$file" "ToolboxAI-Roblox-Environment" "src/roblox-environment"
    update_file_references "$file" "Dashboard/ToolboxAI-Dashboard" "src/dashboard"
    update_file_references "$file" "toolboxai_settings" "src/shared/settings"
    update_file_references "$file" "toolboxai_utils" "src/shared/utils"
done

# Update CLAUDE.md files
find "$PROJECT_ROOT" -name "CLAUDE.md" -type f | while read -r file; do
    update_file_references "$file" "ToolboxAI-Roblox-Environment" "src/roblox-environment"
    update_file_references "$file" "Dashboard/ToolboxAI-Dashboard" "src/dashboard"
    update_file_references "$file" "API/GhostBackend" "src/api/ghost-backend"
done

echo ""
echo "📋 Phase 4: Updating configuration files..."

# Update tsconfig.json files
find "$PROJECT_ROOT" -name "tsconfig.json" -type f | while read -r file; do
    update_file_references "$file" "ToolboxAI-Roblox-Environment" "src/roblox-environment"
    update_file_references "$file" "Dashboard/ToolboxAI-Dashboard" "src/dashboard"
done

# Update other config files
find "$PROJECT_ROOT" -name "*.json" -type f | while read -r file; do
    if [[ "$file" != *"node_modules"* && "$file" != *"package-lock.json"* ]]; then
        update_file_references "$file" "ToolboxAI-Roblox-Environment" "src/roblox-environment"
        update_file_references "$file" "Dashboard/ToolboxAI-Dashboard" "src/dashboard"
    fi
done

echo ""
echo "📋 Phase 5: Updating shell scripts..."

# Update shell scripts
find "$PROJECT_ROOT/scripts" -name "*.sh" -type f | while read -r file; do
    update_file_references "$file" "ToolboxAI-Roblox-Environment" "src/roblox-environment"
    update_file_references "$file" "Dashboard/ToolboxAI-Dashboard" "src/dashboard"
done

echo ""
echo "📋 Phase 6: Updating test files..."

# Update test files (excluding virtual environments)
find "$PROJECT_ROOT/tests" -name "*.py" -type f -not -path "*/venv_clean/*" -not -path "*/venv/*" -not -path "*/.venv/*" | while read -r file; do
    update_python_imports "$file"
done

echo ""
echo "✅ Reference updates completed!"
echo ""
echo "📊 Summary of updates:"
echo "   - Updated pyproject.toml configuration"
echo "   - Updated package.json workspace paths"
echo "   - Updated Python import statements"
echo "   - Updated documentation references"
echo "   - Updated configuration file paths"
echo "   - Updated shell script paths"
echo "   - Updated test file imports"
echo ""
echo "🎯 Next steps:"
echo "   1. Test project functionality"
echo "   2. Run build processes"
echo "   3. Verify all imports work"
echo "   4. Update any remaining hardcoded paths"
