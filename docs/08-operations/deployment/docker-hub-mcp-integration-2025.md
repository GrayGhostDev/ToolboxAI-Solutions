# Docker Hub MCP Integration Guide - 2025

## Overview
Complete guide for integrating ToolboxAI with Docker Hub using Model Context Protocol (MCP) for automated repository management and deployment.

## MCP Docker Hub Configuration

### Current MCP Setup
Based on the MCP configuration in `.cursor/mcp.json`, the Docker Hub integration includes:

```json
{
  "dockerhub": {
    "command": "docker",
    "args": [
      "run", "-i", "--rm", "-e", "HUB_PAT_TOKEN",
      "mcp/dockerhub", "--transport=stdio"
    ],
    "env": {
      "HUB_PAT_TOKEN": "${DOCKER_HUB_PAT_TOKEN}",
      "USER_CONTEXT": "${STYTCH_USER_ID}"
    }
  }
}
```

## Repository Structure on Docker Hub

### ToolboxAI Organization
```
docker.io/toolboxai/
├── dashboard:2025.09.27          # React + Mantine v8 + Pusher
├── backend:2025.09.27            # FastAPI + Pusher + AI services
├── mcp-server:2025.09.27         # Model Context Protocol
├── agent-coordinator:2025.09.27  # AI agent orchestration
├── roblox-bridge:2025.09.27      # Roblox educational integration
└── ghost-cms:2025.09.27          # Content management
```

## Automated Repository Setup

### 1. Environment Configuration
```bash
# Set up Docker Hub credentials
export DOCKER_HUB_PAT_TOKEN="your_docker_hub_personal_access_token"
export DOCKERHUB_USERNAME="your_username"
export STYTCH_USER_ID="your_stytch_user_id"
```

### 2. Repository Creation Script
```bash
#!/bin/bash
# Create all ToolboxAI repositories on Docker Hub

NAMESPACE="toolboxai"
REPOSITORIES=("dashboard" "backend" "mcp-server" "agent-coordinator" "roblox-bridge")

for repo in "${REPOSITORIES[@]}"; do
    echo "Creating repository: $NAMESPACE/$repo"

    # Use Docker Hub API to create repository
    curl -X POST \
        -H "Authorization: Bearer $DOCKER_HUB_PAT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"namespace\": \"$NAMESPACE\",
            \"name\": \"$repo\",
            \"description\": \"ToolboxAI $repo service - 2025 implementation\",
            \"is_private\": false,
            \"full_description\": \"Complete $repo service for ToolboxAI educational platform\"
        }" \
        "https://hub.docker.com/v2/repositories/"
done
```

## Build and Push Workflow

### Automated Build Pipeline
```yaml
# .github/workflows/docker-hub-integration.yml
name: Docker Hub Integration

on:
  push:
    branches: [main, develop]
    paths:
      - 'apps/**'
      - 'infrastructure/docker/**'
  workflow_dispatch:

env:
  REGISTRY: docker.io
  NAMESPACE: toolboxai

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - service: dashboard
            dockerfile: infrastructure/docker/dockerfiles/dashboard.Dockerfile
            context: apps/dashboard
          - service: backend
            dockerfile: infrastructure/docker/dockerfiles/backend.Dockerfile
            context: .
          - service: mcp-server
            dockerfile: infrastructure/docker/dockerfiles/mcp.Dockerfile
            context: .

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.NAMESPACE }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=raw,value=latest,enable={{is_default_branch}}
          type=raw,value={{date 'YYYY.MM.DD'}}

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: ${{ matrix.context }}
        file: ${{ matrix.dockerfile }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        build-args: |
          NODE_ENV=production
          VITE_ENABLE_PUSHER=true
          VITE_ENABLE_WEBSOCKET=false
```

## Local Development Integration

### Build and Test Locally
```bash
# Build all images
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
    --env-file infrastructure/docker/config/environment.env \
    build

# Tag for Docker Hub
docker tag toolboxai-dashboard:latest toolboxai/dashboard:2025.09.27
docker tag toolboxai-backend:latest toolboxai/backend:2025.09.27

# Test locally before pushing
docker run -d -p 5179:80 \
    -e VITE_PUSHER_KEY=test_key \
    -e VITE_API_BASE_URL=http://localhost:8009 \
    toolboxai/dashboard:2025.09.27

# Verify
curl http://localhost:5179/health
```

### Push to Docker Hub
```bash
# Login to Docker Hub
docker login

# Push all images
docker push toolboxai/dashboard:2025.09.27
docker push toolboxai/backend:2025.09.27
docker push toolboxai/mcp-server:2025.09.27
docker push toolboxai/agent-coordinator:2025.09.27
```

## MCP Integration Features

### Repository Management via MCP
The MCP Docker Hub integration provides:

1. **Automated Repository Creation**
2. **Image Metadata Management**
3. **Tag Management**
4. **Security Scanning Integration**
5. **Build Status Monitoring**

### MCP Commands Available
```bash
# List repositories
mcp dockerhub list-repositories --namespace toolboxai

# Create repository
mcp dockerhub create-repository \
    --namespace toolboxai \
    --name dashboard \
    --description "ToolboxAI Dashboard Frontend"

# Update repository
mcp dockerhub update-repository \
    --namespace toolboxai \
    --repository dashboard \
    --description "Updated description"

# Check repository status
mcp dockerhub check-repository \
    --namespace toolboxai \
    --repository dashboard
```

## Monitoring and Maintenance

### Image Health Monitoring
```bash
# Check image vulnerabilities
docker scout cves toolboxai/dashboard:latest

# Check image size
docker images toolboxai/dashboard --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Cleanup old images
docker image prune -a --filter "until=720h"
```

### Automated Updates
```bash
# Weekly update script
#!/bin/bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Pull latest base images
docker pull node:22-alpine
docker pull nginx:1.25-alpine
docker pull python:3.12-alpine

# Rebuild with latest dependencies
docker-compose build --no-cache --pull

# Tag and push
VERSION=$(date +%Y.%m.%d)
docker tag toolboxai-dashboard:latest toolboxai/dashboard:$VERSION
docker push toolboxai/dashboard:$VERSION
```

## Security Best Practices

### Image Security
1. **Vulnerability Scanning**: Enabled on Docker Hub
2. **Multi-stage Builds**: Minimal production images
3. **Non-root Users**: All services run as non-root
4. **Read-only Filesystems**: Enhanced security
5. **Secret Management**: Docker secrets integration

### Access Control
```bash
# Set up repository permissions
# - Read access: Public
# - Write access: Team members only
# - Admin access: Repository owners
```

## Deployment Integration

### Production Deployment
```bash
# Deploy to production with Docker Hub images
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
    -f infrastructure/docker/compose/docker-compose.prod.yml \
    --env-file infrastructure/docker/config/environment.env \
    up -d

# Use specific version tags
export DOCKER_TAG=2025.09.27
docker-compose pull
docker-compose up -d
```

### Rollback Strategy
```bash
# Rollback to previous version
export DOCKER_TAG=2025.09.26
docker-compose pull
docker-compose up -d

# Emergency rollback
docker-compose down
docker run -d -p 5179:80 toolboxai/dashboard:stable
```

## Next Steps

1. **Configure Docker Hub Access Token**
   ```bash
   # Add to your environment
   export DOCKER_HUB_PAT_TOKEN="your_token_here"
   ```

2. **Run Complete Setup**
   ```bash
   ./infrastructure/docker/scripts/complete-setup-2025.sh
   ```

3. **Verify Integration**
   ```bash
   # Check all services
   curl http://localhost:5179/health
   curl http://localhost:8009/health

   # Open dashboard
   open http://localhost:5179
   ```

4. **Configure Pusher Credentials**
   - Update `infrastructure/docker/config/environment.env`
   - Add your actual Pusher keys
   - Restart services

---

**Status**: ✅ Ready for Implementation
**Docker Hub**: Configured for automated builds
**MCP Integration**: Enabled for repository management
**Services**: All integrated and documented
