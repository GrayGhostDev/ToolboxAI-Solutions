# Docker MCP Gateway Integration - ToolBoxAI 2025

## Executive Summary

The ToolBoxAI platform has been successfully integrated with Docker's MCP (Model Context Protocol) Gateway, following the latest 2025 best practices from Docker's compose-for-agents repository and official MCP Gateway documentation. This document provides a comprehensive overview of the actual implementation, correcting previous documentation discrepancies and incorporating real-world deployment patterns.

## ✅ Current Implementation Status

### **Verified Services (Actual Configuration)**

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **Backend** | `8009` | ✅ Running | FastAPI + Embedded AI Agents |
| **Dashboard** | `5180` | ✅ Running | React + Mantine v8 + Pusher |
| **MCP Server** | `9877` | ✅ Running | Model Context Protocol Gateway |
| **Agent Coordinator** | `8888` | ✅ Running | AI Agent Orchestration |
| **PostgreSQL** | `5432` | ✅ Running | Primary Database |
| **Redis** | `6379` | ✅ Running | Cache + Session Store |
| **Roblox Sync** | `34872` | ✅ Running | Roblox Studio Integration |

### **Development Tools (Dev Environment Only)**
| Tool | Port | Purpose |
|------|------|---------|
| **Adminer** | `8080` | Database Management UI |
| **Redis Commander** | `8081` | Redis Management UI |
| **Mailhog** | `8025` | Email Testing |

## 🏗️ Actual Architecture (Corrected)

```
┌─────────────────────────────────────────────────────────────┐
│                   Nginx Load Balancer                       │
│                     (Port 80/443)                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────▼──────────┐         ┌─────────▼─────────┐
│     Dashboard          │         │     Backend       │
│  React + Mantine v8    │         │   FastAPI + AI    │
│     Port: 5180         │         │   Port: 8009      │
└────────────────────────┘         └───────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────▼──────────┐         ┌─────────▼─────────┐
│    MCP Server          │         │ Agent Coordinator │
│   Port: 9877           │◄────────┤   Port: 8888      │
│   (WebSocket Gateway)  │         │  (Orchestrator)   │
└────────────────────────┘         └───────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────▼──────────┐         ┌─────────▼─────────┐
│     PostgreSQL         │         │      Redis        │
│   Port: 5432           │         │   Port: 6379      │
│  (Primary Database)    │         │ (Cache + Queue)   │
└────────────────────────┘         └───────────────────┘
              │
┌─────────────▼──────────┐
│    Roblox Sync         │
│   Port: 34872          │
│ (Studio Integration)   │
└────────────────────────┘
```

## 🐳 Docker Configuration (Actual Implementation)

### **Base Docker Compose** (`infrastructure/docker/compose/docker-compose.yml`)

**Key Services:**
- **Backend**: `toolboxai/backend:latest` - FastAPI with embedded agents
- **Dashboard**: `toolboxai/dashboard:latest` - React with Nginx
- **MCP Server**: `toolboxai/mcp:latest` - WebSocket MCP Gateway
- **Agent Coordinator**: `toolboxai/agent-coordinator:latest` - Task orchestration
- **PostgreSQL**: Standard PostgreSQL with custom init scripts
- **Redis**: Standard Redis with persistence
- **Roblox Sync**: `toolboxai/roblox-sync:latest` - Rojo-based sync service

### **Development Overrides** (`docker-compose.dev.yml`)

```yaml
# Development-specific configurations
backend:
  ports: ["8009:8009", "5678:5678"]  # Main + Debug ports
  environment:
    DEBUG: "true"
    RELOAD: "true"
    WORKERS: 1

dashboard:
  ports: ["5180:80"]  # Corrected port
  command: npm run dev

mcp-server:
  ports: ["9877:9877", "9878:9878"]  # Main + Debug ports
  environment:
    LOG_LEVEL: DEBUG
```

## 📋 MCP Server Configuration (Actual)

### **Current MCP Servers** (`config/mcp/mcp-servers.json`)

```json
{
  "mcpServers": {
    "educational-content": {
      "command": "python",
      "args": ["-m", "core.mcp.servers.educational_content"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "REDIS_URL": "${REDIS_URL}"
      }
    },
    "analytics": {
      "command": "python",
      "args": ["-m", "core.mcp.servers.analytics"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "REDIS_URL": "${REDIS_URL}"
      }
    },
    "roblox-integration": {
      "command": "python",
      "args": ["-m", "core.mcp.servers.roblox"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "REDIS_URL": "${REDIS_URL}",
        "ROBLOX_API_KEY": "${ROBLOX_API_KEY}"
      }
    },
    "agent-coordinator": {
      "command": "python",
      "args": ["-m", "core.mcp.servers.agent_coordinator"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "REDIS_URL": "${REDIS_URL}",
        "COORDINATOR_PORT": "8888"
      }
    }
  }
}
```

### **Docker Hub MCP Integration** (New)

Following Docker's MCP Gateway patterns, we've integrated the Docker Hub MCP server:

```json
{
  "mcpServers": {
    "dockerhub": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "HUB_PAT_TOKEN",
        "mcp/dockerhub",
        "--transport=stdio",
        "--username=thegrayghost23"
      ],
      "env": {
        "HUB_PAT_TOKEN": "${DOCKER_HUB_PAT_TOKEN}"
      }
    }
  }
}
```

**Docker Hub Credentials:**
- **Username**: `thegrayghost23`
- **PAT Token**: Configured via environment variable
- **Repositories**: `toolboxai-dashboard`, `toolboxai-backend`, `toolboxai-mcp-server`, etc.

## 🚀 Quick Start Guide (Corrected)

### **Development Environment**

```bash
# Navigate to Docker directory
cd infrastructure/docker

# Start development stack with corrected ports
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up -d

# Verify services are running on correct ports
curl http://localhost:8009/health    # Backend
curl http://localhost:5180/health    # Dashboard
curl http://localhost:9877/health    # MCP Server
curl http://localhost:8888/health    # Agent Coordinator
```

### **Service Access URLs**

#### **Primary Services**
- **Backend API**: http://localhost:8009
- **Dashboard**: http://localhost:5180
- **MCP Server**: ws://localhost:9877
- **Agent Coordinator**: http://localhost:8888

#### **Development Tools**
- **Database UI**: http://localhost:8080 (Adminer)
- **Redis UI**: http://localhost:8081 (Redis Commander)
- **Email Testing**: http://localhost:8025 (Mailhog)
- **Roblox Studio**: Connect to localhost:34872

## 🔧 Environment Configuration

### **Required Environment Variables**

```env
# Database Configuration
POSTGRES_DB=toolboxai
POSTGRES_USER=toolboxai
POSTGRES_PASSWORD=devpass2024
DATABASE_URL=postgresql://toolboxai:devpass2024@postgres:5432/toolboxai

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Server Configuration
HOST=0.0.0.0
PORT=8009
WORKERS=4

# MCP Configuration
MCP_HOST=0.0.0.0
MCP_PORT=9877
AGENT_DISCOVERY_ENABLED=true

# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-your-anthropic-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key

# Docker Hub MCP
DOCKER_HUB_PAT_TOKEN=dckr_pat_your_token

# Pusher Configuration (Dashboard)
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/api/pusher/auth
```

## 🔄 Service Integration Patterns

### **MCP Gateway Pattern**

Following Docker's compose-for-agents patterns:

```yaml
# MCP Gateway Service
mcp-server:
  image: toolboxai/mcp:latest
  ports: ["9877:9877"]  # Corrected port
  environment:
    MCP_HOST: 0.0.0.0
    MCP_PORT: 9877
    AGENT_DISCOVERY_ENABLED: true
  networks: [mcp, database, cache]
  depends_on:
    postgres: { condition: service_healthy }
    redis: { condition: service_healthy }
```

### **Agent Coordination Pattern**

```yaml
# Agent Coordinator Service
agent-coordinator:
  image: toolboxai/agent-coordinator:latest
  ports: ["8888:8888"]
  environment:
    COORDINATOR_PORT: 8888
    REDIS_URL: redis://redis:6379/1
  networks: [backend, mcp, cache]
  depends_on: [redis, mcp-server]
```

## 🔍 Health Monitoring

### **Health Check Commands**

```bash
# Check all services
docker compose -f compose/docker-compose.yml ps

# Individual service health checks
curl http://localhost:8009/health    # Backend (FastAPI)
curl http://localhost:5180/health    # Dashboard (Nginx)
curl http://localhost:9877/health    # MCP Server
curl http://localhost:8888/health    # Agent Coordinator

# Database connectivity
docker compose exec postgres pg_isready -U toolboxai
docker compose exec redis redis-cli ping
```

### **Service Dependencies**

```mermaid
graph TD
    A[PostgreSQL] --> B[Backend]
    A --> C[MCP Server]
    D[Redis] --> B
    D --> C
    D --> E[Agent Coordinator]
    B --> F[Dashboard]
    C --> E
    E --> G[Educational Agents]
    E --> H[Analytics Agents]
    E --> I[Roblox Agents]
```

## 🛡️ Security Configuration

### **Network Security**

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
  database:
    driver: bridge
    internal: true  # Database isolation
  cache:
    driver: bridge
    internal: true  # Cache isolation
  mcp:
    driver: bridge
    internal: false # MCP communication
```

### **Container Security**

All services follow security best practices:
- Non-root users
- Read-only filesystems
- Dropped capabilities
- Resource limits
- Health checks

## 🚀 Deployment Procedures

### **Production Deployment**

```bash
# Build production images
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml build

# Deploy with scaling
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d --scale backend=3

# Verify deployment
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml ps
```

### **Docker Hub Integration**

```bash
# Login to Docker Hub (using configured MCP)
docker login -u thegrayghost23

# Tag and push images
docker tag toolboxai/backend:latest thegrayghost23/toolboxai-backend:2025.09.27
docker push thegrayghost23/toolboxai-backend:2025.09.27

# Use Docker Hub MCP for repository management
# (Available through Cursor MCP integration)
```

## 🔧 Troubleshooting

### **Common Issues and Solutions**

1. **Port Conflicts**
   ```bash
   # Check for port usage
   lsof -i :8009  # Backend
   lsof -i :5180  # Dashboard
   lsof -i :9877  # MCP Server
   lsof -i :8888  # Agent Coordinator
   ```

2. **Service Connection Issues**
   ```bash
   # Check Docker networks
   docker network ls
   docker network inspect toolboxai_backend

   # Test inter-service connectivity
   docker compose exec backend ping postgres
   docker compose exec mcp-server ping redis
   ```

3. **MCP Server Issues**
   ```bash
   # Check MCP server logs
   docker compose logs mcp-server

   # Test WebSocket connection
   wscat -c ws://localhost:9877/health
   ```

### **Log Analysis**

```bash
# View service logs
docker compose logs -f backend
docker compose logs -f mcp-server
docker compose logs -f agent-coordinator

# Filter logs by service
docker compose logs --tail=100 backend | grep ERROR
```

## 📈 Performance Optimization

### **Resource Allocation (Actual)**

```yaml
# Backend Service
backend:
  deploy:
    resources:
      limits: { cpus: '2.0', memory: 2G }
      reservations: { cpus: '0.5', memory: 512M }

# MCP Server
mcp-server:
  deploy:
    resources:
      limits: { cpus: '1.0', memory: 1G }
      reservations: { cpus: '0.25', memory: 256M }

# Agent Coordinator
agent-coordinator:
  deploy:
    resources:
      limits: { cpus: '1.0', memory: 1G }
      reservations: { cpus: '0.25', memory: 256M }
```

### **Scaling Strategies**

```bash
# Scale backend services
docker compose up -d --scale backend=3

# Scale agent coordinator
docker compose up -d --scale agent-coordinator=2

# Monitor resource usage
docker stats
```

## 🔮 Future Enhancements

### **Planned Improvements**

1. **Enhanced MCP Gateway Integration**
   - Implement Docker's latest MCP Gateway features
   - Add support for multiple MCP server instances
   - Integrate with Cursor MCP ecosystem

2. **Agent Pool Expansion**
   - Dedicated agent containers (currently embedded)
   - Auto-scaling based on workload
   - Specialized agent types

3. **Monitoring Integration**
   - Prometheus metrics collection
   - Grafana dashboards
   - Distributed tracing with Jaeger

4. **Security Enhancements**
   - mTLS between services
   - Enhanced secret management
   - Network policy enforcement

## 📚 References

### **Configuration Files**
- [Base Docker Compose](../../infrastructure/docker/compose/docker-compose.yml)
- [Development Overrides](../../infrastructure/docker/compose/docker-compose.dev.yml)
- [Production Overrides](../../infrastructure/docker/compose/docker-compose.prod.yml)
- [MCP Server Configuration](../../config/mcp/mcp-servers.json)
- [Quick Start Guide](../../infrastructure/docker/QUICK_START.md)

### **Docker Hub Integration**
- [Docker Hub MCP Server Documentation](https://hub.docker.com/mcp/server/dockerhub/overview)
- [Docker MCP Gateway Guide](https://docs.docker.com/ai/mcp-gateway/)
- [Compose for Agents Repository](https://github.com/docker/compose-for-agents)

### **Implementation Reports**
- [Docker Status Report](../11-reports/DOCKER_STATUS_REPORT.md)
- [Migration Documentation](../06-features/migrations/complete-migration-documentation-2025.md)
- [Implementation Status](../08-operations/deployment/IMPLEMENTATION_STATUS_2025.md)

---

**Document Version**: 2.0.0
**Last Updated**: 2025-09-28
**Status**: Current Implementation Documented
**Verified Ports**: ✅ All ports confirmed accurate
**Docker Hub Integration**: ✅ Configured and tested
