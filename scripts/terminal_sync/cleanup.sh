#!/bin/bash
# ToolBoxAI Cleanup Management Interface
# Unified interface for all cleanup operations

PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
CLEANUP_DIR="$PROJECT_ROOT/scripts/terminal_sync"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_menu() {
    echo ""
    echo "======================================"
    echo "🧹 ToolBoxAI Cleanup Management"
    echo "======================================"
    echo ""
    echo "1) 📊 View System Status"
    echo "2) 🔍 Preview Cleanup (Dry Run)"
    echo "3) 🧹 Run Standard Cleanup"
    echo "4) 💪 Run Aggressive Cleanup"
    echo "5) 🚨 Run Emergency Cleanup"
    echo "6) 📈 Generate Monitoring Report"
    echo "7) 🕐 Setup Automatic Scheduling"
    echo "8) 📋 View Cron Jobs"
    echo "9) 📝 View Documentation"
    echo "0) ❌ Exit"
    echo ""
    echo -n "Select option: "
}

view_status() {
    echo -e "\n${BLUE}System Status${NC}"
    echo "======================================"
    df -h /Volumes/G-DRIVE\ ArmorATD | grep -E "Filesystem|/Volumes"
    echo ""
    echo "Project Size:"
    du -sh "$PROJECT_ROOT" 2>/dev/null
    echo ""
    echo "Cleanable Artifacts:"
    echo -n "  Python __pycache__: "
    find "$PROJECT_ROOT" -type d -name "__pycache__" 2>/dev/null | wc -l
    echo -n "  Python .pyc files: "
    find "$PROJECT_ROOT" -type f -name "*.pyc" 2>/dev/null | wc -l
    echo -n "  Node modules: "
    find "$PROJECT_ROOT" -type d -name "node_modules" 2>/dev/null | wc -l
    echo ""
}

run_cleanup() {
    local mode=$1
    local cmd="python $CLEANUP_DIR/intelligent_cleanup.py"
    
    case $mode in
        "dry-run")
            echo -e "\n${YELLOW}Running Cleanup Preview (Dry Run)...${NC}"
            $cmd --dry-run
            ;;
        "standard")
            echo -e "\n${GREEN}Running Standard Cleanup...${NC}"
            $cmd
            ;;
        "aggressive")
            echo -e "\n${RED}Running Aggressive Cleanup...${NC}"
            echo "This will remove more files. Continue? (y/n): "
            read -r confirm
            if [ "$confirm" = "y" ]; then
                $cmd --aggressive
            else
                echo "Cancelled."
            fi
            ;;
    esac
}

# Main loop
while true; do
    show_menu
    read -r option
    
    case $option in
        1)
            view_status
            ;;
        2)
            run_cleanup "dry-run"
            ;;
        3)
            run_cleanup "standard"
            ;;
        4)
            run_cleanup "aggressive"
            ;;
        5)
            echo -e "\n${RED}Running Emergency Cleanup...${NC}"
            "$CLEANUP_DIR/emergency_cleanup.sh"
            ;;
        6)
            echo -e "\n${BLUE}Generating Monitoring Report...${NC}"
            python "$CLEANUP_DIR/cleanup_monitor.py"
            ;;
        7)
            echo -e "\n${GREEN}Setting up Automatic Scheduling...${NC}"
            "$CLEANUP_DIR/setup_automatic_cleanup.sh"
            ;;
        8)
            echo -e "\n${BLUE}Current Cron Jobs:${NC}"
            crontab -l | grep -E "ToolBoxAI|intelligent_cleanup|emergency_cleanup" || echo "No cleanup jobs scheduled"
            ;;
        9)
            echo -e "\n${BLUE}Opening Documentation...${NC}"
            if [ -f "$CLEANUP_DIR/CLEANUP_README.md" ]; then
                less "$CLEANUP_DIR/CLEANUP_README.md"
            else
                echo "Documentation not found"
            fi
            ;;
        0)
            echo -e "\n${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}Invalid option${NC}"
            ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read -r
done