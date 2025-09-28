# MCP and Agent Configuration Guide (2025)

## Overview

This document describes the Model Context Protocol (MCP) and Agent configuration for the ToolBoxAI-Solutions project, updated to comply with Claude Code 2025 specifications.

## Configuration Files Structure

```
ToolBoxAI-Solutions/
├── .mcp.json                    # Project-level MCP servers (team shared)
├── .claude/
│   ├── settings.json            # Project hooks and permissions
│   ├── agents/                  # Project-specific agents
│   │   ├── doc-researcher.md
│   │   ├── code-reviewer.md
│   │   ├── test-runner.md
│   │   └── ... (other agents)
│   └── logs/                    # Hook execution logs
│
~/.claude/                        # User-level configuration
├── mcp.json                     # User-level MCP servers
├── settings.json                # User-level hooks and settings
└── agents/                      # User-level agents
```

## MCP Server Configuration

### Project-Level Servers (`.mcp.json`)

The project includes the following MCP servers:

1. **filesystem** - File system access with security restrictions
2. **ide** - IDE integration for Cursor/Claude Code
3. **git** - Git repository management
4. **github** - GitHub API integration
5. **docker** - Docker container management
6. **postgres** - PostgreSQL database access
7. **memory** - Persistent context memory
8. **toolboxai-orchestrator** - Custom orchestrator for agent coordination

### Key Features

- **Environment Variable Expansion**: Uses `${VAR}` syntax
- **Scope Definition**: Each server includes `"scope": "project"`
- **Security Restrictions**: Filesystem server denies sensitive paths
- **Default Values**: Environment variables support defaults with `${VAR:-default}`

### User-Level Servers (`~/.claude/mcp.json`)

Additional global MCP servers include:
- **brave-search** - Web search capabilities
- **shell** - Safe shell command execution
- **time** - Time and date utilities
- **math** - Mathematical operations

## Hooks Configuration

### Project Hooks (`.claude/settings.json`)

The project implements comprehensive hooks for workflow automation:

#### 1. **UserPromptSubmit**
- Logs all user prompts for audit trails
- Creates session context

#### 2. **PreToolUse**
- Logs Python script executions
- Tracks NPM commands
- Blocks direct .env file modifications for security

#### 3. **PostToolUse**
- Tracks git commits
- Logs file modifications via MultiEdit

#### 4. **SessionStart/SessionEnd**
- Initializes logging infrastructure
- Activates Python virtual environment
- Tracks session duration

#### 5. **PreCompact**
- Logs context compaction events
- Monitors token usage

#### 6. **Notification**
- Captures errors and warnings
- Maintains separate log files for different severity levels

### Hook Security Features

- **Input Validation**: All hook commands use absolute paths
- **Shell Escaping**: Proper quoting of variables
- **Access Control**: Deny list for sensitive operations
- **Audit Logging**: Comprehensive logging of all operations

## Agent Configuration (2025 Format)

### Agent Definition Structure

```yaml
---
name: agent-name
description: Brief description of agent purpose
tools: Read, Write, Grep, Bash  # Comma-separated tool list
mentionable: true                # Enable @-mentions
category: research|quality|testing|development
---

# Agent Name

[Detailed agent instructions in Markdown]
```

### Updated Agents

All agents have been updated to include:
- **tools** field specifying allowed tools
- **mentionable** flag for @-mention support
- **category** for organization
- Detailed system prompts and responsibilities

### Agent Categories

- **research**: Documentation and information gathering
- **quality**: Code review and quality assurance
- **testing**: Test execution and coverage
- **development**: Code generation and implementation
- **orchestration**: Multi-agent coordination

## Permissions System

### Allow List
- Python operations (`pip`, `python`, `pytest`)
- Node.js operations (`npm`, `npx`, `node`)
- Git operations
- Database operations (`psql`, `redis-cli`)
- File operations (with restrictions)

### Deny List
- System-level commands (`sudo`, `rm -rf /`)
- Sensitive file access (SSH keys, credentials)
- Destructive operations

### Ask List
- Potentially dangerous operations requiring confirmation
- Environment file modifications
- Force push operations

## Environment Variables

### Project-Level
- `CLAUDE_PROJECT_DIR`: Project root directory
- `CLAUDE_PYTHON_PATH`: Python interpreter path
- `CLAUDE_NODE_PATH`: Node modules bin path

### Integration Variables
- `GITHUB_TOKEN`: GitHub API access
- `PUSHER_*`: Pusher service credentials
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection

## Custom Commands

The configuration includes shortcuts for common operations:
- `test`: Run all tests
- `dev`: Start development environment
- `backend`: Start backend server
- `dashboard`: Start dashboard
- `typecheck`: Run TypeScript type checking

## Logging Structure

All hook executions generate logs in `.claude/logs/`:
- `audit.log`: User prompt history
- `sessions.log`: Session start/end times
- `python_exec.log`: Python script executions
- `npm_exec.log`: NPM command history
- `git_commits.log`: Git commit history
- `file_changes.log`: File modification tracking
- `errors.log`: Error notifications
- `warnings.log`: Warning notifications
- `compaction.log`: Context compaction events

## Usage Examples

### Invoking Agents

```bash
# Using @-mentions (2025 feature)
@doc-researcher find documentation about MCP configuration

# Using /agent command
/agent doc-researcher

# Agents are auto-invoked based on task description
"Review this code for security issues"  # Triggers code-reviewer
```

### MCP Server Commands

```bash
# List available MCP servers
/mcp list

# Test MCP server connection
/mcp test filesystem

# View MCP server logs
/mcp logs toolboxai-orchestrator
```

### Hook Testing

```bash
# Test hooks are working
echo "test" > test_file.txt  # Should trigger PostToolUse hook

# Check hook logs
cat .claude/logs/file_changes.log
```

## Troubleshooting

### MCP Server Issues

1. **Server not starting**: Check environment variables are set
2. **Connection refused**: Verify ports are not in use
3. **Authentication errors**: Check tokens and credentials

### Hook Issues

1. **Hooks not executing**: Verify settings.json is valid JSON
2. **Permission denied**: Check file permissions for log directory
3. **Command not found**: Use absolute paths in hook commands

### Agent Issues

1. **Agent not found**: Check agent file has .md extension
2. **@-mention not working**: Ensure `mentionable: true` is set
3. **Tools not available**: Verify tools are listed in agent frontmatter

## Best Practices

1. **Security First**: Always validate inputs in hooks
2. **Use Scopes**: Define appropriate scopes for MCP servers
3. **Log Everything**: Comprehensive logging for debugging
4. **Test Hooks**: Test hooks in safe environment first
5. **Document Agents**: Provide clear agent instructions
6. **Version Control**: Track all configuration changes

## Migration Notes

### From Pre-2025 to 2025 Format

1. **Scope Renaming**:
   - Old: `"scope": "global"` → New: `"scope": "user"`
   - Old: `"scope": "project"` → New: `"scope": "local"`
   - New: `"scope": "project"` for team sharing

2. **Agent Format**:
   - Add `tools` field to all agents
   - Add `mentionable: true` for @-mention support
   - Add `category` for organization

3. **Hook Events**:
   - New: `SessionStart` event added
   - Enhanced: `Notification` event with matchers

4. **Environment Variables**:
   - Use `${VAR}` instead of `$VAR`
   - Support defaults: `${VAR:-default}`

## Security Considerations

1. **Never store secrets in configuration files**
2. **Use environment variables for sensitive data**
3. **Implement proper access controls in hooks**
4. **Validate all user inputs**
5. **Log security-relevant events**
6. **Regularly review and update permissions**

## Support and Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/)
- [MCP Protocol Specification](https://modelcontextprotocol.org/)
- [Project Issues](https://github.com/GrayGhostDev/ToolBoxAI-Solutions/issues)

---

*Last Updated: 2025-09-18*
*Configuration Version: 2.0.0*