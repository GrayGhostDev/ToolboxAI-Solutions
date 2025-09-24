#!/bin/bash

# Simple MUI _interopRequireDefault Fix Script
# This script patches all MUI files that use the problematic require statement

set -e

BASE_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
MUI_DIR="$BASE_DIR/node_modules/@mui"

echo "🔧 MUI _interopRequireDefault Patcher"
echo "======================================"
echo ""

# Function to patch a single file
patch_file() {
    local file="$1"
    local relative_path="${file#$MUI_DIR/}"

    # Check if file contains the problematic require
    if ! grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
        echo "⏭️  Already patched: $relative_path"
        return 0
    fi

    # Create backup
    cp "$file" "$file.backup-$(date +%Y%m%d-%H%M%S)"

    # Apply patch
    sed -i '' 's/var _interopRequireDefault = require("@babel\/runtime\/helpers\/interopRequireDefault");/\/\/ Patched: Define _interopRequireDefault inline to fix ESM\/CommonJS issues\nvar _interopRequireDefault = function(obj) {\n  return obj \&\& obj.__esModule ? obj : { default: obj };\n};/' "$file"

    echo "✅ Patched: $relative_path"
    return 0
}

echo "🔍 Finding and patching files..."
echo ""

# Counter
count=0

# Find and patch @mui/system files
if [ -d "$MUI_DIR/system" ]; then
    echo "📦 Processing @mui/system..."
    find "$MUI_DIR/system" -name "*.js" -type f | while read file; do
        if grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
            patch_file "$file"
            count=$((count + 1))
        fi
    done
fi

# Find and patch @mui/material files
if [ -d "$MUI_DIR/material" ]; then
    echo "📦 Processing @mui/material..."
    find "$MUI_DIR/material" -name "*.js" -type f | while read file; do
        if grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
            patch_file "$file"
            count=$((count + 1))
        fi
    done
fi

# Find and patch @mui/base files
if [ -d "$MUI_DIR/base" ]; then
    echo "📦 Processing @mui/base..."
    find "$MUI_DIR/base" -name "*.js" -type f | while read file; do
        if grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
            patch_file "$file"
            count=$((count + 1))
        fi
    done
fi

# Find and patch @mui/styled-engine files
if [ -d "$MUI_DIR/styled-engine" ]; then
    echo "📦 Processing @mui/styled-engine..."
    find "$MUI_DIR/styled-engine" -name "*.js" -type f | while read file; do
        if grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
            patch_file "$file"
            count=$((count + 1))
        fi
    done
fi

echo ""
echo "🎉 Patching completed!"
echo ""
echo "💡 Next steps:"
echo "   1. Test your dashboard: cd apps/dashboard && npm run dev"
echo "   2. Check browser console for any remaining errors"
echo "   3. Backup files saved with timestamp for rollback if needed"
echo ""