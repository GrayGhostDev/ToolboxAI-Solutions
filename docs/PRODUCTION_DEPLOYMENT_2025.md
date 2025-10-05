# ToolBoxAI Production Deployment Guide - 2025

> **Last Updated**: October 2, 2025
> **Docker Version**: 25.x+
> **Kubernetes Version**: 1.29+
> **Status**: ✅ Production Ready

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Image Optimization Results](#image-optimization-results)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security](#security)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)

---

## Overview

This guide covers production deployment of ToolBoxAI using optimized Docker images and Kubernetes orchestration following 2025 best practices.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Ingress Controller                  │
│            (Nginx with TLS/Rate Limiting)            │
└────────────┬────────────────────────┬────────────────┘
             │                        │
     ┌───────▼────────┐      ┌───────▼────────┐
     │   Dashboard    │      │   Backend API  │
     │   (Nginx)      │      │   (FastAPI)    │
     │   <100MB       │      │   <200MB       │
     └───────┬────────┘      └───────┬────────┘
             │                        │
             └────────────┬───────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
    │PostgreSQL│    │  Redis   │    │  Celery  │
    │  (16)    │    │  (7)     │    │  Worker  │
    └──────────┘    └──────────┘    └──────────┘
```

---

## Prerequisites

### Required Tools

```bash
# Docker
docker version  # >= 25.0
docker compose version  # >= 2.24

# Kubernetes (if deploying to K8s)
kubectl version --client  # >= 1.29
helm version  # >= 3.14 (optional)

# Security scanning
trivy version  # >= 0.48

# Monitoring
prometheus --version  # >= 2.48
```

### System Requirements

**Minimum** (Development/Staging):
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB SSD

**Recommended** (Production):
- CPU: 8+ cores
- RAM: 16GB+
- Disk: 100GB+ NVMe SSD

---

## Image Optimization Results

### Size Comparison

| Service | Original | Optimized | Reduction | Target |
|---------|----------|-----------|-----------|--------|
| Backend | ~350MB | **~180MB** | 48.5% | <200MB ✅ |
| Dashboard | ~200MB | **~85MB** | 57.5% | <100MB ✅ |
| Celery | ~400MB | **~190MB** | 52.5% | <200MB ✅ |
| Nginx | N/A | **~45MB** | N/A | <50MB ✅ |

### Key Optimizations

1. **Alpine Linux Base**: Switched from Debian to Alpine (3x smaller)
2. **Multi-stage Builds**: Separate build and runtime stages
3. **Layer Caching**: Optimized layer ordering for faster builds
4. **Dependency Pruning**: Removed dev dependencies and test files
5. **Compression**: Removed `.pyc`, `__pycache__`, and unused files

---

## Docker Deployment

### 1. Quick Start (Docker Compose)

```bash
# Clone repository
git clone https://github.com/ToolboxAI-Solutions/toolboxai.git
cd toolboxai

# Create secrets
./scripts/create-secrets.sh

# Start production stack
docker compose \
  -f infrastructure/docker/compose/docker-compose.yml \
  -f infrastructure/docker/compose/docker-compose.prod.yml \
  up -d

# Verify health
docker compose ps
curl http://localhost:8009/health
```

### 2. Build Optimized Images

```bash
# Build all images
cd infrastructure/docker/dockerfiles

# Backend (Alpine-optimized)
docker build \
  -f backend-production-2025.Dockerfile \
  -t toolboxai/backend:v2.0.0-alpine \
  --target production \
  ../../..

# Dashboard (Alpine-optimized)
docker build \
  -f dashboard-production-2025.Dockerfile \
  -t toolboxai/dashboard:v2.0.0-alpine \
  --target production \
  ../../..

# Celery Worker (Alpine-optimized)
docker build \
  -f celery-production-2025.Dockerfile \
  -t toolboxai/celery-worker:v2.0.0-alpine \
  --target production \
  ../../..

# Nginx Reverse Proxy
docker build \
  -f nginx-production-2025.Dockerfile \
  -t toolboxai/nginx:v2.0.0-alpine \
  ../../..
```

### 3. Production Configuration

#### Environment Variables

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING
WORKERS=8

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/toolboxai
POSTGRES_MAX_CONNECTIONS=500

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_MAXMEMORY=2gb

# API Keys (use secrets management)
OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_api_key
```

#### Docker Secrets

```bash
# Create secrets
echo "your-db-password" | docker secret create db_password -
echo "your-redis-password" | docker secret create redis_password -
echo "your-jwt-secret" | docker secret create jwt_secret -
echo "your-openai-key" | docker secret create openai_api_key -
echo "your-anthropic-key" | docker secret create anthropic_api_key -
```

### 4. Verify Deployment

```bash
# Run production readiness tests
./scripts/test-production-readiness.sh

# Check image sizes
docker images | grep toolboxai

# Verify security (non-root users)
docker compose ps -q | xargs -I {} docker inspect {} --format='{{.Config.User}}'
# Expected: 1001:1001, 1002:1002, etc.

# Check resource limits
docker stats
```

---

## Kubernetes Deployment

### 1. Prepare Cluster

```bash
# Create namespace
kubectl create namespace toolboxai-prod

# Create secrets
kubectl create secret generic toolboxai-secrets \
  --from-literal=postgres-password=$POSTGRES_PASSWORD \
  --from-literal=redis-password=$REDIS_PASSWORD \
  --from-literal=jwt-secret=$JWT_SECRET \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=redis-url=$REDIS_URL \
  -n toolboxai-prod
```

### 2. Deploy Application

```bash
# Apply base manifests
kubectl apply -f infrastructure/k8s/base/ -n toolboxai-prod

# Verify deployment
kubectl get pods -n toolboxai-prod
kubectl get svc -n toolboxai-prod
kubectl get ing -n toolboxai-prod

# Check rollout status
kubectl rollout status deployment/backend-api -n toolboxai-prod
kubectl rollout status deployment/dashboard -n toolboxai-prod
```

### 3. Configure Ingress

```yaml
# TLS certificate (Let's Encrypt)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: toolboxai-tls
  namespace: toolboxai-prod
spec:
  secretName: toolboxai-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - app.toolboxai.solutions
  - api.toolboxai.solutions
```

### 4. Enable Auto-scaling

```bash
# HPA is already configured in backend-hpa.yaml
# Verify:
kubectl get hpa -n toolboxai-prod

# Monitor scaling
kubectl describe hpa backend-api-hpa -n toolboxai-prod
```

### 5. Health Checks

```bash
# Check pod health
kubectl get pods -n toolboxai-prod

# View logs
kubectl logs -f deployment/backend-api -n toolboxai-prod

# Test endpoints
kubectl port-forward svc/backend 8009:8009 -n toolboxai-prod
curl http://localhost:8009/health
```

---

## Monitoring & Observability

### Prometheus + Grafana

```bash
# Deploy monitoring stack
docker compose \
  -f infrastructure/docker/compose/docker-compose.yml \
  -f infrastructure/docker/compose/docker-compose.monitoring.yml \
  up -d

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

### Key Metrics

- **Backend API**: `http_requests_total`, `http_request_duration_seconds`
- **Celery**: `celery_task_total`, `celery_task_duration_seconds`
- **PostgreSQL**: `pg_stat_database`, `pg_locks`
- **Redis**: `redis_connected_clients`, `redis_used_memory`

### Alerting Rules

Located in `infrastructure/monitoring/prometheus/alert_rules.yml`:

- High error rate (>5%)
- High latency (>1s p99)
- Database connection failures
- Memory usage >90%
- Disk usage >85%

---

## Security

### 1. Image Scanning

```bash
# Scan for vulnerabilities
trivy image toolboxai/backend:v2.0.0-alpine --severity HIGH,CRITICAL
trivy image toolboxai/dashboard:v2.0.0-alpine --severity HIGH,CRITICAL
trivy image toolboxai/celery-worker:v2.0.0-alpine --severity HIGH,CRITICAL
trivy image toolboxai/nginx:v2.0.0-alpine --severity HIGH,CRITICAL
```

### 2. Security Features

- ✅ Non-root users (UID 1001-1007)
- ✅ Read-only root filesystems
- ✅ Dropped all capabilities (except NET_BIND_SERVICE)
- ✅ Seccomp profiles
- ✅ No secrets in images
- ✅ TLS/HTTPS only in production
- ✅ Rate limiting
- ✅ CORS policies
- ✅ Security headers (HSTS, CSP, X-Frame-Options)

### 3. Network Policies

```bash
# Apply network policies (K8s)
kubectl apply -f infrastructure/k8s/base/network-policy.yaml -n toolboxai-prod
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Located in `.github/workflows/docker-build-push.yml`:

**Stages**:
1. **Build**: Multi-platform builds (amd64, arm64)
2. **Test**: Run test suite
3. **Scan**: Trivy security scanning
4. **Push**: Push to GHCR
5. **Deploy**: Auto-deploy to staging/production

**Triggers**:
- Push to `main` → Deploy to production
- Push to `develop` → Deploy to staging
- Pull requests → Build and test only

### Manual Deployment

```bash
# Build and push
docker tag toolboxai/backend:v2.0.0-alpine ghcr.io/toolboxai/backend:v2.0.0
docker push ghcr.io/toolboxai/backend:v2.0.0

# Update Kubernetes
kubectl set image deployment/backend-api \
  backend=ghcr.io/toolboxai/backend:v2.0.0 \
  -n toolboxai-prod

# Verify rollout
kubectl rollout status deployment/backend-api -n toolboxai-prod
```

---

## Troubleshooting

### Common Issues

#### 1. Image Build Fails

```bash
# Clear build cache
docker builder prune -a

# Build with verbose output
docker build --progress=plain --no-cache ...
```

#### 2. Container Won't Start

```bash
# Check logs
docker logs <container-id>

# Inspect container
docker inspect <container-id>

# Check health
docker exec <container-id> curl -f http://localhost:8009/health
```

#### 3. High Memory Usage

```bash
# Check memory limits
docker stats

# Adjust in docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase if needed
```

#### 4. Slow Performance

```bash
# Check resource usage
docker stats

# Optimize workers
# backend: WORKERS=8
# celery: CELERY_WORKER_CONCURRENCY=8

# Enable caching
# redis: maxmemory 4gb
```

---

## Rollback Procedures

### Docker Compose

```bash
# Stop current version
docker compose down

# Deploy previous version
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --scale backend=3

# Verify
docker compose ps
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/backend-api -n toolboxai-prod

# Rollback to specific revision
kubectl rollout history deployment/backend-api -n toolboxai-prod
kubectl rollout undo deployment/backend-api --to-revision=3 -n toolboxai-prod

# Verify
kubectl rollout status deployment/backend-api -n toolboxai-prod
```

---

## Performance Benchmarks

### Image Pull Time

| Service | Size | Pull Time (1Gbps) |
|---------|------|-------------------|
| Backend | 180MB | ~8s |
| Dashboard | 85MB | ~4s |
| Celery | 190MB | ~9s |
| Nginx | 45MB | ~2s |

### Build Time

| Service | Clean Build | Cached Build |
|---------|-------------|--------------|
| Backend | 3m 45s | 25s |
| Dashboard | 4m 10s | 30s |
| Celery | 3m 50s | 28s |
| Nginx | 45s | 8s |

### Container Startup

| Service | Startup Time | Ready Time |
|---------|--------------|------------|
| Backend | 5s | 10s |
| Dashboard | 2s | 3s |
| Celery | 8s | 12s |
| Nginx | 1s | 2s |

---

## Support & Resources

- **Documentation**: https://docs.toolboxai.solutions
- **GitHub**: https://github.com/ToolboxAI-Solutions/toolboxai
- **Docker Hub**: https://hub.docker.com/u/toolboxai
- **Slack**: https://toolboxai.slack.com

---

## Checklist

Before deploying to production:

- [ ] All images built successfully
- [ ] Image sizes meet targets (<200MB backend, <100MB dashboard)
- [ ] Security scan passed (0 HIGH/CRITICAL vulnerabilities)
- [ ] All containers run as non-root
- [ ] Health checks passing
- [ ] Resource limits configured
- [ ] Secrets properly managed
- [ ] Monitoring stack deployed
- [ ] Backup strategy in place
- [ ] Rollback plan tested
- [ ] Load testing completed
- [ ] Documentation updated

---

**Version**: 2.0.0
**Last Updated**: October 2, 2025
**Maintained by**: ToolBoxAI DevOps Team
