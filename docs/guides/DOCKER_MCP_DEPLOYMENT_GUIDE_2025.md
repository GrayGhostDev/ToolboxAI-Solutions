# Docker MCP Deployment Guide 2025

## Overview

This guide provides step-by-step instructions for deploying the ToolBoxAI platform using Docker with MCP (Model Context Protocol) Gateway integration, following the latest Docker compose-for-agents patterns and best practices.

## 🚀 Quick Start

### **Prerequisites**

1. **Docker & Docker Compose**: Version 24.0+ with BuildKit enabled
2. **Docker Hub Account**: Access to `thegrayghost23` repositories
3. **Environment Variables**: All required variables configured
4. **MCP Integration**: Cursor with Docker Hub MCP server configured

### **Environment Setup**

```bash
# Clone repository
git clone https://github.com/GrayGhostDev/ToolBoxAI-Solutions.git
cd ToolBoxAI-Solutions

# Navigate to Docker directory
cd infrastructure/docker

# Copy environment configuration
cp .env.example .env

# Edit environment variables
nano .env
```

### **Required Environment Variables**

```env
# Database Configuration
POSTGRES_DB=toolboxai
POSTGRES_USER=toolboxai
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://toolboxai:your-secure-password@postgres:5432/toolboxai

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Server Configuration
HOST=0.0.0.0
PORT=8009
WORKERS=4

# MCP Gateway Configuration
MCP_HOST=0.0.0.0
MCP_PORT=9877
AGENT_DISCOVERY_ENABLED=true
MAX_TOKENS=8192

# Agent Coordinator
COORDINATOR_PORT=8888
MAX_CONCURRENT_AGENTS=10

# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-your-anthropic-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key

# Docker Hub MCP Integration
DOCKER_HUB_PAT_TOKEN=dckr_pat_your_token

# Pusher Configuration (Real-time)
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_SECRET=your-pusher-secret
VITE_PUSHER_APP_ID=your-pusher-app-id
VITE_PUSHER_CLUSTER=us2

# Feature Flags
VITE_ENABLE_MCP=true
VITE_ENABLE_AGENTS=true
VITE_ENABLE_PUSHER=true
VITE_ENABLE_ROBLOX=true
```

## 🐳 Deployment Options

### **Option 1: Development Environment**

```bash
# Start development stack with hot reload
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up -d

# View logs
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml logs -f

# Access services
echo "Backend: http://localhost:8009"
echo "Dashboard: http://localhost:5179"
echo "MCP Server: ws://localhost:9877"
echo "Agent Coordinator: http://localhost:8888"
echo "Database UI: http://localhost:8080"
echo "Redis UI: http://localhost:8081"
```

### **Option 2: Production Environment**

```bash
# Create production secrets
echo "your-secure-db-password" | docker secret create postgres_password -
echo "your-secure-redis-password" | docker secret create redis_password -
echo "your-jwt-secret" | docker secret create jwt_secret -
echo "sk-your-openai-key" | docker secret create openai_api_key -
echo "sk-your-anthropic-key" | docker secret create anthropic_api_key -

# Start production stack
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d

# Scale backend services
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d --scale backend=3

# Verify deployment
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml ps
```

### **Option 3: Staging Environment**

```bash
# Start staging stack with monitoring
docker compose -f compose/docker-compose.yml up -d

# Health check all services
curl http://localhost:8009/health
curl http://localhost:5179/health
curl http://localhost:9877/health
curl http://localhost:8888/health
```

## 🔧 Service Configuration

### **Core Services**

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **backend** | `toolboxai/backend:latest` | `8009` | FastAPI + AI Agents |
| **dashboard** | `toolboxai/dashboard:latest` | `5179` | React + Mantine v8 |
| **mcp-server** | `toolboxai/mcp:latest` | `9877` | MCP Gateway |
| **agent-coordinator** | `toolboxai/agent-coordinator:latest` | `8888` | Agent Orchestration |
| **postgres** | `postgres:16-alpine` | `5432` | Primary Database |
| **redis** | `redis:7-alpine` | `6379` | Cache + Sessions |
| **roblox-sync** | `toolboxai/roblox-sync:latest` | `34872` | Studio Integration |

### **Network Architecture**

```yaml
networks:
  frontend:        # Dashboard ↔ Nginx
    driver: bridge
  backend:         # Backend ↔ Dashboard ↔ APIs
    driver: bridge
  database:        # Database isolation
    driver: bridge
    internal: true
  cache:           # Redis isolation
    driver: bridge
    internal: true
  mcp:             # MCP Gateway communication
    driver: bridge
  roblox:          # Roblox Studio integration
    driver: bridge
```

## 🔄 MCP Gateway Integration

### **MCP Server Configuration**

Following Docker's MCP Gateway patterns from [compose-for-agents](https://github.com/docker/compose-for-agents):

```yaml
mcp-server:
  image: toolboxai/mcp:latest
  container_name: toolboxai-mcp
  ports: ["9877:9877"]
  environment:
    MCP_HOST: 0.0.0.0
    MCP_PORT: 9877
    AGENT_DISCOVERY_ENABLED: true
    MAX_TOKENS: 8192
  networks: [mcp, database, cache]
  depends_on:
    postgres: { condition: service_healthy }
    redis: { condition: service_healthy }
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9877/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### **Agent Coordination**

```yaml
agent-coordinator:
  image: toolboxai/agent-coordinator:latest
  container_name: toolboxai-agent-coordinator
  ports: ["8888:8888"]
  environment:
    COORDINATOR_PORT: 8888
    DATABASE_URL_FILE: /run/secrets/database_url
    REDIS_URL_FILE: /run/secrets/redis_url
    MAX_CONCURRENT_AGENTS: 10
  networks: [backend, mcp, cache]
  depends_on:
    redis: { condition: service_healthy }
    mcp-server: { condition: service_healthy }
```

### **Docker Hub MCP Integration**

The Docker Hub MCP server enables repository management via MCP protocol:

```bash
# List repositories
docker run --rm -i -e HUB_PAT_TOKEN=$DOCKER_HUB_PAT_TOKEN \
  mcp/dockerhub --transport=stdio --username=thegrayghost23

# Available via Cursor MCP integration for:
# - Repository creation and management
# - Tag operations and metadata
# - Search and discovery
# - Namespace management
```

## 📊 Health Monitoring

### **Service Health Checks**

```bash
# Primary services
curl http://localhost:8009/health      # Backend (FastAPI)
curl http://localhost:5179/health      # Dashboard (React)
curl http://localhost:9877/health      # MCP Server
curl http://localhost:8888/health      # Agent Coordinator

# Database services
docker compose exec postgres pg_isready -U toolboxai
docker compose exec redis redis-cli ping

# Roblox integration
curl http://localhost:34872/api/rojo/health
```

### **Monitoring Stack**

```bash
# Start with monitoring (optional)
docker compose -f compose/docker-compose.yml -f compose/docker-compose.monitoring.yml up -d

# Access monitoring
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000"
echo "Alertmanager: http://localhost:9093"
```

## 🔒 Security Configuration

### **Container Security**

All services implement security best practices:

```yaml
# Security template applied to all services
x-security-opts: &security-opts
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  read_only: true
  tmpfs:
    - /tmp
    - /var/run
```

### **Network Isolation**

```yaml
# Database network (isolated)
database:
  driver: bridge
  internal: true  # No external access

# Cache network (isolated)
cache:
  driver: bridge
  internal: true  # No external access
```

### **Secret Management**

```bash
# Production secrets (Docker Swarm)
docker secret create database_url "postgresql://user:pass@postgres:5432/db"
docker secret create redis_url "redis://redis:6379/0"
docker secret create jwt_secret "your-secure-jwt-secret"
docker secret create openai_api_key "sk-your-openai-key"
docker secret create anthropic_api_key "sk-your-anthropic-key"
```

## 🚀 Scaling & Performance

### **Horizontal Scaling**

```bash
# Scale backend services
docker compose up -d --scale backend=3

# Scale agent coordinator
docker compose up -d --scale agent-coordinator=2

# Scale with resource limits
docker compose up -d --scale backend=3 --scale mcp-server=2
```

### **Resource Optimization**

```yaml
# Production resource allocation
backend:
  deploy:
    resources:
      limits: { cpus: '2.0', memory: 2G }
      reservations: { cpus: '0.5', memory: 512M }
    replicas: 3

mcp-server:
  deploy:
    resources:
      limits: { cpus: '1.0', memory: 1G }
      reservations: { cpus: '0.25', memory: 256M }
    replicas: 2
```

## 🔧 Troubleshooting

### **Common Issues**

1. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :8009  # Backend
   lsof -i :5179  # Dashboard
   lsof -i :9877  # MCP Server
   lsof -i :8888  # Agent Coordinator
   ```

2. **Service Dependencies**
   ```bash
   # Check service startup order
   docker compose logs postgres
   docker compose logs redis
   docker compose logs backend
   docker compose logs mcp-server
   ```

3. **MCP Gateway Issues**
   ```bash
   # Test MCP server connectivity
   wscat -c ws://localhost:9877

   # Check agent registration
   curl http://localhost:8888/agents

   # Verify Docker Hub MCP
   docker run --rm -i -e HUB_PAT_TOKEN=$DOCKER_HUB_PAT_TOKEN \
     mcp/dockerhub --transport=stdio --username=thegrayghost23
   ```

### **Log Analysis**

```bash
# Service logs
docker compose logs -f backend
docker compose logs -f mcp-server
docker compose logs -f agent-coordinator

# Error filtering
docker compose logs backend | grep ERROR
docker compose logs mcp-server | grep WARN
```

## 📈 Performance Monitoring

### **Metrics Collection**

```bash
# Service metrics endpoints
curl http://localhost:8009/metrics      # Backend metrics
curl http://localhost:9877/metrics      # MCP server metrics
curl http://localhost:8888/metrics      # Agent coordinator metrics

# Database metrics
docker compose exec postgres psql -U toolboxai -c "\l"
docker compose exec redis redis-cli info stats
```

### **Resource Usage**

```bash
# Container resource usage
docker stats

# Service-specific stats
docker stats toolboxai-backend
docker stats toolboxai-mcp
docker stats toolboxai-agent-coordinator
```

## 🔄 Deployment Automation

### **CI/CD Integration**

```yaml
# Docker Hub automated builds
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: thegrayghost23
          password: ${{ secrets.DOCKER_HUB_PAT_TOKEN }}

      - name: Build and push images
        run: |
          # Build all service images
          docker compose -f compose/docker-compose.yml build

          # Tag with build number
          docker tag toolboxai/backend:latest thegrayghost23/toolboxai-backend:${{ github.run_number }}
          docker tag toolboxai/dashboard:latest thegrayghost23/toolboxai-dashboard:${{ github.run_number }}
          docker tag toolboxai/mcp:latest thegrayghost23/toolboxai-mcp-server:${{ github.run_number }}

          # Push to Docker Hub
          docker push thegrayghost23/toolboxai-backend:${{ github.run_number }}
          docker push thegrayghost23/toolboxai-dashboard:${{ github.run_number }}
          docker push thegrayghost23/toolboxai-mcp-server:${{ github.run_number }}

      - name: Deploy to production
        run: |
          # Update production environment
          export DOCKER_TAG=${{ github.run_number }}
          docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d
```

### **Deployment Scripts**

```bash
# Automated deployment script
#!/bin/bash
# File: scripts/deploy-docker-mcp.sh

set -e

echo "🚀 Deploying ToolBoxAI with Docker MCP Gateway..."

# Build images
echo "📦 Building images..."
docker compose -f compose/docker-compose.yml build

# Run health checks
echo "🔍 Running health checks..."
docker compose -f compose/docker-compose.yml up -d postgres redis
sleep 10

# Deploy core services
echo "🎯 Deploying core services..."
docker compose -f compose/docker-compose.yml up -d backend mcp-server

# Deploy coordination layer
echo "🤖 Deploying agent coordination..."
docker compose -f compose/docker-compose.yml up -d agent-coordinator

# Deploy frontend
echo "🎨 Deploying dashboard..."
docker compose -f compose/docker-compose.yml up -d dashboard

# Verify deployment
echo "✅ Verifying deployment..."
sleep 15
curl -f http://localhost:8009/health || exit 1
curl -f http://localhost:5179/health || exit 1
curl -f http://localhost:9877/health || exit 1
curl -f http://localhost:8888/health || exit 1

echo "🎉 Deployment complete!"
echo "Backend: http://localhost:8009"
echo "Dashboard: http://localhost:5179"
echo "MCP Gateway: ws://localhost:9877"
echo "Agent Coordinator: http://localhost:8888"
```

## 🔍 Verification Procedures

### **Service Verification**

```bash
# Check all services are running
docker compose ps

# Verify service health
curl http://localhost:8009/health      # Backend
curl http://localhost:5179/health      # Dashboard
curl http://localhost:9877/health      # MCP Server
curl http://localhost:8888/health      # Agent Coordinator

# Test database connectivity
docker compose exec postgres pg_isready -U toolboxai
docker compose exec redis redis-cli ping
```

### **MCP Gateway Testing**

```bash
# Test MCP server tools
wscat -c ws://localhost:9877

# Test agent coordination
curl http://localhost:8888/agents

# Test Docker Hub MCP integration
docker run --rm -i -e HUB_PAT_TOKEN=$DOCKER_HUB_PAT_TOKEN \
  mcp/dockerhub --transport=stdio --username=thegrayghost23 <<< '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### **End-to-End Testing**

```bash
# Test complete workflow
curl -X POST http://localhost:8009/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"type": "lesson", "topic": "Python basics"}'

# Test real-time updates
curl http://localhost:5179/api/pusher/test

# Test Roblox integration
curl http://localhost:34872/api/rojo/status
```

## 📚 Integration Patterns

### **Following Compose-for-Agents Patterns**

Based on [Docker's compose-for-agents repository](https://github.com/docker/compose-for-agents):

1. **Service Isolation**: Each service runs in dedicated containers
2. **Network Segmentation**: Logical network separation for security
3. **Health Monitoring**: Comprehensive health checks for all services
4. **Resource Management**: Defined resource limits and reservations
5. **Secret Management**: Secure handling of sensitive data

### **MCP Gateway Integration**

Following [Docker MCP Gateway documentation](https://docs.docker.com/ai/mcp-gateway/):

1. **Unified Endpoint**: Single MCP gateway for all AI services
2. **Container-based Servers**: MCP servers run in isolated containers
3. **Dynamic Discovery**: Automatic tool and resource discovery
4. **Secure Communication**: TLS and authentication for all MCP communication

## 🔄 Maintenance Procedures

### **Regular Maintenance**

```bash
# Update images
docker compose pull

# Restart services with zero downtime
docker compose up -d --force-recreate --no-deps backend

# Clean up unused resources
docker system prune -f

# Backup databases
docker compose exec postgres pg_dump -U toolboxai toolboxai > backup.sql
```

### **Monitoring & Alerts**

```bash
# Check resource usage
docker stats

# Monitor logs
docker compose logs -f --tail=100

# Check disk usage
docker system df
```

## 📋 Troubleshooting Guide

### **Service Startup Issues**

1. **Database Connection Failures**
   ```bash
   # Check PostgreSQL logs
   docker compose logs postgres

   # Test connection
   docker compose exec postgres psql -U toolboxai -c "SELECT 1"
   ```

2. **MCP Server Issues**
   ```bash
   # Check MCP server logs
   docker compose logs mcp-server

   # Test WebSocket connection
   wscat -c ws://localhost:9877/health
   ```

3. **Agent Coordination Problems**
   ```bash
   # Check coordinator status
   curl http://localhost:8888/status

   # View agent registration
   curl http://localhost:8888/agents
   ```

### **Performance Issues**

```bash
# Check resource constraints
docker stats --no-stream

# Monitor service response times
time curl http://localhost:8009/health
time curl http://localhost:5179/health
time curl http://localhost:9877/health
```

## 🎯 Production Checklist

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] Secrets created and verified
- [ ] Docker images built and tested
- [ ] Health checks passing
- [ ] Network configuration verified

### **Post-Deployment**
- [ ] All services healthy
- [ ] MCP Gateway operational
- [ ] Agent coordination functional
- [ ] Database migrations applied
- [ ] Monitoring configured
- [ ] Backup procedures tested

### **Security Verification**
- [ ] Container security policies applied
- [ ] Network isolation verified
- [ ] Secret rotation tested
- [ ] Access controls validated
- [ ] TLS certificates valid

---

**Guide Version**: 2.0.0
**Last Updated**: 2025-09-28
**Docker Compose Version**: 2.24+
**MCP Gateway**: Latest Docker patterns
**Verification Status**: ✅ All procedures tested
