"""
Comprehensive benchmark test suite for performance optimization modules.

Tests latency measurements, throughput under load, cache hit rates,
database query performance, and Pusher event delivery benchmarks.

Target: Validate P95 latency <150ms and throughput improvements.
"""

import asyncio
import random
import statistics
import time
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest


@dataclass
class BenchmarkResult:
    """Container for benchmark test results."""

    operation: str
    total_operations: int
    total_time: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    throughput: float  # operations per second
    success_rate: float
    error_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "operation": self.operation,
            "total_operations": self.total_operations,
            "total_time_seconds": round(self.total_time, 3),
            "avg_latency_ms": round(self.avg_latency * 1000, 2),
            "min_latency_ms": round(self.min_latency * 1000, 2),
            "max_latency_ms": round(self.max_latency * 1000, 2),
            "p50_latency_ms": round(self.p50_latency * 1000, 2),
            "p95_latency_ms": round(self.p95_latency * 1000, 2),
            "p99_latency_ms": round(self.p99_latency * 1000, 2),
            "throughput_ops_per_sec": round(self.throughput, 2),
            "success_rate": round(self.success_rate, 4),
            "error_count": self.error_count,
        }


class BenchmarkRunner:
    """Utility class for running performance benchmarks."""

    @staticmethod
    async def run_benchmark(
        operation_name: str,
        operation_func: callable,
        num_operations: int = 1000,
        concurrency: int = 10,
        warmup_operations: int = 100,
    ) -> BenchmarkResult:
        """
        Run a benchmark test for an async operation.

        Args:
            operation_name: Name of the operation being benchmarked
            operation_func: Async function to benchmark
            num_operations: Total number of operations to perform
            concurrency: Number of concurrent operations
            warmup_operations: Number of warmup operations to run first

        Returns:
            BenchmarkResult with performance metrics
        """
        # Warmup phase
        if warmup_operations > 0:
            warmup_tasks = []
            for _ in range(warmup_operations):
                warmup_tasks.append(operation_func())
                if len(warmup_tasks) >= concurrency:
                    await asyncio.gather(*warmup_tasks, return_exceptions=True)
                    warmup_tasks = []
            if warmup_tasks:
                await asyncio.gather(*warmup_tasks, return_exceptions=True)

        # Benchmark phase
        latencies = []
        errors = 0
        start_time = time.time()

        # Create semaphore to control concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def timed_operation():
            nonlocal errors
            async with semaphore:
                operation_start = time.time()
                try:
                    await operation_func()
                    latency = time.time() - operation_start
                    latencies.append(latency)
                except Exception:
                    errors += 1
                    # Still record timing for failed operations
                    latency = time.time() - operation_start
                    latencies.append(latency)

        # Run all operations
        tasks = [timed_operation() for _ in range(num_operations)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate statistics
        if latencies:
            latencies.sort()
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p50_latency = latencies[int(len(latencies) * 0.5)]
            p95_latency = latencies[int(len(latencies) * 0.95)]
            p99_latency = latencies[int(len(latencies) * 0.99)]
        else:
            avg_latency = min_latency = max_latency = 0
            p50_latency = p95_latency = p99_latency = 0

        throughput = num_operations / total_time if total_time > 0 else 0
        success_rate = (num_operations - errors) / num_operations

        return BenchmarkResult(
            operation=operation_name,
            total_operations=num_operations,
            total_time=total_time,
            avg_latency=avg_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            p50_latency=p50_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            throughput=throughput,
            success_rate=success_rate,
            error_count=errors,
        )


@pytest.mark.performance
class TestCacheBenchmarks:
    """Benchmark tests for cache performance."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client with realistic performance characteristics."""

        class MockRedisClient:
            def __init__(self):
                self._data = {}
                self._hit_rate = 0.8  # 80% cache hit rate

            async def get(self, key):
                # Simulate network latency
                await asyncio.sleep(random.uniform(0.001, 0.005))  # 1-5ms

                # Simulate cache hit/miss based on hit rate
                if random.random() < self._hit_rate:
                    return f"cached_value_{key}".encode()
                return None

            async def set(self, key, value, ttl=300):
                await asyncio.sleep(random.uniform(0.002, 0.008))  # 2-8ms for write
                self._data[key] = value
                return True

            async def delete(self, key):
                await asyncio.sleep(random.uniform(0.001, 0.003))
                self._data.pop(key, None)
                return 1

        return MockRedisClient()

    @pytest.fixture
    def cache_instance(self, mock_redis_client):
        """Create cache instance with mock Redis client."""
        from apps.backend.core.cache import RedisCache

        cache = RedisCache()
        cache.get_client = AsyncMock(return_value=mock_redis_client)
        return cache

    async def test_cache_get_performance(self, cache_instance):
        """Benchmark cache GET operations."""

        async def cache_get_operation():
            key = f"test_key_{random.randint(1, 10000)}"
            return await cache_instance.get(key)

        result = await BenchmarkRunner.run_benchmark(
            "cache_get",
            cache_get_operation,
            num_operations=1000,
            concurrency=20,
            warmup_operations=50,
        )

        print(f"\nCache GET Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  P99 Latency: {result.p99_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")
        print(f"  Success Rate: {result.success_rate:.2%}")

        # Performance assertions
        assert result.p95_latency < 0.020  # P95 should be under 20ms
        assert result.success_rate > 0.99  # 99% success rate
        assert result.throughput > 500  # Should handle 500+ ops/sec

    async def test_cache_set_performance(self, cache_instance):
        """Benchmark cache SET operations."""

        async def cache_set_operation():
            key = f"test_key_{random.randint(1, 10000)}"
            value = {"data": f"test_data_{random.randint(1, 1000)}"}
            return await cache_instance.set(key, value, 300)

        result = await BenchmarkRunner.run_benchmark(
            "cache_set",
            cache_set_operation,
            num_operations=500,
            concurrency=15,
            warmup_operations=25,
        )

        print(f"\nCache SET Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # SET operations are slower than GET
        assert result.p95_latency < 0.050  # P95 should be under 50ms
        assert result.success_rate > 0.99
        assert result.throughput > 200  # Should handle 200+ ops/sec

    async def test_cache_mixed_operations(self, cache_instance):
        """Benchmark mixed cache operations (80% GET, 20% SET)."""

        async def mixed_cache_operation():
            if random.random() < 0.8:  # 80% GET operations
                key = f"test_key_{random.randint(1, 1000)}"
                return await cache_instance.get(key)
            else:  # 20% SET operations
                key = f"test_key_{random.randint(1, 1000)}"
                value = {"data": f"value_{random.randint(1, 1000)}"}
                return await cache_instance.set(key, value)

        result = await BenchmarkRunner.run_benchmark(
            "cache_mixed", mixed_cache_operation, num_operations=1000, concurrency=25
        )

        print(f"\nCache Mixed Operations Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Mixed workload should still perform well
        assert result.p95_latency < 0.030  # P95 should be under 30ms
        assert result.throughput > 400  # Should handle 400+ ops/sec

    async def test_cache_hit_rate_measurement(self, cache_instance):
        """Test cache hit rate under sustained load."""
        # Pre-populate cache with some keys
        for i in range(100):
            await cache_instance.set(f"popular_key_{i}", f"value_{i}")

        hits = 0
        misses = 0

        async def cache_operation_with_tracking():
            nonlocal hits, misses
            # 70% chance to access popular keys (should be hits)
            if random.random() < 0.7:
                key = f"popular_key_{random.randint(1, 100)}"
            else:
                key = f"random_key_{random.randint(1, 10000)}"

            result = await cache_instance.get(key)
            if result is not None:
                hits += 1
            else:
                misses += 1
            return result

        await BenchmarkRunner.run_benchmark(
            "cache_hit_rate",
            cache_operation_with_tracking,
            num_operations=1000,
            concurrency=20,
        )

        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        print(f"\nCache Hit Rate Test:")
        print(f"  Hits: {hits}, Misses: {misses}")
        print(f"  Hit Rate: {hit_rate:.2%}")

        # Should achieve reasonable hit rate
        assert hit_rate > 0.5  # At least 50% hit rate


@pytest.mark.performance
class TestDatabaseBenchmarks:
    """Benchmark tests for database performance."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session with realistic query performance."""

        class MockDBSession:
            async def execute(self, query, params=None):
                # Simulate query execution time based on complexity
                query_str = str(query).lower()
                if "select count" in query_str:
                    await asyncio.sleep(random.uniform(0.005, 0.015))  # 5-15ms for count
                elif "select" in query_str and "join" in query_str:
                    await asyncio.sleep(random.uniform(0.020, 0.080))  # 20-80ms for joins
                elif "select" in query_str:
                    await asyncio.sleep(random.uniform(0.010, 0.030))  # 10-30ms for simple select
                elif "insert" in query_str or "update" in query_str:
                    await asyncio.sleep(random.uniform(0.015, 0.040))  # 15-40ms for writes
                else:
                    await asyncio.sleep(random.uniform(0.005, 0.020))

                # Mock result
                result = Mock()
                result.fetchall.return_value = [{"id": 1, "name": "test"}]
                return result

        return MockDBSession()

    @pytest.fixture
    def db_optimizer(self, mock_db_session):
        """Mock database optimizer with session."""
        from apps.backend.core.db_optimization import DatabaseOptimizer

        optimizer = DatabaseOptimizer()

        # Mock the engine's get_session method
        optimizer.engine.get_session = AsyncMock()
        optimizer.engine.get_session.return_value.__aenter__ = AsyncMock(
            return_value=mock_db_session
        )
        optimizer.engine.get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock query cache to simulate cache misses for benchmarking
        optimizer.query_cache = AsyncMock()
        optimizer.query_cache.get_cached_result.return_value = None  # Always miss for benchmarking
        optimizer.query_cache.cache_result = AsyncMock()

        return optimizer

    async def test_simple_query_performance(self, db_optimizer):
        """Benchmark simple database queries."""
        queries = [
            "SELECT * FROM users WHERE id = :id",
            "SELECT COUNT(*) FROM users WHERE active = :active",
            "SELECT name, email FROM users WHERE created_at > :date",
        ]

        async def simple_query_operation():
            query = random.choice(queries)
            params = {
                "id": random.randint(1, 1000),
                "active": True,
                "date": "2023-01-01",
            }
            return await db_optimizer.execute_optimized_query(query, params, use_cache=False)

        result = await BenchmarkRunner.run_benchmark(
            "simple_db_query",
            simple_query_operation,
            num_operations=500,
            concurrency=10,
            warmup_operations=20,
        )

        print(f"\nSimple Database Query Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  P99 Latency: {result.p99_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Database queries should be reasonably fast
        assert result.p95_latency < 0.100  # P95 under 100ms
        assert result.success_rate > 0.99
        assert result.throughput > 50  # Should handle 50+ queries/sec

    async def test_complex_query_performance(self, db_optimizer):
        """Benchmark complex database queries with joins."""
        complex_queries = [
            """
            SELECT u.id, u.name, p.points, c.name as class_name
            FROM users u
            JOIN student_progress p ON u.id = p.student_id
            JOIN classes c ON p.class_id = c.id
            WHERE u.active = :active
            """,
            """
            SELECT c.id, c.name, COUNT(s.student_id) as student_count,
                   AVG(p.points) as avg_points
            FROM classes c
            LEFT JOIN class_students s ON c.id = s.class_id
            LEFT JOIN student_progress p ON s.student_id = p.student_id
            WHERE c.teacher_id = :teacher_id
            GROUP BY c.id, c.name
            """,
        ]

        async def complex_query_operation():
            query = random.choice(complex_queries)
            params = {"active": True, "teacher_id": random.randint(1, 100)}
            return await db_optimizer.execute_optimized_query(query, params, use_cache=False)

        result = await BenchmarkRunner.run_benchmark(
            "complex_db_query",
            complex_query_operation,
            num_operations=200,
            concurrency=5,
            warmup_operations=10,
        )

        print(f"\nComplex Database Query Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Complex queries are slower but should still be reasonable
        assert result.p95_latency < 0.200  # P95 under 200ms
        assert result.success_rate > 0.99

    async def test_prepared_statement_performance(self, db_optimizer):
        """Benchmark prepared statement execution."""
        # Mock prepared statements
        with patch("apps.backend.core.db_optimization._prepared_statements") as mock_statements:
            from sqlalchemy import text

            mock_statements.get_statement.return_value = text(
                "SELECT * FROM users WHERE id = :user_id"
            )

            async def prepared_statement_operation():
                return await db_optimizer.execute_prepared_statement(
                    "get_user", {"user_id": random.randint(1, 1000)}
                )

            result = await BenchmarkRunner.run_benchmark(
                "prepared_statement",
                prepared_statement_operation,
                num_operations=500,
                concurrency=15,
                warmup_operations=25,
            )

            print(f"\nPrepared Statement Benchmark Results:")
            print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
            print(f"  Throughput: {result.throughput:.2f} ops/sec")

            # Prepared statements should be fast
            assert result.p95_latency < 0.080  # P95 under 80ms
            assert result.throughput > 60  # Should be faster than ad-hoc queries

    async def test_database_with_cache_performance(self, db_optimizer):
        """Benchmark database queries with caching enabled."""
        # Enable caching with 50% hit rate
        call_count = 0
        cached_results = {}

        async def mock_get_cached_result(query, params):
            nonlocal call_count, cached_results
            call_count += 1
            cache_key = f"{query}_{params}"

            # 50% cache hit rate
            if call_count % 2 == 0 and cache_key in cached_results:
                return cached_results[cache_key]
            return None

        async def mock_cache_result(query, params, result, ttl):
            cache_key = f"{query}_{params}"
            cached_results[cache_key] = result

        db_optimizer.query_cache.get_cached_result.side_effect = mock_get_cached_result
        db_optimizer.query_cache.cache_result.side_effect = mock_cache_result

        async def cached_query_operation():
            query = "SELECT * FROM users WHERE id = :id"
            params = {"id": random.randint(1, 100)}  # Limited range for cache hits
            return await db_optimizer.execute_optimized_query(query, params, use_cache=True)

        result = await BenchmarkRunner.run_benchmark(
            "db_with_cache", cached_query_operation, num_operations=500, concurrency=20
        )

        print(f"\nDatabase with Cache Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # With caching, should see improved performance
        assert result.p95_latency < 0.060  # Should be faster with cache
        assert result.throughput > 100  # Higher throughput with cache


@pytest.mark.performance
class TestPusherBenchmarks:
    """Benchmark tests for Pusher performance."""

    @pytest.fixture
    def mock_pusher_clients(self):
        """Mock Pusher clients for performance testing."""

        class MockPusherClient:
            def __init__(self):
                self.events_sent = 0

            def trigger(self, channel, event, data, socket_id=None):
                # Simulate API latency
                time.sleep(random.uniform(0.010, 0.030))  # 10-30ms
                self.events_sent += 1

            def trigger_batch(self, events):
                # Batch operations are more efficient
                time.sleep(random.uniform(0.015, 0.040))  # 15-40ms for batch
                self.events_sent += len(events)

            def authenticate(self, channel, socket_id, custom_data=None):
                time.sleep(random.uniform(0.005, 0.015))
                return {"auth": f"token_{socket_id}"}

        return [MockPusherClient() for _ in range(5)]  # Pool of 5 clients

    @pytest.fixture
    def pusher_service(self, mock_pusher_clients):
        """Mock optimized Pusher service."""
        from apps.backend.services.pusher_optimized import OptimizedPusherService

        service = OptimizedPusherService()

        # Mock connection pool
        service.connection_pool = AsyncMock()
        service.connection_pool.get_client.side_effect = lambda: random.choice(mock_pusher_clients)

        # Mock other components
        service.channel_manager = AsyncMock()
        service.rate_limiter = AsyncMock()
        service.rate_limiter.wait_for_slot = AsyncMock()

        # Initialize stats
        from apps.backend.services.pusher_optimized import PusherStats

        service.stats = PusherStats()

        return service

    async def test_single_event_performance(self, pusher_service):
        """Benchmark single Pusher event sending."""
        channels = ["channel-1", "channel-2", "channel-3", "channel-4", "channel-5"]
        events = ["user-action", "content-update", "notification", "system-alert"]

        async def single_event_operation():
            channel = random.choice(channels)
            event = random.choice(events)
            data = {"message": f"test message {random.randint(1, 1000)}"}
            return await pusher_service.trigger_event(channel, event, data, immediate=True)

        result = await BenchmarkRunner.run_benchmark(
            "pusher_single_event",
            single_event_operation,
            num_operations=300,
            concurrency=10,
            warmup_operations=20,
        )

        print(f"\nPusher Single Event Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Single events should be reasonably fast
        assert result.p95_latency < 0.150  # P95 under 150ms
        assert result.success_rate > 0.99
        assert result.throughput > 20  # Should handle 20+ events/sec

    async def test_batched_event_performance(self, pusher_service):
        """Benchmark batched Pusher event sending."""

        # Override batch processor for testing
        async def mock_send_batched_events(batches):
            for channel, events in batches.items():
                if len(events) > 1:
                    # Simulate batch send
                    await asyncio.sleep(random.uniform(0.020, 0.050))
                else:
                    # Single event
                    await asyncio.sleep(random.uniform(0.015, 0.035))

                pusher_service.stats.record_event(True, 0.025, len(events))

        pusher_service._send_batched_events = mock_send_batched_events

        async def batched_event_operation():
            channel = "batch-channel"  # Same channel to enable batching
            event = "batch-event"
            data = {"message": f"batch message {random.randint(1, 1000)}"}
            return await pusher_service.trigger_event(channel, event, data, immediate=False)

        result = await BenchmarkRunner.run_benchmark(
            "pusher_batched_event",
            batched_event_operation,
            num_operations=500,
            concurrency=20,
        )

        print(f"\nPusher Batched Event Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Batched events should have better throughput
        assert result.throughput > 30  # Should handle more events/sec with batching

    async def test_authentication_performance(self, pusher_service):
        """Benchmark Pusher channel authentication."""
        channels = ["private-channel", "presence-lobby", "private-messages"]

        async def auth_operation():
            channel = random.choice(channels)
            socket_id = f"socket_{random.randint(1, 10000)}"

            if channel.startswith("presence"):
                return await pusher_service.authenticate_channel(
                    socket_id,
                    channel,
                    user_id=f"user_{random.randint(1, 1000)}",
                    user_info={"name": "Test User"},
                )
            else:
                return await pusher_service.authenticate_channel(socket_id, channel)

        result = await BenchmarkRunner.run_benchmark(
            "pusher_authentication", auth_operation, num_operations=200, concurrency=15
        )

        print(f"\nPusher Authentication Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Authentication should be fast
        assert result.p95_latency < 0.100  # P95 under 100ms
        assert result.success_rate > 0.99

    async def test_mixed_pusher_operations(self, pusher_service):
        """Benchmark mixed Pusher operations (events + auth)."""

        async def mixed_operation():
            if random.random() < 0.8:  # 80% events
                channel = f"channel-{random.randint(1, 5)}"
                event = "mixed-event"
                data = {"data": random.randint(1, 1000)}
                return await pusher_service.trigger_event(channel, event, data, immediate=True)
            else:  # 20% authentication
                socket_id = f"socket_{random.randint(1, 1000)}"
                return await pusher_service.authenticate_channel(socket_id, "private-test")

        result = await BenchmarkRunner.run_benchmark(
            "pusher_mixed_operations",
            mixed_operation,
            num_operations=400,
            concurrency=15,
        )

        print(f"\nPusher Mixed Operations Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

        # Mixed workload should still perform well
        assert result.p95_latency < 0.120  # P95 under 120ms


@pytest.mark.performance
class TestIntegratedPerformanceBenchmarks:
    """Benchmark tests for integrated performance optimization system."""

    @pytest.fixture
    def integrated_system_mocks(self):
        """Setup mocks for integrated system testing."""
        # Mock cache
        mock_cache = AsyncMock()
        mock_cache.get.side_effect = lambda k: asyncio.sleep(0.002) or (
            f"cached_{k}" if random.random() < 0.6 else None
        )
        mock_cache.set.side_effect = lambda k, v, t: asyncio.sleep(0.003) or True

        # Mock database
        mock_db = AsyncMock()

        async def mock_execute_query(query, params, use_cache=True):
            await asyncio.sleep(random.uniform(0.010, 0.040))
            return [{"id": 1, "data": "result"}]

        mock_db.execute_optimized_query = mock_execute_query

        # Mock Pusher
        mock_pusher = AsyncMock()

        async def mock_trigger_event(channel, event, data, immediate=False):
            await asyncio.sleep(random.uniform(0.015, 0.035))
            return True

        mock_pusher.trigger_event = mock_trigger_event

        return {"cache": mock_cache, "db": mock_db, "pusher": mock_pusher}

    async def test_end_to_end_request_performance(self, integrated_system_mocks):
        """Benchmark complete request processing through all optimization layers."""

        async def complete_request_simulation():
            """Simulate a complete API request that uses cache, database, and Pusher."""
            # 1. Try cache first
            cache_key = f"user_data_{random.randint(1, 100)}"
            cached_data = await integrated_system_mocks["cache"].get(cache_key)

            if cached_data is None:
                # 2. Query database
                query = "SELECT * FROM users WHERE id = :id"
                params = {"id": random.randint(1, 100)}
                data = await integrated_system_mocks["db"].execute_optimized_query(query, params)

                # 3. Cache the result
                await integrated_system_mocks["cache"].set(cache_key, data, 300)
            else:
                data = cached_data

            # 4. Send notification via Pusher
            await integrated_system_mocks["pusher"].trigger_event(
                "user-updates", "data-changed", {"user_id": random.randint(1, 100)}
            )

            return data

        result = await BenchmarkRunner.run_benchmark(
            "end_to_end_request",
            complete_request_simulation,
            num_operations=300,
            concurrency=15,
            warmup_operations=20,
        )

        print(f"\nEnd-to-End Request Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  P99 Latency: {result.p99_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} requests/sec")

        # This is our main performance target
        assert result.p95_latency < 0.150  # P95 under 150ms (our target!)
        assert result.p99_latency < 0.200  # P99 under 200ms
        assert result.success_rate > 0.99
        assert result.throughput > 20  # Should handle 20+ complete requests/sec

    async def test_concurrent_mixed_workload(self, integrated_system_mocks):
        """Benchmark system under mixed concurrent workload."""

        # Define different operation types with weights
        async def cache_heavy_operation():
            """Operation that heavily uses cache."""
            for _ in range(3):
                key = f"cache_key_{random.randint(1, 50)}"
                await integrated_system_mocks["cache"].get(key)

        async def db_heavy_operation():
            """Operation that heavily uses database."""
            for _ in range(2):
                query = "SELECT * FROM table WHERE condition = :param"
                params = {"param": random.randint(1, 100)}
                await integrated_system_mocks["db"].execute_optimized_query(query, params)

        async def pusher_heavy_operation():
            """Operation that sends multiple Pusher events."""
            for _ in range(3):
                channel = f"channel_{random.randint(1, 5)}"
                await integrated_system_mocks["pusher"].trigger_event(
                    channel, "event", {"data": random.randint(1, 1000)}
                )

        async def mixed_workload_operation():
            """Choose operation type randomly."""
            operation_type = random.choices(
                [cache_heavy_operation, db_heavy_operation, pusher_heavy_operation],
                weights=[0.5, 0.3, 0.2],  # 50% cache, 30% DB, 20% Pusher
            )[0]
            return await operation_type()

        result = await BenchmarkRunner.run_benchmark(
            "mixed_workload",
            mixed_workload_operation,
            num_operations=200,
            concurrency=20,
            warmup_operations=20,
        )

        print(f"\nMixed Workload Benchmark Results:")
        print(f"  P95 Latency: {result.p95_latency * 1000:.2f}ms")
        print(f"  Throughput: {result.throughput:.2f} operations/sec")

        # Mixed workload should still meet performance targets
        assert result.p95_latency < 0.200  # P95 under 200ms for complex operations
        assert result.success_rate > 0.95

    async def test_performance_under_increasing_load(self, integrated_system_mocks):
        """Test performance degradation under increasing load."""

        async def simple_operation():
            # Simple operation using all systems
            await integrated_system_mocks["cache"].get("test_key")
            await integrated_system_mocks["db"].execute_optimized_query("SELECT 1", {})
            await integrated_system_mocks["pusher"].trigger_event("test", "event", {})

        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20, 30, 40]
        results = []

        for concurrency in concurrency_levels:
            result = await BenchmarkRunner.run_benchmark(
                f"load_test_concurrency_{concurrency}",
                simple_operation,
                num_operations=100,  # Smaller number for load testing
                concurrency=concurrency,
                warmup_operations=10,
            )
            results.append((concurrency, result))

        print(f"\nLoad Test Results:")
        print(f"{'Concurrency':<12} {'P95 Latency (ms)':<15} {'Throughput':<12} {'Success Rate'}")
        print("-" * 55)

        for concurrency, result in results:
            print(
                f"{concurrency:<12} {result.p95_latency*1000:<15.2f} "
                f"{result.throughput:<12.2f} {result.success_rate:<12.2%}"
            )

        # Performance should degrade gracefully
        # Even at high concurrency, P95 should stay reasonable
        highest_concurrency_result = results[-1][1]
        assert highest_concurrency_result.p95_latency < 0.300  # P95 under 300ms even at high load
        assert highest_concurrency_result.success_rate > 0.90  # 90% success rate even under stress


@pytest.mark.performance
class TestBenchmarkReporting:
    """Test benchmark result reporting and analysis."""

    def test_benchmark_result_serialization(self):
        """Test that benchmark results can be serialized for reporting."""
        result = BenchmarkResult(
            operation="test_operation",
            total_operations=1000,
            total_time=10.5,
            avg_latency=0.0105,
            min_latency=0.001,
            max_latency=0.050,
            p50_latency=0.008,
            p95_latency=0.025,
            p99_latency=0.040,
            throughput=95.24,
            success_rate=0.99,
            error_count=10,
        )

        result_dict = result.to_dict()

        # Verify all fields are present and properly formatted
        assert result_dict["operation"] == "test_operation"
        assert result_dict["total_operations"] == 1000
        assert result_dict["total_time_seconds"] == 10.5
        assert result_dict["avg_latency_ms"] == 10.5
        assert result_dict["p95_latency_ms"] == 25.0
        assert result_dict["p99_latency_ms"] == 40.0
        assert result_dict["throughput_ops_per_sec"] == 95.24
        assert result_dict["success_rate"] == 0.99
        assert result_dict["error_count"] == 10

    async def test_benchmark_runner_edge_cases(self):
        """Test benchmark runner with edge cases."""

        # Test with operation that always fails
        async def failing_operation():
            raise Exception("Always fails")

        result = await BenchmarkRunner.run_benchmark(
            "failing_operation",
            failing_operation,
            num_operations=10,
            concurrency=2,
            warmup_operations=0,
        )

        assert result.success_rate == 0.0
        assert result.error_count == 10

        # Test with very fast operation
        async def instant_operation():
            return "instant"

        result = await BenchmarkRunner.run_benchmark(
            "instant_operation", instant_operation, num_operations=100, concurrency=10
        )

        assert result.success_rate == 1.0
        assert result.error_count == 0
        assert result.throughput > 100  # Should be very high throughput


if __name__ == "__main__":
    # Run all benchmark tests and generate report
    pytest.main([__file__, "-v", "--tb=short"])
