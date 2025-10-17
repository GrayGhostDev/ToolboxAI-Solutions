"""
Tests for GET /analytics/student-progress endpoint - Student progress tracking.

Tests the analytics_production.py student-progress endpoint which provides:
- Overall progress percentage
- Completed and total lessons
- XP earned
- Leaderboard rank
- Authorization (admin, teacher, or self)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import HTTPException

from apps.backend.api.v1.endpoints.analytics_production import get_student_progress
from database.models.models import User, UserRole, UserProgress, Analytics, Leaderboard, Lesson


class TestGetStudentProgress:
    """Test suite for GET /analytics/student-progress endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create a mock admin user."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "admin_user"
        user.role = UserRole.ADMIN
        user.is_active = True
        return user

    @pytest.fixture
    def mock_teacher_user(self):
        """Create a mock teacher user."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "teacher_user"
        user.role = UserRole.TEACHER
        user.is_active = True
        return user

    @pytest.fixture
    def mock_student_user(self):
        """Create a mock student user."""
        user = MagicMock()
        user.id = uuid4()
        user.username = "student_user"
        user.role = UserRole.STUDENT
        user.is_active = True
        return user

    @pytest.fixture
    def mock_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_student_progress_success_as_admin(self, mock_admin_user, mock_session):
        """Test successful student progress retrieval as admin."""
        target_student_id = str(uuid4())

        # Mock database query results
        query_results = [
            75.5,  # overall_progress
            24,    # completed_lessons
            35,    # total_lessons
            2450,  # xp_earned
            42,    # rank
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=mock_admin_user,
                session=mock_session
            )

        # Assertions
        assert response["overall_progress"] == 75.5
        assert response["completed_lessons"] == 24
        assert response["total_lessons"] == 35
        assert response["xp_earned"] == 2450
        assert response["rank"] == 42
        assert response["current_streak"] == 0  # TODO in implementation
        assert response["best_streak"] == 0     # TODO in implementation
        assert response["badges_earned"] == 0   # Placeholder
        assert "subjects" in response
        assert "recent_activity" in response

    @pytest.mark.asyncio
    async def test_student_progress_success_as_teacher(self, mock_teacher_user, mock_session):
        """Test successful student progress retrieval as teacher."""
        target_student_id = str(uuid4())

        # Mock database query results
        query_results = [
            68.0,  # overall_progress
            18,    # completed_lessons
            30,    # total_lessons
            1800,  # xp_earned
            85,    # rank
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=mock_teacher_user,
                session=mock_session
            )

        assert response["overall_progress"] == 68.0
        assert response["xp_earned"] == 1800

    @pytest.mark.asyncio
    async def test_student_progress_success_as_self(self, mock_student_user, mock_session):
        """Test successful student progress retrieval for own data."""
        # Student viewing their own progress (no student_id provided)
        query_results = [
            55.0,  # overall_progress
            12,    # completed_lessons
            25,    # total_lessons
            1200,  # xp_earned
            150,   # rank
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=None,  # Will default to current_user.id
                class_id=None,
                current_user=mock_student_user,
                session=mock_session
            )

        assert response["overall_progress"] == 55.0
        assert response["completed_lessons"] == 12

    @pytest.mark.asyncio
    async def test_student_progress_authorization_denied_for_other_student(
        self, mock_student_user, mock_session
    ):
        """Test that students cannot view other students' progress."""
        # Different student ID
        other_student_id = str(uuid4())
        assert other_student_id != str(mock_student_user.id)

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_student_progress(
                    student_id=other_student_id,
                    class_id=None,
                    current_user=mock_student_user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 403
            assert "Not authorized" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_student_progress_invalid_student_id_format(
        self, mock_admin_user, mock_session
    ):
        """Test handling of invalid UUID format."""
        invalid_student_id = "not-a-valid-uuid"

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_student_progress(
                    student_id=invalid_student_id,
                    class_id=None,
                    current_user=mock_admin_user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 400
            assert "Invalid student ID format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_student_progress_handles_no_progress_data(
        self, mock_admin_user, mock_session
    ):
        """Test handling when student has no progress data."""
        target_student_id = str(uuid4())

        # Mock all queries returning 0 or None
        query_results = [
            None,  # overall_progress (no data)
            0,     # completed_lessons
            50,    # total_lessons (exist but not started)
            0,     # xp_earned
            None,  # rank (not on leaderboard)
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=mock_admin_user,
                session=mock_session
            )

        # Should return 0 for null values
        assert response["overall_progress"] == 0.0
        assert response["completed_lessons"] == 0
        assert response["xp_earned"] == 0
        assert response["rank"] == 0

    @pytest.mark.asyncio
    async def test_student_progress_rounds_percentage_correctly(
        self, mock_admin_user, mock_session
    ):
        """Test that progress percentage is rounded to 1 decimal place."""
        target_student_id = str(uuid4())

        query_results = [
            67.8523,  # overall_progress (should round to 67.9)
            20,       # completed_lessons
            30,       # total_lessons
            2000,     # xp_earned
            50,       # rank
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert response["overall_progress"] == 67.9

    @pytest.mark.asyncio
    async def test_student_progress_with_class_filter(
        self, mock_admin_user, mock_session
    ):
        """Test student progress with class_id filter."""
        target_student_id = str(uuid4())
        class_id = str(uuid4())

        query_results = [
            80.0,  # overall_progress
            16,    # completed_lessons
            20,    # total_lessons
            1600,  # xp_earned
            30,    # rank
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=class_id,  # Filter by specific class
                current_user=mock_admin_user,
                session=mock_session
            )

        # Should return filtered data
        assert response["overall_progress"] == 80.0
        assert response["completed_lessons"] == 16

    @pytest.mark.asyncio
    async def test_student_progress_database_error_handling(
        self, mock_admin_user, mock_session
    ):
        """Test that database errors are handled gracefully."""
        target_student_id = str(uuid4())

        mock_session.execute.side_effect = Exception("Database error")

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_student_progress(
                    student_id=target_student_id,
                    class_id=None,
                    current_user=mock_admin_user,
                    session=mock_session
                )

            assert exc_info.value.status_code == 500
            assert "Failed to fetch student progress" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_student_progress_response_structure(
        self, mock_admin_user, mock_session
    ):
        """Test that response has correct structure with all required fields."""
        target_student_id = str(uuid4())

        # Mock minimal data
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=mock_admin_user,
                session=mock_session
            )

        # Verify all required fields are present
        required_fields = [
            "overall_progress",
            "completed_lessons",
            "total_lessons",
            "current_streak",
            "best_streak",
            "xp_earned",
            "badges_earned",
            "rank",
            "subjects",
            "recent_activity",
        ]

        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(response["overall_progress"], (int, float))
        assert isinstance(response["completed_lessons"], int)
        assert isinstance(response["total_lessons"], int)
        assert isinstance(response["xp_earned"], int)
        assert isinstance(response["rank"], int)
        assert isinstance(response["subjects"], list)
        assert isinstance(response["recent_activity"], list)

    @pytest.mark.asyncio
    async def test_student_progress_100_percent_completion(
        self, mock_admin_user, mock_session
    ):
        """Test student with 100% completion."""
        target_student_id = str(uuid4())

        query_results = [
            100.0,  # overall_progress (perfect score)
            30,     # completed_lessons
            30,     # total_lessons (all completed)
            3000,   # xp_earned
            1,      # rank (top student)
        ]

        result_mocks = []
        for value in query_results:
            result_mock = AsyncMock()
            result_mock.scalar.return_value = value
            result_mocks.append(result_mock)

        mock_session.execute.side_effect = result_mocks

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=mock_admin_user,
                session=mock_session
            )

        assert response["overall_progress"] == 100.0
        assert response["completed_lessons"] == response["total_lessons"]
        assert response["rank"] == 1

    @pytest.mark.asyncio
    async def test_student_progress_authorization_matrix(self, mock_session):
        """Test authorization for different role combinations."""
        target_student_id = str(uuid4())

        # Mock minimal response
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        with patch('apps.backend.api.v1.endpoints.analytics_production.database_service') as mock_db_service:
            mock_db_service.initialize = AsyncMock()

            # Test 1: Admin can view any student
            admin = MagicMock()
            admin.id = uuid4()
            admin.role = UserRole.ADMIN
            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=admin,
                session=mock_session
            )
            assert response is not None

            # Test 2: Teacher can view any student
            teacher = MagicMock()
            teacher.id = uuid4()
            teacher.role = UserRole.TEACHER
            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=teacher,
                session=mock_session
            )
            assert response is not None

            # Test 3: Student can view own progress
            student = MagicMock()
            student.id = UUID(target_student_id)
            student.role = UserRole.STUDENT
            response = await get_student_progress(
                student_id=target_student_id,
                class_id=None,
                current_user=student,
                session=mock_session
            )
            assert response is not None

            # Test 4: Student CANNOT view other student's progress
            other_student = MagicMock()
            other_student.id = uuid4()
            other_student.role = UserRole.STUDENT
            with pytest.raises(HTTPException) as exc_info:
                await get_student_progress(
                    student_id=target_student_id,
                    class_id=None,
                    current_user=other_student,
                    session=mock_session
                )
            assert exc_info.value.status_code == 403


@pytest.mark.integration
class TestStudentProgressIntegration:
    """Integration tests for student progress endpoint with real database."""

    @pytest.mark.asyncio
    async def test_student_progress_with_test_database(self):
        """Test student progress endpoint with actual test database."""
        # TODO: Implement with test database fixture
        pass

    @pytest.mark.asyncio
    async def test_student_progress_concurrent_access(self):
        """Test concurrent access to student progress by multiple users."""
        # TODO: Implement concurrency test
        pass
