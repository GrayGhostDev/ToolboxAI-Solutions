"""
Unit tests for the Health and System Status API Router.

Tests cover health checks, application info, service status endpoints,
circuit breakers, rate limiting, and comprehensive system monitoring.
"""

import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status


@pytest.mark.unit
class TestHealthCheck:
    """Tests for comprehensive health check endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, test_client):
        """Test health check when all services are healthy"""
        mock_services = {
            "database": {"status": "healthy"},
            "redis": {"status": "healthy"},
            "pusher": {"status": "healthy"},
            "agents": {"status": "healthy"},
            "supabase": {"status": "healthy"},
        }

        mock_request = Mock()
        mock_request.app.state.start_time = time.time() - 3600  # 1 hour uptime

        with patch(
            "apps.backend.api.routers.health._check_all_services",
            AsyncMock(return_value=mock_services),
        ):
            response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime" in data
        assert data["uptime"] > 0
        assert "checks" in data
        assert data["checks"]["database"] is True

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, test_client):
        """Test health check when some services are degraded"""
        mock_services = {
            "database": {"status": "healthy"},
            "redis": {"status": "unhealthy"},
            "pusher": {"status": "healthy"},
            "agents": {"status": "degraded"},
            "supabase": {"status": "healthy"},
        }

        with patch(
            "apps.backend.api.routers.health._check_all_services",
            AsyncMock(return_value=mock_services),
        ):
            response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["redis"] is False
        assert data["checks"]["agents"] is False

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, test_client):
        """Test health check with exception"""
        with patch(
            "apps.backend.api.routers.health._check_all_services",
            AsyncMock(side_effect=Exception("Service check failed")),
        ):
            response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["uptime"] >= 0


@pytest.mark.unit
class TestApplicationInfo:
    """Tests for application information endpoint"""

    def test_get_app_info_success(self, test_client):
        """Test successful app info retrieval"""
        response = test_client.get("/info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "app_name" in data["data"]
        assert "version" in data["data"]
        assert "environment" in data["data"]
        assert "features" in data["data"]
        assert data["data"]["features"]["authentication"] is True
        assert data["data"]["features"]["ai_agents"] is True

    def test_get_app_info_failure(self, test_client):
        """Test app info retrieval with error"""
        with patch(
            "apps.backend.api.routers.health.settings.APP_NAME",
            side_effect=Exception("Config error"),
        ):
            response = test_client.get("/info")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestPusherStatus:
    """Tests for Pusher status endpoint"""

    def test_get_pusher_status_success(self, test_client):
        """Test successful Pusher status retrieval"""
        mock_status = {
            "enabled": True,
            "connected": True,
            "app_id": "test_app_id",
            "cluster": "us2",
        }

        with patch("apps.backend.api.routers.health.get_pusher_status", return_value=mock_status):
            response = test_client.get("/pusher/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["enabled"] is True
        assert data["data"]["connected"] is True

    def test_get_pusher_status_not_configured(self, test_client):
        """Test Pusher status when not configured"""
        with patch(
            "apps.backend.api.routers.health.get_pusher_status",
            side_effect=ImportError("Pusher not available"),
        ):
            response = test_client.get("/pusher/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"
        assert data["data"]["enabled"] is False

    def test_get_pusher_status_error(self, test_client):
        """Test Pusher status with error"""
        with patch(
            "apps.backend.api.routers.health.get_pusher_status",
            side_effect=Exception("Pusher error"),
        ):
            response = test_client.get("/pusher/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.unit
class TestResilienceStatus:
    """Tests for resilience features status endpoint"""

    @pytest.mark.asyncio
    async def test_get_resilience_status_success(self, test_client):
        """Test successful resilience status retrieval"""
        mock_status = {
            "circuit_breakers": {"count": 5, "status": "healthy"},
            "rate_limiters": {"count": 10, "status": "healthy"},
            "retries": {"enabled": True},
        }

        with patch(
            "apps.backend.api.routers.health.get_resilience_status",
            AsyncMock(return_value=mock_status),
        ):
            response = test_client.get("/resilience/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "circuit_breakers" in data["data"]

    @pytest.mark.asyncio
    async def test_get_resilience_status_not_configured(self, test_client):
        """Test resilience status when not configured"""
        with patch(
            "apps.backend.api.routers.health.get_resilience_status",
            AsyncMock(side_effect=ImportError()),
        ):
            response = test_client.get("/resilience/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"
        assert data["data"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_get_resilience_status_error(self, test_client):
        """Test resilience status with error"""
        with patch(
            "apps.backend.api.routers.health.get_resilience_status",
            AsyncMock(side_effect=Exception("Resilience error")),
        ):
            response = test_client.get("/resilience/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.unit
class TestCircuitBreakers:
    """Tests for circuit breaker endpoints"""

    @pytest.mark.asyncio
    async def test_get_circuit_breakers_status_success(self, test_client):
        """Test successful circuit breakers status retrieval"""
        mock_status = {
            "database_breaker": {"state": "closed", "failures": 0},
            "api_breaker": {"state": "closed", "failures": 0},
        }

        with patch(
            "apps.backend.api.routers.health.get_all_circuit_breakers_status",
            AsyncMock(return_value=mock_status),
        ):
            response = test_client.get("/circuit-breakers/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "database_breaker" in data["data"]

    @pytest.mark.asyncio
    async def test_get_circuit_breakers_status_not_configured(self, test_client):
        """Test circuit breakers status when not configured"""
        with patch(
            "apps.backend.api.routers.health.get_all_circuit_breakers_status",
            AsyncMock(side_effect=ImportError()),
        ):
            response = test_client.get("/circuit-breakers/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"
        assert data["data"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_get_circuit_breakers_status_error(self, test_client):
        """Test circuit breakers status with error"""
        with patch(
            "apps.backend.api.routers.health.get_all_circuit_breakers_status",
            AsyncMock(side_effect=Exception("CB error")),
        ):
            response = test_client.get("/circuit-breakers/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"

    def test_reset_circuit_breaker_success(self, test_client):
        """Test successful circuit breaker reset"""
        response = test_client.post("/circuit-breakers/database_breaker/reset")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["breaker_name"] == "database_breaker"
        assert data["data"]["reset"] is True

    def test_reset_circuit_breaker_error(self, test_client):
        """Test circuit breaker reset with error"""
        # The endpoint currently doesn't raise exceptions, but test error path
        with patch(
            "apps.backend.api.routers.health.logger.error", side_effect=Exception("Reset error")
        ):
            response = test_client.post("/circuit-breakers/test_breaker/reset")

        # Should still return success for current implementation
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
class TestRateLimitUsage:
    """Tests for rate limit usage endpoint"""

    def test_get_rate_limit_usage_success(self, test_client):
        """Test successful rate limit usage retrieval"""
        identifier = "192.168.1.1"
        response = test_client.get(f"/rate-limit/usage/{identifier}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["identifier"] == identifier
        assert "requests_made" in data["data"]
        assert "requests_remaining" in data["data"]

    def test_get_rate_limit_usage_special_identifier(self, test_client):
        """Test rate limit usage with special identifier"""
        identifier = "user_abc123"
        response = test_client.get(f"/rate-limit/usage/{identifier}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["identifier"] == identifier

    def test_get_rate_limit_usage_error(self, test_client):
        """Test rate limit usage retrieval with error"""
        # Mock datetime to cause an error
        with patch("apps.backend.api.routers.health.datetime") as mock_datetime:
            mock_datetime.now.side_effect = Exception("Time error")
            response = test_client.get("/rate-limit/usage/test_id")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.unit
class TestSentryStatus:
    """Tests for Sentry monitoring status endpoint"""

    def test_get_sentry_status_enabled(self, test_client):
        """Test Sentry status when enabled"""
        mock_sentry_manager = Mock()
        mock_sentry_manager.initialized = True

        with patch("apps.backend.api.routers.health.sentry_manager", mock_sentry_manager):
            with patch(
                "apps.backend.api.routers.health.settings.SENTRY_DSN", "https://test@sentry.io/123"
            ):
                with patch("apps.backend.api.routers.health.settings.SENTRY_SAMPLE_RATE", 0.5):
                    response = test_client.get("/sentry/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["enabled"] is True
        assert data["data"]["dsn_configured"] is True
        assert data["data"]["sample_rate"] == 0.5

    def test_get_sentry_status_disabled(self, test_client):
        """Test Sentry status when disabled"""
        mock_sentry_manager = Mock()
        mock_sentry_manager.initialized = False

        with patch("apps.backend.api.routers.health.sentry_manager", mock_sentry_manager):
            response = test_client.get("/sentry/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["enabled"] is False

    def test_get_sentry_status_error(self, test_client):
        """Test Sentry status with error"""
        with patch(
            "apps.backend.api.routers.health.sentry_manager", side_effect=Exception("Sentry error")
        ):
            response = test_client.get("/sentry/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.unit
class TestServiceChecks:
    """Tests for service check helper functions"""

    @pytest.mark.asyncio
    async def test_check_all_services(self):
        """Test checking all services"""
        from apps.backend.api.routers.health import _check_all_services

        with patch(
            "apps.backend.api.routers.health._check_database",
            AsyncMock(return_value={"status": "healthy"}),
        ):
            with patch(
                "apps.backend.api.routers.health._check_redis",
                AsyncMock(return_value={"status": "healthy"}),
            ):
                with patch(
                    "apps.backend.api.routers.health._check_pusher",
                    AsyncMock(return_value={"status": "healthy"}),
                ):
                    with patch(
                        "apps.backend.api.routers.health._check_agents",
                        AsyncMock(return_value={"status": "healthy"}),
                    ):
                        with patch(
                            "apps.backend.api.routers.health._check_supabase",
                            AsyncMock(return_value={"status": "healthy"}),
                        ):
                            services = await _check_all_services()

        assert len(services) == 5
        assert all(service["status"] == "healthy" for service in services.values())

    @pytest.mark.asyncio
    async def test_check_database_healthy(self):
        """Test database health check when healthy"""
        from apps.backend.api.routers.health import _check_database

        with patch("apps.backend.api.routers.health.db_service"):
            result = await _check_database()

        assert result["status"] == "healthy"
        assert result["type"] == "postgresql"

    @pytest.mark.asyncio
    async def test_check_database_unhealthy(self):
        """Test database health check when unhealthy"""
        from apps.backend.api.routers.health import _check_database

        with patch(
            "apps.backend.api.routers.health.db_service",
            side_effect=Exception("DB connection failed"),
        ):
            result = await _check_database()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self):
        """Test Redis health check when healthy"""
        from apps.backend.api.routers.health import _check_redis

        mock_redis = Mock()
        mock_redis.ping.return_value = True

        with patch("apps.backend.api.routers.health.settings.REDIS_URL", "redis://localhost:6379"):
            with patch("redis.from_url", return_value=mock_redis):
                result = await _check_redis()

        assert result["status"] == "healthy"
        assert result["type"] == "redis"

    @pytest.mark.asyncio
    async def test_check_redis_not_configured(self):
        """Test Redis health check when not configured"""
        from apps.backend.api.routers.health import _check_redis

        with patch("apps.backend.api.routers.health.settings.REDIS_URL", None):
            result = await _check_redis()

        assert result["status"] == "not_configured"

    @pytest.mark.asyncio
    async def test_check_redis_unhealthy(self):
        """Test Redis health check when unhealthy"""
        from apps.backend.api.routers.health import _check_redis

        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Redis connection failed")

        with patch("apps.backend.api.routers.health.settings.REDIS_URL", "redis://localhost:6379"):
            with patch("redis.from_url", return_value=mock_redis):
                result = await _check_redis()

        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_pusher_healthy(self):
        """Test Pusher health check when healthy"""
        from apps.backend.api.routers.health import _check_pusher

        mock_status = {"enabled": True, "connected": True}

        with patch("apps.backend.api.routers.health.get_pusher_status", return_value=mock_status):
            result = await _check_pusher()

        assert result["status"] == "healthy"
        assert result["details"] == mock_status

    @pytest.mark.asyncio
    async def test_check_pusher_not_configured(self):
        """Test Pusher health check when not configured"""
        from apps.backend.api.routers.health import _check_pusher

        with patch(
            "apps.backend.api.routers.health.get_pusher_status", return_value={"enabled": False}
        ):
            result = await _check_pusher()

        assert result["status"] == "not_configured"

    @pytest.mark.asyncio
    async def test_check_pusher_unhealthy(self):
        """Test Pusher health check when unhealthy"""
        from apps.backend.api.routers.health import _check_pusher

        with patch(
            "apps.backend.api.routers.health.get_pusher_status",
            side_effect=Exception("Pusher error"),
        ):
            result = await _check_pusher()

        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_agents_healthy(self):
        """Test agents health check when healthy"""
        from apps.backend.api.routers.health import _check_agents

        mock_health = {"status": "healthy", "agents": {"content": "running"}}

        with patch(
            "apps.backend.api.routers.health.get_agent_health", AsyncMock(return_value=mock_health)
        ):
            result = await _check_agents()

        assert result["status"] == "healthy"
        assert result["details"] == mock_health

    @pytest.mark.asyncio
    async def test_check_agents_degraded(self):
        """Test agents health check when degraded"""
        from apps.backend.api.routers.health import _check_agents

        mock_health = {"status": "degraded", "agents": {"content": "slow"}}

        with patch(
            "apps.backend.api.routers.health.get_agent_health", AsyncMock(return_value=mock_health)
        ):
            result = await _check_agents()

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_agents_unhealthy(self):
        """Test agents health check when unhealthy"""
        from apps.backend.api.routers.health import _check_agents

        with patch(
            "apps.backend.api.routers.health.get_agent_health",
            AsyncMock(side_effect=Exception("Agent error")),
        ):
            result = await _check_agents()

        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_supabase_healthy(self):
        """Test Supabase health check when healthy"""
        from apps.backend.api.routers.health import _check_supabase

        with patch(
            "apps.backend.api.routers.health.health_check_supabase", AsyncMock(return_value=True)
        ):
            result = await _check_supabase()

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_supabase_unhealthy(self):
        """Test Supabase health check when unhealthy"""
        from apps.backend.api.routers.health import _check_supabase

        with patch(
            "apps.backend.api.routers.health.health_check_supabase", AsyncMock(return_value=False)
        ):
            result = await _check_supabase()

        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_supabase_not_configured(self):
        """Test Supabase health check when not configured"""
        from apps.backend.api.routers.health import _check_supabase

        with patch(
            "apps.backend.api.routers.health.health_check_supabase",
            AsyncMock(side_effect=ImportError()),
        ):
            result = await _check_supabase()

        assert result["status"] == "not_configured"

    @pytest.mark.asyncio
    async def test_check_supabase_error(self):
        """Test Supabase health check with error"""
        from apps.backend.api.routers.health import _check_supabase

        with patch(
            "apps.backend.api.routers.health.health_check_supabase",
            AsyncMock(side_effect=Exception("Supabase error")),
        ):
            result = await _check_supabase()

        assert result["status"] == "unhealthy"
        assert "error" in result
