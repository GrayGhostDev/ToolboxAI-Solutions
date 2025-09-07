"""Performance optimization utilities"""

import time
import threading
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class ConnectionPool:
    """HTTP connection pool with retry strategy"""
    
    def __init__(self, pool_connections: int = 10, pool_maxsize: int = 20):
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET request with connection pooling"""
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST request with connection pooling"""
        return self.session.post(url, **kwargs)


class RequestBatcher:
    """Batch multiple requests for efficiency"""
    
    def __init__(self, batch_size: int = 10, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch: list = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # Start auto-flush thread
        self._start_auto_flush()
    
    def add_request(self, request_func, *args, **kwargs):
        """Add request to batch"""
        with self._lock:
            self._batch.append((request_func, args, kwargs))
            
            if len(self._batch) >= self.batch_size:
                self._flush_batch()
    
    def _flush_batch(self):
        """Flush current batch"""
        if not self._batch:
            return
        
        batch_to_process = self._batch.copy()
        self._batch.clear()
        self._last_flush = time.time()
        
        # Process batch in background
        self._executor.submit(self._process_batch, batch_to_process)
    
    def _process_batch(self, batch):
        """Process batch of requests"""
        for request_func, args, kwargs in batch:
            try:
                request_func(*args, **kwargs)
            except Exception as e:
                logger.error("Batch request failed: %s", e)
    
    def _start_auto_flush(self):
        """Start auto-flush thread"""
        def auto_flush():
            while True:
                time.sleep(self.flush_interval)
                with self._lock:
                    if (time.time() - self._last_flush) >= self.flush_interval:
                        self._flush_batch()
        
        flush_thread = threading.Thread(target=auto_flush, daemon=True)
        flush_thread.start()


class MemoryOptimizer:
    """Memory usage optimization utilities"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024),
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / (1024 * 1024)
            }
        except ImportError:
            # Fallback without psutil
            import sys
            return {
                'objects_count': len(gc.get_objects()) if 'gc' in sys.modules else 0,
                'ref_count': sys.gettotalrefcount() if hasattr(sys, 'gettotalrefcount') else 0
            }
    
    @staticmethod
    def force_gc():
        """Force garbage collection"""
        try:
            import gc
            collected = gc.collect()
            logger.debug("Garbage collection freed %d objects", collected)
            return collected
        except Exception as e:
            logger.error("Garbage collection failed: %s", e)
            return 0


class PerformanceProfiler:
    """Simple performance profiler"""
    
    def __init__(self):
        self._timings: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def time_function(self, name: str):
        """Decorator to time function execution"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_timing(name, duration)
            return wrapper
        return decorator
    
    def record_timing(self, name: str, duration: float):
        """Record timing for operation"""
        with self._lock:
            if name not in self._timings:
                self._timings[name] = []
            
            self._timings[name].append(duration)
            
            # Keep only last 1000 timings
            if len(self._timings[name]) > 1000:
                self._timings[name] = self._timings[name][-1000:]
    
    def get_stats(self, name: str) -> Optional[Dict[str, float]]:
        """Get timing statistics"""
        with self._lock:
            if name not in self._timings or not self._timings[name]:
                return None
            
            timings = self._timings[name]
            return {
                'count': len(timings),
                'avg': sum(timings) / len(timings),
                'min': min(timings),
                'max': max(timings),
                'total': sum(timings)
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all timing statistics"""
        with self._lock:
            return {name: self.get_stats(name) for name in self._timings if self._timings[name]}


# Global instances
connection_pool = ConnectionPool()
request_batcher = RequestBatcher()
profiler = PerformanceProfiler()