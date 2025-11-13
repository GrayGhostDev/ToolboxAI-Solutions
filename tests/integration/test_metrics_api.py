"""
Integration Tests for Dashboard Metrics API - 2025 Implementation

Tests all metrics endpoints with:
- Rate limiting validation
- Cache behavior verification
- Authentication checks
- Response schema validation
- Error handling
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from apps.backend.core.app_factory import create_app
from apps.backend.models.schemas import User
from database.models import Base

# ============================================================================
# Test Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    app = create_app()
    return app


@pytest.fixture
async def async_client(test_app):
    """Create async HTTP client for testing."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_current_user():
    """Create mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = "test-user-123"
    user.username = "testuser"
    user.email = "test@example.com"
    user.organization_id = "test-org-123"
    user.tier = "premium"
    user.is_admin = False
    return user


@pytest.fixture
def admin_user(mock_current_user):
    """Create mock admin user."""
    admin = mock_current_user
    admin.is_admin = True
    return admin


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    return {"Authorization": "Bearer test-token-123"}


# ============================================================================
# Test Cases - Dashboard Metrics
# ============================================================================


@pytest.mark.asyncio
class TestDashboardMetricsAPI:
    """Test suite for dashboard metrics endpoints."""

    async def test_get_dashboard_metrics_success(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test successful dashboard metrics retrieval."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get(
                "/api/v1/metrics/dashboard",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert "timestamp" in data
            assert "organization_id" in data
            assert "user_metrics" in data
            assert "content_metrics" in data
            assert "engagement_metrics" in data
            assert "system_metrics" in data
            assert "trends" in data
            assert "cache_metadata" in data

            # Validate user metrics
            user_metrics = data["user_metrics"]
            assert "total_users" in user_metrics
            assert "active_users" in user_metrics
            assert "new_users_today" in user_metrics
            assert "growth_rate" in user_metrics

            # Validate rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

    async def test_get_dashboard_metrics_force_refresh(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test force refresh parameter."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            # First request (cache miss)
            response1 = await async_client.get(
                "/api/v1/metrics/dashboard?force_refresh=false",
                headers=auth_headers,
            )
            assert response1.status_code == 200

            # Second request with force refresh
            response2 = await async_client.get(
                "/api/v1/metrics/dashboard?force_refresh=true",
                headers=auth_headers,
            )
            assert response2.status_code == 200

            # Should have fresh data
            data2 = response2.json()
            assert data2["cache_metadata"]["cache_key"]

    async def test_get_dashboard_metrics_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test unauthorized access returns 401."""
        response = await async_client.get("/api/v1/metrics/dashboard")
        assert response.status_code == 401

    async def test_rate_limit_enforcement(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test rate limiting is enforced."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            # Mock rate limiter to return rate limit exceeded
            mock_rate_limit_result = MagicMock()
            mock_rate_limit_result.allowed = False
            mock_rate_limit_result.limit = 10
            mock_rate_limit_result.remaining = 0
            mock_rate_limit_result.retry_after = 60
            mock_rate_limit_result.headers = {
                "X-RateLimit-Limit": "10",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(datetime.now(timezone.utc).timestamp() + 60)),
                "Retry-After": "60",
            }

            with patch(
                "apps.backend.core.rate_limiter.RateLimiter.check_rate_limit",
                return_value=mock_rate_limit_result,
            ):
                response = await async_client.get(
                    "/api/v1/metrics/dashboard",
                    headers=auth_headers,
                )

                assert response.status_code == 429
                assert "X-RateLimit-Limit" in response.headers
                assert "Retry-After" in response.headers

                data = response.json()
                assert "error" in data["detail"]
                assert data["detail"]["retry_after"] == 60


# ============================================================================
# Test Cases - Activity Metrics
# ============================================================================


@pytest.mark.asyncio
class TestActivityMetricsAPI:
    """Test suite for activity metrics endpoints."""

    async def test_get_activity_metrics_success(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test successful activity metrics retrieval."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get(
                "/api/v1/metrics/activity",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert "recent_lessons" in data
            assert "recent_assessments" in data
            assert "recent_messages" in data
            assert "top_performing_content" in data
            assert "activity_trend" in data

            # Validate types
            assert isinstance(data["recent_lessons"], int)
            assert isinstance(data["recent_assessments"], int)
            assert isinstance(data["recent_messages"], int)
            assert isinstance(data["top_performing_content"], list)
            assert isinstance(data["activity_trend"], list)


# ============================================================================
# Test Cases - Statistics
# ============================================================================


@pytest.mark.asyncio
class TestStatisticsAPI:
    """Test suite for statistics endpoints."""

    async def test_get_statistics_valid_period(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test statistics with valid period."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            for period in ["24h", "7d", "30d", "90d"]:
                response = await async_client.get(
                    f"/api/v1/metrics/statistics?period={period}",
                    headers=auth_headers,
                )

                assert response.status_code == 200
                data = response.json()
                assert data["period"] == period
                assert "statistics" in data
                assert "generated_at" in data

    async def test_get_statistics_invalid_period(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test statistics with invalid period."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.get(
                "/api/v1/metrics/statistics?period=invalid",
                headers=auth_headers,
            )

            assert response.status_code == 400
            data = response.json()
            assert "Invalid period" in data["detail"]


# ============================================================================
# Test Cases - Export
# ============================================================================


@pytest.mark.asyncio
class TestMetricsExportAPI:
    """Test suite for metrics export endpoints."""

    async def test_export_metrics_json(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test metrics export in JSON format."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            export_request = {
                "format": "json",
                "date_range": "7d",
                "metric_types": ["users", "content", "engagement"],
            }

            response = await async_client.post(
                "/api/v1/metrics/export",
                headers=auth_headers,
                json=export_request,
            )

            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert "expires_at" in data
            assert "file_size" in data
            assert data["format"] == "json"

    async def test_export_metrics_invalid_format(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test export with invalid format."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            export_request = {
                "format": "invalid",
                "date_range": "7d",
                "metric_types": ["users"],
            }

            response = await async_client.post(
                "/api/v1/metrics/export",
                headers=auth_headers,
                json=export_request,
            )

            assert response.status_code == 400
            data = response.json()
            assert "Invalid format" in data["detail"]


# ============================================================================
# Test Cases - Cache Invalidation
# ============================================================================


@pytest.mark.asyncio
class TestCacheInvalidationAPI:
    """Test suite for cache invalidation endpoints."""

    async def test_invalidate_cache_as_admin(
        self,
        async_client: AsyncClient,
        admin_user: User,
        auth_headers: dict[str, str],
    ):
        """Test cache invalidation by admin."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=admin_user,
        ):
            response = await async_client.post(
                "/api/v1/metrics/invalidate-cache",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Metrics cache invalidated" in data["message"]

    async def test_invalidate_cache_as_non_admin(
        self,
        async_client: AsyncClient,
        mock_current_user: User,
        auth_headers: dict[str, str],
    ):
        """Test cache invalidation by non-admin (should fail)."""
        with patch(
            "apps.backend.api.v1.endpoints.metrics.get_current_user",
            return_value=mock_current_user,
        ):
            response = await async_client.post(
                "/api/v1/metrics/invalidate-cache",
                headers=auth_headers,
            )

            assert response.status_code == 403
            data = response.json()
            assert "Admin access required" in data["detail"]


# ============================================================================
# Test Markers
# ============================================================================


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
]
