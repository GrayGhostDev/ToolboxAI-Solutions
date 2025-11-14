"""
Real-time Anomaly Detection System

Provides statistical analysis for detecting anomalies in latency, error rates,
and traffic patterns with real-time alerting capabilities.
"""

import asyncio
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

import numpy as np

# Optional scientific computing dependencies
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    DBSCAN = None
    StandardScaler = None

from .correlation import get_correlation_context

logger = logging.getLogger(__name__)

# Log availability warnings after logger is defined
if not SCIPY_AVAILABLE:
    logger.debug("scipy not available - trend anomaly detection will be disabled")
if not SKLEARN_AVAILABLE:
    logger.debug("sklearn not available - some advanced features will be disabled")


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""

    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_SPIKE = "error_rate_spike"
    TRAFFIC_ANOMALY = "traffic_anomaly"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    UNUSUAL_PATTERN = "unusual_pattern"


class AnomalySeverity(Enum):
    """Severity levels for anomalies"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyAlert:
    """Represents an anomaly alert"""

    id: str
    type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    expected_value: float
    threshold: float
    confidence: float
    correlation_id: str | None = None
    trace_id: str | None = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "threshold": self.threshold,
            "confidence": self.confidence,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MetricDataPoint:
    """Single metric data point"""

    timestamp: float
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)


class TimeSeriesBuffer:
    """Thread-safe time series buffer with automatic cleanup"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._data: deque = deque(maxlen=max_size)
        self._lock = threading.RLock()

    def add(self, value: float, metadata: dict[str, Any] | None = None):
        """Add a data point"""
        with self._lock:
            self._data.append(
                MetricDataPoint(timestamp=time.time(), value=value, metadata=metadata or {})
            )
            self._cleanup_expired()

    def _cleanup_expired(self):
        """Remove expired data points"""
        current_time = time.time()
        cutoff_time = current_time - self.ttl_seconds

        while self._data and self._data[0].timestamp < cutoff_time:
            self._data.popleft()

    def get_recent(self, seconds: int) -> list[MetricDataPoint]:
        """Get data points from the last N seconds"""
        with self._lock:
            cutoff_time = time.time() - seconds
            return [dp for dp in self._data if dp.timestamp >= cutoff_time]

    def get_all(self) -> list[MetricDataPoint]:
        """Get all data points"""
        with self._lock:
            return list(self._data)

    def get_values(self, seconds: int | None = None) -> list[float]:
        """Get just the values"""
        if seconds:
            data_points = self.get_recent(seconds)
        else:
            data_points = self.get_all()
        return [dp.value for dp in data_points]

    def get_timestamps(self, seconds: int | None = None) -> list[float]:
        """Get just the timestamps"""
        if seconds:
            data_points = self.get_recent(seconds)
        else:
            data_points = self.get_all()
        return [dp.timestamp for dp in data_points]

    def size(self) -> int:
        """Get current buffer size"""
        with self._lock:
            return len(self._data)


class StatisticalDetector:
    """Statistical anomaly detection algorithms"""

    @staticmethod
    def z_score_detection(values: list[float], threshold: float = 3.0) -> tuple[bool, float]:
        """Z-score based anomaly detection"""
        if len(values) < 3:
            return False, 0.0

        try:
            mean = statistics.mean(values[:-1])  # Exclude current value from mean
            stdev = statistics.stdev(values[:-1])

            if stdev == 0:
                return False, 0.0

            current_value = values[-1]
            z_score = abs(current_value - mean) / stdev

            return z_score > threshold, z_score
        except Exception as e:
            logger.warning(f"Z-score detection error: {e}")
            return False, 0.0

    @staticmethod
    def modified_z_score_detection(
        values: list[float], threshold: float = 3.5
    ) -> tuple[bool, float]:
        """Modified Z-score using median absolute deviation"""
        if len(values) < 3:
            return False, 0.0

        try:
            historical_values = values[:-1]
            current_value = values[-1]

            median = statistics.median(historical_values)
            mad = statistics.median([abs(v - median) for v in historical_values])

            if mad == 0:
                return False, 0.0

            modified_z_score = 0.6745 * (current_value - median) / mad

            return abs(modified_z_score) > threshold, abs(modified_z_score)
        except Exception as e:
            logger.warning(f"Modified Z-score detection error: {e}")
            return False, 0.0

    @staticmethod
    def interquartile_range_detection(
        values: list[float], factor: float = 1.5
    ) -> tuple[bool, float]:
        """IQR-based anomaly detection"""
        if len(values) < 5:
            return False, 0.0

        try:
            historical_values = sorted(values[:-1])
            current_value = values[-1]

            q1 = np.percentile(historical_values, 25)
            q3 = np.percentile(historical_values, 75)
            iqr = q3 - q1

            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr

            is_anomaly = current_value < lower_bound or current_value > upper_bound

            # Calculate distance from bounds as confidence
            if current_value < lower_bound:
                confidence = (lower_bound - current_value) / iqr if iqr > 0 else 0
            elif current_value > upper_bound:
                confidence = (current_value - upper_bound) / iqr if iqr > 0 else 0
            else:
                confidence = 0

            return is_anomaly, confidence
        except Exception as e:
            logger.warning(f"IQR detection error: {e}")
            return False, 0.0

    @staticmethod
    def exponential_smoothing_detection(
        values: list[float], alpha: float = 0.3, threshold: float = 2.0
    ) -> tuple[bool, float]:
        """Exponential smoothing based detection"""
        if len(values) < 3:
            return False, 0.0

        try:
            # Calculate exponential smoothing
            smoothed = [values[0]]
            for i in range(1, len(values) - 1):
                smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])

            # Calculate residuals
            residuals = []
            for i in range(1, len(smoothed)):
                residuals.append(abs(values[i] - smoothed[i]))

            if not residuals:
                return False, 0.0

            # Use moving average of residuals as threshold
            avg_residual = statistics.mean(residuals)
            current_residual = abs(values[-1] - smoothed[-1])

            confidence = current_residual / avg_residual if avg_residual > 0 else 0

            return confidence > threshold, confidence
        except Exception as e:
            logger.warning(f"Exponential smoothing detection error: {e}")
            return False, 0.0


class PatternDetector:
    """Pattern-based anomaly detection"""

    @staticmethod
    def sudden_change_detection(
        values: list[float], min_change_ratio: float = 2.0
    ) -> tuple[bool, float]:
        """Detect sudden changes in values"""
        if len(values) < 2:
            return False, 0.0

        try:
            recent_avg = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
            historical_avg = statistics.mean(values[:-3]) if len(values) > 3 else values[0]

            if historical_avg == 0:
                return False, 0.0

            change_ratio = recent_avg / historical_avg

            is_anomaly = change_ratio > min_change_ratio or change_ratio < (1 / min_change_ratio)
            confidence = max(change_ratio, 1 / change_ratio) if change_ratio > 0 else 0

            return is_anomaly, confidence
        except Exception as e:
            logger.warning(f"Sudden change detection error: {e}")
            return False, 0.0

    @staticmethod
    def trend_anomaly_detection(values: list[float], timestamps: list[float]) -> tuple[bool, float]:
        """Detect anomalies in trends"""
        if len(values) < 5:
            return False, 0.0

        # Check if scipy is available
        if not SCIPY_AVAILABLE:
            logger.debug("scipy not available - using simplified trend detection")
            # Fallback: Use simple slope calculation instead of linear regression
            try:
                # Calculate simple slope between first and last points
                time_span = timestamps[-1] - timestamps[0]
                if time_span == 0:
                    return False, 0.0

                slope = (values[-1] - values[0]) / time_span
                intercept = values[0] - slope * timestamps[0]

                # Calculate residuals
                predicted = [slope * t + intercept for t in timestamps]
                residuals = [abs(actual - pred) for actual, pred in zip(values, predicted)]

                # Check if latest point is anomalous
                current_residual = residuals[-1]
                avg_residual = statistics.mean(residuals[:-1])

                if avg_residual == 0:
                    return False, 0.0

                confidence = current_residual / avg_residual

                return confidence > 2.0, confidence
            except Exception as e:
                logger.warning(f"Simplified trend detection error: {e}")
                return False, 0.0

        try:
            # Linear regression to find trend (requires scipy)
            slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, values)

            # Calculate residuals
            predicted = [slope * t + intercept for t in timestamps]
            residuals = [abs(actual - pred) for actual, pred in zip(values, predicted)]

            # Check if latest point is anomalous
            current_residual = residuals[-1]
            avg_residual = statistics.mean(residuals[:-1])

            if avg_residual == 0:
                return False, 0.0

            confidence = current_residual / avg_residual

            return confidence > 2.0, confidence
        except Exception as e:
            logger.warning(f"Trend anomaly detection error: {e}")
            return False, 0.0


class AnomalyDetectionEngine:
    """Main anomaly detection engine"""

    def __init__(self, alert_callback: Callable[[AnomalyAlert], None] | None = None):
        self.metrics: dict[str, TimeSeriesBuffer] = defaultdict(lambda: TimeSeriesBuffer())
        self.alert_callback = alert_callback
        self.detection_config = {
            "latency": {
                "threshold_multiplier": 3.0,
                "min_samples": 10,
                "detection_methods": ["z_score", "iqr", "exponential_smoothing"],
            },
            "error_rate": {
                "threshold_multiplier": 2.5,
                "min_samples": 5,
                "detection_methods": ["z_score", "sudden_change"],
            },
            "traffic": {
                "threshold_multiplier": 2.0,
                "min_samples": 10,
                "detection_methods": ["iqr", "trend_anomaly"],
            },
        }
        self._alert_history: dict[str, datetime] = {}
        self._alert_cooldown = 300  # 5 minutes

    def record_metric(self, metric_name: str, value: float, metadata: dict[str, Any] | None = None):
        """Record a metric value"""
        self.metrics[metric_name].add(value, metadata)

        # Trigger real-time detection
        asyncio.create_task(self._check_for_anomalies(metric_name))

    async def _check_for_anomalies(self, metric_name: str):
        """Check for anomalies in a specific metric"""
        try:
            buffer = self.metrics[metric_name]
            values = buffer.get_values()

            if len(values) < 3:
                return

            # Determine metric category
            category = self._categorize_metric(metric_name)
            config = self.detection_config.get(category, self.detection_config["latency"])

            if len(values) < config["min_samples"]:
                return

            # Run detection algorithms
            anomalies = []
            for method in config["detection_methods"]:
                is_anomaly, confidence = await self._run_detection_method(method, values, buffer)
                if is_anomaly:
                    anomalies.append((method, confidence))

            # If multiple methods detect anomaly, create alert
            if len(anomalies) >= 2 or (anomalies and anomalies[0][1] > 5.0):
                await self._create_anomaly_alert(metric_name, values[-1], anomalies, category)

        except Exception as e:
            logger.error(f"Error checking anomalies for {metric_name}: {e}")

    def _categorize_metric(self, metric_name: str) -> str:
        """Categorize metric by name"""
        if "latency" in metric_name.lower() or "response_time" in metric_name.lower():
            return "latency"
        elif "error" in metric_name.lower() or "failure" in metric_name.lower():
            return "error_rate"
        elif "traffic" in metric_name.lower() or "requests" in metric_name.lower():
            return "traffic"
        else:
            return "latency"  # default

    async def _run_detection_method(
        self, method: str, values: list[float], buffer: TimeSeriesBuffer
    ) -> tuple[bool, float]:
        """Run a specific detection method"""
        try:
            if method == "z_score":
                return StatisticalDetector.z_score_detection(values)
            elif method == "modified_z_score":
                return StatisticalDetector.modified_z_score_detection(values)
            elif method == "iqr":
                return StatisticalDetector.interquartile_range_detection(values)
            elif method == "exponential_smoothing":
                return StatisticalDetector.exponential_smoothing_detection(values)
            elif method == "sudden_change":
                return PatternDetector.sudden_change_detection(values)
            elif method == "trend_anomaly":
                timestamps = buffer.get_timestamps()
                return PatternDetector.trend_anomaly_detection(values, timestamps)
            else:
                logger.warning(f"Unknown detection method: {method}")
                return False, 0.0
        except Exception as e:
            logger.error(f"Error running detection method {method}: {e}")
            return False, 0.0

    async def _create_anomaly_alert(
        self,
        metric_name: str,
        current_value: float,
        anomalies: list[tuple[str, float]],
        category: str,
    ):
        """Create and emit anomaly alert"""
        # Check cooldown
        alert_key = f"{metric_name}_{category}"
        last_alert = self._alert_history.get(alert_key)
        if last_alert and (datetime.utcnow() - last_alert).total_seconds() < self._alert_cooldown:
            return

        # Calculate severity
        max_confidence = max(conf for _, conf in anomalies)
        severity = self._calculate_severity(max_confidence, category)

        # Get correlation context
        context = get_correlation_context()

        # Calculate expected value
        buffer = self.metrics[metric_name]
        historical_values = buffer.get_values()[:-1]
        expected_value = statistics.mean(historical_values) if historical_values else current_value

        # Create alert
        alert = AnomalyAlert(
            id=f"anomaly_{int(time.time())}_{metric_name}",
            type=self._get_anomaly_type(category),
            severity=severity,
            title=f"Anomaly detected in {metric_name}",
            description=f"Current value {current_value:.2f} deviates significantly from expected {expected_value:.2f}. "
            f"Detected by methods: {', '.join(method for method, _ in anomalies)}",
            metric_name=metric_name,
            current_value=current_value,
            expected_value=expected_value,
            threshold=max_confidence,
            confidence=max_confidence,
            correlation_id=context.correlation_id if context else None,
            trace_id=context.trace_id if context else None,
            metadata={
                "detection_methods": [method for method, _ in anomalies],
                "confidences": {method: conf for method, conf in anomalies},
                "category": category,
            },
        )

        # Update alert history
        self._alert_history[alert_key] = datetime.utcnow()

        # Emit alert
        if self.alert_callback:
            try:
                await asyncio.get_event_loop().run_in_executor(None, self.alert_callback, alert)
            except Exception as e:
                logger.error(f"Error calling alert callback: {e}")

        # Log alert
        logger.warning(
            f"Anomaly detected: {alert.title}",
            extra={
                "alert_id": alert.id,
                "metric_name": metric_name,
                "current_value": current_value,
                "expected_value": expected_value,
                "confidence": max_confidence,
                "severity": severity.value,
                "correlation_id": alert.correlation_id,
                "trace_id": alert.trace_id,
            },
        )

    def _calculate_severity(self, confidence: float, category: str) -> AnomalySeverity:
        """Calculate severity based on confidence and category"""
        if category == "error_rate":
            if confidence > 10:
                return AnomalySeverity.CRITICAL
            elif confidence > 5:
                return AnomalySeverity.HIGH
            elif confidence > 3:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW
        else:
            if confidence > 8:
                return AnomalySeverity.CRITICAL
            elif confidence > 5:
                return AnomalySeverity.HIGH
            elif confidence > 3:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW

    def _get_anomaly_type(self, category: str) -> AnomalyType:
        """Get anomaly type from category"""
        type_mapping = {
            "latency": AnomalyType.LATENCY_SPIKE,
            "error_rate": AnomalyType.ERROR_RATE_SPIKE,
            "traffic": AnomalyType.TRAFFIC_ANOMALY,
        }
        return type_mapping.get(category, AnomalyType.UNUSUAL_PATTERN)

    def get_metric_summary(self, metric_name: str, seconds: int = 300) -> dict[str, Any]:
        """Get summary statistics for a metric"""
        buffer = self.metrics[metric_name]
        values = buffer.get_values(seconds)

        if not values:
            return {"error": "No data available"}

        try:
            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "latest": values[-1],
                "time_range_seconds": seconds,
            }
        except Exception as e:
            return {"error": f"Error calculating statistics: {e}"}

    def get_all_metrics_summary(self) -> dict[str, Any]:
        """Get summary for all metrics"""
        summary = {}
        for metric_name in self.metrics:
            summary[metric_name] = self.get_metric_summary(metric_name)
        return summary


class AlertManager:
    """Manages anomaly alerts and notifications"""

    def __init__(self):
        self.alert_handlers: list[Callable[[AnomalyAlert], None]] = []
        self.alert_history: deque = deque(maxlen=1000)

    def register_alert_handler(self, handler: Callable[[AnomalyAlert], None]):
        """Register an alert handler"""
        self.alert_handlers.append(handler)

    async def handle_alert(self, alert: AnomalyAlert):
        """Handle an anomaly alert"""
        # Store in history
        self.alert_history.append(alert)

        # Call all handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, handler, alert)
            except Exception as e:
                logger.error(f"Error calling alert handler: {e}")

    def get_recent_alerts(self, limit: int = 50) -> list[AnomalyAlert]:
        """Get recent alerts"""
        return list(self.alert_history)[-limit:]


# Global instances
anomaly_engine = AnomalyDetectionEngine()
alert_manager = AlertManager()

# Connect engine to alert manager
anomaly_engine.alert_callback = alert_manager.handle_alert


# Decorators for automatic metric collection
def track_latency(metric_name: str):
    """Decorator to track function execution latency"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency = (time.time() - start_time) * 1000  # Convert to milliseconds
                anomaly_engine.record_metric(f"{metric_name}_latency", latency)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency = (time.time() - start_time) * 1000  # Convert to milliseconds
                anomaly_engine.record_metric(f"{metric_name}_latency", latency)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def track_errors(metric_name: str):
    """Decorator to track function errors"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                anomaly_engine.record_metric(f"{metric_name}_success", 1)
                return result
            except Exception:
                anomaly_engine.record_metric(f"{metric_name}_error", 1)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                anomaly_engine.record_metric(f"{metric_name}_success", 1)
                return result
            except Exception:
                anomaly_engine.record_metric(f"{metric_name}_error", 1)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Export main components
__all__ = [
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
