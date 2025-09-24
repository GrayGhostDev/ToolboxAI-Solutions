"""Advanced cache management with LRU eviction and persistence"""

import json
import os
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional
import logging
import redis

logger = logging.getLogger(__name__)

# Redis client singleton
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None


def cache_result(ttl: int = None, expire: int = None):
    """Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds (preferred)
        expire: Time to live in seconds (backward compatibility)
    """
    # Support both ttl and expire parameters for backward compatibility
    cache_ttl = ttl or expire or 300
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from Redis cache if available
            if redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        return json.loads(cached)
                except Exception as e:
                    logger.debug(f"Cache get failed: {e}")
            
            # Call the actual function
            result = func(*args, **kwargs)
            
            # Store in cache
            if redis_client:
                try:
                    redis_client.setex(cache_key, cache_ttl, json.dumps(result))
                except Exception as e:
                    logger.debug(f"Cache set failed: {e}")
            
            return result
        return wrapper
    return decorator


class LRUCache:
    """LRU Cache with persistence and monitoring"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300, 
                 persist_file: str = None):
        self.max_size = max_size
        self.ttl = ttl
        self.persist_file = persist_file
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        
        if persist_file:
            self._load_from_disk()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Check TTL
            if time.time() - self._timestamps[key] > self.ttl:
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                # Evict if at capacity
                if len(self._cache) >= self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    del self._timestamps[oldest_key]
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def size(self) -> int:
        """Get cache size"""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'ttl': self.ttl
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired items"""
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if now - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]
            
            return len(expired_keys)
    
    def _load_from_disk(self) -> None:
        """Load cache from disk"""
        try:
            if os.path.exists(self.persist_file):
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache = OrderedDict(data.get('cache', {}))
                    self._timestamps = data.get('timestamps', {})
                logger.info("Loaded cache from %s", self.persist_file)
        except Exception as e:
            logger.error("Failed to load cache: %s", e)
    
    def save_to_disk(self) -> None:
        """Save cache to disk"""
        if not self.persist_file:
            return
        
        try:
            with self._lock:
                data = {
                    'cache': dict(self._cache),
                    'timestamps': self._timestamps
                }
                with open(self.persist_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                logger.debug("Saved cache to %s", self.persist_file)
        except Exception as e:
            logger.error("Failed to save cache: %s", e)
def get_cache_stats() -> dict:
    """Get cache statistics"""
    return {
        'size': len(_cache),
        'keys': list(_cache.keys())
    }
