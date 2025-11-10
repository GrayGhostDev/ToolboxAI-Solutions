# Current Dockerfiles Documentation

**Last Updated:** November 9, 2025
**Status:** Post-consolidation cleanup

## Canonical Dockerfiles (Use These)

### Backend Services
- **`backend.Dockerfile`** - FastAPI backend application
  - Python 3.12
  - Multi-stage build for optimization
  - Non-root user (UID 1001)
  - Read-only filesystem with tmpfs mounts
  - Referenced in: `docker-compose.yml`

### Frontend
- **`dashboard-2025.Dockerfile`** - React dashboard application
  - Node.js 22 with pnpm 9
  - Vite build system
  - Nginx for production serving
  - Referenced in: `docker-compose.yml`

### Celery Workers
- **`celery-worker.Dockerfile`** - Celery task worker
  - Async task processing
  - Connects to Redis broker
  - Referenced in: `docker-compose.yml`

- **`celery-beat.Dockerfile`** - Celery beat scheduler
  - Periodic task scheduling
  - Triggers scheduled jobs
  - Referenced in: `docker-compose.yml`

### Supporting Services
- **`agents.Dockerfile`** - AI agent services
  - LangChain/LangGraph agents
  - MCP integration

- **`base.Dockerfile`** - Base image for other services
  - Common dependencies
  - Security hardening

- **`celery-flower.Dockerfile`** - Celery monitoring dashboard
  - Web UI on port 5555
  - Real-time task monitoring

- **`mcp.Dockerfile`** - Model Context Protocol server
  - Agent communication
  - Port 9877

- **`nginx-production-2025.Dockerfile`** - Production nginx
  - Reverse proxy
  - SSL termination
  - Static file serving

- **`roblox-sync.Dockerfile`** - Roblox integration service
  - Rojo server
  - Asset synchronization

- **`vault-rotator.Dockerfile`** - Hashicorp Vault secret rotation
  - Automated credential rotation
  - Security best practices

## Deleted Dockerfiles (Consolidated)

The following files were removed during cleanup (November 9, 2025):
- `backend-optimized.Dockerfile` → Use `backend.Dockerfile`
- `backend-production-2025.Dockerfile` → Use `backend.Dockerfile`
- `backend-simple.Dockerfile` → Use `backend.Dockerfile`
- `celery-optimized.Dockerfile` → Use `celery-worker.Dockerfile`
- `celery-production-2025.Dockerfile` → Use `celery-worker.Dockerfile`
- `dashboard.Dockerfile` (old) → Use `dashboard-2025.Dockerfile`
- `dashboard-fixed.Dockerfile` → Use `dashboard-2025.Dockerfile`
- `dashboard-production-2025.Dockerfile` → Use `dashboard-2025.Dockerfile`
- `dev.Dockerfile` → Use docker-compose.dev.yml overrides
- `test-dashboard-simple.Dockerfile` → Use test environment configs

## Usage Examples

### Build Backend
```bash
docker build -f infrastructure/docker/dockerfiles/backend.Dockerfile -t toolboxai-backend:latest .
```

### Build Dashboard
```bash
docker build -f infrastructure/docker/dockerfiles/dashboard-2025.Dockerfile -t toolboxai-dashboard:latest .
```

### Using Docker Compose
```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# With monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up
```

## Security Features

All Dockerfiles implement:
- ✅ Non-root users (UID 1001-1004)
- ✅ Read-only root filesystems
- ✅ Tmpfs for writable directories
- ✅ Dropped capabilities
- ✅ Resource limits
- ✅ Multi-stage builds (where applicable)
- ✅ Minimal base images (Alpine where possible)

## Maintenance

When creating new Dockerfiles:
1. Follow naming convention: `<service>.Dockerfile`
2. Document in this file
3. Reference in appropriate docker-compose file
4. Implement security best practices above
5. Update CLAUDE.md if significant

## Questions?

- See `docker-compose.yml` for service definitions
- See `CLAUDE.md` for Docker development guide
- See `/docs/08-operations/docker/` for operational guides
