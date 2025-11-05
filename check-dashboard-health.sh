#!/bin/bash

# Dashboard Health Check Script
# Tests if the dashboard is loading correctly

echo "🔍 Dashboard Health Check"
echo "========================"
echo ""

# Check if server is running
echo "1. Checking if server is running..."
if lsof -i:5179 >/dev/null 2>&1; then
    echo "   ✅ Server is running on port 5179"
else
    echo "   ❌ Server is NOT running"
    exit 1
fi
echo ""

# Check if page responds
echo "2. Checking if page responds..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5179)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Page responds with HTTP 200"
else
    echo "   ❌ Page responds with HTTP $HTTP_CODE"
    exit 1
fi
echo ""

# Check if main.tsx is referenced
echo "3. Checking if main.tsx is loaded..."
if curl -s http://localhost:5179 | grep -q "main.tsx"; then
    echo "   ✅ main.tsx is referenced in HTML"
else
    echo "   ⚠️  main.tsx not found in HTML (may use different entry)"
fi
echo ""

# Check Vite version
echo "4. Checking Vite version..."
VITE_VERSION=$(cat node_modules/vite/package.json 2>/dev/null | grep '"version"' | cut -d'"' -f4)
PLUGIN_VERSION=$(cat node_modules/@vitejs/plugin-react/package.json 2>/dev/null | grep '"version"' | cut -d'"' -f4)
echo "   Vite: $VITE_VERSION"
echo "   Plugin: $PLUGIN_VERSION"

if [ "$VITE_VERSION" = "5.4.21" ] && [ "$PLUGIN_VERSION" = "4.3.4" ]; then
    echo "   ✅ Correct versions installed"
else
    echo "   ⚠️  Version mismatch detected"
fi
echo ""

# Summary
echo "========================"
echo "✅ Dashboard Health Check PASSED"
echo ""
echo "Dashboard is accessible at:"
echo "   http://localhost:5179"
echo ""
echo "To verify in browser:"
echo "1. Open http://localhost:5179"
echo "2. Open DevTools Console (F12)"
echo "3. Check for errors"
echo ""

