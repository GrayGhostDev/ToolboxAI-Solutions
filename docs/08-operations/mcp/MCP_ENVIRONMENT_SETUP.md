# MCP Environment Variables Setup

**Last Updated:** November 13, 2025
**Status:** ✅ Configured

## Overview

MCP (Model Context Protocol) servers in ToolBoxAI-Solutions require environment variables to connect to databases, APIs, and services. This guide explains how to configure these variables.

## Required Environment Variables

| Variable | Required By | Purpose |
|----------|-------------|---------|
| `DATABASE_URL` | postgres, toolboxai-mcp, educational, analytics, roblox, agent-coordinator | PostgreSQL connection |
| `REDIS_URL` | toolboxai-mcp, orchestrator, monitor, educational, analytics, roblox, agent-coordinator | Redis connection |
| `JWT_SECRET_KEY` | toolboxai-mcp | JWT token generation |
| `OPENAI_API_KEY` | toolboxai-educational | OpenAI GPT-4.1 API access |
| `ROBLOX_API_KEY` | toolboxai-roblox | Roblox API integration |
| `GITHUB_TOKEN` | github | GitHub API access |

## Solution Options

### Option 1: Export Variables Before Starting Claude Code (Recommended)

**For bash/zsh users:**
```bash
# Load environment variables from .env
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
source .mcp-env.sh

# Start Claude Code
claude
```

**For permanent setup, add to ~/.zshrc or ~/.bashrc:**
```bash
# Auto-load ToolBoxAI MCP environment when in project
if [ -f "$PWD/.mcp-env.sh" ]; then
    source "$PWD/.mcp-env.sh"
fi
```

### Option 2: Use direnv (Automatic Loading)

**Install direnv:**
```bash
brew install direnv

# Add to ~/.zshrc
eval "$(direnv hook zsh)"
```

**Create .envrc in project root:**
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
cat > .envrc << 'EOF'
#!/bin/bash
# Load environment variables from .env
set -a
source .env
set +a

echo "✅ ToolBoxAI MCP environment loaded"
EOF

# Allow direnv to load .envrc
direnv allow
```

Now environment variables load automatically when you `cd` into the project!

### Option 3: Python MCP Servers Load .env Internally

**Ensure python-dotenv is installed:**
```bash
source venv/bin/activate
pip install python-dotenv
```

**Python MCP servers should include at startup:**
```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Verify required variables
required_vars = ['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing environment variables: {missing}")
```

### Option 4: System-Wide Environment (macOS)

**For system-wide availability:**
```bash
# Add to ~/.zshenv (loads for all shells)
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."
# ... etc

# Reload shell
exec zsh
```

⚠️ **Security Warning:** Never commit actual credentials to git!

## Verification

**Check if variables are available:**
```bash
# Test individual variables (output will be truncated for security)
echo ${DATABASE_URL:0:30}...
echo ${REDIS_URL:0:30}...
echo ${JWT_SECRET_KEY:0:10}...

# Or use the verification script
./scripts/verify-env.sh
```

**Test MCP server startup:**
```bash
# Test a simple MCP server (memory server doesn't need env vars)
npx -y @modelcontextprotocol/server-memory

# Test a Python MCP server
source venv/bin/activate
python -m core.mcp.server --test
```

## Troubleshooting

### Issue: "Missing environment variables" warning

**Cause:** Variables not exported to shell environment

**Solution:**
```bash
# Option A: Source .mcp-env.sh before starting Claude
source .mcp-env.sh

# Option B: Export manually
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."

# Option C: Use direnv (see Option 2 above)
```

### Issue: MCP servers fail to connect

**Check variable values:**
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/dbname

# Verify REDIS_URL format
echo $REDIS_URL
# Should be: redis://:password@host:port/db

# Test connections
psql $DATABASE_URL -c "SELECT version();"
redis-cli -u $REDIS_URL ping
```

### Issue: Variables work in terminal but not in Claude Code

**Cause:** Claude Code may start with different environment

**Solution:**
```bash
# Export variables globally in ~/.zshenv (not ~/.zshrc)
# ~/.zshenv loads for ALL zsh instances, including non-interactive

# Or start Claude Code from terminal where vars are exported
source .mcp-env.sh
claude
```

## MCP Server Status

After loading environment variables, MCP servers should show:

```
✅ postgres - PostgreSQL database access
✅ toolboxai-mcp - Main ToolBoxAI MCP server
✅ toolboxai-orchestrator - Agent orchestration
✅ toolboxai-monitor - System monitoring
✅ toolboxai-educational - Educational content
✅ toolboxai-analytics - Analytics processing
✅ toolboxai-roblox - Roblox integration
✅ toolboxai-agent-coordinator - Agent coordination
```

## Security Best Practices

1. **Never commit .env files** - Use .env.example as template
2. **Use strong, random keys** - Generate with `openssl rand -hex 32`
3. **Rotate credentials regularly** - Especially for production
4. **Restrict permissions** - `chmod 600 .env`
5. **Use separate environments** - Different .env for dev/staging/prod
6. **Audit access** - Monitor who has access to .env files

## References

- **Main .env file:** `/.env` (not tracked in git)
- **Template:** `/.env.example` (tracked in git)
- **Loader script:** `/.mcp-env.sh`
- **MCP Configuration:** `/.mcp.json`
- **Documentation:** `/docs/10-security/ENV_FILES_DOCUMENTATION.md`

---

**For more help:**
- See `/docs/10-security/ENV_FILES_DOCUMENTATION.md`
- See `/.env.example` for variable formats
- Run `./scripts/verify-env.sh` for validation
