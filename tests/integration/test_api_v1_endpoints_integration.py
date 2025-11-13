
"""
Test script for API v1 endpoints

Tests the new analytics, reports, and admin endpoints to ensure they work
correctly with the database and authentication system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_INTEGRATION_TESTS"),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable",
)
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.api.auth.auth import create_user_token

# Import the FastAPI app
from apps.backend.main import app
from database.connection import get_db
from database.models.models import User, UserRole


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def db_session():
    """Create database session for testing"""
    async for session in get_db():
        yield session
        break


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Create admin user for testing"""
    from passlib.context import CryptContext
    from sqlalchemy import select

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # First check if user already exists
    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return existing_user

    admin = User(
        email="admin@test.com",
        username="admin_test",
        password_hash=pwd_context.hash("testpassword123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    return admin


@pytest.fixture
def admin_headers(admin_user):
    """Create authorization headers for admin user"""
    token = create_user_token(admin_user)
    return {"Authorization": f"Bearer {token}"}


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    def test_realtime_analytics_unauthorized(self, client):
        """Test realtime analytics without authentication"""
        response = client.get("/api/v1/analytics/realtime")
        assert response.status_code == 401

    def test_realtime_analytics_authorized(self, client, admin_headers):
        """Test realtime analytics with admin authentication"""
        response = client.get("/api/v1/analytics/realtime", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        # The endpoint returns RealtimeMetrics directly, not wrapped in success
        assert "timestamp" in data
        assert "active_users" in data
        assert "active_sessions" in data
        assert "recent_activities" in data
        assert "system_health" in data

    def test_summary_analytics_authorized(self, client, admin_headers):
        """Test summary analytics with admin authentication"""
        response = client.get("/api/v1/analytics/summary", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "summary_stats" in data
        assert "completion_rates" in data
        assert "popular_content" in data
        assert "growth_metrics" in data
        assert "date_range" in data

    def test_summary_analytics_with_filters(self, client, admin_headers):
        """Test summary analytics with date filters"""
        params = {
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-12-31T23:59:59Z",
            "subject": "Science",
            "grade_level": 7,
        }
        response = client.get("/api/v1/analytics/summary", params=params, headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


class TestReportsEndpoints:
    """Test reports endpoints"""

    def test_generate_report_unauthorized(self, client):
        """Test report generation without authentication"""
        report_data = {"report_type": "user_activity", "format": "csv"}
        response = client.post("/api/v1/reports/generate", json=report_data)
        assert response.status_code == 401

    def test_generate_report_authorized(self, client, admin_headers):
        """Test report generation with admin authentication"""
        report_data = {
            "report_type": "user_activity",
            "format": "csv",
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-12-31T23:59:59Z",
        }
        response = client.post("/api/v1/reports/generate", json=report_data, headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "report_id" in data
        assert data["status"] == "processing"
        assert "estimated_completion" in data

    def test_generate_report_invalid_type(self, client, admin_headers):
        """Test report generation with invalid report type"""
        report_data = {"report_type": "invalid_type", "format": "csv"}
        response = client.post("/api/v1/reports/generate", json=report_data, headers=admin_headers)
        assert response.status_code == 422  # Validation error

    def test_report_status(self, client, admin_headers):
        """Test report status endpoint"""
        report_id = "test-report-id"
        response = client.get(f"/api/v1/reports/status/{report_id}", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["report_id"] == report_id

    def test_download_report(self, client, admin_headers):
        """Test report download endpoint"""
        report_id = "test-report-id"
        response = client.get(f"/api/v1/reports/download/{report_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


class TestAdminUserEndpoints:
    """Test admin user management endpoints"""

    def test_list_users_unauthorized(self, client):
        """Test user listing without authentication"""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_list_users_authorized(self, client, admin_headers):
        """Test user listing with admin authentication"""
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "users" in data
        assert "pagination" in data
        assert "filters_applied" in data

    def test_list_users_with_pagination(self, client, admin_headers):
        """Test user listing with pagination parameters"""
        params = {
            "page": 1,
            "page_size": 10,  # Changed from per_page to page_size
            "search": "admin",
            "role": "admin",
            "sort_by": "created_at",
            "sort_order": "desc",
        }
        response = client.get("/api/v1/admin/users", params=params, headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        # UserListResponse has pagination fields directly, not nested
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert "users" in data
        assert "total" in data

    def test_create_user_authorized(self, client, admin_headers):
        """Test user creation with admin authentication"""
        user_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "TestPassword123!",
            "first_name": "New",
            "last_name": "User",
            "role": "student",
        }
        response = client.post("/api/v1/admin/users", json=user_data, headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["role"] == user_data["role"]

    def test_create_user_invalid_data(self, client, admin_headers):
        """Test user creation with invalid data"""
        user_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "weak",  # Too weak
            "first_name": "",  # Empty
            "last_name": "User",
        }
        response = client.post("/api/v1/admin/users", json=user_data, headers=admin_headers)
        assert response.status_code == 422  # Validation error

    def test_get_user_authorized(self, client, admin_headers, admin_user):
        """Test getting user details with admin authentication"""
        user_id = str(admin_user.id)
        response = client.get(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == admin_user.email
        assert data["username"] == admin_user.username

    def test_get_user_not_found(self, client, admin_headers):
        """Test getting non-existent user"""
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/admin/users/{fake_user_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_update_user_authorized(self, client, admin_headers, admin_user):
        """Test updating user with admin authentication"""
        user_id = str(admin_user.id)
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = client.put(
            f"/api/v1/admin/users/{user_id}", json=update_data, headers=admin_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"

    def test_deactivate_user_not_found(self, client, admin_headers):
        """Test deactivating non-existent user"""
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/admin/users/{fake_user_id}", headers=admin_headers)
        assert response.status_code == 404


def test_endpoint_integration():
    """Test that all endpoints are properly integrated"""
    print("Testing API v1 endpoints integration...")

    with TestClient(app) as client:
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200

        # Test OpenAPI docs
        response = client.get("/docs")
        assert response.status_code == 200

        # Test that our new endpoints appear in OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_data = response.json()
        paths = openapi_data.get("paths", {})

        # Check that our new endpoints are registered
        assert "/api/v1/analytics/realtime" in paths
        assert "/api/v1/analytics/summary" in paths
        assert "/api/v1/reports/generate" in paths
        assert "/api/v1/admin/users" in paths

        print("✅ All API v1 endpoints properly integrated!")


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_database_integration():
    """Test database integration with endpoints"""
    print("Testing database integration...")

    try:
        # Test database connection
        async with get_db() as db:
            # Simple query to test connection
            from sqlalchemy import text

            result = await db.execute(text("SELECT 1"))
            assert result.scalar() == 1

        print("✅ Database connection working!")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


if __name__ == "__main__":
    """Run basic integration tests"""
    print("🚀 Testing API v1 Endpoints...")

    # Test endpoint integration
    test_endpoint_integration()

    # Test database integration
    asyncio.run(test_database_integration())

    print("\n✅ Basic integration tests passed!")
    print("\n📝 To run full test suite:")
    print("   pytest test_api_v1_endpoints.py -v")
    print("\n🔧 Test endpoints manually:")
    print("   1. Start the server: python server/main.py")
    print("   2. Visit: http://localhost:8008/docs")
    print("   3. Test the new /api/v1/* endpoints")
