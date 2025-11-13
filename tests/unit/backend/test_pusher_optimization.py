"""
Comprehensive test suite for Pusher Optimization module.

Tests connection pooling, event batching, rate limiting, channel management,
and performance statistics for the optimized Pusher service.

Target: >95% code coverage for Pusher optimization components.
"""

import asyncio
import time
from collections import defaultdict
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pusher.errors import PusherError

from apps.backend.services.pusher_optimized import (
    ChannelManager,
    ConnectionPool,
    EventBatcher,
    OptimizedPusherService,
    PusherEvent,
    PusherStats,
    RateLimiter,
    authenticate_optimized,
    get_optimized_pusher_service,
    get_pusher_health,
    trigger_optimized,
)


@pytest.mark.unit
class TestPusherEvent:
    """Test PusherEvent dataclass functionality."""

    def test_pusher_event_creation(self):
        """Test basic PusherEvent creation."""
        event = PusherEvent(
            channel="test-channel",
            event="test-event",
            data={"message": "hello"},
            socket_id="socket123",
        )

        assert event.channel == "test-channel"
        assert event.event == "test-event"
        assert event.data == {"message": "hello"}
        assert event.socket_id == "socket123"
        assert isinstance(event.timestamp, datetime)

    def test_pusher_event_without_socket_id(self):
        """Test PusherEvent creation without socket_id."""
        event = PusherEvent(channel="test-channel", event="test-event", data={"message": "hello"})

        assert event.socket_id is None
        assert event.channel == "test-channel"

    def test_pusher_event_timestamp_auto_generation(self):
        """Test automatic timestamp generation."""
        event = PusherEvent("channel", "event", {})
        assert event.timestamp is not None
        assert event.timestamp.tzinfo == timezone.utc

    def test_pusher_event_custom_timestamp(self):
        """Test PusherEvent with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = PusherEvent("channel", "event", {}, timestamp=custom_time)

        assert event.timestamp == custom_time

    def test_to_dict_conversion(self):
        """Test PusherEvent to dictionary conversion."""
        event = PusherEvent(
            channel="test-channel", event="test-event", data={"key": "value"}, socket_id="socket123"
        )

        event_dict = event.to_dict()

        expected = {
            "channel": "test-channel",
            "event": "test-event",
            "data": {"key": "value"},
            "socket_id": "socket123",
        }

        assert event_dict == expected

    def test_to_dict_without_socket_id(self):
        """Test to_dict with None socket_id."""
        event = PusherEvent("channel", "event", {"data": "test"})
        event_dict = event.to_dict()

        assert event_dict["socket_id"] is None


@pytest.mark.unit
class TestPusherStats:
    """Test PusherStats performance tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = PusherStats()

        assert stats.events_sent == 0
        assert stats.batch_events_sent == 0
        assert stats.failed_events == 0
        assert stats.total_latency == 0.0
        assert stats.connection_errors == 0
        assert stats.rate_limit_hits == 0
        assert stats.cache_hits == 0
        assert isinstance(stats.channel_subscriptions, defaultdict)

    def test_record_successful_event(self):
        """Test recording successful event."""
        stats = PusherStats()
        stats.record_event(success=True, latency=0.05, batch_size=1)

        assert stats.events_sent == 1
        assert stats.batch_events_sent == 0
        assert stats.failed_events == 0
        assert stats.total_latency == 0.05

    def test_record_batch_event(self):
        """Test recording successful batch event."""
        stats = PusherStats()
        stats.record_event(success=True, latency=0.1, batch_size=5)

        assert stats.events_sent == 1
        assert stats.batch_events_sent == 5
        assert stats.total_latency == 0.1

    def test_record_failed_event(self):
        """Test recording failed event."""
        stats = PusherStats()
        stats.record_event(success=False, latency=0.2)

        assert stats.events_sent == 0
        assert stats.failed_events == 1
        assert stats.total_latency == 0.2

    def test_record_various_events(self):
        """Test recording various types of events."""
        stats = PusherStats()

        stats.record_connection_error()
        stats.record_rate_limit()
        stats.record_cache_hit()
        stats.record_channel_subscription("test-channel")

        assert stats.connection_errors == 1
        assert stats.rate_limit_hits == 1
        assert stats.cache_hits == 1
        assert stats.channel_subscriptions["test-channel"] == 1

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = PusherStats()

        # Record some successful and failed events
        stats.record_event(success=True, latency=0.01)
        stats.record_event(success=True, latency=0.02)
        stats.record_event(success=False, latency=0.03)

        assert stats.success_rate == 2 / 3  # 2 successful out of 3 total

    def test_success_rate_no_events(self):
        """Test success rate with no events."""
        stats = PusherStats()
        assert stats.success_rate == 0.0

    def test_average_latency_calculation(self):
        """Test average latency calculation."""
        stats = PusherStats()

        stats.record_event(success=True, latency=0.01)
        stats.record_event(success=True, latency=0.03)
        stats.record_event(success=False, latency=0.05)

        assert stats.avg_latency == (0.01 + 0.03 + 0.05) / 3

    def test_to_dict_conversion(self):
        """Test statistics dictionary conversion."""
        stats = PusherStats()

        stats.record_event(success=True, latency=0.02, batch_size=3)
        stats.record_event(success=False, latency=0.08)
        stats.record_connection_error()
        stats.record_rate_limit()
        stats.record_cache_hit()
        stats.record_channel_subscription("popular-channel")
        stats.record_channel_subscription("popular-channel")
        stats.record_channel_subscription("less-popular")

        data = stats.to_dict()

        assert data["events_sent"] == 1
        assert data["batch_events_sent"] == 3
        assert data["failed_events"] == 1
        assert data["success_rate"] == 0.5
        assert data["avg_latency_ms"] == 50.0  # (0.02 + 0.08) / 2 * 1000
        assert data["connection_errors"] == 1
        assert data["rate_limit_hits"] == 1
        assert data["cache_hits"] == 1
        assert "popular_channels" in data
        assert data["popular_channels"]["popular-channel"] == 2


@pytest.mark.unit
class TestConnectionPool:
    """Test Pusher connection pool management."""

    @pytest.fixture
    def mock_settings(self):
        """Mock Pusher settings."""
        with patch("apps.backend.services.pusher_optimized.settings") as mock:
            mock.PUSHER_APP_ID = "test_app_id"
            mock.PUSHER_KEY = "test_key"
            mock.PUSHER_SECRET = "test_secret"
            mock.PUSHER_CLUSTER = "us2"
            mock.PUSHER_SSL = True
            yield mock

    @pytest.fixture
    def connection_pool(self):
        """Create connection pool instance."""
        return ConnectionPool(pool_size=3)

    @patch("pusher.Pusher")
    async def test_initialize_success(self, mock_pusher_class, connection_pool, mock_settings):
        """Test successful connection pool initialization."""
        mock_clients = [Mock() for _ in range(3)]
        mock_pusher_class.side_effect = mock_clients

        await connection_pool.initialize()

        assert connection_pool._initialized is True
        assert len(connection_pool.clients) == 3
        assert connection_pool.current_index == 0
        assert mock_pusher_class.call_count == 3

        # Verify correct configuration was passed
        call_args = mock_pusher_class.call_args[1]
        assert call_args["app_id"] == "test_app_id"
        assert call_args["key"] == "test_key"
        assert call_args["secret"] == "test_secret"
        assert call_args["cluster"] == "us2"
        assert call_args["ssl"] is True
        assert call_args["timeout"] == 10

    @patch("pusher.Pusher")
    async def test_initialize_error(self, mock_pusher_class, connection_pool, mock_settings):
        """Test initialization with connection error."""
        mock_pusher_class.side_effect = Exception("Pusher connection failed")

        with pytest.raises(Exception, match="Pusher connection failed"):
            await connection_pool.initialize()

        assert connection_pool._initialized is False

    async def test_double_initialization_prevention(self, connection_pool, mock_settings):
        """Test that double initialization is prevented."""
        with patch("pusher.Pusher") as mock_pusher:
            mock_pusher.return_value = Mock()

            # First initialization
            await connection_pool.initialize()
            first_init_call_count = mock_pusher.call_count

            # Second initialization should not create new clients
            await connection_pool.initialize()

            assert mock_pusher.call_count == first_init_call_count

    def test_get_client_round_robin(self, connection_pool):
        """Test round-robin client selection."""
        mock_clients = [Mock(), Mock(), Mock()]
        connection_pool._initialized = True
        connection_pool.clients = mock_clients

        # Get clients in round-robin fashion
        client1 = connection_pool.get_client()
        client2 = connection_pool.get_client()
        client3 = connection_pool.get_client()
        client4 = connection_pool.get_client()  # Should wrap around

        assert client1 == mock_clients[0]
        assert client2 == mock_clients[1]
        assert client3 == mock_clients[2]
        assert client4 == mock_clients[0]  # Wrapped around
        assert connection_pool.current_index == 1

    def test_get_client_not_initialized(self, connection_pool):
        """Test getting client when pool not initialized."""
        with pytest.raises(RuntimeError, match="Connection pool not initialized"):
            connection_pool.get_client()

    async def test_close_pool(self, connection_pool):
        """Test closing connection pool."""
        connection_pool._initialized = True
        connection_pool.clients = [Mock(), Mock()]

        await connection_pool.close()

        assert len(connection_pool.clients) == 0
        assert connection_pool._initialized is False


@pytest.mark.unit
class TestEventBatcher:
    """Test event batching functionality."""

    @pytest.fixture
    def batcher(self):
        """Create event batcher instance."""
        return EventBatcher(batch_size=3, batch_timeout=0.1)

    async def test_add_event_no_flush(self, batcher):
        """Test adding event that doesn't trigger flush."""
        event = PusherEvent("channel1", "event1", {"data": "test"})

        should_flush = await batcher.add_event(event)

        assert should_flush is False
        assert len(batcher.pending_events["channel1"]) == 1
        assert batcher.pending_events["channel1"][0] == event

    async def test_add_event_batch_size_flush(self, batcher):
        """Test adding events that trigger batch size flush."""
        events = [
            PusherEvent("channel1", "event1", {"data": "test1"}),
            PusherEvent("channel1", "event2", {"data": "test2"}),
            PusherEvent("channel2", "event3", {"data": "test3"}),
        ]

        # Add events one by one
        for i, event in enumerate(events):
            should_flush = await batcher.add_event(event)
            if i < 2:
                assert should_flush is False
            else:
                assert should_flush is True  # Third event should trigger flush

    async def test_add_event_timeout_flush(self, batcher):
        """Test adding event that triggers timeout flush."""
        event = PusherEvent("channel1", "event1", {"data": "test"})

        # Set last flush time to past to simulate timeout
        batcher.last_flush = time.time() - 0.2  # 0.2 seconds ago

        should_flush = await batcher.add_event(event)

        assert should_flush is True

    async def test_get_batches(self, batcher):
        """Test getting and clearing batches."""
        events = [
            PusherEvent("channel1", "event1", {"data": "test1"}),
            PusherEvent("channel1", "event2", {"data": "test2"}),
            PusherEvent("channel2", "event3", {"data": "test3"}),
        ]

        # Add events
        for event in events:
            await batcher.add_event(event)

        # Get batches
        batches = await batcher.get_batches()

        assert "channel1" in batches
        assert "channel2" in batches
        assert len(batches["channel1"]) == 2
        assert len(batches["channel2"]) == 1

        # Verify batches were cleared
        assert len(batcher.pending_events) == 0

    async def test_concurrent_access(self, batcher):
        """Test concurrent access to batcher."""

        async def add_events(channel_prefix, count):
            for i in range(count):
                event = PusherEvent(f"{channel_prefix}-{i}", "event", {"data": i})
                await batcher.add_event(event)

        # Add events concurrently
        await asyncio.gather(
            add_events("channel1", 5), add_events("channel2", 3), add_events("channel3", 2)
        )

        batches = await batcher.get_batches()
        total_events = sum(len(events) for events in batches.values())
        assert total_events == 10


@pytest.mark.unit
class TestChannelManager:
    """Test channel management functionality."""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for channel manager."""
        return AsyncMock()

    @pytest.fixture
    def channel_manager(self, mock_cache):
        """Create channel manager with mock cache."""
        manager = ChannelManager()
        # Mock the cache import
        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            yield manager

    async def test_register_channel(self, channel_manager, mock_cache):
        """Test registering a channel."""
        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            await channel_manager.register_channel("test-channel")

            assert "test-channel" in channel_manager.active_channels
            assert channel_manager.channel_stats["test-channel"]["last_activity"] is not None
            mock_cache.set.assert_called_once()

    async def test_record_event(self, channel_manager, mock_cache):
        """Test recording event for a channel."""
        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            await channel_manager.record_event("test-channel")

            assert "test-channel" in channel_manager.active_channels
            assert channel_manager.channel_stats["test-channel"]["events_sent"] == 1

    async def test_get_channel_info_cached(self, channel_manager, mock_cache):
        """Test getting cached channel information."""
        cached_info = {"active": True, "registered_at": "2023-01-01T00:00:00Z"}
        mock_cache.get.return_value = cached_info

        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            info = await channel_manager.get_channel_info("test-channel")

            assert info == cached_info
            mock_cache.get.assert_called_once()

    async def test_get_channel_info_not_cached(self, channel_manager, mock_cache):
        """Test getting channel information when not cached."""
        mock_cache.get.return_value = None

        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            info = await channel_manager.get_channel_info("test-channel")

            assert info is None

    def test_get_channel_stats(self, channel_manager):
        """Test getting channel statistics."""
        # Add some channel activity
        channel_manager.active_channels.add("channel1")
        channel_manager.active_channels.add("channel2")
        channel_manager.channel_stats["channel1"]["events_sent"] = 10
        channel_manager.channel_stats["channel2"]["events_sent"] = 5

        stats = channel_manager.get_channel_stats()

        assert stats["active_channels"] == 2
        assert "channel_stats" in stats
        assert "most_active" in stats
        assert len(stats["most_active"]) <= 10


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter with test settings."""
        return RateLimiter(calls_per_second=5)

    async def test_acquire_within_limit(self, rate_limiter):
        """Test acquiring permission within rate limit."""
        # Should be able to make up to 5 calls
        for _ in range(5):
            result = await rate_limiter.acquire()
            assert result is True

    async def test_acquire_exceed_limit(self, rate_limiter):
        """Test acquiring permission when exceeding rate limit."""
        # Make 5 calls to reach limit
        for _ in range(5):
            await rate_limiter.acquire()

        # 6th call should be denied
        result = await rate_limiter.acquire()
        assert result is False

    async def test_acquire_after_time_window(self, rate_limiter):
        """Test acquiring permission after time window expires."""
        # Fill up the rate limit
        for _ in range(5):
            await rate_limiter.acquire()

        # Wait for time window to expire
        await asyncio.sleep(1.1)

        # Should be able to make calls again
        result = await rate_limiter.acquire()
        assert result is True

    async def test_wait_for_slot(self, rate_limiter):
        """Test waiting for available rate limit slot."""
        # Fill up the rate limit
        for _ in range(5):
            await rate_limiter.acquire()

        # This should wait until a slot becomes available
        start_time = time.time()
        await rate_limiter.wait_for_slot()
        end_time = time.time()

        # Should have waited approximately 1 second
        assert end_time - start_time >= 1.0

    async def test_concurrent_acquire(self, rate_limiter):
        """Test concurrent rate limit acquisition."""

        async def try_acquire():
            return await rate_limiter.acquire()

        # Try to acquire 10 permits concurrently
        results = await asyncio.gather(*[try_acquire() for _ in range(10)])

        # Only 5 should succeed
        successful = sum(1 for result in results if result)
        assert successful == 5


@pytest.mark.unit
class TestOptimizedPusherService:
    """Test the main OptimizedPusherService class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock Pusher settings."""
        with patch("apps.backend.services.pusher_optimized.settings") as mock:
            mock.PUSHER_APP_ID = "test_app_id"
            mock.PUSHER_KEY = "test_key"
            mock.PUSHER_SECRET = "test_secret"
            mock.PUSHER_CLUSTER = "us2"
            mock.PUSHER_SSL = True
            yield mock

    @pytest.fixture
    def service(self):
        """Create OptimizedPusherService instance."""
        return OptimizedPusherService()

    @patch("apps.backend.services.pusher_optimized.ConnectionPool")
    async def test_initialize_success(self, mock_pool_class, service, mock_settings):
        """Test successful service initialization."""
        mock_pool = AsyncMock()
        mock_pool_class.return_value = mock_pool

        await service.initialize()

        mock_pool.initialize.assert_called_once()
        assert service._running is True
        assert service._batch_task is not None

    async def test_trigger_event_immediate(self, service):
        """Test triggering immediate event."""
        # Mock dependencies
        service.connection_pool = AsyncMock()
        service.channel_manager = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.stats = Mock()

        mock_client = Mock()
        service.connection_pool.get_client.return_value = mock_client
        service.rate_limiter.wait_for_slot = AsyncMock()

        result = await service.trigger_event(
            "test-channel", "test-event", {"message": "hello"}, immediate=True
        )

        assert result is True
        mock_client.trigger.assert_called_once()
        service.channel_manager.register_channel.assert_called_once_with("test-channel")

    async def test_trigger_event_batched(self, service):
        """Test triggering batched event."""
        service.channel_manager = AsyncMock()
        service.event_batcher = AsyncMock()
        service.event_batcher.add_event.return_value = False  # No flush needed

        result = await service.trigger_event(
            "test-channel", "test-event", {"message": "hello"}, immediate=False
        )

        assert result is True
        service.event_batcher.add_event.assert_called_once()

    async def test_trigger_event_with_flush(self, service):
        """Test triggering event that triggers batch flush."""
        service.channel_manager = AsyncMock()
        service.event_batcher = AsyncMock()
        service.event_batcher.add_event.return_value = True  # Flush needed
        service.event_batcher.get_batches.return_value = {
            "test-channel": [PusherEvent("test-channel", "test-event", {})]
        }

        # Mock batch sending
        service.connection_pool = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.stats = Mock()
        mock_client = Mock()
        service.connection_pool.get_client.return_value = mock_client

        with patch.object(service, "_send_batched_events") as mock_send_batches:
            result = await service.trigger_event(
                "test-channel", "test-event", {"message": "hello"}, immediate=False
            )

            assert result is True
            mock_send_batches.assert_called_once()

    async def test_send_single_event_success(self, service):
        """Test sending single event successfully."""
        # Mock dependencies
        service.connection_pool = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.stats = Mock()
        service.channel_manager = AsyncMock()

        mock_client = Mock()
        service.connection_pool.get_client.return_value = mock_client
        service.rate_limiter.wait_for_slot = AsyncMock()

        event = PusherEvent("test-channel", "test-event", {"data": "test"})

        result = await service._send_single_event(event)

        assert result is True
        mock_client.trigger.assert_called_once_with(
            "test-channel", "test-event", {"data": "test"}, socket_id=None
        )
        service.stats.record_event.assert_called_once()

    async def test_send_single_event_pusher_error(self, service):
        """Test sending single event with Pusher error."""
        service.connection_pool = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.stats = Mock()
        service.channel_manager = AsyncMock()

        mock_client = Mock()
        mock_client.trigger.side_effect = PusherError("API error")
        service.connection_pool.get_client.return_value = mock_client

        event = PusherEvent("test-channel", "test-event", {"data": "test"})

        result = await service._send_single_event(event)

        assert result is False
        service.stats.record_event.assert_called_with(False, 0)

    async def test_send_single_event_rate_limit_error(self, service):
        """Test sending single event with rate limit error."""
        service.connection_pool = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.stats = Mock()
        service.channel_manager = AsyncMock()

        mock_client = Mock()
        mock_client.trigger.side_effect = PusherError("Rate limit exceeded")
        service.connection_pool.get_client.return_value = mock_client

        event = PusherEvent("test-channel", "test-event", {"data": "test"})

        result = await service._send_single_event(event)

        assert result is False
        service.stats.record_rate_limit.assert_called_once()

    async def test_send_batched_events(self, service):
        """Test sending batched events."""
        # Setup mocks
        service.rate_limiter = AsyncMock()
        service.connection_pool = AsyncMock()
        service.stats = Mock()
        service.channel_manager = AsyncMock()

        mock_client = Mock()
        service.connection_pool.get_client.return_value = mock_client
        service.rate_limiter.wait_for_slot = AsyncMock()

        # Create test batch
        events = [
            PusherEvent("test-channel", "event1", {"data": "test1"}),
            PusherEvent("test-channel", "event2", {"data": "test2"}),
        ]
        batches = {"test-channel": events}

        await service._send_batched_events(batches)

        # Should use batch trigger for multiple events of same type
        mock_client.trigger_batch.assert_called_once()
        service.stats.record_event.assert_called_with(True, pytest.approx(0, abs=0.1), 2)

    async def test_authenticate_channel_cached(self, service):
        """Test channel authentication with cached result."""
        mock_cache = AsyncMock()
        cached_auth = {"auth": "cached_token", "channel_data": "{}"}
        mock_cache.get.return_value = cached_auth

        service.stats = Mock()

        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            result = await service.authenticate_channel("socket123", "private-channel")

            assert result == cached_auth
            service.stats.record_cache_hit.assert_called_once()

    async def test_authenticate_channel_not_cached(self, service):
        """Test channel authentication without cached result."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        service.connection_pool = AsyncMock()
        service.channel_manager = AsyncMock()
        service.stats = Mock()

        mock_client = Mock()
        auth_data = {"auth": "new_token"}
        mock_client.authenticate.return_value = auth_data
        service.connection_pool.get_client.return_value = mock_client

        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            result = await service.authenticate_channel("socket123", "private-channel")

            assert result == auth_data
            mock_cache.set.assert_called_once()
            service.channel_manager.register_channel.assert_called_once()

    async def test_authenticate_presence_channel(self, service):
        """Test presence channel authentication."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        service.connection_pool = AsyncMock()
        service.channel_manager = AsyncMock()
        service.stats = Mock()

        mock_client = Mock()
        auth_data = {"auth": "presence_token", "channel_data": "{}"}
        mock_client.authenticate.return_value = auth_data
        service.connection_pool.get_client.return_value = mock_client

        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            result = await service.authenticate_channel(
                "socket123", "presence-channel", user_id="user123", user_info={"name": "Test"}
            )

            assert result == auth_data
            # Verify presence channel authentication was called with custom data
            mock_client.authenticate.assert_called_with(
                channel="presence-channel",
                socket_id="socket123",
                custom_data={"user_id": "user123", "user_info": {"name": "Test"}},
            )

    async def test_authenticate_presence_channel_no_user_id(self, service):
        """Test presence channel authentication without user ID."""
        with pytest.raises(ValueError, match="User ID required for presence channel"):
            await service.authenticate_channel("socket123", "presence-channel")

    async def test_get_channel_info_cached(self, service):
        """Test getting cached channel information."""
        service.channel_manager = AsyncMock()
        cached_info = {"subscriber_count": 5}
        service.channel_manager.get_channel_info.return_value = cached_info

        result = await service.get_channel_info("test-channel")

        assert result == cached_info

    async def test_get_channel_info_from_api(self, service):
        """Test getting channel information from Pusher API."""
        service.channel_manager = AsyncMock()
        service.channel_manager.get_channel_info.return_value = None

        service.connection_pool = AsyncMock()
        mock_client = Mock()
        api_info = {"occupied": True, "user_count": 3}
        mock_client.channel_info.return_value = api_info
        service.connection_pool.get_client.return_value = mock_client

        mock_cache = AsyncMock()
        with patch("apps.backend.services.pusher_optimized.cache", mock_cache):
            result = await service.get_channel_info("test-channel")

            assert result == api_info
            mock_cache.set.assert_called_once()

    async def test_get_channel_info_error(self, service):
        """Test getting channel information with API error."""
        service.channel_manager = AsyncMock()
        service.channel_manager.get_channel_info.return_value = None

        service.connection_pool = AsyncMock()
        mock_client = Mock()
        mock_client.channel_info.side_effect = PusherError("API error")
        service.connection_pool.get_client.return_value = mock_client

        result = await service.get_channel_info("test-channel")

        assert result == {}

    async def test_close_service(self, service):
        """Test closing the service."""
        # Mock batch task
        mock_task = AsyncMock()
        service._batch_task = mock_task
        service._running = True

        service.connection_pool = AsyncMock()

        await service.close()

        assert service._running is False
        mock_task.cancel.assert_called_once()
        service.connection_pool.close.assert_called_once()

    def test_get_performance_stats(self, service):
        """Test getting performance statistics."""
        service.stats = Mock()
        service.stats.to_dict.return_value = {"events_sent": 100}

        service.channel_manager = Mock()
        service.channel_manager.get_channel_stats.return_value = {"active_channels": 5}

        service.connection_pool = Mock()
        service.connection_pool.pool_size = 5

        service.event_batcher = Mock()
        service.event_batcher.batch_size = 10
        service.event_batcher.batch_timeout = 0.1

        service.rate_limiter = Mock()
        service.rate_limiter.calls_per_second = 100

        stats = service.get_performance_stats()

        assert stats["pusher_stats"]["events_sent"] == 100
        assert stats["channel_stats"]["active_channels"] == 5
        assert stats["pool_size"] == 5
        assert stats["batch_config"]["batch_size"] == 10
        assert stats["rate_limit"]["calls_per_second"] == 100


@pytest.mark.unit
class TestGlobalServiceFunctions:
    """Test global service functions and convenience methods."""

    async def test_get_optimized_pusher_service_singleton(self):
        """Test singleton behavior of get_optimized_pusher_service."""
        # Clear global instance
        global _optimized_pusher_service
        _optimized_pusher_service = None

        with patch("apps.backend.services.pusher_optimized.OptimizedPusherService") as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance

            # First call should create instance
            service1 = await get_optimized_pusher_service()
            # Second call should return same instance
            service2 = await get_optimized_pusher_service()

            assert service1 == service2
            mock_class.assert_called_once()
            mock_instance.initialize.assert_called_once()

    async def test_trigger_optimized(self):
        """Test trigger_optimized convenience function."""
        with patch(
            "apps.backend.services.pusher_optimized.get_optimized_pusher_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.trigger_event.return_value = True
            mock_get_service.return_value = mock_service

            result = await trigger_optimized(
                "test-channel",
                "test-event",
                {"message": "hello"},
                socket_id="socket123",
                immediate=True,
            )

            assert result is True
            mock_service.trigger_event.assert_called_once_with(
                "test-channel", "test-event", {"message": "hello"}, "socket123", True
            )

    async def test_authenticate_optimized(self):
        """Test authenticate_optimized convenience function."""
        with patch(
            "apps.backend.services.pusher_optimized.get_optimized_pusher_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            auth_data = {"auth": "token123"}
            mock_service.authenticate_channel.return_value = auth_data
            mock_get_service.return_value = mock_service

            result = await authenticate_optimized(
                "socket123", "private-channel", user_id="user456", user_info={"name": "Test User"}
            )

            assert result == auth_data
            mock_service.authenticate_channel.assert_called_once_with(
                "socket123", "private-channel", "user456", {"name": "Test User"}
            )

    async def test_get_pusher_health_success(self):
        """Test successful Pusher health check."""
        with patch(
            "apps.backend.services.pusher_optimized.get_optimized_pusher_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_performance_stats.return_value = {
                "pusher_stats": {"events_sent": 100},
                "channel_stats": {"active_channels": 5},
            }
            mock_get_service.return_value = mock_service

            health = await get_pusher_health()

            assert health["status"] == "healthy"
            assert health["optimization_enabled"] is True
            assert health["performance"]["pusher_stats"]["events_sent"] == 100

    async def test_get_pusher_health_error(self):
        """Test Pusher health check with error."""
        with patch(
            "apps.backend.services.pusher_optimized.get_optimized_pusher_service"
        ) as mock_get_service:
            mock_get_service.side_effect = Exception("Pusher service error")

            health = await get_pusher_health()

            assert health["status"] == "unhealthy"
            assert health["optimization_enabled"] is False
            assert "error" in health


@pytest.mark.integration
class TestPusherOptimizationIntegration:
    """Integration tests for Pusher optimization components."""

    @pytest.fixture
    def mock_pusher_setup(self):
        """Setup mock Pusher environment for integration testing."""
        with patch("apps.backend.services.pusher_optimized.settings") as mock_settings:
            mock_settings.PUSHER_APP_ID = "test_app_id"
            mock_settings.PUSHER_KEY = "test_key"
            mock_settings.PUSHER_SECRET = "test_secret"
            mock_settings.PUSHER_CLUSTER = "us2"
            mock_settings.PUSHER_SSL = True

            with patch("pusher.Pusher") as mock_pusher_class:
                mock_clients = []

                def create_mock_client(*args, **kwargs):
                    client = Mock()
                    client.trigger = Mock()
                    client.trigger_batch = Mock()
                    client.authenticate = Mock(return_value={"auth": "test_token"})
                    client.channel_info = Mock(return_value={"occupied": True})
                    mock_clients.append(client)
                    return client

                mock_pusher_class.side_effect = create_mock_client

                yield {
                    "settings": mock_settings,
                    "pusher_class": mock_pusher_class,
                    "clients": mock_clients,
                }

    async def test_full_optimization_workflow(self, mock_pusher_setup):
        """Test complete optimization workflow."""
        service = OptimizedPusherService()

        # Initialize service
        await service.initialize()

        # Wait a bit for batch processor to start
        await asyncio.sleep(0.01)

        # Test event triggering
        result = await service.trigger_event(
            "test-channel", "test-event", {"message": "hello world"}
        )

        assert result is True

        # Test authentication
        auth_result = await service.authenticate_channel("socket123", "private-test")
        assert "auth" in auth_result

        # Test channel info
        channel_info = await service.get_channel_info("test-channel")
        assert channel_info.get("occupied") is True

        # Test statistics
        stats = service.get_performance_stats()
        assert "pusher_stats" in stats
        assert "channel_stats" in stats

        # Clean up
        await service.close()

    async def test_batch_processing_integration(self, mock_pusher_setup):
        """Test integration of batch processing system."""
        service = OptimizedPusherService()
        await service.initialize()

        # Add multiple events that should be batched
        events_to_send = [("channel1", "event1", {"data": f"message {i}"}) for i in range(5)]

        # Send events rapidly (should trigger batching)
        tasks = []
        for channel, event, data in events_to_send:
            task = service.trigger_event(channel, event, data, immediate=False)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)

        # Wait for batch processing
        await asyncio.sleep(0.15)  # Longer than batch timeout

        # Verify statistics
        stats = service.get_performance_stats()
        assert stats["pusher_stats"]["events_sent"] >= 1

        await service.close()

    async def test_error_handling_integration(self, mock_pusher_setup):
        """Test error handling across optimization components."""
        # Setup service with error-prone client
        service = OptimizedPusherService()
        await service.initialize()

        # Mock client to raise errors
        for client in mock_pusher_setup["clients"]:
            client.trigger.side_effect = PusherError("Test error")

        # Attempt to send event
        result = await service.trigger_event(
            "test-channel", "test-event", {"data": "test"}, immediate=True
        )

        assert result is False

        # Check that error was recorded in statistics
        stats = service.get_performance_stats()
        assert stats["pusher_stats"]["failed_events"] >= 1

        await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
