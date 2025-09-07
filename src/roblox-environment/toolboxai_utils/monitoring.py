"""Monitoring and metrics collection utilities"""

import time
import threading
import uuid
from collections import defaultdict, deque
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and expose application metrics"""
    
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()
    
    def increment(self, name: str, value: int = 1) -> None:
        """Increment counter"""
        with self._lock:
            self._counters[name] += value
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge value"""
        with self._lock:
            self._gauges[name] = value
    
    def record_histogram(self, name: str, value: float) -> None:
        """Record histogram value"""
        with self._lock:
            self._histograms[name].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            metrics = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {}
            }
            
            for name, values in self._histograms.items():
                if values:
                    metrics['histograms'][name] = {
                        'count': len(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
            
            return metrics


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(threading.current_thread(), 'correlation_id', 'unknown')
        return True


class HealthChecker:
    """Health check manager"""
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def register_check(self, name: str, check_func: callable) -> None:
        """Register health check"""
        with self._lock:
            self._checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        with self._lock:
            for name, check_func in self._checks.items():
                try:
                    start_time = time.time()
                    result = check_func()
                    duration = time.time() - start_time
                    
                    if isinstance(result, bool):
                        status = 'healthy' if result else 'unhealthy'
                        healthy = result
                    else:
                        status = result.get('status', 'unknown')
                        healthy = status == 'healthy'
                    
                    results[name] = {
                        'status': status,
                        'healthy': healthy,
                        'duration_ms': round(duration * 1000, 2),
                        'timestamp': time.time()
                    }
                    
                    if not healthy:
                        overall_healthy = False
                        
                except Exception as e:
                    logger.error("Health check %s failed: %s", name, e)
                    results[name] = {
                        'status': 'error',
                        'healthy': False,
                        'error': str(e),
                        'timestamp': time.time()
                    }
                    overall_healthy = False
        
        return {
            'overall_healthy': overall_healthy,
            'checks': results,
            'timestamp': time.time()
        }


def set_correlation_id(correlation_id: str = None) -> str:
    """Set correlation ID for current thread"""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    
    threading.current_thread().correlation_id = correlation_id
    return correlation_id


def get_correlation_id() -> str:
    """Get correlation ID for current thread"""
    return getattr(threading.current_thread(), 'correlation_id', 'unknown')


# Global instances
metrics = MetricsCollector()
health_checker = HealthChecker()