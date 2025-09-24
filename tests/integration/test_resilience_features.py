"""
Integration tests for load balancing and resilience features

Tests circuit breakers, rate limiting, connection pooling, and failover mechanisms.
"""

import asyncio
import time
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
import pytest
import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from apps.backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerState,
    get_circuit_breaker
)
from apps.backend.core.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitScope
)
from apps.backend.api.middleware.resilience import (
    ResilienceMiddleware,
    RetryMiddleware,
    BulkheadMiddleware
)
from database.pool_config_production import (
    ProductionPoolConfig,
    ProductionPoolManager,
    get_production_pool_config
)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            reset_timeout=10.0,
            timeout=1.0
        )
        breaker = CircuitBreaker("test_service", config)

        # Simulate failures
        failing_func = AsyncMock(side_effect=Exception("Service error"))

        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        # Circuit should be open now
        assert breaker.state == CircuitBreakerState.OPEN

        # Further calls should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            await breaker.call(failing_func)

        assert "Circuit breaker 'test_service' is open" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            reset_timeout=0.1,  # 100ms for fast testing
            timeout=1.0
        )
        breaker = CircuitBreaker("recovery_test", config)

        # Open the circuit
        failing_func = AsyncMock(side_effect=Exception("Error"))
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(0.2)

        # Circuit should allow test call (half-open)
        success_func = AsyncMock(return_value="success")

        # First successful call
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.HALF_OPEN

        # Second successful call should close the circuit
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_fallback(self):
        """Test circuit breaker fallback mechanism"""
        async def fallback_func(*args, **kwargs):
            return {"status": "degraded", "message": "Using cached data"}

        config = CircuitBreakerConfig(
            failure_threshold=1,
            fallback=fallback_func
        )
        breaker = CircuitBreaker("fallback_test", config)

        # Open circuit with failure
        failing_func = AsyncMock(side_effect=Exception("Error"))
        with pytest.raises(Exception):
            await breaker.call(failing_func)

        # Next call should use fallback
        result = await breaker.call(failing_func)
        assert result["status"] == "degraded"
        assert "cached data" in result["message"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self):
        """Test circuit breaker metrics collection"""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            enable_monitoring=True
        )
        breaker = CircuitBreaker("metrics_test", config)

        # Mix of successful and failed calls
        success_func = AsyncMock(return_value="ok")
        failing_func = AsyncMock(side_effect=Exception("Error"))

        # 3 successful calls
        for _ in range(3):
            await breaker.call(success_func)

        # 2 failed calls
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        status = breaker.get_status()
        assert status["metrics"]["successful_calls"] == 3
        assert status["metrics"]["failed_calls"] == 2
        assert status["metrics"]["total_calls"] == 5
        assert status["metrics"]["failure_rate"] == 0.4  # 2/5


class TestRateLimiter:
    """Test rate limiting functionality"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = await aioredis.create_redis_pool(
            "redis://localhost:6379/15",  # Use test database 15
            encoding="utf-8"
        )
        yield client
        await client.flushdb()
        client.close()
        await client.wait_closed()

    @pytest.mark.asyncio
    async def test_sliding_window_rate_limit(self, redis_client):
        """Test sliding window rate limiting algorithm"""
        config = RateLimitConfig(
            requests_per_minute=10,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        limiter = RateLimiter(redis_client, config)

        identifier = "test_user_123"
        endpoint = "/api/test"

        # Make 10 requests (should all succeed)
        for i in range(10):
            result = await limiter.check_rate_limit(identifier, endpoint)
            assert result.allowed is True
            assert result.remaining == 9 - i

        # 11th request should be rejected
        result = await limiter.check_rate_limit(identifier, endpoint)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None

    @pytest.mark.asyncio
    async def test_token_bucket_rate_limit(self, redis_client):
        """Test token bucket rate limiting algorithm"""
        config = RateLimitConfig(
            token_bucket_capacity=5,
            token_bucket_refill_rate=1.0,  # 1 token per second
            strategy=RateLimitStrategy.TOKEN_BUCKET
        )
        limiter = RateLimiter(redis_client, config)

        identifier = "test_token_bucket"

        # Consume all tokens
        for _ in range(5):
            result = await limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Should be rejected (no tokens left)
        result = await limiter.check_rate_limit(identifier)
        assert result.allowed is False

        # Wait for token refill
        await asyncio.sleep(2)  # Wait for 2 tokens to refill

        # Should allow 2 more requests
        for _ in range(2):
            result = await limiter.check_rate_limit(identifier)
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_user_tier_multipliers(self, redis_client):
        """Test user tier rate limit multipliers"""
        config = RateLimitConfig(
            requests_per_minute=10,
            enable_user_tiers=True,
            user_tier_multipliers={
                "free": 1.0,
                "premium": 5.0
            }
        )
        limiter = RateLimiter(redis_client, config)

        # Free user gets 10 requests
        free_user = "free_user_1"
        for _ in range(10):
            result = await limiter.check_rate_limit(free_user, user_tier="free")
            assert result.allowed is True

        result = await limiter.check_rate_limit(free_user, user_tier="free")
        assert result.allowed is False

        # Premium user gets 50 requests
        premium_user = "premium_user_1"
        for _ in range(50):
            result = await limiter.check_rate_limit(premium_user, user_tier="premium")
            assert result.allowed is True

        result = await limiter.check_rate_limit(premium_user, user_tier="premium")
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_endpoint_specific_limits(self, redis_client):
        """Test endpoint-specific rate limits"""
        config = RateLimitConfig(
            requests_per_minute=100,  # Default
            endpoint_limits={
                "/auth/login": {"requests_per_minute": 5},
                "/api/generate": {"requests_per_minute": 20}
            }
        )
        limiter = RateLimiter(redis_client, config)

        user = "test_user"

        # Login endpoint - limited to 5
        for _ in range(5):
            result = await limiter.check_rate_limit(user, "/auth/login")
            assert result.allowed is True

        result = await limiter.check_rate_limit(user, "/auth/login")
        assert result.allowed is False

        # Generate endpoint - limited to 20
        for _ in range(20):
            result = await limiter.check_rate_limit(user, "/api/generate")
            assert result.allowed is True

        result = await limiter.check_rate_limit(user, "/api/generate")
        assert result.allowed is False


class TestResilienceMiddleware:
    """Test resilience middleware integration"""

    @pytest.fixture
    def app_with_resilience(self):
        """Create FastAPI app with resilience middleware"""
        app = FastAPI()

        # Add resilience middleware
        app.add_middleware(ResilienceMiddleware)
        app.add_middleware(
            RetryMiddleware,
            max_retries=3,
            retry_delay=0.1,
            exponential_backoff=True
        )
        app.add_middleware(
            BulkheadMiddleware,
            max_concurrent_requests=10,
            max_queue_size=5
        )

        # Test endpoints
        @app.get("/api/stable")
        async def stable_endpoint():
            return {"status": "ok"}

        @app.get("/api/flaky")
        async def flaky_endpoint():
            if time.time() % 3 < 1:  # Fail 1/3 of the time
                raise HTTPException(status_code=503, detail="Service unavailable")
            return {"status": "ok"}

        @app.get("/api/slow")
        async def slow_endpoint():
            await asyncio.sleep(2)
            return {"status": "ok"}

        return app

    @pytest.mark.asyncio
    async def test_retry_middleware(self, app_with_resilience):
        """Test retry middleware handles transient failures"""
        async with httpx.AsyncClient(app=app_with_resilience, base_url="http://test") as client:
            # Stable endpoint should always work
            response = await client.get("/api/stable")
            assert response.status_code == 200

            # Flaky endpoint should eventually succeed with retries
            successful_count = 0
            for _ in range(10):
                response = await client.get("/api/flaky")
                if response.status_code == 200:
                    successful_count += 1

            # With retries, success rate should be higher than 1/3
            assert successful_count > 3

    @pytest.mark.asyncio
    async def test_bulkhead_pattern(self, app_with_resilience):
        """Test bulkhead pattern limits concurrent requests"""
        async with httpx.AsyncClient(app=app_with_resilience, base_url="http://test") as client:
            # Send many concurrent slow requests
            tasks = [
                client.get("/api/slow", timeout=5.0)
                for _ in range(20)  # More than bulkhead limit
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Some requests should be rejected due to bulkhead limit
            rejected_count = sum(
                1 for r in results
                if isinstance(r, httpx.HTTPStatusError) and r.response.status_code == 503
            )

            assert rejected_count > 0  # Some requests should be rejected


class TestDatabasePooling:
    """Test database connection pooling"""

    def test_production_pool_config(self):
        """Test production pool configuration"""
        config = get_production_pool_config("api_service")

        # Check pool size is optimized
        assert config.pool_size >= 10
        assert config.pool_size <= 50

        # Check overflow is configured
        assert config.max_overflow >= config.pool_size

        # Check recycling is enabled
        assert config.pool_recycle == 900  # 15 minutes

        # Check pre-ping is enabled
        assert config.pool_pre_ping is True

    def test_service_specific_pools(self):
        """Test service-specific pool configurations"""
        config = ProductionPoolConfig()

        # API service - balanced configuration
        api_config = config.get_service_config("api_service")
        assert api_config["pool_size"] >= 15
        assert api_config["statement_timeout"] == 30000  # 30 seconds

        # Agent service - longer timeouts
        agent_config = config.get_service_config("agent_service")
        assert agent_config["statement_timeout"] == 300000  # 5 minutes

        # WebSocket service - more connections, shorter timeout
        ws_config = config.get_service_config("websocket_service")
        assert ws_config["pool_recycle"] == 600  # 10 minutes
        assert ws_config["statement_timeout"] == 15000  # 15 seconds

    @pytest.mark.asyncio
    async def test_connection_pre_warming(self):
        """Test connection pre-warming feature"""
        manager = ProductionPoolManager()

        # Mock connection creation
        with patch.object(manager, '_pre_warm_connections') as mock_pre_warm:
            mock_pre_warm.return_value = asyncio.coroutine(lambda x, y: None)()

            await manager.initialize_pools("api_service")

            # Should pre-warm connections
            mock_pre_warm.assert_called_once()

    def test_pgbouncer_config_generation(self):
        """Test PgBouncer configuration generation"""
        manager = ProductionPoolManager()
        pgbouncer_config = manager.get_pgbouncer_config()

        # Check configuration contains required sections
        assert "[databases]" in pgbouncer_config
        assert "[pgbouncer]" in pgbouncer_config

        # Check pool modes
        assert "pool_mode=transaction" in pgbouncer_config
        assert "pool_mode=session" in pgbouncer_config

        # Check limits
        assert "max_client_conn" in pgbouncer_config
        assert "default_pool_size" in pgbouncer_config


class TestEndToEndResilience:
    """End-to-end tests for complete resilience stack"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cascading_failure_prevention(self):
        """Test that circuit breakers prevent cascading failures"""
        # Create a chain of services
        database_breaker = get_circuit_breaker(
            "database",
            CircuitBreakerConfig(failure_threshold=2, reset_timeout=1.0)
        )

        api_breaker = get_circuit_breaker(
            "api",
            CircuitBreakerConfig(failure_threshold=3, reset_timeout=2.0)
        )

        # Simulate database failures
        database_func = AsyncMock(side_effect=Exception("Database down"))

        async def api_func():
            # API tries to call database
            try:
                return await database_breaker.call(database_func)
            except CircuitBreakerError:
                # Return degraded response
                return {"status": "degraded", "source": "cache"}

        # First few API calls trigger database circuit breaker
        for _ in range(2):
            with pytest.raises(Exception):
                await database_breaker.call(database_func)

        # Database circuit is now open
        assert database_breaker.state == CircuitBreakerState.OPEN

        # API calls should return degraded response without hitting database
        result = await api_breaker.call(api_func)
        assert result["status"] == "degraded"
        assert result["source"] == "cache"

        # API circuit should still be closed (prevented cascade)
        assert api_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_load_shedding_under_pressure(self):
        """Test system sheds load appropriately under pressure"""
        # Simulate high load scenario
        config = RateLimitConfig(
            requests_per_second=10,
            burst_size=5
        )

        # Mock Redis for rate limiting
        redis_mock = AsyncMock()
        limiter = RateLimiter(redis_mock, config)

        # Simulate burst of requests
        results = []
        for i in range(20):  # Double the limit
            result = await limiter.check_rate_limit(f"user_{i % 5}")
            results.append(result.allowed)

        # Should accept some and reject some
        accepted = sum(results)
        rejected = len(results) - accepted

        assert accepted > 0  # Some requests accepted
        assert rejected > 0  # Some requests rejected (load shedding)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_graceful_degradation(self):
        """Test system degrades gracefully under failure conditions"""
        # Create app with fallback responses
        app = FastAPI()

        circuit_breaker = get_circuit_breaker(
            "external_service",
            CircuitBreakerConfig(
                failure_threshold=1,
                fallback=lambda: {"data": "cached", "fresh": False}
            )
        )

        @app.get("/data")
        async def get_data():
            async def fetch_fresh_data():
                # Simulate external service failure
                raise Exception("External service down")

            try:
                result = await circuit_breaker.call(fetch_fresh_data)
                return {"data": result, "fresh": True}
            except CircuitBreakerError:
                # Return cached/degraded data
                return {"data": "cached", "fresh": False}

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # First request opens circuit
            response = await client.get("/data")
            assert response.status_code == 200

            # Subsequent requests get cached data
            response = await client.get("/data")
            assert response.status_code == 200
            data = response.json()
            assert data["fresh"] is False
            assert data["data"] == "cached"