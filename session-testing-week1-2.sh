#!/bin/bash

# session-testing-week1-2.sh
# Launch Claude Code session for Testing Week 1-2 Executor Agent
# This agent handles Days 4-11: 500+ unit tests, code quality improvements

# Agent Configuration
AGENT_NAME="Testing Week 1-2 Executor"
WORKTREE_DIR="parallel-worktrees/testing-week1-2"
BRANCH="feature/testing-unit-quality"
PORT=8033
SESSION_NAME="testing-week1-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Testing Week 1-2 Executor - Production Workflow        ║${NC}"
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
echo "  • Phase: Testing & Quality Part 1 (Days 4-11)"
echo "  • Priority: 🔴 CRITICAL"
echo "  • Duration: 8 developer days"
echo ""
echo -e "${GREEN}Key Responsibilities:${NC}"
echo "  • Week 1: Write 500+ unit tests (Days 4-8)"
echo "  • Week 2: Code quality + multi-tenancy (Days 9-11)"
echo "  • Target: 60% → 85% backend coverage"
echo ""
echo -e "${GREEN}Task File:${NC}"
echo "  worktree-tasks/testing-week1-2-tasks.md (953 lines)"
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
echo "  1. Open task file: worktree-tasks/testing-week1-2-tasks.md"
echo "  2. Start with Day 4: Core API tests"
echo "  3. Follow weekly structure in task file"
echo "  4. Run pytest after each module completion"
echo ""
echo -e "${YELLOW}Important Commands:${NC}"
echo "  • pytest tests/unit/           # Run unit tests"
echo "  • pytest --cov=apps/backend    # Coverage report"
echo "  • pytest -v -m critical        # Run critical tests only"
echo "  • pytest --lf                  # Rerun failed tests"
echo ""
echo -e "${BLUE}Testing Targets:${NC}"
echo "  • Unit Tests: 500+ tests across 15 modules"
echo "  • Backend Coverage: 60% → 85%"
echo "  • Custom Exceptions: Replace 1,811 generic handlers"
echo "  • Multi-tenancy: 100% tenant middleware coverage"
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
