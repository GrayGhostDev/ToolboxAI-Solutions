"""
Rate Limit Manager Service

Centralized rate limiting for the application.
"""

import time
import hashlib
from typing import Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMode(Enum):
    """Rate limiting modes."""
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int = 100
    window_seconds: int = 60
    mode: RateLimitMode = RateLimitMode.SLIDING_WINDOW
    burst_size: Optional[int] = None
    refill_rate: Optional[float] = None


class RateLimitManager:
    """Centralized rate limit manager."""

    _instance = None

    def __init__(self):
        self.request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.window_starts: Dict[str, float] = {}
        self.lock = asyncio.Lock()
        self.mode: RateLimitMode = RateLimitMode.SLIDING_WINDOW

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        global _rate_limit_manager
        _rate_limit_manager = None
        cls._instance = None
        logger.debug("RateLimitManager instance reset")

    @classmethod
    def get_instance(cls) -> 'RateLimitManager':
        """Get the singleton instance (2025 best practice)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_mode(self, mode: RateLimitMode) -> None:
        """Set the rate limiting mode (2025 best practice)."""
        self.mode = mode
        logger.debug(f"Rate limiting mode set to: {mode.value}")

    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = None,
        window_seconds: int = 60,
        source: str = "api"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if a request is within rate limits.

        Args:
            identifier: Unique identifier for the client
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            source: Source of the request (api, websocket, etc.)

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if max_requests is None:
            max_requests = settings.rate_limit_per_minute

        async with self.lock:
            current_time = time.time()
            window_key = f"{identifier}:{source}"

            # Check if we need to reset the window
            if window_key not in self.window_starts or \
               current_time - self.window_starts[window_key] >= window_seconds:
                self.window_starts[window_key] = current_time
                self.request_counts[window_key] = defaultdict(int)

            # Increment request count
            self.request_counts[window_key][source] += 1

            # Check if limit exceeded
            if self.request_counts[window_key][source] > max_requests:
                retry_after = int(window_seconds - (current_time - self.window_starts[window_key]))
                logger.warning(f"Rate limit exceeded for {identifier} from {source}")
                return False, retry_after

            return True, None

    def reset_limits(self, identifier: Optional[str] = None):
        """
        Reset rate limits for an identifier or all identifiers.

        Args:
            identifier: Specific identifier to reset, or None for all
        """
        if identifier:
            # Reset specific identifier
            keys_to_remove = [k for k in self.request_counts.keys() if k.startswith(f"{identifier}:")]
            for key in keys_to_remove:
                del self.request_counts[key]
                if key in self.window_starts:
                    del self.window_starts[key]
        else:
            # Reset all
            self.request_counts.clear()
            self.window_starts.clear()

    def set_mode(self, mode: RateLimitMode) -> None:
        """Set the rate limit mode."""
        global _testing_mode
        if mode == RateLimitMode.TESTING:
            _testing_mode = True
        else:
            _testing_mode = False
        logger.info(f"Rate limit mode set to: {mode.value}")

    def clear_all_limits(self) -> None:
        """Clear all rate limits."""
        self.request_counts.clear()
        self.window_starts.clear()
        logger.debug("All rate limits cleared")

    async def start_cleanup(self):
        """Start background cleanup task for expired rate limit entries."""
        while True:
            try:
                # Clean up expired entries every 60 seconds
                await asyncio.sleep(60)

                async with self.lock:
                    current_time = time.time()

                    # Clean up old windows
                    keys_to_remove = []
                    for window_key, window_start in self.window_starts.items():
                        if current_time - window_start > 120:  # Remove windows older than 2 minutes
                            keys_to_remove.append(window_key)

                    for key in keys_to_remove:
                        if key in self.request_counts:
                            del self.request_counts[key]
                        if key in self.window_starts:
                            del self.window_starts[key]

                    if keys_to_remove:
                        logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit windows")

            except Exception as e:
                logger.error(f"Error in rate limit cleanup: {e}")
                await asyncio.sleep(60)  # Continue after error

    def get_current_usage(self, identifier: str, source: str = "api") -> Dict[str, any]:
        """
        Get current usage statistics for an identifier.

        Args:
            identifier: Unique identifier
            source: Source of requests

        Returns:
            Dictionary with usage statistics
        """
        window_key = f"{identifier}:{source}"
        current_time = time.time()

        if window_key not in self.window_starts:
            return {
                "requests": 0,
                "window_start": None,
                "time_remaining": 0
            }

        window_start = self.window_starts[window_key]
        time_elapsed = current_time - window_start
        time_remaining = max(0, 60 - time_elapsed)  # Assuming 60 second window

        return {
            "requests": self.request_counts[window_key][source],
            "window_start": window_start,
            "time_remaining": time_remaining
        }


# Testing support
_testing_mode = False


class RateLimitTestContext:
    """Context manager for rate limit testing."""

    def __init__(self, bypass: bool = True):
        self.bypass = bypass
        self.original_mode = None

    def __enter__(self):
        global _testing_mode
        self.original_mode = _testing_mode
        _testing_mode = self.bypass
        if self.bypass:
            clear_all_rate_limits()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _testing_mode
        _testing_mode = self.original_mode
        if self.bypass:
            clear_all_rate_limits()


def set_testing_mode(enabled: bool = True):
    """Enable or disable testing mode for rate limiting."""
    global _testing_mode
    _testing_mode = enabled
    if enabled:
        logger.info("Rate limiting testing mode enabled")


def clear_all_rate_limits():
    """Clear all rate limit data (for testing)."""
    manager = get_rate_limit_manager()
    manager.request_counts.clear()
    manager.window_starts.clear()
    logger.debug("All rate limits cleared")


# Create singleton instance
_rate_limit_manager = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get the singleton rate limit manager instance (2025 best practice)."""
    return RateLimitManager.get_instance()


# Export for convenience
rate_limit_manager = get_rate_limit_manager()
