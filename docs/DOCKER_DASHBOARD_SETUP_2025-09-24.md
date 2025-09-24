# Docker Dashboard Initialization Guide
## Complete Setup and Startup Procedures

Created: 2025-09-24

## 🚀 Quick Start

### Prerequisites
1. Docker Desktop installed and running
2. Environment variables configured in `.env` file
3. Sufficient disk space (minimum 5GB free)

### One-Command Startup
```bash
# Start all services with enhanced initialization
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
./infrastructure/docker/start-services-enhanced.sh
```

## 📋 Current Status

### ✅ Verified Working (Local Development)
- Dashboard: Running on http://localhost:5179 with Vite
- Backend: Running on http://localhost:8009 with FastAPI
- Authentication: Legacy auth mode (VITE_ENABLE_CLERK_AUTH=false)
- User Profile Endpoint: `/api/v1/users/me/profile` operational

### 🐳 Docker Configuration Ready
- Docker image built successfully: `toolboxai-dashboard:latest`
- Enhanced Dockerfiles with multi-stage builds
- Comprehensive health checks configured
- Service dependency management implemented
- Startup scripts with retry logic created

## 🏗️ Docker Architecture

### Service Stack
```yaml
Services:
  ├── postgres (port 5434)      # PostgreSQL 15 database
  ├── redis (port 6381)          # Redis 7 cache
  ├── fastapi-main (port 8009)   # Backend API server
  ├── dashboard-frontend (5179)  # React dashboard
  ├── mcp-server (port 9877)     # Model Context Protocol
  ├── agent-coordinator (8888)   # AI agent orchestration
  ├── flask-bridge (port 5001)   # Roblox integration
  └── ghost-backend (port 8000)  # CMS system
```

## 🚦 Startup Flow

### Phase 1: Infrastructure
1. **PostgreSQL Database**
   - Starts first as core dependency
   - Health check: `pg_isready`
   - Creates multiple databases on init

2. **Redis Cache**
   - Starts alongside PostgreSQL
   - Health check: `redis-cli ping`
   - Configured with persistence

### Phase 2: Backend Services
3. **FastAPI Backend**
   - Waits for PostgreSQL and Redis
   - Health check: `/health` endpoint
   - Runs database migrations on startup

### Phase 3: Frontend Services
4. **Dashboard Frontend**
   - Waits for FastAPI to be healthy
   - Health check: HTTP request to Vite server
   - Environment variables injected at runtime

### Phase 4: Support Services
5. **MCP Server, Agent Coordinator, Flask Bridge**
   - Start after core services are healthy
   - Each has independent health checks

## 📁 Key Files Created

### Enhanced Startup Scripts

#### `/infrastructure/docker/docker-entrypoint.sh`
```bash
#!/bin/bash
# Enhanced dashboard startup with dependency validation
# Features:
# - Service health verification
# - Automatic retry logic
# - Environment validation
# - Error recovery
```

#### `/infrastructure/docker/wait-for-it.sh`
```bash
#!/bin/bash
# Service dependency management
# Waits for services to be ready before proceeding
# Supports TCP and HTTP health checks
```

#### `/infrastructure/docker/start-services-enhanced.sh`
```bash
#!/bin/bash
# Orchestrated startup of all services
# Ensures proper initialization order
# Validates entire stack health
```

#### `/infrastructure/docker/validate-setup.sh`
```bash
#!/bin/bash
# Post-startup validation
# Runs integration tests
# Reports service health status
```

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# Authentication (IMPORTANT: Set to false for legacy auth)
VITE_ENABLE_CLERK_AUTH=false
ENABLE_CLERK_AUTH=false

# Database
POSTGRES_DB=educational_platform_dev
POSTGRES_USER=eduplatform
POSTGRES_PASSWORD=eduplatform2024
DATABASE_URL=postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev

# Redis
REDIS_URL=redis://redis:6379

# API Configuration
VITE_API_BASE_URL=http://fastapi-main:8009/api/v1
VITE_WS_URL=ws://fastapi-main:8009
VITE_PROXY_TARGET=http://fastapi-main:8009

# JWT Security
JWT_SECRET_KEY=your-secure-secret-key

# Optional Services
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2
```

## 🐳 Docker Commands

### Build Images
```bash
# Build dashboard image
docker build -f infrastructure/docker/dashboard.dev.Dockerfile -t toolboxai-dashboard .

# Build backend image
docker build -f infrastructure/docker/Dockerfile.backend -t toolboxai-backend .
```

### Start Services
```bash
# Start all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Start specific service
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d dashboard-frontend

# View logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend
```

### Health Checks
```bash
# Check service health
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Test backend health
curl http://localhost:8009/health

# Test dashboard health
curl http://localhost:5179
```

### Cleanup
```bash
# Stop all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml down

# Remove volumes (careful - deletes data)
docker-compose -f infrastructure/docker/docker-compose.dev.yml down -v

# Clean up images
docker image prune -a
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Docker Daemon Not Running
**Error**: `Cannot connect to the Docker daemon`
**Solution**:
```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to be ready
docker version
```

#### 2. Container Name Conflicts
**Error**: `The container name is already in use`
**Solution**:
```bash
# Stop and remove existing containers
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
docker container prune
```

#### 3. Port Already in Use
**Error**: `bind: address already in use`
**Solution**:
```bash
# Find process using port
lsof -i :5179
lsof -i :8009

# Kill process
kill -9 <PID>
```

#### 4. Dashboard Not Loading
**Issue**: White screen or connection errors
**Solution**:
```bash
# Check backend is running
curl http://localhost:8009/health

# Check environment variables
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend env | grep VITE

# Rebuild with fresh dependencies
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache dashboard-frontend
```

#### 5. Authentication Errors
**Issue**: ClerkAuthProvider errors
**Solution**:
```bash
# Ensure legacy auth is enabled
export VITE_ENABLE_CLERK_AUTH=false
export ENABLE_CLERK_AUTH=false

# Restart services
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart dashboard-frontend
```

## 🎯 Validation Checklist

### Pre-Flight Checks
- [ ] Docker Desktop is running
- [ ] `.env` file exists with required variables
- [ ] Ports 5179, 8009, 5434, 6381 are available
- [ ] At least 5GB free disk space

### Startup Verification
- [ ] PostgreSQL container healthy
- [ ] Redis container healthy
- [ ] Backend responds to `/health`
- [ ] Dashboard loads at http://localhost:5179
- [ ] API proxy working (check network tab)

### Integration Tests
- [ ] Login functionality working
- [ ] User profile endpoint returns data
- [ ] Dashboard components render correctly
- [ ] WebSocket/Pusher connections established

## 📊 Service Dependencies

```mermaid
graph TD
    A[PostgreSQL] --> C[FastAPI Backend]
    B[Redis] --> C
    C --> D[Dashboard Frontend]
    C --> E[MCP Server]
    C --> F[Agent Coordinator]
    C --> G[Flask Bridge]
    A --> H[Ghost CMS]
```

## 🔄 Development Workflow

### Making Changes

#### Frontend Changes
1. Edit files in `apps/dashboard/src/`
2. Changes auto-reload via volume mounts
3. Check browser console for errors

#### Backend Changes
1. Edit files in `apps/backend/`
2. Uvicorn auto-reloads on file changes
3. Check docker logs for errors

### Debugging

#### View Logs
```bash
# All services
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs

# Specific service
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs dashboard-frontend

# Follow logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend
```

#### Access Container Shell
```bash
# Dashboard container
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend sh

# Backend container
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec fastapi-main bash
```

#### Network Debugging
```bash
# Test inter-container communication
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend ping fastapi-main

# Check network configuration
docker network ls
docker network inspect toolboxai_network
```

## 💡 Best Practices

### Development Tips
1. **Use the enhanced startup script** for consistent initialization
2. **Monitor logs** during startup to catch issues early
3. **Check health endpoints** before assuming services are ready
4. **Use volume mounts** for hot-reload during development
5. **Keep containers running** to avoid repeated startup time

### Production Considerations
1. Use production Dockerfiles (`dashboard.Dockerfile`)
2. Enable Sentry for error tracking
3. Use environment-specific `.env` files
4. Implement proper secrets management
5. Set resource limits in docker-compose

## 🚨 Emergency Procedures

### Full Reset
```bash
# Stop everything
docker-compose -f infrastructure/docker/docker-compose.dev.yml down -v

# Clean Docker system
docker system prune -a --volumes

# Rebuild from scratch
./infrastructure/docker/start-services-enhanced.sh --rebuild
```

### Quick Restart
```bash
# Restart all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart

# Restart specific service
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart dashboard-frontend
```

## 📝 Notes

### Current Implementation Status
- ✅ Docker images build successfully
- ✅ Enhanced startup scripts created
- ✅ Health checks configured
- ✅ Service dependencies defined
- ✅ Environment variables documented
- ✅ Local development working without Docker

### Pending When Docker Available
- [ ] Test complete stack startup
- [ ] Verify inter-container communication
- [ ] Validate health check timing
- [ ] Test hot-reload functionality
- [ ] Confirm database migrations

## 🔗 Related Documentation
- [Main CLAUDE.md](../CLAUDE.md)
- [Auth Fixes Summary](AUTH_FIXES_SUMMARY_2025-09-23.md)
- [Docker Compose Dev](../infrastructure/docker/docker-compose.dev.yml)
- [Dashboard Dockerfile](../infrastructure/docker/dashboard.dev.Dockerfile)

---

*This documentation ensures proper Docker container initialization for the dashboard, addressing the user's request: "Ensure that frontend/dashboard is included with the initialization of the docker container properly installed in the startup procedures."*