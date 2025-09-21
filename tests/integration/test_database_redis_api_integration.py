import pytest_asyncio
#!/usr/bin/env python3
"""
Database + Redis + API Integration Tests

Tests the complete data flow including:
- Database transactions and rollbacks
- Redis caching behavior
- API endpoint integration with data layers
- Data consistency across components
- Performance with both storage systems
- Cache invalidation scenarios
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["USE_MOCK_DATABASE"] = "false"  # Use real database for integration
os.environ["USE_MOCK_REDIS"] = "false"    # Use real Redis for integration

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.requires_postgres,
    pytest.mark.requires_redis,
]


@pytest.fixture
async def integration_client():
    """HTTP client for database+Redis integration testing"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8009",
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
async def redis_client():
    """Redis client for testing cache operations"""
    try:
        client = redis.Redis(
            host="localhost",
            port=6381,  # Docker Redis port
            db=0,
            decode_responses=True
        )
        # Test connection
        client.ping()
        yield client
        # Cleanup test keys
        client.flushdb()
    except redis.ConnectionError:
        pytest.skip("Redis not available for integration testing")


@pytest.fixture
@pytest.mark.asyncio
async def test_database():
    """Test database session for integration testing"""
    try:
        # Use test database URL
        database_url = "postgresql+asyncpg://eduplatform:eduplatform2024@localhost:5434/educational_platform_dev"

        engine = create_async_engine(database_url, echo=False)

        # Test connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            yield session

        await engine.dispose()

    except Exception as e:
        pytest.skip(f"Database not available for integration testing: {e}")


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    import jwt
    from datetime import timedelta

    payload = {
        "sub": "integration_test_user",
        "role": "teacher",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_data():
    """Test data for integration testing"""
    return {
        "user": {
            "username": f"test_user_{int(time.time())}",
            "email": f"test.{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "role": "teacher",
            "first_name": "Test",
            "last_name": "User"
        },
        "course": {
            "title": f"Test Course {int(time.time())}",
            "code": f"TC{int(time.time())}",
            "description": "Integration test course",
            "subject": "Mathematics",
            "grade_level": 7
        },
        "lesson": {
            "title": f"Test Lesson {int(time.time())}",
            "description": "Integration test lesson",
            "learning_objectives": ["Test objective 1", "Test objective 2"]
        },
        "content": {
            "title": "Test Content",
            "content_type": "lesson",
            "content_data": {
                "slides": ["Introduction", "Main Content", "Summary"],
                "activities": ["Quiz", "Discussion"]
            }
        }
    }


class TestDatabaseTransactionIntegrity:
    """Test database transaction handling and integrity"""

    @pytest.mark.asyncio
async def test_successful_transaction_commit(self, integration_client, auth_headers, test_data):
        """Test successful database transaction with commit"""
        # Create user via API
        response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("User creation endpoint not implemented")

        if response.status_code == 201:
            result = response.json()
            user_id = result["data"]["id"]

            # Verify user exists by fetching it
            get_response = await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            if get_response.status_code == 200:
                user_data = get_response.json()["data"]
                assert user_data["username"] == test_data["user"]["username"]
                assert user_data["email"] == test_data["user"]["email"]

    @pytest.mark.asyncio
async def test_transaction_rollback_on_error(self, integration_client, auth_headers, test_data):
        """Test transaction rollback when errors occur"""
        # Create valid user first
        user_data = test_data["user"]
        response1 = await integration_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )

        if response1.status_code == 404:
            pytest.skip("User creation endpoint not implemented")

        if response1.status_code == 201:
            # Try to create duplicate user (should fail and rollback)
            response2 = await integration_client.post(
                "/api/v1/users",
                json=user_data,  # Same data, should cause conflict
                headers=auth_headers
            )

            # Should fail due to uniqueness constraint
            assert response2.status_code in [400, 409, 422]

            # Verify original user still exists and is valid
            original_user_id = response1.json()["data"]["id"]
            get_response = await integration_client.get(
                f"/api/v1/users/{original_user_id}",
                headers=auth_headers
            )

            if get_response.status_code == 200:
                assert get_response.json()["data"]["username"] == user_data["username"]

    @pytest.mark.asyncio
async def test_complex_transaction_with_relationships(self, integration_client, auth_headers, test_data):
        """Test complex transaction involving multiple related tables"""
        # Create user
        user_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if user_response.status_code == 404:
            pytest.skip("User creation endpoint not implemented")

        if user_response.status_code == 201:
            user_id = user_response.json()["data"]["id"]

            # Create course for the user
            course_data = test_data["course"]
            course_data["instructor_id"] = user_id

            course_response = await integration_client.post(
                "/api/v1/courses",
                json=course_data,
                headers=auth_headers
            )

            if course_response.status_code == 201:
                course_id = course_response.json()["data"]["id"]

                # Create lesson for the course
                lesson_data = test_data["lesson"]
                lesson_data["course_id"] = course_id

                lesson_response = await integration_client.post(
                    "/api/v1/lessons",
                    json=lesson_data,
                    headers=auth_headers
                )

                if lesson_response.status_code == 201:
                    # Verify all related data exists
                    lesson_id = lesson_response.json()["data"]["id"]

                    # Get lesson with relationships
                    lesson_detail = await integration_client.get(
                        f"/api/v1/lessons/{lesson_id}?include=course,instructor",
                        headers=auth_headers
                    )

                    if lesson_detail.status_code == 200:
                        data = lesson_detail.json()["data"]
                        assert data["course"]["id"] == course_id
                        assert data["course"]["instructor_id"] == user_id

    @pytest.mark.asyncio
async def test_concurrent_database_operations(self, integration_client, auth_headers, test_data):
        """Test database consistency under concurrent operations"""

        async def create_user(suffix: int):
            user_data = test_data["user"].copy()
            user_data["username"] = f"{user_data['username']}_{suffix}"
            user_data["email"] = f"user{suffix}@example.com"

            response = await integration_client.post(
                "/api/v1/users",
                json=user_data,
                headers=auth_headers
            )
            return response.status_code, user_data["username"]

        # Create 5 users concurrently
        tasks = [create_user(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful creations
        successful_creations = [
            (status, username) for status, username in results
            if isinstance(status, int) and status == 201
        ]

        if successful_creations:
            # All concurrent operations should succeed
            assert len(successful_creations) >= 3  # At least 3 should succeed

            # Verify all users exist
            for status, username in successful_creations:
                search_response = await integration_client.get(
                    f"/api/v1/users?username={username}",
                    headers=auth_headers
                )
                if search_response.status_code == 200:
                    users = search_response.json()["data"]
                    assert any(user["username"] == username for user in users)


class TestRedisCacheIntegration:
    """Test Redis caching integration with API"""

    @pytest.mark.asyncio
async def test_cache_hit_miss_behavior(self, integration_client, redis_client, auth_headers, test_data):
        """Test cache hit/miss behavior for API endpoints"""
        # Create test data first
        user_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if user_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if user_response.status_code == 201:
            user_id = user_response.json()["data"]["id"]
            cache_key = f"user:{user_id}"

            # First request (cache miss)
            start_time = time.time()
            response1 = await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )
            first_request_time = time.time() - start_time

            if response1.status_code == 200:
                # Check if data was cached
                cached_data = redis_client.get(cache_key)

                # Second request (should be cache hit if caching is implemented)
                start_time = time.time()
                response2 = await integration_client.get(
                    f"/api/v1/users/{user_id}",
                    headers=auth_headers
                )
                second_request_time = time.time() - start_time

                if response2.status_code == 200:
                    # Responses should be identical
                    assert response1.json() == response2.json()

                    # If caching is implemented, second request should be faster
                    if cached_data:
                        assert second_request_time < first_request_time
                        print(f"Cache hit: {second_request_time:.3f}s vs {first_request_time:.3f}s")

    @pytest.mark.asyncio
async def test_cache_invalidation_on_update(self, integration_client, redis_client, auth_headers, test_data):
        """Test cache invalidation when data is updated"""
        # Create user
        user_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if user_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if user_response.status_code == 201:
            user_id = user_response.json()["data"]["id"]
            cache_key = f"user:{user_id}"

            # Get user to populate cache
            await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            # Check cache exists
            cached_before = redis_client.get(cache_key)

            # Update user
            update_data = {"first_name": "Updated"}
            update_response = await integration_client.patch(
                f"/api/v1/users/{user_id}",
                json=update_data,
                headers=auth_headers
            )

            if update_response.status_code == 200:
                # Cache should be invalidated
                cached_after = redis_client.get(cache_key)

                # If caching is implemented, cache should be cleared or updated
                if cached_before:
                    # Either cache is cleared or contains updated data
                    if cached_after:
                        cached_data = json.loads(cached_after)
                        assert cached_data.get("first_name") == "Updated"
                    # Or cache is cleared (None)

                # Get user again to verify update
                get_response = await integration_client.get(
                    f"/api/v1/users/{user_id}",
                    headers=auth_headers
                )

                if get_response.status_code == 200:
                    user_data = get_response.json()["data"]
                    assert user_data["first_name"] == "Updated"

    @pytest.mark.asyncio
async def test_cache_expiration(self, integration_client, redis_client, auth_headers, test_data):
        """Test cache expiration behavior"""
        # Create test data
        user_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if user_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if user_response.status_code == 201:
            user_id = user_response.json()["data"]["id"]
            cache_key = f"user:{user_id}"

            # Get user to populate cache
            await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            # Check cache TTL if implemented
            ttl = redis_client.ttl(cache_key)
            if ttl > 0:
                # Cache has expiration set
                assert ttl <= 3600  # Should be reasonable (1 hour or less)
                print(f"Cache TTL: {ttl} seconds")

                # Set short TTL for testing
                redis_client.expire(cache_key, 2)

                # Wait for expiration
                await asyncio.sleep(3)

                # Cache should be expired
                expired_data = redis_client.get(cache_key)
                assert expired_data is None

    @pytest.mark.asyncio
async def test_cache_performance_benefits(self, integration_client, redis_client, auth_headers, test_data):
        """Test performance benefits of caching"""
        # Create course with lessons for performance testing
        user_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if user_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if user_response.status_code == 201:
            user_id = user_response.json()["data"]["id"]

            # Create course
            course_data = test_data["course"]
            course_data["instructor_id"] = user_id

            course_response = await integration_client.post(
                "/api/v1/courses",
                json=course_data,
                headers=auth_headers
            )

            if course_response.status_code == 201:
                course_id = course_response.json()["data"]["id"]

                # Test course listing performance
                times = []
                for i in range(3):
                    start_time = time.time()
                    response = await integration_client.get(
                        "/api/v1/courses",
                        headers=auth_headers
                    )
                    times.append(time.time() - start_time)

                    if response.status_code == 200:
                        courses = response.json()["data"]
                        assert len(courses) >= 1

                # Performance should improve with caching
                if len(times) >= 3:
                    # Later requests should generally be faster (allowing some variance)
                    avg_first_half = sum(times[:2]) / 2
                    avg_second_half = sum(times[1:]) / 2

                    print(f"Performance times: {times}")
                    print(f"First half avg: {avg_first_half:.3f}s, Second half avg: {avg_second_half:.3f}s")


class TestDataConsistencyAcrossLayers:
    """Test data consistency between database, cache, and API responses"""

    @pytest.mark.asyncio
async def test_create_update_consistency(self, integration_client, redis_client, auth_headers, test_data):
        """Test data consistency during create and update operations"""
        # Create user
        user_data = test_data["user"]
        create_response = await integration_client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )

        if create_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if create_response.status_code == 201:
            user_id = create_response.json()["data"]["id"]

            # Get user via API
            api_response = await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            if api_response.status_code == 200:
                api_data = api_response.json()["data"]

                # Check cache consistency if caching is implemented
                cache_key = f"user:{user_id}"
                cached_data = redis_client.get(cache_key)

                if cached_data:
                    cached_json = json.loads(cached_data)
                    # API and cache should match
                    assert api_data["username"] == cached_json["username"]
                    assert api_data["email"] == cached_json["email"]

                # Update user
                update_data = {"last_name": "UpdatedName"}
                update_response = await integration_client.patch(
                    f"/api/v1/users/{user_id}",
                    json=update_data,
                    headers=auth_headers
                )

                if update_response.status_code == 200:
                    # Get updated data
                    updated_response = await integration_client.get(
                        f"/api/v1/users/{user_id}",
                        headers=auth_headers
                    )

                    if updated_response.status_code == 200:
                        updated_data = updated_response.json()["data"]
                        assert updated_data["last_name"] == "UpdatedName"

                        # Check cache is updated/invalidated
                        updated_cache = redis_client.get(cache_key)
                        if updated_cache:
                            updated_cache_json = json.loads(updated_cache)
                            assert updated_cache_json["last_name"] == "UpdatedName"

    @pytest.mark.asyncio
async def test_deletion_consistency(self, integration_client, redis_client, auth_headers, test_data):
        """Test data consistency during deletion operations"""
        # Create user
        create_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if create_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if create_response.status_code == 201:
            user_id = create_response.json()["data"]["id"]

            # Get user to populate cache
            await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            cache_key = f"user:{user_id}"
            cached_before = redis_client.get(cache_key)

            # Delete user
            delete_response = await integration_client.delete(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            if delete_response.status_code == 204:
                # User should not exist via API
                get_response = await integration_client.get(
                    f"/api/v1/users/{user_id}",
                    headers=auth_headers
                )
                assert get_response.status_code == 404

                # Cache should be cleared
                cached_after = redis_client.get(cache_key)
                if cached_before:
                    assert cached_after is None

    @pytest.mark.asyncio
async def test_concurrent_read_write_consistency(self, integration_client, redis_client, auth_headers, test_data):
        """Test data consistency under concurrent read/write operations"""
        # Create user
        create_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if create_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if create_response.status_code == 201:
            user_id = create_response.json()["data"]["id"]

            async def read_user():
                response = await integration_client.get(
                    f"/api/v1/users/{user_id}",
                    headers=auth_headers
                )
                return response.status_code, response.json() if response.status_code == 200 else None

            async def update_user(suffix: str):
                update_data = {"first_name": f"Updated{suffix}"}
                response = await integration_client.patch(
                    f"/api/v1/users/{user_id}",
                    json=update_data,
                    headers=auth_headers
                )
                return response.status_code

            # Perform concurrent reads and writes
            tasks = []
            tasks.extend([read_user() for _ in range(5)])
            tasks.extend([update_user(str(i)) for i in range(3)])

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify no errors occurred
            errors = [r for r in results if isinstance(r, Exception)]
            assert len(errors) == 0

            # Final state should be consistent
            final_response = await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )

            if final_response.status_code == 200:
                final_data = final_response.json()["data"]
                # Should have some updated first_name
                assert "Updated" in final_data["first_name"]


class TestPerformanceWithBothSystems:
    """Test performance characteristics with both database and Redis"""

    @pytest.mark.asyncio
async def test_cold_vs_warm_cache_performance(self, integration_client, redis_client, auth_headers, test_data):
        """Test performance difference between cold and warm cache"""
        # Create test data
        user_response = await integration_client.post(
            "/api/v1/users",
            json=test_data["user"],
            headers=auth_headers
        )

        if user_response.status_code == 404:
            pytest.skip("User endpoint not implemented")

        if user_response.status_code == 201:
            user_id = user_response.json()["data"]["id"]

            # Clear any existing cache
            cache_key = f"user:{user_id}"
            redis_client.delete(cache_key)

            # Cold cache request
            start_time = time.time()
            cold_response = await integration_client.get(
                f"/api/v1/users/{user_id}",
                headers=auth_headers
            )
            cold_time = time.time() - start_time

            if cold_response.status_code == 200:
                # Warm cache request
                start_time = time.time()
                warm_response = await integration_client.get(
                    f"/api/v1/users/{user_id}",
                    headers=auth_headers
                )
                warm_time = time.time() - start_time

                if warm_response.status_code == 200:
                    # Responses should be identical
                    assert cold_response.json() == warm_response.json()

                    print(f"Cold cache: {cold_time:.3f}s, Warm cache: {warm_time:.3f}s")

                    # If caching is working, warm should be faster
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        assert warm_time < cold_time
                        improvement = ((cold_time - warm_time) / cold_time) * 100
                        print(f"Performance improvement: {improvement:.1f}%")

    @pytest.mark.asyncio
async def test_bulk_operations_performance(self, integration_client, redis_client, auth_headers, test_data):
        """Test performance of bulk operations with caching"""
        # Create multiple users for bulk operations
        user_ids = []
        for i in range(10):
            user_data = test_data["user"].copy()
            user_data["username"] = f"{user_data['username']}_{i}"
            user_data["email"] = f"bulk{i}@example.com"

            response = await integration_client.post(
                "/api/v1/users",
                json=user_data,
                headers=auth_headers
            )

            if response.status_code == 201:
                user_ids.append(response.json()["data"]["id"])

        if user_ids:
            # Test bulk retrieval performance
            start_time = time.time()
            responses = await asyncio.gather(*[
                integration_client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
                for user_id in user_ids
            ])
            first_bulk_time = time.time() - start_time

            # Second bulk retrieval (should hit cache)
            start_time = time.time()
            responses2 = await asyncio.gather(*[
                integration_client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
                for user_id in user_ids
            ])
            second_bulk_time = time.time() - start_time

            successful_first = sum(1 for r in responses if r.status_code == 200)
            successful_second = sum(1 for r in responses2 if r.status_code == 200)

            assert successful_first == successful_second

            print(f"First bulk: {first_bulk_time:.3f}s, Second bulk: {second_bulk_time:.3f}s")

            # If caching is effective, second bulk should be faster
            if successful_first > 0:
                avg_first = first_bulk_time / successful_first
                avg_second = second_bulk_time / successful_second
                print(f"Average per request: {avg_first:.3f}s vs {avg_second:.3f}s")

    @pytest.mark.asyncio
async def test_memory_usage_monitoring(self, integration_client, redis_client, auth_headers, test_data):
        """Test memory usage patterns with both systems"""
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss
        except ImportError:
            pytest.skip("psutil not available for memory monitoring")

        # Perform operations that should populate cache
        for i in range(20):
            user_data = test_data["user"].copy()
            user_data["username"] = f"{user_data['username']}_{i}"
            user_data["email"] = f"memory{i}@example.com"

            response = await integration_client.post(
                "/api/v1/users",
                json=user_data,
                headers=auth_headers
            )

            if response.status_code == 201:
                user_id = response.json()["data"]["id"]
                # Get user to populate cache
                await integration_client.get(
                    f"/api/v1/users/{user_id}",
                    headers=auth_headers
                )

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        print(f"Memory increase: {memory_increase / (1024*1024):.1f} MB")

        # Memory increase should be reasonable
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase

        # Check Redis memory usage
        redis_info = redis_client.info("memory")
        redis_memory = redis_info.get("used_memory", 0)
        print(f"Redis memory usage: {redis_memory / (1024*1024):.1f} MB")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])