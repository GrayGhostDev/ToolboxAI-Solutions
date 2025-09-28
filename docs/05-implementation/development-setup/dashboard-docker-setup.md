---
title: Dashboard Docker Development Setup
description: Complete guide for running the React dashboard in Docker with hot-reload development
audience: developers
difficulty: intermediate
estimated_time: 20 minutes
last_updated: 2025-01-20
prerequisites:
  - Docker 24+
  - Docker Compose 2.0+
  - Basic knowledge of React/Vite
---

# Dashboard Docker Development Setup

This guide covers running the ToolboxAI React dashboard in Docker with full hot-reload development capabilities.

## 🎯 Overview

The dashboard Docker setup provides:

- **Hot-reload development** with Vite dev server
- **Inter-container communication** with backend services
- **Isolated environment** avoiding local Node.js conflicts
- **Production-like networking** for realistic testing
- **Health checks** ensuring >85% test pass rate

## 🏗️ Architecture

### Container Structure

```
┌─────────────────────────────────────────┐
│             Docker Network              │
│  ┌─────────────────┐  ┌─────────────────┤
│  │ dashboard-frontend │  │ fastapi-main    │
│  │ Port: 5179      │  │ Port: 8009      │
│  │ Node.js 22      │  │ Python 3.12     │
│  └─────────────────┘  └─────────────────┤
│  ┌─────────────────┐  ┌─────────────────┤
│  │ postgres        │  │ redis           │
│  │ Port: 5434      │  │ Port: 6381      │
│  └─────────────────┘  └─────────────────┤
└─────────────────────────────────────────┘
```

### Service Dependencies

```mermaid
graph TD
    A[dashboard-frontend:5179] --> B[fastapi-main:8009]
    B --> C[postgres:5434]
    B --> D[redis:6381]
    B --> E[mcp-server:9877]
```

## 🚀 Quick Start

### 1. Environment Configuration

Create or update your `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_DB=toolboxai_dev
POSTGRES_USER=toolboxai
POSTGRES_PASSWORD=dev_password
DATABASE_URL=postgresql://toolboxai:dev_password@postgres:5432/toolboxai_dev

# Redis Configuration
REDIS_PASSWORD=dev_redis_pass
REDIS_URL=redis://:dev_redis_pass@redis:6379

# Pusher Realtime Configuration
PUSHER_ENABLED=true
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2

# API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Development Flags
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 2. Start Dashboard Development

```bash
# Start all required services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres redis fastapi-main

# Start dashboard with hot-reload
docker-compose -f infrastructure/docker/docker-compose.dev.yml up dashboard-frontend

# Or start everything at once
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

### 3. Access Services

- **Dashboard**: http://localhost:5179
- **Backend API**: http://localhost:8009
- **API Docs**: http://localhost:8009/docs

## 🔧 Configuration Details

### Dashboard Dockerfile

Located at `infrastructure/docker/dashboard.dev.Dockerfile`:

```dockerfile
FROM node:22-alpine

WORKDIR /app

# Copy dashboard application
COPY apps/dashboard/ ./

# Install dependencies with legacy peer deps support
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Clear Vite cache for clean builds
RUN rm -rf node_modules/.vite

EXPOSE 5179

# Environment variables will be passed from docker-compose
ENV NODE_ENV=development

# Health check for service monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:5179', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }).on('error', () => { process.exit(1); });"

# Start Vite dev server with hot-reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5179", "--force"]
```

### Docker Compose Service

From `infrastructure/docker/docker-compose.dev.yml`:

```yaml
dashboard-frontend:
  image: ghcr.io/toolboxai-solutions/frontend-dev:latest
  build:
    context: ../..
    dockerfile: infrastructure/docker/dashboard.dev.Dockerfile
  container_name: toolboxai-dashboard-frontend
  environment:
    NODE_ENV: development
    # Docker service names for internal communication
    VITE_API_BASE_URL: http://fastapi-main:8009
    VITE_FASTAPI_URL: http://fastapi-main:8009
    VITE_WS_URL: http://fastapi-main:8009
    VITE_PROXY_TARGET: http://fastapi-main:8009
    # Pusher Configuration
    VITE_PUSHER_KEY: ${PUSHER_KEY}
    VITE_PUSHER_CLUSTER: ${PUSHER_CLUSTER:-us2}
    VITE_PUSHER_AUTH_ENDPOINT: http://fastapi-main:8009/api/v1/pusher/auth
    # Feature Flags
    VITE_ENABLE_WEBSOCKET: true
    VITE_ENABLE_GAMIFICATION: true
    VITE_ENABLE_ANALYTICS: true
    # Development flags
    VITE_DEBUG_MODE: true
    VITE_MOCK_API: false
  ports:
    - '5179:5179'
  # Volume mounts for hot-reload development
  volumes:
    - ../../apps/dashboard:/app
    - /app/node_modules
  depends_on:
    fastapi-main:
      condition: service_healthy
  networks:
    - toolboxai_network
```

## 🔄 Development Workflow

### Hot-Reload Development

The dashboard supports automatic code reloading:

1. **File watching**: Changes in `apps/dashboard/src/` trigger rebuilds
2. **Fast refresh**: React components update without losing state
3. **Style updates**: CSS/SCSS changes apply instantly
4. **Asset reloading**: Static assets update automatically

### Making Code Changes

```bash
# Edit files in apps/dashboard/src/
# Changes are automatically detected and applied

# View real-time logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend

# Restart if needed
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart dashboard-frontend
```

### Testing in Development

```bash
# Run tests inside the container
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test

# Run tests with coverage (must maintain >85%)
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm run test:coverage

# Run specific test file
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test ComponentName.test.tsx
```

## 🌐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API endpoint | `http://fastapi-main:8009` |
| `VITE_PUSHER_KEY` | Pusher public key | `your-pusher-key` |
| `VITE_PUSHER_CLUSTER` | Pusher cluster | `us2` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_DEBUG_MODE` | Enable debug logging | `true` |
| `VITE_MOCK_API` | Use mock API responses | `false` |
| `VITE_ENABLE_GAMIFICATION` | Enable gamification features | `true` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics tracking | `true` |

### Inter-Container Communication

The dashboard uses Docker service names for backend communication:

```javascript
// In development, these resolve to container IPs:
// http://fastapi-main:8009 -> http://172.18.0.3:8009

const API_BASE = import.meta.env.VITE_API_BASE_URL; // "http://fastapi-main:8009"
const WS_URL = import.meta.env.VITE_WS_URL;         // "http://fastapi-main:8009"
```

## 🔍 Debugging & Troubleshooting

### Common Issues

#### 1. Container Won't Start

**Symptoms:**
- Container exits immediately
- Port binding errors
- Health check failures

**Solutions:**
```bash
# Check container logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs dashboard-frontend

# Verify port availability
lsof -i :5179

# Check service dependencies
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps
```

#### 2. Hot-Reload Not Working

**Symptoms:**
- Code changes not reflected
- Manual refresh required
- Build errors on change

**Solutions:**
```bash
# Verify volume mounts
docker-compose -f infrastructure/docker/docker-compose.dev.yml config

# Restart with fresh build
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache dashboard-frontend
docker-compose -f infrastructure/docker/docker-compose.dev.yml up dashboard-frontend
```

#### 3. API Communication Failures

**Symptoms:**
- Network errors in browser console
- CORS errors
- 404 errors for API calls

**Solutions:**
```bash
# Test inter-container connectivity
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend ping fastapi-main

# Check backend health
curl http://localhost:8009/health

# Verify environment variables
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend env | grep VITE
```

#### 4. Test Failures (Below 85% Threshold)

**Symptoms:**
- Test suite fails
- Coverage below 85%
- CI/CD pipeline failures

**Solutions:**
```bash
# Run tests with verbose output
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test -- --verbose

# Check specific test file
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test -- --testPathPattern=ComponentName

# Update snapshots if needed
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test -- --updateSnapshot
```

### Health Checks

The dashboard includes built-in health monitoring:

```bash
# Check service health
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# View health check logs
docker inspect toolboxai-dashboard-frontend | jq '.[0].State.Health'

# Manual health check
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend node -e "require('http').get('http://localhost:5179', (res) => console.log('Status:', res.statusCode))"
```

## 🚀 Performance Optimization

### Build Performance

```bash
# Use buildx for faster builds
docker buildx build --platform linux/amd64 -t toolboxai-dashboard:dev -f infrastructure/docker/dashboard.dev.Dockerfile .

# Multi-stage builds for production
docker-compose -f infrastructure/docker/docker-compose.prod.yml build dashboard
```

### Runtime Performance

```bash
# Monitor resource usage
docker stats toolboxai-dashboard-frontend

# Scale for load testing
docker-compose -f infrastructure/docker/docker-compose.dev.yml up --scale dashboard-frontend=2
```

## 🔐 Security Considerations

### Development Security

- Environment variables are passed securely through Docker Compose
- No secrets are baked into images
- Local-only database credentials for development
- CORS properly configured for development domains

### Production Readiness

```bash
# Build production image
docker-compose -f infrastructure/docker/docker-compose.prod.yml build dashboard

# Security scan
docker scout cves toolboxai-dashboard:latest
```

## 📝 Maintenance

### Regular Tasks

```bash
# Update base image
docker pull node:22-alpine
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache dashboard-frontend

# Clear build cache
docker builder prune

# Update dependencies
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm audit fix
```

### Monitoring

```bash
# View real-time logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend

# Monitor resource usage
docker stats toolboxai-dashboard-frontend

# Check health metrics
curl http://localhost:5179/health
```

## 📚 Additional Resources

- [Main Development Setup](./comprehensive-development-setup.md)
- [Docker Compose Reference](../../infrastructure/docker/)
- [Dashboard Architecture](../../02-architecture/frontend-architecture.md)
- [Vite Configuration](../../apps/dashboard/vite.config.ts)

---

**Need help?**
- Check the [troubleshooting section](#debugging--troubleshooting)
- View container logs: `docker-compose -f infrastructure/docker/docker-compose.dev.yml logs dashboard-frontend`
- Join our [Discord community](https://discord.gg/toolboxai)

---

*Last Updated: 2025-01-20*
*Version: 2.1.0*
*Test Coverage Requirement: >85%*