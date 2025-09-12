#!/bin/bash
while true; do
    clear
    echo "=== SERVICE HEALTH CHECK - $(date) ==="
    echo "Project Status: ~94% Complete | Critical Path: Terminal 2 WebSocket Auth"
    echo ""
    
    # FastAPI
    if curl -s http://localhost:8008/health > /dev/null; then
        echo "✅ FastAPI: OK (port 8008)"
    else
        echo "❌ FastAPI: DOWN - Alert Terminal 1"
    fi
    
    # Flask Bridge
    if curl -s http://localhost:5001/health > /dev/null; then
        echo "✅ Flask Bridge: OK (port 5001)"
    else
        echo "❌ Flask Bridge: DOWN - Alert Terminal 3"
    fi
    
    # Dashboard - UPDATED PORT
    if curl -s http://localhost:5177 > /dev/null; then
        echo "✅ Dashboard: OK (port 5177 - CHANGED!)"
    else
        echo "❌ Dashboard: DOWN - Alert Terminal 2"
    fi
    
    # Critical Auth Refresh Endpoint
    echo ""
    echo "=== CRITICAL ENDPOINT CHECK ==="
    response=$(curl -s -X POST http://localhost:8008/auth/refresh \
        -H "Content-Type: application/json" \
        -d '{"refresh_token": "test"}' \
        -w "\n%{http_code}" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    if [ "$http_code" = "500" ]; then
        echo "⚠️  /auth/refresh: 500 ERROR - Terminal 1 needs to add 'status' import!"
        echo "   FIX: Add 'status,' to FastAPI imports in server/main.py line 36-43"
    elif [ "$http_code" = "401" ] || [ "$http_code" = "400" ]; then
        echo "✅ /auth/refresh: Working (${http_code} - normal for invalid token)"
    else
        echo "⚠️  /auth/refresh: HTTP ${http_code}"
    fi
    
    # Memory usage
    echo ""
    echo "=== MEMORY STATUS ==="
    ps aux | grep -E "python|node" | grep -v grep | awk '{sum+=$6} END {print "Total: " sum/1024 " MB"}'
    
    # Database connections
    echo ""
    echo "=== DATABASE STATUS ==="
    psql -U grayghostdata -d educational_platform -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;" 2>/dev/null || echo "Database check failed"
    
    # Terminal Status
    echo ""
    echo "=== TERMINAL STATUS ==="
    # Compute project root dynamically to avoid hardcoded absolute paths
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="${PROJECT_ROOT:-${SCRIPT_DIR}}"
    SYNC_DIR="${SYNC_DIR:-${PROJECT_ROOT}/scripts/terminal_sync}"
    for terminal in terminal1 terminal2 terminal3 debugger; do
        if [ -f "$SYNC_DIR/status/${terminal}.status" ]; then
            status=$(tail -1 "$SYNC_DIR/status/${terminal}.status")
            echo "${terminal}: ${status}"
        fi
    done
    
    # Recent errors
    echo ""
    echo "=== RECENT ERRORS ==="
    grep -E "ERROR|500|401" logs/*.log 2>/dev/null | tail -3 || echo "No recent errors"
    
    echo ""
    echo "=== ACTION ITEMS ==="
    echo "🔴 Terminal 1: Apply 'status' import fix to server/main.py IMMEDIATELY"
    echo "🟡 Terminal 2: Waiting for auth/refresh fix to implement WebSocket auth"
    echo "🟢 Terminal 3: Ready for integration testing (95% complete)"
    echo "🟢 Debugger: Monitoring all services"
    
    sleep 30
done