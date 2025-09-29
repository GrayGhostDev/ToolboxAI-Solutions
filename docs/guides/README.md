# ToolBoxAI Deployment Guides

## Overview

This directory contains comprehensive deployment guides for the ToolBoxAI platform, covering Docker containerization, MCP Gateway integration, and production deployment strategies.

## 📚 Available Guides

### **🐳 Docker Deployment**

#### **⭐ Current (2025)**
- **[Docker MCP Deployment Guide 2025](DOCKER_MCP_DEPLOYMENT_GUIDE_2025.md)** - **RECOMMENDED**
  - Latest Docker MCP Gateway integration
  - Corrected port numbers and service configurations
  - Following compose-for-agents patterns
  - Docker Hub MCP integration included

#### **Legacy Documentation**
- **[Docker Deployment Guide](DOCKER_DEPLOYMENT_GUIDE.md)** - Original deployment guide
  - ⚠️ **Note**: Contains outdated port references
  - Use for historical reference only

### **🔧 Service Configuration**

| Service | Port | Guide Reference | Status |
|---------|------|----------------|--------|
| **Backend** | `8009` | Docker MCP Guide 2025 | ✅ Current |
| **Dashboard** | `5180` | Docker MCP Guide 2025 | ✅ Current |
| **MCP Server** | `9877` | Docker MCP Guide 2025 | ✅ Current |
| **Agent Coordinator** | `8888` | Docker MCP Guide 2025 | ✅ Current |
| **PostgreSQL** | `5432` | Docker MCP Guide 2025 | ✅ Current |
| **Redis** | `6379` | Docker MCP Guide 2025 | ✅ Current |
| **Roblox Sync** | `34872` | Docker MCP Guide 2025 | ✅ Current |

## 🚀 Quick Start

### **Development Deployment**

```bash
# Navigate to Docker directory
cd infrastructure/docker

# Start development environment
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up -d

# Verify all services
curl http://localhost:8009/health    # Backend
curl http://localhost:5180/health    # Dashboard
curl http://localhost:9877/health    # MCP Server
curl http://localhost:8888/health    # Agent Coordinator
```

### **Production Deployment**

```bash
# Create production secrets
echo "your-secure-password" | docker secret create postgres_password -
echo "your-jwt-secret" | docker secret create jwt_secret -

# Deploy production stack
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d

# Scale services
docker compose up -d --scale backend=3 --scale mcp-server=2
```

## 📊 Service Architecture

### **Current Implementation**

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

## 🔧 Configuration Management

### **Environment Variables**

**Required for all deployments:**
```env
# Core Services
DATABASE_URL=postgresql://toolboxai:password@postgres:5432/toolboxai
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secure-jwt-secret

# MCP Configuration
MCP_HOST=0.0.0.0
MCP_PORT=9877
AGENT_DISCOVERY_ENABLED=true

# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-your-anthropic-key

# Docker Hub MCP
DOCKER_HUB_PAT_TOKEN=dckr_pat_your_token
```

### **Feature Flags**

```env
# Enable/disable platform features
VITE_ENABLE_MCP=true
VITE_ENABLE_AGENTS=true
VITE_ENABLE_PUSHER=true
VITE_ENABLE_ROBLOX=true
VITE_ENABLE_ANALYTICS=true
```

## 🔒 Security Considerations

### **Container Security**

All services implement:
- Non-root user execution
- Read-only filesystems
- Dropped capabilities
- Security options enabled
- Resource limits enforced

### **Network Security**

```yaml
# Network isolation
networks:
  frontend:     # Public-facing
  backend:      # Application layer
  database:     # Database isolation (internal: true)
  cache:        # Cache isolation (internal: true)
  mcp:          # MCP communication
  roblox:       # Roblox integration
```

## 📈 Monitoring & Observability

### **Health Monitoring**

```bash
# Service health endpoints
curl http://localhost:8009/health      # Backend
curl http://localhost:5180/health      # Dashboard
curl http://localhost:9877/health      # MCP Server
curl http://localhost:8888/health      # Agent Coordinator
```

### **Metrics Collection**

```bash
# Prometheus metrics
curl http://localhost:8009/metrics     # Backend metrics
curl http://localhost:9877/metrics     # MCP metrics
curl http://localhost:8888/metrics     # Agent metrics
```

### **Log Management**

```bash
# Centralized logging
docker compose logs -f                 # All services
docker compose logs -f backend         # Backend only
docker compose logs -f mcp-server      # MCP only
```

## 🔄 Maintenance

### **Regular Tasks**

```bash
# Update images
docker compose pull

# Restart with zero downtime
docker compose up -d --force-recreate --no-deps service-name

# Clean unused resources
docker system prune -f

# Backup databases
docker compose exec postgres pg_dump -U toolboxai toolboxai > backup.sql
```

### **Scaling Operations**

```bash
# Scale backend
docker compose up -d --scale backend=3

# Scale MCP server
docker compose up -d --scale mcp-server=2

# Monitor scaling
docker stats
```

## 🆘 Troubleshooting

### **Common Issues**

1. **Port Conflicts**: Use `lsof -i :PORT` to check usage
2. **Service Dependencies**: Check startup order and health
3. **Memory Issues**: Monitor with `docker stats`
4. **Network Issues**: Verify Docker network configuration

### **Emergency Procedures**

```bash
# Emergency restart
docker compose restart

# Complete reset
docker compose down -v
docker compose up -d

# Service isolation
docker compose stop problematic-service
docker compose logs problematic-service
docker compose start problematic-service
```

## 📚 References

### **Implementation Documentation**
- [Docker MCP Gateway Integration 2025](../05-implementation/docker-mcp-gateway-integration-2025.md)
- [Docker Hub MCP Integration](../05-implementation/docker-hub-mcp-integration.md)
- [Implementation Overview](../05-implementation/README.md)

### **Configuration Files**
- [Docker Compose Base](../../infrastructure/docker/compose/docker-compose.yml)
- [Development Overrides](../../infrastructure/docker/compose/docker-compose.dev.yml)
- [Production Overrides](../../infrastructure/docker/compose/docker-compose.prod.yml)
- [MCP Configuration](../../config/mcp/mcp-servers.json)

### **External References**
- [Docker Compose for Agents](https://github.com/docker/compose-for-agents)
- [Docker MCP Gateway](https://docs.docker.com/ai/mcp-gateway/)
- [Docker Hub MCP Server](https://hub.docker.com/mcp/server/dockerhub/overview)

---

**Last Updated**: 2025-09-28
**Guide Version**: 2.0.0
**Verification Status**: ✅ All procedures tested
**Port Numbers**: ✅ Verified accurate
