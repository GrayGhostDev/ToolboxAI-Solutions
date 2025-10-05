#!/bin/bash

# session-testing-week3.sh
# Launch Claude Code session for Testing Week 3 & Integration Agent
# This agent handles Days 12-18: E2E tests, load tests, integration tests

# Agent Configuration
AGENT_NAME="Testing Week 3 & Integration"
WORKTREE_DIR="parallel-worktrees/testing-week3"
BRANCH="feature/testing-e2e-integration"
PORT=8034
SESSION_NAME="testing-week3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Testing Week 3 & Integration - Production Workflow     ║${NC}"
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
echo "  • Phase: Testing & Quality Part 2 (Days 12-18)"
echo "  • Priority: 🟡 HIGH"
echo "  • Duration: 7 developer days"
echo ""
echo -e "${GREEN}Key Responsibilities:${NC}"
echo "  • Days 12-15: Integration tests + E2E tests + Load tests"
echo "  • Days 16-18: Dashboard component tests (384 components)"
echo "  • Target: 80%+ overall test coverage"
echo ""
echo -e "${GREEN}Task Reference:${NC}"
echo "  See PRODUCTION_AGENTS_PLAN.md (Agent 3 specification)"
echo ""

# Navigate to worktree
cd "$WORKTREE_DIR" || exit 1

# Display worktree info
echo -e "${BLUE}Worktree Information:${NC}"
echo "  • Location: $WORKTREE_DIR"
echo "  • Branch: $BRANCH"
echo "  • Port: $PORT"
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
echo "  1. Review PRODUCTION_AGENTS_PLAN.md (Agent 3 specification)"
echo "  2. Start with Day 12: Integration tests"
echo "  3. Setup Playwright for E2E tests (Day 13)"
echo "  4. Configure Locust for load tests (Day 14)"
echo ""
echo -e "${YELLOW}Important Commands:${NC}"
echo "  • pytest tests/integration/    # Integration tests"
echo "  • playwright test              # E2E tests"
echo "  • locust -f tests/load/        # Load tests"
echo "  • npm test                     # Dashboard component tests"
echo ""
echo -e "${BLUE}Testing Targets:${NC}"
echo "  • Integration Tests: Workflow + API integration"
echo "  • E2E Tests: Critical user flows with Playwright"
echo "  • Load Tests: >1000 RPS sustained load"
echo "  • Component Tests: 384 dashboard components"
echo "  • Overall Coverage: 80%+"
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
