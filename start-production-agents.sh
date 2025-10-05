#!/bin/bash

# start-production-agents.sh
# Master launch script for all 6 production workflow agents
# Launches agents sequentially with proper dependency checks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Agent configurations
declare -A AGENTS=(
    [1]="integration-finalizer:Days 1-3:8032:🔴 CRITICAL"
    [2]="testing-week1-2:Days 4-11:8033:🔴 CRITICAL"
    [3]="testing-week3:Days 12-18:8034:🟡 HIGH"
    [4]="performance-optimizer:Days 19-21:8035:🟡 HIGH"
    [5]="monitoring-infrastructure:Days 19-21:8036:🟡 HIGH"
    [6]="production-deployer:Days 22-25:8037:🔴 CRITICAL"
)

# Clear screen
clear

# Display banner
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}║       ${MAGENTA}ToolboxAI Solutions - Production Workflow${CYAN}              ║${NC}"
echo -e "${CYAN}║       ${MAGENTA}Master Agent Launch System${CYAN}                           ║${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if worktrees directory exists
if [ ! -d "parallel-worktrees" ]; then
    echo -e "${RED}✗ parallel-worktrees directory not found${NC}"
    echo -e "${YELLOW}→ Please run worktree initialization first${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Worktrees directory found${NC}"

# Check if task files exist
REQUIRED_FILES=(
    "worktree-tasks/integration-finalizer-tasks.md"
    "worktree-tasks/testing-week1-2-tasks.md"
    "PRODUCTION_AGENTS_PLAN.md"
    "PRODUCTION_WORKFLOW_SUMMARY.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Required file not found: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All task files found${NC}"

# Check if session scripts exist
for i in {1..6}; do
    IFS=':' read -r name _ _ _ <<< "${AGENTS[$i]}"
    script="session-${name}.sh"
    if [ ! -f "$script" ]; then
        echo -e "${RED}✗ Session script not found: $script${NC}"
        exit 1
    fi

    # Make script executable
    chmod +x "$script"
done
echo -e "${GREEN}✓ All session scripts found and executable${NC}"
echo ""

# Display agent overview
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Production Workflow Agents Overview                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

for i in {1..6}; do
    IFS=':' read -r name days port priority <<< "${AGENTS[$i]}"
    printf "  ${GREEN}Agent %d:${NC} %-30s ${YELLOW}%s${NC} ${MAGENTA}Port %s${NC} %s\n" \
        "$i" "$name" "$days" "$port" "$priority"
done
echo ""

# Display execution phases
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Execution Phases                                            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Phase 1:${NC} Integration & Commit (Agent 1)"
echo -e "  ${CYAN}Phase 2:${NC} Testing & Quality Part 1 (Agent 2)"
echo -e "  ${CYAN}Phase 3:${NC} Testing & Quality Part 2 (Agent 3)"
echo -e "  ${CYAN}Phase 4:${NC} Performance & Monitoring (Agents 4 & 5 - Parallel)"
echo -e "  ${CYAN}Phase 5:${NC} Production Deployment (Agent 6)"
echo ""

# Display timeline
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Timeline                                                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Sequential:${NC} 25 developer days"
echo -e "  ${GREEN}Parallel:${NC}   21 developer days (Agents 4 & 5 overlap)"
echo -e "  ${GREEN}Target:${NC}     v2.0.0 production deployment"
echo ""

# Interactive menu
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  Launch Options                                              ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}1.${NC} Launch Agent 1 (Integration Finalizer)"
echo -e "  ${GREEN}2.${NC} Launch Agent 2 (Testing Week 1-2)"
echo -e "  ${GREEN}3.${NC} Launch Agent 3 (Testing Week 3)"
echo -e "  ${GREEN}4.${NC} Launch Agent 4 (Performance Optimizer)"
echo -e "  ${GREEN}5.${NC} Launch Agent 5 (Monitoring Infrastructure)"
echo -e "  ${GREEN}6.${NC} Launch Agent 6 (Production Deployer)"
echo -e "  ${CYAN}7.${NC} Launch Agents 4 & 5 (Parallel)"
echo -e "  ${MAGENTA}8.${NC} View agent status"
echo -e "  ${MAGENTA}9.${NC} View task files"
echo -e "  ${RED}0.${NC} Exit"
echo ""
echo -ne "${YELLOW}Select option:${NC} "
read -r option

case $option in
    1)
        echo -e "\n${GREEN}→ Launching Agent 1: Integration Finalizer${NC}\n"
        ./session-integration-finalizer.sh
        ;;
    2)
        echo -e "\n${GREEN}→ Launching Agent 2: Testing Week 1-2${NC}\n"
        ./session-testing-week1-2.sh
        ;;
    3)
        echo -e "\n${GREEN}→ Launching Agent 3: Testing Week 3${NC}\n"
        ./session-testing-week3.sh
        ;;
    4)
        echo -e "\n${GREEN}→ Launching Agent 4: Performance Optimizer${NC}\n"
        ./session-performance-optimizer.sh
        ;;
    5)
        echo -e "\n${GREEN}→ Launching Agent 5: Monitoring Infrastructure${NC}\n"
        ./session-monitoring-infrastructure.sh
        ;;
    6)
        echo -e "\n${GREEN}→ Launching Agent 6: Production Deployer${NC}\n"
        ./session-production-deployer.sh
        ;;
    7)
        echo -e "\n${GREEN}→ Launching Agents 4 & 5 in Parallel${NC}\n"
        echo -e "${YELLOW}Opening Agent 4 in new terminal...${NC}"
        osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && ./session-performance-optimizer.sh"'
        sleep 2
        echo -e "${YELLOW}Opening Agent 5 in new terminal...${NC}"
        osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && ./session-monitoring-infrastructure.sh"'
        echo -e "${GREEN}✓ Both agents launched in separate terminals${NC}"
        ;;
    8)
        echo -e "\n${BLUE}Agent Status:${NC}\n"
        for i in {1..6}; do
            IFS=':' read -r name days port _ <<< "${AGENTS[$i]}"
            worktree="parallel-worktrees/${name}"

            if [ -d "$worktree" ]; then
                status="${GREEN}✓ Ready${NC}"
            else
                status="${RED}✗ Not initialized${NC}"
            fi

            # Check if port is in use
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
                port_status="${GREEN}✓ Running${NC}"
            else
                port_status="${YELLOW}○ Stopped${NC}"
            fi

            printf "  ${GREEN}Agent %d:${NC} %-30s %s  Port: %s\n" \
                "$i" "$name" "$status" "$port_status"
        done
        echo ""
        ;;
    9)
        echo -e "\n${BLUE}Task Files:${NC}\n"
        echo -e "  ${GREEN}1.${NC} worktree-tasks/integration-finalizer-tasks.md"
        echo -e "  ${GREEN}2.${NC} worktree-tasks/testing-week1-2-tasks.md"
        echo -e "  ${GREEN}3.${NC} PRODUCTION_AGENTS_PLAN.md (Agents 3-6)"
        echo -e "  ${GREEN}4.${NC} PRODUCTION_WORKFLOW_SUMMARY.md"
        echo ""
        echo -ne "${YELLOW}View file (1-4):${NC} "
        read -r file_choice

        case $file_choice in
            1) cat worktree-tasks/integration-finalizer-tasks.md | less ;;
            2) cat worktree-tasks/testing-week1-2-tasks.md | less ;;
            3) cat PRODUCTION_AGENTS_PLAN.md | less ;;
            4) cat PRODUCTION_WORKFLOW_SUMMARY.md | less ;;
            *) echo -e "${RED}Invalid choice${NC}" ;;
        esac
        ;;
    0)
        echo -e "\n${GREEN}Exiting...${NC}\n"
        exit 0
        ;;
    *)
        echo -e "\n${RED}Invalid option${NC}\n"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Done${NC}"
