"""
Optimized Pusher Connection Service
Implements connection reuse, batch processing, and efficient channel management
to reduce Pusher-related latency and improve throughput.
Target: Reduce Pusher operation latency from ~30ms to <20ms
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import json
import hashlib

import pusher
from pusher.errors import PusherError

from apps.backend.core.config import settings
from apps.backend.core.cache import cache, CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class PusherEvent:
    """Represents a Pusher event to be sent"""

    channel: str
    event: str
    data: Dict[str, Any]
    socket_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pusher API"""
        return {
            "channel": self.channel,
            "event": self.event,
            "data": self.data,
            "socket_id": self.socket_id,
        }


class PusherStats:
    """Track Pusher operation performance"""

    def __init__(self):
        self.events_sent = 0
        self.batch_events_sent = 0
        self.failed_events = 0
        self.total_latency = 0.0
        self.connection_errors = 0
        self.rate_limit_hits = 0
        self.cache_hits = 0
        self.channel_subscriptions = defaultdict(int)

    def record_event(self, success: bool, latency: float, batch_size: int = 1):
        """Record event sending statistics"""
        if success:
            self.events_sent += 1
            if batch_size > 1:
                self.batch_events_sent += batch_size
        else:
            self.failed_events += 1

        self.total_latency += latency

    def record_connection_error(self):
        self.connection_errors += 1

    def record_rate_limit(self):
        self.rate_limit_hits += 1

    def record_cache_hit(self):
        self.cache_hits += 1

    def record_channel_subscription(self, channel: str):
        self.channel_subscriptions[channel] += 1

    @property
    def success_rate(self) -> float:
        total = self.events_sent + self.failed_events
        return (self.events_sent / total) if total > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        return (self.total_latency / self.events_sent) if self.events_sent > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events_sent": self.events_sent,
            "batch_events_sent": self.batch_events_sent,
            "failed_events": self.failed_events,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency * 1000,
            "connection_errors": self.connection_errors,
            "rate_limit_hits": self.rate_limit_hits,
            "cache_hits": self.cache_hits,
            "popular_channels": dict(
                sorted(self.channel_subscriptions.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }


class ConnectionPool:
    """Manages multiple Pusher client instances for connection reuse"""

    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.clients: List[pusher.Pusher] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """Initialize the connection pool"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                pusher_config = {
                    "app_id": settings.PUSHER_APP_ID,
                    "key": settings.PUSHER_KEY,
                    "secret": settings.PUSHER_SECRET,
                    "cluster": settings.PUSHER_CLUSTER,
                    "ssl": settings.PUSHER_SSL,
                    # Performance optimizations
                    "timeout": 10,  # Reduced timeout for faster failures
                    "encryption_master_key_base64": None,  # Disable encryption for performance
                }

                # Create multiple client instances for connection pooling
                for _ in range(self.pool_size):
                    client = pusher.Pusher(**pusher_config)
                    self.clients.append(client)

                self._initialized = True
                logger.info(f"Pusher connection pool initialized with {self.pool_size} clients")

            except Exception as e:
                logger.error(f"Failed to initialize Pusher connection pool: {e}")
                raise

    def get_client(self) -> pusher.Pusher:
        """Get next available client using round-robin"""
        if not self._initialized:
            raise RuntimeError("Connection pool not initialized")

        client = self.clients[self.current_index]
        self.current_index = (self.current_index + 1) % self.pool_size
        return client

    async def close(self):
        """Close all connections in the pool"""
        # Pusher clients don't need explicit closing, but we clear references
        self.clients.clear()
        self._initialized = False


class EventBatcher:
    """Batches Pusher events for more efficient sending"""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_events: Dict[str, List[PusherEvent]] = defaultdict(list)
        self.last_flush = time.time()
        self._lock = asyncio.Lock()

    async def add_event(self, event: PusherEvent) -> bool:
        """Add event to batch, returns True if batch should be flushed"""
        async with self._lock:
            self.pending_events[event.channel].append(event)

            # Check if we should flush
            total_events = sum(len(events) for events in self.pending_events.values())
            time_since_last_flush = time.time() - self.last_flush

            return total_events >= self.batch_size or time_since_last_flush >= self.batch_timeout

    async def get_batches(self) -> Dict[str, List[PusherEvent]]:
        """Get and clear current batches"""
        async with self._lock:
            batches = dict(self.pending_events)
            self.pending_events.clear()
            self.last_flush = time.time()
            return batches


class ChannelManager:
    """Optimized channel management with caching"""

    def __init__(self):
        self.active_channels: Set[str] = set()
        self.channel_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"events_sent": 0, "subscribers": 0, "last_activity": None}
        )
        self._cache_prefix = "pusher_channel"

    async def register_channel(self, channel: str):
        """Register an active channel"""
        self.active_channels.add(channel)
        self.channel_stats[channel]["last_activity"] = datetime.now(timezone.utc)

        # Cache channel info
        cache_key = f"{self._cache_prefix}:{channel}"
        await cache.set(
            cache_key,
            {"active": True, "registered_at": datetime.now(timezone.utc).isoformat()},
            CacheConfig.LONG_TTL,
        )

    async def record_event(self, channel: str):
        """Record an event sent to a channel"""
        await self.register_channel(channel)
        self.channel_stats[channel]["events_sent"] += 1

    async def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get cached channel information"""
        cache_key = f"{self._cache_prefix}:{channel}"
        return await cache.get(cache_key)

    def get_channel_stats(self) -> Dict[str, Any]:
        """Get channel usage statistics"""
        return {
            "active_channels": len(self.active_channels),
            "channel_stats": dict(self.channel_stats),
            "most_active": sorted(
                self.channel_stats.items(), key=lambda x: x[1]["events_sent"], reverse=True
            )[:10],
        }


class RateLimiter:
    """Rate limiting for Pusher API calls"""

    def __init__(self, calls_per_second: int = 100):
        self.calls_per_second = calls_per_second
        self.call_times = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire permission to make API call"""
        async with self._lock:
            now = time.time()

            # Remove calls older than 1 second
            while self.call_times and self.call_times[0] < now - 1:
                self.call_times.popleft()

            # Check if we can make the call
            if len(self.call_times) < self.calls_per_second:
                self.call_times.append(now)
                return True

            return False

    async def wait_for_slot(self):
        """Wait until a rate limit slot is available"""
        while not await self.acquire():
            await asyncio.sleep(0.01)  # Small delay before retry


class OptimizedPusherService:
    """High-performance Pusher service with connection pooling and batching"""

    def __init__(self):
        self.connection_pool = ConnectionPool()
        self.event_batcher = EventBatcher()
        self.channel_manager = ChannelManager()
        self.rate_limiter = RateLimiter()
        self.stats = PusherStats()

        # Background task for processing batches
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self):
        """Initialize the optimized Pusher service"""
        try:
            await self.connection_pool.initialize()

            # Start background batch processing task
            self._running = True
            self._batch_task = asyncio.create_task(self._batch_processor())

            logger.info("Optimized Pusher service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize optimized Pusher service: {e}")
            raise

    async def _batch_processor(self):
        """Background task to process batched events"""
        while self._running:
            try:
                await asyncio.sleep(self.event_batcher.batch_timeout)

                batches = await self.event_batcher.get_batches()
                if batches:
                    await self._send_batched_events(batches)

            except Exception as e:
                logger.error(f"Error in batch processor: {e}")

    async def _send_batched_events(self, batches: Dict[str, List[PusherEvent]]):
        """Send batched events efficiently"""
        for channel, events in batches.items():
            if not events:
                continue

            try:
                # Wait for rate limit slot
                await self.rate_limiter.wait_for_slot()

                # Get client from pool
                client = self.connection_pool.get_client()

                start_time = time.time()

                # Group events by event type for more efficient sending
                events_by_type = defaultdict(list)
                for event in events:
                    events_by_type[event.event].append(event)

                # Send each group
                for event_type, type_events in events_by_type.items():
                    if len(type_events) == 1:
                        # Single event
                        event = type_events[0]
                        client.trigger(
                            event.channel, event.event, event.data, socket_id=event.socket_id
                        )
                    else:
                        # Multiple events - use batch trigger if available
                        batch_data = []
                        for event in type_events:
                            batch_data.append(
                                {
                                    "channel": event.channel,
                                    "name": event.event,
                                    "data": event.data,
                                    "socket_id": event.socket_id,
                                }
                            )

                        # Use trigger_batch for efficiency
                        client.trigger_batch(batch_data)

                # Record stats
                latency = time.time() - start_time
                self.stats.record_event(True, latency, len(events))
                await self.channel_manager.record_event(channel)

                logger.debug(f"Sent batch of {len(events)} events to {channel} in {latency:.3f}s")

            except PusherError as e:
                if "rate limit" in str(e).lower():
                    self.stats.record_rate_limit()
                    logger.warning(f"Rate limit hit for channel {channel}")
                else:
                    self.stats.record_event(False, 0, len(events))
                    logger.error(f"Pusher error for channel {channel}: {e}")

            except Exception as e:
                self.stats.record_connection_error()
                self.stats.record_event(False, 0, len(events))
                logger.error(f"Failed to send batch to {channel}: {e}")

    async def trigger_event(
        self,
        channel: str,
        event: str,
        data: Dict[str, Any],
        socket_id: Optional[str] = None,
        immediate: bool = False,
    ) -> bool:
        """Trigger a Pusher event with optimization"""

        # Create event object
        pusher_event = PusherEvent(channel=channel, event=event, data=data, socket_id=socket_id)

        # Register channel
        await self.channel_manager.register_channel(channel)

        if immediate:
            # Send immediately without batching
            return await self._send_single_event(pusher_event)
        else:
            # Add to batch
            should_flush = await self.event_batcher.add_event(pusher_event)

            if should_flush:
                # Process batches immediately
                batches = await self.event_batcher.get_batches()
                if batches:
                    await self._send_batched_events(batches)

            return True

    async def _send_single_event(self, event: PusherEvent) -> bool:
        """Send a single event immediately"""
        try:
            # Wait for rate limit slot
            await self.rate_limiter.wait_for_slot()

            # Get client from pool
            client = self.connection_pool.get_client()

            start_time = time.time()

            # Send event
            client.trigger(event.channel, event.event, event.data, socket_id=event.socket_id)

            # Record stats
            latency = time.time() - start_time
            self.stats.record_event(True, latency)
            await self.channel_manager.record_event(event.channel)

            return True

        except PusherError as e:
            if "rate limit" in str(e).lower():
                self.stats.record_rate_limit()
            self.stats.record_event(False, 0)
            logger.error(f"Pusher error: {e}")
            return False

        except Exception as e:
            self.stats.record_connection_error()
            self.stats.record_event(False, 0)
            logger.error(f"Failed to send event: {e}")
            return False

    async def authenticate_channel(
        self,
        socket_id: str,
        channel_name: str,
        user_id: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Authenticate channel access with caching"""

        # Check cache for recent authentication
        cache_key = f"pusher_auth:{socket_id}:{channel_name}"
        cached_auth = await cache.get(cache_key)

        if cached_auth:
            self.stats.record_cache_hit()
            return cached_auth

        try:
            # Get client from pool
            client = self.connection_pool.get_client()

            if channel_name.startswith("presence-"):
                if not user_id:
                    raise ValueError("User ID required for presence channel")

                auth_data = client.authenticate(
                    channel=channel_name,
                    socket_id=socket_id,
                    custom_data={"user_id": user_id, "user_info": user_info or {}},
                )
            else:
                auth_data = client.authenticate(channel=channel_name, socket_id=socket_id)

            # Cache authentication for short period
            await cache.set(cache_key, auth_data, CacheConfig.SHORT_TTL)

            # Register channel
            await self.channel_manager.register_channel(channel_name)

            return auth_data

        except Exception as e:
            logger.error(f"Channel authentication failed: {e}")
            raise

    async def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """Get channel information with caching"""
        cached_info = await self.channel_manager.get_channel_info(channel)
        if cached_info:
            return cached_info

        try:
            # Get client from pool
            client = self.connection_pool.get_client()

            # Get channel info from Pusher API
            info = client.channel_info(channel, info=["user_count", "subscription_count"])

            # Cache the result
            cache_key = f"pusher_channel_info:{channel}"
            await cache.set(cache_key, info, CacheConfig.MEDIUM_TTL)

            return info

        except Exception as e:
            logger.error(f"Failed to get channel info for {channel}: {e}")
            return {}

    async def close(self):
        """Shutdown the service"""
        self._running = False

        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        await self.connection_pool.close()
        logger.info("Optimized Pusher service closed")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "pusher_stats": self.stats.to_dict(),
            "channel_stats": self.channel_manager.get_channel_stats(),
            "pool_size": self.connection_pool.pool_size,
            "batch_config": {
                "batch_size": self.event_batcher.batch_size,
                "batch_timeout": self.event_batcher.batch_timeout,
            },
            "rate_limit": {"calls_per_second": self.rate_limiter.calls_per_second},
        }


# Global optimized service instance
_optimized_pusher_service: Optional[OptimizedPusherService] = None


async def get_optimized_pusher_service() -> OptimizedPusherService:
    """Get or create the optimized Pusher service"""
    global _optimized_pusher_service

    if _optimized_pusher_service is None:
        _optimized_pusher_service = OptimizedPusherService()
        await _optimized_pusher_service.initialize()

    return _optimized_pusher_service


# Convenience functions
async def trigger_optimized(
    channel: str,
    event: str,
    data: Dict[str, Any],
    socket_id: Optional[str] = None,
    immediate: bool = False,
) -> bool:
    """Trigger event using optimized service"""
    service = await get_optimized_pusher_service()
    return await service.trigger_event(channel, event, data, socket_id, immediate)


async def authenticate_optimized(
    socket_id: str,
    channel_name: str,
    user_id: Optional[str] = None,
    user_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Authenticate channel using optimized service"""
    service = await get_optimized_pusher_service()
    return await service.authenticate_channel(socket_id, channel_name, user_id, user_info)


async def get_pusher_health() -> Dict[str, Any]:
    """Get Pusher service health and performance metrics"""
    try:
        service = await get_optimized_pusher_service()
        return {
            "status": "healthy",
            "performance": service.get_performance_stats(),
            "optimization_enabled": True,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "optimization_enabled": False}


# Export main interfaces
__all__ = [
    "get_optimized_pusher_service",
    "trigger_optimized",
    "authenticate_optimized",
    "get_pusher_health",
    "OptimizedPusherService",
]
