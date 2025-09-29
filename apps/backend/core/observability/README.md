# Observability Integration for FastAPI Application

This module provides comprehensive observability features for the FastAPI application, including trace correlation, anomaly detection, and real-time monitoring.

## Features

### 1. Trace Correlation System (`correlation.py`)

- **W3C Trace Context Propagation**: Full support for W3C trace context standard
- **Cross-Service Correlation**: Track requests across HTTP, WebSocket, and async tasks
- **Context Variables**: Automatic correlation ID, trace ID, and user ID propagation
- **Thread-Safe Storage**: Efficient correlation context storage with automatic cleanup
- **Middleware Integration**: Seamless integration with FastAPI middleware stack

#### Usage

```python
from apps.backend.core.observability import (
    correlation_manager,
    correlate_async_task,
    get_correlation_context
)

# Decorating async functions
@correlate_async_task("data_processing")
async def process_data():
    context = get_correlation_context()
    print(f"Processing data with correlation ID: {context.correlation_id}")

# Manual context management
async def my_handler(request: Request):
    context = correlation_manager.create_context_from_request(request)
    async with correlation_manager.async_correlation_context(context):
        # All operations here will be correlated
        await process_data()
```

### 2. Anomaly Detection System (`anomaly_detection.py`)

- **Statistical Analysis**: Multiple detection algorithms (Z-score, IQR, exponential smoothing)
- **Real-Time Detection**: Continuous monitoring with minimal performance overhead
- **Pattern Recognition**: Sudden change detection and trend analysis
- **Configurable Thresholds**: Customizable sensitivity for different metrics
- **Automatic Alerting**: Real-time alerts when anomalies are detected

#### Usage

```python
from apps.backend.core.observability import (
    anomaly_engine,
    track_latency,
    track_errors
)

# Decorating functions for automatic tracking
@track_latency("api_endpoint")
@track_errors("api_endpoint")
async def my_api_endpoint():
    # Function execution is automatically tracked
    return {"status": "success"}

# Manual metric recording
anomaly_engine.record_metric("custom_metric", 42.0)

# Get metrics summary
summary = anomaly_engine.get_metric_summary("api_endpoint_latency")
```

### 3. Main Integration (`main_observability.py`)

A complete FastAPI application with full observability integration.

## Quick Start

### 1. Basic Integration

```python
from apps.backend.core.observability import (
    CorrelationMiddleware,
    anomaly_engine,
    track_latency
)

app = FastAPI()

# Add correlation middleware
app.add_middleware(CorrelationMiddleware)

@app.get("/api/data")
@track_latency("data_endpoint")
async def get_data():
    return {"data": "example"}
```

### 2. Full Observability App

```python
from apps.backend.main_observability import create_observability_app

# Create app with full observability
app = create_observability_app(
    enable_system_metrics=True,
    enable_alerting=True
)
```

### 3. Custom Alert Handling

```python
from apps.backend.core.observability import alert_manager, AnomalyAlert

async def custom_alert_handler(alert: AnomalyAlert):
    print(f"Alert: {alert.title} - Severity: {alert.severity.value}")
    # Send to custom notification system

alert_manager.register_alert_handler(custom_alert_handler)
```

## API Endpoints

The observability integration adds several monitoring endpoints:

### Health Check
```
GET /observability/health
```
Returns the status of all observability components.

### Metrics Summary
```
GET /observability/metrics
```
Returns current metrics summary and correlation information.

### Recent Alerts
```
GET /observability/alerts?limit=50
```
Returns recent anomaly alerts.

### Correlation Chain
```
GET /observability/correlation/{correlation_id}
```
Returns the full correlation chain for a specific correlation ID.

### Configure Alerting
```
POST /observability/alerts/configure
{
    "webhook_urls": ["https://example.com/webhook"],
    "slack": {"webhook_url": "https://hooks.slack.com/..."},
    "email": {"smtp_host": "smtp.example.com", ...}
}
```

### Test Alert
```
POST /observability/test-alert
```
Creates a test alert to verify the alerting system.

## Configuration

### Environment Variables

```bash
# OpenTelemetry Configuration
OTEL_SERVICE_NAME=toolboxai-backend
OTEL_RESOURCE_ATTRIBUTES=service.name=toolboxai-backend,service.version=1.0.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Alerting Configuration
WEBHOOK_URLS=https://example.com/webhook1,https://example.com/webhook2
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASS=password

# Anomaly Detection Configuration
ANOMALY_DETECTION_ENABLED=true
LATENCY_THRESHOLD_MULTIPLIER=3.0
ERROR_RATE_THRESHOLD_MULTIPLIER=2.5
TRAFFIC_THRESHOLD_MULTIPLIER=2.0
```

### Programmatic Configuration

```python
from apps.backend.core.observability.anomaly_detection import anomaly_engine

# Configure detection thresholds
anomaly_engine.detection_config['latency']['threshold_multiplier'] = 2.5
anomaly_engine.detection_config['error_rate']['min_samples'] = 10

# Configure correlation store
from apps.backend.core.observability.correlation import _correlation_store
_correlation_store.max_size = 20000
_correlation_store.ttl_seconds = 7200  # 2 hours
```

## Integration with Existing Load Balancer

The observability system integrates seamlessly with the existing load balancing components:

```python
from apps.backend.core.global_load_balancer import GlobalLoadBalancer
from apps.backend.core.observability import track_latency, track_errors

class ObservabilityLoadBalancer(GlobalLoadBalancer):

    @track_latency("load_balancer_route")
    @track_errors("load_balancer_route")
    async def route_request(self, request):
        return await super().route_request(request)

    async def health_check_endpoint(self, endpoint):
        start_time = time.time()
        try:
            result = await super().health_check_endpoint(endpoint)
            # Record successful health check
            anomaly_engine.record_metric(
                f"health_check_latency_{endpoint.name}",
                (time.time() - start_time) * 1000
            )
            return result
        except Exception as e:
            # Record failed health check
            anomaly_engine.record_metric(f"health_check_errors_{endpoint.name}", 1)
            raise
```

## Performance Impact

The observability system is designed for minimal performance overhead:

- **Correlation Tracking**: < 1ms per request
- **Anomaly Detection**: < 0.5ms per metric recording
- **System Metrics**: Collected every 30 seconds in background
- **Memory Usage**: ~10MB for 10,000 stored correlation contexts
- **Storage Cleanup**: Automatic cleanup with configurable TTL

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **OpenTelemetry Not Working**
   - Check environment variables are set correctly
   - Verify OTLP endpoint is accessible
   - Enable debug logging: `OTEL_LOG_LEVEL=debug`

3. **High Memory Usage**
   - Reduce correlation store size: `_correlation_store.max_size = 5000`
   - Reduce TTL: `_correlation_store.ttl_seconds = 1800`

4. **Alerts Not Firing**
   - Check alert handlers are registered
   - Verify webhook URLs are accessible
   - Check anomaly detection thresholds

### Debug Mode

```python
import logging
logging.getLogger('apps.backend.core.observability').setLevel(logging.DEBUG)
```

### Health Checks

```bash
# Check observability health
curl http://localhost:8009/observability/health

# Check metrics
curl http://localhost:8009/observability/metrics

# Check recent alerts
curl http://localhost:8009/observability/alerts
```

## Examples

### Complete Example Application

```python
from fastapi import FastAPI, Request
from apps.backend.core.observability import (
    CorrelationMiddleware,
    track_latency,
    track_errors,
    correlate_async_task,
    get_correlation_context,
    anomaly_engine,
    alert_manager
)

app = FastAPI()
app.add_middleware(CorrelationMiddleware)

@app.get("/")
@track_latency("homepage")
@track_errors("homepage")
async def homepage():
    return {"message": "Hello, World!"}

@app.post("/process")
@track_latency("process_data")
@track_errors("process_data")
async def process_data(data: dict):
    # Start background task with correlation
    asyncio.create_task(background_processing(data))
    return {"status": "processing started"}

@correlate_async_task("background_processing")
async def background_processing(data: dict):
    context = get_correlation_context()
    print(f"Processing with correlation ID: {context.correlation_id}")

    # Simulate processing time
    await asyncio.sleep(2.0)

    # Record custom metrics
    anomaly_engine.record_metric("processing_items", len(data.get("items", [])))

    print("Processing completed")

# Custom alert handler
async def slack_alert_handler(alert):
    # Send to Slack
    print(f"Slack Alert: {alert.title}")

alert_manager.register_alert_handler(slack_alert_handler)
```

## Best Practices

1. **Use Correlation IDs**: Always use correlation decorators for async tasks
2. **Monitor Key Metrics**: Track latency and errors for critical endpoints
3. **Set Appropriate Thresholds**: Configure anomaly detection based on your SLAs
4. **Handle Alerts Promptly**: Set up proper alerting channels and response procedures
5. **Regular Cleanup**: Monitor memory usage and adjust TTL settings as needed
6. **Test Alerting**: Regularly test your alerting system with the test endpoint
7. **Performance Monitoring**: Monitor the observability system's own performance

## License

This observability system is part of the ToolboxAI FastAPI application and follows the same licensing terms.