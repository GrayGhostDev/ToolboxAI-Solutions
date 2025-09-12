#!/bin/bash

echo "=== Service Status Monitor ==="
echo "Time: $(date)"
echo ""

# Check FastAPI
if curl -s http://127.0.0.1:8008/health > /dev/null; then
    echo "✅ FastAPI: Running on port 8008"
else
    echo "❌ FastAPI: Not responding on port 8008"
fi

# Check Flask Bridge
if curl -s http://127.0.0.1:5001/health > /dev/null; then
    echo "✅ Flask Bridge: Running on port 5001"
else
    echo "❌ Flask Bridge: Not responding on port 5001"
fi

# Check MCP
if lsof -iTCP:9876 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "✅ MCP Server: Running on port 9876"
else
    echo "❌ MCP Server: Not running on port 9876"
fi

# Check Dashboard
if curl -s http://127.0.0.1:5179 > /dev/null 2>&1; then
    echo "✅ Dashboard: Running on port 5179"
else
    echo "❌ Dashboard: Not responding on port 5179"
fi

# Check Database
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Accepting connections"
else
    echo "❌ PostgreSQL: Not accepting connections"
fi

echo ""
echo "=== Resource Usage ==="
echo "Memory: $(ps aux | grep -E "(python|node)" | awk '{sum+=$4} END {print sum "%"}')"
echo "CPU: $(ps aux | grep -E "(python|node)" | awk '{sum+=$3} END {print sum "%"}')"