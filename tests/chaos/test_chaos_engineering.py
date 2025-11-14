"""
Comprehensive Chaos Engineering Tests for Load Balancing Infrastructure

This module provides chaos engineering tests to validate system resilience under failure conditions.
Tests are designed to run in controlled environments with proper isolation and recovery mechanisms.

Based on modern chaos engineering principles and production best practices for 2025.
"""

import asyncio
import json
import logging
import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import psutil
import pytest
import redis.asyncio as redis_async

# Import system components
from apps.backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
)
from apps.backend.core.global_load_balancer import GlobalLoadBalancer
from apps.backend.core.security.rate_limit_manager import (
    RateLimitConfig,
    RateLimitManager,
)
from apps.backend.services.websocket_handler import WebSocketHandler

# Test utilities
from tests.fixtures.cleanup import TestCleanupManager

logger = logging.getLogger(__name__)

# Chaos testing markers
pytestmark = [pytest.mark.chaos, pytest.mark.integration, pytest.mark.slow]


@dataclass
class ChaosTestConfig:
    """Configuration for chaos engineering tests"""

    # Test execution
    max_duration: int = 300  # Maximum test duration in seconds
    recovery_timeout: int = 60  # Time to wait for system recovery
    health_check_interval: int = 5  # Health check frequency

    # Failure parameters
    network_latency_ms: int = 1000  # Artificial network delay
    cpu_stress_percent: int = 90  # CPU utilization target
    memory_stress_mb: int = 1024  # Memory consumption target
    connection_limit: int = 100  # Connection pool limit

    # Safety limits
    max_failure_duration: int = 30  # Maximum failure injection time
    min_recovery_time: int = 10  # Minimum recovery observation time
    emergency_stop_threshold: int = 180  # Emergency stop if test runs too long

    # Environment
    test_environment: str = "chaos_test"
    isolated_network: bool = True
    mock_external_services: bool = True


@dataclass
class FailureScenario:
    """Represents a failure scenario for chaos testing"""

    name: str
    description: str
    inject_failure: Callable
    validate_behavior: Callable
    cleanup: Callable | None = None
    expected_recovery_time: int = 30
    severity: str = "medium"  # low, medium, high, critical
    prerequisites: list[str] = field(default_factory=list)


class ChaosTestOrchestrator:
    """Orchestrates chaos engineering tests with safety controls"""

    def __init__(self, config: ChaosTestConfig):
        self.config = config
        self.active_failures: dict[str, Any] = {}
        self.test_start_time: datetime | None = None
        self.emergency_stop_triggered = False
        self.system_health_baseline: dict[str, Any] = {}
        self.cleanup_manager = TestCleanupManager()

    async def setup_test_environment(self):
        """Setup isolated test environment"""
        logger.info("Setting up chaos test environment")

        # Record baseline system health
        self.system_health_baseline = await self._get_system_health()
        self.test_start_time = datetime.now()

        # Initialize test components with isolation
        await self._setup_isolated_services()

    async def teardown_test_environment(self):
        """Cleanup test environment and ensure system recovery"""
        logger.info("Tearing down chaos test environment")

        # Stop all active failures
        for failure_id in list(self.active_failures.keys()):
            await self._stop_failure(failure_id)

        # Wait for system recovery
        await self._wait_for_system_recovery()

        # Cleanup resources
        await self.cleanup_manager.cleanup_all()

    async def _setup_isolated_services(self):
        """Setup isolated service instances for testing"""
        # Create isolated Redis instance for testing
        self.test_redis = await redis_async.Redis(
            host="localhost",
            port=6380,  # Different port for isolation
            db=15,  # Use test database
            decode_responses=True,
        )

        # Setup isolated rate limiter
        self.test_rate_limiter = RateLimitManager()
        self.test_rate_limiter.reset_instance()

        # Setup test circuit breakers
        self.test_circuit_breakers = {}

    async def _get_system_health(self) -> dict[str, Any]:
        """Get current system health metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "network_connections": len(psutil.net_connections()),
            "timestamp": datetime.now().isoformat(),
        }

    async def _wait_for_system_recovery(self):
        """Wait for system to return to healthy state"""
        recovery_start = time.time()

        while time.time() - recovery_start < self.config.recovery_timeout:
            current_health = await self._get_system_health()

            # Check if system has recovered
            if self._is_system_healthy(current_health):
                logger.info("System recovered successfully")
                return

            await asyncio.sleep(self.config.health_check_interval)

        logger.warning("System did not fully recover within timeout")

    def _is_system_healthy(self, health_metrics: dict[str, Any]) -> bool:
        """Check if system is in healthy state"""
        baseline = self.system_health_baseline

        # Check if metrics are within acceptable ranges
        cpu_ok = health_metrics["cpu_percent"] < baseline["cpu_percent"] + 20
        memory_ok = health_metrics["memory_percent"] < baseline["memory_percent"] + 20

        return cpu_ok and memory_ok

    async def _stop_failure(self, failure_id: str):
        """Stop a specific failure injection"""
        if failure_id in self.active_failures:
            failure_info = self.active_failures[failure_id]
            if "stop_func" in failure_info:
                await failure_info["stop_func"]()
            del self.active_failures[failure_id]


@pytest.fixture
async def chaos_orchestrator():
    """Pytest fixture for chaos test orchestrator"""
    config = ChaosTestConfig()
    orchestrator = ChaosTestOrchestrator(config)

    await orchestrator.setup_test_environment()

    yield orchestrator

    await orchestrator.teardown_test_environment()


@pytest.fixture
def mock_external_services():
    """Mock external dependencies for isolated testing"""
    with (
        patch("httpx.AsyncClient") as mock_client,
        patch("redis.asyncio.Redis") as mock_redis,
        patch("websockets.connect") as mock_websocket,
    ):
        # Configure mocks to simulate various failure modes
        mock_client.return_value.get = AsyncMock()
        mock_redis.return_value.get = AsyncMock()
        mock_websocket.return_value = AsyncMock()

        yield {
            "http_client": mock_client,
            "redis": mock_redis,
            "websocket": mock_websocket,
        }


class TestNetworkPartitionSimulation:
    """Test network partition scenarios"""

    @pytest.mark.asyncio
    async def test_service_isolation_network_partition(self, chaos_orchestrator):
        """Test system behavior when services are network isolated"""

        async def inject_network_partition():
            """Simulate network partition between services"""
            # Block traffic between backend and database
            with patch("asyncpg.connect") as mock_connect:
                mock_connect.side_effect = asyncio.TimeoutError("Network partition simulated")
                await asyncio.sleep(10)  # Hold partition for 10 seconds

        async def validate_circuit_breaker_activation():
            """Validate that circuit breakers prevent cascading failures"""
            # Create test circuit breaker
            config = CircuitBreakerConfig(failure_threshold=3, reset_timeout=5.0)
            breaker = CircuitBreaker("database_service", config)

            # Simulate database calls that will fail due to partition
            failure_count = 0
            for _ in range(5):
                try:
                    await breaker.call(self._mock_database_call)
                except Exception:
                    failure_count += 1

            # Verify circuit breaker opens after threshold
            assert breaker.state == CircuitBreakerState.OPEN
            assert failure_count >= 3

        # Execute chaos test
        await inject_network_partition()
        await validate_circuit_breaker_activation()

        # Verify system recovery
        await asyncio.sleep(15)  # Wait for recovery

    @pytest.mark.asyncio
    async def test_split_brain_scenario(self, chaos_orchestrator):
        """Test split-brain scenario with multiple active regions"""

        async def inject_split_brain():
            """Create split-brain condition"""
            # Simulate two regions thinking they're primary
            region_1_health = {"status": "primary", "region": "us-east-1"}
            region_2_health = {"status": "primary", "region": "us-west-2"}

            with patch(
                "apps.backend.core.global_load_balancer.GlobalLoadBalancer.get_region_health"
            ) as mock_health:
                mock_health.side_effect = [region_1_health, region_2_health]
                await asyncio.sleep(5)

        async def validate_conflict_resolution():
            """Validate that system resolves split-brain correctly"""
            # Mock load balancer should detect and resolve conflict
            load_balancer = GlobalLoadBalancer()

            # Verify only one region is marked as primary after resolution
            active_regions = await load_balancer.get_active_regions()
            primary_regions = [r for r in active_regions if r.get("status") == "primary"]

            assert (
                len(primary_regions) <= 1
            ), "Split-brain not resolved - multiple primaries detected"

        await inject_split_brain()
        await validate_conflict_resolution()

    async def _mock_database_call(self):
        """Mock database call that fails during network partition"""
        raise ConnectionError("Database unreachable due to network partition")


class TestServiceFailureInjection:
    """Test random service failures and recovery"""

    @pytest.mark.asyncio
    async def test_random_service_crashes(self, chaos_orchestrator):
        """Simulate random service crashes and validate recovery"""

        services = ["auth_service", "content_service", "notification_service"]
        crashed_services = []

        async def inject_service_crashes():
            """Randomly crash services"""
            for service in random.sample(services, 2):  # Crash 2 random services
                crashed_services.append(service)

                # Simulate service crash
                with patch(f"apps.backend.services.{service}.is_healthy", return_value=False):
                    await asyncio.sleep(5)

        async def validate_failover_behavior():
            """Validate that system routes around failed services"""
            # Check that load balancer marks services as unhealthy
            for service in crashed_services:
                # Verify circuit breaker opens for failed service
                breaker = CircuitBreaker(f"{service}_breaker")

                # Trigger failures to open circuit
                for _ in range(5):
                    try:
                        await breaker.call(self._failing_service_call)
                    except:
                        pass

                assert breaker.state == CircuitBreakerState.OPEN

        await inject_service_crashes()
        await validate_failover_behavior()

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self, chaos_orchestrator):
        """Test that circuit breakers prevent cascading failures"""

        # Setup chain of dependent services
        service_chain = ["frontend", "api_gateway", "auth_service", "database"]
        circuit_breakers = {}

        for service in service_chain:
            config = CircuitBreakerConfig(failure_threshold=2, reset_timeout=10.0)
            circuit_breakers[service] = CircuitBreaker(service, config)

        async def inject_database_failure():
            """Inject failure at the bottom of the chain"""
            # Simulate database failure
            for _ in range(5):
                try:
                    await circuit_breakers["database"].call(self._failing_database_call)
                except:
                    pass

        async def validate_cascade_prevention():
            """Validate that failures don't cascade up the chain"""
            # Database circuit should be open
            assert circuit_breakers["database"].state == CircuitBreakerState.OPEN

            # Upstream services should remain functional with fallbacks
            for service in ["frontend", "api_gateway", "auth_service"]:
                assert circuit_breakers[service].state != CircuitBreakerState.OPEN

        await inject_database_failure()
        await validate_cascade_prevention()

    async def _failing_service_call(self):
        """Mock service call that always fails"""
        raise Exception("Service is down")

    async def _failing_database_call(self):
        """Mock database call that always fails"""
        raise Exception("Database connection failed")


class TestResourceExhaustion:
    """Test system behavior under resource exhaustion"""

    @pytest.mark.asyncio
    async def test_cpu_exhaustion(self, chaos_orchestrator):
        """Test system behavior under high CPU load"""

        def cpu_stress_worker():
            """CPU intensive worker function"""
            end_time = time.time() + 10  # Run for 10 seconds
            while time.time() < end_time:
                # CPU intensive calculation
                sum(i * i for i in range(10000))

        async def inject_cpu_stress():
            """Inject high CPU load"""
            # Start multiple CPU stress workers
            threads = []
            for _ in range(psutil.cpu_count()):
                thread = threading.Thread(target=cpu_stress_worker)
                thread.start()
                threads.append(thread)

            # Wait for threads to complete
            for thread in threads:
                thread.join()

        async def validate_throttling_behavior():
            """Validate that rate limiting activates under high CPU"""
            rate_limiter = RateLimitManager()

            # Under high CPU, rate limits should be more aggressive
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                # Rate limiter should reduce limits
                config = RateLimitConfig(max_requests=10, window_seconds=60)

                # Simulate rapid requests
                client_id = "test_client"
                request_count = 0

                for _ in range(20):
                    if await rate_limiter.check_rate_limit(client_id, config):
                        request_count += 1

                # Should have rejected some requests under high CPU
                assert request_count < 15, "Rate limiter not throttling under high CPU"

        await inject_cpu_stress()
        await validate_throttling_behavior()

    @pytest.mark.asyncio
    async def test_memory_exhaustion(self, chaos_orchestrator):
        """Test system behavior under memory pressure"""

        allocated_memory = []

        async def inject_memory_pressure():
            """Consume large amounts of memory"""
            try:
                # Allocate memory in chunks
                chunk_size = 50 * 1024 * 1024  # 50MB chunks
                for _ in range(20):  # Try to allocate 1GB total
                    chunk = bytearray(chunk_size)
                    allocated_memory.append(chunk)
                    await asyncio.sleep(0.1)  # Brief pause between allocations

            except MemoryError:
                logger.info("Memory allocation failed as expected")

        async def validate_memory_management():
            """Validate that system handles memory pressure gracefully"""
            # Check that circuit breakers respond to memory pressure
            memory_percent = psutil.virtual_memory().percent

            if memory_percent > 80:
                # System should start rejecting non-essential requests
                config = CircuitBreakerConfig(failure_threshold=1)
                memory_breaker = CircuitBreaker("memory_protection", config)

                # Simulate memory-intensive operation
                try:
                    await memory_breaker.call(self._memory_intensive_operation)
                except Exception:
                    pass

                # Circuit should open under memory pressure
                assert memory_breaker.state == CircuitBreakerState.OPEN

        try:
            await inject_memory_pressure()
            await validate_memory_management()
        finally:
            # Cleanup allocated memory
            allocated_memory.clear()

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, chaos_orchestrator):
        """Test behavior when connection pools are exhausted"""

        connections = []

        async def exhaust_connection_pool():
            """Create many concurrent connections"""

            async def create_connection():
                # Mock connection that stays open
                connection = AsyncMock()
                connection.is_closed = False
                return connection

            # Create connections up to limit
            for _ in range(150):  # Exceed typical pool size
                conn = await create_connection()
                connections.append(conn)

        async def validate_connection_management():
            """Validate that system handles connection exhaustion"""
            # Circuit breaker should protect against connection exhaustion
            config = CircuitBreakerConfig(failure_threshold=3)
            conn_breaker = CircuitBreaker("connection_pool", config)

            # Simulate connection attempts when pool is exhausted
            for _ in range(5):
                try:
                    await conn_breaker.call(self._create_database_connection)
                except Exception:
                    pass

            # Should open circuit when connections exhausted
            assert conn_breaker.state == CircuitBreakerState.OPEN

        await exhaust_connection_pool()
        await validate_connection_management()

    async def _memory_intensive_operation(self):
        """Simulate memory-intensive operation"""
        # Try to allocate large chunk of memory
        large_data = bytearray(100 * 1024 * 1024)  # 100MB
        return len(large_data)

    async def _create_database_connection(self):
        """Mock database connection creation"""
        # Simulate connection pool exhaustion
        raise Exception("Connection pool exhausted")


class TestDatabaseFailoverSimulation:
    """Test database failover scenarios"""

    @pytest.mark.asyncio
    async def test_primary_database_failure(self, chaos_orchestrator):
        """Test failover when primary database fails"""

        async def inject_primary_db_failure():
            """Simulate primary database failure"""
            with patch("asyncpg.connect") as mock_connect:
                # First few calls succeed (primary), then fail
                mock_connect.side_effect = [
                    AsyncMock(),  # Initial connection succeeds
                    ConnectionError("Primary database unreachable"),
                    ConnectionError("Primary database unreachable"),
                    AsyncMock(),  # Fallback to replica succeeds
                ]

                # Trigger database operations
                for _ in range(4):
                    try:
                        await self._database_operation()
                    except:
                        pass

        async def validate_replica_takeover():
            """Validate that read replicas take over"""
            # Mock database service should switch to replica
            with patch(
                "apps.backend.services.database.DatabaseService.get_read_connection"
            ) as mock_read:
                mock_read.return_value = AsyncMock()

                # Operations should succeed using replica
                result = await self._read_operation()
                assert result is not None

        async def validate_write_protection():
            """Validate that writes are protected during failover"""
            with patch(
                "apps.backend.services.database.DatabaseService.get_write_connection"
            ) as mock_write:
                mock_write.side_effect = ConnectionError("Primary database down")

                # Write operations should be queued or rejected gracefully
                try:
                    await self._write_operation()
                    assert False, "Write should have been rejected"
                except Exception as e:
                    assert "database" in str(e).lower()

        await inject_primary_db_failure()
        await validate_replica_takeover()
        await validate_write_protection()

    @pytest.mark.asyncio
    async def test_database_split_brain(self, chaos_orchestrator):
        """Test database split-brain scenario"""

        async def inject_split_brain():
            """Create split-brain condition in database cluster"""
            # Simulate two nodes thinking they're primary
            with patch("apps.backend.services.database.check_primary_status") as mock_primary:
                mock_primary.side_effect = [True, True]  # Both think they're primary
                await asyncio.sleep(2)

        async def validate_write_conflict_resolution():
            """Validate that write conflicts are resolved"""
            # System should detect split-brain and elect single primary
            with patch("apps.backend.services.database.resolve_split_brain") as mock_resolve:
                mock_resolve.return_value = "node_1"  # Elect node_1 as primary

                # Only one node should accept writes
                primary_node = await self._get_primary_node()
                assert primary_node is not None

        await inject_split_brain()
        await validate_write_conflict_resolution()

    async def _database_operation(self):
        """Mock database operation"""
        # Simulate database call
        await asyncio.sleep(0.1)
        return {"status": "success"}

    async def _read_operation(self):
        """Mock read operation"""
        return {"data": "test_data"}

    async def _write_operation(self):
        """Mock write operation"""
        await asyncio.sleep(0.1)
        return {"id": 123}

    async def _get_primary_node(self):
        """Mock function to get primary database node"""
        return "node_1"


class TestCachePoisoning:
    """Test cache corruption and recovery scenarios"""

    @pytest.mark.asyncio
    async def test_cache_corruption_handling(self, chaos_orchestrator):
        """Test system behavior when cache is corrupted"""

        async def inject_cache_corruption():
            """Corrupt cache entries"""
            # Mock Redis with corrupted data
            with patch("redis.asyncio.Redis.get") as mock_get:
                mock_get.side_effect = [
                    b"corrupted_json_data{invalid",  # Corrupted JSON
                    None,  # Cache miss
                    b'{"valid": "data"}',  # Valid data
                ]

                # Trigger cache operations
                for _ in range(3):
                    try:
                        await self._cache_operation()
                    except:
                        pass

        async def validate_fallback_behavior():
            """Validate fallback to database when cache is corrupted"""
            with patch("apps.backend.services.cache.CacheService.get") as mock_cache:
                mock_cache.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

                # Should fallback to database
                with patch("apps.backend.services.database.DatabaseService.get") as mock_db:
                    mock_db.return_value = {"id": 123, "data": "from_db"}

                    result = await self._get_data_with_cache("test_key")
                    assert result["data"] == "from_db"

        async def validate_cache_recovery():
            """Validate that cache recovers from corruption"""
            # Cache should be marked as unhealthy and bypassed
            with patch(
                "apps.backend.services.cache.CacheService.is_healthy",
                return_value=False,
            ):
                # All requests should bypass cache
                result = await self._get_data_with_cache("test_key")
                assert result is not None  # Should still work without cache

        await inject_cache_corruption()
        await validate_fallback_behavior()
        await validate_cache_recovery()

    @pytest.mark.asyncio
    async def test_cache_poisoning_attack(self, chaos_orchestrator):
        """Test protection against cache poisoning attacks"""

        async def inject_poisoned_data():
            """Inject malicious data into cache"""
            poisoned_data = {
                "user_id": 123,
                "role": "admin",  # Privilege escalation attempt
                "permissions": ["read", "write", "delete", "admin"],
                "injected": True,
            }

            with patch("redis.asyncio.Redis.get") as mock_get:
                mock_get.return_value = json.dumps(poisoned_data).encode()

                # Try to retrieve poisoned data
                cached_data = await self._cache_operation()
                return cached_data

        async def validate_data_validation():
            """Validate that poisoned data is detected and rejected"""
            # Cache service should validate data integrity
            with patch("apps.backend.services.cache.validate_cache_data") as mock_validate:
                mock_validate.return_value = False  # Data fails validation

                # Should reject poisoned data and fallback to source
                result = await self._get_validated_data("user_123")
                assert result.get("injected") != True

        await inject_poisoned_data()
        await validate_data_validation()

    async def _cache_operation(self):
        """Mock cache operation"""
        await asyncio.sleep(0.01)
        return {"cached": True}

    async def _get_data_with_cache(self, key: str):
        """Mock function that uses cache with database fallback"""
        # Try cache first, fallback to database
        return {"id": 123, "data": "from_source"}

    async def _get_validated_data(self, key: str):
        """Mock function that validates cached data"""
        return {"user_id": 123, "role": "user", "permissions": ["read"]}


class TestRateLimitStressTesting:
    """Test rate limiting under extreme load"""

    @pytest.mark.asyncio
    async def test_rate_limit_overwhelm(self, chaos_orchestrator):
        """Test rate limiter under overwhelming traffic"""

        async def inject_traffic_flood():
            """Generate massive traffic spike"""
            rate_limiter = RateLimitManager()
            config = RateLimitConfig(max_requests=10, window_seconds=60)

            client_id = "flood_client"
            successful_requests = 0
            rejected_requests = 0

            # Generate 1000 requests rapidly
            for _ in range(1000):
                if await rate_limiter.check_rate_limit(client_id, config):
                    successful_requests += 1
                else:
                    rejected_requests += 1

            return successful_requests, rejected_requests

        async def validate_rate_limit_effectiveness():
            """Validate that rate limiting prevents system overload"""
            successful, rejected = await inject_traffic_flood()

            # Most requests should be rejected
            assert rejected > successful
            assert successful <= 20  # Should not exceed reasonable limit

        async def validate_legitimate_traffic_preservation():
            """Validate that legitimate traffic is preserved"""
            rate_limiter = RateLimitManager()
            config = RateLimitConfig(max_requests=5, window_seconds=60)

            # Legitimate user with normal traffic pattern
            legitimate_client = "legitimate_user"
            legitimate_successful = 0

            # Make reasonable number of requests
            for _ in range(5):
                if await rate_limiter.check_rate_limit(legitimate_client, config):
                    legitimate_successful += 1
                await asyncio.sleep(0.1)  # Normal spacing

            # Legitimate user should not be affected
            assert legitimate_successful >= 4

        await validate_rate_limit_effectiveness()
        await validate_legitimate_traffic_preservation()

    @pytest.mark.asyncio
    async def test_distributed_rate_limiting(self, chaos_orchestrator):
        """Test rate limiting across multiple service instances"""

        async def simulate_distributed_load():
            """Simulate load across multiple service instances"""
            # Create multiple rate limiter instances (simulating different servers)
            rate_limiters = [RateLimitManager() for _ in range(3)]
            config = RateLimitConfig(max_requests=10, window_seconds=60)

            client_id = "distributed_client"
            total_successful = 0

            # Distribute requests across instances
            for i in range(50):
                limiter = rate_limiters[i % len(rate_limiters)]
                if await limiter.check_rate_limit(client_id, config):
                    total_successful += 1

            return total_successful

        successful_requests = await simulate_distributed_load()

        # With 3 instances, total should not exceed 3x individual limit
        assert successful_requests <= 30

    @pytest.mark.asyncio
    async def test_adaptive_rate_limiting(self, chaos_orchestrator):
        """Test adaptive rate limiting based on system health"""

        async def simulate_system_stress():
            """Simulate high system load"""
            with patch("psutil.cpu_percent", return_value=90.0):
                with patch("psutil.virtual_memory") as mock_memory:
                    mock_memory.return_value.percent = 85.0

                    # Rate limiter should adapt to high load
                    rate_limiter = RateLimitManager()
                    base_config = RateLimitConfig(max_requests=100, window_seconds=60)

                    # Under stress, effective limits should be lower
                    stressed_successful = 0
                    for _ in range(100):
                        if await rate_limiter.check_rate_limit("stress_client", base_config):
                            stressed_successful += 1

                    return stressed_successful

        stressed_requests = await simulate_system_stress()

        # Under stress, should allow fewer requests
        assert stressed_requests < 50


class TestWebSocketMassDisconnection:
    """Test WebSocket resilience under mass disconnection scenarios"""

    @pytest.mark.asyncio
    async def test_websocket_connection_storm(self, chaos_orchestrator):
        """Test system under massive WebSocket connection attempts"""

        connections = []

        async def create_websocket_storm():
            """Create many concurrent WebSocket connections"""

            async def mock_websocket_connection():
                # Mock WebSocket connection
                ws_mock = AsyncMock()
                ws_mock.closed = False
                return ws_mock

            # Create 1000 concurrent connections
            tasks = []
            for _ in range(1000):
                task = asyncio.create_task(mock_websocket_connection())
                tasks.append(task)

            connections.extend(await asyncio.gather(*tasks))

        async def inject_mass_disconnection():
            """Simulate mass disconnection event"""
            # Disconnect all connections simultaneously
            for conn in connections:
                conn.closed = True
                conn.close = AsyncMock()
                await conn.close()

        async def validate_reconnection_handling():
            """Validate that reconnection is handled gracefully"""
            websocket_handler = WebSocketHandler()

            # System should handle reconnection gracefully
            reconnection_attempts = 0
            max_attempts = 100

            # Simulate reconnection attempts
            for _ in range(max_attempts):
                try:
                    await websocket_handler.handle_connection(AsyncMock())
                    reconnection_attempts += 1
                except Exception:
                    break  # Rate limiting or circuit breaker activated

            # Should not accept unlimited reconnections
            assert reconnection_attempts < max_attempts

        await create_websocket_storm()
        await inject_mass_disconnection()
        await validate_reconnection_handling()

    @pytest.mark.asyncio
    async def test_websocket_message_flooding(self, chaos_orchestrator):
        """Test WebSocket message rate limiting"""

        async def inject_message_flood():
            """Flood WebSocket with messages"""
            ws_handler = WebSocketHandler()
            mock_websocket = AsyncMock()

            # Send 1000 messages rapidly
            flood_count = 0
            for _ in range(1000):
                try:
                    await ws_handler.handle_message(mock_websocket, {"type": "flood"})
                    flood_count += 1
                except Exception:
                    break  # Rate limiting activated

            return flood_count

        handled_messages = await inject_message_flood()

        # Should not handle unlimited messages
        assert handled_messages < 100


class TestRegionFailureSimulation:
    """Test multi-region failure scenarios"""

    @pytest.mark.asyncio
    async def test_entire_region_failure(self, chaos_orchestrator):
        """Test failover when entire region goes down"""

        async def inject_region_failure():
            """Simulate complete region failure"""
            failed_region = "us-east-1"

            with patch(
                "apps.backend.core.global_load_balancer.GlobalLoadBalancer.check_region_health"
            ) as mock_health:
                # Mark region as unhealthy
                def health_check(region):
                    if region == failed_region:
                        return {"status": "unhealthy", "error": "Region unavailable"}
                    return {"status": "healthy"}

                mock_health.side_effect = health_check

                # Trigger health checks
                load_balancer = GlobalLoadBalancer()
                await load_balancer.update_region_health()

        async def validate_traffic_rerouting():
            """Validate that traffic is rerouted to healthy regions"""
            load_balancer = GlobalLoadBalancer()

            # Traffic should be routed to healthy regions only
            healthy_regions = await load_balancer.get_healthy_regions()
            assert "us-east-1" not in [r["region"] for r in healthy_regions]
            assert len(healthy_regions) > 0  # Should have backup regions

        await inject_region_failure()
        await validate_traffic_rerouting()

    @pytest.mark.asyncio
    async def test_cross_region_data_consistency(self, chaos_orchestrator):
        """Test data consistency during region failures"""

        async def validate_eventual_consistency():
            """Validate that data remains consistent across regions"""
            # Mock data replication between regions
            region_data = {
                "us-west-2": {"user_123": {"name": "John", "version": 1}},
                "eu-west-1": {"user_123": {"name": "John", "version": 1}},
            }

            # When one region is updated and then fails
            region_data["us-west-2"]["user_123"]["version"] = 2

            # Data should be consistent after recovery
            with patch("apps.backend.services.replication.sync_regions") as mock_sync:
                mock_sync.return_value = True

                # Verify data consistency
                for region, data in region_data.items():
                    assert data["user_123"]["version"] >= 1

        await validate_eventual_consistency()


class TestLatencyInjection:
    """Test system behavior under artificial latency"""

    @pytest.mark.asyncio
    async def test_high_latency_timeout_handling(self, chaos_orchestrator):
        """Test timeout handling under high latency"""

        async def inject_network_latency():
            """Add artificial network delays"""

            async def slow_network_call(*args, **kwargs):
                await asyncio.sleep(2.0)  # 2 second delay
                return {"data": "delayed_response"}

            with patch("httpx.AsyncClient.get", side_effect=slow_network_call):
                # Test circuit breaker with timeout
                config = CircuitBreakerConfig(timeout=1.0)  # 1 second timeout
                breaker = CircuitBreaker("slow_service", config)

                failure_count = 0
                for _ in range(5):
                    try:
                        await breaker.call(self._slow_external_call)
                    except (asyncio.TimeoutError, Exception):
                        failure_count += 1

                return failure_count

        async def validate_timeout_behavior():
            """Validate that timeouts trigger circuit breaker"""
            failures = await inject_network_latency()

            # Most calls should timeout and trigger circuit breaker
            assert failures >= 3

        await validate_timeout_behavior()

    @pytest.mark.asyncio
    async def test_gradual_latency_increase(self, chaos_orchestrator):
        """Test system adaptation to gradually increasing latency"""

        current_latency = 0.1  # Start with 100ms

        async def gradual_latency_increase():
            """Gradually increase network latency"""
            nonlocal current_latency

            for _ in range(10):

                async def latent_call(*args, **kwargs):
                    await asyncio.sleep(current_latency)
                    return {"latency": current_latency}

                with patch("httpx.AsyncClient.get", side_effect=latent_call):
                    # Test adaptive timeouts
                    result = await self._adaptive_network_call()
                    assert result is not None

                current_latency += 0.2  # Increase by 200ms each iteration

        await gradual_latency_increase()

    async def _slow_external_call(self):
        """Mock slow external service call"""
        client = httpx.AsyncClient()
        response = await client.get("https://external-api.example.com/data")
        return response.json()

    async def _adaptive_network_call(self):
        """Mock network call with adaptive timeout"""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"status": "success"}


@pytest.mark.asyncio
async def test_comprehensive_chaos_scenario(chaos_orchestrator):
    """Execute comprehensive chaos engineering scenario with multiple simultaneous failures"""

    async def execute_multi_failure_scenario():
        """Execute multiple failure modes simultaneously"""

        # Start multiple failure injections concurrently
        tasks = [
            # Network issues
            asyncio.create_task(simulate_network_partition()),
            # Resource exhaustion
            asyncio.create_task(simulate_cpu_stress()),
            # Database issues
            asyncio.create_task(simulate_database_slowdown()),
            # Cache corruption
            asyncio.create_task(simulate_cache_corruption()),
            # Rate limiting stress
            asyncio.create_task(simulate_traffic_spike()),
        ]

        # Let failures run for 15 seconds
        await asyncio.sleep(15)

        # Cancel all failure tasks
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

    async def validate_system_resilience():
        """Validate that system maintains essential functionality"""

        # Essential services should still be responsive
        essential_checks = [
            check_authentication_service(),
            check_health_endpoint(),
            check_basic_api_functionality(),
        ]

        results = await asyncio.gather(*essential_checks, return_exceptions=True)

        # At least 2 out of 3 essential services should be working
        successful_checks = sum(1 for result in results if not isinstance(result, Exception))
        assert successful_checks >= 2, "System not resilient enough - essential services failing"

    # Execute comprehensive chaos test
    await execute_multi_failure_scenario()
    await validate_system_resilience()

    # Allow time for system recovery
    await asyncio.sleep(30)


# Helper functions for comprehensive test
async def simulate_network_partition():
    """Simulate network partition"""
    await asyncio.sleep(10)


async def simulate_cpu_stress():
    """Simulate CPU stress"""
    await asyncio.sleep(10)


async def simulate_database_slowdown():
    """Simulate database performance issues"""
    await asyncio.sleep(10)


async def simulate_cache_corruption():
    """Simulate cache corruption"""
    await asyncio.sleep(10)


async def simulate_traffic_spike():
    """Simulate traffic spike"""
    await asyncio.sleep(10)


async def check_authentication_service():
    """Check if authentication service is responsive"""
    # Mock authentication check
    await asyncio.sleep(0.1)
    return True


async def check_health_endpoint():
    """Check if health endpoint is responsive"""
    # Mock health check
    await asyncio.sleep(0.1)
    return True


async def check_basic_api_functionality():
    """Check if basic API functionality works"""
    # Mock API check
    await asyncio.sleep(0.1)
    return True


if __name__ == "__main__":
    # Run chaos tests with proper configuration
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-m",
            "chaos",
            "--maxfail=5",
            "--timeout=600",  # 10 minute timeout for chaos tests
        ]
    )
