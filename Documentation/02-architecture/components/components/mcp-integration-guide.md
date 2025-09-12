# ToolboxAI MCP Integration Guide

## ✅ MCP Servers and Agents Status

### 🟢 Working Services

- **MCP Server**: ✅ Running on ws://localhost:9876
- **FastAPI Server**: ✅ Running on http://127.0.0.1:8008
- **Flask Bridge Server**: ✅ Running on http://127.0.0.1:5001

### 🟡 Services with Import Issues

- Individual Agent files (Content, Quiz, Terrain, Script, Review) have relative import issues when run directly
- These can be accessed through the main orchestrator or server endpoints

## 🚀 Quick Start

### 1. Start MCP Servers

```bash
# Start all MCP servers and agents
./scripts/start_mcp_servers.sh

# Check status
./scripts/check_mcp_status.sh

# Stop all services
./scripts/stop_mcp_servers.sh
```text
### 2. Configure Cursor

The MCP configuration file `mcpServers.json` has been created with all available servers:

```json
{
  "mcpServers": {
    "ToolboxAI-MCP-Server": {
      "command": "python",
      "args": ["/path/to/mcp/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/project/ToolboxAI-Roblox-Environment:/path/to/project/src/shared",
        "MCP_HOST": "localhost",
        "MCP_PORT": "9876"
      }
    }
    // ... other servers
  }
}
```text
### 3. Available Endpoints

#### MCP WebSocket Server

- **URL**: ws://localhost:9876
- **Purpose**: Real-time context management for AI agents
- **Features**: Token-aware context, priority-based pruning, multi-client sync

#### FastAPI Main Server

- **URL**: http://127.0.0.1:8008
- **Documentation**: http://127.0.0.1:8008/docs
- **Purpose**: Primary API server with AI capabilities
- **Features**: Content generation, authentication, LMS integration

#### Flask Bridge Server

- **URL**: http://127.0.0.1:5001
- **Purpose**: Lightweight bridge for Roblox Studio plugin
- **Features**: Plugin registration, simplified content generation

## 🔧 Configuration Files

### Cursor Settings

- **File**: `.cursor/settings.json`
- **Updated**: All paths corrected for new directory structure
- **Python Interpreter**: Points to `src/roblox-environment/venv_clean/bin/python`

### MCP Configuration

- **File**: `mcpServers.json`
- **Purpose**: Cursor MCP server configuration
- **Contains**: All ToolboxAI servers and agents

### Environment

- **File**: `.env.template`
- **Purpose**: Environment variable template
- **Required**: OPENAI_API_KEY for full functionality

## 🛠️ Management Scripts

### Setup Script

```bash
./scripts/setup_mcp_environment.sh
```text
- Creates virtual environment
- Installs dependencies
- Tests imports
- Creates configuration files

### Startup Scripts

```bash
./scripts/start_mcp_servers.sh    # Start all services
./scripts/stop_mcp_servers.sh     # Stop all services
./scripts/check_mcp_status.sh     # Check service status
```text
## 🧪 Testing

### Test MCP Setup

```bash
source ToolboxAI-Roblox-Environment/venv_clean/bin/activate
python scripts/test_mcp_setup.py
```text
### Test Individual Components

```bash
# Test MCP server
curl -s http://localhost:9876

# Test FastAPI server
curl -s http://127.0.0.1:8008/health

# Test Flask bridge
curl -s http://127.0.0.1:5001/status
```text
## 📊 Current Status

### ✅ Completed

1. **Cursor Settings Updated**: All paths corrected for new directory structure
2. **MCP Configuration Created**: Comprehensive `mcpServers.json` with all servers
3. **Startup Scripts Created**: Automated service management
4. **Core Services Running**: MCP, FastAPI, and Flask servers operational
5. **Environment Setup**: Virtual environment with all dependencies

### 🔄 Next Steps

1. **Fix Agent Imports**: Resolve relative import issues in individual agent files
2. **Test Cursor Integration**: Verify MCP servers work with Cursor
3. **API Key Configuration**: Set up OPENAI_API_KEY for full functionality
4. **Agent Testing**: Test individual agents through orchestrator endpoints

## 🎯 Usage with Cursor

1. **Start Services**: Run `./scripts/start_mcp_servers.sh`
2. **Configure Cursor**: Use the `mcpServers.json` configuration
3. **Test Connection**: Verify MCP servers are accessible in Cursor
4. **Use Agents**: Access AI agents through the MCP protocol

## 📝 Logs

- **Location**: `logs/` directory
- **Files**: One log file per service
- **Monitoring**: Use `./scripts/check_mcp_status.sh` for status overview

## 🔗 Integration Points

- **Roblox Studio**: Flask bridge server (port 5001)
- **Web Dashboard**: FastAPI server (port 8008)
- **AI Agents**: MCP WebSocket server (port 9876)
- **Cursor IDE**: MCP protocol integration

---

**Status**: ✅ Core MCP infrastructure operational
**Next**: Configure Cursor to use MCP servers and test agent functionality
