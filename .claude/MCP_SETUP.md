# MCP (Model Context Protocol) Configuration

## Overview
This project is configured with MCP servers to enhance Claude Code's capabilities with specialized tools and integrations.

## Active MCP Servers

### 1. Filesystem Server
- **Purpose**: Secure filesystem access within project boundaries
- **Path**: `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions`
- **Restrictions**: Excludes sensitive directories (Library, .ssh, venv, node_modules, .git)

### 2. Git Server
- **Purpose**: Git repository management and version control
- **Features**: Commit history, branch management, diff viewing

### 3. GitHub Server
- **Purpose**: GitHub API integration
- **Repository**: GrayGhostDev/ToolBoxAI-Solutions
- **Auth**: Uses GITHUB_TOKEN environment variable

### 4. PostgreSQL Server
- **Purpose**: Database access for educational platform
- **Database**: educational_platform_dev
- **Connection**: localhost:5432 with eduplatform user

### 5. Memory Server
- **Purpose**: Persistent context storage across sessions
- **Storage**: `.claude/memory/` directory
- **Usage**: Stores important context and decisions

### 6. ToolBoxAI Orchestrator
- **Purpose**: Custom MCP server for agent coordination
- **Location**: `core/mcp/server.py`
- **Features**: Agent orchestration, task distribution, real-time sync

## Configuration Files

### `.mcp.json` (Project Root)
Main MCP server configuration file that defines all available servers.

### `.claude/settings.local.json`
Claude Code settings that enable MCP servers and configure permissions.

### `.claude/mcp.json`
Backup configuration with additional project-specific settings.

## Testing MCP Setup

Run the test script to verify MCP configuration:
```bash
python scripts/mcp/test_mcp_setup.py
```

## Environment Variables Required

Set these in your `.env` file or shell environment:
- `GITHUB_TOKEN`: GitHub personal access token
- `PUSHER_APP_ID`: Pusher application ID
- `PUSHER_KEY`: Pusher public key
- `PUSHER_SECRET`: Pusher secret key
- `PUSHER_CLUSTER`: Pusher cluster region

## Troubleshooting

### Server Not Starting
1. Check that all required npm packages are installed
2. Verify environment variables are set
3. Check logs in `.claude/logs/`

### Permission Denied
1. Review `.claude/settings.local.json` permissions
2. Ensure filesystem server has correct path access

### Database Connection Failed
1. Verify PostgreSQL is running
2. Check database credentials in `.env`
3. Test connection with: `psql -U eduplatform -d educational_platform_dev`

## Security Notes

- MCP servers run with restricted permissions
- Sensitive directories are explicitly excluded
- Database credentials should use environment variables
- GitHub token should have minimal required scopes

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Claude Code MCP Guide](https://docs.anthropic.com/claude-code/mcp)
- Project MCP Implementation: `core/mcp/`