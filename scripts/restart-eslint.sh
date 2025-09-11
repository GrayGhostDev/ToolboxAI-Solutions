#!/bin/bash

# Script to restart ESLint server in VS Code/Cursor

echo "🔄 Restarting ESLint server..."

# Clear ESLint cache
rm -rf .eslintcache node_modules/.cache/eslint-loader 2>/dev/null

# Kill any existing ESLint processes (for VS Code/Cursor)
pkill -f "eslint" 2>/dev/null || true

echo "✅ ESLint cache cleared"
echo ""
echo "📝 To complete the restart in VS Code/Cursor:"
echo "   1. Open Command Palette (Cmd+Shift+P)"
echo "   2. Run: 'ESLint: Restart ESLint Server'"
echo ""
echo "Or reload the window:"
echo "   - VS Code/Cursor: Cmd+R or 'Developer: Reload Window'"
echo ""
echo "✨ ESLint configuration has been updated for ESLint 9 with TypeScript support!"