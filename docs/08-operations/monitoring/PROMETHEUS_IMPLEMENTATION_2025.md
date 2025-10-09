# Prometheus Monitoring Stack Implementation - ToolboxAI (2025)

## Overview

This document describes the actual implementation of the Prometheus monitoring stack for ToolboxAI, completed on September 28, 2025. This is the production configuration currently running with all components operational.

## Architecture

### Current Running Containers

All monitoring components are deployed as Docker containers on a unified monitoring network:

| Component | Container ID | Port | Status |
|-----------|-------------|------|--------|
| Prometheus | ced4f25f065961fa | 9090 | Running |
| Grafana | 435fb9a29d6d7c8d | 3000 | Running |
| Loki | 03ca72de474e3be4 | 3100 | Running |
| Promtail | 48dec4e7fb08997 | 9080 | Running |
| OpenTelemetry | a3de9f68b91a9081 | 4317/4318 | Running |
| Jaeger | 6ceb03cd6bc9159c | 16686/4317 | Running |
| Redis | c6187cae3954b281 | 6379 | Running |

### Network Configuration

All containers are connected to a custom Docker network `toolboxai-monitoring`:

```bash
# Network created with:
docker network create toolboxai-monitoring

# Containers connected with:
docker network connect toolboxai-monitoring <container_id>
```

## Component Configurations

### 1. Prometheus Configuration

**Location:** `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/config/prometheus/prometheus-runtime.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'fastapi-backend'
    static_configs:
      - targets: ['host.docker.internal:8009']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana-toolboxai:3000']
    metrics_path: /metrics

  - job_name: 'loki'
    static_configs:
      - targets: ['grafana-loki-toolboxai:3100']
    metrics_path: /metrics

  - job_name: 'jaeger'
    static_configs:
      - targets: ['jaegertracing-toolboxai:14269']
    metrics_path: /metrics

  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-toolboxai:8888']
    metrics_path: /metrics

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter-toolboxai:9121']
    metrics_path: /metrics
```

### 2. Loki Configuration (Stable v2.9.3)

**Location:** `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/config/loki/loki-simple.yml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
  filesystem:
    directory: /loki/chunks

compactor:
  working_directory: /loki/boltdb-shipper-compactor

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

### 3. Promtail Configuration

**Location:** `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/config/promtail/promtail-config.yml`

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://grafana-loki-toolboxai:3100/loki/api/v1/push
    tenant_id: toolboxai

scrape_configs:
  - job_name: docker
    static_configs:
      - targets:
          - localhost
        labels:
          job: docker
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            time: time

      - regex:
          expression: '^/var/lib/docker/containers/(?P<container_id>[^/]+)/.*$'
          source: filename

      - labels:
          container_id:
          stream:

      - timestamp:
          source: time
          format: RFC3339Nano

      - output:
          source: log

  - job_name: application
    static_configs:
      - targets:
          - localhost
        labels:
          job: application
          __path__: /app/logs/*.log
```

### 4. OpenTelemetry Collector Configuration

**Location:** `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/config/otel/otel-collector-config.yaml`

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
  resource:
    attributes:
      - key: environment
        value: production
        action: upsert
      - key: service.namespace
        value: toolboxai
        action: upsert

exporters:
  otlp/jaeger:
    endpoint: jaegertracing-toolboxai:4317
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: otel
    const_labels:
      environment: production

  otlphttp/loki:
    endpoint: http://grafana-loki-toolboxai:3100/otlp/v1/logs
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [otlp/jaeger]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [prometheus]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlphttp/loki]

  telemetry:
    logs:
      level: info
    metrics:
      level: detailed
```

### 5. Jaeger v2 Configuration (OTLP Support)

Jaeger is running with the following configuration:
- **Storage:** In-memory (development) - Switch to Cassandra/Elasticsearch for production
- **OTLP Receiver:** Port 4317 (gRPC) and 4318 (HTTP)
- **Query UI:** Port 16686
- **Metrics:** Port 14269

Command used to start Jaeger:
```bash
docker run -d \
  --name jaegertracing-toolboxai \
  --network toolboxai-monitoring \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14269:14269 \
  -p 4317:4317 \
  -p 4318:4318 \
  -e SPAN_STORAGE_TYPE=memory \
  jaegertracing/all-in-one:latest
```

## FastAPI Integration

### Metrics Endpoint

Added to `/apps/backend/main.py`:

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    metrics_data = generate_latest(REGISTRY)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={"Content-Type": CONTENT_TYPE_LATEST}
    )
```

### OpenTelemetry Instrumentation

Created `/apps/backend/core/telemetry.py` with comprehensive instrumentation:

```python
class TelemetryManager:
    def initialize(self, service_name, service_version, otel_endpoint):
        # Initialize tracing with OTLP exporter
        # Initialize metrics with periodic export
        # Instrument libraries (FastAPI, SQLAlchemy, Redis, etc.)

    def instrument_fastapi(self, app):
        # Auto-instrument FastAPI endpoints
        # Add custom span attributes
        # Exclude health/metrics endpoints
```

Integration in app factory (`/apps/backend/core/app_factory.py`):
- Initialize telemetry during app creation
- Instrument FastAPI app after creation
- Shutdown telemetry in lifecycle cleanup

## Grafana Configuration

### Datasources

Configured via API:

```bash
# Prometheus datasource
curl -X POST http://localhost:3000/api/datasources \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus-toolboxai:9090",
    "access": "proxy"
  }'

# Loki datasource
curl -X POST http://localhost:3000/api/datasources \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://grafana-loki-toolboxai:3100",
    "access": "proxy"
  }'

# Jaeger datasource
curl -X POST http://localhost:3000/api/datasources \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jaeger",
    "type": "jaeger",
    "url": "http://jaegertracing-toolboxai:16686",
    "access": "proxy"
  }'
```

### Dashboards Created

1. **FastAPI Application Metrics** (`fastapi-dashboard.json`)
   - Request rate and response time
   - HTTP status codes distribution
   - Active connections and error rate
   - CPU and memory usage
   - Database query performance
   - Redis operations metrics
   - Agent task processing

2. **Loki Logs Visualization** (`loki-logs-dashboard.json`)
   - Log volume by level
   - Error logs stream
   - Application and container logs
   - API request and database query logs
   - Agent activity logs
   - Authentication and security logs

3. **Jaeger Distributed Tracing** (`jaeger-traces-dashboard.json`)
   - Trace timeline view
   - Service dependency map
   - Operation latency distribution
   - Trace error rate
   - Active spans monitoring
   - Database and HTTP request traces
   - Agent task traces

### Alerting Rules

Created comprehensive alerting rules in `/infrastructure/grafana/alerting/alert-rules.yaml`:

- **Critical Alerts:**
  - Service down (2 minutes)
  - High error rate (>5%)
  - Redis connection issues
  - SSL certificate expiry

- **Warning Alerts:**
  - High response time (P95 > 2s)
  - High memory usage (>2GB)
  - Database slow queries (P95 > 1s)
  - High agent error rate
  - Pusher connection failures
  - Low disk space (<10%)

### Notification Channels

Configured in `/infrastructure/grafana/alerting/notification-channels.yaml`:

- Email notifications for critical alerts
- Slack notifications for warnings
- Webhook to FastAPI backend for all alerts
- Mute intervals for weekends and after-hours

## Troubleshooting & Lessons Learned

### Issues Encountered and Resolved

1. **Loki Configuration Errors**
   - **Problem:** `field shared_store not found in type indexshipper.Config`
   - **Solution:** Removed unsupported fields, used simpler configuration with stable v2.9.3

2. **OpenTelemetry Collector Issues**
   - **Problem:** `unknown type: 'loki' for id: 'loki'`
   - **Solution:** Changed to `otlphttp/loki` exporter
   - **Problem:** `service.telemetry.metrics has invalid keys: address`
   - **Solution:** Removed address field from telemetry.metrics

3. **Promtail JSON Parsing Errors**
   - **Problem:** `invalid json stage config: could not compile JMES expression`
   - **Solution:** Removed template syntax from JSON expressions

4. **Jaeger Storage Issues**
   - **Problem:** `mkdir /badger/key: permission denied`
   - **Solution:** Switched to in-memory storage for development

5. **FastAPI Import Issues**
   - **Problem:** Circular import with monitoring module
   - **Solution:** Removed conflicting monitoring directory, cleaned up imports

### Performance Optimizations

1. **Batch Processing:** Configured batch processors in OTEL collector to reduce overhead
2. **Memory Limits:** Set memory limits for OTEL collector to prevent OOM
3. **Scrape Intervals:** Optimized Prometheus scrape intervals (10s for critical, 15s for standard)
4. **Log Rotation:** Configured log retention in Loki (168h max age)
5. **Metric Cardinality:** Excluded high-cardinality labels from metrics

## Testing & Validation

### Health Checks

```bash
# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Loki ready check
curl http://localhost:3100/ready

# Jaeger health
curl http://localhost:16686/api/health

# OTEL collector metrics
curl http://localhost:8888/metrics

# FastAPI metrics
curl http://localhost:8009/metrics
```

### Query Examples

**Prometheus Queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# P95 response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Loki Queries:**
```logql
# Error logs
{job="application"} |= "ERROR"

# API requests
{job="application"} |~ "(GET|POST|PUT|DELETE)" |~ "/api/"

# Agent activity
{job="application"} |~ "ContentAgent|OrchestrationAgent"
```

**Jaeger Queries:**
```
# Service: toolboxai-backend
# Operation: GET /api/v1/content
# Tags: http.status_code=200
# Min Duration: 100ms
```

## Production Deployment Checklist

- [ ] Switch Jaeger to persistent storage (Cassandra/Elasticsearch)
- [ ] Configure TLS for all monitoring endpoints
- [ ] Set up authentication for Grafana and Prometheus
- [ ] Implement log rotation and archival strategy
- [ ] Configure alerting recipients and escalation policies
- [ ] Set up backup for Grafana dashboards and configurations
- [ ] Implement metric retention policies
- [ ] Configure distributed tracing sampling rates
- [ ] Set up monitoring for the monitoring stack itself
- [ ] Document runbooks for each alert

## Maintenance Procedures

### Daily Tasks
- Review Grafana dashboards for anomalies
- Check alert status and acknowledge/resolve
- Verify all targets are being scraped

### Weekly Tasks
- Review and tune alert thresholds
- Analyze trace data for performance bottlenecks
- Archive old logs if needed

### Monthly Tasks
- Update monitoring component versions
- Review and optimize dashboard queries
- Audit metric cardinality
- Test disaster recovery procedures

## Access URLs

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Jaeger UI:** http://localhost:16686
- **Loki:** http://localhost:3100 (API only)
- **OTEL Metrics:** http://localhost:8888/metrics
- **FastAPI Metrics:** http://localhost:8009/metrics

## Support & References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [FastAPI Monitoring Guide](https://fastapi.tiangolo.com/tutorial/monitoring/)

---

*Last Updated: September 28, 2025*
*Implementation Completed By: Claude Code*