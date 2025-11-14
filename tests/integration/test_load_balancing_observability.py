"""
Integration tests for load balancing with observability.
Tests the complete system including circuit breakers, rate limiting,
database replicas, edge caching, and observability metrics.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis

from apps.backend.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from apps.backend.core.edge_cache import EdgeCache
from apps.backend.core.observability.anomaly_detection import AnomalyDetector
from apps.backend.core.observability.telemetry import MetricsCollector
from apps.backend.core.rate_limiter import RateLimiter
from database.replica_router import ConsistencyLevel, ReplicaRouter


class TestLoadBalancingWithObservability:
    """Test suite for load balancing with observability features."""

    @pytest.fixture
    async def circuit_breaker(self):
        """Create a test circuit breaker."""
        cb = CircuitBreaker(
            name="test_service",
            failure_threshold=3,
            recovery_timeout=5,
            expected_exception=Exception,
        )
        yield cb
        await cb.reset()

    @pytest.fixture
    async def rate_limiter(self):
        """Create a test rate limiter."""
        rl = RateLimiter(redis_client=Mock(spec=redis.Redis), default_limit=10, default_window=60)
        yield rl

    @pytest.fixture
    async def edge_cache(self):
        """Create a test edge cache."""
        cache = EdgeCache(redis_client=Mock(spec=redis.Redis), cdn_provider="cloudflare")
        yield cache

    @pytest.fixture
    async def metrics_collector(self):
        """Create a test metrics collector."""
        collector = MetricsCollector()
        yield collector

    @pytest.fixture
    async def anomaly_detector(self):
        """Create a test anomaly detector."""
        detector = AnomalyDetector(sensitivity=2.0, window_size=100)
        yield detector

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_metrics(self, circuit_breaker, metrics_collector):
        """Test circuit breaker integration with metrics collection."""

        # Simulate failures to trip the circuit breaker
        for _ in range(3):
            try:
                async with circuit_breaker:
                    await metrics_collector.record_request_start("test_service")
                    raise Exception("Service failure")
            except Exception:
                await metrics_collector.record_request_end("test_service", success=False)

        # Verify circuit is open
        assert circuit_breaker.state == "OPEN"

        # Check metrics reflect the failures
        error_rate = await metrics_collector.get_error_rate()
        assert error_rate > 0

        # Wait for recovery timeout
        await asyncio.sleep(5)

        # Test half-open state with success
        try:
            async with circuit_breaker:
                await metrics_collector.record_request_start("test_service")
                # Successful call
                await metrics_collector.record_request_end("test_service", success=True)
        except CircuitBreakerError:
            pytest.fail("Circuit breaker should allow test call in HALF_OPEN state")

        # Verify circuit is closed again
        assert circuit_breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_rate_limiter_with_metrics(self, rate_limiter, metrics_collector):
        """Test rate limiter integration with metrics collection."""

        # Mock Redis operations
        rate_limiter.redis.incr = Mock(side_effect=range(1, 20))
        rate_limiter.redis.expire = Mock()

        # Simulate requests up to the limit
        for i in range(10):
            allowed = await rate_limiter.allow_request(key="test_user", limit=10, window=60)
            assert allowed
            await metrics_collector.record_request_start("rate_limited_endpoint")
            await metrics_collector.record_request_end("rate_limited_endpoint", success=True)

        # Next request should be rate limited
        rate_limiter.redis.incr.return_value = 11
        allowed = await rate_limiter.allow_request(key="test_user", limit=10, window=60)
        assert not allowed

        # Record rate limit hit in metrics
        await metrics_collector.increment_counter(
            "rate_limit_exceeded", labels={"user": "test_user"}
        )

        # Verify metrics
        stats = await rate_limiter.get_stats()
        assert stats["throttled_percentage"] > 0

    @pytest.mark.asyncio
    async def test_database_replica_routing_with_metrics(self, metrics_collector):
        """Test database replica routing with metrics collection."""

        # Create mock replica router
        router = ReplicaRouter(
            master_url="postgresql://master/db",
            replica_urls=["postgresql://replica1/db", "postgresql://replica2/db"],
        )

        # Mock health checks
        with patch.object(router, "check_replica_health", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True

            # Test read routing to replicas
            for i in range(10):
                start_time = time.time()

                replica = await router.get_read_connection(
                    consistency_level=ConsistencyLevel.EVENTUAL
                )

                duration = (time.time() - start_time) * 1000
                await metrics_collector.record_histogram(
                    "db_connection_time",
                    duration,
                    labels={"operation": "read", "replica": replica},
                )

            # Test write routing to master
            master = await router.get_write_connection()
            assert "master" in master

            # Verify replica distribution metrics
            replicas = await router.get_replica_health()
            assert len(replicas) == 2

    @pytest.mark.asyncio
    async def test_edge_cache_with_metrics(self, edge_cache, metrics_collector):
        """Test edge cache integration with metrics collection."""

        # Mock cache operations
        edge_cache.redis.get = Mock(side_effect=[None, b"cached_value"])
        edge_cache.redis.setex = Mock()

        # First request - cache miss
        start_time = time.time()
        result = await edge_cache.get("test_key")
        duration = (time.time() - start_time) * 1000

        assert result is None
        await metrics_collector.increment_counter("cache_miss", labels={"tier": "edge"})
        await metrics_collector.record_histogram(
            "cache_operation_duration",
            duration,
            labels={"operation": "get", "result": "miss"},
        )

        # Set cache value
        await edge_cache.set("test_key", "cached_value", ttl=300)

        # Second request - cache hit
        start_time = time.time()
        result = await edge_cache.get("test_key")
        duration = (time.time() - start_time) * 1000

        assert result == "cached_value"
        await metrics_collector.increment_counter("cache_hit", labels={"tier": "edge"})
        await metrics_collector.record_histogram(
            "cache_operation_duration",
            duration,
            labels={"operation": "get", "result": "hit"},
        )

        # Calculate hit rate
        stats = await edge_cache.get_stats()
        assert stats["hit_rate"] > 0

    @pytest.mark.asyncio
    async def test_anomaly_detection_integration(self, anomaly_detector, metrics_collector):
        """Test anomaly detection with metrics collection."""

        # Generate normal traffic pattern
        normal_latencies = [50, 52, 48, 51, 49, 53, 50, 51, 52, 49]

        for latency in normal_latencies:
            await metrics_collector.record_histogram(
                "request_latency", latency, labels={"endpoint": "/api/test"}
            )

            # Feed to anomaly detector
            is_anomaly = await anomaly_detector.detect_point_anomaly(
                value=latency, metric_name="request_latency"
            )
            assert not is_anomaly

        # Generate anomalous traffic
        anomalous_latencies = [500, 450, 480]  # 10x normal

        for latency in anomalous_latencies:
            await metrics_collector.record_histogram(
                "request_latency",
                latency,
                labels={"endpoint": "/api/test", "anomaly": "true"},
            )

            # Detect anomaly
            is_anomaly = await anomaly_detector.detect_point_anomaly(
                value=latency, metric_name="request_latency"
            )
            assert is_anomaly

            # Record anomaly
            await metrics_collector.increment_counter(
                "anomaly_detected",
                labels={"metric": "request_latency", "severity": "high"},
            )

        # Verify anomalies were detected
        anomalies = await anomaly_detector.get_recent_anomalies(limit=10)
        assert len(anomalies) >= 3

    @pytest.mark.asyncio
    async def test_full_system_integration(
        self,
        circuit_breaker,
        rate_limiter,
        edge_cache,
        metrics_collector,
        anomaly_detector,
    ):
        """Test complete load balancing system with observability."""

        # Simulate a full request flow
        user_id = "user_456"
        endpoint = "/api/data"

        # 1. Check rate limit
        rate_limiter.redis.incr = Mock(return_value=5)
        rate_limiter.redis.expire = Mock()

        allowed = await rate_limiter.allow_request(key=f"user:{user_id}", limit=100, window=60)
        assert allowed

        # 2. Check cache
        edge_cache.redis.get = Mock(return_value=None)
        cache_result = await edge_cache.get(f"{endpoint}:{user_id}")

        if cache_result is None:
            await metrics_collector.increment_counter("cache_miss")

            # 3. Use circuit breaker for backend call
            async with circuit_breaker:
                start_time = time.time()

                # Simulate backend processing
                await asyncio.sleep(0.05)  # 50ms latency

                duration = (time.time() - start_time) * 1000

                # Record metrics
                await metrics_collector.record_histogram(
                    "request_duration",
                    duration,
                    labels={"endpoint": endpoint, "method": "GET", "status": "200"},
                )

                # Check for anomalies
                is_anomaly = await anomaly_detector.detect_point_anomaly(
                    value=duration, metric_name="request_duration"
                )

                if is_anomaly:
                    await metrics_collector.increment_counter(
                        "anomaly_detected", labels={"type": "latency_spike"}
                    )

            # 4. Cache the result
            edge_cache.redis.setex = Mock()
            await edge_cache.set(f"{endpoint}:{user_id}", "response_data", ttl=300)

        # 5. Collect final metrics
        await metrics_collector.record_request_end(endpoint, success=True)

        # Verify system health
        metrics = {
            "request_rate": await metrics_collector.get_request_rate(),
            "error_rate": await metrics_collector.get_error_rate(),
            "p95_latency": await metrics_collector.get_percentile_latency(95),
            "circuit_breaker_state": circuit_breaker.state,
            "cache_hit_rate": (await edge_cache.get_stats())["hit_rate"],
        }

        # System should be healthy
        assert metrics["error_rate"] < 0.01  # Less than 1% errors
        assert metrics["p95_latency"] < 100  # Less than 100ms P95
        assert metrics["circuit_breaker_state"] == "CLOSED"

    @pytest.mark.asyncio
    async def test_observability_data_correlation(self, metrics_collector):
        """Test correlation of observability data across components."""

        trace_id = "trace_789"

        # Simulate distributed trace
        spans = [
            {
                "service": "api_gateway",
                "operation": "handle_request",
                "duration": 10,
                "trace_id": trace_id,
            },
            {
                "service": "rate_limiter",
                "operation": "check_limit",
                "duration": 2,
                "trace_id": trace_id,
            },
            {
                "service": "cache",
                "operation": "get",
                "duration": 5,
                "trace_id": trace_id,
            },
            {
                "service": "database",
                "operation": "query",
                "duration": 30,
                "trace_id": trace_id,
            },
        ]

        total_duration = 0
        for span in spans:
            await metrics_collector.record_histogram(
                f"span_duration_{span['service']}",
                span["duration"],
                labels={"operation": span["operation"], "trace_id": trace_id},
            )
            total_duration += span["duration"]

        # Verify trace correlation
        assert total_duration == 47  # Sum of all span durations

        # Check if any span exceeded SLO
        slo_threshold = 20  # 20ms per operation

        violations = []
        for span in spans:
            if span["duration"] > slo_threshold:
                violations.append(span["service"])
                await metrics_collector.increment_counter(
                    "slo_violation",
                    labels={"service": span["service"], "operation": span["operation"]},
                )

        assert "database" in violations  # Database query exceeded SLO


@pytest.mark.asyncio
class TestObservabilityEndpoints:
    """Test observability API endpoints."""

    @pytest.fixture
    def mock_pusher(self):
        """Mock Pusher service."""
        with patch("apps.backend.services.pusher.trigger_event") as mock:
            yield mock

    async def test_metrics_streaming_via_pusher(self, mock_pusher):
        """Test that metrics are streamed via Pusher channel."""

        from apps.backend.api.v1.endpoints.observability import stream_metrics_to_pusher

        # Run streaming task for one iteration
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError()  # Stop after first iteration

            try:
                await stream_metrics_to_pusher()
            except asyncio.CancelledError:
                pass

        # Verify Pusher was called with correct channel and data
        mock_pusher.assert_called_once()
        call_args = mock_pusher.call_args

        assert call_args[1]["channel"] == "observability-metrics"
        assert call_args[1]["event"] == "metrics.updated"
        assert "metrics" in call_args[1]["data"]
        assert "component_health" in call_args[1]["data"]
        assert "system_status" in call_args[1]["data"]
