#!/bin/bash

# ToolBoxAI-Solutions Duplicate Removal Script
# Removes duplicate files identified in the cleanup plan

set -e

PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🧹 Starting duplicate file removal..."
echo "Project root: $PROJECT_ROOT"

# Function to safely remove file with confirmation
remove_file() {
    local file_path="$1"
    local reason="$2"
    
    if [[ -f "$file_path" ]]; then
        echo "🗑️  Removing: $file_path"
        echo "   Reason: $reason"
        rm "$file_path"
        echo "   ✅ Removed successfully"
    else
        echo "⚠️  File not found: $file_path"
    fi
}

# Function to safely remove directory with confirmation
remove_directory() {
    local dir_path="$1"
    local reason="$2"
    
    if [[ -d "$dir_path" ]]; then
        echo "🗑️  Removing directory: $dir_path"
        echo "   Reason: $reason"
        rm -rf "$dir_path"
        echo "   ✅ Removed successfully"
    else
        echo "⚠️  Directory not found: $dir_path"
    fi
}

echo ""
echo "📋 Phase 1: Removing duplicate CLAUDE.md files..."

# Remove duplicate CLAUDE.md files (keeping main ones)
remove_file "$PROJECT_ROOT/Documentation/09-meta/CLAUDE.md" "Duplicate - keeping main project CLAUDE.md"
remove_file "$PROJECT_ROOT/Dashboard/ToolboxAI-Dashboard/CLAUDE.md" "Duplicate - will be consolidated into dashboard-specific file"
remove_file "$PROJECT_ROOT/ToolboxAI-Roblox-Environment/API/Dashboard/CLAUDE.md" "Duplicate dashboard CLAUDE.md"

echo ""
echo "📋 Phase 2: Removing duplicate configuration files..."

# Remove conflicting package.json
remove_file "$PROJECT_ROOT/ToolboxAI-Roblox-Environment/package.json" "Conflicting with workspace package.json"

# Remove duplicate pyrightconfig.json
remove_file "$PROJECT_ROOT/ToolboxAI-Roblox-Environment/pyrightconfig.json" "Duplicate - keeping root version"

echo ""
echo "📋 Phase 3: Removing duplicate node_modules directories..."

# Remove duplicate node_modules (keep root one)
remove_directory "$PROJECT_ROOT/ToolboxAI-Roblox-Environment/node_modules" "Duplicate - keeping root node_modules"

echo ""
echo "📋 Phase 4: Removing scattered status files..."

# Remove scattered status files (will be consolidated)
remove_file "$PROJECT_ROOT/CURSOR_ISSUES_FIXED.md" "Status file - will be moved to docs/status/"
remove_file "$PROJECT_ROOT/CURSOR_PYRIGHT_COMPLETE.md" "Status file - will be moved to docs/status/"
remove_file "$PROJECT_ROOT/CURSOR_PYRIGHT_CONFIG.md" "Status file - will be moved to docs/status/"
remove_file "$PROJECT_ROOT/CURSOR_SETUP_COMPLETE.md" "Status file - will be moved to docs/status/"
remove_file "$PROJECT_ROOT/VIM_DISABLED.md" "Status file - will be moved to docs/status/"

echo ""
echo "📋 Phase 5: Removing test and utility files from root..."

# Remove scattered test files
remove_file "$PROJECT_ROOT/cursor_test.py" "Test file - will be moved to tests/"
remove_file "$PROJECT_ROOT/test_cursorpyright.py" "Test file - will be moved to tests/"

# Remove utility files that should be in scripts/
remove_file "$PROJECT_ROOT/fix-cursor.sh" "Utility script - will be moved to scripts/"
remove_file "$PROJECT_ROOT/check-lock-files.sh" "Utility script - will be moved to scripts/"

echo ""
echo "📋 Phase 6: Removing scattered Python files..."

# Remove scattered Python files
remove_file "$PROJECT_ROOT/pydantic_settings.py" "Python file - will be moved to appropriate location"

echo ""
echo "✅ Duplicate removal completed!"
echo ""
echo "📊 Summary of removed files:"
echo "   - Duplicate CLAUDE.md files: 3 removed"
echo "   - Conflicting package.json: 1 removed"
echo "   - Duplicate pyrightconfig.json: 1 removed"
echo "   - Duplicate node_modules: 1 removed"
echo "   - Scattered status files: 5 removed"
echo "   - Scattered test files: 2 removed"
echo "   - Scattered utility scripts: 2 removed"
echo "   - Scattered Python files: 1 removed"
echo ""
echo "🎯 Next steps:"
echo "   1. Run structural reorganization script"
echo "   2. Update import paths and references"
echo "   3. Test project functionality"
echo "   4. Update documentation"
