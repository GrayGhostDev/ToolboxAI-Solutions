"""
Advanced Observability with OpenTelemetry

Provides comprehensive distributed tracing, metrics, and logging correlation
for the entire load balancing infrastructure.
"""

import asyncio
import inspect
import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

from opentelemetry import baggage, context, metrics, trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import Meter
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer

# GRPC exporters moved to lazy imports inside methods to avoid module-level crashes
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

# Optional Jaeger exporter (deprecated but still supported)
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
    JaegerExporter = None
    logger.warning(
        "Jaeger exporter not available. Install 'opentelemetry-exporter-jaeger' if needed."
    )

T = TypeVar("T")


@dataclass
class TelemetryConfig:
    """Configuration for telemetry system"""

    service_name: str
    service_version: str = "1.0.0"
    environment: str = "production"

    # Tracing
    enable_tracing: bool = True
    jaeger_endpoint: str | None = None
    otlp_endpoint: str | None = None
    sampling_rate: float = 0.1

    # Metrics
    enable_metrics: bool = True
    metrics_export_interval: int = 60

    # Logging
    enable_log_correlation: bool = True
    log_level: str = "INFO"

    # Performance
    enable_profiling: bool = True
    profile_sample_rate: float = 0.01

    # Custom attributes
    custom_attributes: dict[str, Any] = field(default_factory=dict)

    # Feature flags
    trace_database_queries: bool = True
    trace_cache_operations: bool = True
    trace_http_headers: bool = False
    trace_request_body: bool = False

    # Sampling strategies
    head_sampling: bool = True
    tail_sampling: bool = False
    adaptive_sampling: bool = True


class AdaptiveSampler(sampling.Sampler):
    """Adaptive sampling based on system load and error rates"""

    def __init__(
        self,
        base_rate: float = 0.1,
        error_rate: float = 1.0,
        high_latency_threshold_ms: float = 1000,
        high_latency_rate: float = 0.5,
    ):
        self.base_rate = base_rate
        self.error_rate = error_rate
        self.high_latency_threshold_ms = high_latency_threshold_ms
        self.high_latency_rate = high_latency_rate
        self.request_count = 0
        self.error_count = 0

    def should_sample(
        self,
        parent_context: context.Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind,
        attributes: dict[str, Any] = None,
        links: list = None,
    ) -> sampling.SamplingResult:
        """Determine if span should be sampled"""

        # Always sample if parent was sampled
        parent_span_context = trace.get_current_span(parent_context).get_span_context()
        if (
            parent_span_context
            and parent_span_context.is_valid
            and parent_span_context.trace_flags.sampled
        ):
            return sampling.SamplingResult(
                decision=sampling.Decision.RECORD_AND_SAMPLE, attributes=attributes
            )

        # Sample errors at higher rate
        if attributes and attributes.get("error", False):
            if trace_id % int(1 / self.error_rate) == 0:
                return sampling.SamplingResult(
                    decision=sampling.Decision.RECORD_AND_SAMPLE, attributes=attributes
                )

        # Sample high latency operations
        if attributes and attributes.get("latency_ms", 0) > self.high_latency_threshold_ms:
            if trace_id % int(1 / self.high_latency_rate) == 0:
                return sampling.SamplingResult(
                    decision=sampling.Decision.RECORD_AND_SAMPLE, attributes=attributes
                )

        # Base sampling
        if trace_id % int(1 / self.base_rate) == 0:
            return sampling.SamplingResult(
                decision=sampling.Decision.RECORD_AND_SAMPLE, attributes=attributes
            )

        return sampling.SamplingResult(decision=sampling.Decision.DROP, attributes=attributes)

    def get_description(self) -> str:
        return f"AdaptiveSampler(base={self.base_rate}, error={self.error_rate})"


class TelemetryManager:
    """Manages OpenTelemetry instrumentation and tracing"""

    def __init__(self, config: TelemetryConfig):
        self.config = config
        self.tracer: Tracer | None = None
        self.meter: Meter | None = None
        self.resource: Resource | None = None
        self.propagator = TraceContextTextMapPropagator()

        # Metrics collectors
        self.request_counter = None
        self.request_duration = None
        self.error_counter = None
        self.active_requests = None

        # Performance profiling
        self.profile_data: dict[str, list[float]] = {}

    def initialize(self):
        """Initialize telemetry providers"""

        # Create resource
        self.resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.environment,
                **self.config.custom_attributes,
            }
        )

        if self.config.enable_tracing:
            self._initialize_tracing()

        if self.config.enable_metrics:
            self._initialize_metrics()

        if self.config.enable_log_correlation:
            self._initialize_logging()

        # Auto-instrument libraries
        self._auto_instrument()

        logger.info(f"Telemetry initialized for {self.config.service_name}")

    def _initialize_tracing(self):
        """Initialize tracing provider and exporters"""

        # Create sampler
        if self.config.adaptive_sampling:
            sampler = AdaptiveSampler(base_rate=self.config.sampling_rate)
        elif self.config.head_sampling:
            sampler = sampling.TraceIdRatioBased(self.config.sampling_rate)
        else:
            sampler = sampling.AlwaysOn()

        # Create tracer provider
        tracer_provider = TracerProvider(resource=self.resource, sampler=sampler)

        # Add exporters
        if self.config.jaeger_endpoint and JAEGER_AVAILABLE:
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_endpoint.split(":")[0],
                agent_port=(
                    int(self.config.jaeger_endpoint.split(":")[1])
                    if ":" in self.config.jaeger_endpoint
                    else 6831
                ),
                collector_endpoint=None,
                username=None,
                password=None,
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        if self.config.otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                otlp_exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint, insecure=True)
                tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except Exception as e:
                logger.warning(f"OTLP GRPC trace exporter failed: {e}")

        # Console exporter for debugging
        if logger.isEnabledFor(logging.DEBUG):
            tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        self.tracer = trace.get_tracer(self.config.service_name, self.config.service_version)

    def _initialize_metrics(self):
        """Initialize metrics provider and collectors"""

        # Create metric reader and exporter
        if self.config.otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                    OTLPMetricExporter,
                )

                metric_exporter = OTLPMetricExporter(
                    endpoint=self.config.otlp_endpoint, insecure=True
                )
            except Exception as e:
                logger.warning(f"OTLP GRPC metric exporter failed, using console: {e}")
                metric_exporter = ConsoleMetricExporter()
        else:
            metric_exporter = ConsoleMetricExporter()

        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=self.config.metrics_export_interval * 1000,
        )

        # Create meter provider
        meter_provider = MeterProvider(resource=self.resource, metric_readers=[metric_reader])

        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
        self.meter = metrics.get_meter(self.config.service_name, self.config.service_version)

        # Create common metrics
        self.request_counter = self.meter.create_counter(
            "http_requests_total", description="Total number of HTTP requests", unit="1"
        )

        self.request_duration = self.meter.create_histogram(
            "http_request_duration_seconds", description="HTTP request duration", unit="s"
        )

        self.error_counter = self.meter.create_counter(
            "http_errors_total", description="Total number of HTTP errors", unit="1"
        )

        self.active_requests = self.meter.create_up_down_counter(
            "http_active_requests", description="Number of active HTTP requests", unit="1"
        )

    def _initialize_logging(self):
        """Initialize log correlation with traces"""
        LoggingInstrumentor().instrument()

    def _auto_instrument(self):
        """Auto-instrument common libraries"""

        # HTTP clients
        HTTPXClientInstrumentor().instrument()

        # Databases
        if self.config.trace_database_queries:
            SQLAlchemyInstrumentor().instrument()
            Psycopg2Instrumentor().instrument()

        # Cache
        if self.config.trace_cache_operations:
            RedisInstrumentor().instrument()

    @contextmanager
    def trace_operation(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] = None,
        record_exception: bool = True,
    ):
        """Context manager for tracing operations"""

        if not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name, kind=kind, attributes=attributes or {}, record_exception=record_exception
        ) as span:
            start_time = time.time()

            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                if record_exception:
                    span.record_exception(e)
                raise
            finally:
                # Record duration
                duration = time.time() - start_time
                span.set_attribute("duration_ms", duration * 1000)

                # Update metrics
                if self.request_duration:
                    self.request_duration.record(duration, attributes={"operation": name})

    @asynccontextmanager
    async def trace_async_operation(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] = None,
        record_exception: bool = True,
    ):
        """Async context manager for tracing operations"""

        if not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(
            name, kind=kind, attributes=attributes or {}, record_exception=record_exception
        ) as span:
            start_time = time.time()

            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                if record_exception:
                    span.record_exception(e)
                raise
            finally:
                # Record duration
                duration = time.time() - start_time
                span.set_attribute("duration_ms", duration * 1000)

                # Update metrics
                if self.request_duration:
                    self.request_duration.record(duration, attributes={"operation": name})

    def trace_function(
        self,
        name: str | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] = None,
    ):
        """Decorator for tracing functions"""

        def decorator(func: Callable) -> Callable:
            operation_name = name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self.trace_async_operation(
                    operation_name, kind=kind, attributes=attributes
                ) as span:
                    # Add function arguments as attributes
                    if span and self.config.trace_request_body:
                        sig = inspect.signature(func)
                        bound = sig.bind(*args, **kwargs)
                        bound.apply_defaults()

                        for param, value in bound.arguments.items():
                            if param not in ["self", "cls"]:
                                span.set_attribute(f"arg.{param}", str(value)[:100])

                    result = await func(*args, **kwargs)

                    # Add result as attribute
                    if span and result is not None:
                        span.set_attribute("result.type", type(result).__name__)

                    return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.trace_operation(operation_name, kind=kind, attributes=attributes) as span:
                    # Add function arguments as attributes
                    if span and self.config.trace_request_body:
                        sig = inspect.signature(func)
                        bound = sig.bind(*args, **kwargs)
                        bound.apply_defaults()

                        for param, value in bound.arguments.items():
                            if param not in ["self", "cls"]:
                                span.set_attribute(f"arg.{param}", str(value)[:100])

                    result = func(*args, **kwargs)

                    # Add result as attribute
                    if span and result is not None:
                        span.set_attribute("result.type", type(result).__name__)

                    return result

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def inject_context(self, headers: dict[str, str]):
        """Inject trace context into headers for propagation"""
        inject(headers)

    def extract_context(self, headers: dict[str, str]):
        """Extract trace context from headers"""
        return extract(headers)

    def record_metric(
        self,
        name: str,
        value: float,
        attributes: dict[str, Any] = None,
        metric_type: str = "counter",
    ):
        """Record a custom metric"""

        if not self.meter:
            return

        # Get or create metric instrument
        if metric_type == "counter":
            metric = self.meter.create_counter(
                name, description=f"Custom counter: {name}", unit="1"
            )
            metric.add(value, attributes=attributes)
        elif metric_type == "histogram":
            metric = self.meter.create_histogram(
                name, description=f"Custom histogram: {name}", unit="1"
            )
            metric.record(value, attributes=attributes)
        elif metric_type == "gauge":
            # OpenTelemetry doesn't have direct gauge support
            # Use observable gauge instead
            metric = self.meter.create_observable_gauge(
                name,
                description=f"Custom gauge: {name}",
                unit="1",
                callback=lambda x: [(value, attributes)],
            )

    def create_baggage(self, key: str, value: str):
        """Create baggage item for context propagation"""
        return baggage.set_baggage(key, value)

    def get_baggage(self, key: str) -> str | None:
        """Get baggage item from context"""
        return baggage.get_baggage(key)

    def profile_operation(self, name: str):
        """Decorator for profiling operations"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.config.enable_profiling:
                    return await func(*args, **kwargs)

                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()

                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.perf_counter() - start_time
                    memory_delta = self._get_memory_usage() - start_memory

                    # Store profile data
                    if name not in self.profile_data:
                        self.profile_data[name] = []

                    self.profile_data[name].append(
                        {
                            "duration": duration,
                            "memory_delta": memory_delta,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    # Keep only last 1000 samples
                    if len(self.profile_data[name]) > 1000:
                        self.profile_data[name] = self.profile_data[name][-1000:]

                    # Add to current span if exists
                    current_span = trace.get_current_span()
                    if current_span:
                        current_span.set_attribute(f"profile.{name}.duration_ms", duration * 1000)
                        current_span.set_attribute(
                            f"profile.{name}.memory_delta_mb", memory_delta / 1024 / 1024
                        )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.config.enable_profiling:
                    return func(*args, **kwargs)

                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.perf_counter() - start_time
                    memory_delta = self._get_memory_usage() - start_memory

                    # Store profile data
                    if name not in self.profile_data:
                        self.profile_data[name] = []

                    self.profile_data[name].append(
                        {
                            "duration": duration,
                            "memory_delta": memory_delta,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    # Keep only last 1000 samples
                    if len(self.profile_data[name]) > 1000:
                        self.profile_data[name] = self.profile_data[name][-1000:]

                    # Add to current span if exists
                    current_span = trace.get_current_span()
                    if current_span:
                        current_span.set_attribute(f"profile.{name}.duration_ms", duration * 1000)
                        current_span.set_attribute(
                            f"profile.{name}.memory_delta_mb", memory_delta / 1024 / 1024
                        )

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        import psutil

        process = psutil.Process()
        return process.memory_info().rss

    def get_profile_summary(self, name: str) -> dict[str, Any]:
        """Get profiling summary for an operation"""

        if name not in self.profile_data or not self.profile_data[name]:
            return {}

        data = self.profile_data[name]
        durations = [d["duration"] for d in data]
        memory_deltas = [d["memory_delta"] for d in data]

        import statistics

        return {
            "count": len(data),
            "duration": {
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "stdev": statistics.stdev(durations) if len(durations) > 1 else 0,
                "min": min(durations),
                "max": max(durations),
            },
            "memory": {
                "mean": statistics.mean(memory_deltas),
                "median": statistics.median(memory_deltas),
                "stdev": statistics.stdev(memory_deltas) if len(memory_deltas) > 1 else 0,
                "min": min(memory_deltas),
                "max": max(memory_deltas),
            },
        }

    def shutdown(self):
        """Shutdown telemetry providers"""

        if self.tracer:
            trace.get_tracer_provider().shutdown()

        if self.meter:
            metrics.get_meter_provider().shutdown()

        logger.info("Telemetry shutdown complete")


# Custom instrumentations for load balancing components


class LoadBalancerInstrumentor:
    """Custom instrumentation for load balancing components"""

    def __init__(self, telemetry: TelemetryManager):
        self.telemetry = telemetry

    def instrument_circuit_breaker(self, circuit_breaker):
        """Add tracing to circuit breaker"""

        original_call = circuit_breaker.call

        @wraps(original_call)
        async def traced_call(*args, **kwargs):
            async with self.telemetry.trace_async_operation(
                "circuit_breaker.call",
                attributes={
                    "breaker.name": circuit_breaker.name,
                    "breaker.state": circuit_breaker.state.value,
                },
            ) as span:
                try:
                    result = await original_call(*args, **kwargs)
                    if span:
                        span.set_attribute("breaker.success", True)
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("breaker.success", False)
                        span.set_attribute("breaker.error", str(e))
                    raise

        circuit_breaker.call = traced_call

    def instrument_rate_limiter(self, rate_limiter):
        """Add tracing to rate limiter"""

        original_check = rate_limiter.check_rate_limit

        @wraps(original_check)
        async def traced_check(identifier: str, endpoint: str = None, **kwargs):
            async with self.telemetry.trace_async_operation(
                "rate_limiter.check", attributes={"identifier": identifier, "endpoint": endpoint}
            ) as span:
                result = await original_check(identifier, endpoint, **kwargs)

                if span:
                    span.set_attribute("allowed", result.allowed)
                    span.set_attribute("remaining", result.remaining)
                    if result.retry_after:
                        span.set_attribute("retry_after", result.retry_after)

                return result

        rate_limiter.check_rate_limit = traced_check

    def instrument_database_router(self, router):
        """Add tracing to database replica router"""

        original_get_session = router.get_session

        @asynccontextmanager
        async def traced_get_session(consistency=None, session_id=None, for_write=False):
            async with self.telemetry.trace_async_operation(
                "database_router.get_session",
                attributes={
                    "consistency": consistency.value if consistency else None,
                    "for_write": for_write,
                    "session_id": session_id,
                },
            ) as span:
                async with original_get_session(consistency, session_id, for_write) as session:
                    if span and "routed_to" in session.info:
                        span.set_attribute("routed_to", session.info["routed_to"])

                    yield session

        router.get_session = traced_get_session

    def instrument_cache(self, cache):
        """Add tracing to edge cache"""

        original_get = cache.get
        original_set = cache.set

        @wraps(original_get)
        async def traced_get(key: str, tier=None, strategy=None):
            async with self.telemetry.trace_async_operation(
                "cache.get",
                attributes={
                    "key": key[:50],  # Truncate key for security
                    "tier": tier.value if tier else None,
                    "strategy": strategy.value if strategy else None,
                },
            ) as span:
                result = await original_get(key, tier, strategy)

                if span:
                    span.set_attribute("hit", result is not None)
                    if result:
                        span.set_attribute("size_bytes", result.size_bytes)

                return result

        @wraps(original_set)
        async def traced_set(key: str, entry, tier=None, config=None):
            async with self.telemetry.trace_async_operation(
                "cache.set", attributes={"key": key[:50], "tier": tier.value if tier else None}
            ) as span:
                result = await original_set(key, entry, tier, config)

                if span:
                    span.set_attribute("success", result)

                return result

        cache.get = traced_get
        cache.set = traced_set


# Metrics Collector for backward compatibility
class MetricsCollector:
    """Legacy metrics collector for backward compatibility"""

    def __init__(self):
        self._metrics = {}
        logger.info("MetricsCollector initialized (compatibility mode)")

    def record_metric(self, name: str, value: float, labels: dict[str, str] = None):
        """Record a metric"""
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(
            {"value": value, "labels": labels or {}, "timestamp": time.time()}
        )

    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics"""
        return self._metrics


# Global telemetry instance
_telemetry_manager: TelemetryManager | None = None
_metrics_collector: MetricsCollector | None = None


def init_telemetry(config: TelemetryConfig) -> TelemetryManager:
    """Initialize global telemetry manager"""
    global _telemetry_manager
    _telemetry_manager = TelemetryManager(config)
    _telemetry_manager.initialize()
    return _telemetry_manager


def get_telemetry() -> TelemetryManager | None:
    """Get global telemetry manager"""
    return _telemetry_manager


def shutdown_telemetry():
    """Shutdown global telemetry manager"""
    if _telemetry_manager:
        _telemetry_manager.shutdown()


# Create default instances for backward compatibility
try:
    # Initialize with minimal config if environment variables are available
    import os

    default_config = TelemetryConfig(
        service_name=os.getenv("SERVICE_NAME", "toolboxai-backend"),
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
        environment=os.getenv("ENVIRONMENT", "development"),
        enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
        enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
    )

    telemetry_manager = TelemetryManager(default_config)
    metrics_collector = MetricsCollector()

    logger.info("Default telemetry instances created (not initialized until explicitly called)")

except Exception as e:
    logger.warning(f"Could not create default telemetry instances: {e}")
    telemetry_manager = None
    metrics_collector = MetricsCollector()


# Export all public APIs
__all__ = [
    "TelemetryConfig",
    "TelemetryManager",
    "MetricsCollector",
    "LoadBalancerInstrumentor",
    "AdaptiveSampler",
    "init_telemetry",
    "get_telemetry",
    "shutdown_telemetry",
    "telemetry_manager",
    "metrics_collector",
]
