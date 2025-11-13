"""
Unit tests for Courses Router
Tests all CRUD operations for courses, lessons, and enrollments
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import status

# Import factories


@pytest.mark.unit
class TestCoursesRouter:
    """Test suite for courses router endpoints"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.delete = Mock()
        return session

    @pytest.fixture
    def sample_course_data(self):
        """Sample course data for testing"""
        return {
            "title": "Introduction to Python",
            "code": "PY101",
            "description": "Learn Python programming basics",
            "subject": "Computer Science",
            "grade_level": 9,
            "is_published": True,
            "difficulty_level": "beginner",
            "instructor_id": str(uuid4()),
        }

    @pytest.fixture
    def sample_lesson_data(self):
        """Sample lesson data for testing"""
        return {
            "title": "Variables and Data Types",
            "description": "Introduction to Python variables",
            "order_index": 1,
            "content_type": "interactive",
            "difficulty": "intermediate",
            "estimated_duration": 45,
        }

    # ===== Course List Tests =====

    def test_list_courses_success(self, test_client, mock_db_session):
        """Test successful course listing"""
        # Mock course data
        mock_courses = [
            Mock(id=uuid4(), title="Course 1", code="C1"),
            Mock(id=uuid4(), title="Course 2", code="C2"),
        ]

        # Configure mock query chain
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_courses
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get("/api/v1/courses/")

        assert response.status_code == status.HTTP_200_OK
        # Verify query was called
        mock_db_session.query.assert_called_once()

    def test_list_courses_with_filters(self, test_client, mock_db_session):
        """Test course listing with filters"""
        mock_courses = [Mock(id=uuid4(), title="Filtered Course")]

        # Mock query chain with filters
        mock_query = Mock()
        filter_mock = Mock()
        filter_mock.offset.return_value.limit.return_value.all.return_value = mock_courses
        mock_query.filter.return_value = filter_mock
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get(
                "/api/v1/courses/", params={"is_published": True, "difficulty_level": "beginner"}
            )

        assert response.status_code == status.HTTP_200_OK
        # Verify filters were applied
        assert mock_query.filter.call_count >= 1

    def test_list_courses_pagination(self, test_client, mock_db_session):
        """Test course listing pagination"""
        mock_courses = [Mock(id=uuid4())]

        mock_query = Mock()
        offset_mock = Mock()
        limit_mock = Mock()
        limit_mock.all.return_value = mock_courses
        offset_mock.limit.return_value = limit_mock
        mock_query.offset.return_value = offset_mock
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get("/api/v1/courses/?skip=10&limit=5")

        assert response.status_code == status.HTTP_200_OK
        mock_query.offset.assert_called_with(10)
        offset_mock.limit.assert_called_with(5)

    # ===== Get Course Tests =====

    def test_get_course_success(self, test_client, mock_db_session):
        """Test successful course retrieval"""
        course_id = uuid4()
        mock_course = Mock(id=course_id, title="Test Course", code="TC101")

        # Mock course query
        course_query = Mock()
        course_query.filter.return_value.first.return_value = mock_course

        # Mock lesson count query
        count_query = Mock()
        count_query.filter.return_value.scalar.return_value = 5

        mock_db_session.query.side_effect = [course_query, count_query]

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            with patch("apps.backend.api.routers.courses.CourseResponse") as mock_response:
                mock_response.model_validate.return_value.model_dump.return_value = {
                    "id": str(course_id),
                    "title": "Test Course",
                }
                response = test_client.get(f"/api/v1/courses/{course_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_get_course_not_found(self, test_client, mock_db_session):
        """Test course not found error"""
        course_id = uuid4()

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get(f"/api/v1/courses/{course_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    # ===== Create Course Tests =====

    def test_create_course_success(self, test_client, mock_db_session, sample_course_data):
        """Test successful course creation"""
        new_course = Mock(id=uuid4(), **sample_course_data)

        # Mock instructor lookup
        instructor_query = Mock()
        instructor_query.filter.return_value.first.return_value = Mock(
            id=sample_course_data["instructor_id"]
        )

        mock_db_session.query.return_value = instructor_query
        mock_db_session.refresh.side_effect = lambda x: setattr(x, "id", uuid4())

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            with patch("apps.backend.api.routers.courses.Course", return_value=new_course):
                response = test_client.post("/api/v1/courses/", json=sample_course_data)

        assert response.status_code == status.HTTP_201_CREATED
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_course_instructor_not_found(
        self, test_client, mock_db_session, sample_course_data
    ):
        """Test course creation with invalid instructor"""
        # Mock instructor not found
        instructor_query = Mock()
        instructor_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = instructor_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.post("/api/v1/courses/", json=sample_course_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "instructor" in response.json()["detail"].lower()

    def test_create_course_without_instructor(self, test_client, mock_db_session):
        """Test course creation without instructor_id"""
        course_data = {
            "title": "Self-Paced Course",
            "code": "SP101",
            "description": "Learn at your own pace",
            "subject": "Math",
            "grade_level": 10,
        }

        new_course = Mock(id=uuid4(), **course_data)

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            with patch("apps.backend.api.routers.courses.Course", return_value=new_course):
                response = test_client.post("/api/v1/courses/", json=course_data)

        assert response.status_code == status.HTTP_201_CREATED
        mock_db_session.add.assert_called_once()

    # ===== Update Course Tests =====

    def test_update_course_success(self, test_client, mock_db_session):
        """Test successful course update"""
        course_id = uuid4()
        mock_course = Mock(id=course_id, title="Old Title")

        update_data = {"title": "New Title", "description": "Updated description"}

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_course
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.put(f"/api/v1/courses/{course_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_course)

    def test_update_course_not_found(self, test_client, mock_db_session):
        """Test updating non-existent course"""
        course_id = uuid4()

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.put(f"/api/v1/courses/{course_id}", json={"title": "New Title"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ===== Delete Course Tests =====

    def test_delete_course_success(self, test_client, mock_db_session):
        """Test successful course deletion"""
        course_id = uuid4()
        mock_course = Mock(id=course_id)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_course
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.delete(f"/api/v1/courses/{course_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_db_session.delete.assert_called_once_with(mock_course)
        mock_db_session.commit.assert_called_once()

    def test_delete_course_not_found(self, test_client, mock_db_session):
        """Test deleting non-existent course"""
        course_id = uuid4()

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.delete(f"/api/v1/courses/{course_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestLessonsEndpoints:
    """Test suite for lesson endpoints"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.delete = Mock()
        return session

    def test_list_course_lessons_success(self, test_client, mock_db_session):
        """Test listing lessons for a course"""
        course_id = uuid4()
        mock_course = Mock(id=course_id)
        mock_lessons = [
            Mock(id=uuid4(), title="Lesson 1", order_index=1),
            Mock(id=uuid4(), title="Lesson 2", order_index=2),
        ]

        # Mock course exists check
        course_query = Mock()
        course_query.filter.return_value.first.return_value = mock_course

        # Mock lessons query
        lessons_query = Mock()
        lessons_query.filter.return_value.order_by.return_value.all.return_value = mock_lessons

        mock_db_session.query.side_effect = [course_query, lessons_query]

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get(f"/api/v1/courses/{course_id}/lessons")

        assert response.status_code == status.HTTP_200_OK

    def test_list_lessons_course_not_found(self, test_client, mock_db_session):
        """Test listing lessons for non-existent course"""
        course_id = uuid4()

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get(f"/api/v1/courses/{course_id}/lessons")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_lesson_success(self, test_client, mock_db_session):
        """Test successful lesson creation"""
        course_id = uuid4()
        mock_course = Mock(id=course_id)

        lesson_data = {
            "title": "New Lesson",
            "description": "Lesson description",
            "order_index": 1,
            "content_type": "video",
            "difficulty": "beginner",
            "estimated_duration": 30,
        }

        # Mock course exists
        course_query = Mock()
        course_query.filter.return_value.first.return_value = mock_course
        mock_db_session.query.return_value = course_query

        new_lesson = Mock(id=uuid4(), **lesson_data)

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            with patch("apps.backend.api.routers.courses.Lesson", return_value=new_lesson):
                response = test_client.post(
                    f"/api/v1/courses/{course_id}/lessons", json=lesson_data
                )

        assert response.status_code == status.HTTP_201_CREATED
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_update_lesson_success(self, test_client, mock_db_session):
        """Test successful lesson update"""
        course_id = uuid4()
        lesson_id = uuid4()
        mock_lesson = Mock(id=lesson_id, title="Old Title")

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lesson
        mock_db_session.query.return_value = mock_query

        update_data = {"title": "Updated Lesson Title"}

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.put(
                f"/api/v1/courses/{course_id}/lessons/{lesson_id}", json=update_data
            )

        assert response.status_code == status.HTTP_200_OK
        mock_db_session.commit.assert_called_once()

    def test_delete_lesson_success(self, test_client, mock_db_session):
        """Test successful lesson deletion"""
        course_id = uuid4()
        lesson_id = uuid4()
        mock_lesson = Mock(id=lesson_id)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_lesson
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.delete(f"/api/v1/courses/{course_id}/lessons/{lesson_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_db_session.delete.assert_called_once_with(mock_lesson)


@pytest.mark.unit
class TestEnrollmentEndpoints:
    """Test suite for enrollment endpoints"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        return session

    def test_enroll_in_course_success(self, test_client, mock_db_session):
        """Test successful course enrollment"""
        course_id = uuid4()
        user_id = uuid4()

        mock_course = Mock(id=course_id)

        # Mock course exists
        course_query = Mock()
        course_query.filter.return_value.first.return_value = mock_course

        # Mock no existing enrollment
        enrollment_query = Mock()
        enrollment_query.filter.return_value.first.return_value = None

        mock_db_session.query.side_effect = [course_query, enrollment_query]

        new_enrollment = Mock(id=uuid4(), user_id=user_id, course_id=course_id)

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            with patch("apps.backend.api.routers.courses.Enrollment", return_value=new_enrollment):
                response = test_client.post(f"/api/v1/courses/{course_id}/enroll?user_id={user_id}")

        assert response.status_code == status.HTTP_201_CREATED
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_enroll_already_enrolled(self, test_client, mock_db_session):
        """Test enrolling when already enrolled"""
        course_id = uuid4()
        user_id = uuid4()

        mock_course = Mock(id=course_id)
        existing_enrollment = Mock(id=uuid4())

        # Mock course exists
        course_query = Mock()
        course_query.filter.return_value.first.return_value = mock_course

        # Mock existing enrollment
        enrollment_query = Mock()
        enrollment_query.filter.return_value.first.return_value = existing_enrollment

        mock_db_session.query.side_effect = [course_query, enrollment_query]

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.post(f"/api/v1/courses/{course_id}/enroll?user_id={user_id}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already enrolled" in response.json()["detail"].lower()

    def test_get_user_enrollments(self, test_client, mock_db_session):
        """Test getting user's enrollments"""
        user_id = uuid4()
        mock_enrollments = [
            Mock(id=uuid4(), user_id=user_id),
            Mock(id=uuid4(), user_id=user_id),
        ]

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_enrollments
        mock_db_session.query.return_value = mock_query

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            response = test_client.get(f"/api/v1/courses/enrollments/user/{user_id}")

        assert response.status_code == status.HTTP_200_OK

    def test_get_course_progress(self, test_client, mock_db_session):
        """Test getting course progress for a user"""
        course_id = uuid4()
        user_id = uuid4()

        mock_enrollment = Mock(
            id=uuid4(), user_id=user_id, course_id=course_id, progress_percentage=75.0
        )
        mock_lessons = [Mock(id=uuid4()), Mock(id=uuid4())]
        mock_progress = [
            Mock(lesson_id=mock_lessons[0].id, completed=True, time_spent_minutes=45),
            Mock(lesson_id=mock_lessons[1].id, completed=False, time_spent_minutes=20),
        ]

        # Mock enrollment query
        enrollment_query = Mock()
        enrollment_query.filter.return_value.first.return_value = mock_enrollment

        # Mock lessons query
        lessons_query = Mock()
        lessons_query.filter.return_value.all.return_value = mock_lessons

        # Mock progress query
        progress_query = Mock()
        progress_query.filter.return_value.all.return_value = mock_progress

        mock_db_session.query.side_effect = [enrollment_query, lessons_query, progress_query]

        with patch("apps.backend.api.routers.courses.get_db", return_value=mock_db_session):
            with patch("apps.backend.api.routers.courses.EnrollmentResponse"):
                response = test_client.get(f"/api/v1/courses/{course_id}/progress/{user_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_lessons" in data
        assert "completed_lessons" in data
        assert "progress_percentage" in data
