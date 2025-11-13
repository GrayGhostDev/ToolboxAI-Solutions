"""
Modern Database Usage Examples (2025 Standards)

Demonstrates complete usage patterns for SQLAlchemy 2.0 async database layer.

Run with:
    python -m database.examples.usage_examples
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from database.cache_modern import cache_result, redis_cache
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

# Example organization ID for testing
ORG_ID = uuid.uuid4()


async def example_1_create_user_with_profile():
    """
    Example 1: Create user with profile in a single transaction.

    Demonstrates:
    - Transaction management
    - Creating related records
    - Repository pattern
    """
    print("\n=== Example 1: Create User with Profile ===")

    async with db_manager.transaction() as session:
        repo = UserRepository()

        user = await repo.create_user_with_profile(
            session=session,
            organization_id=ORG_ID,
            email="student@example.com",
            username="student123",
            hashed_password="$2b$12$...",  # Pre-hashed password
            full_name="John Student",
            role=UserRole.STUDENT,
            # Profile fields
            bio="Aspiring developer learning Python and databases",
            skills=["Python", "SQL", "FastAPI"],
            interests=["Web Development", "AI", "Data Science"],
        )

        print(f"Created user: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role.value}")
        print(f"  Profile ID: {user.profile.id if user.profile else 'None'}")
        print(f"  Skills: {user.profile.skills if user.profile else []}")


async def example_2_query_users():
    """
    Example 2: Query users with filters and pagination.

    Demonstrates:
    - Repository find method
    - Filtering and ordering
    - Pagination
    """
    print("\n=== Example 2: Query Users ===")

    async with db_manager.session() as session:
        repo = UserRepository()

        # Get all active students
        students = await repo.get_active_users(
            session=session,
            organization_id=ORG_ID,
            role=UserRole.STUDENT,
            skip=0,
            limit=10,
        )

        print(f"Found {len(students)} active students")

        # Advanced filtering with repository
        recent_users = await repo.find(
            session=session,
            filters={
                "organization_id": ORG_ID,
                "status": UserStatus.ACTIVE,
            },
            order_by="created_at",
            descending=True,
            limit=5,
        )

        print(f"Found {len(recent_users)} recent users")
        for user in recent_users:
            print(f"  - {user.email} (created {user.created_at})")


async def example_3_user_authentication():
    """
    Example 3: User authentication and session management.

    Demonstrates:
    - Login tracking
    - Session creation
    - Failed login attempts
    """
    print("\n=== Example 3: User Authentication ===")

    async with db_manager.transaction() as session:
        repo = UserRepository()

        # Get user by email
        user = await repo.get_by_email(
            session=session,
            email="student@example.com",
            organization_id=ORG_ID,
        )

        if user:
            # Record successful login
            user_session = await repo.record_login(
                session=session,
                user_id=user.id,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0...",
                token_jti=str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )

            print(f"Login successful for {user.email}")
            print(f"  Session ID: {user_session.id if user_session else 'None'}")
            print(f"  Last login: {user.last_login_at}")
            print(f"  IP: {user.last_login_ip}")

            # Get active sessions
            sessions = await repo.get_active_sessions(session, user.id)
            print(f"  Active sessions: {len(sessions)}")


async def example_4_create_content():
    """
    Example 4: Create educational content with full-text search.

    Demonstrates:
    - Content creation
    - JSONB metadata
    - Array fields
    - Computed fields (search_vector)
    """
    print("\n=== Example 4: Create Educational Content ===")

    async with db_manager.transaction() as session:
        repo = BaseRepository(EducationalContent)

        content = await repo.create(
            session=session,
            organization_id=ORG_ID,
            title="Introduction to Async Python",
            slug="intro-async-python",
            description="Learn the fundamentals of asynchronous programming in Python",
            content="""
            # Introduction to Async Python

            Asynchronous programming allows you to write concurrent code that can
            handle multiple operations efficiently...

            ## Key Concepts
            - Event Loop
            - Coroutines
            - Tasks
            - Async/Await syntax
            """,
            content_type=ContentType.LESSON,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            status=ContentStatus.PUBLISHED,
            author_id=uuid.uuid4(),
            published_at=datetime.utcnow(),
            tags=["python", "async", "programming"],
            learning_objectives=[
                "Understand async/await syntax",
                "Write asynchronous functions",
                "Use asyncio for concurrent operations",
            ],
            metadata={
                "version": "1.0",
                "language": "en",
                "prerequisite_knowledge": ["Python basics", "Functions"],
            },
            estimated_duration_minutes=45,
        )

        print(f"Created content: {content.id}")
        print(f"  Title: {content.title}")
        print(f"  Type: {content.content_type.value}")
        print(f"  Difficulty: {content.difficulty_level.value}")
        print(f"  Tags: {content.tags}")
        print(f"  Duration: {content.estimated_duration_minutes} minutes")


async def example_5_caching():
    """
    Example 5: Redis caching with decorators.

    Demonstrates:
    - Cache decorators
    - Manual cache operations
    - Cache invalidation
    """
    print("\n=== Example 5: Redis Caching ===")

    # Define cached function
    @cache_result(prefix="user_stats", expire=300)
    async def get_user_stats(org_id: uuid.UUID) -> dict:
        """Get user statistics (expensive query)."""
        async with db_manager.session() as session:
            repo = UserRepository()
            return await repo.get_user_statistics(session, org_id)

    # First call - hits database
    print("First call (cache miss):")
    stats = await get_user_stats(ORG_ID)
    print(f"  Stats: {stats}")

    # Second call - hits cache
    print("Second call (cache hit):")
    stats = await get_user_stats(ORG_ID)
    print(f"  Stats: {stats}")

    # Manual cache operations
    await redis_cache.set("manual_key", {"data": "value"}, expire=60)
    value = await redis_cache.get("manual_key")
    print(f"  Manual cache: {value}")

    # Delete pattern
    deleted = await redis_cache.delete_pattern("user_stats:*")
    print(f"  Deleted {deleted} cache keys")


async def example_6_soft_delete():
    """
    Example 6: Soft delete and restore.

    Demonstrates:
    - Soft delete functionality
    - Restore deleted records
    - Querying with/without deleted records
    """
    print("\n=== Example 6: Soft Delete and Restore ===")

    async with db_manager.transaction() as session:
        repo = UserRepository()

        # Create test user
        user = await repo.create(
            session=session,
            organization_id=ORG_ID,
            email="temp@example.com",
            username="tempuser",
            hashed_password="$2b$12$...",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
        )

        user_id = user.id
        print(f"Created user: {user_id}")

        # Soft delete
        deleted = await repo.delete(
            session=session,
            id=user_id,
            soft=True,
            deleted_by_id=uuid.uuid4(),
        )
        print(f"  Soft deleted: {deleted}")

        # Verify not in normal queries
        user = await repo.get_by_id(session, user_id, include_deleted=False)
        print(f"  Found in normal query: {user is not None}")

        # Find in deleted records
        user = await repo.get_by_id(session, user_id, include_deleted=True)
        print(f"  Found in deleted query: {user is not None}")
        print(f"  Is deleted: {user.is_deleted if user else 'N/A'}")

        # Restore
        if user:
            restored = await repo.restore(session, user_id)
            print(f"  Restored: {restored is not None}")


async def example_7_bulk_operations():
    """
    Example 7: Bulk create and query operations.

    Demonstrates:
    - Bulk inserts
    - Batch processing
    - Performance optimization
    """
    print("\n=== Example 7: Bulk Operations ===")

    async with db_manager.transaction() as session:
        repo = BaseRepository(User)

        # Create multiple users at once
        users_data = [
            {
                "organization_id": ORG_ID,
                "email": f"bulk{i}@example.com",
                "username": f"bulk{i}",
                "hashed_password": "$2b$12$...",
                "role": UserRole.STUDENT,
                "status": UserStatus.ACTIVE,
            }
            for i in range(10)
        ]

        users = await repo.create_many(session, users_data)
        print(f"Created {len(users)} users in bulk")

        # Count total users
        count = await repo.count(session, include_deleted=False)
        print(f"Total active users: {count}")


async def example_8_relationships():
    """
    Example 8: Working with relationships.

    Demonstrates:
    - Eager loading
    - Relationship traversal
    - Cascade operations
    """
    print("\n=== Example 8: Relationships ===")

    async with db_manager.session() as session:
        repo = UserRepository()

        # Get user with profile eagerly loaded
        user = await repo.get_by_email(
            session=session,
            email="student@example.com",
            organization_id=ORG_ID,
        )

        if user and user.profile:
            print(f"User: {user.email}")
            print(f"  Profile bio: {user.profile.bio}")
            print(f"  Profile skills: {user.profile.skills}")

        # Get user with sessions
        sessions = await repo.get_active_sessions(session, user.id)
        print(f"  Active sessions: {len(sessions)}")
        for sess in sessions:
            print(f"    - {sess.ip_address} ({sess.device_type})")


async def example_9_tenant_isolation():
    """
    Example 9: Multi-tenant isolation.

    Demonstrates:
    - Tenant-scoped queries
    - RLS support
    - Cross-tenant prevention
    """
    print("\n=== Example 9: Tenant Isolation ===")

    org1_id = uuid.uuid4()
    org2_id = uuid.uuid4()

    async with db_manager.transaction() as session:
        repo = BaseRepository(User)

        # Create users in different organizations
        user1 = await repo.create(
            session=session,
            organization_id=org1_id,
            email="org1@example.com",
            username="org1user",
            hashed_password="$2b$12$...",
            role=UserRole.STUDENT,
        )

        user2 = await repo.create(
            session=session,
            organization_id=org2_id,
            email="org2@example.com",
            username="org2user",
            hashed_password="$2b$12$...",
            role=UserRole.STUDENT,
        )

        print(f"Created users in different orgs: {user1.id}, {user2.id}")

        # Query with tenant filter
        org1_users = await repo.find(
            session=session,
            filters={"organization_id": org1_id},
        )
        print(f"  Org 1 users: {len(org1_users)}")

        org2_users = await repo.find(
            session=session,
            filters={"organization_id": org2_id},
        )
        print(f"  Org 2 users: {len(org2_users)}")


async def example_10_health_checks():
    """
    Example 10: System health checks.

    Demonstrates:
    - Database connectivity check
    - Redis connectivity check
    - Session cleanup
    """
    print("\n=== Example 10: Health Checks ===")

    # Database health
    db_healthy = await db_manager.health_check()
    print(f"Database healthy: {db_healthy}")

    # Redis health
    redis_healthy = await redis_cache.health_check()
    print(f"Redis healthy: {redis_healthy}")

    # Cleanup expired sessions
    async with db_manager.session() as session:
        repo = UserRepository()
        cleaned = await repo.cleanup_expired_sessions(session)
        print(f"Cleaned {cleaned} expired sessions")


async def run_all_examples():
    """Run all examples in sequence."""
    try:
        await example_1_create_user_with_profile()
        await example_2_query_users()
        await example_3_user_authentication()
        await example_4_create_content()
        await example_5_caching()
        await example_6_soft_delete()
        await example_7_bulk_operations()
        await example_8_relationships()
        await example_9_tenant_isolation()
        await example_10_health_checks()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        await db_manager.close()
        await redis_cache.close()


if __name__ == "__main__":
    asyncio.run(run_all_examples())
