# Deployment Validation Checklist

**Branch:** feature/infrastructure-complete
**Version:** 1.0.0
**Date:** 2025-10-02

---

## Pre-Deployment Validation

### Code Quality & Testing

- [ ] **All tests passing**
  ```bash
  # Run Phase 3 comprehensive tests
  pytest tests/infrastructure/test_docker_phase3_comprehensive.py -v

  # Run all integration tests
  pytest tests/integration/ -v --tb=short

  # Run Docker services integration
  pytest tests/integration/test_docker_services_integration.py -v
  ```

- [ ] **Security scans completed**
  ```bash
  # Scan Docker images for vulnerabilities
  docker scan toolboxai/backend:latest
  docker scan toolboxai/dashboard:latest

  # Check for secrets in code
  git secrets --scan

  # Run security audit
  npm audit --production
  ```

- [ ] **Image sizes validated**
  ```bash
  # Check image sizes
  docker images toolboxai/* --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

  # Should show:
  # toolboxai/backend    latest    ~180MB  (target <200MB) ✓
  # toolboxai/dashboard  latest    ~85MB   (target <100MB) ✓
  ```

- [ ] **Kubernetes manifests validated**
  ```bash
  # Run validation script
  ./scripts/validate-kubernetes-manifests.sh

  # Dry-run apply
  kubectl apply --dry-run=client -k infrastructure/kubernetes/overlays/staging/
  ```

### Configuration Review

- [ ] **Environment variables reviewed**
  - All required variables defined
  - No hardcoded secrets
  - Correct values for target environment
  - Files: `.env.example`, `docker-compose.yml`, Kubernetes ConfigMaps

- [ ] **Secrets configuration validated**
  ```bash
  # Verify all secrets are external
  grep -r "external: true" infrastructure/docker/compose/docker-compose.yml

  # Check Kubernetes secrets
  kubectl get secrets -n toolboxai
  ```

- [ ] **Resource limits configured**
  - CPU limits set for all services
  - Memory limits set for all services
  - Storage quotas defined
  - Resource reservations configured

- [ ] **Network policies reviewed**
  - Internal networks isolated
  - Firewall rules configured
  - Network policies applied
  - Ingress/egress rules validated

### Monitoring & Alerting

- [ ] **Prometheus configured**
  ```bash
  # Validate Prometheus config
  promtool check config infrastructure/docker/config/prometheus/prometheus.yml

  # Check alert rules
  promtool check rules infrastructure/docker/config/prometheus/alert_rules.yml
  ```

- [ ] **Grafana dashboards imported**
  - All 5+ dashboards present
  - Datasources configured
  - Alert channels configured
  - Notification templates set

- [ ] **Loki log aggregation ready**
  ```bash
  # Check Loki config
  cat infrastructure/docker/config/loki/loki-config.yml

  # Validate Promtail config
  cat infrastructure/docker/config/promtail/promtail-config.yml
  ```

- [ ] **Jaeger tracing configured**
  - Jaeger agent running
  - Application instrumented
  - Trace collection working
  - UI accessible

### Backup & Recovery

- [ ] **Backup system configured**
  - Backup coordinator service running
  - Backup schedule configured (hourly/daily)
  - Retention policies set (30 days)
  - S3/Cloud storage configured
  - Encryption enabled

- [ ] **Recovery procedures tested**
  ```bash
  # Test backup integrity
  ./scripts/verify-backup.sh --latest

  # Test recovery (dry-run)
  ./scripts/test-recovery.sh --dry-run

  # Verify backup locations
  ls -lh /backup/postgres/
  ```

- [ ] **Disaster recovery runbook reviewed**
  - Team familiar with procedures
  - Emergency contacts updated
  - Communication channels tested
  - Recovery time objectives documented

---

## Staging Deployment

### Pre-Deployment

- [ ] **Staging environment ready**
  ```bash
  # Check cluster status
  kubectl cluster-info
  kubectl get nodes
  kubectl get namespaces
  ```

- [ ] **Database migrations prepared**
  ```bash
  # Check pending migrations
  alembic current
  alembic history

  # Test migration (dry-run)
  alembic upgrade head --sql > migration.sql
  ```

- [ ] **Load balancer configured**
  - Health check endpoints configured
  - SSL/TLS certificates installed
  - DNS records updated
  - Rate limiting configured

### Deployment Execution

- [ ] **Deploy infrastructure services**
  ```bash
  # Deploy to staging
  kubectl apply -k infrastructure/kubernetes/overlays/staging/

  # Wait for rollout
  kubectl rollout status deployment/backend -n toolboxai-staging
  kubectl rollout status deployment/dashboard -n toolboxai-staging
  ```

- [ ] **Verify service health**
  ```bash
  # Check all pods
  kubectl get pods -n toolboxai-staging

  # Check services
  kubectl get svc -n toolboxai-staging

  # Check ingress
  kubectl get ingress -n toolboxai-staging
  ```

- [ ] **Run smoke tests**
  ```bash
  # Run automated smoke tests
  ./tests/smoke-tests.sh --staging

  # Manual checks
  curl -f https://staging.toolboxai.com/health
  curl -f https://staging.toolboxai.com/api/v1/health
  ```

### Post-Deployment Validation

- [ ] **Application functionality verified**
  - [ ] User can login
  - [ ] Dashboard loads correctly
  - [ ] API endpoints responding
  - [ ] Database queries working
  - [ ] Cache functioning
  - [ ] Background jobs processing

- [ ] **Performance validated**
  ```bash
  # Check response times
  curl -w "@curl-format.txt" -o /dev/null -s https://staging.toolboxai.com/

  # Run load test
  ./tests/load-test.sh --staging --duration 60s
  ```

- [ ] **Monitoring validated**
  - [ ] Metrics appearing in Prometheus
  - [ ] Logs flowing to Loki
  - [ ] Traces visible in Jaeger
  - [ ] Grafana dashboards populating
  - [ ] Alerts configured and firing (test)

- [ ] **Security validated**
  ```bash
  # Run security scan
  ./scripts/security-scan.sh --staging

  # Check for exposed secrets
  ./scripts/check-secrets.sh --staging

  # Verify HTTPS
  curl -I https://staging.toolboxai.com/
  ```

---

## Production Deployment

### Pre-Production Checklist

- [ ] **Staging validation complete**
  - All staging tests passed
  - Performance acceptable
  - No critical issues
  - Stakeholder sign-off

- [ ] **Production environment ready**
  - [ ] Production cluster accessible
  - [ ] Secrets configured
  - [ ] DNS updated
  - [ ] SSL certificates valid
  - [ ] Backup system operational

- [ ] **Rollback plan prepared**
  - Previous version tagged
  - Rollback procedure documented
  - Database rollback tested
  - Team briefed on rollback

- [ ] **Communication plan**
  - [ ] Status page updated
  - [ ] Users notified (if maintenance)
  - [ ] Team on standby
  - [ ] Incident channel active

### Production Deployment

- [ ] **Create production backup**
  ```bash
  # Backup current production state
  ./scripts/backup-production.sh --pre-deployment

  # Verify backup
  ./scripts/verify-backup.sh --latest
  ```

- [ ] **Deploy to production**
  ```bash
  # Using ArgoCD (recommended)
  argocd app sync toolboxai-backend --prune
  argocd app sync toolboxai-dashboard --prune

  # Or kubectl
  kubectl apply -k infrastructure/kubernetes/overlays/production/

  # Monitor rollout
  kubectl rollout status deployment/backend -n toolboxai
  kubectl rollout status deployment/dashboard -n toolboxai
  ```

- [ ] **Verify deployment**
  ```bash
  # Check pod status
  kubectl get pods -n toolboxai -w

  # Check service health
  curl -f https://app.toolboxai.com/health

  # Check logs for errors
  kubectl logs -f deployment/backend -n toolboxai --tail=100
  ```

### Post-Production Validation

- [ ] **Critical path testing**
  - [ ] User authentication working
  - [ ] Core features functional
  - [ ] Payment processing (if applicable)
  - [ ] Data persistence verified
  - [ ] API endpoints responding

- [ ] **Performance monitoring**
  - [ ] Response times normal
  - [ ] Error rates low
  - [ ] CPU/memory usage acceptable
  - [ ] Database performance good
  - [ ] Cache hit rate healthy

- [ ] **24-hour monitoring**
  - [ ] Monitor dashboards
  - [ ] Check error logs
  - [ ] Review metrics
  - [ ] Watch for alerts
  - [ ] Track user feedback

---

## Rollback Procedures

### When to Rollback

Immediate rollback if:
- [ ] Critical functionality broken
- [ ] Security vulnerability introduced
- [ ] Data corruption detected
- [ ] Performance degradation >50%
- [ ] Error rate >5%

### Rollback Steps

```bash
# 1. Stop new deployments
argocd app set toolboxai-backend --sync-policy none

# 2. Rollback to previous version
kubectl rollout undo deployment/backend -n toolboxai
kubectl rollout undo deployment/dashboard -n toolboxai

# 3. Verify rollback
kubectl rollout status deployment/backend -n toolboxai
kubectl rollout status deployment/dashboard -n toolboxai

# 4. Check health
curl -f https://app.toolboxai.com/health

# 5. If database migration, restore backup
./scripts/restore-database.sh --backup-id [PREVIOUS_BACKUP]

# 6. Monitor for 30 minutes
kubectl logs -f deployment/backend -n toolboxai
```

---

## Post-Deployment Tasks

### Immediate (Within 1 hour)

- [ ] **Update status page**
  - Deployment complete notification
  - Any known issues
  - Next maintenance window

- [ ] **Monitor metrics**
  - Check Grafana dashboards
  - Review error logs
  - Verify alert channels

- [ ] **Verify backups**
  - Post-deployment backup completed
  - Backup integrity verified
  - Retention policies applied

### Short-term (Within 24 hours)

- [ ] **Performance review**
  - Compare baseline metrics
  - Identify any degradation
  - Optimize if needed

- [ ] **User feedback**
  - Monitor support tickets
  - Check user reports
  - Address critical issues

- [ ] **Documentation update**
  - Update deployment log
  - Document any issues
  - Update runbooks if needed

### Long-term (Within 1 week)

- [ ] **Post-mortem meeting**
  - Review deployment process
  - Identify improvements
  - Update procedures

- [ ] **Metrics analysis**
  - Performance trends
  - Resource utilization
  - Cost analysis

- [ ] **Team retrospective**
  - What went well
  - What can improve
  - Action items

---

## Validation Scripts

### Quick Health Check

```bash
#!/bin/bash
# Quick health check script

echo "Checking service health..."

services=(
  "https://app.toolboxai.com/health"
  "https://app.toolboxai.com/api/v1/health"
  "http://localhost:9090/-/healthy"  # Prometheus
  "http://localhost:3000/api/health"  # Grafana
)

for service in "${services[@]}"; do
  if curl -f -s "$service" > /dev/null; then
    echo "✓ $service"
  else
    echo "✗ $service"
  fi
done
```

### Performance Benchmark

```bash
#!/bin/bash
# Performance benchmark script

echo "Running performance benchmark..."

# API response time
time curl -s https://app.toolboxai.com/api/v1/health > /dev/null

# Load test
ab -n 1000 -c 10 https://app.toolboxai.com/

# Database query performance
docker compose exec postgres psql -c "
  SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"
```

---

## Sign-off

### Staging Deployment

- [ ] **Technical Lead:** _________________ Date: _______
- [ ] **DevOps Lead:** _________________ Date: _______
- [ ] **QA Lead:** _________________ Date: _______

### Production Deployment

- [ ] **Technical Lead:** _________________ Date: _______
- [ ] **DevOps Lead:** _________________ Date: _______
- [ ] **Product Manager:** _________________ Date: _______
- [ ] **CTO/Engineering Director:** _________________ Date: _______

---

## Appendix: Common Issues & Solutions

### Issue: Pods not starting

**Symptoms:** Pods stuck in `Pending` or `CrashLoopBackOff`

**Solutions:**
```bash
# Check pod events
kubectl describe pod [POD_NAME] -n toolboxai

# Check logs
kubectl logs [POD_NAME] -n toolboxai --previous

# Common fixes:
# - Check resource limits
# - Verify secrets exist
# - Check image pull policy
# - Verify network policies
```

### Issue: Service not accessible

**Symptoms:** Cannot reach service via LoadBalancer/Ingress

**Solutions:**
```bash
# Check service
kubectl get svc -n toolboxai

# Check ingress
kubectl describe ingress -n toolboxai

# Check endpoints
kubectl get endpoints -n toolboxai

# Test from within cluster
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
```

### Issue: Database connection failures

**Symptoms:** Backend cannot connect to database

**Solutions:**
```bash
# Check database pod
kubectl get pods -l app=postgres -n toolboxai

# Check database logs
kubectl logs -l app=postgres -n toolboxai

# Test connection
kubectl exec -it deployment/backend -n toolboxai -- \
  psql -h postgres -U toolboxai -d toolboxai -c "SELECT 1;"
```

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-02
**Next Review:** 2025-11-02
