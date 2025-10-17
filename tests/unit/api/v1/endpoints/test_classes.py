"""
Unit tests for Class Management API endpoints.

Tests all class CRUD operations, enrollment management, and role-based access control.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from fastapi import HTTPException, status

from apps.backend.api.v1.endpoints.classes import (
    get_classes,
    get_class_details,
    get_class_students,
    create_class,
    update_class,
    enroll_student,
    unenroll_student,
    batch_enroll_students,
    delete_class,
)
from apps.backend.models.classes import ClassCreate, ClassUpdate, ClassSummary, ClassDetails
from database.models.models import Class, ClassEnrollment, User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_current_user_teacher():
    """Mock teacher user."""
    user = Mock()
    user.id = str(uuid4())
    user.username = "teacher_user"
    user.role = "teacher"
    user.email = "teacher@school.edu"
    return user


@pytest.fixture
def mock_current_user_student():
    """Mock student user."""
    user = Mock()
    user.id = str(uuid4())
    user.username = "student_user"
    user.role = "student"
    user.email = "student@school.edu"
    return user


@pytest.fixture
def mock_current_user_admin():
    """Mock admin user."""
    user = Mock()
    user.id = str(uuid4())
    user.username = "admin_user"
    user.role = "admin"
    user.email = "admin@school.edu"
    return user


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    # Mock the async context manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


@pytest.fixture
def sample_class_data():
    """Sample class data for testing."""
    return {
        "id": uuid4(),
        "name": "Mathematics 101",
        "subject": "Mathematics",
        "grade_level": 7,
        "room": "Room 203",
        "schedule": "Mon/Wed/Fri 10:00 AM",
        "description": "Introductory mathematics course",
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(days=90),
        "max_students": 30,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def sample_student():
    """Sample student user."""
    student = Mock(spec=User)
    student.id = uuid4()
    student.username = "student_test"
    student.first_name = "Test"
    student.last_name = "Student"
    student.email = "student@test.com"
    student.role = "student"
    return student


# ============================================================================
# Test Get Classes
# ============================================================================


class TestGetClasses:
    """Test class listing endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_classes_teacher_success(
        self, mock_db_service, mock_current_user_teacher, mock_db_session, sample_class_data
    ):
        """Test teacher successfully retrieving their classes."""
        # Setup
        mock_db_service.initialize = AsyncMock()
        mock_db_service.async_session_scope = AsyncMock(return_value=mock_db_session)

        # Create mock class object
        mock_class = Mock(spec=Class)
        for key, value in sample_class_data.items():
            setattr(mock_class, key, value)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        # Mock query result with class and student count
        mock_result = AsyncMock()
        mock_result.all = Mock(return_value=[(mock_class, 15)])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await get_classes(
            current_user=mock_current_user_teacher,
            limit=20,
            offset=0,
            session=mock_db_session,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ClassSummary)
        assert result[0].name == sample_class_data["name"]
        assert result[0].student_count == 15

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_classes_student_success(
        self, mock_db_service, mock_current_user_student, mock_db_session, sample_class_data
    ):
        """Test student successfully retrieving enrolled classes."""
        # Setup
        mock_db_service.initialize = AsyncMock()
        mock_db_service.async_session_scope = AsyncMock(return_value=mock_db_session)

        mock_class = Mock(spec=Class)
        for key, value in sample_class_data.items():
            setattr(mock_class, key, value)

        mock_result = AsyncMock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_class])))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await get_classes(
            current_user=mock_current_user_student,
            limit=20,
            offset=0,
            session=mock_db_session,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].name == sample_class_data["name"]

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_classes_admin_with_filters(
        self, mock_db_service, mock_current_user_admin, mock_db_session, sample_class_data
    ):
        """Test admin retrieving classes with filters."""
        # Setup
        mock_db_service.initialize = AsyncMock()
        mock_db_service.async_session_scope = AsyncMock(return_value=mock_db_session)

        mock_class = Mock(spec=Class)
        for key, value in sample_class_data.items():
            setattr(mock_class, key, value)

        mock_result = AsyncMock()
        mock_result.all = Mock(return_value=[(mock_class, 20)])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Execute with filters
        result = await get_classes(
            current_user=mock_current_user_admin,
            limit=20,
            offset=0,
            subject="Mathematics",
            grade_level=7,
            session=mock_db_session,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_classes_database_error_fallback(
        self, mock_db_service, mock_current_user_teacher, mock_db_session
    ):
        """Test fallback to sample data on database error."""
        # Setup
        mock_db_service.initialize = AsyncMock()
        mock_db_service.async_session_scope = AsyncMock(return_value=mock_db_session)
        mock_db_session.execute = AsyncMock(side_effect=Exception("Database error"))

        # Execute
        result = await get_classes(
            current_user=mock_current_user_teacher,
            limit=20,
            offset=0,
            session=mock_db_session,
        )

        # Assert fallback data returned
        assert isinstance(result, list)
        assert len(result) > 0


# ============================================================================
# Test Get Class Details
# ============================================================================


class TestGetClassDetails:
    """Test class details endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_class_details_success(
        self, mock_db_service, mock_current_user_teacher, sample_class_data
    ):
        """Test successfully retrieving class details."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(sample_class_data["id"])
        mock_class = Mock(spec=Class)
        for key, value in sample_class_data.items():
            setattr(mock_class, key, value)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        # Mock teacher
        mock_teacher = Mock(spec=User)
        mock_teacher.first_name = "John"
        mock_teacher.last_name = "Doe"
        mock_teacher.username = "john_doe"
        mock_teacher.email = "john@school.edu"

        mock_session = AsyncMock()

        # Mock class query
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        # Mock student count query
        count_result = AsyncMock()
        count_result.scalar = Mock(return_value=15)

        # Mock teacher query
        teacher_result = AsyncMock()
        teacher_result.scalar_one_or_none = Mock(return_value=mock_teacher)

        # Setup execute to return different results based on call order
        mock_session.execute = AsyncMock(side_effect=[class_result, count_result, teacher_result])

        # Execute
        result = await get_class_details(class_id=class_id, current_user=mock_current_user_teacher, session=mock_session)

        # Assert
        assert isinstance(result, ClassDetails)
        assert result.id == class_id
        assert result.name == sample_class_data["name"]
        assert result.student_count == 15
        assert result.teacher_name == "John Doe"

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_class_details_not_found(
        self, mock_db_service, mock_current_user_teacher
    ):
        """Test class not found error."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        mock_session = AsyncMock()
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=class_result)

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_class_details(
                class_id=str(uuid4()), current_user=mock_current_user_teacher, session=mock_session
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_class_details_invalid_uuid(self, mock_current_user_teacher):
        """Test invalid UUID format."""
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_class_details(class_id="invalid-uuid", current_user=mock_current_user_teacher)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Test Get Class Students
# ============================================================================


class TestGetClassStudents:
    """Test class student listing endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_get_class_students_success(
        self, mock_db_service, mock_current_user_teacher, sample_student
    ):
        """Test successfully retrieving class students."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(uuid4())
        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_session = AsyncMock()

        # Mock class query
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        # Mock students query
        students_result = AsyncMock()
        students_result.all = Mock(return_value=[
            (sample_student, datetime.now(), "active", None, None)
        ])

        mock_session.execute = AsyncMock(side_effect=[class_result, students_result])

        # Execute
        result = await get_class_students(class_id=class_id, current_user=mock_current_user_teacher, session=mock_session)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["username"] == sample_student.username

    @pytest.mark.asyncio
    async def test_get_class_students_forbidden_student(self, mock_current_user_student):
        """Test student cannot view student list."""
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_class_students(class_id=str(uuid4()), current_user=mock_current_user_student)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test Create Class
# ============================================================================


class TestCreateClass:
    """Test class creation endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_create_class_teacher_success(
        self, mock_db_service, mock_current_user_teacher, sample_class_data
    ):
        """Test teacher successfully creating a class."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_data = ClassCreate(
            name=sample_class_data["name"],
            subject=sample_class_data["subject"],
            grade_level=sample_class_data["grade_level"],
            room=sample_class_data["room"],
            schedule=sample_class_data["schedule"],
        )

        mock_class = Mock(spec=Class)
        for key, value in sample_class_data.items():
            setattr(mock_class, key, value)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_session = AsyncMock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        with patch("apps.backend.api.v1.endpoints.classes.Class", return_value=mock_class):
            # Execute
            result = await create_class(class_data=class_data, current_user=mock_current_user_teacher, session=mock_session)

        # Assert
        assert isinstance(result, ClassSummary)
        assert result.name == sample_class_data["name"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_class_forbidden_student(self, mock_current_user_student):
        """Test student cannot create classes."""
        # Setup
        class_data = ClassCreate(
            name="Test Class",
            subject="Test",
            grade_level=7,
        )

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_class(class_data=class_data, current_user=mock_current_user_student)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test Update Class
# ============================================================================


class TestUpdateClass:
    """Test class update endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_update_class_success(
        self, mock_db_service, mock_current_user_teacher, sample_class_data
    ):
        """Test successfully updating a class."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(sample_class_data["id"])
        update_data = ClassUpdate(name="Updated Class Name")

        mock_class = Mock(spec=Class)
        for key, value in sample_class_data.items():
            setattr(mock_class, key, value)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_session = AsyncMock()

        # Mock class query
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        # Mock student count query
        count_result = AsyncMock()
        count_result.scalar = Mock(return_value=10)

        mock_session.execute = AsyncMock(side_effect=[class_result, count_result])
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        # Execute
        result = await update_class(
            class_id=class_id, class_data=update_data, current_user=mock_current_user_teacher
        , session=mock_session)

        # Assert
        assert isinstance(result, ClassSummary)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_update_class_not_found(
        self, mock_db_service, mock_current_user_teacher
    ):
        """Test updating non-existent class."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        update_data = ClassUpdate(name="Updated Name")

        mock_session = AsyncMock()
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=class_result)

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_class(
                class_id=str(uuid4()), class_data=update_data, current_user=mock_current_user_teacher, session=mock_session
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Enroll Student
# ============================================================================


class TestEnrollStudent:
    """Test student enrollment endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_enroll_student_success(
        self, mock_db_service, mock_current_user_teacher, sample_student
    ):
        """Test successfully enrolling a student."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(uuid4())
        student_id = str(sample_student.id)

        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)
        mock_class.max_students = 30

        mock_session = AsyncMock()

        # Mock class query
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        # Mock student query
        student_result = AsyncMock()
        student_result.scalar_one_or_none = Mock(return_value=sample_student)

        # Mock existing enrollment query (none exists)
        existing_result = AsyncMock()
        existing_result.scalar_one_or_none = Mock(return_value=None)

        # Mock student count query
        count_result = AsyncMock()
        count_result.scalar = Mock(return_value=15)

        mock_session.execute = AsyncMock(
            side_effect=[class_result, student_result, existing_result, count_result]
        )
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        # Execute
        result = await enroll_student(
            class_id=class_id, student_id=student_id, current_user=mock_current_user_teacher
        , session=mock_session)

        # Assert
        assert "message" in result
        assert "enrolled successfully" in result["message"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_enroll_student_already_enrolled(
        self, mock_db_service, mock_current_user_teacher, sample_student
    ):
        """Test enrolling already enrolled student."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(uuid4())
        student_id = str(sample_student.id)

        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_enrollment = Mock(spec=ClassEnrollment)
        mock_enrollment.status = "active"

        mock_session = AsyncMock()

        # Mock queries
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        student_result = AsyncMock()
        student_result.scalar_one_or_none = Mock(return_value=sample_student)

        existing_result = AsyncMock()
        existing_result.scalar_one_or_none = Mock(return_value=mock_enrollment)

        mock_session.execute = AsyncMock(
            side_effect=[class_result, student_result, existing_result]
        )

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await enroll_student(
                class_id=class_id, student_id=student_id, current_user=mock_current_user_teacher, session=mock_session
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already enrolled" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_enroll_student_forbidden_student(self, mock_current_user_student):
        """Test student cannot enroll others."""
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await enroll_student(
                class_id=str(uuid4()), student_id=str(uuid4()), current_user=mock_current_user_student
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test Unenroll Student
# ============================================================================


class TestUnenrollStudent:
    """Test student unenrollment endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_unenroll_student_success(
        self, mock_db_service, mock_current_user_teacher
    ):
        """Test successfully unenrolling a student."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(uuid4())
        student_id = str(uuid4())

        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_enrollment = Mock(spec=ClassEnrollment)
        mock_enrollment.status = "active"

        mock_session = AsyncMock()

        # Mock queries
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        enrollment_result = AsyncMock()
        enrollment_result.scalar_one_or_none = Mock(return_value=mock_enrollment)

        mock_session.execute = AsyncMock(side_effect=[class_result, enrollment_result])
        mock_session.commit = AsyncMock()

        # Execute
        result = await unenroll_student(
            class_id=class_id, student_id=student_id, current_user=mock_current_user_teacher
        , session=mock_session)

        # Assert
        assert "message" in result
        assert "removed" in result["message"]
        assert mock_enrollment.status == "inactive"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_unenroll_student_not_enrolled(
        self, mock_db_service, mock_current_user_teacher
    ):
        """Test unenrolling non-enrolled student."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(uuid4())
        student_id = str(uuid4())

        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_session = AsyncMock()

        # Mock queries
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        enrollment_result = AsyncMock()
        enrollment_result.scalar_one_or_none = Mock(return_value=None)

        mock_session.execute = AsyncMock(side_effect=[class_result, enrollment_result])

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await unenroll_student(
                class_id=class_id, student_id=student_id, current_user=mock_current_user_teacher, session=mock_session
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Batch Enroll Students
# ============================================================================


class TestBatchEnrollStudents:
    """Test batch student enrollment endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_batch_enroll_students_success(
        self, mock_db_service, mock_current_user_teacher, sample_student
    ):
        """Test successfully batch enrolling students."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(uuid4())
        student_ids = [str(sample_student.id)]

        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.teacher_id = UUID(mock_current_user_teacher.id)

        mock_session = AsyncMock()

        # Mock class query
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        # Mock student query
        student_result = AsyncMock()
        student_result.scalar_one_or_none = Mock(return_value=sample_student)

        # Mock existing enrollment query (none exists)
        existing_result = AsyncMock()
        existing_result.scalar_one_or_none = Mock(return_value=None)

        mock_session.execute = AsyncMock(
            side_effect=[class_result, student_result, existing_result]
        )
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        # Execute
        result = await batch_enroll_students(
            class_id=class_id, student_ids=student_ids, current_user=mock_current_user_teacher
        , session=mock_session)

        # Assert
        assert "summary" in result
        assert result["summary"]["successfully_enrolled"] == 1
        assert len(result["enrolled"]) == 1
        assert result["enrolled"][0] == sample_student.username

    @pytest.mark.asyncio
    async def test_batch_enroll_students_forbidden(self, mock_current_user_student):
        """Test student cannot batch enroll."""
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await batch_enroll_students(
                class_id=str(uuid4()), student_ids=[], current_user=mock_current_user_student
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test Delete Class
# ============================================================================


class TestDeleteClass:
    """Test class deletion endpoint."""

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_delete_class_success(
        self, mock_db_service, mock_current_user_admin, sample_class_data
    ):
        """Test admin successfully deleting a class."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        class_id = str(sample_class_data["id"])

        mock_class = Mock(spec=Class)
        mock_class.id = UUID(class_id)
        mock_class.name = sample_class_data["name"]

        mock_session = AsyncMock()

        # Mock class query
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=mock_class)

        mock_session.execute = AsyncMock(return_value=class_result)
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        # Execute
        result = await delete_class(class_id=class_id, current_user=mock_current_user_admin, session=mock_session)

        # Assert
        assert "message" in result
        assert sample_class_data["name"] in result["message"]
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_class_forbidden_teacher(self, mock_current_user_teacher):
        """Test teacher cannot delete classes."""
        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_class(class_id=str(uuid4()), current_user=mock_current_user_teacher)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    @patch("apps.backend.api.v1.endpoints.classes.database_service")
    async def test_delete_class_not_found(
        self, mock_db_service, mock_current_user_admin
    ):
        """Test deleting non-existent class."""
        # Setup
        mock_db_service.initialize = AsyncMock()

        mock_session = AsyncMock()
        class_result = AsyncMock()
        class_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=class_result)

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_class(class_id=str(uuid4()), current_user=mock_current_user_admin, session=mock_session)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
