#!/bin/bash

# ToolBoxAI-Solutions Nested Structure Fix Script
# Fixes the nested ToolboxAI-Roblox-Environment structure

set -e

# Determine project root dynamically (allow override)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

echo "🔧 Fixing nested structure issue..."
echo "Project root: $PROJECT_ROOT"

# Check if the nested structure exists in roblox-environment
if [[ -d "$PROJECT_ROOT/src/roblox-environment/ToolboxAI-Roblox-Environment" ]]; then
    echo "📁 Found nested structure in roblox-environment, flattening..."
    
    # Move contents from nested directory to parent
    echo "📦 Moving contents from nested directory..."
    mv "$PROJECT_ROOT/src/roblox-environment/ToolboxAI-Roblox-Environment"/* "$PROJECT_ROOT/src/roblox-environment/" 2>/dev/null || true
    
    # Remove the now-empty nested directory
    echo "🗑️  Removing empty nested directory..."
    rmdir "$PROJECT_ROOT/src/roblox-environment/ToolboxAI-Roblox-Environment" 2>/dev/null || true
    
    echo "✅ Roblox environment nested structure fixed!"
else
    echo "✅ No nested structure found in roblox-environment, structure is correct"
fi

# Check if the nested structure exists in dashboard
if [[ -d "$PROJECT_ROOT/src/dashboard/ToolboxAI-Dashboard" ]]; then
    echo "📁 Found nested structure in dashboard, flattening..."
    
    # Move contents from nested directory to parent
    echo "📦 Moving contents from nested directory..."
    mv "$PROJECT_ROOT/src/dashboard/ToolboxAI-Dashboard"/* "$PROJECT_ROOT/src/dashboard/" 2>/dev/null || true
    
    # Remove the now-empty nested directory
    echo "🗑️  Removing empty nested directory..."
    rmdir "$PROJECT_ROOT/src/dashboard/ToolboxAI-Dashboard" 2>/dev/null || true
    
    echo "✅ Dashboard nested structure fixed!"
else
    echo "✅ No nested structure found in dashboard, structure is correct"
fi

# Verify the virtual environment is in the right place
if [[ -d "$PROJECT_ROOT/src/roblox-environment/venv_clean" ]]; then
    echo "✅ Virtual environment is in correct location: src/roblox-environment/venv_clean"
else
    echo "⚠️  Virtual environment not found in expected location"
fi

# List the contents to verify
echo ""
echo "📋 Current src/roblox-environment/ contents:"
ls -la "$PROJECT_ROOT/src/roblox-environment/"

echo ""
echo "✅ Structure fix completed!"
