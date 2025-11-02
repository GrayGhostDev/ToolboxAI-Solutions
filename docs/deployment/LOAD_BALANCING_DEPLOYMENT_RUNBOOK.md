# Load Balancing Infrastructure Deployment Runbook

## 🎯 Overview

This runbook provides step-by-step instructions for deploying the enhanced load balancing infrastructure to production. The deployment is designed for zero-downtime with automatic rollback capabilities.

## 📋 Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] PostgreSQL primary database operational
- [ ] At least 2 PostgreSQL read replicas configured
- [ ] Redis cluster (minimum 3 nodes) deployed
- [ ] Kubernetes cluster with HPA enabled
- [ ] Prometheus & Grafana monitoring stack
- [ ] PgBouncer installed on database hosts
- [ ] CDN account configured (CloudFlare/CloudFront)
- [ ] DNS management access

### Configuration Requirements
- [ ] Database connection strings for all replicas
- [ ] Redis connection strings
- [ ] CDN API keys and zones configured
- [ ] Monitoring webhooks configured
- [ ] Backup procedures tested

### Team Readiness
- [ ] Deployment team identified
- [ ] Rollback procedures reviewed
- [ ] Communication channels established
- [ ] Maintenance window scheduled

## 🚀 Deployment Phases

### Phase 1: Database Layer (Risk: Low, Impact: High)

#### 1.1 Deploy Read Replica Router

```bash
# Test replica connectivity
./scripts/test-replica-connectivity.sh

# Deploy replica router configuration
kubectl apply -f infrastructure/kubernetes/replica-router-configmap.yaml

# Update application to use replica router
kubectl set env deployment/fastapi-main \
  ENABLE_REPLICA_ROUTING=true \
  REPLICA_URLS="${REPLICA_URLS}"

# Verify routing metrics
curl -s http://localhost:8009/metrics/replica-routing | jq .
```

**Validation:**
- Primary database load should decrease by 40-60%
- No increase in error rates
- P95 latency should improve

**Rollback:**
```bash
kubectl set env deployment/fastapi-main ENABLE_REPLICA_ROUTING=false
```

#### 1.2 Deploy PgBouncer

```bash
# Deploy PgBouncer
cd infrastructure/pgbouncer
./deploy-pgbouncer.sh deploy

# Test connectivity
./deploy-pgbouncer.sh test

# Monitor stats
./deploy-pgbouncer.sh monitor
```

**Validation:**
- Connection pool utilization < 80%
- No connection timeouts
- Reduced connection overhead

**Rollback:**
```bash
./deploy-pgbouncer.sh rollback
```

### Phase 2: Application Resilience (Risk: Medium, Impact: High)

#### 2.1 Enable Circuit Breakers

```bash
# Deploy circuit breaker configuration
kubectl apply -f infrastructure/kubernetes/circuit-breaker-config.yaml

# Enable resilience middleware
kubectl set env deployment/fastapi-main \
  ENABLE_CIRCUIT_BREAKER=true \
  CB_FAILURE_THRESHOLD=10 \
  CB_RESET_TIMEOUT=30

# Monitor circuit states
watch -n 5 'curl -s http://localhost:8009/health/circuit-breakers | jq .'
```

**Validation:**
- Circuit breakers in CLOSED state for healthy services
- Automatic recovery from transient failures
- No cascading failures

#### 2.2 Enable Rate Limiting

```bash
# Deploy rate limit rules
kubectl apply -f infrastructure/kubernetes/rate-limit-rules.yaml

# Enable distributed rate limiting
kubectl set env deployment/fastapi-main \
  ENABLE_RATE_LIMITING=true \
  RATE_LIMIT_REDIS_URL="${REDIS_URL}" \
  DEFAULT_RATE_LIMIT=1000

# Test rate limiting
./scripts/test-rate-limiting.sh
```

**Validation:**
- Rate limit headers present in responses
- Fair distribution across users
- No false positives for legitimate traffic

### Phase 3: Edge Caching (Risk: Low, Impact: Very High)

#### 3.1 Deploy Edge Cache

```bash
# Initialize edge cache
kubectl apply -f infrastructure/kubernetes/edge-cache-deployment.yaml

# Configure CDN integration
./scripts/configure-cdn.sh \
  --provider cloudflare \
  --zone-id "${CF_ZONE_ID}" \
  --api-key "${CF_API_KEY}"

# Enable caching middleware
kubectl set env deployment/fastapi-main \
  ENABLE_EDGE_CACHE=true \
  CACHE_REDIS_URL="${REDIS_URL}" \
  CDN_PROVIDER=cloudflare
```

**Validation:**
- Cache hit rate > 60% after warm-up
- X-Cache headers present
- CDN metrics showing traffic distribution

#### 3.2 Cache Warming

```bash
# Warm critical paths
./scripts/cache-warmer.py \
  --endpoints /api/v1/content/popular \
  --endpoints /api/v1/static/* \
  --concurrent 10

# Verify cache population
redis-cli --scan --pattern "cache:*" | wc -l
```

### Phase 4: WebSocket Clustering (Risk: Medium, Impact: Medium)

#### 4.1 Deploy WebSocket Cluster

```bash
# Deploy cluster coordinator
kubectl apply -f infrastructure/kubernetes/websocket-cluster.yaml

# Scale WebSocket pods
kubectl scale deployment/websocket-handler --replicas=3

# Enable session affinity
kubectl patch service/websocket-service -p \
  '{"spec":{"sessionAffinity":"ClientIP","sessionAffinityConfig":{"clientIP":{"timeoutSeconds":3600}}}}'
```

**Validation:**
- WebSocket connections distributed across nodes
- Session persistence during reconnects
- Cross-node message delivery working

### Phase 5: Global Load Balancing (Risk: High, Impact: Very High)

#### 5.1 Configure Multi-Region Setup

```bash
# Deploy to secondary regions
./scripts/deploy-region.sh --region eu-west-1
./scripts/deploy-region.sh --region ap-south-1

# Configure global load balancer
./scripts/configure-global-lb.sh \
  --primary us-east-1 \
  --secondary eu-west-1,ap-south-1 \
  --policy geoproximity

# Update DNS for GeoDNS
./scripts/update-geodns.sh
```

**Validation:**
- Traffic routing to nearest region
- Automatic failover on region failure
- Global metrics aggregation working

### Phase 6: Enhanced Nginx (Risk: Low, Impact: High)

#### 6.1 Deploy Enhanced Nginx Configuration

```bash
# Deploy enhanced Nginx
cd infrastructure/nginx
./deploy-nginx-enhanced.sh deploy

# Test enhanced features
./deploy-nginx-enhanced.sh test

# Monitor upstream health
curl http://localhost:8081/nginx-status
```

**Validation:**
- Health checks passing for all upstreams
- Load distribution per configured algorithm
- WebSocket connections maintaining affinity

## 📊 Monitoring & Validation

### Import Dashboards

```bash
# Import Grafana dashboards
./scripts/import-dashboards.sh \
  --dashboard monitoring/grafana/dashboards/load-balancing-dashboard.json \
  --dashboard monitoring/grafana/dashboards/resilience-dashboard.json

# Configure alerts
kubectl apply -f monitoring/prometheus/alerts/load-balancing-alerts.yml
```

### Performance Baseline

```bash
# Run performance tests
cd tests/performance
python test_load_balancing_performance.py

# Generate baseline report
./scripts/generate-performance-baseline.sh > baseline-report.json
```

### Health Check Endpoints

Monitor these endpoints continuously during deployment:

- `/health/circuit-breakers` - Circuit breaker states
- `/health/rate-limits` - Rate limit status
- `/health/replica-routing` - Database routing metrics
- `/health/cache` - Cache hit rates
- `/health/websocket-cluster` - WebSocket cluster status
- `/health/global-lb` - Global load balancer metrics

## 🔥 Disaster Recovery

### Immediate Rollback Procedure

If critical issues occur, execute full rollback:

```bash
# Execute emergency rollback
./scripts/emergency-rollback.sh --confirm

# This will:
# 1. Disable all load balancing features
# 2. Route all traffic to primary database
# 3. Disable caching
# 4. Revert to single WebSocket node
# 5. Restore original Nginx configuration
```

### Component-Specific Rollback

For individual component issues:

```bash
# Rollback specific component
./scripts/rollback-component.sh --component <component-name>

# Available components:
# - replica-router
# - circuit-breaker
# - rate-limiter
# - edge-cache
# - websocket-cluster
# - global-lb
# - nginx-enhanced
```

### Data Recovery

If data inconsistency detected:

```bash
# Verify data consistency
./scripts/verify-data-consistency.sh

# If issues found, initiate recovery
./scripts/data-recovery.sh --source primary --target replicas
```

## 📈 Post-Deployment Validation

### Success Criteria

All of the following must be met to consider deployment successful:

1. **Availability**: > 99.95% over 24 hours
2. **P95 Latency**: < 200ms for API calls
3. **Cache Hit Rate**: > 60% for cacheable content
4. **Database Load**: Primary load reduced by > 50%
5. **Error Rate**: < 0.1% increase from baseline
6. **WebSocket Stability**: < 1% unexpected disconnections

### Performance Validation

```bash
# Run comprehensive validation suite
./scripts/validate-deployment.sh --comprehensive

# Generate performance comparison
./scripts/compare-performance.sh \
  --baseline baseline-report.json \
  --current post-deployment-report.json
```

### Load Testing

```bash
# Run gradual load test
./scripts/load-test.sh \
  --start-users 100 \
  --end-users 5000 \
  --ramp-time 300 \
  --duration 1800
```

## 🚨 Incident Response

### Alert Response Matrix

| Alert | Severity | Response Time | Action |
|-------|----------|--------------|--------|
| Circuit Breaker Open | High | 5 min | Check downstream service, consider manual reset |
| Rate Limit Exceeded | Medium | 15 min | Review limits, check for abuse |
| Cache Hit Rate Drop | Low | 30 min | Check invalidation patterns |
| Replica Lag High | High | 5 min | Check replication, failover if needed |
| WebSocket Imbalance | Medium | 15 min | Check session affinity, rebalance |
| Global LB Failover | Critical | Immediate | Verify region health, investigate root cause |

### Communication Plan

1. **Initial Detection**: Alert sent to #ops-alerts
2. **Acknowledgment**: On-call responds within 5 minutes
3. **Escalation**: Team lead notified if not resolved in 15 minutes
4. **Updates**: Every 30 minutes until resolved
5. **Post-Mortem**: Within 48 hours for severity High/Critical

## 📝 Deployment Log Template

```markdown
## Deployment: Load Balancing Infrastructure
**Date**: YYYY-MM-DD
**Time**: HH:MM UTC
**Team**: [Names]

### Pre-Deployment
- [ ] Checklist completed
- [ ] Backups verified
- [ ] Team briefed

### Phase 1: Database Layer
- [ ] Started: HH:MM
- [ ] Replica router deployed
- [ ] PgBouncer configured
- [ ] Validation passed
- [ ] Completed: HH:MM

### Phase 2: Application Resilience
- [ ] Started: HH:MM
- [ ] Circuit breakers enabled
- [ ] Rate limiting configured
- [ ] Validation passed
- [ ] Completed: HH:MM

### Phase 3: Edge Caching
- [ ] Started: HH:MM
- [ ] Cache layer deployed
- [ ] CDN integrated
- [ ] Cache warmed
- [ ] Validation passed
- [ ] Completed: HH:MM

### Phase 4: WebSocket Clustering
- [ ] Started: HH:MM
- [ ] Cluster deployed
- [ ] Session affinity verified
- [ ] Validation passed
- [ ] Completed: HH:MM

### Phase 5: Global Load Balancing
- [ ] Started: HH:MM
- [ ] Multi-region configured
- [ ] GeoDNS updated
- [ ] Validation passed
- [ ] Completed: HH:MM

### Phase 6: Enhanced Nginx
- [ ] Started: HH:MM
- [ ] Configuration deployed
- [ ] Health checks verified
- [ ] Validation passed
- [ ] Completed: HH:MM

### Post-Deployment
- [ ] All health checks passing
- [ ] Performance baselines met
- [ ] Monitoring dashboards operational
- [ ] Documentation updated

### Issues Encountered
[List any issues and resolutions]

### Lessons Learned
[Key takeaways for future deployments]
```

## 🔄 Regular Maintenance

### Daily Tasks
- Review circuit breaker states
- Check cache hit rates
- Monitor replica lag
- Verify WebSocket distribution

### Weekly Tasks
- Analyze performance trends
- Review rate limit violations
- Update cache warming lists
- Test failover procedures

### Monthly Tasks
- Capacity planning review
- Cost optimization analysis
- Security audit of load balancing rules
- Disaster recovery drill

## 📚 References

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Database Read Replicas Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html)
- [CDN Caching Strategies](https://www.cloudflare.com/learning/cdn/what-is-caching/)
- [WebSocket Clustering](https://socket.io/docs/v4/using-multiple-nodes/)
- [Global Load Balancing](https://cloud.google.com/load-balancing/docs/https/setting-up-global-traffic-mgmt)

## ⚡ Quick Commands Reference

```bash
# Check overall health
./scripts/health-check-all.sh

# View real-time metrics
./scripts/watch-metrics.sh

# Generate status report
./scripts/status-report.sh

# Emergency stop
./scripts/emergency-stop.sh

# Full restart
./scripts/full-restart.sh
```

---

*Last Updated: 2025-01-23*
*Version: 1.0.0*
*Next Review: 2025-02-23*