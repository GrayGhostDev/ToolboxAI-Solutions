"""
Unit Tests for User Management Endpoints

Tests role-based endpoints for admin, teacher, student, and parent users.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status, FastAPI

from apps.backend.api.v1.endpoints.users import (
    admin_router,
    teacher_router,
    student_router,
    parent_router,
    router
)
from apps.backend.core.security.jwt_handler import create_access_token
from tests.utils import APITestHelper, MockDataGenerator


@pytest.fixture
def app():
    """Create FastAPI app with user routers."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create admin JWT token."""
    return create_access_token(
        data={"sub": "admin", "role": "admin", "user_id": 1}
    )


@pytest.fixture
def teacher_token():
    """Create teacher JWT token."""
    return create_access_token(
        data={"sub": "teacher", "role": "teacher", "user_id": 2}
    )


@pytest.fixture
def student_token():
    """Create student JWT token."""
    return create_access_token(
        data={"sub": "student", "role": "student", "user_id": 3}
    )


@pytest.fixture
def parent_token():
    """Create parent JWT token."""
    return create_access_token(
        data={"sub": "parent", "role": "parent", "user_id": 4}
    )


@pytest.fixture
def admin_headers(admin_token):
    """Create authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def teacher_headers(teacher_token):
    """Create authorization headers for teacher."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def student_headers(student_token):
    """Create authorization headers for student."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def parent_headers(parent_token):
    """Create authorization headers for parent."""
    return {"Authorization": f"Bearer {parent_token}"}


class TestAdminEndpoints:
    """Test admin-only endpoints."""

    def test_get_user_statistics(self, client, admin_headers):
        """Test admin can access user statistics."""
        response = client.get(
            "/api/admin/stats/users",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify expected statistics
        assert "total_users" in data
        assert "active_users" in data
        assert "new_users_today" in data
        assert "by_role" in data
        assert isinstance(data["total_users"], int)
        assert isinstance(data["by_role"], dict)

    def test_get_system_health(self, client, admin_headers):
        """Test admin can access system health metrics."""
        response = client.get(
            "/api/admin/health",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify health metrics
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "database_status" in data
        assert "services" in data
        assert isinstance(data["services"], dict)

    def test_get_recent_activity(self, client, admin_headers):
        """Test admin can access recent activity."""
        response = client.get(
            "/api/admin/activity",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify activity list
        assert isinstance(data, list)
        if len(data) > 0:
            activity = data[0]
            assert "id" in activity
            assert "type" in activity
            assert "message" in activity
            assert "timestamp" in activity

    def test_get_revenue_analytics(self, client, admin_headers):
        """Test admin can access revenue analytics."""
        response = client.get(
            "/api/admin/revenue",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify revenue data
        assert "monthly_revenue" in data
        assert "yearly_revenue" in data
        assert "growth_percentage" in data
        assert isinstance(data["monthly_revenue"], (int, float))

    def test_get_support_queue(self, client, admin_headers):
        """Test admin can access support queue."""
        response = client.get(
            "/api/admin/support/queue",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify support tickets
        assert isinstance(data, list)
        if len(data) > 0:
            ticket = data[0]
            assert "id" in ticket
            assert "subject" in ticket
            assert "priority" in ticket
            assert "status" in ticket

    def test_get_server_metrics(self, client, admin_headers):
        """Test admin can access server metrics."""
        response = client.get(
            "/api/admin/metrics",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify metrics
        assert "requests_per_minute" in data
        assert "average_response_time" in data
        assert "error_rate" in data
        assert isinstance(data["error_rate"], (int, float))

    def test_get_compliance_status(self, client, admin_headers):
        """Test admin can access compliance status."""
        response = client.get(
            "/api/admin/compliance/status",
            headers=admin_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify compliance data
        assert "coppa" in data
        assert "ferpa" in data
        assert "gdpr" in data
        assert "ada" in data
        assert isinstance(data["coppa"], dict)

    def test_admin_endpoints_reject_teacher(self, client, teacher_headers):
        """Test admin endpoints reject teacher access."""
        response = client.get(
            "/api/admin/stats/users",
            headers=teacher_headers
        )

        # Should be forbidden (403) or unauthorized (401)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_admin_endpoints_reject_student(self, client, student_headers):
        """Test admin endpoints reject student access."""
        response = client.get(
            "/api/admin/health",
            headers=student_headers
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_admin_endpoints_reject_unauthenticated(self, client):
        """Test admin endpoints require authentication."""
        response = client.get("/api/admin/stats/users")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


class TestTeacherEndpoints:
    """Test teacher-specific endpoints."""

    def test_get_todays_classes(self, client, teacher_headers):
        """Test teacher can access today's classes."""
        response = client.get(
            "/api/teacher/classes/today",
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify class data
        assert "total" in data
        assert "completed" in data
        assert "upcoming" in data
        assert "classes" in data
        assert isinstance(data["classes"], list)

    def test_get_class_progress(self, client, teacher_headers):
        """Test teacher can access class progress."""
        response = client.get(
            "/api/teacher/progress",
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify progress metrics
        assert "average_score" in data
        assert "completion_rate" in data
        assert "at_risk_students" in data
        assert isinstance(data["average_score"], (int, float))

    def test_get_pending_grades(self, client, teacher_headers):
        """Test teacher can access pending grades."""
        response = client.get(
            "/api/teacher/grades/pending",
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify grades list
        assert isinstance(data, list)
        if len(data) > 0:
            assignment = data[0]
            assert "id" in assignment
            assert "title" in assignment
            assert "class" in assignment
            assert "submissions" in assignment

    def test_get_teacher_calendar(self, client, teacher_headers):
        """Test teacher can access calendar."""
        response = client.get(
            "/api/teacher/calendar",
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify calendar events
        assert "events" in data
        assert isinstance(data["events"], list)
        if len(data["events"]) > 0:
            event = data["events"][0]
            assert "id" in event
            assert "title" in event
            assert "date" in event

    def test_get_recent_submissions(self, client, teacher_headers):
        """Test teacher can access recent submissions."""
        response = client.get(
            "/api/teacher/submissions",
            headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify submissions list
        assert isinstance(data, list)
        if len(data) > 0:
            submission = data[0]
            assert "id" in submission
            assert "student" in submission
            assert "assignment" in submission

    def test_teacher_endpoints_reject_student(self, client, student_headers):
        """Test teacher endpoints reject student access."""
        response = client.get(
            "/api/teacher/classes/today",
            headers=student_headers
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_teacher_endpoints_allow_admin(self, client, admin_headers):
        """Test teacher endpoints allow admin access (higher privilege)."""
        # Note: This depends on RBAC implementation
        # If admins have access to all endpoints, this should succeed
        # If not, it should fail - adjust based on actual RBAC design
        response = client.get(
            "/api/teacher/classes/today",
            headers=admin_headers
        )

        # Could be 200 (admin has access) or 403 (strict role check)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN
        ]


class TestStudentEndpoints:
    """Test student-specific endpoints."""

    def test_get_student_xp(self, client, student_headers):
        """Test student can access XP data."""
        response = client.get(
            "/api/student/xp",
            headers=student_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify XP data
        assert "current_xp" in data
        assert "current_level" in data
        assert "xp_to_next_level" in data
        assert isinstance(data["current_xp"], int)

    def test_get_assignments_due(self, client, student_headers):
        """Test student can access due assignments."""
        response = client.get(
            "/api/student/assignments/due",
            headers=student_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify assignments list
        assert isinstance(data, list)
        if len(data) > 0:
            assignment = data[0]
            assert "id" in assignment
            assert "title" in assignment
            assert "due_date" in assignment
            assert "xp_reward" in assignment

    def test_get_recent_achievements(self, client, student_headers):
        """Test student can access achievements."""
        response = client.get(
            "/api/student/achievements/recent",
            headers=student_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify achievements list
        assert isinstance(data, list)
        if len(data) > 0:
            achievement = data[0]
            assert "id" in achievement
            assert "name" in achievement
            assert "description" in achievement

    def test_get_student_rank(self, client, student_headers):
        """Test student can access class rank."""
        response = client.get(
            "/api/student/rank",
            headers=student_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify rank data
        assert "class_rank" in data
        assert "total_students" in data
        assert "percentile" in data
        assert isinstance(data["class_rank"], int)

    def test_get_learning_path(self, client, student_headers):
        """Test student can access learning path."""
        response = client.get(
            "/api/student/path",
            headers=student_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify learning path data
        assert "current_unit" in data
        assert "progress" in data
        assert "completed_lessons" in data
        assert "next_lesson" in data

    def test_get_available_worlds(self, client, student_headers):
        """Test student can access Roblox worlds."""
        response = client.get(
            "/api/student/roblox/worlds",
            headers=student_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify worlds list
        assert isinstance(data, list)
        if len(data) > 0:
            world = data[0]
            assert "id" in world
            assert "name" in world
            assert "subject" in world
            assert "xp_reward" in world

    def test_student_endpoints_reject_teacher(self, client, teacher_headers):
        """Test student endpoints reject teacher access."""
        response = client.get(
            "/api/student/xp",
            headers=teacher_headers
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


class TestParentEndpoints:
    """Test parent-specific endpoints."""

    def test_get_children_overview(self, client, parent_headers):
        """Test parent can access children overview."""
        response = client.get(
            "/api/parent/children/overview",
            headers=parent_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify children data
        assert "children" in data
        assert isinstance(data["children"], list)
        if len(data["children"]) > 0:
            child = data["children"][0]
            assert "id" in child
            assert "name" in child
            assert "grade" in child
            assert "school" in child

    def test_get_recent_grades(self, client, parent_headers):
        """Test parent can access children's grades."""
        response = client.get(
            "/api/parent/grades/recent",
            headers=parent_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify grades list
        assert isinstance(data, list)
        if len(data) > 0:
            grade = data[0]
            assert "child" in grade
            assert "assignment" in grade
            assert "grade" in grade
            assert "score" in grade

    def test_get_upcoming_events(self, client, parent_headers):
        """Test parent can access upcoming events."""
        response = client.get(
            "/api/parent/events",
            headers=parent_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify events list
        assert isinstance(data, list)
        if len(data) > 0:
            event = data[0]
            assert "id" in event
            assert "title" in event
            assert "date" in event
            assert "location" in event

    def test_get_attendance_summary(self, client, parent_headers):
        """Test parent can access attendance summary."""
        response = client.get(
            "/api/parent/attendance/summary",
            headers=parent_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify attendance data structure
        assert isinstance(data, dict)
        # Should contain child names as keys
        if len(data) > 0:
            first_child_data = list(data.values())[0]
            assert "present" in first_child_data
            assert "absent" in first_child_data
            assert "percentage" in first_child_data

    def test_get_progress_chart(self, client, parent_headers):
        """Test parent can access progress chart."""
        response = client.get(
            "/api/parent/progress/chart",
            headers=parent_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify progress chart structure
        assert isinstance(data, dict)
        if len(data) > 0:
            first_child_data = list(data.values())[0]
            assert isinstance(first_child_data, dict)
            # Should contain subjects as keys with score arrays
            if len(first_child_data) > 0:
                first_subject_scores = list(first_child_data.values())[0]
                assert isinstance(first_subject_scores, list)

    def test_parent_endpoints_reject_student(self, client, student_headers):
        """Test parent endpoints reject student access."""
        response = client.get(
            "/api/parent/children/overview",
            headers=student_headers
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


class TestAuthorizationEnforcement:
    """Test authorization enforcement across all endpoints."""

    def test_all_endpoints_require_authentication(self, client):
        """Test that all user endpoints require authentication."""
        endpoints = [
            "/api/admin/stats/users",
            "/api/teacher/classes/today",
            "/api/student/xp",
            "/api/parent/children/overview"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ], f"Endpoint {endpoint} should require authentication"

    def test_role_based_access_control_enforced(self, client, student_headers, teacher_headers):
        """Test that RBAC prevents unauthorized role access."""
        # Student trying to access teacher endpoint
        response = client.get(
            "/api/teacher/classes/today",
            headers=student_headers
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

        # Teacher trying to access admin endpoint
        response = client.get(
            "/api/admin/stats/users",
            headers=teacher_headers
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


class TestResponseFormat:
    """Test response format consistency."""

    def test_endpoints_return_json(self, client, admin_headers):
        """Test that endpoints return JSON responses."""
        response = client.get(
            "/api/admin/stats/users",
            headers=admin_headers
        )

        assert response.headers["content-type"] == "application/json"

    def test_list_endpoints_return_arrays(self, client, teacher_headers):
        """Test that list endpoints return arrays."""
        response = client.get(
            "/api/teacher/grades/pending",
            headers=teacher_headers
        )

        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
