#!/bin/bash

# ToolBoxAI-Solutions Structural Reorganization Script
# Implements the new directory structure and moves files accordingly

set -e

# Determine project root dynamically (allow override)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

echo "🏗️  Starting structural reorganization..."
echo "Project root: $PROJECT_ROOT"

# Function to create directory if it doesn't exist
create_dir() {
    local dir_path="$1"
    if [[ ! -d "$dir_path" ]]; then
        echo "📁 Creating directory: $dir_path"
        mkdir -p "$dir_path"
    fi
}

# Function to move file with logging
move_file() {
    local source="$1"
    local destination="$2"
    local reason="$3"
    
    if [[ -f "$source" ]]; then
        echo "📄 Moving: $source → $destination"
        echo "   Reason: $reason"
        mkdir -p "$(dirname "$destination")"
        mv "$source" "$destination"
        echo "   ✅ Moved successfully"
    else
        echo "⚠️  Source file not found: $source"
    fi
}

# Function to move directory with logging
move_directory() {
    local source="$1"
    local destination="$2"
    local reason="$3"
    
    if [[ -d "$source" ]]; then
        echo "📁 Moving directory: $source → $destination"
        echo "   Reason: $reason"
        mkdir -p "$(dirname "$destination")"
        mv "$source" "$destination"
        echo "   ✅ Moved successfully"
    else
        echo "⚠️  Source directory not found: $source"
    fi
}

echo ""
echo "📋 Phase 1: Creating new directory structure..."

# Create main directories
create_dir "$PROJECT_ROOT/docs"
create_dir "$PROJECT_ROOT/docs/architecture"
create_dir "$PROJECT_ROOT/docs/api"
create_dir "$PROJECT_ROOT/docs/user-guides"
create_dir "$PROJECT_ROOT/docs/development"
create_dir "$PROJECT_ROOT/docs/deployment"
create_dir "$PROJECT_ROOT/docs/status"

create_dir "$PROJECT_ROOT/src"
create_dir "$PROJECT_ROOT/src/roblox-environment"
create_dir "$PROJECT_ROOT/src/dashboard"
create_dir "$PROJECT_ROOT/src/api"
create_dir "$PROJECT_ROOT/src/shared"

create_dir "$PROJECT_ROOT/scripts"
create_dir "$PROJECT_ROOT/scripts/setup"
create_dir "$PROJECT_ROOT/scripts/build"
create_dir "$PROJECT_ROOT/scripts/deploy"
create_dir "$PROJECT_ROOT/scripts/maintenance"

create_dir "$PROJECT_ROOT/config"
create_dir "$PROJECT_ROOT/config/development"
create_dir "$PROJECT_ROOT/config/production"
create_dir "$PROJECT_ROOT/config/templates"

create_dir "$PROJECT_ROOT/tests"
create_dir "$PROJECT_ROOT/tests/e2e"
create_dir "$PROJECT_ROOT/tests/integration"
create_dir "$PROJECT_ROOT/tests/performance"

create_dir "$PROJECT_ROOT/tools"
create_dir "$PROJECT_ROOT/tools/linting"
create_dir "$PROJECT_ROOT/tools/formatting"
create_dir "$PROJECT_ROOT/tools/analysis"

echo ""
echo "📋 Phase 2: Moving Roblox Environment to src/..."

# Move main Roblox environment
move_directory "$PROJECT_ROOT/ToolboxAI-Roblox-Environment" "$PROJECT_ROOT/src/roblox-environment" "Main Roblox platform code"

echo ""
echo "📋 Phase 3: Consolidating Dashboard..."

# Move dashboard to src/
move_directory "$PROJECT_ROOT/Dashboard/ToolboxAI-Dashboard" "$PROJECT_ROOT/src/dashboard" "React dashboard application"

# Remove empty Dashboard directory
if [[ -d "$PROJECT_ROOT/Dashboard" ]]; then
    rmdir "$PROJECT_ROOT/Dashboard" 2>/dev/null || echo "⚠️  Dashboard directory not empty, skipping removal"
fi

echo ""
echo "📋 Phase 4: Moving API components..."

# Move Ghost backend
if [[ -d "$PROJECT_ROOT/src/roblox-environment/API/GhostBackend" ]]; then
    move_directory "$PROJECT_ROOT/src/roblox-environment/API/GhostBackend" "$PROJECT_ROOT/src/api/ghost-backend" "Ghost backend framework"
fi

# Move API integrations
if [[ -d "$PROJECT_ROOT/src/roblox-environment/API" ]]; then
    # Keep only non-GhostBackend API components
    if [[ -d "$PROJECT_ROOT/src/roblox-environment/API/Dashboard" ]]; then
        move_directory "$PROJECT_ROOT/src/roblox-environment/API/Dashboard" "$PROJECT_ROOT/src/api/dashboard-backend" "Dashboard backend API"
    fi
    
    # Remove empty API directory
    rmdir "$PROJECT_ROOT/src/roblox-environment/API" 2>/dev/null || echo "⚠️  API directory not empty, skipping removal"
fi

echo ""
echo "📋 Phase 5: Moving shared utilities..."

# Move shared utilities
move_directory "$PROJECT_ROOT/toolboxai_settings" "$PROJECT_ROOT/src/shared/settings" "Shared settings module"
move_directory "$PROJECT_ROOT/toolboxai_utils" "$PROJECT_ROOT/src/shared/utils" "Shared utility modules"
move_directory "$PROJECT_ROOT/types" "$PROJECT_ROOT/src/shared/types" "Type definitions"

echo ""
echo "📋 Phase 6: Moving documentation files..."

# Move root-level documentation to docs/
move_file "$PROJECT_ROOT/AI_DEPENDENCIES.md" "$PROJECT_ROOT/docs/development/ai-dependencies.md" "AI dependencies documentation"
move_file "$PROJECT_ROOT/ROBLOX_INTEGRATION_PLAN.md" "$PROJECT_ROOT/docs/development/roblox-integration-plan.md" "Roblox integration planning"

# Move status files to docs/status/
move_file "$PROJECT_ROOT/pyright_diagnostics_post_dashboard_fixes.json" "$PROJECT_ROOT/docs/status/pyright-diagnostics.json" "Pyright diagnostics status"

echo ""
echo "📋 Phase 7: Moving scripts and utilities..."

# Move utility scripts
move_file "$PROJECT_ROOT/fix-cursor.sh" "$PROJECT_ROOT/scripts/maintenance/fix-cursor.sh" "Cursor maintenance script"
move_file "$PROJECT_ROOT/check-lock-files.sh" "$PROJECT_ROOT/scripts/maintenance/check-lock-files.sh" "Lock file checking script"

echo ""
echo "📋 Phase 8: Moving test files..."

# Move test files
move_file "$PROJECT_ROOT/cursor_test.py" "$PROJECT_ROOT/tests/cursor_test.py" "Cursor testing script"
move_file "$PROJECT_ROOT/test_cursorpyright.py" "$PROJECT_ROOT/tests/test_cursorpyright.py" "Cursor Pyright testing"

# Move existing tests directory
if [[ -d "$PROJECT_ROOT/tests" && "$PROJECT_ROOT/tests" != "$PROJECT_ROOT/tests" ]]; then
    # Move contents of existing tests directory
    if [[ -d "$PROJECT_ROOT/tests/__pycache__" ]]; then
        rm -rf "$PROJECT_ROOT/tests/__pycache__"
    fi
    if [[ -f "$PROJECT_ROOT/tests/test_settings.py" ]]; then
        move_file "$PROJECT_ROOT/tests/test_settings.py" "$PROJECT_ROOT/tests/unit/test_settings.py" "Settings unit test"
    fi
fi

echo ""
echo "📋 Phase 9: Moving Roblox components..."

# Move Roblox components to appropriate location
if [[ -d "$PROJECT_ROOT/Roblox" ]]; then
    move_directory "$PROJECT_ROOT/Roblox" "$PROJECT_ROOT/src/roblox-environment/roblox-components" "Roblox components"
fi

echo ""
echo "✅ Structural reorganization completed!"
echo ""
echo "📊 Summary of reorganization:"
echo "   - Created new directory structure"
echo "   - Moved Roblox environment to src/roblox-environment/"
echo "   - Consolidated dashboard to src/dashboard/"
echo "   - Organized API components in src/api/"
echo "   - Moved shared utilities to src/shared/"
echo "   - Organized documentation in docs/"
echo "   - Moved scripts to scripts/"
echo "   - Organized tests in tests/"
echo ""
echo "🎯 Next steps:"
echo "   1. Update import paths and references"
echo "   2. Update configuration files"
echo "   3. Test project functionality"
echo "   4. Update documentation references"
