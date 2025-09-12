"""
Centralized Rate Limit Management for ToolboxAI Roblox Environment

This module provides centralized rate limiting state management that can be 
used across all server components. It includes proper state isolation for 
testing and production-ready rate limiting functionality.

Features:
- Centralized state management
- Test mode for bypassing rate limits
- Production mode with full rate limiting
- Thread-safe operations
- Redis and in-memory backends
- Proper cleanup mechanisms
"""

import asyncio
import logging
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import redis
from config.environment import get_environment_config
settings = get_environment_config()

logger = logging.getLogger(__name__)


class RateLimitMode(Enum):
    """Rate limiting operation modes"""
    PRODUCTION = "production"
    TESTING = "testing"
    BYPASS = "bypass"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 100
    burst_limit: int = 200
    window_seconds: int = 60
    exclude_paths: Set[str] = field(default_factory=lambda: {"/health", "/metrics"})
    by_endpoint: Dict[str, int] = field(default_factory=dict)
    mode: RateLimitMode = RateLimitMode.PRODUCTION


class RateLimitManager:
    """
    Centralized rate limit management system
    
    This class manages all rate limiting state across the application,
    providing consistent behavior and proper isolation for testing.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for global rate limit state"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[RateLimitConfig] = None, redis_client: Optional[redis.Redis] = None):
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return
            
        self.config = config or RateLimitConfig()
        self.redis_client = redis_client
        self._lock = threading.RLock()
        
        # Storage backends
        self.local_buckets: Dict[str, deque] = defaultdict(deque)
        self.auth_memory_store: Dict[str, Any] = {}
        self.flask_rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.middleware_buckets: Dict[str, deque] = defaultdict(deque)
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_running = False
        
        # Testing support
        self.bypass_for_testing = False
        
        self._initialized = True
        logger.info(f"RateLimitManager initialized in {self.config.mode.value} mode")
    
    @classmethod
    def get_instance(cls, config: Optional[RateLimitConfig] = None, redis_client: Optional[redis.Redis] = None):
        """Get the singleton instance"""
        if cls._instance is None or not hasattr(cls._instance, '_initialized'):
            cls._instance = cls(config, redis_client)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)"""
        with cls._lock:
            if cls._instance:
                # Clean up any running tasks
                instance = cls._instance
                if instance.cleanup_task and not instance.cleanup_task.done():
                    instance.cleanup_task.cancel()
            cls._instance = None
    
    def set_mode(self, mode: RateLimitMode):
        """Set the rate limiting mode"""
        with self._lock:
            self.config.mode = mode
            if mode == RateLimitMode.TESTING or mode == RateLimitMode.BYPASS:
                self.bypass_for_testing = True
                logger.info("Rate limiting bypassed for testing")
            else:
                self.bypass_for_testing = False
                logger.info("Rate limiting enabled for production")
    
    def should_bypass(self) -> bool:
        """Check if rate limiting should be bypassed"""
        # Only bypass if explicitly in bypass mode or testing mode
        if self.config.mode == RateLimitMode.BYPASS:
            return True
        elif self.config.mode == RateLimitMode.TESTING:
            # In testing mode, only bypass if explicitly configured to do so
            return getattr(settings, 'BYPASS_RATE_LIMIT_IN_TESTS', False)
        else:
            # Production mode: never bypass
            return False
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        endpoint: str = "", 
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        source: str = "default"
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier for rate limiting (IP, user ID, etc.)
            endpoint: API endpoint being accessed
            max_requests: Maximum requests allowed (overrides config)
            window_seconds: Time window in seconds (overrides config)
            source: Source component making the request (for debugging)
            
        Returns:
            Tuple of (allowed: bool, retry_after_seconds: int)
        """
        if self.should_bypass():
            return True, 0
        
        # Determine limits
        limit = max_requests or self.config.by_endpoint.get(endpoint, self.config.requests_per_minute)
        window = window_seconds or self.config.window_seconds
        
        # Check if path is excluded (only if not in strict testing mode)
        if endpoint in self.config.exclude_paths and self.config.mode != RateLimitMode.PRODUCTION:
            return True, 0
        
        try:
            if self.redis_client:
                return await self._check_redis_limit(identifier, limit, window)
            else:
                return self._check_local_limit(identifier, limit, window, source)
        except Exception as e:
            logger.error(f"Rate limit check failed for {identifier}: {e}")
            # Fail open in case of errors
            return True, 0
    
    async def _check_redis_limit(self, identifier: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check rate limit using Redis backend"""
        key = f"rate_limit:{identifier}"
        now = time.time()
        window_start = now - window
        
        try:
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(uuid4()): now})
            
            # Set expiry
            pipe.expire(key, window + 1)
            
            results = pipe.execute()
            current_count = results[1]
            
            if current_count >= limit:
                retry_after = int(window - (now - window_start))
                return False, max(1, retry_after)
            
            return True, 0
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to local limiting
            return self._check_local_limit(identifier, limit, window, "redis_fallback")
    
    def _check_local_limit(self, identifier: str, limit: int, window: int, source: str) -> Tuple[bool, int]:
        """Check rate limit using local memory"""
        with self._lock:
            now = time.time()
            window_start = now - window
            
            # Get the appropriate bucket based on source
            if source == "auth":
                bucket = self.auth_memory_store.setdefault(f"rate_limit:{identifier}", deque())
            elif source == "flask":
                bucket = self.flask_rate_limits[identifier]
            elif source == "middleware":
                bucket = self.middleware_buckets[identifier]
            else:
                bucket = self.local_buckets[identifier]
            
            # Remove old entries
            if isinstance(bucket, deque):
                while bucket and bucket[0] < window_start:
                    bucket.popleft()
            else:  # List for Flask compatibility
                bucket[:] = [t for t in bucket if now - t < window]
            
            # Check limit
            current_count = len(bucket)
            if current_count >= limit:
                oldest_request = bucket[0] if bucket else now
                retry_after = int(window - (now - oldest_request))
                return False, max(1, retry_after)
            
            # Add current request
            if isinstance(bucket, deque):
                bucket.append(now)
                # Limit bucket size to prevent memory issues
                while len(bucket) > limit * 2:
                    bucket.popleft()
            else:
                bucket.append(now)
            
            return True, 0
    
    def clear_all_limits(self):
        """Clear all rate limiting state (for testing)"""
        with self._lock:
            # Clear local storage
            self.local_buckets.clear()
            self.auth_memory_store.clear()
            self.flask_rate_limits.clear()
            self.middleware_buckets.clear()
            
            # Clear Redis if available
            if self.redis_client:
                try:
                    # Get all rate limit keys
                    keys = self.redis_client.keys("rate_limit:*")
                    if keys:
                        self.redis_client.delete(*keys)
                    logger.debug(f"Cleared {len(keys)} rate limit keys from Redis")
                except Exception as e:
                    logger.error(f"Failed to clear Redis rate limits: {e}")
            
            logger.info("All rate limiting state cleared")
    
    def clear_identifier_limits(self, identifier: str):
        """Clear rate limits for a specific identifier"""
        with self._lock:
            # Clear from all local stores
            self.local_buckets.pop(identifier, None)
            
            # Clear auth memory store entries
            auth_keys_to_remove = [k for k in self.auth_memory_store.keys() if identifier in k]
            for key in auth_keys_to_remove:
                del self.auth_memory_store[key]
            
            # Clear Flask rate limits
            self.flask_rate_limits.pop(identifier, None)
            
            # Clear middleware buckets
            self.middleware_buckets.pop(identifier, None)
            
            # Clear from Redis
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(f"rate_limit:*{identifier}*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Failed to clear Redis limits for {identifier}: {e}")
    
    def get_limit_status(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for an identifier"""
        with self._lock:
            status = {
                "identifier": identifier,
                "bypass_enabled": self.should_bypass(),
                "mode": self.config.mode.value,
                "limits": {}
            }
            
            # Check all storage locations
            for source, storage in [
                ("local", self.local_buckets),
                ("flask", self.flask_rate_limits),
                ("middleware", self.middleware_buckets)
            ]:
                if identifier in storage:
                    bucket = storage[identifier]
                    status["limits"][source] = {
                        "current_requests": len(bucket),
                        "window_seconds": self.config.window_seconds
                    }
            
            # Check auth memory store
            auth_keys = [k for k in self.auth_memory_store.keys() if identifier in k]
            if auth_keys:
                status["limits"]["auth"] = {
                    "keys": len(auth_keys),
                    "details": {k: len(v) if isinstance(v, (list, deque)) else str(type(v)) 
                              for k, v in self.auth_memory_store.items() if identifier in k}
                }
            
            return status
    
    async def start_cleanup(self):
        """Start periodic cleanup of old entries"""
        if not self._cleanup_running and not self.cleanup_task:
            self._cleanup_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup(self):
        """Stop cleanup task"""
        self._cleanup_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old rate limit entries"""
        while self._cleanup_running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                if self.should_bypass():
                    continue
                    
                self._cleanup_expired_entries()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
    
    def _cleanup_expired_entries(self):
        """Clean up expired rate limit entries"""
        with self._lock:
            cutoff = time.time() - self.config.window_seconds
            cleaned_count = 0
            
            # Clean local buckets
            for identifier in list(self.local_buckets.keys()):
                bucket = self.local_buckets[identifier]
                original_size = len(bucket)
                while bucket and bucket[0] < cutoff:
                    bucket.popleft()
                if not bucket:
                    del self.local_buckets[identifier]
                cleaned_count += original_size - len(bucket)
            
            # Clean Flask rate limits
            for identifier in list(self.flask_rate_limits.keys()):
                bucket = self.flask_rate_limits[identifier]
                original_size = len(bucket)
                bucket[:] = [t for t in bucket if t >= cutoff]
                if not bucket:
                    del self.flask_rate_limits[identifier]
                cleaned_count += original_size - len(bucket)
            
            # Clean middleware buckets
            for identifier in list(self.middleware_buckets.keys()):
                bucket = self.middleware_buckets[identifier]
                original_size = len(bucket)
                while bucket and bucket[0] < cutoff:
                    bucket.popleft()
                if not bucket:
                    del self.middleware_buckets[identifier]
                cleaned_count += original_size - len(bucket)
            
            if cleaned_count > 0:
                logger.debug(f"Cleaned {cleaned_count} expired rate limit entries")


# Convenience functions for backward compatibility

def get_rate_limit_manager() -> RateLimitManager:
    """Get the global rate limit manager instance"""
    return RateLimitManager.get_instance()


def clear_all_rate_limits():
    """Clear all rate limiting state (for testing)"""
    manager = get_rate_limit_manager()
    manager.clear_all_limits()


def set_testing_mode(enabled: bool = True):
    """Enable or disable testing mode"""
    manager = get_rate_limit_manager()
    mode = RateLimitMode.TESTING if enabled else RateLimitMode.PRODUCTION
    manager.set_mode(mode)


def bypass_rate_limits(enabled: bool = True):
    """Enable or disable rate limit bypass"""
    manager = get_rate_limit_manager()
    mode = RateLimitMode.BYPASS if enabled else RateLimitMode.PRODUCTION
    manager.set_mode(mode)


# Context manager for testing
class RateLimitTestContext:
    """Context manager for rate limit testing"""
    
    def __init__(self, bypass: bool = True, clear_on_exit: bool = True):
        self.bypass = bypass
        self.clear_on_exit = clear_on_exit
        self.original_mode = None
        self.manager = None
    
    def __enter__(self):
        self.manager = get_rate_limit_manager()
        self.original_mode = self.manager.config.mode
        
        if self.bypass:
            self.manager.set_mode(RateLimitMode.BYPASS)
        
        return self.manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            if self.clear_on_exit:
                self.manager.clear_all_limits()
            
            if self.original_mode:
                self.manager.set_mode(self.original_mode)


__all__ = [
    "RateLimitManager",
    "RateLimitConfig", 
    "RateLimitMode",
    "get_rate_limit_manager",
    "clear_all_rate_limits",
    "set_testing_mode",
    "bypass_rate_limits",
    "RateLimitTestContext"
]