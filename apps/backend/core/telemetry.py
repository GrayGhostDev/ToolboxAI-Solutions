"""
OpenTelemetry instrumentation for ToolboxAI FastAPI application.

This module configures distributed tracing, metrics collection, and logging
integration with OpenTelemetry for comprehensive observability.
"""

import logging
import os
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

_OTLP_SPAN_EXPORTER = None
_OTLP_METRIC_EXPORTER = None


def _load_otlp_span_exporter():
    global _OTLP_SPAN_EXPORTER
    if _OTLP_SPAN_EXPORTER is None:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter as _Exporter,
            )

            _OTLP_SPAN_EXPORTER = _Exporter
        except Exception as exc:
            logger.warning(f"OTLP span exporter unavailable: {exc}")
            _OTLP_SPAN_EXPORTER = False
    return _OTLP_SPAN_EXPORTER


def _load_otlp_metric_exporter():
    global _OTLP_METRIC_EXPORTER
    if _OTLP_METRIC_EXPORTER is None:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter as _MetricExporter,
            )

            _OTLP_METRIC_EXPORTER = _MetricExporter
        except Exception as exc:
            logger.warning(f"OTLP metric exporter unavailable: {exc}")
            _OTLP_METRIC_EXPORTER = False
    return _OTLP_METRIC_EXPORTER


class TelemetryManager:
    """Manages OpenTelemetry instrumentation for the application."""

    def __init__(self):
        self.tracer_provider: TracerProvider | None = None
        self.meter_provider: MeterProvider | None = None
        self.tracer = None
        self.meter = None
        self.initialized = False

    def initialize(
        self,
        service_name: str = "toolboxai-backend",
        service_version: str = "1.0.0",
        otel_endpoint: str = None,
        enable_logging: bool = True,
        enable_metrics: bool = True,
        enable_tracing: bool = True,
        additional_attributes: dict[str, Any] = None,
    ):
        """
        Initialize OpenTelemetry instrumentation.

        Args:
            service_name: Name of the service
            service_version: Version of the service
            otel_endpoint: OpenTelemetry collector endpoint
            enable_logging: Enable logging instrumentation
            enable_metrics: Enable metrics collection
            enable_tracing: Enable distributed tracing
            additional_attributes: Additional resource attributes
        """
        if self.initialized:
            logger.warning("Telemetry already initialized, skipping")
            return

        # Use environment variable if endpoint not provided
        if not otel_endpoint:
            otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

        if not otel_endpoint:
            logger.info("OTLP endpoint not configured – telemetry exporters disabled")
            enable_tracing = False
            enable_metrics = False

        # Create resource with service information
        resource_attributes = {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "deployment.environment": os.getenv("DEPLOYMENT_ENV", "local"),
            "service.namespace": "toolboxai",
            "host.name": os.getenv("HOSTNAME", "localhost"),
        }

        # Add any additional attributes
        if additional_attributes:
            resource_attributes.update(additional_attributes)

        resource = Resource.create(resource_attributes)

        # Initialize tracing
        if enable_tracing:
            self._initialize_tracing(resource, otel_endpoint)

        # Initialize metrics
        if enable_metrics:
            self._initialize_metrics(resource, otel_endpoint)

        # Set up propagators for distributed tracing
        # Use B3 propagator for compatibility with various systems
        set_global_textmap(B3MultiFormat())

        # Initialize instrumentations
        self._instrument_libraries()

        # Enable logging instrumentation if requested
        if enable_logging:
            LoggingInstrumentor().instrument(set_logging_format=True, log_level=logging.INFO)

        self.initialized = True
        logger.info(
            f"OpenTelemetry initialized for {service_name} v{service_version} "
            f"with endpoint {otel_endpoint}"
        )

    def _initialize_tracing(self, resource: Resource, endpoint: str):
        """Initialize tracing with OTLP exporter."""
        exporter_cls = _load_otlp_span_exporter()
        if not exporter_cls or not endpoint:
            logger.info("Tracing exporter unavailable; skipping OTLP tracing initialization")
            return

        otlp_exporter = exporter_cls(
            endpoint=endpoint,
            insecure=True,
            headers=(
                ("authorization", f"Bearer {os.getenv('OTEL_AUTH_TOKEN')}")
                if os.getenv("OTEL_AUTH_TOKEN")
                else None
            ),
        )

        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)

        # Add batch processor for efficient span export
        processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            schedule_delay_millis=5000,
        )
        self.tracer_provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(self.tracer_provider)

        # Get tracer for application use
        self.tracer = trace.get_tracer(__name__)

    def _initialize_metrics(self, resource: Resource, endpoint: str):
        """Initialize metrics with OTLP exporter."""
        exporter_cls = _load_otlp_metric_exporter()
        if not exporter_cls or not endpoint:
            logger.info("Metrics exporter unavailable; skipping OTLP metrics initialization")
            return

        otlp_exporter = exporter_cls(
            endpoint=endpoint,
            insecure=True,
            headers=(
                ("authorization", f"Bearer {os.getenv('OTEL_AUTH_TOKEN')}")
                if os.getenv("OTEL_AUTH_TOKEN")
                else None
            ),
        )

        # Create metrics reader with periodic export
        reader = PeriodicExportingMetricReader(
            exporter=otlp_exporter,
            export_interval_millis=60000,  # Export every minute
        )

        # Create meter provider
        self.meter_provider = MeterProvider(resource=resource, metric_readers=[reader])

        # Set as global meter provider
        metrics.set_meter_provider(self.meter_provider)

        # Get meter for application use
        self.meter = metrics.get_meter(__name__)

    def _instrument_libraries(self):
        """Instrument various libraries for automatic tracing."""
        # Instrument FastAPI - will be called separately with app instance
        # FastAPIInstrumentor is initialized in main.py

        # Instrument HTTP client (httpx)
        try:
            HTTPXClientInstrumentor().instrument()
            logger.debug("HTTPX instrumented for tracing")
        except Exception as e:
            logger.warning(f"Failed to instrument HTTPX: {e}")

        # Instrument SQLAlchemy
        try:
            # Will be called with engine in database initialization
            logger.debug("SQLAlchemy instrumentation prepared")
        except Exception as e:
            logger.warning(f"Failed to prepare SQLAlchemy instrumentation: {e}")

        # Instrument Redis
        try:
            RedisInstrumentor().instrument()
            logger.debug("Redis instrumented for tracing")
        except Exception as e:
            logger.warning(f"Failed to instrument Redis: {e}")

        # Instrument Psycopg2 (PostgreSQL)
        try:
            Psycopg2Instrumentor().instrument()
            logger.debug("Psycopg2 instrumented for tracing")
        except Exception as e:
            logger.warning(f"Failed to instrument Psycopg2: {e}")

    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application.

        Args:
            app: FastAPI application instance
        """
        if not self.initialized:
            logger.warning("Telemetry not initialized, skipping FastAPI instrumentation")
            return

        try:
            FastAPIInstrumentor.instrument_app(
                app,
                excluded_urls="health,/metrics,/docs,/openapi.json",
                server_request_hook=self._server_request_hook,
                client_request_hook=self._client_request_hook,
                client_response_hook=self._client_response_hook,
            )
            logger.info("FastAPI application instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")

    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine.

        Args:
            engine: SQLAlchemy engine instance
        """
        if not self.initialized:
            logger.warning("Telemetry not initialized, skipping SQLAlchemy instrumentation")
            return

        try:
            SQLAlchemyInstrumentor().instrument(
                engine=engine,
                enable_commenter=True,
                commenter_options={
                    "opentelemetry_values": True,
                },
            )
            logger.info("SQLAlchemy engine instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}")

    def _server_request_hook(self, span, scope):
        """Hook to add custom attributes to server request spans."""
        if span and scope:
            # Add custom attributes
            span.set_attribute(
                "http.user_agent", scope.get("headers", {}).get(b"user-agent", [b""])[0].decode()
            )
            span.set_attribute(
                "http.real_ip", scope.get("headers", {}).get(b"x-real-ip", [b""])[0].decode()
            )
            span.set_attribute(
                "app.request_id", scope.get("headers", {}).get(b"x-request-id", [b""])[0].decode()
            )

    def _client_request_hook(self, span, request):
        """Hook to add custom attributes to client request spans."""
        if span and request:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("http.request.url", str(request.url))

    def _client_response_hook(self, span, request, response):
        """Hook to add custom attributes to client response spans."""
        if span and response:
            span.set_attribute("http.response.status_code", response.status_code)

    def create_custom_metrics(self):
        """Create custom metrics for the application."""
        if not self.meter:
            logger.warning("Meter not initialized, cannot create custom metrics")
            return {}

        # Create custom metrics
        metrics_dict = {
            "request_counter": self.meter.create_counter(
                name="toolboxai_requests_total", description="Total number of requests", unit="1"
            ),
            "request_duration": self.meter.create_histogram(
                name="toolboxai_request_duration",
                description="Request duration in seconds",
                unit="s",
            ),
            "active_users": self.meter.create_up_down_counter(
                name="toolboxai_active_users", description="Number of active users", unit="1"
            ),
            "agent_tasks": self.meter.create_counter(
                name="toolboxai_agent_tasks_total",
                description="Total number of agent tasks processed",
                unit="1",
            ),
            "database_connections": self.meter.create_observable_gauge(
                name="toolboxai_db_connections",
                callbacks=[self._get_db_connections],
                description="Number of active database connections",
                unit="1",
            ),
        }

        return metrics_dict

    def _get_db_connections(self, options):
        """Callback to get current database connections."""
        # This would query the actual database connection pool
        # For now, return a mock value
        return [{"value": 5, "attributes": {"pool": "main"}}]

    def shutdown(self):
        """Shutdown telemetry and flush all pending data."""
        if not self.initialized:
            return

        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()
            if self.meter_provider:
                self.meter_provider.shutdown()
            logger.info("Telemetry shutdown complete")
        except Exception as e:
            logger.error(f"Error during telemetry shutdown: {e}")
        finally:
            self.initialized = False


# Global telemetry manager instance
telemetry_manager = TelemetryManager()


def get_telemetry_manager() -> TelemetryManager:
    """Get the global telemetry manager instance."""
    return telemetry_manager
