# ToolboxAI Docker Setup Guide
## Complete Step-by-Step Instructions

**Last Updated**: October 1, 2025
**Status**: Production Ready
**Docker Version**: 25.x
**Compose Version**: v2

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (30 seconds)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Service Overview](#service-overview)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| **Docker Desktop** | 25.x+ | [Download](https://www.docker.com/products/docker-desktop) |
| **Docker Compose** | v2+ | Included with Docker Desktop |
| **Git** | 2.x+ | [Download](https://git-scm.com/downloads) |

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 10GB free space minimum
- **OS**: macOS 12+, Windows 10+, or Linux (Ubuntu 20.04+)
- **CPU**: Multi-core processor recommended

### Required Ports

Ensure these ports are available:

| Port | Service | Description |
|------|---------|-------------|
| 5180 | Dashboard | React frontend |
| 8009 | Backend API | FastAPI server |
| 5434 | PostgreSQL | Database |
| 6381 | Redis | Cache/Queue |
| 8080 | Adminer | DB Admin (dev only) |
| 8081 | Redis Commander | Redis Admin (dev only) |
| 5555 | Flower | Celery monitor (dev only) |

---

## Quick Start

### Option 1: One-Command Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/ToolBoxAI-Solutions/toolboxai.git
cd toolboxai

# Run complete setup
./infrastructure/docker/scripts/complete-setup-2025.sh

# Access the platform
open http://localhost:5180
```

That's it! The script handles everything automatically.

### Option 2: Manual Setup

```bash
# 1. Copy environment template
cp .env.docker.example .env

# 2. Create Docker secrets
./infrastructure/docker/scripts/create-secrets.sh development

# 3. Start services
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 4. Wait for services to be ready (2-3 minutes)
docker compose logs -f backend dashboard
```

---

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/ToolBoxAI-Solutions/toolboxai.git
cd toolboxai
```

### Step 2: Environment Configuration

#### Development Setup

```bash
# Copy template
cp .env.docker.example .env

# The template includes secure defaults for development
# Edit .env to customize (optional):
nano .env
```

#### Production Setup

```bash
# Copy template
cp .env.docker.example .env.production

# CRITICAL: Replace ALL placeholder values
# Generate secure values:
openssl rand -hex 32      # For JWT_SECRET_KEY
openssl rand -base64 32   # For passwords

# Edit with actual values
nano .env.production
```

**Required Variables** (must be set for production):

```bash
# Database
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_PASSWORD=<strong-password>

# Security
JWT_SECRET_KEY=<64-char-hex-string>

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Pusher (Required for real-time features)
VITE_PUSHER_KEY=your-actual-key
VITE_PUSHER_CLUSTER=us2

# Clerk Auth (Optional)
VITE_CLERK_PUBLISHABLE_KEY=pk_...
```

### Step 3: Create Docker Secrets

Docker secrets provide secure credential management:

```bash
# Development mode (uses defaults from .env)
./infrastructure/docker/scripts/create-secrets.sh development

# Production mode (uses .env.production)
ENV_FILE=.env.production ./infrastructure/docker/scripts/create-secrets.sh production

# Verify secrets created
docker secret ls
```

**What This Creates:**
- ✅ 13 Docker secrets for all services
- ✅ Secure, encrypted credential storage
- ✅ No secrets in environment variables
- ✅ Automatic generation of missing values (dev mode)

### Step 4: Verify Configuration Files

The setup script copies these automatically, but you can verify:

```bash
# Check required files exist
ls infrastructure/docker/compose/config/postgres-init.sql
ls infrastructure/docker/compose/config/redis.conf
ls infrastructure/docker/compose/config/rojo/default.project.json

# If missing, the complete-setup script will copy them
```

### Step 5: Start Services

#### Development Mode

```bash
cd infrastructure/docker/compose

# Start with hot-reload and debug features
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Follow logs
docker compose logs -f backend dashboard
```

#### Production Mode

```bash
cd infrastructure/docker/compose

# Start with security hardening
docker compose -f docker-compose.yml up -d

# Monitor startup
docker compose ps
```

### Step 6: Wait for Services

Services take 2-3 minutes to fully initialize:

```bash
# Watch all services become healthy
watch -n 2 'docker compose ps'

# Or check individual service logs
docker compose logs -f postgres   # Database startup
docker compose logs -f redis      # Redis startup
docker compose logs -f backend    # API server
docker compose logs -f dashboard  # Frontend
```

### Step 7: Verify Deployment

```bash
# Check all services are healthy
docker compose ps

# Test backend API
curl http://localhost:8009/health

# Test dashboard
curl http://localhost:5180/

# View service logs
docker compose logs --tail=100
```

---

## Configuration

### Environment Variables Reference

#### Database Configuration

```bash
POSTGRES_DB=toolboxai           # Database name
POSTGRES_USER=toolboxai         # Database user
POSTGRES_PASSWORD=<secure>      # Database password (use secrets in prod)
```

#### Redis Configuration

```bash
REDIS_PASSWORD=<secure>         # Redis password (use secrets in prod)
```

#### Backend Configuration

```bash
HOST=0.0.0.0                    # Bind address
PORT=8009                       # API port
WORKERS=4                       # Gunicorn workers (prod)
DEBUG=false                     # Debug mode (dev: true)
RELOAD=false                    # Auto-reload (dev: true)
LOG_LEVEL=INFO                  # Logging level
```

#### Frontend Configuration

```bash
VITE_API_BASE_URL=http://localhost:8009    # API endpoint
VITE_PUSHER_KEY=<your-key>                 # Pusher app key
VITE_PUSHER_CLUSTER=us2                    # Pusher cluster
VITE_ENABLE_WEBSOCKET=false                # WebSocket (deprecated)
VITE_ENABLE_PUSHER=true                    # Pusher real-time
```

#### Feature Flags

```bash
VITE_ENABLE_GAMIFICATION=true   # Enable gamification
VITE_ENABLE_ANALYTICS=true      # Enable analytics
VITE_ENABLE_MCP=true            # Enable MCP server
VITE_ENABLE_AGENTS=true         # Enable AI agents
VITE_ENABLE_ROBLOX=true         # Enable Roblox integration
```

### Docker Compose Configuration

#### Development Overrides

The `docker-compose.dev.yml` file provides development-friendly settings:

- ✅ Volume mounts for hot-reload
- ✅ Debug ports exposed (5678, 9229)
- ✅ Relaxed security (no read-only filesystems)
- ✅ Single worker for easier debugging
- ✅ Development tools (Adminer, Redis Commander, Mailhog)

#### Production Security

The base `docker-compose.yml` enforces security:

- ✅ Non-root users (UID 1001-1007)
- ✅ Read-only root filesystems
- ✅ Dropped Linux capabilities
- ✅ Network isolation
- ✅ Resource limits
- ✅ Health checks

---

## Service Overview

### Core Services

#### 1. PostgreSQL Database
- **Image**: postgres:16-alpine
- **Port**: 5434 → 5432
- **Volume**: `postgres_data`
- **Purpose**: Primary data storage

**Health Check**:
```bash
docker compose exec postgres pg_isready -U toolboxai
```

#### 2. Redis Cache
- **Image**: redis:7-alpine
- **Port**: 6381 → 6379
- **Volume**: `redis_data`
- **Purpose**: Caching, sessions, Celery broker

**Health Check**:
```bash
docker compose exec redis redis-cli ping
```

#### 3. FastAPI Backend
- **Build**: `infrastructure/docker/dockerfiles/backend.Dockerfile`
- **Port**: 8009
- **Volumes**: Source code (dev), logs, agent data
- **Purpose**: REST API, business logic

**Health Check**:
```bash
curl http://localhost:8009/health
```

#### 4. React Dashboard
- **Build**: `infrastructure/docker/dockerfiles/dashboard-2025.Dockerfile`
- **Port**: 5180 → 80
- **Purpose**: User interface

**Health Check**:
```bash
curl http://localhost:5180/health
```

### Support Services

#### 5. MCP Server
- **Port**: 9877
- **Purpose**: Model Context Protocol for AI coordination

#### 6. Agent Coordinator
- **Port**: 8888
- **Purpose**: AI agent orchestration

#### 7. Celery Worker
- **Purpose**: Background task processing
- **Queues**: default, high_priority, low_priority, email, reports, ai_generation

#### 8. Celery Beat
- **Purpose**: Periodic task scheduling

#### 9. Celery Flower (Dev Only)
- **Port**: 5555
- **Purpose**: Celery monitoring dashboard
- **Access**: http://localhost:5555 (admin/admin)

#### 10. Roblox Sync (Rojo)
- **Port**: 34872
- **Purpose**: Roblox Studio synchronization

### Development-Only Services

#### Adminer
- **Port**: 8080
- **Purpose**: Database management GUI
- **Credentials**: Use database credentials

#### Redis Commander
- **Port**: 8081
- **Purpose**: Redis management GUI
- **Credentials**: admin/admin

#### Mailhog
- **Port**: 8025 (UI), 1025 (SMTP)
- **Purpose**: Email testing

---

## Troubleshooting

### Common Issues

#### Issue 1: Port Already in Use

**Symptoms**:
```
Error: bind: address already in use
```

**Solution**:
```bash
# Find process using port
lsof -ti:5180  # Example for dashboard port

# Kill process
kill -9 $(lsof -ti:5180)

# Or change port in .env
PORT=5181
```

#### Issue 2: Docker Secrets Not Found

**Symptoms**:
```
Error: secret not found: db_password
```

**Solution**:
```bash
# Create secrets
./infrastructure/docker/scripts/create-secrets.sh development

# Verify created
docker secret ls
```

#### Issue 3: Services Not Starting

**Symptoms**:
```
Container exits immediately
```

**Solution**:
```bash
# Check logs for specific service
docker compose logs backend

# Common issues:
# - Missing environment variables
# - Configuration file not found
# - Port conflict
# - Insufficient resources

# Restart single service
docker compose restart backend
```

#### Issue 4: Database Connection Failed

**Symptoms**:
```
FATAL: password authentication failed
```

**Solution**:
```bash
# Reset database
docker compose down -v  # WARNING: Deletes all data
docker compose up -d postgres

# Check credentials match in:
# - .env file
# - Docker secrets
# - Application config
```

#### Issue 5: Health Checks Failing

**Symptoms**:
```
Service marked as unhealthy
```

**Solution**:
```bash
# Check service logs
docker compose logs backend

# Test health endpoint manually
docker compose exec backend curl localhost:8009/health

# Increase health check timeouts
# Edit docker-compose.yml:
healthcheck:
  interval: 60s
  timeout: 30s
  retries: 5
  start_period: 120s
```

### Debug Commands

```bash
# View all containers
docker compose ps

# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f backend

# Execute command in container
docker compose exec backend bash

# Check resource usage
docker stats

# Inspect container
docker compose exec backend env | grep DATABASE

# View networks
docker network ls

# Inspect network
docker network inspect compose_backend
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All secrets generated with secure random values
- [ ] `.env` file contains production values
- [ ] API keys are valid and have proper permissions
- [ ] SSL/TLS certificates configured
- [ ] Backup strategy implemented
- [ ] Monitoring configured (Prometheus/Grafana)
- [ ] Log aggregation configured
- [ ] Resource limits reviewed and adjusted
- [ ] Security scan completed on images
- [ ] Load testing performed

### Production Environment Setup

```bash
# 1. Prepare production environment file
cp .env.docker.example .env.production

# 2. Edit with production values
nano .env.production

# 3. Generate secure secrets
openssl rand -hex 32 > jwt_secret.txt
openssl rand -base64 32 > db_password.txt
openssl rand -base64 32 > redis_password.txt

# 4. Create Docker secrets from files
echo "$(cat db_password.txt)" | docker secret create db_password -
echo "postgresql://toolboxai:$(cat db_password.txt)@postgres:5432/toolboxai" | docker secret create database_url -
echo "redis://:$(cat redis_password.txt)@redis:6379/0" | docker secret create redis_url -
echo "$(cat jwt_secret.txt)" | docker secret create jwt_secret -

# 5. Securely store secret files
# Move to secure location or password manager
# Delete local copies
rm -P jwt_secret.txt db_password.txt redis_password.txt

# 6. Deploy
ENV_FILE=.env.production docker compose -f docker-compose.yml up -d

# 7. Verify deployment
docker compose ps
curl https://your-domain.com/health
```

### Production Monitoring

```bash
# Enable Prometheus monitoring
docker compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000

# View Prometheus
open http://localhost:9090

# Check service health
curl http://localhost:8009/health
```

### Backup Procedures

```bash
# Database backup
docker compose exec postgres pg_dump -U toolboxai toolboxai > backup-$(date +%Y%m%d).sql

# Redis backup
docker compose exec redis redis-cli --rdb /data/dump.rdb
docker cp <container_id>:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb

# Configuration backup
tar -czf config-backup-$(date +%Y%m%d).tar.gz infrastructure/docker/compose/config
```

### Scaling Services

```bash
# Scale Celery workers
docker compose up -d --scale celery-worker=5

# Scale backend API
docker compose up -d --scale backend=3

# Add load balancer (nginx)
# Edit docker-compose.yml to add nginx service
```

---

## Additional Resources

### Documentation
- [Architecture Overview](./ARCHITECTURE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Secrets Management](./SECRETS_MANAGEMENT.md)
- [Development Guide](./DEVELOPMENT.md)

### External Links
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

### Support
- **GitHub Issues**: https://github.com/ToolBoxAI-Solutions/toolboxai/issues
- **Discussion Forum**: https://github.com/ToolBoxAI-Solutions/toolboxai/discussions
- **Email**: support@toolboxai.com

---

## Changelog

### October 1, 2025
- ✅ Created comprehensive setup guide
- ✅ Added automated setup script
- ✅ Implemented Docker secrets management
- ✅ Added development and production configurations
- ✅ Documented all services and health checks

---

**Next Steps**: After successful setup, proceed to the [Development Guide](./DEVELOPMENT.md) to learn about the development workflow.
