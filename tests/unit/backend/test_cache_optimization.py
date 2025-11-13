"""
Comprehensive test suite for Redis Cache Layer optimization module.

Tests cache decorator functionality, invalidation strategies, connection pooling,
serialization, compression, statistics tracking, and error handling.

Target: >95% code coverage for cache optimization components.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis.asyncio as redis

from apps.backend.core.cache import (
    CacheConfig,
    CacheInvalidator,
    CacheKey,
    CacheSerializer,
    CacheStats,
    CacheWarmer,
    RedisCache,
    RedisConnectionManager,
    cache_dashboard,
    cache_result,
    cached,
    get_cache_health,
    get_cached_dashboard,
    initialize_cache,
)


@pytest.mark.unit
class TestCacheConfig:
    """Test cache configuration constants and settings."""

    def test_ttl_constants(self):
        """Test TTL constant values."""
        assert CacheConfig.DEFAULT_TTL == 300
        assert CacheConfig.SHORT_TTL == 60
        assert CacheConfig.MEDIUM_TTL == 900
        assert CacheConfig.LONG_TTL == 3600
        assert CacheConfig.VERY_LONG_TTL == 86400

    def test_prefix_constants(self):
        """Test cache key prefix constants."""
        assert CacheConfig.PREFIX_USER == "user"
        assert CacheConfig.PREFIX_DASHBOARD == "dashboard"
        assert CacheConfig.PREFIX_CONTENT == "content"
        assert CacheConfig.PREFIX_AGENT == "agent"
        assert CacheConfig.PREFIX_API == "api"
        assert CacheConfig.PREFIX_QUERY == "query"

    def test_pool_configuration(self):
        """Test connection pool configuration."""
        assert CacheConfig.POOL_MIN_CONNECTIONS == 10
        assert CacheConfig.POOL_MAX_CONNECTIONS == 50
        assert CacheConfig.POOL_RETRY_ON_TIMEOUT is True
        assert CacheConfig.COMPRESSION_THRESHOLD == 1024


@pytest.mark.unit
class TestCacheKey:
    """Test cache key generation utilities."""

    def test_generate_simple_key(self):
        """Test simple cache key generation."""
        key = CacheKey.generate("prefix", "arg1", "arg2")
        assert key == "prefix:arg1:arg2"

    def test_generate_with_kwargs(self):
        """Test cache key generation with keyword arguments."""
        key = CacheKey.generate("prefix", "arg1", user="123", role="admin")
        assert "prefix:arg1" in key
        assert "role:admin" in key
        assert "user:123" in key

    def test_generate_with_complex_objects(self):
        """Test cache key generation with complex objects."""
        complex_obj = {"nested": {"data": [1, 2, 3]}}
        key = CacheKey.generate("prefix", complex_obj)
        assert key.startswith("prefix:")
        assert len(key.split(":")) == 2  # prefix + hashed object

    def test_user_dashboard_key(self):
        """Test user dashboard specific key generation."""
        key = CacheKey.user_dashboard(123, "student")
        assert key == "dashboard:123:student"

    def test_api_response_key(self):
        """Test API response key generation."""
        key = CacheKey.api_response("users", limit=10, offset=0)
        assert "api:users" in key
        assert "limit:10" in key
        assert "offset:0" in key

    def test_database_query_key(self):
        """Test database query key generation."""
        query_hash = "abc123"
        key = CacheKey.database_query(query_hash, "param1", "param2")
        assert key == "query:abc123:param1:param2"

    def test_key_consistency(self):
        """Test that identical inputs generate identical keys."""
        key1 = CacheKey.generate("prefix", "arg", value=42)
        key2 = CacheKey.generate("prefix", "arg", value=42)
        assert key1 == key2

    def test_key_uniqueness(self):
        """Test that different inputs generate different keys."""
        key1 = CacheKey.generate("prefix", "arg1")
        key2 = CacheKey.generate("prefix", "arg2")
        assert key1 != key2


@pytest.mark.unit
class TestCacheSerializer:
    """Test cache serialization and compression."""

    def test_serialize_string(self):
        """Test string serialization."""
        data = CacheSerializer.serialize("test string")
        assert isinstance(data, bytes)
        assert data == b"test string"

    def test_serialize_bytes(self):
        """Test bytes serialization."""
        original = b"test bytes"
        data = CacheSerializer.serialize(original)
        assert data == original

    def test_serialize_complex_object(self):
        """Test complex object serialization."""
        obj = {"key": "value", "number": 42, "list": [1, 2, 3]}
        data = CacheSerializer.serialize(obj)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_serialize_with_compression(self):
        """Test serialization with compression for large data."""
        # Create large data to trigger compression
        large_data = {"data": "x" * 2000}  # Exceeds compression threshold
        serialized = CacheSerializer.serialize(large_data)
        assert isinstance(serialized, bytes)
        assert serialized.startswith(b"GZIP:")

    def test_deserialize_string(self):
        """Test string deserialization."""
        original = "test string"
        serialized = CacheSerializer.serialize(original)
        deserialized = CacheSerializer.deserialize(serialized)
        assert deserialized == original

    def test_deserialize_complex_object(self):
        """Test complex object deserialization."""
        original = {"key": "value", "number": 42, "list": [1, 2, 3]}
        serialized = CacheSerializer.serialize(original)
        deserialized = CacheSerializer.deserialize(serialized)
        assert deserialized == original

    def test_deserialize_compressed_data(self):
        """Test deserialization of compressed data."""
        large_data = {"data": "x" * 2000}
        serialized = CacheSerializer.serialize(large_data)
        deserialized = CacheSerializer.deserialize(serialized)
        assert deserialized == large_data

    def test_deserialize_empty_data(self):
        """Test deserialization of empty data."""
        result = CacheSerializer.deserialize(b"")
        assert result is None

    def test_deserialize_invalid_pickle(self):
        """Test graceful handling of invalid pickle data."""
        invalid_data = b"invalid pickle data"
        result = CacheSerializer.deserialize(invalid_data)
        assert result == "invalid pickle data"

    def test_deserialize_invalid_utf8(self):
        """Test handling of invalid UTF-8 data."""
        invalid_utf8 = b"\xff\xfe"
        result = CacheSerializer.deserialize(invalid_utf8)
        assert result == invalid_utf8


@pytest.mark.unit
class TestCacheStats:
    """Test cache statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.errors == 0
        assert stats.total_time == 0.0

    def test_record_hit(self):
        """Test recording cache hits."""
        stats = CacheStats()
        stats.record_hit(0.01)
        assert stats.hits == 1
        assert stats.total_time == 0.01

    def test_record_miss(self):
        """Test recording cache misses."""
        stats = CacheStats()
        stats.record_miss(0.05)
        assert stats.misses == 1
        assert stats.total_time == 0.05

    def test_record_operations(self):
        """Test recording various operations."""
        stats = CacheStats()
        stats.record_set()
        stats.record_delete()
        stats.record_error()

        assert stats.sets == 1
        assert stats.deletes == 1
        assert stats.errors == 1

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        stats.record_hit(0.01)
        stats.record_hit(0.01)
        stats.record_miss(0.05)

        assert stats.hit_rate == 2 / 3  # 2 hits out of 3 total

    def test_hit_rate_zero_operations(self):
        """Test hit rate with no operations."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_average_time_calculation(self):
        """Test average time calculation."""
        stats = CacheStats()
        stats.record_hit(0.01)
        stats.record_miss(0.05)

        assert abs(stats.avg_time - 0.03) < 1e-10  # (0.01 + 0.05) / 2

    def test_to_dict(self):
        """Test statistics dictionary conversion."""
        stats = CacheStats()
        stats.record_hit(0.01)
        stats.record_miss(0.05)
        stats.record_set()

        data = stats.to_dict()
        assert data["hits"] == 1
        assert data["misses"] == 1
        assert data["sets"] == 1
        assert data["hit_rate"] == 0.5
        assert data["avg_time_ms"] == 30.0  # 0.03 * 1000


@pytest.mark.unit
class TestRedisConnectionManager:
    """Test Redis connection pool management."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("apps.backend.core.cache.settings") as mock:
            mock.REDIS_URL = "redis://localhost:6379/0"
            yield mock

    @pytest.fixture
    def connection_manager(self):
        """Create fresh connection manager for testing."""
        return RedisConnectionManager()

    @patch("redis.asyncio.ConnectionPool.from_url")
    @patch("redis.asyncio.Redis")
    async def test_initialize_success(
        self, mock_redis, mock_pool, connection_manager, mock_settings
    ):
        """Test successful connection pool initialization."""
        # Mock pool and client
        mock_pool_instance = Mock()
        mock_pool.return_value = mock_pool_instance

        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        await connection_manager.initialize()

        assert connection_manager.pool == mock_pool_instance
        assert connection_manager.client == mock_client
        mock_client.ping.assert_called_once()

    @patch("redis.asyncio.ConnectionPool.from_url")
    async def test_initialize_connection_error(self, mock_pool, connection_manager, mock_settings):
        """Test initialization with connection error."""
        mock_pool.side_effect = redis.ConnectionError("Connection failed")

        with pytest.raises(redis.ConnectionError):
            await connection_manager.initialize()

    async def test_get_client_not_initialized(self, connection_manager):
        """Test getting client when not initialized."""
        with patch.object(connection_manager, "initialize") as mock_init:
            mock_init.return_value = None
            connection_manager.client = Mock()

            client = await connection_manager.get_client()
            mock_init.assert_called_once()
            assert client == connection_manager.client

    async def test_get_client_already_initialized(self, connection_manager):
        """Test getting client when already initialized."""
        mock_client = Mock()
        connection_manager.client = mock_client

        client = await connection_manager.get_client()
        assert client == mock_client

    async def test_close_connections(self, connection_manager):
        """Test closing connections."""
        mock_client = AsyncMock()
        mock_pool = AsyncMock()

        connection_manager.client = mock_client
        connection_manager.pool = mock_pool

        await connection_manager.close()

        mock_client.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()

    async def test_double_initialization_prevention(self, connection_manager, mock_settings):
        """Test that double initialization is prevented."""
        with patch("redis.asyncio.ConnectionPool.from_url") as mock_pool:
            with patch("redis.asyncio.Redis") as mock_redis:
                mock_client = AsyncMock()
                mock_redis.return_value = mock_client
                mock_client.ping.return_value = True

                # First initialization
                await connection_manager.initialize()
                first_pool = connection_manager.pool

                # Second initialization should not create new pool
                await connection_manager.initialize()
                assert connection_manager.pool == first_pool

                # Pool creation should only be called once
                assert mock_pool.call_count == 1


@pytest.mark.unit
class TestRedisCache:
    """Test Redis cache implementation."""

    @pytest.fixture
    def mock_client(self):
        """Mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def cache_instance(self, mock_client):
        """Create cache instance with mocked client."""
        cache = RedisCache()
        cache.get_client = AsyncMock(return_value=mock_client)
        return cache

    async def test_get_hit(self, cache_instance, mock_client):
        """Test cache get with hit."""
        test_data = {"key": "value"}
        serialized_data = CacheSerializer.serialize(test_data)
        mock_client.get.return_value = serialized_data

        result = await cache_instance.get("test_key")

        assert result == test_data
        mock_client.get.assert_called_once_with("test_key")
        assert cache_instance.stats.hits == 1
        assert cache_instance.stats.misses == 0

    async def test_get_miss(self, cache_instance, mock_client):
        """Test cache get with miss."""
        mock_client.get.return_value = None

        result = await cache_instance.get("test_key")

        assert result is None
        assert cache_instance.stats.hits == 0
        assert cache_instance.stats.misses == 1

    async def test_get_error_handling(self, cache_instance, mock_client):
        """Test cache get with Redis error."""
        mock_client.get.side_effect = redis.ConnectionError("Connection lost")

        result = await cache_instance.get("test_key")

        assert result is None
        assert cache_instance.stats.errors == 1

    async def test_set_success(self, cache_instance, mock_client):
        """Test successful cache set."""
        mock_client.setex.return_value = True

        result = await cache_instance.set("test_key", "test_value", 300)

        assert result is True
        mock_client.setex.assert_called_once()
        assert cache_instance.stats.sets == 1

    async def test_set_error_handling(self, cache_instance, mock_client):
        """Test cache set with error."""
        mock_client.setex.side_effect = redis.ConnectionError("Connection lost")

        result = await cache_instance.set("test_key", "test_value", 300)

        assert result is False
        assert cache_instance.stats.errors == 1

    async def test_delete_success(self, cache_instance, mock_client):
        """Test successful cache delete."""
        mock_client.delete.return_value = 1

        result = await cache_instance.delete("test_key")

        assert result is True
        mock_client.delete.assert_called_once_with("test_key")
        assert cache_instance.stats.deletes == 1

    async def test_delete_pattern(self, cache_instance, mock_client):
        """Test deleting keys by pattern."""
        mock_client.keys.return_value = ["key1", "key2", "key3"]
        mock_client.delete.return_value = 3

        result = await cache_instance.delete_pattern("test:*")

        assert result == 3
        mock_client.keys.assert_called_once_with("test:*")
        mock_client.delete.assert_called_once_with("key1", "key2", "key3")

    async def test_delete_pattern_no_keys(self, cache_instance, mock_client):
        """Test deleting pattern with no matching keys."""
        mock_client.keys.return_value = []

        result = await cache_instance.delete_pattern("test:*")

        assert result == 0
        mock_client.delete.assert_not_called()

    async def test_mget(self, cache_instance, mock_client):
        """Test multiple get operation."""
        test_data = [b"value1", None, b"value3"]
        mock_client.mget.return_value = test_data

        result = await cache_instance.mget(["key1", "key2", "key3"])

        assert len(result) == 3
        assert result[0] == "value1"  # Deserialized
        assert result[1] is None
        assert result[2] == "value3"  # Deserialized

    async def test_mget_error(self, cache_instance, mock_client):
        """Test mget with error."""
        mock_client.mget.side_effect = redis.ConnectionError("Connection lost")

        result = await cache_instance.mget(["key1", "key2"])

        assert result == [None, None]
        assert cache_instance.stats.errors == 1

    def test_get_stats(self, cache_instance):
        """Test getting cache statistics."""
        # Simulate some operations
        cache_instance.stats.record_hit(0.01)
        cache_instance.stats.record_miss(0.05)
        cache_instance.stats.record_set()

        stats = cache_instance.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 0.5


@pytest.mark.unit
class TestCachedDecorator:
    """Test the @cached decorator functionality."""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache instance."""
        with patch("apps.backend.core.cache._cache") as mock:
            yield mock

    async def test_cached_decorator_hit(self, mock_cache):
        """Test cached decorator with cache hit."""
        mock_cache.get.return_value = "cached_result"

        @cached(ttl=300)
        async def test_function(arg1, arg2):
            return f"computed_{arg1}_{arg2}"

        result = await test_function("a", "b")

        assert result == "cached_result"
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()

    async def test_cached_decorator_miss(self, mock_cache):
        """Test cached decorator with cache miss."""
        mock_cache.get.return_value = None

        @cached(ttl=300)
        async def test_function(arg1, arg2):
            return f"computed_{arg1}_{arg2}"

        result = await test_function("a", "b")

        assert result == "computed_a_b"
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    async def test_cached_decorator_custom_key_func(self, mock_cache):
        """Test cached decorator with custom key function."""
        mock_cache.get.return_value = None

        def custom_key(*args, **kwargs):
            return f"custom:{args[0]}"

        @cached(key_func=custom_key, ttl=300)
        async def test_function(arg1):
            return f"computed_{arg1}"

        result = await test_function("test")

        assert result == "computed_test"
        # Verify custom key was used
        mock_cache.get.assert_called_once()
        call_args = mock_cache.get.call_args[0]
        assert call_args[0] == "custom:test"

    async def test_cached_decorator_sync_function(self, mock_cache):
        """Test cached decorator with synchronous function."""
        mock_cache.get.return_value = None

        @cached(ttl=300)
        def sync_function(arg1):
            return f"sync_computed_{arg1}"

        result = await sync_function("test")

        assert result == "sync_computed_test"
        mock_cache.set.assert_called_once()


@pytest.mark.unit
class TestCacheWarmer:
    """Test cache warming functionality."""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache instance."""
        return Mock()

    @pytest.fixture
    def warmer(self, mock_cache):
        """Create cache warmer instance."""
        return CacheWarmer(mock_cache)

    @patch("apps.backend.core.cache.db_service")
    async def test_warm_user_dashboard_success(self, mock_db_service, warmer, mock_cache):
        """Test successful dashboard cache warming."""
        mock_dashboard_data = {"user_id": 123, "role": "student"}
        mock_db_service.get_dashboard_data.return_value = mock_dashboard_data
        mock_cache.set.return_value = True

        await warmer.warm_user_dashboard(123, "student")

        mock_db_service.get_dashboard_data.assert_called_once_with("student", 123)
        mock_cache.set.assert_called_once()

    @patch("apps.backend.core.cache.db_service")
    async def test_warm_user_dashboard_db_error(self, mock_db_service, warmer, mock_cache):
        """Test dashboard warming with database error."""
        mock_db_service.get_dashboard_data.side_effect = Exception("DB error")

        # Should not raise exception, just log error
        await warmer.warm_user_dashboard(123, "student")

        mock_cache.set.assert_not_called()


@pytest.mark.unit
class TestCacheInvalidator:
    """Test cache invalidation functionality."""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache instance."""
        return AsyncMock()

    @pytest.fixture
    def invalidator(self, mock_cache):
        """Create cache invalidator instance."""
        return CacheInvalidator(mock_cache)

    async def test_invalidate_user_data(self, invalidator, mock_cache):
        """Test invalidating user data."""
        mock_cache.delete_pattern.return_value = 5

        await invalidator.invalidate_user_data(123)

        mock_cache.delete_pattern.assert_called_once_with("*:123:*")

    async def test_invalidate_dashboard_data(self, invalidator, mock_cache):
        """Test invalidating specific dashboard data."""
        await invalidator.invalidate_dashboard_data(123, "student")

        expected_key = CacheKey.user_dashboard(123, "student")
        mock_cache.delete.assert_called_once_with(expected_key)


@pytest.mark.unit
class TestCacheResultDecorator:
    """Test the legacy cache_result decorator."""

    async def test_cache_result_async_function(self):
        """Test cache_result decorator with async function."""
        call_count = 0

        @cache_result(ttl=300)
        async def test_function(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"

        with patch("apps.backend.core.cache._cache") as mock_cache:
            mock_cache.get.side_effect = [None, "cached_result"]

            # First call - cache miss
            result1 = await test_function("test")
            assert result1 == "result_test"
            assert call_count == 1

            # Second call - cache hit
            result2 = await test_function("test")
            assert result2 == "cached_result"
            assert call_count == 1  # Function not called again

    def test_cache_result_sync_function(self):
        """Test cache_result decorator with sync function."""

        @cache_result(ttl=300)
        def sync_function(arg):
            return f"sync_result_{arg}"

        result = sync_function("test")
        assert result == "sync_result_test"


@pytest.mark.unit
class TestCacheHealthAndMetrics:
    """Test cache health monitoring and metrics."""

    @patch("apps.backend.core.cache._connection_manager")
    async def test_get_cache_health_success(self, mock_manager):
        """Test successful cache health check."""
        mock_client = AsyncMock()
        mock_manager.get_client.return_value = mock_client
        mock_client.info.return_value = {
            "used_memory_human": "10MB",
            "used_memory_peak_human": "15MB",
            "mem_fragmentation_ratio": "1.2",
            "connected_clients": "5",
            "blocked_clients": "0",
        }

        with patch("apps.backend.core.cache.cache") as mock_cache:
            mock_cache.get_stats.return_value = {"hits": 100, "misses": 20}

            health = await get_cache_health()

            assert health["status"] == "healthy"
            assert health["stats"]["hits"] == 100
            assert health["memory"]["used"] == "10MB"
            assert health["connections"]["connected_clients"] == "5"

    @patch("apps.backend.core.cache._connection_manager")
    async def test_get_cache_health_error(self, mock_manager):
        """Test cache health check with error."""
        mock_manager.get_client.side_effect = redis.ConnectionError("Connection failed")

        health = await get_cache_health()

        assert health["status"] == "unhealthy"
        assert "error" in health
        assert "stats" in health


@pytest.mark.unit
class TestCacheConvenienceFunctions:
    """Test convenience functions for common cache operations."""

    async def test_get_cached_dashboard(self):
        """Test getting cached dashboard data."""
        with patch("apps.backend.core.cache.cache") as mock_cache:
            mock_cache.get.return_value = {"user_id": 123, "role": "student"}

            result = await get_cached_dashboard(123, "student")

            assert result["user_id"] == 123
            expected_key = CacheKey.user_dashboard(123, "student")
            mock_cache.get.assert_called_once_with(expected_key)

    async def test_cache_dashboard(self):
        """Test caching dashboard data."""
        dashboard_data = {"user_id": 123, "role": "student"}

        with patch("apps.backend.core.cache.cache") as mock_cache:
            await cache_dashboard(123, "student", dashboard_data)

            expected_key = CacheKey.user_dashboard(123, "student")
            mock_cache.set.assert_called_once_with(
                expected_key, dashboard_data, CacheConfig.MEDIUM_TTL
            )


@pytest.mark.unit
class TestCacheInitialization:
    """Test cache system initialization."""

    @patch("apps.backend.core.cache._connection_manager")
    async def test_initialize_cache_success(self, mock_manager):
        """Test successful cache initialization."""
        mock_manager.initialize.return_value = None

        await initialize_cache()

        mock_manager.initialize.assert_called_once()

    @patch("apps.backend.core.cache._connection_manager")
    async def test_initialize_cache_error(self, mock_manager):
        """Test cache initialization with error."""
        mock_manager.initialize.side_effect = redis.ConnectionError("Connection failed")

        # Should not raise exception, just log error
        await initialize_cache()


@pytest.mark.unit
class TestCacheIntegration:
    """Integration tests for cache components working together."""

    @pytest.fixture
    def isolated_cache(self):
        """Create isolated cache instance for testing."""
        cache = RedisCache()
        cache.stats = CacheStats()
        return cache

    async def test_cache_workflow_complete(self, isolated_cache):
        """Test complete cache workflow with mock Redis."""
        mock_client = AsyncMock()
        isolated_cache.get_client = AsyncMock(return_value=mock_client)

        # Test set operation
        mock_client.setex.return_value = True
        result = await isolated_cache.set("test_key", {"data": "test"}, 300)
        assert result is True

        # Test get operation (cache hit)
        test_data = {"data": "test"}
        mock_client.get.return_value = CacheSerializer.serialize(test_data)
        result = await isolated_cache.get("test_key")
        assert result == test_data

        # Verify statistics
        assert isolated_cache.stats.sets == 1
        assert isolated_cache.stats.hits == 1
        assert isolated_cache.stats.misses == 0

    async def test_cache_error_resilience(self, isolated_cache):
        """Test cache resilience to Redis errors."""
        mock_client = AsyncMock()
        isolated_cache.get_client = AsyncMock(return_value=mock_client)

        # Simulate Redis connection error
        mock_client.get.side_effect = redis.ConnectionError("Connection lost")
        mock_client.setex.side_effect = redis.ConnectionError("Connection lost")

        # Operations should not raise exceptions
        result = await isolated_cache.get("test_key")
        assert result is None

        result = await isolated_cache.set("test_key", "value", 300)
        assert result is False

        # Verify error statistics
        assert isolated_cache.stats.errors == 2


@pytest.mark.unit
class TestCachePerformance:
    """Performance-related tests for cache operations."""

    async def test_cache_operation_timing(self):
        """Test that cache operations are properly timed."""
        cache = RedisCache()
        mock_client = AsyncMock()
        cache.get_client = AsyncMock(return_value=mock_client)

        # Simulate slow Redis operation
        async def slow_get(key):
            await asyncio.sleep(0.1)
            return b"test_data"

        mock_client.get = slow_get

        start_time = time.time()
        result = await cache.get("test_key")
        end_time = time.time()

        assert result == "test_data"
        assert end_time - start_time >= 0.1
        assert cache.stats.hits == 1
        assert cache.stats.total_time >= 0.1

    def test_cache_stats_performance_metrics(self):
        """Test cache statistics performance calculations."""
        stats = CacheStats()

        # Simulate operations with different timings
        stats.record_hit(0.001)  # Fast hit
        stats.record_hit(0.005)  # Slower hit
        stats.record_miss(0.050)  # Slow miss (database query)

        assert stats.hit_rate == 2 / 3
        assert stats.avg_time == (0.001 + 0.005 + 0.050) / 3

        performance_data = stats.to_dict()
        expected_avg_ms = (0.001 + 0.005 + 0.050) / 3 * 1000
        assert performance_data["avg_time_ms"] == pytest.approx(expected_avg_ms, rel=1e-2)


@pytest.mark.integration
class TestCacheWithMockRedis:
    """Integration tests using mock Redis instances."""

    @pytest.fixture
    async def mock_redis_client(self):
        """Create a mock Redis client that behaves like real Redis."""

        class MockRedisClient:
            def __init__(self):
                self._data = {}
                self._expires = {}

            async def get(self, key):
                # Check if key has expired
                if key in self._expires:
                    if time.time() > self._expires[key]:
                        del self._data[key]
                        del self._expires[key]
                        return None
                return self._data.get(key)

            async def setex(self, key, ttl, value):
                self._data[key] = value
                self._expires[key] = time.time() + ttl
                return True

            async def delete(self, *keys):
                deleted = 0
                for key in keys:
                    if key in self._data:
                        del self._data[key]
                        self._expires.pop(key, None)
                        deleted += 1
                return deleted

            async def keys(self, pattern):
                import fnmatch

                return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]

            async def mget(self, keys):
                return [await self.get(key) for key in keys]

            async def ping(self):
                return True

            async def info(self, section=None):
                return {
                    "used_memory_human": "1MB",
                    "used_memory_peak_human": "2MB",
                    "mem_fragmentation_ratio": "1.1",
                    "connected_clients": "1",
                    "blocked_clients": "0",
                }

        return MockRedisClient()

    async def test_full_cache_workflow(self, mock_redis_client):
        """Test complete cache workflow with realistic Redis mock."""
        cache = RedisCache()
        cache.get_client = AsyncMock(return_value=mock_redis_client)

        # Test cache miss
        result = await cache.get("nonexistent_key")
        assert result is None
        assert cache.stats.misses == 1

        # Test cache set
        test_data = {"user_id": 123, "name": "Test User"}
        success = await cache.set("user:123", test_data, 300)
        assert success is True
        assert cache.stats.sets == 1

        # Test cache hit
        result = await cache.get("user:123")
        assert result == test_data
        assert cache.stats.hits == 1

        # Test pattern deletion
        await cache.set("user:456", {"user_id": 456, "name": "Another User"}, 300)
        deleted = await cache.delete_pattern("user:*")
        assert deleted == 2

        # Verify deletion worked
        result = await cache.get("user:123")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
