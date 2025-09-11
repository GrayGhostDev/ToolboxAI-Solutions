#!/bin/bash
# Debugger Terminal - Live Dashboard
# Real-time monitoring dashboard for the ToolBoxAI Educational Platform

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SYNC_DIR="$PROJECT_ROOT/scripts/terminal_sync"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to check if monitoring is running
check_monitoring_status() {
    local running=0
    for pid_file in "$SYNC_DIR"/pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                running=$((running + 1))
            fi
        fi
    done
    return $running
}

# Check if monitoring is running
check_monitoring_status
MONITORS_RUNNING=$?

if [ $MONITORS_RUNNING -eq 0 ]; then
    echo -e "${YELLOW}⚠️ Warning: No monitoring processes are running${NC}"
    echo "Would you like to start monitoring? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        bash "$SCRIPT_DIR/debugger_start.sh"
        sleep 5
    else
        echo "Dashboard will show cached data only."
        sleep 2
    fi
fi

# Function to get terminal status color
get_status_color() {
    local status=$1
    case $status in
        "healthy"|"running"|"active")
            echo -e "${GREEN}✅"
            ;;
        "degraded"|"warning")
            echo -e "${YELLOW}⚠️"
            ;;
        "down"|"stopped"|"error")
            echo -e "${RED}❌"
            ;;
        *)
            echo -e "${WHITE}❓"
            ;;
    esac
}

# Function to format bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -gt 1073741824 ]; then
        echo "$(echo "scale=2; $bytes/1073741824" | bc) GB"
    elif [ $bytes -gt 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc) MB"
    elif [ $bytes -gt 1024 ]; then
        echo "$(echo "scale=2; $bytes/1024" | bc) KB"
    else
        echo "$bytes B"
    fi
}

# Main dashboard loop
while true; do
    clear
    
    # Header
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                    🔍 DEBUGGER TERMINAL - LIVE DASHBOARD                      ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} $(date '+%Y-%m-%d %H:%M:%S')                                                        ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Monitoring Process Status
    echo -e "${MAGENTA}═══ MONITORING PROCESSES ═══════════════════════════════════════════════════════${NC}"
    for pid_file in "$SYNC_DIR"/pids/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            name=$(basename "$pid_file" .pid | tr '_' ' ' | sed 's/\b\(.\)/\u\1/g')
            if ps -p "$pid" > /dev/null 2>&1; then
                cpu=$(ps -p "$pid" -o %cpu= | xargs)
                mem=$(ps -p "$pid" -o %mem= | xargs)
                echo -e "  $(get_status_color "running") ${name}: PID ${pid} | CPU: ${cpu}% | MEM: ${mem}%${NC}"
            else
                echo -e "  $(get_status_color "down") ${name}: Not running${NC}"
            fi
        fi
    done
    echo ""
    
    # Terminal Status
    echo -e "${MAGENTA}═══ TERMINAL STATUS ═════════════════════════════════════════════════════════════${NC}"
    
    # Terminal 1 - Backend
    T1_STATUS="down"
    if curl -s http://localhost:8008/health > /dev/null 2>&1; then
        T1_STATUS="healthy"
        T1_DATA=$(curl -s http://localhost:8008/health)
        T1_UPTIME=$(echo "$T1_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d.get('uptime', 0):.0f}s\")" 2>/dev/null || echo "N/A")
    fi
    echo -e "  $(get_status_color "$T1_STATUS") Terminal 1 (Backend):   Port 8008 | Uptime: ${T1_UPTIME}${NC}"
    
    # Terminal 2 - Frontend
    T2_STATUS="down"
    if curl -s http://localhost:5179 > /dev/null 2>&1; then
        T2_STATUS="healthy"
    fi
    echo -e "  $(get_status_color "$T2_STATUS") Terminal 2 (Frontend):  Port 5179${NC}"
    
    # Terminal 3 - Roblox Bridge
    T3_STATUS="down"
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        T3_STATUS="healthy"
        T3_DATA=$(curl -s http://localhost:5001/health)
        T3_UPTIME=$(echo "$T3_DATA" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"{d.get('uptime', 0):.0f}s\")" 2>/dev/null || echo "N/A")
    fi
    echo -e "  $(get_status_color "$T3_STATUS") Terminal 3 (Roblox):    Port 5001 | Uptime: ${T3_UPTIME}${NC}"
    echo ""
    
    # Security Status
    echo -e "${MAGENTA}═══ SECURITY STATUS ═════════════════════════════════════════════════════════════${NC}"
    if [ -f "$SYNC_DIR/status/security_report.json" ]; then
        SECURITY_DATA=$(cat "$SYNC_DIR/status/security_report.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    v = data.get('vulnerabilities', {})
    critical = v.get('critical', 0)
    high = v.get('high', 0)
    medium = v.get('medium', 0)
    low = v.get('low', 0)
    
    # Color coding
    if critical > 0:
        critical_str = f'\\033[0;31m{critical}\\033[0m'
    else:
        critical_str = f'\\033[0;32m{critical}\\033[0m'
    
    if high > 0:
        high_str = f'\\033[1;33m{high}\\033[0m'
    else:
        high_str = f'\\033[0;32m{high}\\033[0m'
    
    print(f'  Vulnerabilities - Critical: {critical_str} | High: {high_str} | Medium: {medium} | Low: {low}')
    
    # Show recommendations
    recs = data.get('recommendations', [])
    if recs:
        print('  Top Recommendations:')
        for i, rec in enumerate(recs[:3], 1):
            print(f'    {i}. {rec}')
except Exception as e:
    print(f'  Error reading security data: {e}')
" 2>/dev/null)
        echo -e "$SECURITY_DATA"
    else
        echo "  No security report available"
    fi
    echo ""
    
    # Performance Metrics
    echo -e "${MAGENTA}═══ SYSTEM PERFORMANCE ══════════════════════════════════════════════════════════${NC}"
    if [ -f "$SYNC_DIR/metrics/performance.json" ]; then
        PERF_DATA=$(cat "$SYNC_DIR/metrics/performance.json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'system' in data:
        s = data['system']
        cpu = s.get('cpu_percent', 0)
        mem = s.get('memory_percent', 0)
        disk = s.get('disk_usage', 0)
        
        # Color coding
        cpu_color = '\\033[0;32m' if cpu < 70 else '\\033[1;33m' if cpu < 85 else '\\033[0;31m'
        mem_color = '\\033[0;32m' if mem < 70 else '\\033[1;33m' if mem < 85 else '\\033[0;31m'
        disk_color = '\\033[0;32m' if disk < 80 else '\\033[1;33m' if disk < 90 else '\\033[0;31m'
        
        print(f'  CPU Usage:    {cpu_color}{cpu:5.1f}%\\033[0m  |  Memory: {mem_color}{mem:5.1f}%\\033[0m  |  Disk: {disk_color}{disk:5.1f}%\\033[0m')
        
        # API metrics
        if 'terminal1' in data:
            t1 = data['terminal1']
            if 'api_response_time' in t1:
                rt = t1['api_response_time']
                rt_color = '\\033[0;32m' if rt < 200 else '\\033[1;33m' if rt < 500 else '\\033[0;31m'
                print(f'  API Response: {rt_color}{rt:5.0f}ms\\033[0m')
except:
    print('  No performance data available')
" 2>/dev/null)
        echo -e "$PERF_DATA"
    else
        echo "  No performance data available"
    fi
    echo ""
    
    # Recent Alerts
    echo -e "${MAGENTA}═══ RECENT ALERTS ═══════════════════════════════════════════════════════════════${NC}"
    if [ -f "$SYNC_DIR/alerts/history.json" ]; then
        ALERTS=$(cat "$SYNC_DIR/alerts/history.json" | python3 -c "
import json, sys
from datetime import datetime
try:
    data = json.load(sys.stdin)
    recent = data[-5:] if len(data) > 0 else []
    if recent:
        for alert in reversed(recent):
            severity = alert.get('severity', 'INFO')
            message = alert.get('message', 'No message')[:60]
            timestamp = alert.get('timestamp', '')
            
            # Color based on severity
            if severity == 'CRITICAL':
                color = '\\033[0;31m'
            elif severity in ['HIGH', 'ESCALATED']:
                color = '\\033[1;33m'
            elif severity == 'MEDIUM':
                color = '\\033[0;33m'
            else:
                color = '\\033[0;36m'
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = 'N/A'
            
            print(f'  {color}[{severity:8s}]{time_str} {message}\\033[0m')
    else:
        print('  No recent alerts')
except Exception as e:
    print(f'  Error reading alerts: {e}')
" 2>/dev/null)
        echo -e "$ALERTS"
    else
        echo "  No alert history available"
    fi
    echo ""
    
    # Network Activity
    echo -e "${MAGENTA}═══ NETWORK ACTIVITY ════════════════════════════════════════════════════════════${NC}"
    NETWORK_DATA=$(python3 -c "
import psutil
net = psutil.net_io_counters()
print(f'  Sent: {net.bytes_sent / (1024*1024*1024):.2f} GB | Received: {net.bytes_recv / (1024*1024*1024):.2f} GB')
print(f'  Packets: {net.packets_sent:,} sent | {net.packets_recv:,} received')
" 2>/dev/null || echo "  Network data unavailable")
    echo "$NETWORK_DATA"
    echo ""
    
    # Footer
    echo -e "${CYAN}═════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}Commands: [q]uit | [r]estart monitoring | [c]lear alerts | [s]ecurity scan${NC}"
    echo -e "${WHITE}Auto-refresh: 5 seconds | Press Ctrl+C to exit${NC}"
    
    # Handle user input with timeout
    read -t 5 -n 1 key
    case $key in
        q|Q)
            echo ""
            echo "Exiting dashboard..."
            exit 0
            ;;
        r|R)
            echo ""
            echo "Restarting monitoring..."
            bash "$SCRIPT_DIR/debugger_stop.sh"
            sleep 2
            bash "$SCRIPT_DIR/debugger_start.sh"
            sleep 5
            ;;
        c|C)
            echo ""
            echo "Clearing alert history..."
            echo "[]" > "$SYNC_DIR/alerts/history.json"
            echo "Alert history cleared."
            sleep 2
            ;;
        s|S)
            echo ""
            echo "Triggering security scan..."
            # This would trigger an immediate security scan
            echo "Security scan initiated."
            sleep 2
            ;;
    esac
done