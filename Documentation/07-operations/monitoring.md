# Monitoring and Observability Guide

## Overview

The ToolboxAI platform implements comprehensive monitoring across all components to ensure system health, performance, and reliability.

## Monitoring Stack

### Core Components

1. **Prometheus**: Metrics collection and storage
2. **Grafana**: Visualization and dashboards
3. **AlertManager**: Alert routing and management
4. **Loki**: Log aggregation
5. **Jaeger**: Distributed tracing
6. **Elasticsearch**: Log analysis and search
7. **Kibana**: Log visualization

## Metrics Collection

### Application Metrics

#### FastAPI Metrics

```python
# server/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

# Agent metrics
agent_tasks = Counter(
    'agent_tasks_total',
    'Total agent tasks',
    ['agent_type', 'status']
)

agent_duration = Histogram(
    'agent_task_duration_seconds',
    'Agent task duration',
    ['agent_type']
)

# Database metrics
db_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# WebSocket metrics
ws_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

ws_messages = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['direction', 'message_type']
)

# Middleware for automatic metrics collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    active_requests.inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    finally:
        active_requests.dec()

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

#### Custom Business Metrics

```python
# Business metrics
content_generated = Counter(
    'content_generated_total',
    'Total content items generated',
    ['content_type', 'subject', 'grade_level']
)

quiz_completions = Counter(
    'quiz_completions_total',
    'Total quiz completions',
    ['quiz_type', 'difficulty', 'result']
)

user_sessions = Gauge(
    'user_sessions_active',
    'Active user sessions',
    ['user_type']
)

learning_progress = Histogram(
    'learning_progress_percentage',
    'User learning progress',
    ['course_id', 'user_type']
)

# Usage in code
content_generated.labels(
    content_type='lesson',
    subject='Math',
    grade_level='7'
).inc()
```

### Infrastructure Metrics

#### Node Exporter Configuration

```yaml
# node-exporter-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9100"
    spec:
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
        resources:
          requests:
            memory: 30Mi
            cpu: 100m
          limits:
            memory: 50Mi
            cpu: 200m
```

#### Database Metrics

```yaml
# postgres-exporter.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-exporter
  template:
    metadata:
      labels:
        app: postgres-exporter
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9187"
    spec:
      containers:
      - name: postgres-exporter
        image: wrouesnel/postgres_exporter:latest
        env:
        - name: DATA_SOURCE_NAME
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: connection-string
        ports:
        - containerPort: 9187
```

## Logging

### Structured Logging

```python
# server/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id

def setup_logging():
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for persistent logs
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Usage
logger = setup_logging()

# Log with context
logger.info(
    "Content generated successfully",
    extra={
        'request_id': request_id,
        'user_id': user_id,
        'content_type': 'lesson',
        'duration': duration
    }
)
```

### Log Aggregation with Loki

```yaml
# loki-config.yaml
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
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2023-01-01
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
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
```

### Promtail Configuration

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            request_id: request_id
      - labels:
          level:
          request_id:
      - timestamp:
          source: timestamp
          format: Unix
```

## Distributed Tracing

### Jaeger Integration

```python
# server/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_tracing(app):
    # Configure tracer
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    
    return tracer

# Custom span creation
@app.post("/generate_content")
async def generate_content(request: ContentRequest):
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("generate_content") as span:
        span.set_attribute("content.type", request.content_type)
        span.set_attribute("content.subject", request.subject)
        
        # AI generation with nested span
        with tracer.start_as_current_span("ai_generation"):
            content = await generate_with_ai(request)
        
        # Database save with nested span
        with tracer.start_as_current_span("database_save"):
            await save_to_database(content)
        
        return content
```

## Dashboards

### Grafana Dashboard Configuration

#### System Overview Dashboard

```json
{
  "dashboard": {
    "title": "ToolboxAI System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Response Time (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Connections",
        "targets": [
          {
            "expr": "websocket_connections_active"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "database_connections_active"
          }
        ],
        "type": "gauge"
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

#### Agent Performance Dashboard

```json
{
  "dashboard": {
    "title": "Agent Performance",
    "panels": [
      {
        "title": "Agent Task Rate",
        "targets": [
          {
            "expr": "rate(agent_tasks_total[5m])",
            "legendFormat": "{{agent_type}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Agent Task Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(agent_task_duration_seconds_bucket[5m]))",
            "legendFormat": "{{agent_type}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Agent Success Rate",
        "targets": [
          {
            "expr": "rate(agent_tasks_total{status=\"success\"}[5m]) / rate(agent_tasks_total[5m])"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

## Alerting

### Alert Rules

```yaml
# prometheus-alerts.yaml
groups:
  - name: application
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is {{ $value }} seconds"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: database_connections_active / database_connections_max > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value }}% of connections in use"
      
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"
      
      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value }}% disk space remaining"
      
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.job }} is down"
```

### AlertManager Configuration

```yaml
# alertmanager.yaml
global:
  resolve_timeout: 5m
  smtp_from: 'alerts@toolboxai.com'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'alerts@toolboxai.com'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops-team@toolboxai.com'
        
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'ToolboxAI Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## Health Checks

### Application Health Endpoints

```python
# server/health.py
from fastapi import APIRouter, status
from typing import Dict, Any
import asyncio
import aioredis
import asyncpg

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        async with database.get_session() as session:
            await session.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis = await aioredis.create_redis_pool(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check external APIs
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=5.0
            )
            if response.status_code == 200:
                health_status["components"]["openai"] = "healthy"
            else:
                health_status["components"]["openai"] = f"unhealthy: status {response.status_code}"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["openai"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """Readiness check for Kubernetes"""
    # Check if all required services are ready
    try:
        async with database.get_session() as session:
            await session.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return {"status": "not ready"}, status.HTTP_503_SERVICE_UNAVAILABLE
```

### Kubernetes Probes

```yaml
# deployment.yaml
spec:
  containers:
  - name: api
    livenessProbe:
      httpGet:
        path: /health
        port: 8008
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 8008
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
    startupProbe:
      httpGet:
        path: /health
        port: 8008
      initialDelaySeconds: 0
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 30
```

## Performance Monitoring

### APM Integration

```python
# server/apm.py
from elasticapm import Client
from elasticapm.contrib.starlette import ElasticAPM

def setup_apm(app):
    apm_client = Client({
        'SERVICE_NAME': 'toolboxai-api',
        'SERVER_URL': 'http://apm-server:8200',
        'ENVIRONMENT': settings.ENVIRONMENT,
        'SECRET_TOKEN': settings.APM_SECRET_TOKEN
    })
    
    app.add_middleware(ElasticAPM, client=apm_client)
    
    return apm_client

# Custom transaction tracking
@app.post("/complex_operation")
async def complex_operation():
    apm_client = elasticapm.get_client()
    
    # Start transaction
    apm_client.begin_transaction('custom')
    
    try:
        # Track custom spans
        with apm_client.capture_span('database_query'):
            result = await database.query()
        
        with apm_client.capture_span('ai_processing'):
            processed = await ai_service.process(result)
        
        with apm_client.capture_span('cache_update'):
            await cache.set(key, processed)
        
        apm_client.end_transaction('complex_operation', 'success')
        return processed
    except Exception as e:
        apm_client.end_transaction('complex_operation', 'failure')
        raise
```

### Performance Baselines

```yaml
# performance-baselines.yaml
baselines:
  api_endpoints:
    - endpoint: /health
      p50: 10ms
      p95: 50ms
      p99: 100ms
    
    - endpoint: /api/auth/login
      p50: 100ms
      p95: 500ms
      p99: 1000ms
    
    - endpoint: /api/content/generate
      p50: 2000ms
      p95: 5000ms
      p99: 10000ms
  
  database_queries:
    - query: user_by_id
      p50: 5ms
      p95: 20ms
      p99: 50ms
    
    - query: content_list
      p50: 50ms
      p95: 200ms
      p99: 500ms
  
  agent_tasks:
    - agent: content_agent
      p50: 1000ms
      p95: 3000ms
      p99: 5000ms
    
    - agent: quiz_agent
      p50: 500ms
      p95: 1500ms
      p99: 3000ms
```

## Log Analysis

### Elasticsearch Queries

```json
// Find all errors in the last hour
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}

// Track specific user journey
{
  "query": {
    "bool": {
      "must": [
        {"match": {"user_id": "user-123"}},
        {"range": {"@timestamp": {"gte": "now-24h"}}}
      ]
    }
  },
  "sort": [{"@timestamp": "asc"}]
}

// Analyze slow requests
{
  "query": {
    "range": {
      "duration": {"gte": 1000}
    }
  },
  "aggs": {
    "by_endpoint": {
      "terms": {
        "field": "endpoint.keyword"
      }
    }
  }
}
```

### Kibana Visualizations

1. **Error Rate Timeline**: Line chart showing error rate over time
2. **Request Distribution**: Pie chart of requests by endpoint
3. **User Activity Heatmap**: Heatmap showing user activity patterns
4. **Performance Metrics**: Gauge charts for key performance indicators
5. **Agent Performance**: Bar charts comparing agent task durations

## Monitoring Best Practices

### 1. Metric Naming Conventions

```python
# Good metric names
http_requests_total
database_query_duration_seconds
cache_hit_ratio
user_sessions_active

# Bad metric names
requests  # Too generic
dbQueryTime  # Inconsistent casing
cache_hits_percentage  # Use ratio instead
```

### 2. Label Usage

```python
# Good label usage
request_count.labels(
    method="POST",
    endpoint="/api/content",
    status="200"
)

# Avoid high cardinality labels
# Bad: user_id as label (too many unique values)
# Good: user_type as label (limited values)
```

### 3. Alert Fatigue Prevention

- Set appropriate thresholds based on baselines
- Use alert grouping and deduplication
- Implement alert escalation policies
- Regular alert review and tuning

### 4. Dashboard Organization

- **Overview Dashboard**: High-level system health
- **Service Dashboards**: Detailed per-service metrics
- **Business Dashboards**: Business KPIs and metrics
- **Debug Dashboards**: Detailed technical metrics

### 5. Log Retention Policies

```yaml
retention_policies:
  - level: ERROR
    retention: 90d
  - level: WARNING
    retention: 30d
  - level: INFO
    retention: 7d
  - level: DEBUG
    retention: 1d
```

## Incident Response

### Runbook Template

```markdown
# Service: [Service Name]
## Alert: [Alert Name]

### Description
Brief description of what this alert means

### Impact
- User impact
- Business impact
- Technical impact

### Detection
- How is this issue detected?
- What metrics/logs to check?

### Mitigation
1. Immediate steps to mitigate
2. How to verify mitigation worked
3. Rollback procedures if needed

### Root Cause Analysis
- Common causes
- Where to look for root cause
- Historical incidents

### Prevention
- How to prevent recurrence
- Long-term fixes needed
```

## Monitoring Checklist

### Pre-Production
- [ ] All endpoints have metrics
- [ ] Health checks implemented
- [ ] Logging configured with proper levels
- [ ] Dashboards created and tested
- [ ] Alerts configured with runbooks
- [ ] Performance baselines established

### Production
- [ ] 24/7 monitoring enabled
- [ ] Alert escalation configured
- [ ] Log retention policies applied
- [ ] Backup monitoring in place
- [ ] Capacity planning metrics tracked
- [ ] Regular monitoring review scheduled