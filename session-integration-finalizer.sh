#!/bin/bash

# session-integration-finalizer.sh
# Launch Claude Code session for Integration Finalizer Agent
# This agent handles Days 1-3: Security fixes, branch merging, release tagging

# Agent Configuration
AGENT_NAME="Integration Finalizer"
WORKTREE_DIR="parallel-worktrees/integration-finalizer"
BRANCH="feature/integration-final"
PORT=8032
SESSION_NAME="integration-finalizer"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Integration Finalizer Agent - Production Workflow      ║${NC}"
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
echo "  • Phase: Integration & Commit (Days 1-3)"
echo "  • Priority: 🔴 CRITICAL"
echo "  • Duration: 3 developer days"
echo ""
echo -e "${GREEN}Key Responsibilities:${NC}"
echo "  • Day 1: Fix security vulnerabilities (npm + Python)"
echo "  • Day 2: Merge all feature branches to main"
echo "  • Day 3: Tag v2.0.0-alpha release"
echo ""
echo -e "${GREEN}Task File:${NC}"
echo "  worktree-tasks/integration-finalizer-tasks.md (734 lines)"
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
echo "  1. Open task file: worktree-tasks/integration-finalizer-tasks.md"
echo "  2. Start with Day 1: Security Fixes"
echo "  3. Follow daily checklist in task file"
echo "  4. Update TODO.md as you complete each day"
echo ""
echo -e "${YELLOW}Important Commands:${NC}"
echo "  • npm audit fix              # Fix npm vulnerabilities"
echo "  • safety check               # Check Python vulnerabilities"
echo "  • git merge --no-ff          # Merge branches"
echo "  • git tag -a v2.0.0-alpha    # Tag release"
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
