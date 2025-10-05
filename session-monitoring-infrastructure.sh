#!/bin/bash

# session-monitoring-infrastructure.sh
# Launch Claude Code session for Monitoring Infrastructure Agent
# This agent handles Days 19-21: Prometheus, Grafana, Jaeger, runbooks

# Agent Configuration
AGENT_NAME="Monitoring Infrastructure"
WORKTREE_DIR="parallel-worktrees/monitoring-infrastructure"
BRANCH="feature/monitoring-setup"
PORT=8036
SESSION_NAME="monitoring-infrastructure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Monitoring Infrastructure - Production Workflow         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if worktree exists
if [ ! -d "$WORKTREE_DIR" ]; then
    echo -e "${RED}✗ Worktree not found: $WORKTREE_DIR${NC}"
    echo -e "${YELLOW}→ Please run initialization script first${NC}"
    exit 1
fi

# Display agent mission
echo -e "${GREEN}Agent Mission:${NC}"
echo "  • Phase: Performance & Monitoring (Days 19-21)"
echo "  • Priority: 🟡 HIGH"
echo "  • Duration: 3 developer days"
echo ""
echo -e "${GREEN}Key Responsibilities:${NC}"
echo "  • Setup Prometheus metrics and alerting"
echo "  • Configure Grafana dashboards (API, DB, Redis)"
echo "  • Implement Jaeger distributed tracing"
echo "  • Create 6 operational runbooks"
echo ""
echo -e "${GREEN}Task Reference:${NC}"
echo "  See PRODUCTION_AGENTS_PLAN.md (Agent 5 specification)"
echo ""

# Navigate to worktree
cd "$WORKTREE_DIR" || exit 1

# Display worktree info
echo -e "${BLUE}Worktree Information:${NC}"
echo "  • Location: $WORKTREE_DIR"
echo "  • Branch: $BRANCH"
echo "  • Port: $PORT"
echo ""

# Check if monitoring stack is running
PROMETHEUS_RUNNING=false
GRAFANA_RUNNING=false
JAEGER_RUNNING=false

if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    PROMETHEUS_RUNNING=true
fi

if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    GRAFANA_RUNNING=true
fi

if curl -s http://localhost:16686 > /dev/null 2>&1; then
    JAEGER_RUNNING=true
fi

echo -e "${BLUE}Monitoring Stack Status:${NC}"
if [ "$PROMETHEUS_RUNNING" = true ]; then
    echo -e "  • Prometheus: ${GREEN}✓ Running${NC} (http://localhost:9090)"
else
    echo -e "  • Prometheus: ${YELLOW}⚠ Not running${NC}"
fi

if [ "$GRAFANA_RUNNING" = true ]; then
    echo -e "  • Grafana: ${GREEN}✓ Running${NC} (http://localhost:3001)"
else
    echo -e "  • Grafana: ${YELLOW}⚠ Not running${NC}"
fi

if [ "$JAEGER_RUNNING" = true ]; then
    echo -e "  • Jaeger: ${GREEN}✓ Running${NC} (http://localhost:16686)"
else
    echo -e "  • Jaeger: ${YELLOW}⚠ Not running${NC}"
fi
echo ""

# Check if development server is running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠ Port $PORT is already in use${NC}"
    echo -e "${YELLOW}→ Stopping existing process...${NC}"
    kill $(lsof -t -i:$PORT) 2>/dev/null || true
    sleep 2
fi

# Start development server in background
echo -e "${GREEN}→ Starting development server on port $PORT...${NC}"
cd apps/backend
source venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --reload --port $PORT > /tmp/$SESSION_NAME-server.log 2>&1 &
SERVER_PID=$!
cd ../..

# Wait for server to start
echo -e "${YELLOW}→ Waiting for server to start...${NC}"
sleep 3

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Server started successfully (PID: $SERVER_PID)${NC}"
else
    echo -e "${RED}✗ Server failed to start${NC}"
    echo -e "${YELLOW}→ Check logs: /tmp/$SESSION_NAME-server.log${NC}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Ready to Launch Claude Code Session                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Display launch instructions
echo -e "${GREEN}Next Steps:${NC}"
echo "  1. Review PRODUCTION_AGENTS_PLAN.md (Agent 5 specification)"
echo "  2. Start with Day 19: Prometheus metrics + alerting"
echo "  3. Day 20: Grafana dashboards (API, DB, Redis)"
echo "  4. Day 21: Jaeger tracing + operational runbooks"
echo ""
echo -e "${YELLOW}Important Commands:${NC}"
echo "  • docker-compose up prometheus  # Start Prometheus"
echo "  • docker-compose up grafana     # Start Grafana"
echo "  • docker-compose up jaeger      # Start Jaeger"
echo "  • curl localhost:9090/metrics   # Check Prometheus"
echo ""
echo -e "${BLUE}Monitoring Deliverables:${NC}"
echo "  • Prometheus: Metrics + 5 alert rules"
echo "  • Grafana: 3 dashboards (API, DB, Redis)"
echo "  • Jaeger: Distributed tracing + service map"
echo "  • Runbooks: 6 operational guides"
echo "    - Deployment, Incident Response, Rollback"
echo "    - Database Migration, Performance Issues, Security"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo "  • Backend API: http://localhost:$PORT"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana: http://localhost:3001"
echo "  • Jaeger UI: http://localhost:16686"
echo "  • Logs: /tmp/$SESSION_NAME-server.log"
echo ""

# Launch Claude Code
echo -e "${GREEN}→ Launching Claude Code session...${NC}"
echo ""

# Open Claude Code in current directory
claude code .

# Cleanup on exit
trap "kill $SERVER_PID 2>/dev/null || true" EXIT

echo ""
echo -e "${GREEN}✓ Session ended${NC}"
echo -e "${YELLOW}→ Server (PID: $SERVER_PID) will be stopped${NC}"
