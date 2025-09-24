#!/bin/bash
# Phase 1 Critical Stabilization Monitoring Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================================================================================${NC}"
echo -e "${BLUE}🚀 PHASE 1 CRITICAL STABILIZATION MONITORING SYSTEM${NC}"
echo -e "${BLUE}================================================================================================${NC}"
echo -e "${GREEN}Project: ToolBoxAI-Solutions${NC}"
echo -e "${GREEN}Target: 48-hour stabilization${NC}"
echo -e "${GREEN}Location: ${PROJECT_ROOT}${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}🐍 Checking Python environment...${NC}"
python_version=$(python --version 2>&1)
echo "Python version: $python_version"

# Check virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  No virtual environment detected${NC}"
    if [ -d "venv" ]; then
        echo -e "${BLUE}🔄 Activating venv...${NC}"
        source venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ No venv found. Please create one: python -m venv venv${NC}"
        exit 1
    fi
fi

# Function to show menu
show_menu() {
    echo ""
    echo -e "${BLUE}📋 MONITORING OPTIONS:${NC}"
    echo "1) 🚀 Start Full Monitoring (Recommended)"
    echo "2) 🧪 Run Test Cycle Only"
    echo "3) 📊 Check Current Status"
    echo "4) 🔧 Install Dependencies"
    echo "5) 🧪 Individual Monitor Tests"
    echo "6) 📈 Generate Report Only"
    echo "7) 🚨 Alert System Only"
    echo "8) 📖 View Documentation"
    echo "9) 🗂️  View Output Files"
    echo "0) ❌ Exit"
    echo ""
}

# Function to check if monitoring is running
check_monitoring_status() {
    if pgrep -f "master_control.py" > /dev/null; then
        echo -e "${GREEN}✅ Monitoring is currently running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚪ No monitoring processes detected${NC}"
        return 1
    fi
}

# Function to stop monitoring
stop_monitoring() {
    echo -e "${YELLOW}🛑 Stopping monitoring processes...${NC}"
    pkill -f "master_control.py" 2>/dev/null || true
    pkill -f "phase1_dashboard.py" 2>/dev/null || true
    pkill -f "test_monitor.py" 2>/dev/null || true
    pkill -f "security_monitor.py" 2>/dev/null || true
    pkill -f "performance_monitor.py" 2>/dev/null || true
    pkill -f "alert_system.py" 2>/dev/null || true
    sleep 2
    echo -e "${GREEN}✅ Monitoring stopped${NC}"
}

# Function to show current targets
show_targets() {
    echo -e "${BLUE}🎯 CURRENT PHASE 1 TARGETS:${NC}"
    echo ""
    echo -e "${YELLOW}📊 Test Infrastructure:${NC}"
    echo "   Current: 67.7% pass rate (86/127 tests passing)"
    echo "   Target:  95% pass rate (121/127 tests passing)"
    echo "   Gap:     41 tests need to be fixed"
    echo ""
    echo -e "${YELLOW}🔒 Security Hardening:${NC}"
    echo "   Current: 85% security score"
    echo "   Target:  95% security score"
    echo "   Gap:     10 percentage points improvement"
    echo ""
    echo -e "${YELLOW}⚡ Performance Optimization:${NC}"
    echo "   Current: 950KB bundle size"
    echo "   Target:  <500KB bundle size"
    echo "   Gap:     450KB+ reduction needed"
    echo ""
    echo -e "${YELLOW}⏰ Timeline:${NC}"
    echo "   Target:  Complete within 48 hours"
    echo "   Status:  Monitoring just started"
    echo ""
}

# Function to run individual tests
run_individual_tests() {
    echo -e "${BLUE}🧪 INDIVIDUAL MONITOR TESTS:${NC}"
    echo "1) Test Infrastructure Monitor"
    echo "2) Security Hardening Monitor"
    echo "3) Performance Monitor"
    echo "4) Alert System Test"
    echo "5) Hourly Reporter Test"
    echo "6) Run All Individual Tests"
    echo "0) Back to main menu"
    echo ""
    read -p "Select test: " test_choice

    case $test_choice in
        1)
            echo -e "${BLUE}🧪 Testing test infrastructure monitor...${NC}"
            python monitoring/test_monitor.py
            ;;
        2)
            echo -e "${BLUE}🔒 Testing security monitor...${NC}"
            python monitoring/security_monitor.py
            ;;
        3)
            echo -e "${BLUE}⚡ Testing performance monitor...${NC}"
            python monitoring/performance_monitor.py
            ;;
        4)
            echo -e "${BLUE}🚨 Testing alert system...${NC}"
            python monitoring/alert_system.py --test-alert
            ;;
        5)
            echo -e "${BLUE}📊 Testing hourly reporter...${NC}"
            python monitoring/hourly_reporter.py --run-once
            ;;
        6)
            echo -e "${BLUE}🔄 Running all individual tests...${NC}"
            python monitoring/test_monitor.py
            python monitoring/security_monitor.py
            python monitoring/performance_monitor.py
            python monitoring/alert_system.py --test-alert
            python monitoring/hourly_reporter.py --run-once
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            ;;
    esac
}

# Function to view output files
view_output_files() {
    echo -e "${BLUE}📁 MONITORING OUTPUT FILES:${NC}"
    echo ""

    monitoring_dir="monitoring"

    if [ -d "$monitoring_dir" ]; then
        echo -e "${YELLOW}JSON Data Files:${NC}"
        for file in "$monitoring_dir"/*.json; do
            if [ -f "$file" ]; then
                size=$(ls -lh "$file" | awk '{print $5}')
                modified=$(ls -l "$file" | awk '{print $6, $7, $8}')
                echo "  📄 $(basename "$file") ($size, modified: $modified)"
            fi
        done

        echo ""
        echo -e "${YELLOW}Database Files:${NC}"
        for file in "$monitoring_dir"/*.db; do
            if [ -f "$file" ]; then
                size=$(ls -lh "$file" | awk '{print $5}')
                echo "  🗄️  $(basename "$file") ($size)"
            fi
        done

        echo ""
        echo -e "${YELLOW}Log Files:${NC}"
        for file in "$monitoring_dir"/*.log; do
            if [ -f "$file" ]; then
                size=$(ls -lh "$file" | awk '{print $5}')
                lines=$(wc -l < "$file" 2>/dev/null || echo "0")
                echo "  📝 $(basename "$file") ($size, $lines lines)"
            fi
        done

        echo ""
        echo -e "${YELLOW}Report Files:${NC}"
        reports_dir="$monitoring_dir/reports"
        if [ -d "$reports_dir" ]; then
            for file in "$reports_dir"/*.txt; do
                if [ -f "$file" ]; then
                    size=$(ls -lh "$file" | awk '{print $5}')
                    echo "  📊 $(basename "$file") ($size)"
                fi
            done
        else
            echo "  📊 No reports generated yet"
        fi

        echo ""
        echo -e "${BLUE}💡 Quick commands:${NC}"
        echo "  View latest metrics: cat monitoring/hourly_progress.json | jq"
        echo "  View test status: cat monitoring/test_metrics.json | jq"
        echo "  View alerts: cat monitoring/alerts.log"
        echo "  View latest report: cat monitoring/reports/latest_hourly_report.txt"

    else
        echo -e "${RED}❌ Monitoring directory not found${NC}"
    fi
}

# Main menu loop
while true; do
    clear
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}🚀 PHASE 1 CRITICAL STABILIZATION MONITORING SYSTEM${NC}"
    echo -e "${BLUE}================================================================================================${NC}"

    # Show current status
    check_monitoring_status

    # Show targets
    show_targets

    # Show menu
    show_menu

    read -p "Enter your choice [0-9]: " choice

    case $choice in
        1)
            echo -e "${GREEN}🚀 Starting full monitoring system...${NC}"
            echo -e "${YELLOW}⚠️  This will run continuously. Press Ctrl+C to stop.${NC}"
            echo ""
            read -p "Continue? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}🔄 Starting monitoring...${NC}"
                python monitoring/master_control.py
            fi
            ;;
        2)
            echo -e "${BLUE}🧪 Running test cycle...${NC}"
            python monitoring/master_control.py --test-run
            echo ""
            read -p "Press Enter to continue..."
            ;;
        3)
            echo -e "${BLUE}📊 Checking current status...${NC}"
            python monitoring/master_control.py --status
            echo ""
            read -p "Press Enter to continue..."
            ;;
        4)
            echo -e "${BLUE}🔧 Installing dependencies...${NC}"
            python monitoring/master_control.py --install-deps
            echo ""
            read -p "Press Enter to continue..."
            ;;
        5)
            run_individual_tests
            echo ""
            read -p "Press Enter to continue..."
            ;;
        6)
            echo -e "${BLUE}📈 Generating hourly report...${NC}"
            python monitoring/hourly_reporter.py --run-once
            echo ""
            read -p "Press Enter to continue..."
            ;;
        7)
            echo -e "${BLUE}🚨 Starting alert system only...${NC}"
            echo -e "${YELLOW}⚠️  This will run continuously. Press Ctrl+C to stop.${NC}"
            echo ""
            read -p "Continue? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                python monitoring/alert_system.py --monitor
            fi
            ;;
        8)
            echo -e "${BLUE}📖 Opening documentation...${NC}"
            if [ -f "monitoring/README.md" ]; then
                if command -v less >/dev/null 2>&1; then
                    less monitoring/README.md
                else
                    cat monitoring/README.md
                fi
            else
                echo -e "${RED}❌ Documentation not found${NC}"
            fi
            echo ""
            read -p "Press Enter to continue..."
            ;;
        9)
            view_output_files
            echo ""
            read -p "Press Enter to continue..."
            ;;
        0)
            echo -e "${YELLOW}🛑 Stopping any running monitoring...${NC}"
            stop_monitoring
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid choice. Please enter 0-9.${NC}"
            sleep 2
            ;;
    esac
done