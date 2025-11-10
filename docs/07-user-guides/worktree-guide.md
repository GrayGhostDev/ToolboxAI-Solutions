# Git Worktrees for Parallel Claude Code Sessions - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Overview

The ToolBoxAI Worktree Management System enables you to run multiple Claude Code sessions in parallel, each working on different features or bug fixes simultaneously. This follows Anthropic's official best practices and community-proven patterns for maximizing development productivity.

### Key Benefits

- **Parallel Development**: Work on multiple features simultaneously without context switching
- **Isolated Environments**: Each worktree has its own ports, dependencies, and environment
- **Resource Efficiency**: Intelligent resource allocation and monitoring
- **Session Management**: Track productivity and manage multiple Claude sessions
- **Automatic Setup**: One command to create, configure, and launch a worktree

## Quick Start

### 1. Create Your First Worktree

```bash
# Create a new worktree for a feature
./scripts/worktree/worktree-manager.sh create feature-auth-refactor --launch-claude

# This single command will:
# - Create a new git worktree
# - Allocate unique ports (backend & frontend)
# - Set up the environment
# - Launch Claude Code in the worktree
```

### 2. Monitor Your Worktrees

```bash
# View real-time status dashboard
./scripts/worktree/worktree-status.sh

# List all worktrees
./scripts/worktree/worktree-manager.sh list --detailed
```

### 3. Start Services

```bash
# Navigate to your worktree
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees/feature-auth-refactor

# Start all services
./start.sh

# Or start individually:
# Backend: uvicorn main:app --port $BACKEND_PORT
# Frontend: PORT=$FRONTEND_PORT npm run dev
```

## Installation

### Prerequisites

- Git 2.7.0+ (for worktree support)
- Claude Code CLI installed
- Python 3.8+
- Node.js 16+
- PostgreSQL (running)
- Redis (running)

### Setup Shell Aliases

Add these aliases to your `~/.zshrc` or `~/.bashrc`:

```bash
# Worktree management aliases
alias wcreate='/Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/scripts/worktree/worktree-manager.sh create'
alias wlist='/Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/scripts/worktree/worktree-manager.sh list'
alias wstatus='/Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/scripts/worktree/worktree-status.sh'
alias wremove='/Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/scripts/worktree/worktree-manager.sh remove'
alias wclean='/Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/scripts/worktree/worktree-manager.sh cleanup'

# Quick navigation
alias wroot='cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees'
```

Reload your shell configuration:

```bash
source ~/.zshrc  # or ~/.bashrc
```

## Basic Usage

### Creating a Worktree

```bash
# Basic creation
wcreate feature-name

# Create and launch Claude
wcreate feature-name --launch-claude

# The system will:
# 1. Create branch 'feature-name'
# 2. Set up worktree at ../ToolBoxAI-Solutions-worktrees/feature-name
# 3. Allocate ports (e.g., backend: 8009, frontend: 5179)
# 4. Copy environment files
# 5. Create helper scripts (start.sh, stop.sh, status.sh)
```

### Managing Sessions

```bash
# List all worktrees with details
wlist --detailed

# Check status dashboard (interactive)
wstatus

# Get JSON output for scripting
wstatus json

# Remove a worktree
wremove feature-name

# Clean up old worktrees (older than 7 days)
wclean --auto
```

### Working in a Worktree

Each worktree includes helper scripts:

```bash
cd /path/to/worktree

# Start all services
./start.sh

# Check status
./status.sh

# Stop all services
./stop.sh
```

### Environment Variables

Each worktree has a `.env.worktree` file with:

```bash
WORKTREE_NAME=feature-name
BACKEND_PORT=8009
FRONTEND_PORT=5180
REDIS_DB=2
LOG_DIR=/path/to/worktree/logs
CACHE_DIR=/path/to/worktree/.cache
```

## Advanced Features

### Parallel Task Coordination

Run multiple Claude sessions on related tasks:

```bash
# Create worktrees for different parts of a feature
wcreate feature-ui --launch-claude
wcreate feature-backend --launch-claude
wcreate feature-tests --launch-claude

# Monitor all sessions
wstatus watch
```

### Resource Monitoring

```bash
# Show resource usage
./scripts/worktree/worktree-manager.sh resources

# Optimize resource allocation
./scripts/worktree/worktree-manager.sh optimize
```

### Session Analytics

Using the Python agents:

```python
from core.agents.github_agents.session_manager_agent import SessionManagerAgent

# Initialize agent
agent = SessionManagerAgent()

# Analyze productivity
result = await agent.execute({"action": "analyze"})
print(result["productivity_trend"])

# Get session summary
summary = await agent.execute({
    "action": "summary",
    "session_id": "claude-feature-auth-20250117-143022"
})
```

### VS Code Integration

Each worktree is configured for VS Code:

```bash
# Open worktree in VS Code
code /path/to/worktree

# VS Code will have:
# - Correct Python interpreter
# - Workspace-specific settings
# - Color-coded title bar
# - Debug configurations
```

### Docker Support (Optional)

For complete isolation:

```bash
# Create containerized worktree
docker run -v $(pwd):/workspace \
  -p 8009:8009 -p 5179:5179 \
  toolboxai/worktree:latest \
  create feature-name
```

## Best Practices

### 1. Naming Conventions

Use descriptive branch names:
- Features: `feature-<name>`
- Bugfixes: `bugfix-<issue-number>`
- Experiments: `experiment-<name>`

### 2. Session Management

- **Limit Concurrent Sessions**: Don't exceed 5-6 parallel sessions
- **Regular Cleanup**: Run `wclean` weekly
- **Monitor Resources**: Check `wstatus` regularly

### 3. Task Distribution

```bash
# Good: Clear task separation
wcreate feature-auth-ui        # Frontend work
wcreate feature-auth-api       # Backend work
wcreate feature-auth-tests     # Test creation

# Bad: Overlapping concerns
wcreate feature-everything     # Too broad
```

### 4. Commit Strategy

- Commit frequently within worktrees
- Use descriptive commit messages
- Create PRs from worktree branches

### 5. Resource Management

- Stop services when not in use: `./stop.sh`
- Clean up completed worktrees promptly
- Monitor port usage with `wstatus`

## Troubleshooting

### Port Conflicts

**Problem**: "Port already in use" error

**Solution**:
```bash
# Find process using port
lsof -i :8009

# Kill process
kill -9 <PID>

# Or use the cleanup command
wclean --force
```

### Worktree Not Found

**Problem**: Worktree exists but not recognized

**Solution**:
```bash
# Prune worktree list
git worktree prune

# Re-add worktree
git worktree add ../worktrees/branch-name branch-name
```

### Dependencies Not Installing

**Problem**: `npm install` or `pip install` failing

**Solution**:
```bash
# Clean install dependencies
cd /path/to/worktree

# For Node.js
rm -rf node_modules package-lock.json
npm install

# For Python
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Claude Not Launching

**Problem**: Claude Code doesn't start in worktree

**Solution**:
```bash
# Check Claude installation
which claude

# Launch manually
cd /path/to/worktree
claude --continue
```

### Database Connection Issues

**Problem**: Can't connect to PostgreSQL or Redis

**Solution**:
```bash
# Check services
pg_isready
redis-cli ping

# Start if needed
brew services start postgresql
brew services start redis
```

## FAQ

### Q: How many parallel sessions can I run?

**A:** The system supports up to 10 parallel worktrees by default. Practically, 3-5 concurrent sessions is optimal for most developers.

### Q: Do worktrees share dependencies?

**A:** No, each worktree has its own `node_modules` and Python `venv`. This ensures complete isolation but requires more disk space.

### Q: Can I use existing branches?

**A:** Yes, the system will use an existing branch if it exists, or create a new one.

### Q: How much disk space do worktrees use?

**A:** Typically 500MB-2GB per worktree, depending on dependencies. Monitor with:
```bash
du -sh /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees/*
```

### Q: Can I move a worktree?

**A:** No, worktree paths are fixed. Remove and recreate if you need a different location.

### Q: What happens to uncommitted changes?

**A:** The system automatically stashes uncommitted changes in the main repository before creating a worktree.

### Q: Can multiple people use worktrees on the same machine?

**A:** Yes, but ensure port ranges don't overlap. Configure different port ranges per user in the config file.

### Q: How do I merge changes from a worktree?

**A:** Standard git workflow:
```bash
cd /path/to/worktree
git add .
git commit -m "Feature complete"
git push origin feature-branch
# Create PR on GitHub
```

## Performance Tips

1. **SSD Storage**: Use SSD for worktree directory for best performance
2. **Memory**: Ensure at least 16GB RAM for 3+ concurrent sessions
3. **CPU**: Multiple cores help with parallel builds
4. **Network**: Stable connection for Claude Code communication

## Security Considerations

- Each worktree has isolated environment variables
- Secrets in `.env` files are not committed
- Use different Redis databases per worktree
- Regular cleanup prevents orphaned processes

## Integration with CI/CD

```yaml
# .github/workflows/worktree-tests.yml
name: Worktree Tests
on:
  push:
    branches: [feature-*, bugfix-*]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test Worktree Branch
        run: |
          npm test
          pytest
```

## Monitoring and Metrics

The session manager tracks:
- Session duration
- Files modified
- Commits made
- Productivity scores
- Resource usage

Access metrics:
```bash
cat /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions-worktrees/.claude-sessions.json | jq '.metrics'
```

## Support and Resources

- **Documentation**: This guide and inline help (`worktree-manager.sh help`)
- **Logs**: Check `~/.claude-code/logs/` and worktree-specific `logs/` directories
- **Community**: Anthropic Discord #claude-code channel
- **Issues**: GitHub repository issues

## Conclusion

The worktree system enables true parallel development with Claude Code, multiplying your productivity. Start with 2-3 worktrees and gradually increase as you become comfortable with the workflow.

Remember: The goal is not to maximize the number of sessions, but to optimize your development flow and maintain code quality while working on multiple features simultaneously.

---

*Last Updated: January 2025*
*Version: 1.0.0*