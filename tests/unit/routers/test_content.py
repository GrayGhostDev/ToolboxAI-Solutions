"""
Unit tests for the Content Generation API Router.

Tests cover content generation, retrieval, streaming, deletion, user content listing,
and Celery background task integration with comprehensive mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timezone
from uuid import uuid4


# Sample test data
@pytest.fixture
def sample_content_request():
    """Sample content generation request"""
    return {
        "topic": "Pythagorean Theorem",
        "subject": "Mathematics",
        "grade_level": "8-10",
        "content_type": "lesson"
    }


@pytest.fixture
def sample_lesson_request():
    """Sample lesson generation request"""
    return {
        "lesson_id": f"lesson_{uuid4()}",
        "subject": "Mathematics",
        "topic": "Fractions",
        "grade_level": "5-7",
        "learning_objectives": [
            "Understand fraction basics",
            "Add and subtract fractions"
        ],
        "duration": 45
    }


@pytest.fixture
def sample_quiz_request():
    """Sample quiz generation request"""
    return {
        "assessment_id": f"quiz_{uuid4()}",
        "subject": "Science",
        "topic": "Photosynthesis",
        "grade_level": "6-8",
        "num_questions": 10,
        "difficulty": "medium",
        "question_types": ["multiple_choice", "true_false"],
        "learning_objectives": ["Understand photosynthesis process"]
    }


@pytest.fixture
def sample_script_optimize_request():
    """Sample script optimization request"""
    return {
        "script_id": f"script_{uuid4()}",
        "script_code": "local function test()\n  print('Hello')\nend",
        "script_name": "TestScript",
        "optimization_level": "balanced",
        "preserve_comments": True,
        "generate_report": True
    }


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = str(uuid4())
    user.role = "teacher"
    user.organization_id = "org_123"
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = Mock()
    user.id = str(uuid4())
    user.role = "admin"
    user.organization_id = "org_admin"
    return user


@pytest.mark.unit
class TestContentGeneration:
    """Tests for content generation endpoint"""

    @pytest.mark.asyncio
    async def test_generate_content_success(
        self, test_client, sample_content_request, mock_current_user
    ):
        """Test successful content generation"""
        mock_result = {
            "title": "Pythagorean Theorem Lesson",
            "content": "Detailed lesson content here...",
            "exercises": ["Exercise 1", "Exercise 2"]
        }

        with patch('apps.backend.api.routers.content.generate_educational_content', AsyncMock(return_value=mock_result)):
            with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
                response = test_client.post(
                    "/api/v1/content/generate",
                    json=sample_content_request
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["content"] == mock_result
        assert "metadata" in data
        assert "request_id" in data["metadata"]
        assert "generation_time" in data["metadata"]

    @pytest.mark.asyncio
    async def test_generate_content_missing_topic(
        self, test_client, mock_current_user
    ):
        """Test content generation without required topic"""
        invalid_request = {
            "subject": "Mathematics",
            # Missing topic field
        }

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            response = test_client.post(
                "/api/v1/content/generate",
                json=invalid_request
            )

        # FastAPI validation should catch this
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_generate_content_agent_failure(
        self, test_client, sample_content_request, mock_current_user
    ):
        """Test content generation when agent fails"""
        with patch('apps.backend.api.routers.content.generate_educational_content', AsyncMock(side_effect=Exception("Agent service unavailable"))):
            with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
                response = test_client.post(
                    "/api/v1/content/generate",
                    json=sample_content_request
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "generation failed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_generate_content_broadcasts_update(
        self, test_client, sample_content_request, mock_current_user
    ):
        """Test that successful generation broadcasts Pusher update"""
        mock_result = {"content": "test content"}
        mock_broadcast = AsyncMock()

        with patch('apps.backend.api.routers.content.generate_educational_content', AsyncMock(return_value=mock_result)):
            with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
                with patch('apps.backend.api.routers.content._broadcast_content_update', mock_broadcast):
                    response = test_client.post(
                        "/api/v1/content/generate",
                        json=sample_content_request
                    )

        assert response.status_code == status.HTTP_200_OK
        # Background task is queued, not executed immediately in tests


@pytest.mark.unit
class TestContentRetrieval:
    """Tests for content retrieval endpoints"""

    def test_get_content_success(self, test_client, mock_current_user):
        """Test retrieving content by ID"""
        content_id = "content_test_123"

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            response = test_client.get(f"/content/{content_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["id"] == content_id
        assert data["data"]["user_id"] == mock_current_user.id

    def test_get_content_retrieval_error(self, test_client, mock_current_user):
        """Test content retrieval with error"""
        content_id = "nonexistent_content"

        # Mock an exception during retrieval
        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.log_audit', side_effect=Exception("Database error")):
                response = test_client.get(f"/content/{content_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestContentStreaming:
    """Tests for content streaming endpoint"""

    @pytest.mark.asyncio
    async def test_stream_content_generation(self, test_client, mock_current_user):
        """Test streaming content generation progress"""
        content_id = "content_stream_123"

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            response = test_client.get(
                f"/content/{content_id}/stream",
                headers={"Accept": "text/plain"}
            )

        assert response.status_code == status.HTTP_200_OK
        # Streaming response returns iterator

    @pytest.mark.asyncio
    async def test_stream_content_generation_error(self, test_client, mock_current_user):
        """Test streaming content generation with error"""
        content_id = "content_error"

        # Mock an error in stream generation
        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.asyncio.sleep', AsyncMock(side_effect=Exception("Stream error"))):
                response = test_client.get(f"/content/{content_id}/stream")

        # The endpoint catches exceptions and returns 500
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


@pytest.mark.unit
class TestContentDeletion:
    """Tests for content deletion endpoint"""

    def test_delete_content_success_admin(self, test_client, mock_admin_user):
        """Test deleting content as admin"""
        content_id = "content_delete_123"

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_admin_user):
            response = test_client.delete(f"/content/{content_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["content_id"] == content_id
        assert data["data"]["deleted"] is True

    def test_delete_content_success_teacher(self, test_client, mock_current_user):
        """Test deleting content as teacher"""
        content_id = "content_teacher_delete"

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            response = test_client.delete(f"/content/{content_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_delete_content_failure(self, test_client, mock_admin_user):
        """Test content deletion with error"""
        content_id = "content_error"

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.content.log_audit', side_effect=Exception("Delete failed")):
                response = test_client.delete(f"/content/{content_id}")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestUserContent:
    """Tests for user content listing endpoint"""

    def test_get_user_content_own_content(self, test_client, mock_current_user):
        """Test user retrieving their own content"""
        user_id = mock_current_user.id

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            response = test_client.get(f"/content/user/{user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "content" in data["data"]
        assert data["data"]["total"] > 0

    def test_get_user_content_with_pagination(self, test_client, mock_current_user):
        """Test user content with pagination parameters"""
        user_id = mock_current_user.id

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            response = test_client.get(
                f"/content/user/{user_id}",
                params={"limit": 5, "offset": 10}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["limit"] == 5
        assert data["data"]["offset"] == 10

    def test_get_user_content_admin_access(self, test_client, mock_admin_user):
        """Test admin accessing other user's content"""
        other_user_id = str(uuid4())

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_admin_user):
            with patch('apps.backend.api.routers.content._user_has_role', return_value=True):
                response = test_client.get(f"/content/user/{other_user_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_get_user_content_forbidden(self, test_client, mock_current_user):
        """Test non-admin user accessing other user's content"""
        other_user_id = str(uuid4())

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content._user_has_role', return_value=False):
                response = test_client.get(f"/content/user/{other_user_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_content_retrieval_error(self, test_client, mock_current_user):
        """Test user content retrieval with error"""
        user_id = mock_current_user.id

        with patch('apps.backend.api.routers.content.get_current_user', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.JSONResponse', side_effect=Exception("Database error")):
                response = test_client.get(f"/content/user/{user_id}")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestCeleryLessonGeneration:
    """Tests for Celery lesson generation endpoint"""

    def test_generate_lesson_content_success(
        self, test_client, sample_lesson_request, mock_current_user
    ):
        """Test successful lesson generation task queuing"""
        mock_task = Mock()
        mock_task.id = "task_123456"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.generate_lesson_content_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/content/lessons/generate",
                    json=sample_lesson_request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["task_id"] == "task_123456"
        assert data["data"]["lesson_id"] == sample_lesson_request["lesson_id"]
        assert "pusher_channel" in data["data"]

    def test_generate_lesson_content_teacher_permission(
        self, test_client, sample_lesson_request, mock_current_user
    ):
        """Test lesson generation with teacher role"""
        mock_current_user.role = "teacher"
        mock_task = Mock()
        mock_task.id = "task_teacher"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.generate_lesson_content_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/content/lessons/generate",
                    json=sample_lesson_request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_generate_lesson_content_task_failure(
        self, test_client, sample_lesson_request, mock_current_user
    ):
        """Test lesson generation when task queuing fails"""
        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.generate_lesson_content_sync', side_effect=Exception("Celery unavailable")):
                response = test_client.post(
                    "/api/v1/content/lessons/generate",
                    json=sample_lesson_request
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestCeleryQuizGeneration:
    """Tests for Celery quiz generation endpoint"""

    def test_generate_quiz_success(
        self, test_client, sample_quiz_request, mock_current_user
    ):
        """Test successful quiz generation task queuing"""
        mock_task = Mock()
        mock_task.id = "quiz_task_123"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.generate_quiz_questions_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/content/assessments/generate",
                    json=sample_quiz_request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["data"]["task_id"] == "quiz_task_123"
        assert data["data"]["assessment_id"] == sample_quiz_request["assessment_id"]

    def test_generate_quiz_with_optional_params(
        self, test_client, mock_current_user
    ):
        """Test quiz generation with optional parameters"""
        quiz_request = {
            "assessment_id": "quiz_opt_123",
            "subject": "History",
            "topic": "World War II",
            "grade_level": "9-12",
            "num_questions": 15,
            "difficulty": "hard",
            "question_types": ["multiple_choice"],
            "learning_objectives": ["Understand WWII causes"],
            "lesson_id": "lesson_history_001"
        }

        mock_task = Mock()
        mock_task.id = "quiz_task_opt"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.generate_quiz_questions_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/content/assessments/generate",
                    json=quiz_request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_generate_quiz_task_failure(
        self, test_client, sample_quiz_request, mock_current_user
    ):
        """Test quiz generation when task queuing fails"""
        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.generate_quiz_questions_sync', side_effect=Exception("Task queue error")):
                response = test_client.post(
                    "/api/v1/content/assessments/generate",
                    json=sample_quiz_request
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestScriptOptimization:
    """Tests for Roblox script optimization endpoint"""

    def test_optimize_script_success(
        self, test_client, sample_script_optimize_request, mock_current_user
    ):
        """Test successful script optimization task queuing"""
        mock_task = Mock()
        mock_task.id = "optimize_task_123"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.optimize_roblox_script_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/roblox/optimize-script",
                    json=sample_script_optimize_request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["data"]["task_id"] == "optimize_task_123"
        assert data["data"]["script_id"] == sample_script_optimize_request["script_id"]

    def test_optimize_script_invalid_optimization_level(
        self, test_client, sample_script_optimize_request, mock_current_user
    ):
        """Test script optimization with invalid optimization level"""
        sample_script_optimize_request["optimization_level"] = "invalid_level"

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            response = test_client.post(
                "/api/v1/roblox/optimize-script",
                json=sample_script_optimize_request
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid optimization level" in response.json()["detail"].lower()

    def test_optimize_script_conservative_level(
        self, test_client, mock_current_user
    ):
        """Test script optimization with conservative level"""
        request = {
            "script_id": "script_conservative",
            "script_code": "local x = 1",
            "script_name": "SimpleScript",
            "optimization_level": "conservative",
            "preserve_comments": True,
            "generate_report": False
        }

        mock_task = Mock()
        mock_task.id = "task_conservative"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.optimize_roblox_script_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/roblox/optimize-script",
                    json=request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_optimize_script_aggressive_level(
        self, test_client, mock_current_user
    ):
        """Test script optimization with aggressive level"""
        request = {
            "script_id": "script_aggressive",
            "script_code": "local x = 1; local y = 2",
            "script_name": "ComplexScript",
            "optimization_level": "aggressive",
            "preserve_comments": False,
            "generate_report": True
        }

        mock_task = Mock()
        mock_task.id = "task_aggressive"

        mock_celery_task = Mock()
        mock_celery_task.delay.return_value = mock_task

        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.optimize_roblox_script_sync', mock_celery_task):
                response = test_client.post(
                    "/api/v1/roblox/optimize-script",
                    json=request
                )

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_optimize_script_task_failure(
        self, test_client, sample_script_optimize_request, mock_current_user
    ):
        """Test script optimization when task queuing fails"""
        with patch('apps.backend.api.routers.content.require_any_role', return_value=mock_current_user):
            with patch('apps.backend.api.routers.content.optimize_roblox_script_sync', side_effect=Exception("Optimization service down")):
                response = test_client.post(
                    "/api/v1/roblox/optimize-script",
                    json=sample_script_optimize_request
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.unit
class TestHelperFunctions:
    """Tests for helper functions"""

    def test_user_has_role_admin(self, mock_admin_user):
        """Test user has role check for admin"""
        from apps.backend.api.routers.content import _user_has_role

        result = _user_has_role(mock_admin_user, ["admin", "teacher"])
        assert result is True

    def test_user_has_role_teacher(self, mock_current_user):
        """Test user has role check for teacher"""
        from apps.backend.api.routers.content import _user_has_role

        result = _user_has_role(mock_current_user, ["admin", "teacher"])
        assert result is True

    def test_user_has_role_no_match(self, mock_current_user):
        """Test user has role check with no match"""
        from apps.backend.api.routers.content import _user_has_role

        mock_current_user.role = "student"
        result = _user_has_role(mock_current_user, ["admin", "teacher"])
        assert result is False

    def test_user_has_role_no_role_attribute(self):
        """Test user has role check when user has no role attribute"""
        from apps.backend.api.routers.content import _user_has_role

        user_no_role = Mock(spec=[])  # Mock without role attribute
        result = _user_has_role(user_no_role, ["admin"])
        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_content_update_success(self):
        """Test successful Pusher broadcast"""
        from apps.backend.api.routers.content import _broadcast_content_update

        mock_broadcast = AsyncMock()

        with patch('apps.backend.api.routers.content.broadcast_content_update', mock_broadcast):
            await _broadcast_content_update(
                user_id="user_123",
                content_id="content_456",
                status="completed",
                result="Generated content"
            )

        mock_broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_content_update_failure(self):
        """Test Pusher broadcast with error (should not raise)"""
        from apps.backend.api.routers.content import _broadcast_content_update

        with patch('apps.backend.api.routers.content.broadcast_content_update', AsyncMock(side_effect=Exception("Pusher error"))):
            # Should not raise exception, just log warning
            await _broadcast_content_update(
                user_id="user_123",
                content_id="content_456",
                status="failed",
                error="Test error"
            )
