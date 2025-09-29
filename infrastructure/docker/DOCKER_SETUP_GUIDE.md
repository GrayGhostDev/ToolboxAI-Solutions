# ToolBoxAI Docker Development Environment

## Overview

This Docker development environment provides a complete, containerized setup for the ToolBoxAI platform with all services properly configured and orchestrated.

## Services Included

### Core Services
- **FastAPI Backend** (Port 8009) - Main API server with AI agents and MCP
- **Dashboard Frontend** (Port 5179) - React-based admin dashboard
- **PostgreSQL** (Port 5434) - Primary database
- **Redis** (Port 6381) - Cache and session store

### AI & Agent Services
- **MCP Server** (Port 9877) - Model Context Protocol server
- **Agent Coordinator** (Port 8888) - AI agent orchestration
- **Educational Agents** - Content generation agents

### Integration Services
- **Flask Bridge** (Port 5001) - Roblox integration API
- **Ghost CMS** (Port 8000) - Content management system

## Prerequisites

1. **Docker Desktop** - Must be installed and running
2. **Environment File** - `.env` file with required variables
3. **Available Ports** - Ports 8009, 5179, 5434, 6381, 8888, 9877, 5001, 8000

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the comprehensive setup script
./infrastructure/docker/start-docker-dev.sh
```

This script will:
- Validate all prerequisites
- Check for port conflicts
- Build all Docker images
- Start services in the correct order
- Verify service health
- Display service URLs

### Option 2: Manual Setup

```bash
# 1. Check setup first
./infrastructure/docker/check-setup.sh

# 2. Start services manually
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# 3. Check service status
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps
```

## Service URLs

Once started, access services at:

- **Dashboard**: http://localhost:5179
- **API Backend**: http://localhost:8009
- **API Docs**: http://localhost:8009/docs
- **MCP Server**: http://localhost:9877
- **Agent Coordinator**: http://localhost:8888
- **Flask Bridge**: http://localhost:5001
- **Ghost CMS**: http://localhost:8000

## Database Connections

- **PostgreSQL**: `localhost:5434`
  - Database: `educational_platform_dev`
  - User: `eduplatform`
  - Password: From `.env` file
- **Redis**: `localhost:6381`

## Environment Variables Required

The following variables must be set in your `.env` file:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Security
JWT_SECRET_KEY=your_jwt_secret

# Pusher (Realtime)
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=us2

# Optional but recommended
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Service Startup Order

Services start in phases to ensure proper dependency resolution:

1. **Phase 1**: PostgreSQL, Redis (databases)
2. **Phase 2**: FastAPI Backend
3. **Phase 3**: MCP Server, Agent Coordinator, Educational Agents
4. **Phase 4**: Flask Bridge, Ghost CMS
5. **Phase 5**: Dashboard Frontend

## Common Commands

```bash
# Start all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Stop all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml down

# View logs (all services)
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f

# View logs (specific service)
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend

# Check service status
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Rebuild services
docker-compose -f infrastructure/docker/docker-compose.dev.yml build

# Restart specific service
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart fastapi-main
```

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Find what's using a port
lsof -i :8009

# Kill process using port
sudo kill -9 $(lsof -t -i:8009)
```

#### Services Not Starting
```bash
# Check logs for errors
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs service-name

# Restart problematic service
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart service-name
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is ready
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec postgres pg_isready -U eduplatform

# Connect to database
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec postgres psql -U eduplatform -d educational_platform_dev
```

#### Frontend Build Issues
```bash
# Rebuild frontend with no cache
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache dashboard-frontend

# Check frontend logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend
```

### Health Checks

Each service has health checks that can be monitored:

```bash
# Check all service health
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Manual health checks
curl http://localhost:8009/health        # Backend
curl http://localhost:5179/              # Dashboard
curl http://localhost:9877/health        # MCP Server
curl http://localhost:8888/health        # Agent Coordinator
```

### Performance Tuning

#### Resource Limits
The docker-compose file includes resource limits. Adjust if needed:

```yaml
deploy:
  resources:
    limits:
      memory: 2G    # Increase for more memory
    reservations:
      memory: 512M
```

#### Database Optimization
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U eduplatform -d educational_platform_dev

# Check database size
SELECT pg_size_pretty(pg_database_size('educational_platform_dev'));

# Optimize performance
VACUUM ANALYZE;
```

## Development Workflow

### Making Changes

1. **Backend Changes**:
   - Edit files in `apps/backend/`
   - Container will auto-reload with volume mounts

2. **Frontend Changes**:
   - Edit files in `apps/dashboard/src/`
   - Vite dev server provides hot-reload

3. **Database Changes**:
   - Update models in `database/models.py`
   - Create Alembic migrations
   - Run migrations in container

### Adding New Services

1. Create Dockerfile in `infrastructure/docker/`
2. Add service to `docker-compose.dev.yml`
3. Update startup scripts if needed
4. Update this README

## Monitoring & Logs

### Centralized Logging
```bash
# View all logs with timestamps
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f -t

# Filter logs by service
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main | grep ERROR
```

### Container Stats
```bash
# View resource usage
docker stats

# Container-specific stats
docker stats toolboxai-fastapi toolboxai-dashboard-frontend
```

## Cleanup

### Remove All Containers and Data
```bash
# Stop and remove everything
docker-compose -f infrastructure/docker/docker-compose.dev.yml down --volumes --remove-orphans

# Remove unused images
docker image prune -f

# Remove unused volumes (careful!)
docker volume prune -f
```

### Reset Development Environment
```bash
# Full reset (removes all data!)
docker-compose -f infrastructure/docker/docker-compose.dev.yml down --volumes --remove-orphans
docker system prune -f
./infrastructure/docker/start-docker-dev.sh
```

## Security Considerations

- All containers run as non-root users
- Secrets are passed via environment variables
- Database passwords are required (no defaults in production)
- JWT secrets must be secure
- API keys should be rotated regularly

## Support

For issues:
1. Check this guide first
2. Run `./infrastructure/docker/check-setup.sh`
3. Check service logs
4. Ensure all environment variables are set
5. Verify Docker Desktop is running

---

**Note**: This is a development environment. For production deployment, use the production Docker Compose files and ensure proper security configurations.
