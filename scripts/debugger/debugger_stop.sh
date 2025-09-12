#!/usr/bin/env sh
# shellcheck shell=sh
set -eu
# shellcheck source=../common/lib.sh
. "$(cd "$(dirname "$0")"/.. && pwd -P)/common/lib.sh" 2>/dev/null || true
# Debugger Terminal - Stop Script
# Gracefully stops all debugger monitoring processes

echo "🛑 Stopping Debugger Terminal Monitoring..."
echo "=========================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SYNC_DIR="$PROJECT_ROOT/scripts/terminal_sync"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to stop a process
stop_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -n "  Stopping $process_name (PID: $PID)..."
            kill $PID 2>/dev/null
            sleep 2
            
            # Check if process stopped
            if ps -p $PID > /dev/null 2>&1; then
                echo -e " ${YELLOW}Force killing...${NC}"
                kill -9 $PID 2>/dev/null
            else
                echo -e " ${GREEN}✅ Stopped${NC}"
            fi
        else
            echo -e "  ${YELLOW}$process_name not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "  ${YELLOW}No PID file for $process_name${NC}"
    fi
}

# Stop monitoring processes
echo "Stopping monitoring processes..."
stop_process "$SYNC_DIR/pids/security_monitor.pid" "Security Monitor"
stop_process "$SYNC_DIR/pids/performance_monitor.pid" "Performance Monitor"
stop_process "$SYNC_DIR/pids/alert_orchestrator.pid" "Alert Orchestrator"

# Also try to stop by process name (in case PID files are missing)
echo ""
echo "Cleaning up any remaining processes..."
pkill -f debugger_security_monitor.py 2>/dev/null && echo -e "  ${GREEN}✅ Stopped security monitor by name${NC}"
pkill -f debugger_performance.py 2>/dev/null && echo -e "  ${GREEN}✅ Stopped performance monitor by name${NC}"
pkill -f debugger_alerts.py 2>/dev/null && echo -e "  ${GREEN}✅ Stopped alert orchestrator by name${NC}"

# Update status file
echo ""
echo "Updating status..."
cat > "$SYNC_DIR/status/debugger.json" << EOF
{
    "terminal": "debugger",
    "status": "stopped",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "components": {
        "security_monitor": "stopped",
        "performance_monitor": "stopped",
        "alert_orchestrator": "stopped"
    },
    "monitoring": {
        "terminals": [],
        "metrics_collection": "inactive",
        "alert_processing": "inactive",
        "security_scanning": "inactive"
    }
}
EOF

echo -e "${GREEN}✅ Status updated${NC}"

# Generate final report
echo ""
echo "📊 Generating final report..."
if [ -f "$SYNC_DIR/alerts/history.json" ]; then
    ALERT_COUNT=$(cat "$SYNC_DIR/alerts/history.json" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "  Total alerts processed: $ALERT_COUNT"
fi

if [ -f "$SYNC_DIR/status/security_report.json" ]; then
    cat "$SYNC_DIR/status/security_report.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    v = data.get('vulnerabilities', {})
    total = sum(v.values())
    print(f'  Total vulnerabilities found: {total}')
    if total > 0:
        print(f'    Critical: {v.get(\"critical\", 0)}')
        print(f'    High: {v.get(\"high\", 0)}')
        print(f'    Medium: {v.get(\"medium\", 0)}')
        print(f'    Low: {v.get(\"low\", 0)}')
except:
    pass
"
fi

echo ""
echo "════════════════════════════════════════"
echo -e "${GREEN}✅ Debugger Terminal stopped successfully${NC}"
echo "════════════════════════════════════════"
echo ""
echo "To restart monitoring, run:"
echo "  bash scripts/debugger_start.sh"