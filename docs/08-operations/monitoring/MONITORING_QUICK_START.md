# ToolboxAI Monitoring Stack - Quick Start Guide

## 🚀 Quick Access

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana** | [http://localhost:3000](http://localhost:3000) | admin/admin | Dashboards & Alerts |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | - | Metrics Explorer |
| **Jaeger** | [http://localhost:16686](http://localhost:16686) | - | Distributed Traces |
| **FastAPI Metrics** | [http://localhost:8009/metrics](http://localhost:8009/metrics) | - | Application Metrics |

## 📊 Available Dashboards

1. **FastAPI Application Metrics** - Real-time application performance
2. **Loki Logs Visualization** - Centralized log viewing
3. **Jaeger Distributed Tracing** - Request flow analysis

## 🔍 Common Queries

### Prometheus Metrics
```promql
# Request rate
rate(http_requests_total[5m])

# Error percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# P95 response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active connections
http_requests_in_progress
```

### Loki Logs
```logql
# View all errors
{job="application"} |= "ERROR"

# API requests
{job="application"} |~ "/api/" |~ "(GET|POST|PUT|DELETE)"

# Specific agent logs
{job="application"} |~ "ContentAgent"

# Authentication issues
{job="application"} |~ "(auth|login|permission|denied)"
```

## 🚨 Key Alerts Configured

### Critical (Immediate Action)
- ❌ Service Down - Backend unavailable for >2 minutes
- ❌ High Error Rate - Error rate >5% for 5 minutes
- ❌ Redis Down - Cache service unavailable

### Warning (Investigation Needed)
- ⚠️ High Response Time - P95 >2 seconds
- ⚠️ High Memory Usage - >2GB RAM usage
- ⚠️ Slow Database Queries - P95 >1 second
- ⚠️ Low Disk Space - <10% remaining

## 🔧 Troubleshooting

### Check Service Health
```bash
# Prometheus targets status
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Loki readiness
curl http://localhost:3100/ready

# Jaeger health
curl http://localhost:16686/api/health

# FastAPI health
curl http://localhost:8009/health
```

### Container Status
```bash
# Check monitoring containers
docker ps | grep -E "prometheus|grafana|loki|jaeger|otel"

# View container logs
docker logs <container_id> --tail 50

# Network connectivity
docker network inspect toolboxai-monitoring
```

## 📝 Data Retention

| Component | Retention Period | Storage Location |
|-----------|-----------------|------------------|
| Prometheus | 30 days | `/prometheus` volume |
| Loki | 7 days | `/loki` volume |
| Jaeger | In-memory (dev) | Upgrade to persistent for prod |
| Grafana | Persistent | `/var/lib/grafana` volume |

## 🔄 Common Operations

### Restart Services
```bash
# Restart individual service
docker restart <container_id>

# Restart all monitoring
docker restart ced4f25f065 435fb9a29d6d 03ca72de474 48dec4e7fb08 6ceb03cd6bc9 a3de9f68b91

# Check logs after restart
docker logs <container_id> --since 5m
```

### Add New Metrics
1. Add metric in FastAPI code
2. Restart backend: `docker restart toolboxai-backend`
3. Verify in Prometheus: http://localhost:9090/targets
4. Create dashboard panel in Grafana

### Export/Import Dashboards
```bash
# Export dashboard
curl -H "Authorization: Bearer glsa_kX2M4FnzQ8kX2M4FnzQ8" \
  http://localhost:3000/api/dashboards/uid/toolboxai-fastapi > dashboard.json

# Import dashboard
curl -X POST -H "Authorization: Bearer glsa_kX2M4FnzQ8kX2M4FnzQ8" \
  -H "Content-Type: application/json" \
  -d @dashboard.json \
  http://localhost:3000/api/dashboards/db
```

## 📚 Full Documentation

For complete implementation details, configurations, and architecture:
- [PROMETHEUS_IMPLEMENTATION_2025.md](./PROMETHEUS_IMPLEMENTATION_2025.md) - Full production setup
- [monitoring.md](./monitoring.md) - Architecture overview
- [infrastructure-monitoring.md](./infrastructure-monitoring.md) - Infrastructure strategy

## 🆘 Support Checklist

If monitoring isn't working:

- [ ] Verify all containers are running: `docker ps`
- [ ] Check network connectivity: `docker network ls`
- [ ] Ensure backend is exposing metrics: `curl localhost:8009/metrics`
- [ ] Verify Prometheus scraping: Check http://localhost:9090/targets
- [ ] Check Grafana datasources: Settings → Data Sources
- [ ] Review container logs for errors: `docker logs <container>`
- [ ] Ensure correct container names in configs (use `docker ps` to verify)

---
*Quick Start Guide - Last Updated: September 28, 2025*