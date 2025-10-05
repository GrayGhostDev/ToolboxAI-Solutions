#!/bin/bash

# session-performance-optimizer.sh
# Launch Claude Code session for Performance Optimizer Agent
# This agent handles Days 19-21: Performance optimization and caching

# Agent Configuration
AGENT_NAME="Performance Optimizer"
WORKTREE_DIR="parallel-worktrees/performance-optimizer"
BRANCH="feature/performance-optimization"
PORT=8035
SESSION_NAME="performance-optimizer"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Performance Optimizer - Production Workflow            ║${NC}"
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
echo "  • Fix N+1 query patterns (15-20 instances)"
echo "  • Implement Redis caching for 20+ endpoints"
echo "  • Optimize frontend bundles (2.3MB → <1MB)"
echo "  • Achieve performance targets (p95 <200ms)"
echo ""
echo -e "${GREEN}Task Reference:${NC}"
echo "  See PRODUCTION_AGENTS_PLAN.md (Agent 4 specification)"
echo ""

# Navigate to worktree
cd "$WORKTREE_DIR" || exit 1

# Display worktree info
echo -e "${BLUE}Worktree Information:${NC}"
echo "  • Location: $WORKTREE_DIR"
echo "  • Branch: $BRANCH"
echo "  • Port: $PORT"
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Redis is not running${NC}"
    echo -e "${YELLOW}→ Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi

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
echo "  1. Review PRODUCTION_AGENTS_PLAN.md (Agent 4 specification)"
echo "  2. Start with Day 19: Fix N+1 queries (15-20 instances)"
echo "  3. Day 20: Implement Redis caching (20+ endpoints)"
echo "  4. Day 21: Frontend bundle optimization"
echo ""
echo -e "${YELLOW}Important Commands:${NC}"
echo "  • pytest -m performance        # Performance tests"
echo "  • locust -f tests/load/        # Load testing"
echo "  • redis-cli monitor            # Monitor Redis activity"
echo "  • npm run build -- --analyze   # Analyze bundle size"
echo ""
echo -e "${BLUE}Performance Targets:${NC}"
echo "  • p50 Response Time: <100ms"
echo "  • p95 Response Time: <200ms"
echo "  • p99 Response Time: <500ms"
echo "  • Sustained Load: >1000 RPS"
echo "  • Frontend Bundle: 2.3MB → <1MB"
echo "  • Cache Hit Rate: >80%"
echo ""
echo -e "${BLUE}Server Status:${NC}"
echo "  • Backend API: http://localhost:$PORT"
echo "  • API Docs: http://localhost:$PORT/docs"
echo "  • Redis: redis://localhost:6379"
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
