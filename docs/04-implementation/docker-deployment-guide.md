---
title: Docker Deployment Guide 2025
description: Comprehensive Docker deployment and containerization guide
version: 2.0.0
last_updated: 2025-09-14
---

# 🐳 Docker Deployment Guide 2025

## Overview

This guide provides comprehensive instructions for deploying the ToolboxAI Solutions platform using Docker containers, implementing 2025 best practices for containerization, security, and orchestration.

## 🏗️ Container Architecture

### Service Overview

```mermaid
graph TB
    subgraph "Frontend Services"
        A[Dashboard Frontend] --> B[Nginx Reverse Proxy]
    end

    subgraph "Backend Services"
        C[FastAPI Main] --> D[PostgreSQL]
        C --> E[Redis Cache]
        F[Flask Bridge] --> C
        G[Ghost CMS] --> D
        H[WebSocket Server] --> E
    end

    subgraph "Infrastructure"
        I[Prometheus] --> J[Grafana]
        K[Backup Service] --> D
    end
```

### Container Specifications

| Service | Image | Ports | Resources | Health Check |
|---------|-------|-------|-----------|--------------|
| FastAPI Main | `ghcr.io/toolboxai-solutions/backend:latest` | 8008, 9876 | 2 CPU, 2GB RAM | `/health` |
| Dashboard Frontend | `ghcr.io/toolboxai-solutions/frontend:latest` | 80 | 0.5 CPU, 1GB RAM | `/health` |
| Dashboard Backend | `ghcr.io/toolboxai-solutions/dashboard-backend:latest` | 8001 | 1 CPU, 1GB RAM | `/api/health` |
| Ghost CMS | `ghcr.io/toolboxai-solutions/ghost:latest` | 8000 | 1 CPU, 1GB RAM | `/ghost/api/v3/admin/site/` |
| Flask Bridge | `ghcr.io/toolboxai-solutions/flask-bridge:latest` | 5001 | 0.5 CPU, 512MB RAM | `/status` |
| PostgreSQL | `postgres:15-alpine` | 5432 | 2 CPU, 4GB RAM | `pg_isready` |
| Redis | `redis:7-alpine` | 6379 | 0.5 CPU, 512MB RAM | `redis-cli ping` |

## 🚀 Quick Start

### Prerequisites

- Docker Engine 24.0+ or Docker Desktop 4.25+
- Docker Compose 2.20+
- 8GB RAM minimum, 16GB recommended
- 50GB disk space

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/ToolBoxAI-Solutions/ToolboxAI-Solutions.git
cd ToolboxAI-Solutions

# Create environment file
cp .env.example .env

# Start development environment
docker-compose -f infrastructure/docker/docker-compose.staging.yml up -d

# Check service status
docker-compose ps
```

### Production Deployment

```bash
# Set production environment variables
export ENVIRONMENT=production
export POSTGRES_PASSWORD=your_secure_password
export REDIS_PASSWORD=your_redis_password
export JWT_SECRET_KEY=your_jwt_secret

# Deploy production stack
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f infrastructure/docker/docker-compose.prod.yml ps
```

## 🐳 Dockerfile Analysis

### Backend Service (FastAPI)

```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc g++ make libpq-dev libffi-dev libssl-dev git && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt requirements-ai.txt ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-ai.txt

# Runtime stage
FROM python:3.11-slim AS runtime

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r toolboxai && \
    useradd -r -g toolboxai -d /app -s /sbin/nologin toolboxai

# Copy application code
COPY --chown=toolboxai:toolboxai . /app
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Switch to non-root user
USER toolboxai

# Expose ports
EXPOSE 8008 9876

# Start command
CMD ["python", "-m", "uvicorn", "server.main:app", \
     "--host", "0.0.0.0", "--port", "8008", \
     "--workers", "4", "--loop", "uvloop"]
```

### Frontend Service (React)

```dockerfile
# Build stage
FROM node:18-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git python3 make g++

WORKDIR /build

# Copy package files
COPY package*.json tsconfig*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY src ./src
COPY public ./public
COPY index.html ./
COPY vite.config.ts ./

# Build application
ENV NODE_ENV=production
RUN npm run build

# Production stage with nginx
FROM nginx:alpine AS runtime

# Install runtime dependencies
RUN apk add --no-cache curl

# Copy nginx configuration
COPY config/production/nginx/frontend.conf /etc/nginx/conf.d/

# Copy built application
COPY --from=builder /build/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S toolboxai && \
    adduser -S -u 1001 -G toolboxai toolboxai

# Configure nginx to run as non-root
RUN sed -i 's/user  nginx;/user  toolboxai;/g' /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Switch to non-root user
USER toolboxai

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

## 🔧 Docker Compose Configuration

### Production Configuration

```yaml
version: '3.9'

x-common-variables: &common-variables
  TZ: UTC
  LOG_LEVEL: ${LOG_LEVEL:-INFO}

x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

services:
  # Nginx Reverse Proxy & Load Balancer
  nginx:
    image: nginx:alpine
    container_name: toolboxai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_files:/usr/share/nginx/html/static
    depends_on:
      - fastapi-main
      - dashboard-backend
      - dashboard-frontend
    networks:
      - toolboxai_network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "nginx", "-t"]

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: toolboxai-postgres
    environment:
      POSTGRES_DB: toolboxai_prod
      POSTGRES_USER: toolboxai_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_MULTIPLE_DATABASES: educational_platform,ghost_backend,roblox_data,mcp_memory
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
    ports:
      - '127.0.0.1:5432:5432'
    networks:
      - database_network
      - toolboxai_network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD-SHELL", "pg_isready -U toolboxai_user -d toolboxai_prod"]

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: toolboxai-redis
    command: >
      redis-server
      --appendonly yes
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - '127.0.0.1:6379:6379'
    networks:
      - toolboxai_network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]

  # FastAPI Main Backend
  fastapi-main:
    image: ghcr.io/toolboxai-solutions/backend:${VERSION:-latest}
    container_name: toolboxai-fastapi
    environment:
      <<: *common-variables
      ENVIRONMENT: production
      DATABASE_URL: postgresql://toolboxai_user:${POSTGRES_PASSWORD}@postgres:5432/educational_platform
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - '127.0.0.1:8008:8008'
      - '127.0.0.1:9876:9876'
    volumes:
      - agent_data:/app/agent_data
      - logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - toolboxai_network
      - database_network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  agent_data:
    driver: local
  logs:
    driver: local
  static_files:
    driver: local

networks:
  toolboxai_network:
    driver: overlay
    attachable: true
  database_network:
    driver: overlay
    internal: true
```

## 🔒 Security Configuration

### Container Security

```yaml
# Security context for containers
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

### Network Security

```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: toolboxai-network-policy
spec:
  podSelector:
    matchLabels:
      app: toolboxai
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: toolboxai-production
    ports:
    - protocol: TCP
      port: 8008
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: toolboxai-production
    ports:
    - protocol: TCP
      port: 5432
```

## 📊 Monitoring & Logging

### Prometheus Configuration

```yaml
# Prometheus monitoring
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
    - job_name: 'toolboxai-backend'
      static_configs:
      - targets: ['fastapi-main:8008']
      metrics_path: /metrics
      scrape_interval: 30s
```

### Logging Configuration

```yaml
# Fluentd logging
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>

    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name toolboxai-logs
    </match>
```

## 🚀 Deployment Strategies

### Blue-Green Deployment

```bash
#!/bin/bash
# Blue-green deployment script

# Deploy to green environment
docker-compose -f docker-compose.prod.yml up -d --scale fastapi-main=0
docker-compose -f docker-compose.prod.yml up -d --scale fastapi-main=3

# Health check
curl -f http://localhost:8008/health || exit 1

# Switch traffic (update load balancer)
# Update nginx configuration to point to green environment

# Clean up blue environment
docker-compose -f docker-compose.prod.yml stop fastapi-main-blue
```

### Rolling Update

```bash
#!/bin/bash
# Rolling update script

# Update images
docker-compose -f docker-compose.prod.yml pull

# Rolling update
docker-compose -f docker-compose.prod.yml up -d --no-deps fastapi-main

# Verify update
docker-compose -f docker-compose.prod.yml ps
```

## 🔧 Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker-compose logs fastapi-main

# Check container status
docker-compose ps

# Check resource usage
docker stats
```

#### Database Connection Issues

```bash
# Check database connectivity
docker-compose exec postgres psql -U toolboxai_user -d toolboxai_prod -c "SELECT 1;"

# Check network connectivity
docker-compose exec fastapi-main ping postgres
```

#### Memory Issues

```bash
# Check memory usage
docker stats --no-stream

# Increase memory limits in docker-compose.yml
services:
  fastapi-main:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Performance Optimization

#### Resource Tuning

```yaml
# Optimized resource configuration
services:
  fastapi-main:
    deploy:
      resources:
        requests:
          cpus: '1'
          memory: 1G
        limits:
          cpus: '2'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

#### Database Optimization

```yaml
# PostgreSQL optimization
postgres:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_MAINTENANCE_WORK_MEM: 64MB
    POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
```

## 📋 Maintenance Procedures

### Regular Maintenance

#### Daily Tasks
- Monitor container health
- Check resource usage
- Review logs for errors
- Verify backup completion

#### Weekly Tasks
- Update base images
- Review security patches
- Analyze performance metrics
- Test disaster recovery

#### Monthly Tasks
- Full security audit
- Capacity planning review
- Update documentation
- Disaster recovery testing

### Backup Procedures

```bash
#!/bin/bash
# Database backup script

# Create backup
docker-compose exec postgres pg_dump -U toolboxai_user toolboxai_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d_%H%M%S).sql.gz s3://toolboxai-backups/
```

## 🎯 Best Practices

### Container Best Practices

1. **Use Multi-stage Builds**: Reduce image size and attack surface
2. **Non-root Users**: Run containers as non-root users
3. **Health Checks**: Implement comprehensive health checks
4. **Resource Limits**: Set appropriate resource limits
5. **Security Scanning**: Regular vulnerability scanning

### Docker Compose Best Practices

1. **Environment Variables**: Use environment files for secrets
2. **Networks**: Use custom networks for service isolation
3. **Volumes**: Use named volumes for persistent data
4. **Dependencies**: Define proper service dependencies
5. **Health Checks**: Implement health checks for all services

### Monitoring Best Practices

1. **Comprehensive Logging**: Log all important events
2. **Metrics Collection**: Collect application and system metrics
3. **Alerting**: Set up appropriate alerts
4. **Dashboard**: Create monitoring dashboards
5. **Documentation**: Document monitoring procedures

---

*Last Updated: 2025-09-14*
*Version: 2.0.0*
*Compliance: COPPA, FERPA, GDPR, SOC 2 Type 2*
