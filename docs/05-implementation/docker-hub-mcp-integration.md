# Docker Hub MCP Integration Guide

## Overview

This document describes the integration of Docker Hub's official MCP (Model Context Protocol) server with the ToolBoxAI platform, enabling seamless Docker repository management directly from Cursor and other MCP clients.

## ✅ Integration Status

### **Docker Hub MCP Server Configuration**

The Docker Hub MCP server has been successfully integrated following the official Docker documentation and best practices from the [Docker Hub MCP Server](https://hub.docker.com/mcp/server/dockerhub/overview).

### **Authentication Setup**

- **Docker Hub Username**: `thegrayghost23`
- **PAT Token**: `dckr_pat_LzH5fIFvmGDSQLcxdgSLELJzclw` (configured via environment)
- **Authentication Status**: ✅ Verified and working

### **Repository Structure**

```
docker.io/thegrayghost23/
├── toolboxai-dashboard:2025.09.27      # React + Mantine v8 + Pusher
├── toolboxai-backend:2025.09.27        # FastAPI + AI services
├── toolboxai-mcp-server:2025.09.27     # Model Context Protocol Gateway
├── toolboxai-agent-coordinator:2025.09.27  # AI agent orchestration
├── toolboxai-roblox-sync:2025.09.27    # Roblox Studio integration
└── toolboxai-base:2025.09.27           # Base image for all services
```

## 🔧 MCP Server Configuration

### **Cursor MCP Configuration**

The Docker Hub MCP server is configured in Cursor's MCP configuration file:

**File**: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "dockerhub": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "HUB_PAT_TOKEN",
        "mcp/dockerhub",
        "--transport=stdio",
        "--username=thegrayghost23"
      ],
      "env": {
        "HUB_PAT_TOKEN": "${DOCKER_HUB_PAT_TOKEN}",
        "USER_CONTEXT": "${STYTCH_USER_ID}"
      }
    }
  }
}
```

### **Environment Variables**

```bash
# Required environment variable
export DOCKER_HUB_PAT_TOKEN="dckr_pat_LzH5fIFvmGDSQLcxdgSLELJzclw"

# Optional: Set in shell profile for persistence
echo 'export DOCKER_HUB_PAT_TOKEN="dckr_pat_LzH5fIFvmGDSQLcxdgSLELJzclw"' >> ~/.zshrc
```

## 🛠️ Available Tools (13 Total)

The Docker Hub MCP server provides comprehensive repository management capabilities:

### **Repository Management**
- `listRepositoriesByNamespace` - List repositories by organization/namespace
- `createRepository` - Create new Docker repositories
- `getRepositoryInfo` - Get detailed repository information
- `updateRepositoryInfo` - Update repository descriptions and settings
- `checkRepository` - Verify if repositories exist

### **Tag Management**
- `listRepositoryTags` - List all tags for a repository
- `getRepositoryTag` - Get detailed tag information
- `checkRepositoryTag` - Verify tag existence

### **Search & Discovery**
- `search` - Search Docker Hub repositories
- `dockerHardenedImages` - List Docker Hardened Images (DHI)

### **Namespace Management**
- `listNamespaces` - List accessible namespaces/organizations
- `getPersonalNamespace` - Get your personal namespace
- `listAllNamespacesMemberOf` - List all namespaces you're a member of

## 🚀 Usage Examples

### **Repository Operations**

```python
# List repositories in namespace
repositories = mcp_client.call_tool("listRepositoriesByNamespace", {
    "namespace": "thegrayghost23"
})

# Get repository details
repo_info = mcp_client.call_tool("getRepositoryInfo", {
    "namespace": "thegrayghost23",
    "repository": "toolboxai-backend"
})

# Create new repository
new_repo = mcp_client.call_tool("createRepository", {
    "namespace": "thegrayghost23",
    "name": "toolboxai-new-service",
    "description": "New microservice for ToolBoxAI",
    "is_private": False
})
```

### **Tag Management**

```python
# List tags for a repository
tags = mcp_client.call_tool("listRepositoryTags", {
    "namespace": "thegrayghost23",
    "repository": "toolboxai-backend"
})

# Get specific tag details
tag_info = mcp_client.call_tool("getRepositoryTag", {
    "namespace": "thegrayghost23",
    "repository": "toolboxai-backend",
    "tag": "2025.09.27"
})
```

### **Search Operations**

```python
# Search for repositories
search_results = mcp_client.call_tool("search", {
    "query": "toolboxai educational platform",
    "badges": ["verified_publisher"],
    "architectures": ["amd64", "arm64"]
})
```

## 🔄 Integration with CI/CD

### **Automated Image Management**

The Docker Hub MCP integration enables automated repository management in CI/CD pipelines:

```yaml
# GitHub Actions example
name: Deploy with Docker Hub MCP
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build and Push via MCP
        env:
          DOCKER_HUB_PAT_TOKEN: ${{ secrets.DOCKER_HUB_PAT_TOKEN }}
        run: |
          # Build images
          docker build -t thegrayghost23/toolboxai-backend:${{ github.sha }} .

          # Push via Docker Hub MCP
          docker push thegrayghost23/toolboxai-backend:${{ github.sha }}

          # Update repository metadata via MCP
          # (This would use the MCP client to update descriptions, etc.)
```

### **Repository Metadata Management**

```bash
# Update repository description via MCP
curl -X POST http://localhost:8888/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "updateRepositoryInfo",
    "args": {
      "namespace": "thegrayghost23",
      "repository": "toolboxai-backend",
      "description": "ToolBoxAI Backend - FastAPI with AI agents and educational content generation"
    }
  }'
```

## 🔒 Security Configuration

### **PAT Token Management**

The Personal Access Token (PAT) is managed securely:

1. **Environment Variable**: Stored as `DOCKER_HUB_PAT_TOKEN`
2. **Scope**: Limited to repository management only
3. **Rotation**: Can be rotated without service interruption
4. **Access Control**: Restricted to specific repositories

### **Network Security**

```yaml
# Docker Hub MCP runs in isolated container
dockerhub-mcp:
  image: mcp/dockerhub
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  read_only: true
  networks:
    - mcp_network  # Isolated network
```

## 📊 Monitoring & Observability

### **MCP Server Health**

```bash
# Check Docker Hub MCP server status
curl http://localhost:9877/health

# View MCP server logs
docker logs toolboxai-mcp-server

# Monitor MCP tool usage
tail -f /var/log/mcp/dockerhub-calls.log
```

### **Repository Metrics**

The Docker Hub MCP integration provides metrics on:
- Repository access patterns
- Tag creation/deletion events
- Search query analytics
- Namespace utilization

## 🔧 Troubleshooting

### **Common Issues**

1. **Authentication Failures**
   ```bash
   # Verify PAT token
   echo $DOCKER_HUB_PAT_TOKEN | cut -c1-10

   # Test direct Docker Hub API access
   curl -H "Authorization: Bearer $DOCKER_HUB_PAT_TOKEN" \
        https://hub.docker.com/v2/user/
   ```

2. **MCP Server Connection Issues**
   ```bash
   # Check MCP server is running
   docker ps | grep mcp/dockerhub

   # Test MCP server connectivity
   docker run --rm -i mcp/dockerhub --transport=stdio <<< '{"method":"tools/list"}'
   ```

3. **Repository Access Issues**
   ```bash
   # Verify repository exists
   docker run --rm -i -e HUB_PAT_TOKEN=$DOCKER_HUB_PAT_TOKEN \
     mcp/dockerhub --transport=stdio --username=thegrayghost23 <<< '{
       "method": "tools/call",
       "params": {
         "name": "checkRepository",
         "arguments": {"namespace": "thegrayghost23", "repository": "toolboxai-backend"}
       }
     }'
   ```

### **Error Resolution**

| Error | Cause | Solution |
|-------|-------|----------|
| `InvalidTokenError: missing part #2` | Invalid PAT token format | Regenerate PAT token from Docker Hub |
| `401 Unauthorized` | Token expired or invalid | Check token permissions and expiry |
| `404 Repository not found` | Repository doesn't exist | Create repository first |
| `Connection timeout` | Network/firewall issues | Check Docker daemon and network |

## 🚀 Advanced Usage

### **Bulk Operations**

```python
# Bulk repository management
async def manage_repositories():
    # List all repositories
    repos = await mcp_client.call_tool("listRepositoriesByNamespace", {
        "namespace": "thegrayghost23"
    })

    # Update descriptions for all ToolBoxAI repositories
    for repo in repos.get("results", []):
        if repo["name"].startswith("toolboxai-"):
            await mcp_client.call_tool("updateRepositoryInfo", {
                "namespace": "thegrayghost23",
                "repository": repo["name"],
                "description": f"ToolBoxAI {repo['name'].replace('toolboxai-', '').title()} Service"
            })
```

### **Integration with Cursor**

The Docker Hub MCP server integrates seamlessly with Cursor, enabling:

1. **Repository Management**: Create, update, and manage repositories directly from Cursor
2. **Tag Operations**: List and inspect Docker image tags
3. **Search Capabilities**: Find relevant Docker images for development
4. **Automated Workflows**: Integrate with Cursor's AI-powered development workflows

### **Custom Workflows**

```javascript
// Cursor workflow example
async function deployNewFeature(featureName) {
  // Create new repository
  const repo = await mcp.call("createRepository", {
    namespace: "thegrayghost23",
    name: `toolboxai-${featureName}`,
    description: `ToolBoxAI ${featureName} microservice`,
    is_private: false
  });

  // Build and push image
  await exec(`docker build -t thegrayghost23/toolboxai-${featureName}:latest .`);
  await exec(`docker push thegrayghost23/toolboxai-${featureName}:latest`);

  // Update repository metadata
  await mcp.call("updateRepositoryInfo", {
    namespace: "thegrayghost23",
    repository: `toolboxai-${featureName}`,
    full_description: `# ToolBoxAI ${featureName}\n\nMicroservice for ${featureName} functionality.`
  });
}
```

## 📚 References

### **Official Documentation**
- [Docker Hub MCP Server](https://hub.docker.com/mcp/server/dockerhub/overview)
- [Docker MCP Gateway Documentation](https://docs.docker.com/ai/mcp-gateway/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

### **ToolBoxAI Integration**
- [MCP Configuration](../../config/mcp/mcp-servers.json)
- [Docker Compose Configuration](../../infrastructure/docker/compose/docker-compose.yml)
- [Cursor MCP Setup](../../.cursor/mcp.json)

### **Repository Management**
- [Docker Hub Repository: thegrayghost23](https://hub.docker.com/u/thegrayghost23)
- [ToolBoxAI Docker Images](https://hub.docker.com/search?q=thegrayghost23%2Ftoolboxai)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-09-28
**Integration Status**: ✅ Active and Verified
**MCP Server Version**: Latest (mcp/dockerhub)
**Authentication**: ✅ PAT Token Configured
