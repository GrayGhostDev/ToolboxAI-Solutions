#!/bin/bash

# session-production-deployer.sh
# Launch Claude Code session for Production Deployer Agent
# This agent handles Days 22-25: Blue-green deployment to production

# Agent Configuration
AGENT_NAME="Production Deployer"
WORKTREE_DIR="parallel-worktrees/production-deployer"
BRANCH="feature/production-deployment"
PORT=8037
SESSION_NAME="production-deployer"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Production Deployer - Production Workflow              ║${NC}"
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
echo "  • Phase: Production Deployment (Days 22-25)"
echo "  • Priority: 🔴 CRITICAL"
echo "  • Duration: 4 developer days"
echo ""
echo -e "${GREEN}Key Responsibilities:${NC}"
echo "  • Blue-green deployment to production"
echo "  • Gradual traffic shift (10% → 50% → 100%)"
echo "  • Zero-downtime deployment"
echo "  • Tag and release v2.0.0"
echo ""
echo -e "${GREEN}Task Reference:${NC}"
echo "  See PRODUCTION_AGENTS_PLAN.md (Agent 6 specification)"
echo ""

# Navigate to worktree
cd "$WORKTREE_DIR" || exit 1

# Display worktree info
echo -e "${BLUE}Worktree Information:${NC}"
echo "  • Location: $WORKTREE_DIR"
echo "  • Branch: $BRANCH"
echo "  • Port: $PORT"
echo ""

# Check kubernetes connection
echo -e "${BLUE}Kubernetes Status:${NC}"
if kubectl cluster-info > /dev/null 2>&1; then
    CONTEXT=$(kubectl config current-context)
    echo -e "  • Cluster: ${GREEN}✓ Connected${NC} ($CONTEXT)"

    # Check current deployment
    if kubectl get deployment toolboxai-backend > /dev/null 2>&1; then
        CURRENT_ENV=$(kubectl get deployment toolboxai-backend -o jsonpath='{.spec.template.metadata.labels.environment}')
        echo -e "  • Current Environment: ${GREEN}$CURRENT_ENV${NC}"
    fi
else
    echo -e "  • Cluster: ${RED}✗ Not connected${NC}"
    echo -e "  ${YELLOW}→ Run: kubectl config use-context <production-context>${NC}"
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
echo "  1. Review PRODUCTION_AGENTS_PLAN.md (Agent 6 specification)"
echo "  2. Day 22: Prepare green deployment"
echo "  3. Day 23: Deploy and shift 10% traffic"
echo "  4. Day 24: Monitor and shift to 100%"
echo "  5. Day 25: Tag v2.0.0 and cleanup"
echo ""
echo -e "${YELLOW}Important Commands:${NC}"
echo "  • kubectl get deployments          # Check deployments"
echo "  • kubectl get pods -l app=backend  # Check pods"
echo "  • kubectl logs -f <pod-name>       # Follow logs"
echo "  • ./scripts/deploy/blue-green.sh  # Deploy script"
echo ""
echo -e "${RED}⚠️  CRITICAL SAFETY CHECKS:${NC}"
echo "  1. ✅ All tests passing (500+ tests)"
echo "  2. ✅ Test coverage >80%"
echo "  3. ✅ Load tests passed (>1000 RPS)"
echo "  4. ✅ Monitoring dashboards ready"
echo "  5. ✅ Rollback procedures documented"
echo ""
echo -e "${BLUE}Deployment Process:${NC}"
echo "  • Label current: environment=blue"
echo "  • Deploy new: environment=green"
echo "  • Shift traffic: 10% → 50% → 100%"
echo "  • Monitor metrics at each step"
echo "  • Rollback if issues detected"
echo ""
echo -e "${BLUE}Server Status:${NC}"
echo "  • Backend API: http://localhost:$PORT"
echo "  • API Docs: http://localhost:$PORT/docs"
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
