#!/bin/bash

echo "=== TERMINAL 1 VERIFICATION SCRIPT ==="
echo "Time: $(date)"
echo ""

# Check if processes are actually running
echo "🔍 PROCESS VERIFICATION:"
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "✅ FastAPI process found"
    ps aux | grep -E "uvicorn.*main:app" | grep -v grep
else
    echo "❌ FastAPI process NOT FOUND"
fi

if pgrep -f "flask.*run" > /dev/null; then
    echo "✅ Flask process found"
    ps aux | grep -E "flask.*run" | grep -v grep
else
    echo "❌ Flask process NOT FOUND"
fi

if pgrep -f "mcp.*server" > /dev/null; then
    echo "✅ MCP process found"
    ps aux | grep -E "mcp.*server" | grep -v grep
else
    echo "❌ MCP process NOT FOUND"
fi

echo ""
echo "🌐 SERVICE CONNECTIVITY:"

# Test actual connectivity
curl -s --max-time 5 http://127.0.0.1:8008/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ FastAPI responding on port 8008"
else
    echo "❌ FastAPI NOT responding on port 8008"
fi

curl -s --max-time 5 http://127.0.0.1:5001/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Flask responding on port 5001"
else
    echo "❌ Flask NOT responding on port 5001"
fi

# Test WebSocket
nc -z 127.0.0.1 9876 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ MCP WebSocket port 9876 open"
else
    echo "❌ MCP WebSocket port 9876 closed"
fi

echo ""
echo "🗄️  DATABASE VERIFICATION:"

# Test database connections with actual credentials from .env
psql -U eduplatform -d educational_platform_dev -h localhost -c "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Educational Platform DB accessible (eduplatform user)"
else
    echo "❌ Educational Platform DB NOT accessible (eduplatform user)"
    # Try the old credentials for comparison
    psql -U toolbox_edu -d educational_platform -h localhost -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "ℹ️  Old toolbox_edu credentials still work - database migration incomplete"
    fi
fi

# Test the unified database approach
psql -U eduplatform -d educational_platform_dev -h localhost -c "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Unified Database accessible (eduplatform user)"
    # Get table count for verification
    TABLE_COUNT=$(psql -U eduplatform -d educational_platform_dev -h localhost -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    echo "ℹ️  Found $TABLE_COUNT tables in educational_platform_dev"
else
    echo "❌ Unified Database NOT accessible (eduplatform user)"
fi

echo ""
echo "📊 RESOURCE USAGE:"
echo "Memory usage: $(ps aux | grep -E "(python|uvicorn|flask)" | grep -v grep | awk '{sum+=$4} END {print sum "%"}' || echo "0%")"
echo "CPU usage: $(ps aux | grep -E "(python|uvicorn|flask)" | grep -v grep | awk '{sum+=$3} END {print sum "%"}' || echo "0%")"

echo ""
echo "🔧 RECOMMENDATION:"
if ! pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "❌ TERMINAL 1 NOT ACTUALLY COMPLETE - Services are down"
    echo "   Need to restart FastAPI, Flask, and MCP servers"
else
    echo "✅ TERMINAL 1 appears operational"
fi
