"""
Observability Integration for FastAPI Application

Integrates comprehensive observability features including trace correlation,
anomaly detection, and real-time monitoring into the main FastAPI application.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from apps.backend.core.app_factory import create_app
from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager

# Import observability components
from apps.backend.core.observability.correlation import (
    CorrelationMiddleware,
    correlation_manager,
    websocket_correlation_manager,
    get_correlation_context,
    correlate_async_task
)
from apps.backend.core.observability.anomaly_detection import (
    anomaly_engine,
    alert_manager,
    AnomalyAlert,
    AnomalySeverity,
    track_latency,
    track_errors
)

logger = logging_manager.get_logger(__name__)


class ObservabilityMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect observability metrics"""

    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        self.request_count += 1

        # Record traffic metrics
        anomaly_engine.record_metric('http_requests_total', 1)
        anomaly_engine.record_metric('concurrent_requests', self.request_count)

        try:
            response = await call_next(request)

            # Record latency
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            self.total_processing_time += processing_time

            anomaly_engine.record_metric('http_request_duration_ms', processing_time)
            anomaly_engine.record_metric(
                f'http_request_duration_ms_{request.method.lower()}',
                processing_time
            )

            # Record status code metrics
            status_group = f"{response.status_code // 100}xx"
            anomaly_engine.record_metric(f'http_responses_{status_group}', 1)

            # Record error metrics
            if response.status_code >= 400:
                self.error_count += 1
                anomaly_engine.record_metric('http_errors_total', 1)
                anomaly_engine.record_metric(
                    f'http_errors_{response.status_code}',
                    1
                )

            # Calculate and record error rate
            if self.request_count > 0:
                error_rate = (self.error_count / self.request_count) * 100
                anomaly_engine.record_metric('http_error_rate_percent', error_rate)

            # Add observability headers to response
            response.headers['X-Request-Count'] = str(self.request_count)
            response.headers['X-Processing-Time-Ms'] = f"{processing_time:.2f}"

            return response

        except Exception as e:
            # Record exception metrics
            processing_time = (time.time() - start_time) * 1000
            self.error_count += 1

            anomaly_engine.record_metric('http_exceptions_total', 1)
            anomaly_engine.record_metric('http_request_duration_ms', processing_time)

            # Log error with correlation context
            context = get_correlation_context()
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra=context.to_log_extra() if context else {}
            )

            raise


class SystemMetricsCollector:
    """Collects system-level metrics"""

    def __init__(self):
        self.collection_interval = 30  # seconds
        self.collection_task = None

    async def start_collection(self):
        """Start collecting system metrics"""
        self.collection_task = asyncio.create_task(self._collection_loop())

    async def stop_collection(self):
        """Stop collecting system metrics"""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

    async def _collection_loop(self):
        """Main collection loop"""
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_metrics(self):
        """Collect various system metrics"""
        try:
            import psutil

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            anomaly_engine.record_metric('system_cpu_percent', cpu_percent)

            # Memory metrics
            memory = psutil.virtual_memory()
            anomaly_engine.record_metric('system_memory_percent', memory.percent)
            anomaly_engine.record_metric('system_memory_available_mb', memory.available / (1024 * 1024))

            # Disk metrics
            disk = psutil.disk_usage('/')
            anomaly_engine.record_metric('system_disk_percent', disk.percent)

            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                anomaly_engine.record_metric('system_network_bytes_sent', network.bytes_sent)
                anomaly_engine.record_metric('system_network_bytes_recv', network.bytes_recv)
            except Exception:
                pass  # Network metrics not available

        except ImportError:
            # psutil not available, skip system metrics
            pass
        except Exception as e:
            logger.warning(f"Error collecting system metrics: {e}")


class AlertingService:
    """Service for handling and routing anomaly alerts"""

    def __init__(self):
        self.webhook_urls: list = []
        self.email_enabled = False
        self.slack_enabled = False

        # Register with alert manager
        alert_manager.register_alert_handler(self.handle_alert)

    async def handle_alert(self, alert: AnomalyAlert):
        """Handle an anomaly alert"""
        try:
            # Log the alert
            logger.warning(
                f"Anomaly Alert: {alert.title}",
                extra={
                    'alert_id': alert.id,
                    'alert_type': alert.type.value,
                    'severity': alert.severity.value,
                    'metric': alert.metric_name,
                    'current_value': alert.current_value,
                    'expected_value': alert.expected_value,
                    'confidence': alert.confidence,
                    'correlation_id': alert.correlation_id,
                    'trace_id': alert.trace_id
                }
            )

            # Send to configured channels
            await self._send_to_webhooks(alert)
            await self._send_to_slack(alert)
            await self._send_email(alert)

        except Exception as e:
            logger.error(f"Error handling alert {alert.id}: {e}")

    async def _send_to_webhooks(self, alert: AnomalyAlert):
        """Send alert to configured webhooks"""
        if not self.webhook_urls:
            return

        import httpx

        payload = alert.to_dict()

        async with httpx.AsyncClient() as client:
            for webhook_url in self.webhook_urls:
                try:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    logger.debug(f"Alert sent to webhook: {webhook_url}")
                except Exception as e:
                    logger.error(f"Failed to send alert to webhook {webhook_url}: {e}")

    async def _send_to_slack(self, alert: AnomalyAlert):
        """Send alert to Slack (if configured)"""
        if not self.slack_enabled:
            return

        # Slack integration would go here
        # This is a placeholder for future implementation
        logger.debug("Slack alerting not implemented yet")

    async def _send_email(self, alert: AnomalyAlert):
        """Send alert via email (if configured)"""
        if not self.email_enabled:
            return

        # Email integration would go here
        # This is a placeholder for future implementation
        logger.debug("Email alerting not implemented yet")

    def configure_webhooks(self, webhook_urls: list):
        """Configure webhook URLs for alerts"""
        self.webhook_urls = webhook_urls

    def enable_slack(self, webhook_url: str):
        """Enable Slack alerting"""
        self.slack_enabled = True
        # Store Slack webhook URL

    def enable_email(self, smtp_config: dict):
        """Enable email alerting"""
        self.email_enabled = True
        # Store SMTP configuration


def create_observability_app(
    config_settings: Optional[object] = None,
    enable_system_metrics: bool = True,
    enable_alerting: bool = True
) -> FastAPI:
    """
    Create FastAPI app with full observability integration

    Args:
        config_settings: Optional configuration settings
        enable_system_metrics: Whether to collect system metrics
        enable_alerting: Whether to enable alerting service

    Returns:
        Configured FastAPI application with observability
    """
    # Create base app
    app = create_app(config_settings=config_settings)

    # Add observability middleware (order matters)
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(ObservabilityMetricsMiddleware)

    # Initialize services
    system_metrics_collector = SystemMetricsCollector() if enable_system_metrics else None
    alerting_service = AlertingService() if enable_alerting else None

    # Store services in app state
    app.state.system_metrics_collector = system_metrics_collector
    app.state.alerting_service = alerting_service

    # Add observability endpoints
    @app.get("/observability/health")
    async def observability_health():
        """Health check for observability components"""
        return {
            "status": "healthy",
            "correlation_manager": "active",
            "anomaly_detection": "active",
            "system_metrics": "active" if system_metrics_collector else "disabled",
            "alerting": "active" if alerting_service else "disabled",
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/observability/metrics")
    async def get_metrics():
        """Get current metrics summary"""
        context = get_correlation_context()

        summary = anomaly_engine.get_all_metrics_summary()
        correlation_metrics = correlation_manager.get_metrics()

        return {
            "metrics_summary": summary,
            "correlation_metrics": correlation_metrics,
            "correlation_id": context.correlation_id if context else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/observability/alerts")
    async def get_recent_alerts(limit: int = 50):
        """Get recent anomaly alerts"""
        alerts = alert_manager.get_recent_alerts(limit)
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/observability/correlation/{correlation_id}")
    async def get_correlation_chain(correlation_id: str):
        """Get correlation chain for a specific correlation ID"""
        chain = correlation_manager.get_correlation_chain(correlation_id)
        return {
            "correlation_id": correlation_id,
            "chain": [
                {
                    "correlation_id": ctx.correlation_id,
                    "trace_id": ctx.trace_id,
                    "span_id": ctx.span_id,
                    "request_type": ctx.request_type,
                    "user_id": ctx.user_id,
                    "created_at": ctx.created_at.isoformat(),
                    "metadata": ctx.metadata
                }
                for ctx in chain
            ],
            "chain_length": len(chain),
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.post("/observability/alerts/configure")
    async def configure_alerting(background_tasks: BackgroundTasks, config: Dict[str, Any]):
        """Configure alerting service"""
        if not alerting_service:
            raise HTTPException(status_code=404, detail="Alerting service not enabled")

        try:
            if "webhook_urls" in config:
                alerting_service.configure_webhooks(config["webhook_urls"])

            if "slack" in config:
                alerting_service.enable_slack(config["slack"]["webhook_url"])

            if "email" in config:
                alerting_service.enable_email(config["email"])

            return {"status": "configured", "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"Error configuring alerting: {e}")
            raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")

    @app.post("/observability/test-alert")
    async def create_test_alert(background_tasks: BackgroundTasks):
        """Create a test alert for testing alerting system"""
        if not alerting_service:
            raise HTTPException(status_code=404, detail="Alerting service not enabled")

        context = get_correlation_context()

        test_alert = AnomalyAlert(
            id=f"test_alert_{int(time.time())}",
            type=anomaly_engine.AnomalyType.UNUSUAL_PATTERN,
            severity=AnomalySeverity.LOW,
            title="Test Alert",
            description="This is a test alert to verify the alerting system is working",
            metric_name="test_metric",
            current_value=100.0,
            expected_value=50.0,
            threshold=2.0,
            confidence=2.5,
            correlation_id=context.correlation_id if context else None,
            trace_id=context.trace_id if context else None
        )

        background_tasks.add_task(alerting_service.handle_alert, test_alert)

        return {
            "status": "test_alert_created",
            "alert_id": test_alert.id,
            "timestamp": datetime.utcnow().isoformat()
        }

    # Add startup event for system metrics
    @app.on_event("startup")
    async def startup_observability():
        """Start observability services"""
        logger.info("Starting observability services")

        if system_metrics_collector:
            await system_metrics_collector.start_collection()
            logger.info("System metrics collection started")

        logger.info("Observability integration initialized")

    # Add shutdown event for cleanup
    @app.on_event("shutdown")
    async def shutdown_observability():
        """Stop observability services"""
        logger.info("Stopping observability services")

        if system_metrics_collector:
            await system_metrics_collector.stop_collection()
            logger.info("System metrics collection stopped")

        logger.info("Observability services stopped")

    # Add example endpoints with observability decorators
    @app.get("/example/tracked")
    @track_latency("example_endpoint")
    @track_errors("example_endpoint")
    async def tracked_endpoint():
        """Example endpoint with observability tracking"""
        context = get_correlation_context()

        # Simulate some work
        await asyncio.sleep(0.1)

        return {
            "message": "This endpoint is tracked for latency and errors",
            "correlation_id": context.correlation_id if context else None,
            "trace_id": context.trace_id if context else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/example/async-task")
    async def trigger_async_task():
        """Example endpoint that triggers an async task"""

        @correlate_async_task("background_processing")
        async def background_task():
            """Example background task with correlation"""
            await asyncio.sleep(0.5)
            logger.info("Background task completed")
            return "Task completed"

        # Start background task
        asyncio.create_task(background_task())

        context = get_correlation_context()
        return {
            "message": "Async task triggered",
            "correlation_id": context.correlation_id if context else None,
            "timestamp": datetime.utcnow().isoformat()
        }

    return app


# Create the observability-enabled app
app = create_observability_app(
    config_settings=settings,
    enable_system_metrics=True,
    enable_alerting=True
)

logger = logging_manager.get_logger(__name__)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI application with full observability")

    # Development server configuration
    uvicorn.run(
        "main_observability:app",
        host="127.0.0.1",
        port=8009,
        reload=True,
        log_level="info"
    )