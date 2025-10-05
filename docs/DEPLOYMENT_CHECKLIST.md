# ToolBoxAI Production Deployment Checklist

**Version**: 2.0.0
**Last Updated**: October 2, 2025
**Environment**: Production

---

## Pre-Deployment Checklist

### 1. Code & Repository ✓

- [ ] All code merged to `main` branch
- [ ] Version tag created (e.g., `v2.0.0`)
- [ ] CHANGELOG.md updated
- [ ] All tests passing in CI/CD
- [ ] Code review completed
- [ ] Security scan passed (Trivy)
- [ ] No HIGH/CRITICAL vulnerabilities

### 2. Docker Images ✓

- [ ] All images built successfully
- [ ] Image sizes verified:
  - [ ] Backend < 200MB
  - [ ] Dashboard < 100MB
  - [ ] Celery < 200MB
  - [ ] Nginx < 50MB
- [ ] Images tagged with version
- [ ] Images pushed to registry
- [ ] Images scanned for vulnerabilities
- [ ] Non-root users configured (UIDs 1001-1007)

### 3. Configuration ⚙️

- [ ] Environment variables configured
- [ ] Secrets created and stored securely
- [ ] Database connection strings verified
- [ ] API keys validated
- [ ] Redis configuration reviewed
- [ ] Resource limits set
- [ ] Logging configuration verified
- [ ] Monitoring endpoints configured

### 4. Database 🗄️

- [ ] Database migrations tested
- [ ] Backup taken before deployment
- [ ] Database credentials rotated
- [ ] Connection pool size configured
- [ ] Indexes optimized
- [ ] Query performance tested
- [ ] Replication verified (if applicable)

### 5. Infrastructure 🏗️

- [ ] Kubernetes cluster ready
- [ ] Namespaces created
- [ ] Storage classes configured
- [ ] Persistent volumes provisioned
- [ ] Network policies applied
- [ ] Ingress controller configured
- [ ] TLS certificates installed
- [ ] DNS records updated

### 6. Security 🔐

- [ ] All secrets managed via Kubernetes secrets
- [ ] TLS/HTTPS enforced
- [ ] Rate limiting configured
- [ ] CORS policies set
- [ ] Security headers configured
- [ ] Network policies applied
- [ ] Pod security policies enabled
- [ ] Service accounts configured
- [ ] RBAC roles defined

### 7. Monitoring & Logging 📊

- [ ] Prometheus deployed
- [ ] Grafana dashboards configured
- [ ] Alerting rules set up
- [ ] Loki deployed for logs
- [ ] Alert channels configured (Slack, email, etc.)
- [ ] SLO/SLI metrics defined
- [ ] On-call rotation set up

### 8. Backup & Recovery 💾

- [ ] Backup strategy documented
- [ ] Automated backup scheduled
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] RTO/RPO defined
- [ ] Backup retention policy set

---

## Deployment Steps

### Phase 1: Pre-Deployment (T-1 day)

1. **Notify stakeholders**
   ```
   Subject: Production Deployment - ToolBoxAI v2.0.0
   Date: [DATE]
   Downtime: Estimated 30 minutes
   ```

2. **Create backup**
   ```bash
   ./scripts/backup-docker-volumes.sh
   # Or for K8s:
   ./scripts/backup-k8s-volumes.sh
   ```

3. **Run smoke tests**
   ```bash
   ./scripts/test-production-readiness.sh
   ```

### Phase 2: Deployment (T-0)

#### Docker Compose Deployment

```bash
# 1. Pull latest images
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull

# 2. Stop services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 3. Run database migrations
docker compose run --rm backend python -m alembic upgrade head

# 4. Start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Verify health
docker compose ps
curl http://localhost:8009/health
```

#### Kubernetes Deployment

```bash
# 1. Update image tags
kubectl set image deployment/backend-api \
  backend=ghcr.io/toolboxai/backend:v2.0.0 \
  -n toolboxai-prod

kubectl set image deployment/dashboard \
  dashboard=ghcr.io/toolboxai/dashboard:v2.0.0 \
  -n toolboxai-prod

# 2. Watch rollout
kubectl rollout status deployment/backend-api -n toolboxai-prod
kubectl rollout status deployment/dashboard -n toolboxai-prod

# 3. Verify pods
kubectl get pods -n toolboxai-prod

# 4. Check health
kubectl port-forward svc/backend 8009:8009 -n toolboxai-prod
curl http://localhost:8009/health
```

### Phase 3: Verification (T+15 min)

- [ ] All containers/pods running
- [ ] Health checks passing
- [ ] Database connections successful
- [ ] Redis connections successful
- [ ] API endpoints responding
- [ ] Dashboard accessible
- [ ] Authentication working
- [ ] Background jobs processing
- [ ] Metrics being collected
- [ ] Logs being aggregated

### Phase 4: Smoke Testing (T+30 min)

```bash
# Run automated smoke tests
./scripts/smoke-test-production.sh

# Manual checks:
# 1. User login
# 2. Create/read/update/delete operations
# 3. API rate limiting
# 4. File uploads
# 5. Background jobs
# 6. Real-time features
```

### Phase 5: Monitoring (T+1 hour)

- [ ] Check error rates (< 1%)
- [ ] Check response times (p95 < 1s)
- [ ] Check CPU usage (< 70%)
- [ ] Check memory usage (< 80%)
- [ ] Check database connections
- [ ] Check Redis usage
- [ ] Review logs for errors
- [ ] Verify metrics in Grafana

---

## Post-Deployment

### Immediate (T+2 hours)

- [ ] Monitor error rates
- [ ] Monitor performance metrics
- [ ] Check for anomalies
- [ ] Verify all integrations
- [ ] Test critical user flows

### Short-term (T+24 hours)

- [ ] Review logs for patterns
- [ ] Analyze performance trends
- [ ] Check resource utilization
- [ ] Verify backup completion
- [ ] Update documentation

### Long-term (T+1 week)

- [ ] Conduct retrospective
- [ ] Document lessons learned
- [ ] Update runbooks
- [ ] Optimize resource allocation
- [ ] Plan next deployment

---

## Rollback Procedure

### If Issues Detected

1. **Assess severity**
   - Critical: Immediate rollback
   - High: Rollback within 15 minutes
   - Medium: Apply hotfix or rollback

2. **Execute rollback**

   **Docker Compose:**
   ```bash
   docker compose down
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3
   ```

   **Kubernetes:**
   ```bash
   kubectl rollout undo deployment/backend-api -n toolboxai-prod
   kubectl rollout undo deployment/dashboard -n toolboxai-prod
   ```

3. **Restore database** (if needed)
   ```bash
   ./scripts/restore-docker-volumes.sh -t [TIMESTAMP]
   ```

4. **Verify rollback**
   - [ ] Services running
   - [ ] Health checks passing
   - [ ] Functionality restored
   - [ ] Performance normal

5. **Communicate**
   - Notify stakeholders
   - Document root cause
   - Create post-mortem

---

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| DevOps Lead | [NAME] | [EMAIL/PHONE] | 24/7 |
| Backend Lead | [NAME] | [EMAIL/PHONE] | 24/7 |
| Frontend Lead | [NAME] | [EMAIL/PHONE] | Business hours |
| DBA | [NAME] | [EMAIL/PHONE] | On-call |
| Security | [NAME] | [EMAIL/PHONE] | 24/7 |

---

## Success Criteria

Deployment is considered successful when:

- ✅ All services healthy for 2+ hours
- ✅ Error rate < 1%
- ✅ P95 response time < 1s
- ✅ CPU usage < 70%
- ✅ Memory usage < 80%
- ✅ Database connections stable
- ✅ No critical alerts fired
- ✅ User-facing features functional
- ✅ Background jobs processing
- ✅ Monitoring and alerting operational

---

## Documentation Updates

After successful deployment:

- [ ] Update deployment docs
- [ ] Update API documentation
- [ ] Update architecture diagrams
- [ ] Update runbooks
- [ ] Create release notes
- [ ] Update knowledge base

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Deployer | | | |
| Reviewer | | | |
| Approver | | | |

---

**Deployment Status**: ⬜ Not Started / 🔄 In Progress / ✅ Complete / ❌ Failed

**Notes**:
```
[Add any additional notes, observations, or issues here]
```

---

_This checklist should be completed for every production deployment._
