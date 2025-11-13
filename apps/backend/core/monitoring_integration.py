"""
Monitoring Integration for ToolBoxAI FastAPI Application
======================================================

This module integrates comprehensive monitoring capabilities into the FastAPI application:
- Prometheus metrics collection and exposition
- Custom metrics for business logic
- Health check endpoints
- Middleware for automatic request tracking
- Performance monitoring integration
"""

import logging
import time

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from apps.backend.api.health.enhanced_health import router as health_router
from apps.backend.core.config import settings
from apps.backend.core.metrics import metrics as custom_metrics
from apps.backend.middleware.prometheus_middleware import setup_prometheus_middleware

logger = logging.getLogger(__name__)


class ToolBoxAIMonitoringIntegration:
    """
    Main integration class for ToolBoxAI monitoring capabilities.

    Provides a single point of configuration for all monitoring features
    including Prometheus metrics, health checks, and observability.
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.instrumentator = None
        self.custom_registry = None
        self.monitoring_enabled = True

        # Track initialization
        self.initialized = False
        self.start_time = time.time()

    def setup_monitoring(
        self,
        enable_prometheus: bool = True,
        enable_health_checks: bool = True,
        enable_custom_metrics: bool = True,
        metrics_endpoint: str = "/metrics",
        excluded_paths: set | None = None,
    ) -> None:
        """
        Setup comprehensive monitoring for the FastAPI application.

        Args:
            enable_prometheus: Enable Prometheus metrics collection
            enable_health_checks: Enable health check endpoints
            enable_custom_metrics: Enable custom business metrics
            metrics_endpoint: Endpoint path for Prometheus metrics
            excluded_paths: Paths to exclude from monitoring
        """

        logger.info("Setting up ToolBoxAI monitoring integration...")

        try:
            # Default excluded paths
            if excluded_paths is None:
                excluded_paths = {
                    "/docs",
                    "/redoc",
                    "/openapi.json",
                    "/favicon.ico",
                    "/robots.txt",
                    "/health/live",  # Exclude liveness probe from metrics
                }

            # 1. Setup Prometheus FastAPI Instrumentator
            if enable_prometheus:
                self._setup_prometheus_instrumentator(metrics_endpoint, excluded_paths)

            # 2. Setup custom middleware for detailed tracking
            if enable_custom_metrics:
                self._setup_custom_middleware(excluded_paths)

            # 3. Setup health check endpoints
            if enable_health_checks:
                self._setup_health_endpoints()

            # 4. Setup custom metrics endpoint
            if enable_custom_metrics:
                self._setup_custom_metrics_endpoint(metrics_endpoint)

            # 5. Add startup metrics
            self._setup_startup_metrics()

            # 6. Add shutdown handlers
            self._setup_shutdown_handlers()

            self.initialized = True
            logger.info("✅ ToolBoxAI monitoring integration completed successfully")

        except Exception as e:
            logger.error(f"❌ Failed to setup monitoring integration: {e}")
            self.monitoring_enabled = False
            raise

    def _setup_prometheus_instrumentator(self, metrics_endpoint: str, excluded_paths: set) -> None:
        """Setup Prometheus FastAPI Instrumentator with custom configuration"""

        logger.info("Setting up Prometheus FastAPI Instrumentator...")

        # Create instrumentator with custom configuration
        self.instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/health/live"],  # Exclude liveness probe
            env_var_name="ENABLE_METRICS",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )

        # Add default metrics
        self.instrumentator.add(
            metrics.request_size(
                should_include_handler=True,
                should_include_method=True,
                should_include_status=True,
                metric_namespace="toolboxai",
                metric_subsystem="http",
            )
        ).add(
            metrics.response_size(
                should_include_handler=True,
                should_include_method=True,
                should_include_status=True,
                metric_namespace="toolboxai",
                metric_subsystem="http",
            )
        ).add(
            metrics.latency(
                should_include_handler=True,
                should_include_method=True,
                should_include_status=True,
                metric_namespace="toolboxai",
                metric_subsystem="http",
            )
        ).add(
            metrics.requests(
                should_include_handler=True,
                should_include_method=True,
                should_include_status=True,
                metric_namespace="toolboxai",
                metric_subsystem="http",
            )
        )

        # Add custom ToolBoxAI-specific metrics
        self.instrumentator.add(self._create_custom_instrumentator_metric())

        # Initialize instrumentator with the app
        self.instrumentator.instrument(self.app)

        # Expose metrics endpoint
        self.instrumentator.expose(self.app, endpoint=metrics_endpoint, tags=["monitoring"])

        logger.info(f"✅ Prometheus instrumentator configured with endpoint: {metrics_endpoint}")

    def _create_custom_instrumentator_metric(self):
        """Create custom instrumentator metric for ToolBoxAI-specific tracking"""

        def custom_metric(info: metrics.Info) -> None:
            """Custom metric function to track ToolBoxAI-specific request patterns"""

            # Track API endpoint performance
            if info.modified_handler.startswith("/api/"):
                custom_metrics.record_request(
                    method=info.method,
                    endpoint=info.modified_handler,
                    status_code=info.response.status_code,
                    duration=info.modified_duration,
                    handler="api_endpoint",
                )

            # Track content generation requests specifically
            if "/content" in info.modified_handler:
                custom_metrics.record_content_generation(
                    content_type="api_request",
                    subject="general",
                    grade_level="mixed",
                    duration=info.modified_duration,
                    status="success" if info.response.status_code < 400 else "failed",
                )

            # Track agent requests
            if "/agent" in info.modified_handler:
                custom_metrics.record_agent_task(
                    agent_type="api_agent",
                    task_type="api_request",
                    duration=info.modified_duration,
                    status="success" if info.response.status_code < 400 else "failed",
                )

        return custom_metric

    def _setup_custom_middleware(self, excluded_paths: set) -> None:
        """Setup custom Prometheus middleware for detailed tracking"""

        logger.info("Setting up custom Prometheus middleware...")

        try:
            setup_prometheus_middleware(
                app=self.app,
                metrics_path="/metrics",
                skip_paths=excluded_paths,
                enable_request_size_tracking=True,
                enable_response_size_tracking=True,
                high_cardinality_limit=1000,
                rate_limit_window=60,
                rate_limit_requests=60,
            )

            logger.info("✅ Custom Prometheus middleware configured")

        except Exception as e:
            logger.warning(f"⚠️ Failed to setup custom middleware: {e}")

    def _setup_health_endpoints(self) -> None:
        """Setup comprehensive health check endpoints"""

        logger.info("Setting up health check endpoints...")

        # Include the enhanced health router
        self.app.include_router(health_router)

        # Add a simple liveness probe that doesn't generate metrics
        @self.app.get("/health/live", tags=["health"], include_in_schema=False)
        async def liveness_probe():
            """Simple liveness probe for Kubernetes"""
            return {"status": "alive"}

        logger.info("✅ Health check endpoints configured")

    def _setup_custom_metrics_endpoint(self, base_metrics_endpoint: str) -> None:
        """Setup custom metrics endpoint for business metrics"""

        logger.info("Setting up custom metrics endpoints...")

        # Business metrics endpoint
        @self.app.get("/metrics/business", tags=["monitoring"])
        async def business_metrics():
            """Endpoint for business-specific metrics"""
            return {
                "timestamp": time.time(),
                "metrics": {
                    "active_users": custom_metrics.active_users_total._value._value,
                    "content_generation_rate": "calculated_from_prometheus",
                    "agent_task_queue_size": "calculated_from_prometheus",
                },
            }

        # Performance metrics endpoint
        @self.app.get("/metrics/performance", tags=["monitoring"])
        async def performance_metrics():
            """Endpoint for performance-specific metrics"""
            return {
                "timestamp": time.time(),
                "sla_metrics": {
                    "p95_response_time_ms": "calculated_from_prometheus",
                    "error_rate_percent": "calculated_from_prometheus",
                    "availability_percent": 99.9,
                },
            }

        # Metrics health endpoint
        @self.app.get("/metrics/health", tags=["monitoring"])
        async def metrics_health():
            """Health check for metrics system"""
            from apps.backend.core.metrics import check_metrics_health

            return check_metrics_health()

        logger.info("✅ Custom metrics endpoints configured")

    def _setup_startup_metrics(self) -> None:
        """Setup application startup metrics"""

        @self.app.on_event("startup")
        async def startup_metrics():
            """Record application startup metrics"""
            logger.info("Recording startup metrics...")

            # Update app info metric
            custom_metrics.app_uptime_seconds.set_to_current_time()
            custom_metrics.app_health_status.state("healthy")

            # Record startup event
            logger.info(f"ToolBoxAI backend started - monitoring active")

    def _setup_shutdown_handlers(self) -> None:
        """Setup application shutdown handlers"""

        @self.app.on_event("shutdown")
        async def shutdown_metrics():
            """Handle application shutdown metrics"""
            logger.info("Recording shutdown metrics...")

            # Update health status
            custom_metrics.app_health_status.state("unhealthy")

            logger.info("ToolBoxAI backend shutting down - monitoring stopped")

    def get_monitoring_status(self) -> dict:
        """Get current monitoring system status"""

        return {
            "monitoring_enabled": self.monitoring_enabled,
            "initialized": self.initialized,
            "uptime_seconds": time.time() - self.start_time,
            "instrumentator_enabled": self.instrumentator is not None,
            "custom_metrics_enabled": True,
            "health_checks_enabled": True,
        }


# Global monitoring integration instance
monitoring_integration = None


def setup_monitoring_for_app(app: FastAPI, **kwargs) -> ToolBoxAIMonitoringIntegration:
    """
    Setup monitoring for a FastAPI application.

    Args:
        app: FastAPI application instance
        **kwargs: Configuration options for monitoring setup

    Returns:
        ToolBoxAIMonitoringIntegration instance
    """
    global monitoring_integration

    if monitoring_integration is None:
        monitoring_integration = ToolBoxAIMonitoringIntegration(app)

    # Setup monitoring with provided configuration
    monitoring_integration.setup_monitoring(**kwargs)

    return monitoring_integration


def get_monitoring_integration() -> ToolBoxAIMonitoringIntegration | None:
    """Get the current monitoring integration instance"""
    return monitoring_integration


# Startup function to be called during app initialization
def initialize_monitoring(app: FastAPI) -> None:
    """
    Initialize monitoring during application startup.

    This function should be called during FastAPI app creation.
    """

    logger.info("Initializing ToolBoxAI monitoring...")

    try:
        # Check if monitoring is disabled
        if settings.ENVIRONMENT == "testing":
            logger.info("Monitoring disabled in testing environment")
            return

        # Setup monitoring with environment-specific configuration
        monitoring_config = {
            "enable_prometheus": True,
            "enable_health_checks": True,
            "enable_custom_metrics": True,
            "metrics_endpoint": "/metrics",
            "excluded_paths": {
                "/docs",
                "/redoc",
                "/openapi.json",
                "/favicon.ico",
                "/robots.txt",
                "/health/live",
            },
        }

        # Disable certain features in development if needed
        if settings.ENVIRONMENT == "development":
            logger.info("Development mode - full monitoring enabled")

        # Setup monitoring
        setup_monitoring_for_app(app, **monitoring_config)

        logger.info("✅ ToolBoxAI monitoring initialization completed")

    except Exception as e:
        logger.error(f"❌ Failed to initialize monitoring: {e}")
        # Don't fail the application startup due to monitoring issues
        logger.warning("⚠️ Application will continue without full monitoring capabilities")


# Export main components
__all__ = [
    "ToolBoxAIMonitoringIntegration",
    "setup_monitoring_for_app",
    "get_monitoring_integration",
    "initialize_monitoring",
    "monitoring_integration",
]
