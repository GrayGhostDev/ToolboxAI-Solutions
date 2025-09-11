#!/bin/bash
# Debugger Terminal - System Monitor Startup Script
# Part of the ToolBoxAI Educational Platform

echo "🔍 Debugger Terminal - System Monitor Startup"
echo "============================================="
echo "Starting at: $(date)"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SYNC_DIR="$PROJECT_ROOT/scripts/terminal_sync"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p "$SYNC_DIR"/{status,messages,metrics,alerts}
mkdir -p "$PROJECT_ROOT/incidents"
mkdir -p "$PROJECT_ROOT/security_reports"

# Function to check if a service is running
check_service() {
    local service_name=$1
    local url=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name: Connected${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ $service_name: Not responding${NC}"
        return 1
    fi
}

# Check Python environment
echo ""
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python3 found: $(python3 --version)${NC}"
else
    echo -e "${RED}❌ Python3 not found!${NC}"
    exit 1
fi

# Check Redis
echo ""
echo "🔗 Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis: Connected${NC}"
else
    echo -e "${YELLOW}⚠️ Redis: Not running (alerts will use file-based fallback)${NC}"
fi

# Check all terminals
echo ""
echo "🔍 Verifying all terminals..."
check_service "Terminal 1 (Backend)" "http://localhost:8008/health"
T1_STATUS=$?
check_service "Terminal 2 (Frontend)" "http://localhost:5179"
T2_STATUS=$?
check_service "Terminal 3 (Roblox)" "http://localhost:5001/health"
T3_STATUS=$?

# Start monitoring components
echo ""
echo "🚀 Starting monitoring components..."

# Kill any existing monitoring processes
echo "  Cleaning up existing processes..."
pkill -f debugger_security_monitor.py 2>/dev/null
pkill -f debugger_performance.py 2>/dev/null
pkill -f debugger_alerts.py 2>/dev/null
sleep 2

# Start Security Monitor
echo ""
echo "🛡️ Starting Security Monitor..."
cd "$PROJECT_ROOT"
python3 scripts/debugger_security_monitor.py > "$SYNC_DIR/logs/security.log" 2>&1 &
SECURITY_PID=$!
echo "  PID: $SECURITY_PID"

# Wait a bit for initialization
sleep 2

# Start Performance Monitor
echo "📊 Starting Performance Monitor..."
python3 scripts/debugger_performance.py > "$SYNC_DIR/logs/performance.log" 2>&1 &
PERFORMANCE_PID=$!
echo "  PID: $PERFORMANCE_PID"

# Wait a bit for initialization
sleep 2

# Start Alert Orchestrator
echo "🔔 Starting Alert Orchestrator..."
python3 scripts/debugger_alerts.py > "$SYNC_DIR/logs/alerts.log" 2>&1 &
ALERT_PID=$!
echo "  PID: $ALERT_PID"

# Wait for components to initialize
echo ""
echo "⏳ Waiting for components to initialize..."
sleep 5

# Verify all monitoring components are running
echo ""
echo "🔍 Verifying monitoring components..."
if ps -p $SECURITY_PID > /dev/null; then
    echo -e "${GREEN}✅ Security Monitor: Running (PID: $SECURITY_PID)${NC}"
else
    echo -e "${RED}❌ Security Monitor: Failed to start${NC}"
fi

if ps -p $PERFORMANCE_PID > /dev/null; then
    echo -e "${GREEN}✅ Performance Monitor: Running (PID: $PERFORMANCE_PID)${NC}"
else
    echo -e "${RED}❌ Performance Monitor: Failed to start${NC}"
fi

if ps -p $ALERT_PID > /dev/null; then
    echo -e "${GREEN}✅ Alert Orchestrator: Running (PID: $ALERT_PID)${NC}"
else
    echo -e "${RED}❌ Alert Orchestrator: Failed to start${NC}"
fi

# Save process IDs
echo "$SECURITY_PID" > "$SYNC_DIR/pids/security_monitor.pid"
echo "$PERFORMANCE_PID" > "$SYNC_DIR/pids/performance_monitor.pid"
echo "$ALERT_PID" > "$SYNC_DIR/pids/alert_orchestrator.pid"

# Update debugger status
cat > "$SYNC_DIR/status/debugger.json" << EOF
{
    "terminal": "debugger",
    "status": "monitoring_active",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "components": {
        "security_monitor": $SECURITY_PID,
        "performance_monitor": $PERFORMANCE_PID,
        "alert_orchestrator": $ALERT_PID
    },
    "monitoring": {
        "terminals": ["terminal1", "terminal2", "terminal3"],
        "metrics_collection": "active",
        "alert_processing": "active",
        "security_scanning": "active"
    },
    "terminal_status": {
        "terminal1": $([ $T1_STATUS -eq 0 ] && echo '"healthy"' || echo '"down"'),
        "terminal2": $([ $T2_STATUS -eq 0 ] && echo '"healthy"' || echo '"down"'),
        "terminal3": $([ $T3_STATUS -eq 0 ] && echo '"healthy"' || echo '"down"')
    }
}
EOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Debugger Terminal ready and monitoring${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Monitor Status:"
echo "  • Security Scanner: Active"
echo "  • Performance Metrics: Collecting"
echo "  • Alert Processing: Enabled"
echo ""
echo "📝 Log Files:"
echo "  • Security: $SYNC_DIR/logs/security.log"
echo "  • Performance: $SYNC_DIR/logs/performance.log"
echo "  • Alerts: $SYNC_DIR/logs/alerts.log"
echo ""
echo "🔧 Commands:"
echo "  • View status: cat $SYNC_DIR/status/debugger.json"
echo "  • Stop monitoring: bash scripts/debugger_stop.sh"
echo "  • View live dashboard: bash scripts/debugger_dashboard.sh"
echo ""
echo "Press Ctrl+C to stop monitoring (processes will continue in background)"
echo ""

# Function to display live status
show_live_status() {
    while true; do
        clear
        echo "═══════════════════════════════════════════════════════════════"
        echo "             🔍 DEBUGGER TERMINAL - LIVE MONITOR"
        echo "═══════════════════════════════════════════════════════════════"
        echo "Time: $(date)"
        echo ""
        
        # Security Status
        echo "🛡️ SECURITY STATUS:"
        if [ -f "$SYNC_DIR/status/security_report.json" ]; then
            cat "$SYNC_DIR/status/security_report.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    v = data.get('vulnerabilities', {})
    print(f'  Critical: {v.get(\"critical\", 0)} | High: {v.get(\"high\", 0)} | Medium: {v.get(\"medium\", 0)} | Low: {v.get(\"low\", 0)}')
except:
    print('  No security data available')
"
        else
            echo "  No security report available"
        fi
        
        # Performance Status
        echo ""
        echo "📊 PERFORMANCE STATUS:"
        if [ -f "$SYNC_DIR/metrics/performance.json" ]; then
            cat "$SYNC_DIR/metrics/performance.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'system' in data:
        s = data['system']
        print(f'  CPU: {s.get(\"cpu_percent\", 0):.1f}% | Memory: {s.get(\"memory_percent\", 0):.1f}% | Disk: {s.get(\"disk_usage\", 0):.1f}%')
except:
    print('  No performance data available')
"
        else
            echo "  No performance data available"
        fi
        
        # Terminal Status
        echo ""
        echo "🔗 TERMINAL STATUS:"
        for terminal in terminal1 terminal2 terminal3; do
            if [ -f "$SYNC_DIR/status/$terminal.json" ]; then
                status=$(cat "$SYNC_DIR/status/$terminal.json" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
                echo "  $terminal: $status"
            else
                echo "  $terminal: no status file"
            fi
        done
        
        # Recent Alerts
        echo ""
        echo "🚨 RECENT ALERTS:"
        if [ -f "$SYNC_DIR/alerts/history.json" ]; then
            cat "$SYNC_DIR/alerts/history.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    recent = data[-5:] if len(data) > 0 else []
    if recent:
        for alert in recent:
            print(f'  [{alert.get(\"severity\", \"INFO\")}] {alert.get(\"message\", \"No message\")[:50]}')
    else:
        print('  No recent alerts')
except:
    print('  No alert data available')
"
        else
            echo "  No recent alerts"
        fi
        
        # Process Status
        echo ""
        echo "⚙️ MONITORING PROCESSES:"
        for pid_file in "$SYNC_DIR"/pids/*.pid; do
            if [ -f "$pid_file" ]; then
                pid=$(cat "$pid_file")
                name=$(basename "$pid_file" .pid)
                if ps -p "$pid" > /dev/null 2>&1; then
                    echo -e "  ${GREEN}✅ $name (PID: $pid)${NC}"
                else
                    echo -e "  ${RED}❌ $name (PID: $pid - not running)${NC}"
                fi
            fi
        done
        
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "Press Ctrl+C to exit monitoring"
        
        sleep 5
    done
}

# Trap to handle Ctrl+C
trap 'echo -e "\n${YELLOW}Monitoring continues in background. Use debugger_stop.sh to stop all processes.${NC}"; exit 0' INT

# Ask if user wants to see live dashboard
echo -n "Show live monitoring dashboard? (y/n): "
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    show_live_status
else
    echo ""
    echo "Monitoring is running in the background."
    echo "Use 'bash scripts/debugger_dashboard.sh' to view live status."
fi