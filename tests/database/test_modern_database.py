"""
Comprehensive Tests for Modern Database Layer (2025 Standards)

Tests SQLAlchemy 2.0 async database operations with pytest-asyncio.

Run with:
    pytest tests/database/test_modern_database.py -v
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.cache_modern import redis_cache
from database.models.content_modern import (
    ContentStatus,
    ContentType,
    DifficultyLevel,
    EducationalContent,
)
from database.models.user_modern import User, UserRole, UserStatus
from database.repositories.base_repository import BaseRepository
from database.repositories.user_repository import UserRepository
from database.session_modern import db_manager

# Test organization ID
TEST_ORG_ID = uuid.uuid4()


@pytest.fixture
async def session():
    """Provide async database session for tests."""
    async with db_manager.session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def transaction_session():
    """Provide async database session with transaction."""
    async with db_manager.transaction() as session:
        yield session
        await session.rollback()


@pytest.fixture
def user_data():
    """Provide sample user data."""
    return {
        "organization_id": TEST_ORG_ID,
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": "$2b$12$test...",
        "full_name": "Test User",
        "role": UserRole.STUDENT,
        "status": UserStatus.ACTIVE,
    }


@pytest.fixture
def content_data():
    """Provide sample content data."""
    return {
        "organization_id": TEST_ORG_ID,
        "title": "Test Lesson",
        "slug": "test-lesson",
        "description": "Test description",
        "content": "Test content body",
        "content_type": ContentType.LESSON,
        "difficulty_level": DifficultyLevel.BEGINNER,
        "status": ContentStatus.DRAFT,
        "author_id": uuid.uuid4(),
        "tags": ["test", "lesson"],
    }


class TestBaseRepository:
    """Test generic repository operations."""

    @pytest.mark.asyncio
    async def test_create(self, transaction_session, user_data):
        """Test creating a record."""
        repo = BaseRepository(User)

        user = await repo.create(transaction_session, **user_data)

        assert user.id is not None
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_get_by_id(self, transaction_session, user_data):
        """Test retrieving record by ID."""
        repo = BaseRepository(User)

        # Create user
        created_user = await repo.create(transaction_session, **user_data)
        user_id = created_user.id

        # Retrieve user
        retrieved_user = await repo.get_by_id(transaction_session, user_id)

        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.email == user_data["email"]

    @pytest.mark.asyncio
    async def test_update(self, transaction_session, user_data):
        """Test updating a record."""
        repo = BaseRepository(User)

        # Create user
        user = await repo.create(transaction_session, **user_data)

        # Update user
        updated_user = await repo.update(
            transaction_session,
            user.id,
            full_name="Updated Name",
        )

        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == user_data["email"]  # Unchanged

    @pytest.mark.asyncio
    async def test_soft_delete(self, transaction_session, user_data):
        """Test soft delete functionality."""
        repo = BaseRepository(User)

        # Create user
        user = await repo.create(transaction_session, **user_data)
        user_id = user.id

        # Soft delete
        deleted = await repo.delete(
            transaction_session,
            user_id,
            soft=True,
            deleted_by_id=uuid.uuid4(),
        )

        assert deleted is True

        # Verify not in normal queries
        user = await repo.get_by_id(
            transaction_session,
            user_id,
            include_deleted=False,
        )
        assert user is None

        # Verify in deleted queries
        user = await repo.get_by_id(
            transaction_session,
            user_id,
            include_deleted=True,
        )
        assert user is not None
        assert user.is_deleted is True

    @pytest.mark.asyncio
    async def test_restore(self, transaction_session, user_data):
        """Test restoring soft-deleted record."""
        repo = BaseRepository(User)

        # Create and delete user
        user = await repo.create(transaction_session, **user_data)
        await repo.delete(transaction_session, user.id, soft=True)

        # Restore user
        restored = await repo.restore(transaction_session, user.id)

        assert restored is not None
        assert restored.is_deleted is False

    @pytest.mark.asyncio
    async def test_count(self, transaction_session, user_data):
        """Test counting records."""
        repo = BaseRepository(User)

        # Create multiple users
        for i in range(5):
            data = user_data.copy()
            data["email"] = f"test{i}@example.com"
            data["username"] = f"test{i}"
            await repo.create(transaction_session, **data)

        count = await repo.count(transaction_session)

        assert count >= 5

    @pytest.mark.asyncio
    async def test_find_with_filters(self, transaction_session, user_data):
        """Test finding records with filters."""
        repo = BaseRepository(User)

        # Create users with different roles
        for role in [UserRole.STUDENT, UserRole.TEACHER]:
            data = user_data.copy()
            data["email"] = f"{role.value}@example.com"
            data["username"] = f"{role.value}user"
            data["role"] = role
            await repo.create(transaction_session, **data)

        # Find students
        students = await repo.find(
            transaction_session,
            filters={
                "organization_id": TEST_ORG_ID,
                "role": UserRole.STUDENT,
            },
        )

        assert len(students) >= 1
        assert all(u.role == UserRole.STUDENT for u in students)

    @pytest.mark.asyncio
    async def test_bulk_create(self, transaction_session):
        """Test bulk insert operations."""
        repo = BaseRepository(User)

        users_data = [
            {
                "organization_id": TEST_ORG_ID,
                "email": f"bulk{i}@example.com",
                "username": f"bulk{i}",
                "hashed_password": "$2b$12$...",
                "role": UserRole.STUDENT,
                "status": UserStatus.ACTIVE,
            }
            for i in range(10)
        ]

        users = await repo.create_many(transaction_session, users_data)

        assert len(users) == 10
        assert all(u.id is not None for u in users)


class TestUserRepository:
    """Test user-specific repository operations."""

    @pytest.mark.asyncio
    async def test_get_by_email(self, transaction_session, user_data):
        """Test getting user by email."""
        repo = UserRepository()

        # Create user
        await repo.create(transaction_session, **user_data)

        # Retrieve by email
        user = await repo.get_by_email(
            transaction_session,
            user_data["email"],
            TEST_ORG_ID,
        )

        assert user is not None
        assert user.email == user_data["email"]

    @pytest.mark.asyncio
    async def test_get_by_username(self, transaction_session, user_data):
        """Test getting user by username."""
        repo = UserRepository()

        # Create user
        await repo.create(transaction_session, **user_data)

        # Retrieve by username
        user = await repo.get_by_username(
            transaction_session,
            user_data["username"],
            TEST_ORG_ID,
        )

        assert user is not None
        assert user.username == user_data["username"]

    @pytest.mark.asyncio
    async def test_create_user_with_profile(self, transaction_session):
        """Test creating user with profile."""
        repo = UserRepository()

        user = await repo.create_user_with_profile(
            session=transaction_session,
            organization_id=TEST_ORG_ID,
            email="profile@example.com",
            username="profileuser",
            hashed_password="$2b$12$...",
            full_name="Profile User",
            role=UserRole.STUDENT,
            bio="Test bio",
            skills=["Python", "SQL"],
        )

        assert user.id is not None
        assert user.profile is not None
        assert user.profile.bio == "Test bio"
        assert user.profile.skills == ["Python", "SQL"]

    @pytest.mark.asyncio
    async def test_verify_email(self, transaction_session, user_data):
        """Test email verification."""
        repo = UserRepository()

        # Create user
        user = await repo.create(transaction_session, **user_data)

        # Verify email
        success = await repo.verify_email(transaction_session, user.id)

        assert success is True

        # Check user
        verified_user = await repo.get_by_id(transaction_session, user.id)
        assert verified_user.email_verified is True
        assert verified_user.email_verified_at is not None
        assert verified_user.status == UserStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_record_login(self, transaction_session, user_data):
        """Test recording successful login."""
        repo = UserRepository()

        # Create user
        user = await repo.create(transaction_session, **user_data)

        # Record login
        session = await repo.record_login(
            session=transaction_session,
            user_id=user.id,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            token_jti=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        assert session is not None
        assert session.ip_address == "192.168.1.1"
        assert session.is_active is True

        # Check user updated
        updated_user = await repo.get_by_id(transaction_session, user.id)
        assert updated_user.last_login_at is not None
        assert updated_user.last_login_ip == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, transaction_session, user_data):
        """Test getting active sessions for user."""
        repo = UserRepository()

        # Create user and sessions
        user = await repo.create(transaction_session, **user_data)

        for i in range(3):
            await repo.record_login(
                session=transaction_session,
                user_id=user.id,
                ip_address=f"192.168.1.{i}",
                user_agent="Test Browser",
                token_jti=str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )

        sessions = await repo.get_active_sessions(transaction_session, user.id)

        assert len(sessions) == 3
        assert all(s.is_active for s in sessions)

    @pytest.mark.asyncio
    async def test_get_user_statistics(self, transaction_session):
        """Test getting user statistics."""
        repo = UserRepository()

        # Create various users
        for i in range(5):
            await repo.create(
                transaction_session,
                organization_id=TEST_ORG_ID,
                email=f"stats{i}@example.com",
                username=f"stats{i}",
                hashed_password="$2b$12$...",
                role=UserRole.STUDENT if i < 3 else UserRole.TEACHER,
                status=UserStatus.ACTIVE,
            )

        stats = await repo.get_user_statistics(
            transaction_session,
            TEST_ORG_ID,
        )

        assert "total_users" in stats
        assert "active_users" in stats
        assert "users_by_role" in stats
        assert stats["total_users"] >= 5


class TestContentModels:
    """Test content models and operations."""

    @pytest.mark.asyncio
    async def test_create_content(self, transaction_session, content_data):
        """Test creating educational content."""
        repo = BaseRepository(EducationalContent)

        content = await repo.create(transaction_session, **content_data)

        assert content.id is not None
        assert content.title == content_data["title"]
        assert content.slug == content_data["slug"]
        assert content.version == 1
        assert content.is_latest_version is True

    @pytest.mark.asyncio
    async def test_content_publish(self, transaction_session, content_data):
        """Test publishing content."""
        repo = BaseRepository(EducationalContent)

        # Create draft content
        content = await repo.create(transaction_session, **content_data)

        # Publish
        content.publish(reviewer_id=uuid.uuid4())
        await transaction_session.flush()

        assert content.status == ContentStatus.PUBLISHED
        assert content.published_at is not None
        assert content.reviewer_id is not None

    @pytest.mark.asyncio
    async def test_content_views_and_completions(
        self,
        transaction_session,
        content_data,
    ):
        """Test tracking views and completions."""
        repo = BaseRepository(EducationalContent)

        content = await repo.create(transaction_session, **content_data)

        # Increment views
        for _ in range(5):
            content.increment_views()

        # Increment completions
        for _ in range(2):
            content.increment_completions()

        await transaction_session.flush()

        assert content.view_count == 5
        assert content.completion_count == 2


class TestSessionManagement:
    """Test database session management."""

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session context manager."""
        async with db_manager.session() as session:
            assert session is not None
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio
    async def test_transaction_context_manager(self):
        """Test transaction context manager."""
        async with db_manager.transaction() as session:
            assert session is not None
            # Transaction auto-commits on success

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test database health check."""
        is_healthy = await db_manager.health_check()
        assert is_healthy is True


class TestCaching:
    """Test Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test basic cache operations."""
        test_key = "test_key"
        test_value = {"data": "test"}

        # Set value
        success = await redis_cache.set(test_key, test_value, expire=60)
        assert success is True

        # Get value
        retrieved = await redis_cache.get(test_key)
        assert retrieved == test_value

        # Cleanup
        await redis_cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_cache_exists(self):
        """Test checking cache key existence."""
        test_key = "exists_test"

        # Should not exist
        exists = await redis_cache.exists(test_key)
        assert exists is False

        # Set and check
        await redis_cache.set(test_key, "value", expire=60)
        exists = await redis_cache.exists(test_key)
        assert exists is True

        # Cleanup
        await redis_cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_cache_delete_pattern(self):
        """Test deleting cache keys by pattern."""
        # Create multiple keys
        for i in range(3):
            await redis_cache.set(f"pattern_test:{i}", i, expire=60)

        # Delete all matching pattern
        deleted = await redis_cache.delete_pattern("pattern_test:*")
        assert deleted >= 3

    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check."""
        is_healthy = await redis_cache.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_teardown():
    """Cleanup after all tests."""
    await db_manager.close()
    await redis_cache.close()
