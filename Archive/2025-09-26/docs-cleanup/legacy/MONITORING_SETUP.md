# ToolBoxAI Comprehensive Monitoring Setup
=============================================

This document provides instructions for setting up and using the comprehensive Prometheus and Grafana monitoring integration for the ToolBoxAI backend application.

## 🎯 Overview

The monitoring system provides:
- **Real-time metrics collection** with Prometheus
- **Visual dashboards** with Grafana
- **Alerting capabilities** with AlertManager
- **System health monitoring** with various exporters
- **Business metrics tracking** for ToolBoxAI-specific KPIs
- **SLA compliance monitoring** (<150ms P95 latency target)

## 📊 Components

### Core Services
- **Prometheus** (port 9090) - Metrics collection and storage
- **Grafana** (port 3000) - Visualization and dashboards
- **AlertManager** (port 9093) - Alert processing and routing

### Exporters
- **Node Exporter** (port 9100) - System metrics
- **Redis Exporter** (port 9121) - Redis cache metrics
- **Postgres Exporter** (port 9187) - Database metrics
- **cAdvisor** (port 8080) - Container metrics

### Optional Components
- **Loki** (port 3100) - Log aggregation
- **Promtail** - Log shipping to Loki

## 🚀 Quick Start

### Method 1: Using Docker Compose (Recommended)

```bash
# Start the complete monitoring stack
docker-compose -f infrastructure/docker/docker-compose.monitoring.yml up -d

# Wait for services to be ready (2-3 minutes)

# Run setup script to configure dashboards and data sources
python scripts/monitoring/setup_monitoring.py --wait-for-services --test-data
```

### Method 2: Using the Startup Script

```bash
# Make the script executable
chmod +x start_monitoring.sh

# Start monitoring in development mode
./start_monitoring.sh --dev --setup

# Or start in production mode
./start_monitoring.sh --prod --setup
```

### Method 3: Manual Setup

```bash
# Install Python dependencies
pip install httpx docker pyyaml prometheus_client

# Start Docker services
cd infrastructure/docker
docker-compose -f docker-compose.monitoring.yml up -d

# Run setup script
python ../../scripts/monitoring/setup_monitoring.py
```

## 🔧 Configuration

### Environment Variables

Create or update your `.env` file:

```env
# Database (for exporters)
POSTGRES_DB=toolboxai_dev
POSTGRES_USER=toolboxai
POSTGRES_PASSWORD=dev_password

# Redis (for exporter)
REDIS_PASSWORD=dev_redis_pass

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure-password

# Prometheus retention
PROMETHEUS_RETENTION_TIME=15d
PROMETHEUS_RETENTION_SIZE=10GB
```

### Backend Integration

The monitoring is automatically integrated into the FastAPI backend. To enable in your application:

```python
from apps.backend.core.monitoring_integration import initialize_monitoring

# In your FastAPI app creation
app = FastAPI()
initialize_monitoring(app)
```

### Custom Metrics

Add custom business metrics in your application code:

```python
from apps.backend.core.metrics import metrics

# Record user activity
metrics.record_user_registration(user_type="student", source="web")
metrics.update_active_users(count=150, user_type="student")

# Record content generation
metrics.record_content_generation(
    content_type="lesson",
    subject="mathematics",
    grade_level="5th",
    duration=2.5,
    status="success"
)

# Record agent tasks
metrics.record_agent_task(
    agent_type="content_agent",
    task_type="lesson_creation",
    duration=15.2,
    status="success"
)
```

## 📊 Dashboards

### Main Dashboard: ToolBoxAI Comprehensive Monitoring

Access: http://localhost:3000/d/toolboxai-main

**Sections:**
1. **API Performance Dashboard**
   - P50/P95/P99 latency graphs
   - Request rate and error rate
   - SLA compliance tracking

2. **System Health Dashboard**
   - CPU and Memory usage
   - Database connection pool status
   - Redis cache performance

3. **Business Metrics Dashboard**
   - Active users by type
   - Content generation rates
   - Educational metrics

4. **Agent System Dashboard**
   - AI agent task metrics
   - LLM API performance
   - Task queue monitoring

5. **Container & Infrastructure**
   - Docker container metrics
   - Resource utilization
   - Health status overview

### Creating Custom Dashboards

1. Login to Grafana (admin/secure-password)
2. Create new dashboard
3. Add panels with PromQL queries
4. Use provided metrics (see Metrics Reference below)

## 🚨 Alerting

### Pre-configured Alerts

The system includes alerts for:
- **API Performance**: P95 latency >150ms (SLA violation)
- **Error Rates**: >1% 5xx errors
- **System Resources**: CPU >80%, Memory >85%, Disk >85%
- **Service Health**: Service down, database issues
- **Business Metrics**: Low content generation rates
- **Security**: High client error rates, rate limiting

### Alert Channels

Configure alert destinations in AlertManager:

```yaml
# Add to monitoring/alertmanager/alertmanager.yml
receivers:
  - name: 'slack-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts'
        title: 'ToolBoxAI Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### Webhook Integration

The backend provides webhook endpoints for alerts:
- `/api/v1/alerts/webhook` - General alerts
- `/api/v1/alerts/critical` - Critical alerts
- `/api/v1/alerts/security` - Security alerts

## 📈 Metrics Reference

### API Metrics
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_total` - Total requests by endpoint/status
- `http_active_requests` - Active concurrent requests
- `http_request_size_bytes` - Request size distribution
- `http_response_size_bytes` - Response size distribution

### Business Metrics
- `toolboxai_active_users_total` - Active users by type
- `toolboxai_content_generation_requests_total` - Content generation requests
- `toolboxai_content_generation_duration_seconds` - Generation duration
- `toolboxai_lessons_created_total` - Lessons created
- `toolboxai_quiz_completions_total` - Quiz completions

### Agent Metrics
- `toolboxai_agent_tasks_total` - Agent task counts
- `toolboxai_agent_task_duration_seconds` - Task durations
- `toolboxai_active_agent_tasks` - Active task queue size
- `toolboxai_llm_api_requests_total` - LLM API usage
- `toolboxai_llm_token_usage_total` - Token consumption

### Cache Metrics
- `toolboxai_cache_operations_total` - Cache hit/miss counts
- `toolboxai_cache_hit_rate` - Cache hit percentage
- `redis_*` - Redis-specific metrics from exporter

### Database Metrics
- `toolboxai_database_query_duration_seconds` - Query performance
- `toolboxai_database_connection_pool_*` - Connection pool stats
- `pg_*` - PostgreSQL metrics from exporter

## 🛠️ Troubleshooting

### Common Issues

**1. Services not starting**
```bash
# Check Docker daemon
docker info

# Check compose file syntax
docker-compose -f infrastructure/docker/docker-compose.monitoring.yml config

# View logs
docker-compose -f infrastructure/docker/docker-compose.monitoring.yml logs
```

**2. Grafana login issues**
- Default: admin/secure-password
- Reset: Stop container, remove grafana data volume, restart

**3. Prometheus not scraping targets**
```bash
# Check targets page
curl http://localhost:9090/api/v1/targets

# Check backend metrics endpoint
curl http://localhost:8009/metrics
```

**4. No metrics appearing**
- Ensure backend is running with monitoring enabled
- Check metrics endpoint: `curl http://localhost:8009/metrics`
- Verify Prometheus configuration

**5. Alerts not firing**
- Check AlertManager UI: http://localhost:9093
- Verify alert rules: http://localhost:9090/alerts
- Test webhook endpoints

### Health Checks

```bash
# Check all service health
python scripts/monitoring/setup_monitoring.py --status

# Individual health checks
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health # Grafana
curl http://localhost:9093/-/healthy  # AlertManager
```

### Performance Tuning

**For high-traffic deployments:**

1. **Increase Prometheus retention**:
```yaml
# In docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=30d'
  - '--storage.tsdb.retention.size=50GB'
```

2. **Adjust scrape intervals**:
```yaml
# In monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 30s  # Increase for less load
```

3. **Enable metric sampling**:
```python
# In apps/backend/core/metrics.py
# Reduce high-cardinality metrics
```

## 📚 Example Queries

### PromQL Examples

```promql
# P95 response time
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Error rate percentage
(sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# Active users trend
rate(toolboxai_user_registrations_total[1h]) * 3600

# Cache hit rate
(sum(rate(toolboxai_cache_operations_total{result="hit"}[5m])) / sum(rate(toolboxai_cache_operations_total[5m]))) * 100

# Top slowest endpoints
topk(10, histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)))
```

### Grafana Variables

Use these template variables in dashboards:
```
# Instance selector
label_values(up, instance)

# Endpoint selector
label_values(http_requests_total, endpoint)

# User type selector
label_values(toolboxai_active_users_total, user_type)
```

## 🔐 Security Considerations

### Production Security

1. **Change default passwords**:
   - Grafana: admin/secure-password → strong password
   - Database passwords in .env

2. **Enable TLS**:
   - Configure HTTPS for Grafana
   - Use TLS for metric endpoints

3. **Network security**:
   - Firewall rules for monitoring ports
   - VPN access for monitoring interfaces

4. **Authentication**:
   - LDAP/OAuth integration for Grafana
   - API key authentication for Prometheus

### Sensitive Data

- Metrics do not contain sensitive user data
- Alert messages sanitized
- Log aggregation excludes PII

## 🚀 Scaling & Production

### Multi-Instance Setup

For production deployments:

1. **Prometheus Federation**:
```yaml
# In prometheus.yml
- job_name: 'federate'
  static_configs:
    - targets: ['prometheus-1:9090', 'prometheus-2:9090']
```

2. **Grafana High Availability**:
   - External database for dashboards
   - Load balancer for multiple Grafana instances

3. **Long-term Storage**:
   - Configure remote write to external TSDB
   - Use Thanos for long-term metrics storage

### Resource Planning

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB for 15 days retention

**Recommended Production:**
- CPU: 4+ cores
- RAM: 8GB+
- SSD: 100GB+ for metrics storage

## 📞 Support

### Getting Help

1. **Check logs**: `docker-compose logs [service_name]`
2. **Review configuration**: All configs in `monitoring/` directory
3. **Test endpoints**: Use provided health check URLs
4. **Consult documentation**: This file and inline comments

### Monitoring the Monitoring

The system includes self-monitoring:
- Prometheus monitors its own health
- Grafana includes system metrics
- AlertManager has dead man's switch alerts

---

## 🎉 Success Criteria

Your monitoring is working correctly when:

✅ All services show healthy in `docker-compose ps`
✅ Grafana dashboard loads with data
✅ Prometheus shows all targets as UP
✅ Alerts can be triggered and received
✅ Business metrics appear in dashboards
✅ SLA compliance is tracked (<150ms P95)

**Next Steps:**
1. Customize dashboards for your specific needs
2. Set up additional alert channels (Slack, email, PagerDuty)
3. Configure long-term storage for metrics
4. Implement custom business logic metrics
5. Set up monitoring for additional services

---

*ToolBoxAI Comprehensive Monitoring v1.0*
*Built for production-grade observability*