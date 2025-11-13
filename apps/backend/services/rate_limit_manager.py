"""
Rate Limit Manager Service

Centralized rate limiting for the application.
"""

import asyncio
import logging
import time
from collections import defaultdict

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitManager:
    """Centralized rate limit manager."""

    def __init__(self):
        self.request_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.window_starts: dict[str, float] = {}
        self.lock = asyncio.Lock()
        self.mode = "sliding_window"  # Default mode

    def set_mode(self, mode) -> None:
        """Set the rate limiting mode (2025 best practice)."""
        self.mode = mode.value if hasattr(mode, "value") else mode
        logger.debug(f"Rate limiting mode set to: {self.mode}")

    def clear_all_limits(self) -> None:
        """Clear all rate limit data (for testing)."""
        self.request_counts.clear()
        self.window_starts.clear()
        logger.debug("All rate limits cleared")

    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = None,
        window_seconds: int = 60,
        source: str = "api",
    ) -> tuple[bool, int | None]:
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
            if (
                window_key not in self.window_starts
                or current_time - self.window_starts[window_key] >= window_seconds
            ):
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

    def reset_limits(self, identifier: str | None = None):
        """
        Reset rate limits for an identifier or all identifiers.

        Args:
            identifier: Specific identifier to reset, or None for all
        """
        if identifier:
            # Reset specific identifier
            keys_to_remove = [
                k for k in self.request_counts.keys() if k.startswith(f"{identifier}:")
            ]
            for key in keys_to_remove:
                del self.request_counts[key]
                if key in self.window_starts:
                    del self.window_starts[key]
        else:
            # Reset all
            self.request_counts.clear()
            self.window_starts.clear()

    def get_current_usage(self, identifier: str, source: str = "api") -> dict[str, any]:
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
            return {"requests": 0, "window_start": None, "time_remaining": 0}

        window_start = self.window_starts[window_key]
        time_elapsed = current_time - window_start
        time_remaining = max(0, 60 - time_elapsed)  # Assuming 60 second window

        return {
            "requests": self.request_counts[window_key][source],
            "window_start": window_start,
            "time_remaining": time_remaining,
        }


# Create singleton instance
_rate_limit_manager = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get the singleton rate limit manager instance."""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
    return _rate_limit_manager


# Export for convenience
rate_limit_manager = get_rate_limit_manager()
