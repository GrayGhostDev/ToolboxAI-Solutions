# Docker Production Optimization Worktree Tasks
**Branch**: feature/docker-production-optimization
**Ports**: Backend(8020), Dashboard(5191), MCP(9888), Coordinator(8899)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Follow Docker and container best practices!

**Requirements**:
- ✅ Docker 25+ with BuildKit
- ✅ Multi-stage builds for minimal images
- ✅ Non-root users in all containers
- ✅ Read-only filesystems where possible
- ✅ Auto-accept enabled for corrections
- ❌ NO exposing secrets in images

## Primary Objectives

### 1. **Production Docker Optimization**
   - Reduce Docker image sizes
   - Improve build times with caching
   - Enhance security posture
   - Optimize for production deployment

### 2. **Orchestration & Scaling**
   - Kubernetes deployment configs
   - Docker Swarm mode setup
   - Auto-scaling configuration
   - Health checks and readiness probes

### 3. **Monitoring & Observability**
   - Container metrics collection
   - Log aggregation
   - Distributed tracing
   - Performance monitoring

## Current Tasks

### Phase 1: Docker Image Optimization (Priority: CRITICAL)

**Current State**: Docker infrastructure modernized Sept 2024, but images can be further optimized

**Files to Optimize:**
- [ ] `infrastructure/docker/dockerfiles/Dockerfile.backend`
- [ ] `infrastructure/docker/dockerfiles/Dockerfile.dashboard`
- [ ] `infrastructure/docker/dockerfiles/Dockerfile.celery`
- [ ] `infrastructure/docker/dockerfiles/Dockerfile.nginx`

**Optimization Tasks**:
- [ ] Implement multi-stage builds for all images
- [ ] Use Alpine-based images where possible
- [ ] Add .dockerignore for smaller build contexts
- [ ] Implement layer caching strategies
- [ ] Remove development dependencies from prod images
- [ ] Use specific version tags (no `:latest`)
- [ ] Implement build-time argument passing
- [ ] Add health check instructions

**Image Size Targets**:
- Backend: < 200MB (currently unknown)
- Dashboard: < 100MB (currently unknown)
- Celery: < 200MB (currently unknown)
- Nginx: < 50MB (currently unknown)

### Phase 2: Docker Compose Production Config (Priority: HIGH)

**Files to Create/Update:**
- [ ] `infrastructure/docker/compose/docker-compose.prod.yml` - Production overrides
- [ ] `infrastructure/docker/compose/docker-compose.staging.yml` - Staging config
- [ ] `infrastructure/docker/compose/docker-compose.monitoring.yml` - Enhanced monitoring

**Production Configuration**:
- [ ] Add resource limits (CPU, memory)
- [ ] Configure restart policies
- [ ] Add logging configuration
- [ ] Implement health checks
- [ ] Add volume mounts for persistence
- [ ] Configure networks for isolation
- [ ] Add secrets management
- [ ] Configure service dependencies

**Monitoring Stack**:
- [ ] Prometheus for metrics
- [ ] Grafana for dashboards
- [ ] Loki for log aggregation
- [ ] Jaeger for distributed tracing
- [ ] cAdvisor for container metrics

### Phase 3: Docker Testing & Validation (Priority: CRITICAL)

**MANDATORY TESTING BEFORE PROCEEDING**:

**Test 1: Image Build Verification**
```bash
# Test all Dockerfiles build successfully
cd infrastructure/docker/dockerfiles
docker build -f Dockerfile.backend -t test-backend:latest ../../../
docker build -f Dockerfile.dashboard -t test-dashboard:latest ../../../
docker build -f Dockerfile.celery -t test-celery:latest ../../../
docker build -f Dockerfile.nginx -t test-nginx:latest ../../../

# Verify image sizes meet targets
docker images | grep test- | awk '{print $1, $7}'
# Expected: backend <200MB, dashboard <100MB, celery <200MB, nginx <50MB
```

**Test 2: Docker Compose Stack Validation**
```bash
# Test development stack
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
# All services should be "healthy" or "running"

# Test production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

**Test 3: Security Validation**
```bash
# Check all containers run as non-root
docker compose ps -q | xargs -I {} docker inspect {} --format='{{.Config.User}}'
# Expected: All output should be "1001:1001", "1002:1002", "1003:1003", or "1004:1004"

# Verify no secrets in images
docker history test-backend:latest | grep -iE "password|secret|key"
docker history test-dashboard:latest | grep -iE "password|secret|key"
# Expected: No matches (exit code 1)

# Check read-only filesystems
docker compose ps -q | xargs -I {} docker inspect {} --format='{{.HostConfig.ReadonlyRootfs}}'
# Expected: "true" for all containers
```

**Test 4: Health Check Validation**
```bash
# Wait for services to be healthy
timeout 60 bash -c 'until docker compose ps | grep -q "healthy"; do sleep 2; done'

# Test backend health endpoint
curl -f http://localhost:8009/health || echo "Backend health check FAILED"

# Test dashboard availability
curl -f http://localhost:5179/ || echo "Dashboard health check FAILED"

# Test Redis connectivity
docker compose exec redis redis-cli ping || echo "Redis health check FAILED"

# Test PostgreSQL connectivity
docker compose exec postgres pg_isready -U eduplatform || echo "PostgreSQL health check FAILED"
```

**Test 5: Resource Limits Validation**
```bash
# Check CPU limits are set
docker compose ps -q | xargs -I {} docker inspect {} --format='{{.HostConfig.CpuQuota}}'
# Expected: Non-zero values

# Check memory limits are set
docker compose ps -q | xargs -I {} docker inspect {} --format='{{.HostConfig.Memory}}'
# Expected: Non-zero values (e.g., 1073741824 for 1GB)
```

**Test 6: Network Isolation Validation**
```bash
# Verify custom networks exist
docker network ls | grep -E "toolboxai-network|toolboxai-monitoring"

# Check service network membership
docker compose ps -q | xargs -I {} docker inspect {} --format='{{range $net, $config := .NetworkSettings.Networks}}{{$net}} {{end}}'
# Expected: Services on appropriate networks
```

**Test 7: Monitoring Stack Validation**
```bash
# Start monitoring stack
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Test Prometheus
curl -f http://localhost:9090/-/healthy || echo "Prometheus health check FAILED"

# Test Grafana
curl -f http://localhost:3000/api/health || echo "Grafana health check FAILED"

# Test Loki
curl -f http://localhost:3100/ready || echo "Loki health check FAILED"
```

**Test 8: Build Performance Validation**
```bash
# Measure build times (should be <5 minutes each)
time docker build -f infrastructure/docker/dockerfiles/Dockerfile.backend -t test-backend:timed ../../../
time docker build -f infrastructure/docker/dockerfiles/Dockerfile.dashboard -t test-dashboard:timed ../../../

# Verify layer caching works (rebuild should be much faster)
time docker build -f infrastructure/docker/dockerfiles/Dockerfile.backend -t test-backend:cached ../../../
# Expected: <30 seconds for cached build
```

**Test 9: Production Readiness Checklist**
```bash
# Create comprehensive test script
cat > infrastructure/docker/test-production-readiness.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Testing Docker Production Readiness..."

# Test 1: Image sizes
echo "✓ Checking image sizes..."
docker images | grep -E "backend|dashboard|celery|nginx"

# Test 2: Security
echo "✓ Checking non-root users..."
docker compose ps -q | xargs -I {} docker inspect {} --format='{{.Config.User}}' | grep -qv "^$" && echo "  ✓ Non-root users configured"

# Test 3: Health checks
echo "✓ Checking health status..."
docker compose ps | grep -q "healthy" && echo "  ✓ Services are healthy"

# Test 4: Resource limits
echo "✓ Checking resource limits..."
docker compose ps -q | xargs -I {} docker inspect {} --format='CPU: {{.HostConfig.CpuQuota}} Memory: {{.HostConfig.Memory}}' | grep -qv "CPU: 0" && echo "  ✓ Resource limits set"

# Test 5: Networks
echo "✓ Checking network isolation..."
docker network ls | grep -q "toolboxai" && echo "  ✓ Custom networks created"

echo "🎉 All tests passed!"
EOF

chmod +x infrastructure/docker/test-production-readiness.sh
./infrastructure/docker/test-production-readiness.sh
```

**Test 10: Integration Testing**
```bash
# Full stack integration test
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for all services
sleep 30

# Test backend API
curl -f http://localhost:8009/api/v1/health | jq .

# Test authentication flow
TOKEN=$(curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | jq -r .access_token)

# Test authenticated endpoint
curl -f http://localhost:8009/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

echo "✓ All integration tests passed"
```

**Success Criteria - ALL MUST PASS:**
- [ ] All Docker images build without errors
- [ ] All image sizes meet targets (backend <200MB, dashboard <100MB)
- [ ] All containers run as non-root users (UID 1001-1004)
- [ ] All services pass health checks
- [ ] All resource limits configured
- [ ] Network isolation working
- [ ] No secrets exposed in images or logs
- [ ] Build times < 5 minutes per image
- [ ] Monitoring stack operational
- [ ] Integration tests pass

**If ANY test fails, DO NOT PROCEED to Phase 4. Fix issues first.**

### Phase 4: Kubernetes Deployment (Priority: HIGH)

**Files to Create:**
- [ ] `infrastructure/k8s/backend-deployment.yaml`
- [ ] `infrastructure/k8s/backend-service.yaml`
- [ ] `infrastructure/k8s/backend-ingress.yaml`
- [ ] `infrastructure/k8s/dashboard-deployment.yaml`
- [ ] `infrastructure/k8s/dashboard-service.yaml`
- [ ] `infrastructure/k8s/celery-deployment.yaml`
- [ ] `infrastructure/k8s/redis-statefulset.yaml`
- [ ] `infrastructure/k8s/postgres-statefulset.yaml`
- [ ] `infrastructure/k8s/configmap.yaml`
- [ ] `infrastructure/k8s/secrets.yaml`
- [ ] `infrastructure/k8s/namespace.yaml`
- [ ] `infrastructure/k8s/network-policy.yaml`

**Kubernetes Features**:
- [ ] Deployments for stateless services
- [ ] StatefulSets for databases
- [ ] Services for internal communication
- [ ] Ingress for external access
- [ ] ConfigMaps for configuration
- [ ] Secrets for sensitive data
- [ ] PersistentVolumes for data
- [ ] HorizontalPodAutoscaler for scaling
- [ ] NetworkPolicies for security
- [ ] ResourceQuotas for limits

### Phase 4: CI/CD Integration (Priority: HIGH)

**Files to Create:**
- [ ] `.github/workflows/docker-build.yml` - Build and push images
- [ ] `.github/workflows/docker-scan.yml` - Security scanning
- [ ] `.github/workflows/k8s-deploy.yml` - Kubernetes deployment
- [ ] `scripts/docker/build-all.sh` - Build all images
- [ ] `scripts/docker/push-all.sh` - Push to registry
- [ ] `scripts/docker/scan-all.sh` - Scan all images

**CI/CD Tasks**:
- [ ] Build Docker images on PR
- [ ] Run security scans (Trivy/Snyk)
- [ ] Push images to registry on merge
- [ ] Deploy to staging automatically
- [ ] Manual approval for production
- [ ] Rollback capability
- [ ] Image versioning strategy
- [ ] Build cache optimization

### Phase 5: Security Hardening (Priority: CRITICAL)

**Security Tasks**:
- [ ] Scan images for vulnerabilities (Trivy)
- [ ] Implement read-only root filesystems
- [ ] Drop all unnecessary capabilities
- [ ] Use non-root users (already implemented)
- [ ] Add security contexts
- [ ] Implement network policies
- [ ] Add secrets scanning in CI
- [ ] Regular base image updates

**Files to Create**:
- [ ] `infrastructure/security/trivy-config.yaml` - Vulnerability scanning
- [ ] `infrastructure/security/falco-rules.yaml` - Runtime security
- [ ] `.github/workflows/security-scan.yml` - Automated security scans

**Security Checks**:
- [ ] No secrets in images
- [ ] No latest tags in production
- [ ] All images signed
- [ ] Vulnerability scans passing
- [ ] Container runtime security enabled
- [ ] Network policies enforced

### Phase 6: Performance Optimization (Priority: MEDIUM)

**Tasks**:
- [ ] Optimize Dockerfile layer caching
- [ ] Implement build cache with BuildKit
- [ ] Use Docker BuildX for multi-platform
- [ ] Optimize image startup time
- [ ] Reduce image build time
- [ ] Implement parallel builds
- [ ] Optimize container resource usage

**Build Performance Targets**:
- Backend image build: < 2 minutes
- Dashboard image build: < 3 minutes
- Full stack build: < 5 minutes
- Image pull time: < 30 seconds

### Phase 7: Monitoring & Observability (Priority: HIGH)

**Files to Create**:
- [ ] `infrastructure/monitoring/prometheus/prometheus.yml`
- [ ] `infrastructure/monitoring/prometheus/alerts.yml`
- [ ] `infrastructure/monitoring/grafana/dashboards/docker.json`
- [ ] `infrastructure/monitoring/grafana/dashboards/kubernetes.json`
- [ ] `infrastructure/monitoring/loki/loki-config.yaml`
- [ ] `infrastructure/monitoring/jaeger/jaeger-config.yaml`

**Monitoring Stack Setup**:
- [ ] Prometheus for metrics collection
- [ ] Grafana dashboards for visualization
- [ ] Loki for log aggregation
- [ ] Jaeger for distributed tracing
- [ ] cAdvisor for container metrics
- [ ] Node Exporter for host metrics
- [ ] AlertManager for alerting

**Metrics to Track**:
- [ ] Container CPU usage
- [ ] Container memory usage
- [ ] Container network I/O
- [ ] Container disk I/O
- [ ] Application metrics
- [ ] Request latency
- [ ] Error rates
- [ ] Throughput

### Phase 8: Logging & Log Aggregation (Priority: MEDIUM)

**Tasks**:
- [ ] Configure Docker logging drivers
- [ ] Set up Loki for log aggregation
- [ ] Add structured logging to applications
- [ ] Implement log rotation
- [ ] Add log retention policies
- [ ] Create log queries and alerts
- [ ] Add log correlation IDs

**Log Files to Create**:
- [ ] `infrastructure/logging/fluentd/fluent.conf` - Log collection
- [ ] `infrastructure/logging/loki/loki-config.yaml` - Log storage
- [ ] `infrastructure/logging/promtail/promtail-config.yaml` - Log shipping

### Phase 9: Backup & Disaster Recovery (Priority: HIGH)

**Tasks**:
- [ ] Implement volume backup strategy
- [ ] Create database backup containers
- [ ] Add automated backup scheduling
- [ ] Implement backup verification
- [ ] Create disaster recovery procedures
- [ ] Test backup restoration
- [ ] Add cross-region replication

**Files to Create**:
- [ ] `infrastructure/backup/backup-cronjob.yaml` - K8s backup job
- [ ] `scripts/docker/backup-volumes.sh` - Volume backup script
- [ ] `scripts/docker/restore-volumes.sh` - Volume restore script
- [ ] `docs/docker/DISASTER_RECOVERY.md` - DR procedures

### Phase 10: Documentation & Operations (Priority: MEDIUM)

**Files to Create**:
- [ ] `docs/docker/PRODUCTION_DEPLOYMENT.md` - Production guide
- [ ] `docs/docker/KUBERNETES_GUIDE.md` - K8s deployment guide
- [ ] `docs/docker/MONITORING_GUIDE.md` - Monitoring setup
- [ ] `docs/docker/TROUBLESHOOTING.md` - Common issues
- [ ] `docs/docker/SCALING_GUIDE.md` - Scaling strategies
- [ ] `docs/docker/SECURITY_GUIDE.md` - Security best practices
- [ ] `docs/docker/ROLLBACK_PROCEDURES.md` - Rollback guide

**Operations Runbooks**:
- [ ] Create deployment runbook
- [ ] Create scaling runbook
- [ ] Create rollback runbook
- [ ] Create incident response runbook
- [ ] Create backup/restore runbook

## File Locations

### Docker Files
- **Dockerfiles**: `infrastructure/docker/dockerfiles/`
- **Compose Files**: `infrastructure/docker/compose/`
- **Scripts**: `infrastructure/docker/scripts/`

### Kubernetes Files
- **Manifests**: `infrastructure/k8s/`
- **Helm Charts**: `infrastructure/helm/` (if using Helm)

### Monitoring
- **Prometheus**: `infrastructure/monitoring/prometheus/`
- **Grafana**: `infrastructure/monitoring/grafana/`
- **Loki**: `infrastructure/monitoring/loki/`
- **Jaeger**: `infrastructure/monitoring/jaeger/`

### Documentation
- **Guides**: `docs/docker/`
- **Runbooks**: `docs/operations/runbooks/`

## Technology Stack (2025)

### Container Runtime
```bash
docker: ">=25.0"
docker-compose: ">=2.24"
buildkit: enabled
```

### Orchestration
```bash
kubernetes: ">=1.29"
helm: ">=3.14"  # Optional
kubectl: ">=1.29"
```

### Monitoring Stack
```yaml
prometheus: "v2.50+"
grafana: "v10.3+"
loki: "v2.9+"
jaeger: "v1.54+"
cadvisor: "v0.48+"
```

## Modern Docker Patterns (2025)

### Multi-Stage Build Example
```dockerfile
# ✅ CORRECT - Multi-stage build for minimal image
# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-alpine

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -D -u 1001 -G appgroup appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set working directory
WORKDIR /app

# Copy application
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment Example
```yaml
# ✅ CORRECT - Production-ready K8s deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: production
  labels:
    app: backend-api
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
        version: v1.0.0
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: backend
        image: registry.example.com/backend-api:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Commands

### Docker Commands
```bash
# Build with BuildKit
DOCKER_BUILDKIT=1 docker build -t backend-api:latest \
  --target production \
  --cache-from backend-api:cache \
  -f infrastructure/docker/dockerfiles/Dockerfile.backend .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 \
  -t backend-api:latest .

# Push to registry
docker tag backend-api:latest registry.example.com/backend-api:v1.0.0
docker push registry.example.com/backend-api:v1.0.0

# Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image backend-api:latest
```

### Kubernetes Commands
```bash
# Apply manifests
kubectl apply -f infrastructure/k8s/

# Deploy with Helm
helm upgrade --install toolboxai ./infrastructure/helm/toolboxai \
  --namespace production --create-namespace

# Check deployment
kubectl rollout status deployment/backend-api -n production

# Scale deployment
kubectl scale deployment/backend-api --replicas=5 -n production

# View logs
kubectl logs -f deployment/backend-api -n production

# Rollback deployment
kubectl rollout undo deployment/backend-api -n production
```

### Monitoring Commands
```bash
# Port forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Port forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# View metrics
curl http://localhost:9090/api/v1/query?query=up
```

## Performance Targets

- **Image Build Time**: < 5 minutes for all images
- **Image Size**: < 500MB total for all images
- **Container Startup**: < 10 seconds
- **Resource Usage**: < 1GB RAM per container
- **CPU Usage**: < 50% under normal load
- **Deploy Time**: < 2 minutes for rolling update

## Success Metrics

- ✅ All Docker images optimized (< target sizes)
- ✅ Multi-stage builds implemented
- ✅ Kubernetes configs created and tested
- ✅ CI/CD pipeline functional
- ✅ Security scans passing (zero critical vulns)
- ✅ Monitoring stack deployed and operational
- ✅ Logging aggregation working
- ✅ Auto-scaling configured
- ✅ Health checks passing
- ✅ Backup/restore tested
- ✅ Documentation complete
- ✅ Production deployment successful

---

**REMEMBER**: Docker is your deployment foundation. Optimize it well, secure it properly, and monitor it closely!
