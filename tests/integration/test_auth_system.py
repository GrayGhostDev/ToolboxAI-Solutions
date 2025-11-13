from unittest.mock import Mock, patch

import pytest
import pytest_asyncio


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


#!/usr/bin/env python3
"""
Test authentication system with real database users
"""

import asyncio
import os
from datetime import datetime

import httpx
import psycopg2
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable",
)


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_authentication_with_real_users():
    """Test authentication using real users from database"""

    print("🔐 Testing Authentication System with Real Users")
    print("=" * 60)

    # Connect to database to verify users exist
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="educational_platform_dev",
            user="eduplatform",
            password="eduplatform2024",
        )
        cur = conn.cursor()

        # Get real users from database
        cur.execute(
            """
            SELECT username, email, role
            FROM users
            WHERE is_active = true
            LIMIT 5
        """
        )
        users = cur.fetchall()

        print(f"✅ Found {len(users)} active users in database:")
        for username, email, role in users:
            print(f"   - {username} ({email}) - Role: {role}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # Test authentication endpoint
    base_url = "http://127.0.0.1:8008"

    async with httpx.AsyncClient() as client:
        # Test with different user credentials
        test_credentials = [
            {"username": "john_teacher", "password": "Teacher123!"},
            {"username": "alice_student", "password": "Student123!"},
            {"username": "admin", "password": "Admin123!"},
        ]

        print("\n🔍 Testing login endpoint:")
        for creds in test_credentials:
            try:
                # Try login endpoint
                response = await client.post(f"{base_url}/auth/login", json=creds)

                if response.status_code == 200:
                    print(f"  ✅ Login successful for {creds['username']}")
                    token = response.json().get("access_token")
                    print(f"     Token: {token[:50]}...")
                elif response.status_code == 404:
                    print(f"  ⚠️  Login endpoint not found - trying /login")
                    # Try alternative endpoint
                    response = await client.post(f"{base_url}/login", json=creds)
                    if response.status_code == 200:
                        print(f"  ✅ Login successful for {creds['username']} on /login")
                    else:
                        print(f"  ❌ Login failed for {creds['username']}: {response.status_code}")
                else:
                    print(f"  ❌ Login failed for {creds['username']}: {response.status_code}")
                    if response.text:
                        print(f"     Response: {response.text[:200]}")

            except Exception as e:
                print(f"  ❌ Error testing {creds['username']}: {e}")

        # Test token generation directly
        print("\n🔍 Testing direct token generation:")
        try:
            from apps.backend.api.auth.auth import create_user_token
            from apps.backend.models.schemas import User

            # Create test user
            test_user = User(
                id="test-id", username="john_teacher", email="john@teacher.com", role="teacher"
            )

            token = create_user_token(test_user)
            print(f"  ✅ Token generated successfully")
            print(f"     Token: {token[:50]}...")

            # Test using the token
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{base_url}/health", headers=headers)

            if response.status_code == 200:
                print(f"  ✅ Token validated successfully")
            else:
                print(f"  ❌ Token validation failed: {response.status_code}")

        except Exception as e:
            print(f"  ❌ Error generating token: {e}")

    return True


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_protected_endpoints():
    """Test protected endpoints with authentication"""

    print("\n🔒 Testing Protected Endpoints")
    print("=" * 60)

    base_url = "http://127.0.0.1:8008"

    # Generate a test token
    from apps.backend.api.auth.auth import create_user_token
    from apps.backend.models.schemas import User

    test_user = User(
        id="teacher-123", username="test_teacher", email="test@teacher.com", role="teacher"
    )

    token = create_user_token(test_user)

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        # Test various protected endpoints
        endpoints = [
            (
                "/generate_content",
                "POST",
                {
                    "subject": "Science",
                    "grade_level": 7,
                    "learning_objectives": ["Solar System"],
                    "environment_type": "space_station",
                },
            ),
            (
                "/quiz/generate",
                "POST",
                {
                    "subject": "Science",
                    "topic": "Solar System",
                    "num_questions": 5,
                    "difficulty": "medium",
                },
            ),
            ("/analytics", "GET", None),
        ]

        for endpoint, method, data in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{base_url}{endpoint}", headers=headers)
                else:
                    response = await client.post(
                        f"{base_url}{endpoint}", json=data, headers=headers, timeout=10.0
                    )

                if response.status_code == 200:
                    print(f"  ✅ {method} {endpoint} - Success")
                elif response.status_code == 404:
                    print(f"  ⚠️  {method} {endpoint} - Not found")
                elif response.status_code == 401:
                    print(f"  🔒 {method} {endpoint} - Unauthorized (auth working)")
                elif response.status_code == 422:
                    print(f"  ⚠️  {method} {endpoint} - Validation error")
                else:
                    print(f"  ❌ {method} {endpoint} - Status: {response.status_code}")

            except Exception as e:
                print(f"  ❌ {method} {endpoint} - Error: {e}")

    return True


async def main():
    """Run all authentication tests"""
    await test_authentication_with_real_users()
    await test_protected_endpoints()
    print("\n✅ Authentication testing completed")


if __name__ == "__main__":
    # Ensure server modules are importable
    import sys

    sys.path.insert(0, "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")

    asyncio.run(main())
