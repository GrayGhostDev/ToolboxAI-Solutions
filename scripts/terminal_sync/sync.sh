#!/bin/bash

# Terminal Synchronization Script
# Usage: ./sync.sh [terminal_id] [action] [message]
# Actions: status, message, check, report

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERMINAL_ID=${1:-"unknown"}
ACTION=${2:-"check"}
MESSAGE=${3:-""}

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to update status
update_status() {
    local terminal=$1
    local status=$2
    echo "# Terminal $terminal Status Update" > "$SCRIPT_DIR/status/$terminal.status"
    echo "# Last Updated: $(date '+%Y-%m-%d %H:%M:%S')" >> "$SCRIPT_DIR/status/$terminal.status"
    echo "$status" >> "$SCRIPT_DIR/status/$terminal.status"
    echo -e "${GREEN}✓${NC} Status updated for $terminal"
}

# Function to send message
send_message() {
    local from=$1
    local to=$2
    local msg=$3
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$from] $msg" >> "$SCRIPT_DIR/messages/$to.msg"
    echo -e "${BLUE}📨${NC} Message sent to $to"
}

# Function to check messages
check_messages() {
    local terminal=$1
    local msg_file="$SCRIPT_DIR/messages/$terminal.msg"
    
    if [ -f "$msg_file" ]; then
        echo -e "${YELLOW}📬 Messages for $terminal:${NC}"
        tail -n 5 "$msg_file"
    else
        echo -e "${YELLOW}📭${NC} No messages for $terminal"
    fi
}

# Function to show all terminal status
show_all_status() {
    echo -e "${BLUE}=== TERMINAL STATUS OVERVIEW ===${NC}"
    echo ""
    
    for status_file in "$SCRIPT_DIR/status"/*.status; do
        if [ -f "$status_file" ]; then
            terminal=$(basename "$status_file" .status)
            echo -e "${GREEN}[$terminal]${NC}"
            grep -E "^# Current Task:|^# Progress:|^# Status:" "$status_file" | sed 's/^# /  /'
            echo ""
        fi
    done
}

# Function to create daily report
create_report() {
    local terminal=$1
    local report_dir="$SCRIPT_DIR/completed/$(date '+%Y-%m-%d')"
    mkdir -p "$report_dir"
    
    local report_file="$report_dir/${terminal}_$(date '+%H%M%S').log"
    
    echo "=== Daily Report for $terminal ===" > "$report_file"
    echo "Generated: $(date)" >> "$report_file"
    echo "" >> "$report_file"
    
    if [ -f "$SCRIPT_DIR/status/$terminal.status" ]; then
        echo "Current Status:" >> "$report_file"
        cat "$SCRIPT_DIR/status/$terminal.status" >> "$report_file"
    fi
    
    echo -e "${GREEN}✓${NC} Report saved to $report_file"
}

# Main logic
case $ACTION in
    "status")
        if [ -n "$MESSAGE" ]; then
            update_status "$TERMINAL_ID" "$MESSAGE"
        else
            echo "Usage: ./sync.sh [terminal_id] status [status_message]"
        fi
        ;;
        
    "message")
        TO_TERMINAL=${4:-"all"}
        if [ "$TO_TERMINAL" = "all" ]; then
            for term in terminal1 terminal2 terminal3 debugger; do
                if [ "$term" != "$TERMINAL_ID" ]; then
                    send_message "$TERMINAL_ID" "$term" "$MESSAGE"
                fi
            done
        else
            send_message "$TERMINAL_ID" "$TO_TERMINAL" "$MESSAGE"
        fi
        ;;
        
    "check")
        check_messages "$TERMINAL_ID"
        ;;
        
    "overview")
        show_all_status
        ;;
        
    "report")
        create_report "$TERMINAL_ID"
        ;;
        
    *)
        echo "Terminal Synchronization System"
        echo "================================"
        echo "Usage: ./sync.sh [terminal_id] [action] [options]"
        echo ""
        echo "Actions:"
        echo "  status [message]     - Update terminal status"
        echo "  message [text] [to]  - Send message to terminal(s)"
        echo "  check               - Check messages for terminal"
        echo "  overview            - Show all terminal status"
        echo "  report              - Create daily report"
        echo ""
        echo "Terminal IDs: terminal1, terminal2, terminal3, debugger"
        ;;
esac