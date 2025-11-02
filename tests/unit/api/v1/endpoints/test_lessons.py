"""
Unit Tests for Lessons API Endpoints

Tests lesson management functionality for all user roles.

Phase 1 Week 1: Authentication & user management endpoint tests
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException, status

# Import endpoint functions and models
from apps.backend.api.v1.endpoints.lessons import (
    get_lessons,
    get_lesson_details,
    create_lesson,
    update_lesson_progress,
    get_lesson_statistics,
    in_memory_lessons,
    User,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_teacher_user():
    """Create mock teacher user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "teacher_user"
    user.email = "teacher@school.edu"
    user.role = "teacher"
    user.first_name = "Jane"
    user.last_name = "Smith"
    return user


@pytest.fixture
def mock_student_user():
    """Create mock student user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "student_user"
    user.email = "student@school.edu"
    user.role = "student"
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "admin_user"
    user.email = "admin@toolboxai.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_parent_user():
    """Create mock parent user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.username = "parent_user"
    user.email = "parent@example.com"
    user.role = "parent"
    return user


@pytest.fixture
def valid_lesson_data():
    """Create valid lesson creation data."""
    return {
        "title": "Introduction to Programming",
        "description": "Learn the basics of programming",
        "class_id": 1,
        "subject": "Computer Science",
        "duration": 45,
        "difficulty": "beginner",
        "objectives": ["Understand variables", "Learn loops", "Write functions"],
        "xp_reward": 50,
    }


@pytest.fixture
def valid_progress_data():
    """Create valid progress update data."""
    return {"progress": 75, "completed": False}


@pytest.fixture(autouse=True)
def clear_in_memory_lessons():
    """Clear in-memory lessons before each test."""
    in_memory_lessons.clear()
    yield
    in_memory_lessons.clear()


# ============================================================================
# Test Get Lessons Endpoint
# ============================================================================


class TestGetLessons:
    """Test lessons retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_lessons_teacher_fallback(self, mock_teacher_user):
        """Test getting lessons as teacher with fallback data."""
        result = await get_lessons(current_user=mock_teacher_user)

        assert isinstance(result, list)
        assert len(result) > 0
        # Teacher view should show completion counts
        assert "completion_count" in result[0]
        assert "total_students" in result[0]

    @pytest.mark.asyncio
    async def test_get_lessons_student_fallback(self, mock_student_user):
        """Test getting lessons as student with fallback data."""
        result = await get_lessons(current_user=mock_student_user)

        assert isinstance(result, list)
        assert len(result) > 0
        # Student view should show progress
        assert "progress" in result[0]
        assert "completed" in result[0]
        assert "xp_reward" in result[0]

    @pytest.mark.asyncio
    async def test_get_lessons_admin_fallback(self, mock_admin_user):
        """Test getting lessons as admin with fallback data."""
        result = await get_lessons(current_user=mock_admin_user)

        assert isinstance(result, list)
        assert len(result) > 0
        # Admin view should show teacher name and students completed
        assert "teacher_name" in result[0]
        assert "students_completed" in result[0]

    @pytest.mark.asyncio
    async def test_get_lessons_parent_fallback(self, mock_parent_user):
        """Test getting lessons as parent with fallback data."""
        result = await get_lessons(current_user=mock_parent_user)

        assert isinstance(result, list)
        assert len(result) > 0
        # Parent view should show student name and progress
        assert "student_name" in result[0]
        assert "progress" in result[0]

    @pytest.mark.asyncio
    async def test_get_lessons_with_class_filter(self, mock_teacher_user):
        """Test getting lessons with class_id filter."""
        result = await get_lessons(current_user=mock_teacher_user, class_id=1)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_lessons_with_subject_filter(self, mock_teacher_user):
        """Test getting lessons with subject filter."""
        result = await get_lessons(current_user=mock_teacher_user, subject="Mathematics")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_lessons_with_pagination(self, mock_teacher_user):
        """Test getting lessons with pagination."""
        result = await get_lessons(current_user=mock_teacher_user, limit=10, offset=5)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_lessons_teacher_includes_created_lessons(
        self, mock_teacher_user, valid_lesson_data
    ):
        """Test that teacher's created lessons appear in their list."""
        # Create a lesson first
        created = await create_lesson(lesson_data=valid_lesson_data, current_user=mock_teacher_user)

        # Now get lessons
        result = await get_lessons(current_user=mock_teacher_user)

        # Should include the created lesson
        created_ids = [l["id"] for l in result]
        assert created["id"] in created_ids

    @pytest.mark.asyncio
    async def test_get_lessons_different_roles_return_different_data(
        self, mock_teacher_user, mock_student_user, mock_admin_user
    ):
        """Test that different roles get role-appropriate data."""
        teacher_lessons = await get_lessons(current_user=mock_teacher_user)
        student_lessons = await get_lessons(current_user=mock_student_user)
        admin_lessons = await get_lessons(current_user=mock_admin_user)

        # All should return lists
        assert isinstance(teacher_lessons, list)
        assert isinstance(student_lessons, list)
        assert isinstance(admin_lessons, list)

        # Check role-specific fields
        if len(teacher_lessons) > 0:
            assert "completion_count" in teacher_lessons[0]
        if len(student_lessons) > 0:
            assert "progress" in student_lessons[0]
        if len(admin_lessons) > 0:
            assert "teacher_name" in admin_lessons[0]


# ============================================================================
# Test Get Lesson Details Endpoint
# ============================================================================


class TestGetLessonDetails:
    """Test get lesson details endpoint."""

    @pytest.mark.asyncio
    async def test_get_lesson_details_fallback(self, mock_teacher_user):
        """Test getting lesson details with fallback data."""
        result = await get_lesson_details(lesson_id=1, current_user=mock_teacher_user)

        assert "id" in result
        assert "title" in result
        assert "description" in result
        assert "class_name" in result
        assert "teacher_name" in result
        assert "objectives" in result
        assert isinstance(result["objectives"], list)

    @pytest.mark.asyncio
    async def test_get_lesson_details_has_content_structure(self, mock_teacher_user):
        """Test lesson details includes content structure."""
        result = await get_lesson_details(lesson_id=1, current_user=mock_teacher_user)

        assert "content" in result
        assert isinstance(result["content"], dict)
        assert "sections" in result["content"]

    @pytest.mark.asyncio
    async def test_get_lesson_details_has_resources(self, mock_teacher_user):
        """Test lesson details includes resources."""
        result = await get_lesson_details(lesson_id=1, current_user=mock_teacher_user)

        assert "resources" in result
        assert isinstance(result["resources"], list)

    @pytest.mark.asyncio
    async def test_get_lesson_details_has_metadata(self, mock_teacher_user):
        """Test lesson details includes metadata."""
        result = await get_lesson_details(lesson_id=1, current_user=mock_teacher_user)

        assert "duration" in result
        assert "difficulty" in result
        assert "xp_reward" in result
        assert "created_at" in result


# ============================================================================
# Test Create Lesson Endpoint
# ============================================================================


class TestCreateLesson:
    """Test lesson creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_lesson_teacher_success(self, mock_teacher_user, valid_lesson_data):
        """Test successful lesson creation by teacher."""
        result = await create_lesson(lesson_data=valid_lesson_data, current_user=mock_teacher_user)

        assert "id" in result
        assert result["title"] == valid_lesson_data["title"]
        assert result["teacher_id"] == mock_teacher_user.id
        assert result["status"] == "draft"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_create_lesson_admin_success(self, mock_admin_user, valid_lesson_data):
        """Test successful lesson creation by admin."""
        result = await create_lesson(lesson_data=valid_lesson_data, current_user=mock_admin_user)

        assert "id" in result
        assert result["title"] == valid_lesson_data["title"]

    @pytest.mark.asyncio
    async def test_create_lesson_student_forbidden(self, mock_student_user, valid_lesson_data):
        """Test that students cannot create lessons."""
        with pytest.raises(HTTPException) as exc_info:
            await create_lesson(lesson_data=valid_lesson_data, current_user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized to create lessons" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_lesson_parent_forbidden(self, mock_parent_user, valid_lesson_data):
        """Test that parents cannot create lessons."""
        with pytest.raises(HTTPException) as exc_info:
            await create_lesson(lesson_data=valid_lesson_data, current_user=mock_parent_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_lesson_includes_all_submitted_data(
        self, mock_teacher_user, valid_lesson_data
    ):
        """Test that created lesson includes all submitted data."""
        result = await create_lesson(lesson_data=valid_lesson_data, current_user=mock_teacher_user)

        # All original fields should be present
        assert result["title"] == valid_lesson_data["title"]
        assert result["description"] == valid_lesson_data["description"]
        assert result["subject"] == valid_lesson_data["subject"]
        assert result["duration"] == valid_lesson_data["duration"]
        assert result["difficulty"] == valid_lesson_data["difficulty"]
        assert result["objectives"] == valid_lesson_data["objectives"]
        assert result["xp_reward"] == valid_lesson_data["xp_reward"]

    @pytest.mark.asyncio
    async def test_create_lesson_adds_metadata(self, mock_teacher_user, valid_lesson_data):
        """Test that lesson creation adds necessary metadata."""
        result = await create_lesson(lesson_data=valid_lesson_data, current_user=mock_teacher_user)

        assert "id" in result
        assert "teacher_id" in result
        assert "teacher_name" in result
        assert "completion_count" in result
        assert result["completion_count"] == 0
        assert "total_students" in result
        assert result["total_students"] == 0
        assert "status" in result
        assert "created_at" in result
        assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_create_lesson_with_published_status(self, mock_teacher_user):
        """Test creating lesson with published status."""
        lesson_data = {
            "title": "Published Lesson",
            "class_id": 1,
            "status": "published",
        }

        result = await create_lesson(lesson_data=lesson_data, current_user=mock_teacher_user)

        assert result["status"] == "published"

    @pytest.mark.asyncio
    async def test_create_lesson_adds_to_in_memory_storage(
        self, mock_teacher_user, valid_lesson_data
    ):
        """Test that created lesson is added to in-memory storage."""
        initial_count = len(in_memory_lessons)

        await create_lesson(lesson_data=valid_lesson_data, current_user=mock_teacher_user)

        assert len(in_memory_lessons) == initial_count + 1

    @pytest.mark.asyncio
    async def test_create_lesson_handles_snake_case_class_id(self, mock_teacher_user):
        """Test lesson creation with snake_case class_id."""
        lesson_data = {"title": "Test Lesson", "class_id": 123}

        result = await create_lesson(lesson_data=lesson_data, current_user=mock_teacher_user)

        assert "class_name" in result

    @pytest.mark.asyncio
    async def test_create_lesson_handles_camel_case_class_id(self, mock_teacher_user):
        """Test lesson creation with camelCase classId."""
        lesson_data = {"title": "Test Lesson", "classId": 123}

        result = await create_lesson(lesson_data=lesson_data, current_user=mock_teacher_user)

        assert "class_name" in result


# ============================================================================
# Test Update Lesson Progress Endpoint
# ============================================================================


class TestUpdateLessonProgress:
    """Test lesson progress update endpoint."""

    @pytest.mark.asyncio
    async def test_update_progress_non_student_forbidden(
        self, mock_teacher_user, valid_progress_data
    ):
        """Test that non-students cannot update progress."""
        with pytest.raises(HTTPException) as exc_info:
            await update_lesson_progress(
                lesson_id=1, progress_data=valid_progress_data, current_user=mock_teacher_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Only students can update their progress" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_progress_admin_forbidden(self, mock_admin_user, valid_progress_data):
        """Test that admins cannot update progress."""
        with pytest.raises(HTTPException) as exc_info:
            await update_lesson_progress(
                lesson_id=1, progress_data=valid_progress_data, current_user=mock_admin_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_progress_no_db_raises_error(
        self, mock_student_user, valid_progress_data
    ):
        """Test that progress update without database raises error."""
        with pytest.raises(HTTPException) as exc_info:
            await update_lesson_progress(
                lesson_id=1, progress_data=valid_progress_data, current_user=mock_student_user
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to update progress" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_progress_with_completion(self, mock_student_user):
        """Test updating progress with completion."""
        progress_data = {"progress": 100, "completed": True}

        with pytest.raises(HTTPException):
            await update_lesson_progress(
                lesson_id=1, progress_data=progress_data, current_user=mock_student_user
            )

    @pytest.mark.asyncio
    async def test_update_progress_partial_completion(self, mock_student_user):
        """Test updating progress partially completed."""
        progress_data = {"progress": 50, "completed": False}

        with pytest.raises(HTTPException):
            await update_lesson_progress(
                lesson_id=1, progress_data=progress_data, current_user=mock_student_user
            )


# ============================================================================
# Test Get Lesson Statistics Endpoint
# ============================================================================


class TestGetLessonStatistics:
    """Test lesson statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_statistics_teacher_success(self, mock_teacher_user):
        """Test successful statistics retrieval by teacher."""
        result = await get_lesson_statistics(lesson_id=1, current_user=mock_teacher_user)

        assert "lesson_id" in result
        assert "total_students" in result
        assert "completed" in result
        assert "in_progress" in result
        assert "not_started" in result
        assert "average_progress" in result
        assert "completion_rate" in result

    @pytest.mark.asyncio
    async def test_get_statistics_admin_success(self, mock_admin_user):
        """Test successful statistics retrieval by admin."""
        result = await get_lesson_statistics(lesson_id=1, current_user=mock_admin_user)

        assert result["lesson_id"] == 1
        assert isinstance(result["total_students"], int)
        assert isinstance(result["average_progress"], (int, float))

    @pytest.mark.asyncio
    async def test_get_statistics_student_forbidden(self, mock_student_user):
        """Test that students cannot view statistics."""
        with pytest.raises(HTTPException) as exc_info:
            await get_lesson_statistics(lesson_id=1, current_user=mock_student_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized to view statistics" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_statistics_parent_forbidden(self, mock_parent_user):
        """Test that parents cannot view statistics."""
        with pytest.raises(HTTPException) as exc_info:
            await get_lesson_statistics(lesson_id=1, current_user=mock_parent_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_statistics_includes_progress_breakdown(self, mock_teacher_user):
        """Test that statistics include progress breakdown."""
        result = await get_lesson_statistics(lesson_id=1, current_user=mock_teacher_user)

        # Progress breakdown
        assert result["completed"] >= 0
        assert result["in_progress"] >= 0
        assert result["not_started"] >= 0
        # Total should equal sum of breakdown
        expected_total = result["completed"] + result["in_progress"] + result["not_started"]
        assert result["total_students"] == expected_total

    @pytest.mark.asyncio
    async def test_get_statistics_includes_performance_metrics(self, mock_teacher_user):
        """Test that statistics include performance metrics."""
        result = await get_lesson_statistics(lesson_id=1, current_user=mock_teacher_user)

        assert "average_time_spent" in result
        assert "difficulty_rating" in result
        assert isinstance(result["average_time_spent"], (int, float))
        assert isinstance(result["difficulty_rating"], (int, float))

    @pytest.mark.asyncio
    async def test_get_statistics_completion_rate_is_percentage(self, mock_teacher_user):
        """Test that completion rate is a valid percentage."""
        result = await get_lesson_statistics(lesson_id=1, current_user=mock_teacher_user)

        assert 0 <= result["completion_rate"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
