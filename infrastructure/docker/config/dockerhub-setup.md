# Docker Hub Setup for ToolboxAI - 2025 Configuration

## Overview
This document outlines the proper Docker Hub setup for the ToolboxAI project, including repository creation, image tagging, and automated CI/CD integration.

## Docker Hub Repository Structure

### Recommended Repository Organization
```
toolboxai/
├── dashboard          # React frontend with Nginx
├── backend           # FastAPI backend service
├── mcp-server        # Model Context Protocol server
├── agent-coordinator # AI agent coordination service
├── roblox-bridge     # Roblox integration service
├── ghost-cms         # Ghost CMS service
└── base              # Shared base image
```

## Repository Creation Commands

### 1. Create Dashboard Repository
```bash
# Create the main dashboard repository
docker tag toolboxai/dashboard:latest toolboxai/dashboard:2025.09.27
docker tag toolboxai/dashboard:latest toolboxai/dashboard:latest

# Push to Docker Hub
docker push toolboxai/dashboard:2025.09.27
docker push toolboxai/dashboard:latest
```

### 2. Create Backend Repository
```bash
# Create the backend repository
docker tag toolboxai/backend:latest toolboxai/backend:2025.09.27
docker tag toolboxai/backend:latest toolboxai/backend:latest

# Push to Docker Hub
docker push toolboxai/backend:2025.09.27
docker push toolboxai/backend:latest
```

### 3. Create Service Repositories
```bash
# MCP Server
docker tag toolboxai/mcp-server:latest toolboxai/mcp-server:2025.09.27
docker push toolboxai/mcp-server:2025.09.27

# Agent Coordinator
docker tag toolboxai/agent-coordinator:latest toolboxai/agent-coordinator:2025.09.27
docker push toolboxai/agent-coordinator:2025.09.27

# Roblox Bridge
docker tag toolboxai/roblox-bridge:latest toolboxai/roblox-bridge:2025.09.27
docker push toolboxai/roblox-bridge:2025.09.27

# Ghost CMS
docker tag toolboxai/ghost-cms:latest toolboxai/ghost-cms:2025.09.27
docker push toolboxai/ghost-cms:2025.09.27
```

## Docker Hub Repository Configuration

### Repository Settings
- **Visibility**: Public (for open-source) or Private (for proprietary)
- **Description**: Educational AI platform with real-time collaboration
- **README**: Link to project documentation
- **Build Settings**: Automated builds from GitHub

### Automated Build Configuration
```yaml
# .github/workflows/docker-build.yml
name: Docker Build and Push

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: docker.io
  NAMESPACE: toolboxai

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [dashboard, backend, mcp-server, agent-coordinator, roblox-bridge]

    steps:
    - name: Checkout
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
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=raw,value=latest,enable={{is_default_branch}}
          type=raw,value={{date 'YYYY.MM.DD'}}

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        file: infrastructure/docker/dockerfiles/${{ matrix.service }}.Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        build-args: |
          BUILDKIT_INLINE_CACHE=1
          NODE_ENV=production
```

## Image Tagging Strategy

### Semantic Versioning
```bash
# Production releases
toolboxai/dashboard:1.0.0
toolboxai/dashboard:1.0
toolboxai/dashboard:1
toolboxai/dashboard:latest

# Development builds
toolboxai/dashboard:develop
toolboxai/dashboard:2025.09.27
toolboxai/dashboard:pr-123

# Feature branches
toolboxai/dashboard:feature-pusher-integration
toolboxai/dashboard:feature-mantine-v8
```

### Build Commands
```bash
# Build all services
docker-compose -f infrastructure/docker/compose/docker-compose.yml build

# Tag for Docker Hub
docker tag toolboxai-dashboard:latest toolboxai/dashboard:2025.09.27
docker tag toolboxai-backend:latest toolboxai/backend:2025.09.27

# Push to Docker Hub
docker push toolboxai/dashboard:2025.09.27
docker push toolboxai/backend:2025.09.27
```

## Repository Descriptions

### Dashboard Repository
```
ToolboxAI Dashboard Frontend

Modern React 18 application with:
- Mantine v8.3.1 UI components
- Pusher real-time communication
- TypeScript support
- Nginx production server
- Docker multi-stage build

Educational platform for AI-powered learning experiences.
```

### Backend Repository
```
ToolboxAI Backend API

FastAPI backend service with:
- Python 3.12 async support
- PostgreSQL database integration
- Redis caching
- Pusher server integration
- JWT authentication
- Comprehensive API documentation

RESTful API for educational AI platform.
```

### MCP Server Repository
```
ToolboxAI MCP Server

Model Context Protocol server for:
- AI model coordination
- Context management
- Multi-model support
- Performance monitoring

Enables seamless AI model integration.
```

## Security Configuration

### Docker Hub Secrets
```bash
# Required secrets for GitHub Actions
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_TOKEN=your_dockerhub_access_token

# Optional for private repositories
DOCKERHUB_NAMESPACE=toolboxai
```

### Image Scanning
- Enable vulnerability scanning on Docker Hub
- Configure automated security updates
- Set up notifications for security issues

## Multi-Architecture Support

### Build for Multiple Platforms
```bash
# Create multi-arch builder
docker buildx create --name multiarch --use

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t toolboxai/dashboard:2025.09.27 \
  -f infrastructure/docker/dockerfiles/dashboard.Dockerfile \
  --push .
```

## Monitoring and Maintenance

### Image Cleanup Policy
- Keep latest 10 tags per repository
- Remove tags older than 90 days
- Maintain LTS versions indefinitely

### Update Schedule
- Weekly security updates
- Monthly dependency updates
- Quarterly major version updates

## Usage Examples

### Pull and Run
```bash
# Pull latest dashboard
docker pull toolboxai/dashboard:latest

# Run with Docker Compose
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
  --env-file infrastructure/docker/config/environment.env \
  up -d
```

### Development Workflow
```bash
# Build locally
docker build -t toolboxai/dashboard:dev \
  -f infrastructure/docker/dockerfiles/dashboard.Dockerfile \
  apps/dashboard/

# Test locally
docker run -p 5180:80 toolboxai/dashboard:dev

# Push to Docker Hub
docker tag toolboxai/dashboard:dev toolboxai/dashboard:2025.09.27
docker push toolboxai/dashboard:2025.09.27
```

---

**Next Steps:**
1. Configure Docker Hub access token
2. Create repositories on Docker Hub
3. Set up automated builds
4. Configure image scanning
5. Implement multi-architecture builds
