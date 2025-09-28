"""
Custom Instrumentation for Load Balancing Components

Integrates OpenTelemetry with all custom load balancing components
to provide comprehensive distributed tracing.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace, baggage, context
from opentelemetry.trace import Span, StatusCode, Status
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from apps.backend.core.observability.telemetry import (
    TelemetryManager,
    LoadBalancerInstrumentor,
    get_telemetry,
)
from apps.backend.core.circuit_breaker import CircuitBreaker, get_circuit_breaker
from apps.backend.core.rate_limiter import RateLimiter
from database.replica_router import ReplicaRouter, get_replica_router
from apps.backend.core.edge_cache import EdgeCache
from apps.backend.core.websocket_cluster import WebSocketCluster, get_websocket_cluster
from apps.backend.core.global_load_balancer import GlobalLoadBalancer

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for comprehensive observability"""

    def __init__(
        self,
        app,
        telemetry: TelemetryManager,
        track_user_id: bool = True,
        track_session_id: bool = True,
        track_request_body: bool = False,
        track_response_body: bool = False,
    ):
        super().__init__(app)
        self.telemetry = telemetry
        self.track_user_id = track_user_id
        self.track_session_id = track_session_id
        self.track_request_body = track_request_body
        self.track_response_body = track_response_body

        # Metrics
        self.request_counter = telemetry.meter.create_counter(
            "http_requests", description="HTTP requests", unit="1"
        )

        self.request_duration = telemetry.meter.create_histogram(
            "http_request_duration", description="HTTP request duration", unit="ms"
        )

        self.response_size = telemetry.meter.create_histogram(
            "http_response_size", description="HTTP response size", unit="bytes"
        )

    async def dispatch(self, request: Request, call_next):
        """Process request with observability"""

        start_time = time.perf_counter()

        # Extract trace context from headers
        trace_context = self.telemetry.extract_context(dict(request.headers))

        # Start span
        with self.telemetry.tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            context=trace_context,
            kind=trace.SpanKind.SERVER,
        ) as span:
            # Add request attributes
            self._add_request_attributes(span, request)

            # Extract identifiers
            user_id = None
            session_id = None

            if self.track_user_id:
                user_id = (
                    request.headers.get("X-User-ID") or request.session.get("user_id")
                    if hasattr(request, "session")
                    else None
                )
                if user_id:
                    span.set_attribute("user.id", user_id)
                    baggage.set_baggage("user.id", user_id)

            if self.track_session_id:
                session_id = (
                    request.headers.get("X-Session-ID") or request.session.get("session_id")
                    if hasattr(request, "session")
                    else None
                )
                if session_id:
                    span.set_attribute("session.id", session_id)
                    baggage.set_baggage("session.id", session_id)

            # Track request body if enabled
            if self.track_request_body and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    span.set_attribute("http.request.body.size", len(body))
                    # Only log small bodies
                    if len(body) < 1024:
                        span.set_attribute("http.request.body", body.decode()[:500])
                except:
                    pass

            try:
                # Call next middleware/handler
                response = await call_next(request)

                # Add response attributes
                self._add_response_attributes(span, response)

                # Track response body if enabled
                if self.track_response_body and hasattr(response, "body"):
                    span.set_attribute("http.response.body.size", len(response.body))

                # Set span status based on response
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                    # Record error metric
                    self.telemetry.error_counter.add(
                        1,
                        attributes={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                        },
                    )
                else:
                    span.set_status(Status(StatusCode.OK))

                return response

            except Exception as e:
                # Record exception
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))

                # Record error metric
                self.telemetry.error_counter.add(
                    1,
                    attributes={
                        "method": request.method,
                        "path": request.url.path,
                        "exception": type(e).__name__,
                    },
                )

                raise

            finally:
                # Record metrics
                duration = (time.perf_counter() - start_time) * 1000

                self.request_counter.add(
                    1,
                    attributes={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code if "response" in locals() else 500,
                    },
                )

                self.request_duration.record(
                    duration, attributes={"method": request.method, "path": request.url.path}
                )

                if "response" in locals() and hasattr(response, "headers"):
                    content_length = response.headers.get("content-length")
                    if content_length:
                        self.response_size.record(
                            int(content_length),
                            attributes={"method": request.method, "path": request.url.path},
                        )

    def _add_request_attributes(self, span: Span, request: Request):
        """Add request attributes to span"""

        span.set_attribute(SpanAttributes.HTTP_METHOD, request.method)
        span.set_attribute(SpanAttributes.HTTP_URL, str(request.url))
        span.set_attribute(SpanAttributes.HTTP_TARGET, request.url.path)
        span.set_attribute(SpanAttributes.HTTP_SCHEME, request.url.scheme)
        span.set_attribute(SpanAttributes.HTTP_HOST, request.url.hostname)
        span.set_attribute(SpanAttributes.NET_HOST_PORT, request.url.port or 80)

        # Add headers if configured
        if self.telemetry.config.trace_http_headers:
            for name, value in request.headers.items():
                if name.lower() not in ["authorization", "cookie"]:
                    span.set_attribute(f"http.request.header.{name.lower()}", value[:100])

        # Add client info
        client_host = request.client.host if request.client else None
        if client_host:
            span.set_attribute(SpanAttributes.HTTP_CLIENT_IP, client_host)

    def _add_response_attributes(self, span: Span, response: Response):
        """Add response attributes to span"""

        span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)

        # Add response headers if configured
        if self.telemetry.config.trace_http_headers:
            for name, value in response.headers.items():
                if name.lower() not in ["set-cookie"]:
                    span.set_attribute(f"http.response.header.{name.lower()}", value[:100])


class ComponentInstrumentor:
    """Instruments all load balancing components"""

    def __init__(self, telemetry: TelemetryManager):
        self.telemetry = telemetry
        self.lb_instrumentor = LoadBalancerInstrumentor(telemetry)

    def instrument_all(self):
        """Instrument all components"""

        # Instrument circuit breakers
        self._instrument_circuit_breakers()

        # Instrument rate limiters
        self._instrument_rate_limiters()

        # Instrument database router
        self._instrument_database_router()

        # Instrument caches
        self._instrument_caches()

        # Instrument WebSocket cluster
        self._instrument_websocket_cluster()

        logger.info("All components instrumented for observability")

    def _instrument_circuit_breakers(self):
        """Instrument all circuit breakers"""

        # Get all circuit breakers
        breaker_names = ["database", "api", "external_service", "redis"]

        for name in breaker_names:
            breaker = get_circuit_breaker(name)
            if breaker:
                self.lb_instrumentor.instrument_circuit_breaker(breaker)
                logger.debug(f"Instrumented circuit breaker: {name}")

    def _instrument_rate_limiters(self):
        """Instrument rate limiting"""

        # This would instrument the global rate limiter
        # Implementation depends on your rate limiter setup
        pass

    def _instrument_database_router(self):
        """Instrument database replica router"""

        router = get_replica_router()
        if router:
            self.lb_instrumentor.instrument_database_router(router)
            logger.debug("Instrumented database router")

    def _instrument_caches(self):
        """Instrument edge caches"""

        # This would instrument your cache instances
        # Implementation depends on your cache setup
        pass

    def _instrument_websocket_cluster(self):
        """Instrument WebSocket cluster"""

        cluster = get_websocket_cluster()
        if cluster:
            self._add_websocket_tracing(cluster)
            logger.debug("Instrumented WebSocket cluster")

    def _add_websocket_tracing(self, cluster: WebSocketCluster):
        """Add tracing to WebSocket cluster operations"""

        # Trace connection handling
        original_connect = cluster.connect

        @wraps(original_connect)
        async def traced_connect(websocket, session_id=None, user_id=None, metadata=None):
            async with self.telemetry.trace_async_operation(
                "websocket.connect",
                kind=trace.SpanKind.SERVER,
                attributes={
                    "session_id": session_id,
                    "user_id": user_id,
                    "node_id": cluster.node_id,
                },
            ) as span:
                connection_id = await original_connect(websocket, session_id, user_id, metadata)

                if span:
                    span.set_attribute("connection_id", connection_id)

                return connection_id

        cluster.connect = traced_connect

        # Trace message handling
        original_send = cluster.send_message

        @wraps(original_send)
        async def traced_send(connection_id: str, message: Dict[str, Any]):
            async with self.telemetry.trace_async_operation(
                "websocket.send_message",
                attributes={
                    "connection_id": connection_id,
                    "message_type": message.get("type", "unknown"),
                },
            ):
                await original_send(connection_id, message)

        cluster.send_message = traced_send

        # Trace room operations
        original_join_room = cluster.join_room

        @wraps(original_join_room)
        async def traced_join_room(connection_id: str, room: str):
            async with self.telemetry.trace_async_operation(
                "websocket.join_room", attributes={"connection_id": connection_id, "room": room}
            ):
                await original_join_room(connection_id, room)

        cluster.join_room = traced_join_room


class TraceContextPropagator:
    """Propagates trace context across service boundaries"""

    def __init__(self, telemetry: TelemetryManager):
        self.telemetry = telemetry

    def inject_to_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Inject trace context into message"""

        headers = {}
        self.telemetry.inject_context(headers)

        message["_trace_context"] = headers
        return message

    def extract_from_message(self, message: Dict[str, Any]) -> context.Context:
        """Extract trace context from message"""

        if "_trace_context" in message:
            return self.telemetry.extract_context(message["_trace_context"])

        return context.get_current()

    async def propagate_to_service(
        self, service_url: str, headers: Dict[str, str] = None
    ) -> Dict[str, str]:
        """Propagate trace context to another service"""

        if headers is None:
            headers = {}

        # Inject current context
        self.telemetry.inject_context(headers)

        # Add baggage items
        user_id = baggage.get_baggage("user.id")
        if user_id:
            headers["X-User-ID"] = user_id

        session_id = baggage.get_baggage("session.id")
        if session_id:
            headers["X-Session-ID"] = session_id

        return headers


class PerformanceProfiler:
    """Advanced performance profiling with OpenTelemetry"""

    def __init__(self, telemetry: TelemetryManager):
        self.telemetry = telemetry
        self.profile_spans: Dict[str, List[Dict]] = {}

    def profile_endpoint(self, pattern: str = None):
        """Decorator for profiling FastAPI endpoints"""

        def decorator(func: Callable) -> Callable:
            endpoint_name = f"{func.__module__}.{func.__name__}"

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Start profiling span
                async with self.telemetry.trace_async_operation(
                    f"profile.{endpoint_name}",
                    attributes={"profile.type": "endpoint", "profile.pattern": pattern},
                ) as span:
                    # CPU profiling
                    import cProfile

                    profiler = cProfile.Profile()
                    profiler.enable()

                    # Memory profiling
                    import tracemalloc

                    tracemalloc.start()

                    start_time = time.perf_counter()

                    try:
                        result = await func(*args, **kwargs)

                        # Stop profiling
                        profiler.disable()
                        current, peak = tracemalloc.get_traced_memory()
                        tracemalloc.stop()

                        duration = time.perf_counter() - start_time

                        # Add profile data to span
                        if span:
                            span.set_attribute("profile.duration_ms", duration * 1000)
                            span.set_attribute("profile.memory_current_mb", current / 1024 / 1024)
                            span.set_attribute("profile.memory_peak_mb", peak / 1024 / 1024)

                            # Extract top functions
                            import io
                            import pstats

                            s = io.StringIO()
                            ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
                            ps.print_stats(10)
                            span.set_attribute("profile.top_functions", s.getvalue()[:1000])

                        # Store for analysis
                        if endpoint_name not in self.profile_spans:
                            self.profile_spans[endpoint_name] = []

                        self.profile_spans[endpoint_name].append(
                            {
                                "timestamp": time.time(),
                                "duration": duration,
                                "memory_current": current,
                                "memory_peak": peak,
                            }
                        )

                        # Keep only last 100 profiles
                        if len(self.profile_spans[endpoint_name]) > 100:
                            self.profile_spans[endpoint_name] = self.profile_spans[endpoint_name][
                                -100:
                            ]

                        return result

                    except Exception as e:
                        profiler.disable()
                        tracemalloc.stop()
                        raise

            return wrapper

        return decorator

    def get_profile_report(self, endpoint: str = None) -> Dict[str, Any]:
        """Get profiling report"""

        if endpoint:
            if endpoint not in self.profile_spans:
                return {"error": "No profile data for endpoint"}

            data = self.profile_spans[endpoint]
        else:
            # Aggregate all endpoints
            data = []
            for endpoint_data in self.profile_spans.values():
                data.extend(endpoint_data)

        if not data:
            return {"error": "No profile data available"}

        durations = [d["duration"] for d in data]
        memory_current = [d["memory_current"] for d in data]
        memory_peak = [d["memory_peak"] for d in data]

        import statistics

        return {
            "sample_count": len(data),
            "duration_stats": {
                "mean_ms": statistics.mean(durations) * 1000,
                "median_ms": statistics.median(durations) * 1000,
                "p95_ms": (
                    statistics.quantiles(durations, n=20)[18] * 1000 if len(durations) > 20 else 0
                ),
                "p99_ms": (
                    statistics.quantiles(durations, n=100)[98] * 1000 if len(durations) > 100 else 0
                ),
                "min_ms": min(durations) * 1000,
                "max_ms": max(durations) * 1000,
            },
            "memory_stats": {
                "mean_current_mb": statistics.mean(memory_current) / 1024 / 1024,
                "mean_peak_mb": statistics.mean(memory_peak) / 1024 / 1024,
                "max_peak_mb": max(memory_peak) / 1024 / 1024,
            },
            "endpoints": list(self.profile_spans.keys()) if not endpoint else [endpoint],
        }


# FastAPI integration
def setup_fastapi_observability(
    app: FastAPI, telemetry: TelemetryManager, instrument_components: bool = True
):
    """Setup comprehensive observability for FastAPI application"""

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Add custom middleware
    app.add_middleware(
        ObservabilityMiddleware,
        telemetry=telemetry,
        track_user_id=True,
        track_session_id=True,
        track_request_body=telemetry.config.trace_request_body,
        track_response_body=False,
    )

    # Instrument components
    if instrument_components:
        instrumentor = ComponentInstrumentor(telemetry)
        instrumentor.instrument_all()

    # Create profiler
    profiler = PerformanceProfiler(telemetry)

    # Add observability endpoints
    @app.get("/observability/traces")
    async def get_traces():
        """Get recent traces (if using in-memory storage)"""
        return {"message": "Traces are exported to configured backend"}

    @app.get("/observability/metrics")
    async def get_metrics():
        """Get current metrics"""
        return {
            "request_count": (
                telemetry.request_counter._value
                if hasattr(telemetry.request_counter, "_value")
                else 0
            ),
            "error_count": (
                telemetry.error_counter._value if hasattr(telemetry.error_counter, "_value") else 0
            ),
            "active_requests": (
                telemetry.active_requests._value
                if hasattr(telemetry.active_requests, "_value")
                else 0
            ),
        }

    @app.get("/observability/profile")
    async def get_profile_data(endpoint: str = None):
        """Get profiling data"""
        return profiler.get_profile_report(endpoint)

    @app.get("/observability/health")
    async def observability_health():
        """Check observability system health"""
        return {
            "tracing": telemetry.tracer is not None,
            "metrics": telemetry.meter is not None,
            "logging": telemetry.config.enable_log_correlation,
            "profiling": telemetry.config.enable_profiling,
        }

    logger.info("FastAPI observability setup complete")


# Correlation ID middleware
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to all requests for tracing"""

    async def dispatch(self, request: Request, call_next):
        # Get or create correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")

        if not correlation_id:
            import uuid

            correlation_id = str(uuid.uuid4())

        # Add to baggage for propagation
        baggage.set_baggage("correlation_id", correlation_id)

        # Add to current span
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute("correlation_id", correlation_id)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id

        return response
