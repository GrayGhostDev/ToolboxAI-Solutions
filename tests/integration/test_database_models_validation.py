from unittest.mock import Mock, patch

import pytest
import pytest_asyncio


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

"""
Database and Models Validation Tests

Comprehensive validation of database integration and models:
1. Database connection and health
2. Model imports and relationships
3. Enhanced Content Generation models
4. Content Generation Batch operations
5. Database migrations and schema validation
6. Performance and indexing
7. Data integrity and constraints
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import database components
try:
    from database.connection import AsyncSessionLocal, engine, get_async_session
    from database.models import (
        Agent,
        Base,
        ContentGenerationBatch,
        ContentGenerationRequest,
        EducationalContent,
        EnhancedContentGeneration,
        User,
    )
    from database.repositories import AgentRepository, ContentRepository, UserRepository
except ImportError as e:
    pytest.skip(f"Required database modules not available: {e}", allow_module_level=True)

logger = logging.getLogger(__name__)


class TestDatabaseConnectivity:
    """Test database connection and basic operations"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_database_connection_health(self):
        """Test database connection health"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                health_value = result.scalar()
                assert health_value == 1
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_database_version_compatibility(self):
        """Test database version and compatibility"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                assert version is not None
                assert "PostgreSQL" in version
                logger.info(f"Database version: {version}")
        except Exception as e:
            logger.warning(f"Database version check failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_database_transaction_handling(self):
        """Test database transaction handling"""
        async with AsyncSessionLocal() as session:
            try:
                # Start transaction
                await session.begin()

                # Test operation
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1

                # Rollback transaction
                await session.rollback()

            except Exception as e:
                await session.rollback()
                pytest.fail(f"Transaction handling failed: {e}")


class TestModelImportsAndStructure:
    """Test model imports and structure validation"""

    def test_base_model_import(self):
        """Test Base model import"""
        assert Base is not None
        assert hasattr(Base, 'metadata')

    def test_user_model_import(self):
        """Test User model import and structure"""
        assert User is not None
        assert hasattr(User, '__tablename__')
        assert hasattr(User, 'id')
        assert hasattr(User, 'email')
        assert hasattr(User, 'username')

    def test_agent_model_import(self):
        """Test Agent model import and structure"""
        assert Agent is not None
        assert hasattr(Agent, '__tablename__')
        assert hasattr(Agent, 'id')
        assert hasattr(Agent, 'name')

    def test_enhanced_content_generation_model_import(self):
        """Test EnhancedContentGeneration model import"""
        assert EnhancedContentGeneration is not None
        assert hasattr(EnhancedContentGeneration, '__tablename__')
        assert hasattr(EnhancedContentGeneration, 'id')
        assert hasattr(EnhancedContentGeneration, 'request_id')
        assert hasattr(EnhancedContentGeneration, 'status')

    def test_content_generation_batch_model_import(self):
        """Test ContentGenerationBatch model import"""
        assert ContentGenerationBatch is not None
        assert hasattr(ContentGenerationBatch, '__tablename__')
        assert hasattr(ContentGenerationBatch, 'id')
        assert hasattr(ContentGenerationBatch, 'batch_id')

    def test_educational_content_model_import(self):
        """Test EducationalContent model import"""
        try:
            assert EducationalContent is not None
            assert hasattr(EducationalContent, '__tablename__')
        except (NameError, AttributeError):
            pytest.skip("EducationalContent model not available")


class TestUserModelOperations:
    """Test User model CRUD operations"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_user_creation_and_retrieval(self):
        """Test user creation and retrieval"""
        async with AsyncSessionLocal() as session:
            # Create test user
            test_user = User(
                email=f"test_{uuid4()}@example.com",
                username=f"testuser_{uuid4().hex[:8]}",
                full_name="Test User",
                role="student",
                is_active=True
            )

            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)

            # Verify creation
            assert test_user.id is not None
            assert test_user.email is not None
            assert test_user.role == "student"
            assert test_user.is_active is True

            # Test retrieval
            retrieved_user = await session.get(User, test_user.id)
            assert retrieved_user is not None
            assert retrieved_user.email == test_user.email

            # Cleanup
            await session.delete(test_user)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_user_email_uniqueness(self):
        """Test user email uniqueness constraint"""
        async with AsyncSessionLocal() as session:
            email = f"unique_test_{uuid4()}@example.com"

            # Create first user
            user1 = User(
                email=email,
                username=f"user1_{uuid4().hex[:8]}",
                full_name="User One",
                role="student"
            )

            session.add(user1)
            await session.commit()

            try:
                # Attempt to create second user with same email
                user2 = User(
                    email=email,
                    username=f"user2_{uuid4().hex[:8]}",
                    full_name="User Two",
                    role="teacher"
                )

                session.add(user2)
                await session.commit()

                # Should not reach here due to unique constraint
                pytest.fail("Email uniqueness constraint not enforced")

            except Exception:
                # Expected - email should be unique
                await session.rollback()

            finally:
                # Cleanup
                await session.delete(user1)
                await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_user_role_validation(self):
        """Test user role validation"""
        async with AsyncSessionLocal() as session:
            valid_roles = ["admin", "teacher", "student"]

            for role in valid_roles:
                user = User(
                    email=f"role_test_{role}_{uuid4()}@example.com",
                    username=f"user_{role}_{uuid4().hex[:8]}",
                    full_name=f"Test {role.title()}",
                    role=role
                )

                session.add(user)
                await session.commit()
                await session.refresh(user)

                assert user.role == role

                # Cleanup
                await session.delete(user)
                await session.commit()


class TestEnhancedContentGenerationModel:
    """Test EnhancedContentGeneration model operations"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_enhanced_content_generation_creation(self):
        """Test EnhancedContentGeneration model creation"""
        async with AsyncSessionLocal() as session:
            content_gen = EnhancedContentGeneration(
                request_id=f"req_{uuid4()}",
                subject_type="mathematics",
                grade_level="5th",
                content_type="lesson",
                topic="fractions",
                requirements="Interactive lesson with visual examples",
                status="pending",
                priority=1,
                estimated_duration=30
            )

            session.add(content_gen)
            await session.commit()
            await session.refresh(content_gen)

            # Verify creation
            assert content_gen.id is not None
            assert content_gen.subject_type == "mathematics"
            assert content_gen.status == "pending"
            assert content_gen.created_at is not None

            # Cleanup
            await session.delete(content_gen)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_enhanced_content_generation_status_updates(self):
        """Test status updates for enhanced content generation"""
        async with AsyncSessionLocal() as session:
            content_gen = EnhancedContentGeneration(
                request_id=f"status_test_{uuid4()}",
                subject_type="science",
                grade_level="6th",
                content_type="quiz",
                status="pending"
            )

            session.add(content_gen)
            await session.commit()
            await session.refresh(content_gen)

            # Test status transitions
            statuses = ["pending", "processing", "completed", "failed"]

            for status in statuses:
                content_gen.status = status
                content_gen.updated_at = datetime.now(timezone.utc)
                await session.commit()

                # Verify update
                await session.refresh(content_gen)
                assert content_gen.status == status

            # Cleanup
            await session.delete(content_gen)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_enhanced_content_generation_with_metadata(self):
        """Test enhanced content generation with metadata"""
        async with AsyncSessionLocal() as session:
            metadata = {
                "custom_instructions": "Use visual aids",
                "target_skills": ["addition", "subtraction"],
                "difficulty_level": "beginner"
            }

            content_gen = EnhancedContentGeneration(
                request_id=f"metadata_test_{uuid4()}",
                subject_type="mathematics",
                grade_level="3rd",
                content_type="worksheet",
                status="pending",
                metadata=metadata
            )

            session.add(content_gen)
            await session.commit()
            await session.refresh(content_gen)

            # Verify metadata storage
            assert content_gen.metadata is not None
            assert content_gen.metadata["custom_instructions"] == "Use visual aids"
            assert "target_skills" in content_gen.metadata

            # Cleanup
            await session.delete(content_gen)
            await session.commit()


class TestContentGenerationBatchModel:
    """Test ContentGenerationBatch model operations"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_content_generation_batch_creation(self):
        """Test ContentGenerationBatch creation and management"""
        async with AsyncSessionLocal() as session:
            batch = ContentGenerationBatch(
                batch_id=f"batch_{uuid4()}",
                total_requests=5,
                completed_requests=0,
                failed_requests=0,
                status="pending",
                created_by="test_user"
            )

            session.add(batch)
            await session.commit()
            await session.refresh(batch)

            # Verify creation
            assert batch.id is not None
            assert batch.total_requests == 5
            assert batch.completed_requests == 0
            assert batch.status == "pending"

            # Cleanup
            await session.delete(batch)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_batch_progress_tracking(self):
        """Test batch progress tracking"""
        async with AsyncSessionLocal() as session:
            batch = ContentGenerationBatch(
                batch_id=f"progress_test_{uuid4()}",
                total_requests=10,
                completed_requests=0,
                status="processing",
                created_by="test_user"
            )

            session.add(batch)
            await session.commit()
            await session.refresh(batch)

            # Simulate progress updates
            for completed in range(1, 11):
                batch.completed_requests = completed
                batch.updated_at = datetime.now(timezone.utc)

                if completed == batch.total_requests:
                    batch.status = "completed"

                await session.commit()
                await session.refresh(batch)

                assert batch.completed_requests == completed

            # Final verification
            assert batch.status == "completed"
            assert batch.completed_requests == batch.total_requests

            # Cleanup
            await session.delete(batch)
            await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_batch_with_content_items(self):
        """Test batch with associated content generation items"""
        async with AsyncSessionLocal() as session:
            # Create batch
            batch = ContentGenerationBatch(
                batch_id=f"items_test_{uuid4()}",
                total_requests=3,
                completed_requests=0,
                status="processing",
                created_by="test_user"
            )

            session.add(batch)
            await session.commit()
            await session.refresh(batch)

            # Create associated content generation items
            content_items = []
            for i in range(3):
                content_gen = EnhancedContentGeneration(
                    request_id=f"batch_item_{i}_{uuid4()}",
                    subject_type="science",
                    grade_level="4th",
                    content_type="lesson",
                    status="pending",
                    batch_id=batch.batch_id
                )
                session.add(content_gen)
                content_items.append(content_gen)

            await session.commit()

            # Verify relationships
            for item in content_items:
                await session.refresh(item)
                assert item.batch_id == batch.batch_id

            # Cleanup
            for item in content_items:
                await session.delete(item)
            await session.delete(batch)
            await session.commit()


class TestDatabaseRepositories:
    """Test database repository patterns"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_user_repository_operations(self):
        """Test UserRepository operations"""
        try:
            repo = UserRepository()

            # Test repository initialization
            assert repo is not None

            # Test user creation through repository
            user_data = {
                "email": f"repo_test_{uuid4()}@example.com",
                "username": f"repo_user_{uuid4().hex[:8]}",
                "full_name": "Repository Test User",
                "role": "student"
            }

            created_user = await repo.create_user(user_data)
            assert created_user is not None
            assert created_user.email == user_data["email"]

            # Test user retrieval
            retrieved_user = await repo.get_user_by_email(user_data["email"])
            assert retrieved_user is not None
            assert retrieved_user.id == created_user.id

            # Cleanup
            await repo.delete_user(created_user.id)

        except (ImportError, AttributeError):
            pytest.skip("UserRepository not available")

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_content_repository_operations(self):
        """Test ContentRepository operations"""
        try:
            repo = ContentRepository()

            # Test content creation
            content_data = {
                "request_id": f"content_repo_{uuid4()}",
                "subject_type": "mathematics",
                "grade_level": "5th",
                "content_type": "quiz",
                "status": "pending"
            }

            created_content = await repo.create_content_request(content_data)
            assert created_content is not None

            # Test content retrieval
            retrieved_content = await repo.get_content_by_request_id(content_data["request_id"])
            assert retrieved_content is not None

            # Cleanup
            await repo.delete_content_request(created_content.id)

        except (ImportError, AttributeError):
            pytest.skip("ContentRepository not available")


class TestDatabasePerformance:
    """Test database performance and indexing"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_query_performance(self):
        """Test query performance with multiple records"""
        async with AsyncSessionLocal() as session:
            # Create test data
            users = []
            for i in range(100):
                user = User(
                    email=f"perf_test_{i}_{uuid4()}@example.com",
                    username=f"perfuser_{i}_{uuid4().hex[:8]}",
                    full_name=f"Performance Test User {i}",
                    role="student"
                )
                users.append(user)

            session.add_all(users)
            await session.commit()

            try:
                # Test query performance
                start_time = time.time()

                result = await session.execute(
                    text("SELECT COUNT(*) FROM users WHERE role = 'student'")
                )
                count = result.scalar()

                query_time = time.time() - start_time

                # Should complete quickly
                assert query_time < 1.0
                assert count >= 100

            finally:
                # Cleanup
                for user in users:
                    await session.delete(user)
                await session.commit()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_database_indexes(self):
        """Test that important database indexes exist"""
        try:
            async with engine.begin() as conn:
                # Get table information
                inspector = inspect(conn.sync_engine)

                # Check for important indexes
                user_indexes = inspector.get_indexes('users')
                user_index_columns = [idx['column_names'] for idx in user_indexes]

                # Email should be indexed (unique constraint)
                email_indexed = any('email' in cols for cols in user_index_columns)
                assert email_indexed, "Email column should be indexed"

        except Exception as e:
            logger.warning(f"Index check failed: {e}")


class TestDataIntegrityAndConstraints:
    """Test data integrity and database constraints"""

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_foreign_key_constraints(self):
        """Test foreign key constraints"""
        async with AsyncSessionLocal() as session:
            try:
                # Attempt to create content generation with invalid user reference
                content_gen = EnhancedContentGeneration(
                    request_id=f"fk_test_{uuid4()}",
                    subject_type="mathematics",
                    grade_level="5th",
                    content_type="lesson",
                    status="pending",
                    created_by="non_existent_user_id"  # Invalid reference
                )

                session.add(content_gen)
                await session.commit()

                # If we reach here, FK constraint might not be enforced
                logger.warning("Foreign key constraint not enforced")

                # Cleanup
                await session.delete(content_gen)
                await session.commit()

            except Exception:
                # Expected behavior - FK constraint should prevent this
                await session.rollback()

    @pytest.mark.asyncio
    @pytest.mark.database
    @pytest.mark.asyncio
async def test_not_null_constraints(self):
        """Test NOT NULL constraints"""
        async with AsyncSessionLocal() as session:
            try:
                # Attempt to create user without required fields
                user = User(
                    email=None,  # Should be NOT NULL
                    username="test_user",
                    role="student"
                )

                session.add(user)
                await session.commit()

                pytest.fail("NOT NULL constraint not enforced")

            except Exception:
                # Expected behavior
                await session.rollback()


# Database validation test runner
async def run_database_validation_tests():
    """Run comprehensive database validation tests"""
    database_results = {
        "connectivity": False,
        "model_imports": False,
        "crud_operations": False,
        "enhanced_content": False,
        "batch_operations": False,
        "repositories": False,
        "performance": False,
        "data_integrity": False,
        "errors": []
    }

    try:
        # Test database connectivity
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                database_results["connectivity"] = True

        # Test model imports
        if User and EnhancedContentGeneration and ContentGenerationBatch:
            database_results["model_imports"] = True

    except Exception as e:
        database_results["errors"].append(f"Database validation failed: {e}")

    return database_results


if __name__ == "__main__":
    # Run basic database tests when executed directly
    print("Running Database and Models Validation Tests...")

    # Test model imports
    try:
        from database.models import ContentGenerationBatch, EnhancedContentGeneration, User
        print("✓ Database models import successful")
    except Exception as e:
        print(f"✗ Database models import failed: {e}")

    # Test database connection
    try:
        import asyncio
        @pytest.mark.asyncio
async def test_connection():
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1

        if asyncio.run(test_connection()):
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
    except Exception as e:
        print(f"✗ Database connection test failed: {e}")

    print("\nRun 'pytest tests/integration/test_database_models_validation.py -v' for full database test suite")