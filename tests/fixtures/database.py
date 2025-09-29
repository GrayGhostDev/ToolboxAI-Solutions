"""
Database test fixtures for ToolboxAI test suite.

Provides reusable database fixtures for testing.
"""
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from datetime import datetime
from typing import AsyncGenerator, Generator
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_db_session():
    """Mock synchronous database session."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.flush = Mock()
    session.refresh = Mock()
    session.merge = Mock()
    session.delete = Mock()
    
    # Configure query chain
    query_mock = Mock()
    query_mock.filter = Mock(return_value=query_mock)
    query_mock.filter_by = Mock(return_value=query_mock)
    query_mock.first = Mock(return_value=None)
    query_mock.all = Mock(return_value=[])
    query_mock.count = Mock(return_value=0)
    query_mock.limit = Mock(return_value=query_mock)
    query_mock.offset = Mock(return_value=query_mock)
    query_mock.order_by = Mock(return_value=query_mock)
    session.query.return_value = query_mock
    
    return session


@pytest.fixture
async def mock_async_db_session():
    """
    Mock asynchronous database session (2025 pattern).
    Properly handles async context manager protocol.
    """
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.merge = Mock()
    session.delete = Mock()
    session.begin = AsyncMock()
    
    # Configure async execute with proper result handling
    result_mock = AsyncMock()
    scalars_mock = Mock()
    scalars_mock.first = Mock(return_value=None)
    scalars_mock.all = Mock(return_value=[])
    scalars_mock.one = Mock(side_effect=Exception("No rows found"))
    scalars_mock.one_or_none = Mock(return_value=None)
    result_mock.scalars = Mock(return_value=scalars_mock)
    result_mock.scalar = Mock(return_value=None)
    result_mock.scalar_one = Mock(side_effect=Exception("No rows found"))
    result_mock.scalar_one_or_none = Mock(return_value=None)
    session.execute = AsyncMock(return_value=result_mock)
    
    # Support async context manager protocol (2025 best practice)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    return session


@pytest.fixture
def test_user():
    """Create a test user object."""
    return {
        "id": str(uuid.uuid4()),
        "username": "test_user",
        "email": "test@example.com",
        "role": "student",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "profile": {
            "first_name": "Test",
            "last_name": "User",
            "avatar_url": None,
            "bio": "Test user for automated testing"
        }
    }


@pytest.fixture
def test_teacher():
    """Create a test teacher object."""
    return {
        "id": str(uuid.uuid4()),
        "username": "test_teacher",
        "email": "teacher@example.com",
        "role": "teacher",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "profile": {
            "first_name": "Test",
            "last_name": "Teacher",
            "avatar_url": None,
            "bio": "Test teacher for automated testing",
            "subjects": ["Mathematics", "Science"]
        }
    }


@pytest.fixture
def test_admin():
    """Create a test admin object."""
    return {
        "id": str(uuid.uuid4()),
        "username": "test_admin",
        "email": "admin@example.com",
        "role": "admin",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "profile": {
            "first_name": "Test",
            "last_name": "Admin",
            "avatar_url": None,
            "bio": "Test admin for automated testing",
            "permissions": ["all"]
        }
    }


@pytest.fixture
def test_content():
    """Create test educational content."""
    return {
        "id": str(uuid.uuid4()),
        "title": "Test Lesson",
        "description": "A test lesson for automated testing",
        "content_type": "lesson",
        "subject": "Mathematics",
        "grade_level": 9,
        "difficulty": "medium",
        "estimated_duration": 45,
        "created_by": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "tags": ["algebra", "equations"],
        "metadata": {
            "version": "1.0",
            "language": "en",
            "prerequisites": []
        }
    }


@pytest.fixture
def test_course():
    """Create a test course object."""
    course_id = str(uuid.uuid4())
    return {
        "id": course_id,
        "title": "Introduction to Algebra",
        "description": "Basic algebraic concepts and problem solving",
        "subject": "Mathematics",
        "grade_level": 9,
        "created_by": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_published": True,
        "enrollment_count": 25,
        "modules": [
            {
                "id": str(uuid.uuid4()),
                "course_id": course_id,
                "title": "Module 1: Variables and Expressions",
                "order": 1,
                "is_locked": False
            },
            {
                "id": str(uuid.uuid4()),
                "course_id": course_id,
                "title": "Module 2: Linear Equations",
                "order": 2,
                "is_locked": True
            }
        ]
    }


@pytest.fixture
def test_assessment():
    """Create a test assessment object."""
    return {
        "id": str(uuid.uuid4()),
        "title": "Algebra Quiz 1",
        "description": "Test your understanding of variables and expressions",
        "assessment_type": "quiz",
        "subject": "Mathematics",
        "grade_level": 9,
        "total_points": 100,
        "passing_score": 70,
        "time_limit": 30,
        "created_by": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "questions": [
            {
                "id": str(uuid.uuid4()),
                "question": "What is 2x + 3 when x = 5?",
                "type": "multiple_choice",
                "points": 10,
                "options": ["13", "10", "15", "8"],
                "correct_answer": "13"
            }
        ]
    }


@pytest.fixture
def test_submission():
    """Create a test submission object."""
    return {
        "id": str(uuid.uuid4()),
        "assessment_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "submitted_at": datetime.utcnow(),
        "score": 85,
        "status": "graded",
        "feedback": "Good work! Review the section on solving equations.",
        "answers": [
            {
                "question_id": str(uuid.uuid4()),
                "answer": "13",
                "is_correct": True,
                "points_earned": 10
            }
        ]
    }


@pytest.fixture
def mock_db_models():
    """Mock database models."""
    models = Mock()
    
    # User model
    models.User = Mock()
    models.User.__name__ = "User"
    models.User.query = Mock()
    
    # Content model
    models.Content = Mock()
    models.Content.__name__ = "Content"
    models.Content.query = Mock()
    
    # Course model
    models.Course = Mock()
    models.Course.__name__ = "Course"
    models.Course.query = Mock()
    
    # Assessment model
    models.Assessment = Mock()
    models.Assessment.__name__ = "Assessment"
    models.Assessment.query = Mock()
    
    return models


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    connection = Mock()
    connection.execute = Mock()
    connection.commit = Mock()
    connection.rollback = Mock()
    connection.close = Mock()
    connection.is_active = True
    return connection


@pytest.fixture
async def async_db_generator():
    """Async database session generator for dependency injection."""
    session = await mock_async_db_session()
    
    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield session
        finally:
            await session.close()
    
    return get_session