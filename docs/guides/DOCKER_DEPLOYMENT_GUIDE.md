# Docker Deployment Guide for ToolboxAI Backend

This guide provides step-by-step instructions for deploying the ToolboxAI backend using Docker.

## Prerequisites

1. **Docker & Docker Compose**: Install Docker Desktop or Docker Engine
2. **Environment Variables**: Copy the appropriate environment file

## Quick Start

### 1. Prepare Environment
```bash
# Copy the Docker environment configuration
cp .env.docker .env

# Or create your own .env file with required variables
```

### 2. Test Configuration (Optional)
```bash
# Test that the backend configuration is Docker-ready
python scripts/test_docker_config.py
```

### 3. Start Services
```bash
# Start all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Or start services individually
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres redis
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d fastapi-main
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d dashboard-frontend
```

### 4. Verify Deployment
```bash
# Check service status
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Check backend health
curl http://localhost:8009/health

# View logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs fastapi-main
```

## Environment Configuration

### Required Environment Variables

The following variables must be set in your `.env` file:

```bash
# Database Configuration
POSTGRES_DB=educational_platform_dev
POSTGRES_USER=eduplatform
POSTGRES_PASSWORD=eduplatform2024
DATABASE_URL=postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Server Configuration
HOST=0.0.0.0  # CRITICAL: Must be 0.0.0.0 for Docker
PORT=8009
WORKERS=2
ENVIRONMENT=development

# Security
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
```

### Optional Configuration

```bash
# AI Services
OPENAI_API_KEY=your-openai-api-key
LANGCHAIN_API_KEY=your-langchain-api-key

# Pusher (for realtime features)
PUSHER_ENABLED=true
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=us2

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

## Docker Services

### Core Services

1. **postgres** (Port 5434 → 5432)
   - PostgreSQL 15 database
   - Health check: `pg_isready`

2. **redis** (Port 6381 → 6379) 
   - Redis 7 cache
   - Health check: `redis-cli ping`

3. **fastapi-main** (Port 8009 → 8009)
   - Main FastAPI backend
   - Health check: `curl http://localhost:8009/health`

### Additional Services

4. **dashboard-frontend** (Port 5179 → 5179)
   - React dashboard
   - Health check: `wget --spider http://localhost:5179`

5. **mcp-server** (Port 9877 → 9877)
   - Model Context Protocol server
   - Health check: `curl http://localhost:9877/health`

6. **agent-coordinator** (Port 8888 → 8888)
   - AI agent orchestration
   - Health check: `curl http://localhost:8888/health`

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start
```bash
# Check if host is properly configured
grep "HOST=" .env
# Should show: HOST=0.0.0.0

# Check backend logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs fastapi-main
```

#### 2. Database Connection Issues
```bash
# Check if database is healthy
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps postgres

# Test database connection
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec postgres pg_isready -U eduplatform -d educational_platform_dev
```

#### 3. Port Conflicts
```bash
# Check for port conflicts
lsof -i :8009  # Backend
lsof -i :5434  # PostgreSQL
lsof -i :6381  # Redis

# Stop conflicting processes or change ports in docker-compose.dev.yml
```

#### 4. Build Context Too Large
```bash
# Clean up unnecessary files
docker system prune -f

# Check .dockerignore is properly excluding large directories
```

### Health Checks

All services include health checks that ensure proper startup:

```bash
# Check all service health
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Manual health checks
curl http://localhost:8009/health        # Backend
curl http://localhost:8009/migration/status  # Migration status
```

### Logs and Debugging

```bash
# View all logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs

# View specific service logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs fastapi-main
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs postgres
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs redis

# Follow logs in real-time
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main
```

## Development vs Production

### Development (docker-compose.dev.yml)
- Hot-reload enabled
- Debug logging
- Volume mounts for development
- Exposed ports for local access

### Production (docker-compose.prod.yml)
- Multi-replica deployment
- Resource limits
- Nginx load balancer
- SSL termination
- Monitoring (Prometheus/Grafana)

## Performance Optimization

### Resource Limits
The Docker Compose files include resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Scaling Services
```bash
# Scale backend replicas
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d --scale fastapi-main=3

# Scale agent workers
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d --scale educational-agents=5
```

## Security Considerations

1. **Change default passwords** in production
2. **Use secure JWT secrets** (not the example ones)
3. **Enable SSL** in production deployment
4. **Restrict database access** (internal network only)
5. **Use environment-specific API keys**

## Next Steps

After successful deployment:

1. **Configure monitoring** (Sentry, Prometheus)
2. **Set up backups** for PostgreSQL
3. **Configure SSL certificates** for production
4. **Set up CI/CD pipeline** for automated deployments
5. **Configure load balancing** for high availability

## Support

For issues:
1. Check the troubleshooting section above
2. Review service logs for error messages
3. Verify environment variable configuration
4. Test with the provided `scripts/test_docker_config.py` script

