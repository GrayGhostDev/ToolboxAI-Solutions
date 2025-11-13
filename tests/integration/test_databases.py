from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


import asyncio
import os
from datetime import datetime

import asyncpg
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable",
)


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.asyncio
async def test_databases():
    """Test all database connections with real queries"""

    # Use environment variables with fallback to standard CI credentials
    db_user = os.environ.get("DB_USER", "eduplatform")
    db_password = os.environ.get("DB_PASSWORD", "eduplatform2024")
    db_host = os.environ.get("DB_HOST", "localhost")

    databases = {
        "ghost_backend": f"postgresql://{db_user}:{db_password}@{db_host}/ghost_backend",
        "educational_platform": f"postgresql://{db_user}:{db_password}@{db_host}/educational_platform_dev",
        "roblox_data": f"postgresql://{db_user}:{db_password}@{db_host}/roblox_data",
        "mcp_memory": f"postgresql://{db_user}:{db_password}@{db_host}/mcp_memory",
    }

    results = {}

    for db_name, connection_string in databases.items():
        try:
            conn = await asyncpg.connect(connection_string)

            # Test basic connectivity
            version = await conn.fetchval("SELECT version()")

            # Get table count
            table_count = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
            )

            # Get row counts for key tables
            row_counts = {}
            if db_name == "educational_platform":
                try:
                    row_counts["users"] = await conn.fetchval("SELECT COUNT(*) FROM users")
                except:
                    row_counts["users"] = "Table not found"
                try:
                    row_counts["lessons"] = await conn.fetchval("SELECT COUNT(*) FROM lessons")
                except:
                    row_counts["lessons"] = "Table not found"
                try:
                    row_counts["classes"] = await conn.fetchval("SELECT COUNT(*) FROM classes")
                except:
                    row_counts["classes"] = "Table not found"

            await conn.close()

            results[db_name] = {
                "status": "✅ Connected",
                "tables": table_count,
                "row_counts": row_counts,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            results[db_name] = {"status": f"❌ Failed", "error": str(e)}

    return results


# Run the test
results = asyncio.run(test_databases())
for db, info in results.items():
    print(f"\n{db}:")
    for key, value in info.items():
        print(f"  {key}: {value}")
