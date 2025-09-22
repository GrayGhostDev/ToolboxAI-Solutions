#!/bin/bash

# Patch the most critical MUI files for dashboard loading

BASE_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/node_modules/@mui"

# Critical files that need patching for dashboard to load
CRITICAL_FILES=(
    "system/styled.js"
    "system/ThemeProvider/ThemeProvider.js"
    "system/useTheme.js"
    "system/Box/Box.js"
    "system/Stack/Stack.js"
    "material/styles/createTheme.js"
    "material/styles/ThemeProvider.js"
    "material/styles/styled.js"
    "material/Button/Button.js"
    "material/Paper/Paper.js"
    "material/Typography/Typography.js"
    "material/AppBar/AppBar.js"
    "material/Box/Box.js"
    "material/Container/Container.js"
    "material/Grid/Grid.js"
)

patch_file() {
    local file_path="$BASE_DIR/$1"

    if [[ ! -f "$file_path" ]]; then
        echo "❌ File not found: $1"
        return 1
    fi

    if ! grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file_path"; then
        echo "⏭️  Already patched: $1"
        return 0
    fi

    # Create backup
    cp "$file_path" "$file_path.backup-$(date +%Y%m%d-%H%M%S)"

    # Apply patch
    sed -i '' 's/var _interopRequireDefault = require("@babel\/runtime\/helpers\/interopRequireDefault");/\/\/ Patched: Define _interopRequireDefault inline to fix ESM\/CommonJS issues\nvar _interopRequireDefault = function(obj) {\n  return obj \&\& obj.__esModule ? obj : { default: obj };\n};/' "$file_path"

    echo "✅ Patched: $1"
}

echo "🔧 Patching critical MUI files..."
echo ""

for file in "${CRITICAL_FILES[@]}"; do
    patch_file "$file"
done

echo ""
echo "🎉 Critical files patched!"
echo "💡 Test the dashboard now: cd apps/dashboard && npm run dev"