# ToolBoxAI Production Deployment Guide

**Version:** 1.0.0
**Last Updated:** October 2, 2025
**Target Platform:** Kubernetes 1.29+, Docker 25+

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Docker Image Optimization](#docker-image-optimization)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Security Configuration](#security-configuration)
6. [Monitoring & Observability](#monitoring--observability)
7. [Scaling Strategy](#scaling-strategy)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Docker Engine 25+
docker --version  # Should be >= 25.0

# Docker Compose 2.24+
docker compose version  # Should be >= 2.24

# Kubernetes 1.29+
kubectl version --client  # Should be >= 1.29

# Helm 3.14+ (optional)
helm version  # Should be >= 3.14
```

### System Requirements

**Minimum Production Environment:**
- **CPU:** 8 cores (16 recommended)
- **RAM:** 16GB (32GB recommended)
- **Storage:** 100GB SSD (500GB recommended)
- **Network:** 1Gbps

**Kubernetes Cluster:**
- **Worker Nodes:** 3+ (for high availability)
- **Node CPU:** 4 cores minimum
- **Node RAM:** 8GB minimum
- **Container Runtime:** containerd 1.7+

---

## Quick Start

### 1. Build Optimized Images

```bash
# Build all optimized images
cd /path/to/toolboxai

# Backend (Target: <200MB)
DOCKER_BUILDKIT=1 docker build \
  -f infrastructure/docker/dockerfiles/backend-optimized.Dockerfile \
  --target production \
  -t ghcr.io/toolboxai-solutions/backend:latest \
  .

# Dashboard (Target: <100MB)
DOCKER_BUILDKIT=1 docker build \
  -f apps/dashboard/Dockerfile \
  --target runner \
  -t ghcr.io/toolboxai-solutions/dashboard:latest \
  apps/dashboard/

# Celery Worker (Target: <200MB)
DOCKER_BUILDKIT=1 docker build \
  -f infrastructure/docker/dockerfiles/celery-optimized.Dockerfile \
  --target worker \
  -t ghcr.io/toolboxai-solutions/celery-worker:latest \
  .

# Celery Beat
DOCKER_BUILDKIT=1 docker build \
  -f infrastructure/docker/dockerfiles/celery-optimized.Dockerfile \
  --target beat \
  -t ghcr.io/toolboxai-solutions/celery-beat:latest \
  .

# Flower Monitoring
DOCKER_BUILDKIT=1 docker build \
  -f infrastructure/docker/dockerfiles/celery-optimized.Dockerfile \
  --target flower \
  -t ghcr.io/toolboxai-solutions/flower:latest \
  .
```

### 2. Verify Image Sizes

```bash
# Check image sizes
docker images | grep toolboxai-solutions

# Expected output:
# backend:latest        ~150-180MB
# dashboard:latest      ~80-95MB
# celery-worker:latest  ~160-180MB
# celery-beat:latest    ~140-160MB
# flower:latest         ~170-190MB
```

### 3. Run Security Scan

```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Scan all images
for image in backend dashboard celery-worker celery-beat flower; do
  echo "Scanning ghcr.io/toolboxai-solutions/$image:latest"
  trivy image --severity CRITICAL,HIGH ghcr.io/toolboxai-solutions/$image:latest
done
```

---

## Docker Image Optimization

### Build Context Optimization

Our optimized `.dockerignore` reduces build context from ~500MB to <50MB:

```bash
# Check build context size
du -sh . | grep -v node_modules

# Before: ~500MB
# After: ~40-50MB
```

### Multi-Stage Build Benefits

**Backend Dockerfile** (`backend-optimized.Dockerfile`):
- **Stage 1 (builder):** Compiles dependencies (~800MB)
- **Stage 2 (production):** Runtime only (~150MB)
- **Reduction:** 81% smaller

**Key Optimizations:**
```dockerfile
# Alpine base instead of slim
FROM python:3.12-alpine AS production

# Virtual environment isolation
COPY --from=builder /opt/venv /opt/venv

# Cleanup
find /opt/venv -type d -name __pycache__ -exec rm -rf {} +
```

### Image Size Targets

| Service | Target | Typical Size | Status |
|---------|--------|--------------|--------|
| Backend | <200MB | ~150-180MB | ✅ |
| Dashboard | <100MB | ~80-95MB | ✅ |
| Celery Worker | <200MB | ~160-180MB | ✅ |
| Celery Beat | <200MB | ~140-160MB | ✅ |
| Flower | <200MB | ~170-190MB | ✅ |

---

## Kubernetes Deployment

### Architecture Overview

```
┌─────────────────────────────────────────┐
│           Ingress Controller            │
│      (NGINX/Traefik/Istio Gateway)     │
└────────────┬────────────────────────────┘
             │
   ┌─────────┴──────────┐
   │                    │
   ▼                    ▼
┌──────────┐      ┌──────────┐
│Dashboard │      │ Backend  │
│  (2-6    │      │  (3-10   │
│replicas) │      │replicas) │
└──────────┘      └────┬─────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌────────┐    ┌────────┐    ┌────────┐
   │Celery  │    │Celery  │    │Flower  │
   │Worker  │    │Beat    │    │Monitor │
   │(3-10)  │    │(1)     │    │(1)     │
   └────┬───┘    └───┬────┘    └───┬────┘
        │            │              │
        └────────────┼──────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   ┌────────┐              ┌────────┐
   │Postgres│              │ Redis  │
   │StatefulSet             │StatefulSet
   │(1-3)   │              │(1-3)   │
   └────────┘              └────────┘
```

### Deploy to Kubernetes

#### Step 1: Create Namespace

```bash
kubectl create namespace toolboxai-prod
kubectl label namespace toolboxai-prod environment=production
```

#### Step 2: Create Secrets

```bash
# Database credentials
kubectl create secret generic postgres-secrets \
  --from-literal=password='CHANGE_ME' \
  --from-literal=url='postgresql://toolboxai:CHANGE_ME@postgres:5432/toolboxai' \
  -n toolboxai-prod

# Redis password
kubectl create secret generic redis-secrets \
  --from-literal=password='CHANGE_ME' \
  -n toolboxai-prod

# Backend secrets
kubectl create secret generic backend-secrets \
  --from-literal=secret-key='CHANGE_ME' \
  --from-literal=jwt-secret='CHANGE_ME' \
  -n toolboxai-prod

# Celery secrets
kubectl create secret generic celery-secrets \
  --from-literal=broker-url='redis://:CHANGE_ME@redis:6379/0' \
  --from-literal=result-backend='redis://:CHANGE_ME@redis:6379/1' \
  -n toolboxai-prod

# Flower auth
kubectl create secret generic flower-secrets \
  --from-literal=basic-auth='admin:CHANGE_ME' \
  -n toolboxai-prod

# Container registry
kubectl create secret docker-registry ghcr-credentials \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  -n toolboxai-prod
```

#### Step 3: Deploy Using Kustomize

```bash
# Deploy all resources
kubectl apply -k infrastructure/kubernetes/base/ -n toolboxai-prod

# Watch deployment progress
kubectl get pods -n toolboxai-prod -w

# Check deployment status
kubectl rollout status deployment/backend -n toolboxai-prod
kubectl rollout status deployment/dashboard -n toolboxai-prod
kubectl rollout status deployment/celery-worker -n toolboxai-prod
```

#### Step 4: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n toolboxai-prod

# Check services
kubectl get svc -n toolboxai-prod

# Check ingress
kubectl get ingress -n toolboxai-prod

# Check HPA status
kubectl get hpa -n toolboxai-prod
```

---

## Security Configuration

### Security Best Practices

All images implement:

✅ **Non-root users** (UIDs 1001-1005)
✅ **Read-only root filesystem**
✅ **No privilege escalation**
✅ **Minimal capabilities (drop ALL)**
✅ **Seccomp profiles (RuntimeDefault)**
✅ **Network policies for isolation**
✅ **PodDisruptionBudgets for availability**

### Security Scanning

**Automated Scanning:**
```bash
# GitHub Actions runs security scans on:
# - Every PR
# - Every push to main/staging
# - Daily at 2 AM UTC

# Manual scan
gh workflow run docker-security-scan.yml
```

**Local Scanning:**
```bash
# Scan image for vulnerabilities
trivy image --severity CRITICAL,HIGH \
  ghcr.io/toolboxai-solutions/backend:latest

# Scan for secrets
trivy image --scanners secret \
  ghcr.io/toolboxai-solutions/backend:latest

# Scan for misconfigurations
trivy image --scanners config \
  ghcr.io/toolboxai-solutions/backend:latest
```

### Security Hardening Checklist

- [ ] All secrets stored in Kubernetes Secrets (not ConfigMaps)
- [ ] TLS/SSL enabled on all ingress endpoints
- [ ] Network policies restrict pod-to-pod traffic
- [ ] Resource limits set on all pods
- [ ] Security contexts configured
- [ ] Regular vulnerability scans passing
- [ ] Image signing enabled (Cosign/Notary)
- [ ] Runtime security monitoring (Falco)

---

## Monitoring & Observability

### Metrics Collection

**Prometheus Metrics:**
- Backend API metrics: `http://backend:8009/metrics`
- Celery worker metrics: `http://celery-exporter:9540/metrics`
- Redis metrics: `http://redis-exporter:9121/metrics`
- Postgres metrics: `http://postgres-exporter:9187/metrics`

**Key Metrics to Monitor:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Request latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Celery queue length
celery_queue_length

# Pod CPU usage
container_cpu_usage_seconds_total

# Pod memory usage
container_memory_working_set_bytes
```

### Grafana Dashboards

Access Grafana:
```bash
# Port forward
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Open browser
open http://localhost:3000
```

**Available Dashboards:**
- Kubernetes Cluster Overview
- Backend API Performance
- Celery Workers & Queue Status
- Database Performance
- Infrastructure Resources

### Logging

**Log Aggregation with Loki:**
```bash
# View logs
kubectl logs -f deployment/backend -n toolboxai-prod

# Query logs in Grafana
{namespace="toolboxai-prod", app="backend"} |= "error"

# Celery worker logs
{namespace="toolboxai-prod", app="celery-worker"} |= "task"
```

---

## Scaling Strategy

### Horizontal Pod Autoscaling (HPA)

**Backend API:**
```yaml
minReplicas: 3
maxReplicas: 10
metrics:
  - CPU: 70%
  - Memory: 80%
```

**Dashboard:**
```yaml
minReplicas: 2
maxReplicas: 6
metrics:
  - CPU: 70%
  - Memory: 80%
```

**Celery Workers:**
```yaml
minReplicas: 3
maxReplicas: 10
metrics:
  - CPU: 70%
  - Memory: 80%
```

### Manual Scaling

```bash
# Scale backend to 5 replicas
kubectl scale deployment backend --replicas=5 -n toolboxai-prod

# Scale celery workers to 8 replicas
kubectl scale deployment celery-worker --replicas=8 -n toolboxai-prod

# Scale dashboard to 4 replicas
kubectl scale deployment dashboard --replicas=4 -n toolboxai-prod
```

### Vertical Pod Autoscaling (VPA)

```bash
# Install VPA (if not already installed)
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vertical-pod-autoscaler.yaml

# Create VPA for backend
kubectl apply -f infrastructure/kubernetes/base/vpa/backend-vpa.yaml
```

---

## Troubleshooting

### Common Issues

#### 1. Pods Stuck in Pending

```bash
# Check pod events
kubectl describe pod <pod-name> -n toolboxai-prod

# Common causes:
# - Insufficient resources
# - Image pull errors
# - PVC binding issues

# Check node resources
kubectl top nodes
```

#### 2. High Memory Usage

```bash
# Check memory usage
kubectl top pods -n toolboxai-prod

# Increase memory limits
kubectl set resources deployment backend \
  --limits=memory=4Gi \
  -n toolboxai-prod
```

#### 3. Failed Health Checks

```bash
# Check liveness/readiness probes
kubectl describe pod <pod-name> -n toolboxai-prod

# View application logs
kubectl logs <pod-name> -n toolboxai-prod

# Exec into pod
kubectl exec -it <pod-name> -n toolboxai-prod -- sh
```

#### 4. Image Pull Errors

```bash
# Verify secret exists
kubectl get secret ghcr-credentials -n toolboxai-prod

# Recreate secret
kubectl delete secret ghcr-credentials -n toolboxai-prod
kubectl create secret docker-registry ghcr-credentials \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  -n toolboxai-prod
```

### Performance Tuning

**Database Connection Pooling:**
```python
# Backend settings
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
SQLALCHEMY_POOL_TIMEOUT = 30
```

**Celery Worker Tuning:**
```bash
# Increase concurrency
CELERY_WORKER_CONCURRENCY=8

# Increase prefetch
CELERY_WORKER_PREFETCH_MULTIPLIER=8

# Set max tasks per child
CELERY_WORKER_MAX_TASKS_PER_CHILD=2000
```

**Redis Tuning:**
```bash
# Increase max memory
maxmemory 4gb

# Set eviction policy
maxmemory-policy allkeys-lru
```

---

## Backup & Disaster Recovery

### Database Backups

```bash
# Create backup CronJob
kubectl apply -f infrastructure/kubernetes/base/backup/postgres-backup.yaml

# Manual backup
kubectl exec -it postgres-0 -n toolboxai-prod -- \
  pg_dump -U toolboxai -d toolboxai > backup-$(date +%Y%m%d).sql
```

### Volume Backups

```bash
# Backup PVCs using Velero
velero backup create toolboxai-backup \
  --include-namespaces toolboxai-prod

# Restore from backup
velero restore create --from-backup toolboxai-backup
```

---

## Production Checklist

Before going live:

- [ ] All images scanned with zero critical vulnerabilities
- [ ] All secrets properly configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan tested
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Rollback procedure tested

---

## Support & Resources

- **Documentation:** https://docs.toolboxai.solutions
- **GitHub:** https://github.com/ToolBoxAI-Solutions/toolboxai
- **Support:** support@toolboxai.solutions
- **Status Page:** https://status.toolboxai.solutions

---

**Last Reviewed:** October 2, 2025
**Next Review:** January 2, 2026
