"""
Trace Correlation System for FastAPI Application

Provides W3C Trace Context propagation and correlation tracking across
HTTP requests, WebSocket connections, and async tasks with minimal overhead.
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, Any, Optional, List, Set, Callable, TypeVar, Union
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
import contextvars
import json
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi import Request, Response, WebSocket
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace, context, baggage
from opentelemetry.trace import Tracer, Span, Status, StatusCode, SpanKind
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

# Context variables for correlation tracking
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="")
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
request_type_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_type", default="http"
)

T = TypeVar("T")


@dataclass
class CorrelationContext:
    """Correlation context containing all tracking information"""

    correlation_id: str
    trace_id: str
    span_id: str
    user_id: Optional[str] = None
    request_type: str = "http"
    parent_correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_headers(self) -> Dict[str, str]:
        """Convert context to HTTP headers"""
        headers = {
            "X-Correlation-ID": self.correlation_id,
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
            "X-Request-Type": self.request_type,
        }

        if self.user_id:
            headers["X-User-ID"] = self.user_id
        if self.parent_correlation_id:
            headers["X-Parent-Correlation-ID"] = self.parent_correlation_id
        if self.session_id:
            headers["X-Session-ID"] = self.session_id

        return headers

    def to_baggage(self) -> Dict[str, str]:
        """Convert context to OpenTelemetry baggage"""
        baggage_data = {
            "correlation.id": self.correlation_id,
            "correlation.type": self.request_type,
        }

        if self.user_id:
            baggage_data["correlation.user_id"] = self.user_id
        if self.session_id:
            baggage_data["correlation.session_id"] = self.session_id

        return baggage_data

    def to_log_extra(self) -> Dict[str, Any]:
        """Convert context to logging extra fields"""
        return {
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "request_type": self.request_type,
            "session_id": self.session_id,
            "client_ip": self.client_ip,
        }


class CorrelationStore:
    """Thread-safe store for correlation contexts"""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, CorrelationContext] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()

        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup()

    def _start_cleanup(self):
        """Start background cleanup task"""

        def cleanup_worker():
            while True:
                try:
                    self._cleanup_expired()
                    time.sleep(300)  # Cleanup every 5 minutes
                except Exception as e:
                    logger.error(f"Error in correlation store cleanup: {e}")

        executor = ThreadPoolExecutor(max_workers=1)
        self._cleanup_task = executor.submit(cleanup_worker)

    def _cleanup_expired(self):
        """Remove expired correlation contexts"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for correlation_id, access_time in self._access_times.items():
                if current_time - access_time > self.ttl_seconds:
                    expired_keys.append(correlation_id)

            for key in expired_keys:
                self._store.pop(key, None)
                self._access_times.pop(key, None)

            # Also enforce max size
            if len(self._store) > self.max_size:
                # Remove oldest accessed items
                sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])
                to_remove = len(self._store) - self.max_size

                for correlation_id, _ in sorted_items[:to_remove]:
                    self._store.pop(correlation_id, None)
                    self._access_times.pop(correlation_id, None)

    def store(self, context: CorrelationContext):
        """Store a correlation context"""
        with self._lock:
            self._store[context.correlation_id] = context
            self._access_times[context.correlation_id] = time.time()

    def get(self, correlation_id: str) -> Optional[CorrelationContext]:
        """Get a correlation context"""
        with self._lock:
            context = self._store.get(correlation_id)
            if context:
                self._access_times[correlation_id] = time.time()
            return context

    def get_all_for_trace(self, trace_id: str) -> List[CorrelationContext]:
        """Get all correlation contexts for a trace"""
        with self._lock:
            return [ctx for ctx in self._store.values() if ctx.trace_id == trace_id]

    def get_children(self, parent_correlation_id: str) -> List[CorrelationContext]:
        """Get all child correlation contexts"""
        with self._lock:
            return [
                ctx
                for ctx in self._store.values()
                if ctx.parent_correlation_id == parent_correlation_id
            ]


# Global correlation store
_correlation_store = CorrelationStore()


class W3CTraceContextPropagator:
    """W3C Trace Context propagation handler"""

    def __init__(self):
        self.propagator = TraceContextTextMapPropagator()

    def extract_from_headers(self, headers: Dict[str, str]) -> Optional[context.Context]:
        """Extract W3C trace context from headers"""
        try:
            return self.propagator.extract(headers)
        except Exception as e:
            logger.warning(f"Failed to extract trace context: {e}")
            return None

    def inject_to_headers(self, headers: Dict[str, str], ctx: Optional[context.Context] = None):
        """Inject W3C trace context into headers"""
        try:
            if ctx is None:
                ctx = context.get_current()
            self.propagator.inject(headers, ctx)
        except Exception as e:
            logger.warning(f"Failed to inject trace context: {e}")

    def extract_from_websocket(self, websocket: WebSocket) -> Optional[context.Context]:
        """Extract trace context from WebSocket headers"""
        headers = dict(websocket.headers)
        return self.extract_from_headers(headers)


class CorrelationManager:
    """Main correlation management class"""

    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.propagator = W3CTraceContextPropagator()
        self._active_correlations: Set[str] = set()
        self._correlation_metrics = defaultdict(int)

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID"""
        return f"corr_{uuid.uuid4().hex[:16]}"

    def create_context_from_request(self, request: Request) -> CorrelationContext:
        """Create correlation context from HTTP request"""
        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-request-id")
            or self.generate_correlation_id()
        )

        # Extract trace context
        trace_ctx = self.propagator.extract_from_headers(dict(request.headers))

        # Get current span information
        current_span = trace.get_current_span()
        trace_id = f"{current_span.get_span_context().trace_id:032x}" if current_span else ""
        span_id = f"{current_span.get_span_context().span_id:016x}" if current_span else ""

        # Extract additional context
        user_id = request.headers.get("x-user-id")
        session_id = request.headers.get("x-session-id")
        parent_correlation_id = request.headers.get("x-parent-correlation-id")

        context = CorrelationContext(
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            user_id=user_id,
            request_type="http",
            parent_correlation_id=parent_correlation_id,
            session_id=session_id,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "method": request.method,
                "path": str(request.url.path),
                "query_params": str(request.query_params),
            },
        )

        return context

    def create_context_from_websocket(self, websocket: WebSocket) -> CorrelationContext:
        """Create correlation context from WebSocket connection"""
        # Extract or generate correlation ID
        headers = dict(websocket.headers)
        correlation_id = (
            headers.get("x-correlation-id")
            or headers.get("x-request-id")
            or self.generate_correlation_id()
        )

        # Extract trace context
        trace_ctx = self.propagator.extract_from_websocket(websocket)

        # Get current span information
        current_span = trace.get_current_span()
        trace_id = f"{current_span.get_span_context().trace_id:032x}" if current_span else ""
        span_id = f"{current_span.get_span_context().span_id:016x}" if current_span else ""

        context = CorrelationContext(
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            user_id=headers.get("x-user-id"),
            request_type="websocket",
            parent_correlation_id=headers.get("x-parent-correlation-id"),
            session_id=headers.get("x-session-id"),
            client_ip=websocket.client.host if websocket.client else None,
            user_agent=headers.get("user-agent"),
            metadata={"path": str(websocket.url.path), "query_params": str(websocket.query_params)},
        )

        return context

    def create_child_context(
        self,
        parent_context: CorrelationContext,
        operation_name: str,
        request_type: str = "async_task",
    ) -> CorrelationContext:
        """Create a child correlation context for async operations"""
        child_correlation_id = self.generate_correlation_id()

        # Create new span as child
        with self.tracer.start_as_current_span(operation_name) as span:
            trace_id = f"{span.get_span_context().trace_id:032x}"
            span_id = f"{span.get_span_context().span_id:016x}"

        child_context = CorrelationContext(
            correlation_id=child_correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            user_id=parent_context.user_id,
            request_type=request_type,
            parent_correlation_id=parent_context.correlation_id,
            session_id=parent_context.session_id,
            client_ip=parent_context.client_ip,
            user_agent=parent_context.user_agent,
            metadata={"operation": operation_name, "parent_type": parent_context.request_type},
        )

        return child_context

    @contextmanager
    def correlation_context(self, context: CorrelationContext):
        """Context manager for correlation context"""
        # Store context
        _correlation_store.store(context)
        self._active_correlations.add(context.correlation_id)

        # Set context variables
        correlation_token = correlation_id_var.set(context.correlation_id)
        trace_token = trace_id_var.set(context.trace_id)
        span_token = span_id_var.set(context.span_id)
        user_token = user_id_var.set(context.user_id or "")
        type_token = request_type_var.set(context.request_type)

        # Set OpenTelemetry baggage
        baggage_data = context.to_baggage()
        baggage_ctx = context.get_current()
        for key, value in baggage_data.items():
            baggage_ctx = baggage.set_baggage(key, value, baggage_ctx)

        baggage_token = context.attach(baggage_ctx)

        try:
            yield context
        finally:
            # Reset context variables
            correlation_id_var.reset(correlation_token)
            trace_id_var.reset(trace_token)
            span_id_var.reset(span_token)
            user_id_var.reset(user_token)
            request_type_var.reset(type_token)
            context.detach(baggage_token)

            # Remove from active set
            self._active_correlations.discard(context.correlation_id)

    @asynccontextmanager
    async def async_correlation_context(self, context: CorrelationContext):
        """Async context manager for correlation context"""
        with self.correlation_context(context):
            yield context

    def get_current_correlation(self) -> Optional[CorrelationContext]:
        """Get current correlation context"""
        correlation_id = correlation_id_var.get()
        if correlation_id:
            return _correlation_store.get(correlation_id)
        return None

    def propagate_to_headers(self, headers: Dict[str, str]):
        """Propagate current correlation context to headers"""
        current_context = self.get_current_correlation()
        if current_context:
            headers.update(current_context.to_headers())

        # Also inject W3C trace context
        self.propagator.inject_to_headers(headers)

    def get_correlation_chain(self, correlation_id: str) -> List[CorrelationContext]:
        """Get the full correlation chain (parent and children)"""
        context = _correlation_store.get(correlation_id)
        if not context:
            return []

        chain = [context]

        # Get parent chain
        current = context
        while current and current.parent_correlation_id:
            parent = _correlation_store.get(current.parent_correlation_id)
            if parent:
                chain.insert(0, parent)
                current = parent
            else:
                break

        # Get children
        children = _correlation_store.get_children(correlation_id)
        chain.extend(children)

        return chain

    def get_metrics(self) -> Dict[str, Any]:
        """Get correlation metrics"""
        return {
            "active_correlations": len(self._active_correlations),
            "total_stored": len(_correlation_store._store),
            "correlation_types": dict(self._correlation_metrics),
        }


# Global correlation manager
correlation_manager = CorrelationManager()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for correlation tracking"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Create correlation context
        context = correlation_manager.create_context_from_request(request)

        # Use correlation context for the request
        async with correlation_manager.async_correlation_context(context):
            try:
                # Process request
                response = await call_next(request)

                # Add correlation headers to response
                response.headers.update(context.to_headers())

                # Log completion
                logger.info(
                    f"Request completed: {request.method} {request.url.path}",
                    extra=context.to_log_extra(),
                )

                return response

            except Exception as e:
                # Log error with correlation context
                logger.error(
                    f"Request failed: {request.method} {request.url.path} - {str(e)}",
                    extra=context.to_log_extra(),
                )
                raise


def correlate_async_task(operation_name: str):
    """Decorator to correlate async tasks with parent context"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            parent_context = correlation_manager.get_current_correlation()

            if parent_context:
                # Create child context
                child_context = correlation_manager.create_child_context(
                    parent_context, operation_name, "async_task"
                )

                # Execute with child context
                async with correlation_manager.async_correlation_context(child_context):
                    return await func(*args, **kwargs)
            else:
                # No parent context, execute normally
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def correlate_sync_task(operation_name: str):
    """Decorator to correlate sync tasks with parent context"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            parent_context = correlation_manager.get_current_correlation()

            if parent_context:
                # Create child context
                child_context = correlation_manager.create_child_context(
                    parent_context, operation_name, "sync_task"
                )

                # Execute with child context
                with correlation_manager.correlation_context(child_context):
                    return func(*args, **kwargs)
            else:
                # No parent context, execute normally
                return func(*args, **kwargs)

        return wrapper

    return decorator


class WebSocketCorrelationManager:
    """Specialized correlation manager for WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, CorrelationContext] = {}

    async def connect(self, websocket: WebSocket) -> CorrelationContext:
        """Handle WebSocket connection with correlation"""
        context = correlation_manager.create_context_from_websocket(websocket)
        self.active_connections[context.correlation_id] = context

        # Store in global store
        _correlation_store.store(context)

        logger.info(f"WebSocket connected: {websocket.url.path}", extra=context.to_log_extra())

        return context

    async def disconnect(self, correlation_id: str):
        """Handle WebSocket disconnection"""
        context = self.active_connections.pop(correlation_id, None)
        if context:
            logger.info(
                f"WebSocket disconnected: {context.metadata.get('path', 'unknown')}",
                extra=context.to_log_extra(),
            )

    def get_connection_context(self, correlation_id: str) -> Optional[CorrelationContext]:
        """Get WebSocket connection context"""
        return self.active_connections.get(correlation_id)


# Global WebSocket correlation manager
websocket_correlation_manager = WebSocketCorrelationManager()


# Utility functions for easy access
def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id_var.get("")


def get_trace_id() -> str:
    """Get current trace ID"""
    return trace_id_var.get("")


def get_user_id() -> str:
    """Get current user ID"""
    return user_id_var.get("")


def get_correlation_context() -> Optional[CorrelationContext]:
    """Get current correlation context"""
    return correlation_manager.get_current_correlation()


def log_with_correlation(level: int, message: str, **kwargs):
    """Log message with correlation context"""
    context = get_correlation_context()
    if context:
        kwargs.update(context.to_log_extra())

    logger.log(level, message, extra=kwargs)


# Export main components
__all__ = [
    "CorrelationContext",
    "CorrelationManager",
    "CorrelationMiddleware",
    "WebSocketCorrelationManager",
    "correlate_async_task",
    "correlate_sync_task",
    "correlation_manager",
    "websocket_correlation_manager",
    "get_correlation_id",
    "get_trace_id",
    "get_user_id",
    "get_correlation_context",
    "log_with_correlation",
]
