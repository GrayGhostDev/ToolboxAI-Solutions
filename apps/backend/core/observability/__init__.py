"""
Observability Package for FastAPI Application

Provides comprehensive observability features including:
- W3C Trace Context propagation and correlation tracking
- Real-time anomaly detection with statistical analysis
- System metrics collection and monitoring
- Alerting and notification system
- Integration with existing load balancing components
"""

from .anomaly_detection import (
    AlertManager,
    AnomalyAlert,
    AnomalyDetectionEngine,
    AnomalySeverity,
    AnomalyType,
    alert_manager,
    anomaly_engine,
    track_errors,
    track_latency,
)
from .correlation import (
    CorrelationContext,
    CorrelationManager,
    CorrelationMiddleware,
    WebSocketCorrelationManager,
    correlate_async_task,
    correlate_sync_task,
    correlation_manager,
    get_correlation_context,
    get_correlation_id,
    get_trace_id,
    get_user_id,
    log_with_correlation,
    websocket_correlation_manager,
)

__version__ = "1.0.0"

__all__ = [
    # Correlation components
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
    # Anomaly detection components
    "AnomalyType",
    "AnomalySeverity",
    "AnomalyAlert",
    "AnomalyDetectionEngine",
    "AlertManager",
    "anomaly_engine",
    "alert_manager",
    "track_latency",
    "track_errors",
]
