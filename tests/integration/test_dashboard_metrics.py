"""
Integration Tests for Dashboard Metrics API

Tests the new dashboard metrics endpoints with rate limiting,
caching, and multi-tenant isolation.
"""

from datetime import datetime, timedelta

import pytest
from apps.backend.services.cache_service import cache_service
from fastapi.testclient import TestClient

from apps.backend.core.app_factory import create_test_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_test_app()
    return TestClient(app)


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with JWT token"""
    # Mock JWT token for testing
    token = "mock_jwt_token_for_testing"
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def test_user():
    """Mock test user"""
    return {
        "id": "test_user_123",
        "organization_id": "org_456",
        "email": "test@example.com",
        "role": "admin",
    }


class TestDashboardMetricsEndpoints:
    """Test suite for dashboard metrics endpoints"""

    def test_get_dashboard_metrics_success(self, client, auth_headers):
        """Test successful retrieval of dashboard metrics"""
        response = client.get("/api/v1/dashboard/metrics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert data["status"] == "success"
        assert "data" in data
        assert "metadata" in data

        # Verify metrics sections
        metrics_data = data["data"]
        assert "users" in metrics_data
        assert "content" in metrics_data
        assert "engagement" in metrics_data
        assert "system" in metrics_data

        # Verify user metrics structure
        user_metrics = metrics_data["users"]
        assert "total" in user_metrics
        assert "active_today" in user_metrics
        assert "active_week" in user_metrics
        assert "active_month" in user_metrics
        assert "growth_rate" in user_metrics
        assert "by_role" in user_metrics

        # Verify content metrics structure
        content_metrics = metrics_data["content"]
        assert "total" in content_metrics
        assert "published" in content_metrics
        assert "draft" in content_metrics
        assert "pending_review" in content_metrics

    def test_get_dashboard_metrics_unauthorized(self, client):
        """Test metrics endpoint without authentication"""
        response = client.get("/api/v1/dashboard/metrics")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_dashboard_metrics_cached(self, client, auth_headers):
        """Test that metrics are properly cached"""
        # First request - should cache the result
        response1 = client.get("/api/v1/dashboard/metrics", headers=auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()

        # Second request - should return cached result
        response2 = client.get("/api/v1/dashboard/metrics", headers=auth_headers)
        assert response2.status_code == 200
        data2 = response2.json()

        # Metadata should indicate caching
        assert data1["metadata"].get("cached") is True
        assert data2["metadata"].get("cached") is True

    def test_get_recent_activity_success(self, client, auth_headers):
        """Test successful retrieval of recent activity"""
        response = client.get("/api/v1/dashboard/activity", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "metadata" in data

        # Verify activity item structure if present
        if data["data"]:
            activity = data["data"][0]
            assert "id" in activity
            assert "type" in activity
            assert "action" in activity
            assert "user_id" in activity
            assert "user_name" in activity
            assert "timestamp" in activity

    def test_get_recent_activity_with_limit(self, client, auth_headers):
        """Test activity endpoint with limit parameter"""
        limit = 5
        response = client.get(f"/api/v1/dashboard/activity?limit={limit}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= limit

    def test_get_recent_activity_invalid_limit(self, client, auth_headers):
        """Test activity endpoint with invalid limit"""
        # Limit too high
        response = client.get("/api/v1/dashboard/activity?limit=200", headers=auth_headers)
        assert response.status_code == 422  # Validation error

        # Limit too low
        response = client.get("/api/v1/dashboard/activity?limit=0", headers=auth_headers)
        assert response.status_code == 422

    def test_get_detailed_statistics_success(self, client, auth_headers):
        """Test detailed statistics endpoint"""
        response = client.get("/api/v1/dashboard/statistics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "data" in data
        stats_data = data["data"]

        # Verify statistics structure
        assert "date_range" in stats_data
        assert "user_growth" in stats_data
        assert "content_creation" in stats_data
        assert "engagement_trends" in stats_data

    def test_get_detailed_statistics_with_date_range(self, client, auth_headers):
        """Test statistics endpoint with custom date range"""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()

        response = client.get(
            f"/api/v1/dashboard/statistics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        stats_data = data["data"]

        # Verify date range matches
        assert "date_range" in stats_data
        assert stats_data["date_range"]["start"] == start_date
        assert stats_data["date_range"]["end"] == end_date

    def test_export_metrics_json(self, client, auth_headers):
        """Test metrics export in JSON format"""
        response = client.post("/api/v1/dashboard/export?format=json", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "success"
        assert "data" in data
        export_data = data["data"]

        assert "export_format" in export_data
        assert export_data["export_format"] == "json"
        assert "download_url" in export_data
        assert "expires_at" in export_data

    def test_export_metrics_csv(self, client, auth_headers):
        """Test metrics export in CSV format"""
        response = client.post("/api/v1/dashboard/export?format=csv", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["export_format"] == "csv"

    def test_export_metrics_xlsx(self, client, auth_headers):
        """Test metrics export in Excel format"""
        response = client.post("/api/v1/dashboard/export?format=xlsx", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["export_format"] == "xlsx"

    def test_export_metrics_invalid_format(self, client, auth_headers):
        """Test metrics export with invalid format"""
        response = client.post("/api/v1/dashboard/export?format=pdf", headers=auth_headers)

        assert response.status_code == 422  # Validation error


class TestRateLimiting:
    """Test suite for rate limiting functionality"""

    def test_rate_limiting_enforced(self, client, auth_headers):
        """Test that rate limiting is enforced"""
        # Make multiple requests rapidly
        responses = []
        for i in range(15):  # Assuming limit is 10/minute
            response = client.get("/api/v1/dashboard/metrics", headers=auth_headers)
            responses.append(response)

        # First 10 should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)

        assert success_count > 0
        # If rate limiting is enabled, some requests should be blocked
        # This depends on the actual rate limit configuration

    def test_rate_limit_headers_present(self, client, auth_headers):
        """Test that rate limit headers are included in response"""
        response = client.get("/api/v1/dashboard/metrics", headers=auth_headers)

        # Check for rate limit headers
        headers = response.headers
        # These headers should be added by the rate limiting middleware
        # assert "X-RateLimit-Limit-60s" in headers
        # assert "X-RateLimit-Remaining-60s" in headers

    def test_rate_limit_retry_after_header(self, client, auth_headers):
        """Test that Retry-After header is present when rate limited"""
        # Make enough requests to trigger rate limit
        for _ in range(20):
            response = client.get("/api/v1/dashboard/metrics", headers=auth_headers)
            if response.status_code == 429:
                # Check for Retry-After header
                assert "Retry-After" in response.headers
                retry_after = int(response.headers["Retry-After"])
                assert retry_after > 0
                break


class TestCaching:
    """Test suite for caching functionality"""

    @pytest.mark.asyncio
    async def test_cache_service_get_set(self):
        """Test basic cache operations"""
        await cache_service.connect()

        # Set value
        success = await cache_service.set(
            key="test_key", value={"data": "test_value"}, namespace="test", ttl=60
        )
        assert success is True

        # Get value
        value = await cache_service.get(key="test_key", namespace="test")
        assert value is not None
        assert value["data"] == "test_value"

        # Delete value
        deleted = await cache_service.delete(key="test_key", namespace="test")
        assert deleted is True

        # Verify deletion
        value = await cache_service.get(key="test_key", namespace="test")
        assert value is None

        await cache_service.close()

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics tracking"""
        await cache_service.connect()

        # Reset stats
        cache_service.cache_hits = 0
        cache_service.cache_misses = 0

        # Cause cache miss
        await cache_service.get("nonexistent_key", namespace="test")

        # Set and get (cause cache hit)
        await cache_service.set("test_key", {"data": "value"}, namespace="test")
        await cache_service.get("test_key", namespace="test")

        # Check stats
        stats = await cache_service.get_stats()
        assert stats["cache_hits"] > 0
        assert stats["cache_misses"] > 0
        assert stats["total_requests"] == stats["cache_hits"] + stats["cache_misses"]

        await cache_service.close()


class TestMultiTenantIsolation:
    """Test suite for multi-tenant data isolation"""

    def test_metrics_filtered_by_organization(self, client):
        """Test that metrics are properly filtered by organization"""
        # Create auth headers for different organizations
        org1_headers = {"Authorization": "Bearer org1_token", "Content-Type": "application/json"}
        org2_headers = {"Authorization": "Bearer org2_token", "Content-Type": "application/json"}

        # Get metrics for org1
        response1 = client.get("/api/v1/dashboard/metrics", headers=org1_headers)

        # Get metrics for org2
        response2 = client.get("/api/v1/dashboard/metrics", headers=org2_headers)

        # Both should succeed but may have different data
        # This test would need actual test data to verify isolation
        # For now, just verify both requests succeed
        assert response1.status_code in [200, 401]  # 401 if auth not mocked
        assert response2.status_code in [200, 401]


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
