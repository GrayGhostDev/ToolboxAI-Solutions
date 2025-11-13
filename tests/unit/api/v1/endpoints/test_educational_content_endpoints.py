"""
Unit Tests for Educational Content Endpoints

Tests CRUD operations, content generation, analytics, and publishing functionality.
"""

from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from apps.backend.api.v1.endpoints.educational_content import (
    _mock_analytics_db,
    _mock_content_db,
    router,
)
from apps.backend.core.security.jwt_handler import create_access_token
from tests.utils import APITestHelper


@pytest.fixture(autouse=True)
def clear_mock_data():
    """Clear mock databases before each test."""
    _mock_content_db.clear()
    _mock_analytics_db.clear()
    yield
    _mock_content_db.clear()
    _mock_analytics_db.clear()


@pytest.fixture
def app():
    """Create FastAPI app with content router."""
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
        data={"sub": "admin", "role": "admin", "user_id": 1, "id": "admin-1"}
    )


@pytest.fixture
def teacher_token():
    """Create teacher JWT token."""
    return create_access_token(
        data={"sub": "teacher", "role": "teacher", "user_id": 2, "id": "teacher-1"}
    )


@pytest.fixture
def student_token():
    """Create student JWT token."""
    return create_access_token(
        data={"sub": "student", "role": "student", "user_id": 3, "id": "student-1"}
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
def sample_content_request():
    """Sample content creation request."""
    return {
        "title": "Introduction to Algebra",
        "description": "Basic algebraic concepts for 7th grade students",
        "content_type": "lesson",
        "subject_area": "mathematics",
        "grade_level": 7,
        "difficulty_level": "beginner",
        "learning_objectives": [
            {
                "description": "Understand basic algebraic expressions",
                "bloom_level": "understand",
                "assessment_criteria": "Can identify variables and constants",
            }
        ],
        "curriculum_standards": [
            {
                "standard_id": "CCSS.MATH.7.EE.A.1",
                "description": "Apply properties of operations",
                "grade_level": 7,
                "subject_area": "mathematics",
            }
        ],
        "content_data": {
            "sections": ["Introduction", "Examples", "Practice"],
            "materials": ["Worksheet", "Video"],
        },
        "metadata": {
            "estimated_duration": 45,
            "prerequisites": [],
            "tags": ["algebra", "math", "7th-grade"],
            "language": "en",
            "accessibility_features": [],
        },
    }


class TestCreateContentEndpoint:
    """Test POST /educational-content/create endpoint."""

    def test_create_content_with_valid_data(self, client, teacher_headers, sample_content_request):
        """Test creating content with valid request."""
        response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_201_CREATED
        )

        # Verify response structure
        assert "id" in data
        assert data["title"] == sample_content_request["title"]
        assert data["content_type"] == sample_content_request["content_type"]
        assert data["status"] == "draft"
        assert data["created_by"] == "teacher-1"

    def test_create_content_requires_authentication(self, client, sample_content_request):
        """Test create content requires authentication."""
        response = client.post("/educational-content/create", json=sample_content_request)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_create_content_requires_teacher_or_admin(
        self, client, student_headers, sample_content_request
    ):
        """Test students cannot create content."""
        response = client.post(
            "/educational-content/create", json=sample_content_request, headers=student_headers
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_create_quiz_validates_content_data(self, client, teacher_headers):
        """Test quiz content validation requires questions and scoring."""
        request_data = {
            "title": "Math Quiz",
            "description": "A short math quiz",
            "content_type": "quiz",
            "subject_area": "mathematics",
            "grade_level": 7,
            "difficulty_level": "beginner",
            "learning_objectives": [{"description": "Test math skills", "bloom_level": "apply"}],
            "content_data": {
                # Missing required "questions" and "scoring" fields
                "time_limit": 30
            },
            "metadata": {"estimated_duration": 30, "tags": ["quiz"], "language": "en"},
        }

        response = client.post(
            "/educational-content/create", json=request_data, headers=teacher_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_lesson_validates_content_data(self, client, teacher_headers):
        """Test lesson content validation requires sections and materials."""
        request_data = {
            "title": "Science Lesson",
            "description": "A science lesson",
            "content_type": "lesson",
            "subject_area": "science",
            "grade_level": 7,
            "difficulty_level": "intermediate",
            "learning_objectives": [
                {"description": "Understand scientific method", "bloom_level": "understand"}
            ],
            "content_data": {
                # Missing required "sections" and "materials" fields
                "duration": 45
            },
            "metadata": {"estimated_duration": 45, "tags": ["science"], "language": "en"},
        }

        response = client.post(
            "/educational-content/create", json=request_data, headers=teacher_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_content_validates_title_length(
        self, client, teacher_headers, sample_content_request
    ):
        """Test title validation."""
        # Title too short
        sample_content_request["title"] = "AB"

        response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_content_validates_grade_level(
        self, client, teacher_headers, sample_content_request
    ):
        """Test grade level validation."""
        # Invalid grade level
        sample_content_request["grade_level"] = 15  # Must be 1-12

        response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListContentEndpoint:
    """Test GET /educational-content/list endpoint."""

    def test_list_content_returns_empty_list(self, client, teacher_headers):
        """Test listing content with no content created."""
        response = client.get("/educational-content/list", headers=teacher_headers)

        data = APITestHelper.assert_success_response(response)

        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_list_content_with_pagination(self, client, teacher_headers):
        """Test content listing with pagination."""
        response = client.get(
            "/educational-content/list?page=1&page_size=10", headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert "has_previous" in data
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_content_filters_by_subject(self, client, teacher_headers):
        """Test filtering content by subject area."""
        response = client.get(
            "/educational-content/list?subject_area=mathematics", headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        assert "filters_applied" in data
        assert data["filters_applied"]["subject_area"] == "mathematics"

    def test_list_content_filters_by_grade_level(self, client, teacher_headers):
        """Test filtering content by grade level."""
        response = client.get("/educational-content/list?grade_level=7", headers=teacher_headers)

        data = APITestHelper.assert_success_response(response)

        assert data["filters_applied"]["grade_level"] == 7

    def test_list_content_filters_by_content_type(self, client, teacher_headers):
        """Test filtering content by type."""
        response = client.get(
            "/educational-content/list?content_type=quiz", headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        assert data["filters_applied"]["content_type"] == "quiz"

    def test_list_content_supports_search(self, client, teacher_headers):
        """Test content search functionality."""
        response = client.get("/educational-content/list?search=algebra", headers=teacher_headers)

        data = APITestHelper.assert_success_response(response)

        assert data["filters_applied"]["search"] == "algebra"

    def test_students_only_see_published_content(
        self, client, teacher_headers, student_headers, sample_content_request
    ):
        """Test students can only see published content."""
        # Create draft content as teacher
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        assert create_response.status_code == status.HTTP_201_CREATED

        # Student list should be empty (draft content not visible)
        response = client.get("/educational-content/list", headers=student_headers)

        data = response.json()
        assert len(data["items"]) == 0


class TestGetContentEndpoint:
    """Test GET /educational-content/{content_id} endpoint."""

    def test_get_content_by_id(self, client, teacher_headers, sample_content_request):
        """Test retrieving specific content by ID."""
        # Create content first
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Get content
        response = client.get(f"/educational-content/{content_id}", headers=teacher_headers)

        data = APITestHelper.assert_success_response(response)

        assert data["id"] == content_id
        assert data["title"] == sample_content_request["title"]

    def test_get_nonexistent_content_returns_404(self, client, teacher_headers):
        """Test getting non-existent content returns 404."""
        response = client.get(f"/educational-content/{uuid4()}", headers=teacher_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_students_cannot_access_draft_content(
        self, client, teacher_headers, student_headers, sample_content_request
    ):
        """Test students cannot access draft content."""
        # Create draft content
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Student tries to access
        response = client.get(f"/educational-content/{content_id}", headers=student_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateContentEndpoint:
    """Test PUT /educational-content/{content_id} endpoint."""

    def test_update_content_with_valid_data(self, client, teacher_headers, sample_content_request):
        """Test updating content with valid data."""
        # Create content first
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Update content
        update_data = {
            "title": "Updated Title",
            "description": "Updated description for the content",
        }

        response = client.put(
            f"/educational-content/{content_id}", json=update_data, headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description for the content"

    def test_update_nonexistent_content_returns_404(self, client, teacher_headers):
        """Test updating non-existent content returns 404."""
        response = client.put(
            f"/educational-content/{uuid4()}", json={"title": "New Title"}, headers=teacher_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_teachers_can_only_update_own_content(
        self, client, teacher_headers, admin_headers, sample_content_request
    ):
        """Test teachers can only update their own content."""
        # Admin creates content
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=admin_headers
        )

        content_id = create_response.json()["id"]

        # Teacher tries to update admin's content
        response = client.put(
            f"/educational-content/{content_id}",
            json={"title": "Unauthorized Update"},
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_students_cannot_update_content(
        self, client, teacher_headers, student_headers, sample_content_request
    ):
        """Test students cannot update content."""
        # Create content as teacher
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Student tries to update
        response = client.put(
            f"/educational-content/{content_id}",
            json={"title": "Student Update"},
            headers=student_headers,
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestDeleteContentEndpoint:
    """Test DELETE /educational-content/{content_id} endpoint."""

    def test_delete_content(self, client, teacher_headers, sample_content_request):
        """Test deleting content."""
        # Create content first
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Delete content
        response = client.delete(f"/educational-content/{content_id}", headers=teacher_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify content is deleted
        get_response = client.get(f"/educational-content/{content_id}", headers=teacher_headers)

        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_content_returns_404(self, client, teacher_headers):
        """Test deleting non-existent content returns 404."""
        response = client.delete(f"/educational-content/{uuid4()}", headers=teacher_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_teachers_can_only_delete_own_content(
        self, client, teacher_headers, admin_headers, sample_content_request
    ):
        """Test teachers can only delete their own content."""
        # Admin creates content
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=admin_headers
        )

        content_id = create_response.json()["id"]

        # Teacher tries to delete admin's content
        response = client.delete(f"/educational-content/{content_id}", headers=teacher_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGenerateContentEndpoint:
    """Test POST /educational-content/generate endpoint."""

    def test_generate_content_request(self, client, teacher_headers):
        """Test AI content generation request."""
        request_data = {
            "subject_area": "mathematics",
            "grade_level": 7,
            "topic": "Linear Equations",
            "content_type": "lesson",
            "difficulty_level": "intermediate",
            "learning_objectives": ["Solve linear equations", "Graph linear functions"],
            "curriculum_standards": ["CCSS.MATH.7.EE.B.4"],
            "target_duration": 45,
        }

        response = client.post(
            "/educational-content/generate", json=request_data, headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_202_ACCEPTED
        )

        assert "generation_id" in data
        assert data["status"] == "processing"
        assert "estimated_completion_time" in data

    def test_generate_content_requires_teacher_or_admin(self, client, student_headers):
        """Test students cannot generate content."""
        request_data = {
            "subject_area": "mathematics",
            "grade_level": 7,
            "topic": "Algebra",
            "content_type": "lesson",
            "difficulty_level": "beginner",
            "learning_objectives": ["Learn algebra"],
        }

        response = client.post(
            "/educational-content/generate", json=request_data, headers=student_headers
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestContentAnalyticsEndpoint:
    """Test GET /educational-content/{content_id}/analytics endpoint."""

    def test_get_content_analytics(self, client, teacher_headers, sample_content_request):
        """Test retrieving content analytics."""
        # Create content first
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Get analytics
        response = client.get(
            f"/educational-content/{content_id}/analytics", headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        # Verify analytics structure
        assert "content_id" in data
        assert "total_views" in data
        assert "unique_users" in data
        assert "completion_rate" in data
        assert "average_time_spent" in data

    def test_analytics_requires_teacher_or_admin(
        self, client, teacher_headers, student_headers, sample_content_request
    ):
        """Test students cannot access analytics."""
        # Create content
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Student tries to get analytics
        response = client.get(
            f"/educational-content/{content_id}/analytics", headers=student_headers
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestPublishContentEndpoint:
    """Test POST /educational-content/{content_id}/publish endpoint."""

    def test_publish_content(self, client, teacher_headers, sample_content_request):
        """Test publishing content."""
        # Create content first
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=teacher_headers
        )

        content_id = create_response.json()["id"]

        # Publish content
        response = client.post(
            f"/educational-content/{content_id}/publish", headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        assert data["status"] == "published"

    def test_teachers_can_only_publish_own_content(
        self, client, teacher_headers, admin_headers, sample_content_request
    ):
        """Test teachers can only publish their own content."""
        # Admin creates content
        create_response = client.post(
            "/educational-content/create", json=sample_content_request, headers=admin_headers
        )

        content_id = create_response.json()["id"]

        # Teacher tries to publish admin's content
        response = client.post(
            f"/educational-content/{content_id}/publish", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSearchCurriculumStandards:
    """Test GET /educational-content/standards/search endpoint."""

    def test_search_curriculum_standards(self, client, teacher_headers):
        """Test searching curriculum standards."""
        response = client.get(
            "/educational-content/standards/search?query=math", headers=teacher_headers
        )

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)

    def test_search_standards_with_filters(self, client, teacher_headers):
        """Test searching standards with subject and grade filters."""
        response = client.get(
            "/educational-content/standards/search?query=math&subject_area=mathematics&grade_level=5",
            headers=teacher_headers,
        )

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)

    def test_search_standards_validates_query_length(self, client, teacher_headers):
        """Test search requires minimum query length."""
        response = client.get(
            "/educational-content/standards/search?query=a", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
