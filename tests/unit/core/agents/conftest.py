"""
Test configuration for Supabase migration agent tests.

This module provides test configuration, fixtures, and utilities
specifically for the Supabase migration system unit tests.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

# Import fixtures from the main supabase migration fixtures
from tests.fixtures.supabase_migration import (
    mock_state_manager,
    mock_openai_client,
    mock_database_config,
    educational_platform_schema,
    sample_access_patterns,
    sample_migration_options,
    sample_table_data,
    mock_migration_plan,
    mock_asyncpg_connection,
    migration_validation_scenarios,
    migration_complexity_scenarios,
    performance_metrics,
    migration_test_helper
)


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external services for unit tests."""
    with patch('openai.AsyncOpenAI') as mock_openai, \
         patch('asyncpg.connect') as mock_asyncpg:

        # Setup OpenAI mock
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(
            return_value=Mock(
                data=[Mock(embedding=[0.1] * 1536) for _ in range(10)]
            )
        )
        mock_openai.return_value = mock_client

        # Setup asyncpg mock
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 1000
        mock_conn.fetch.return_value = []
        mock_conn.fetchrow.return_value = None
        mock_conn.execute.return_value = None
        mock_conn.executemany.return_value = None
        mock_conn.close.return_value = None
        mock_asyncpg.return_value = mock_conn

        yield {
            'openai': mock_openai,
            'asyncpg': mock_asyncpg,
            'openai_client': mock_client,
            'asyncpg_conn': mock_conn
        }


@pytest.fixture
def unit_test_config():
    """Configuration for unit tests."""
    return {
        'test_mode': 'unit',
        'mock_external_apis': True,
        'mock_database_connections': True,
        'enable_logging': False,
        'timeout_seconds': 30
    }


# Add custom markers for the test suite
def pytest_configure(config):
    """Configure pytest with custom markers for Supabase migration tests."""
    config.addinivalue_line(
        "markers",
        "supabase: mark test as a Supabase migration test"
    )
    config.addinivalue_line(
        "markers",
        "schema_analysis: mark test as schema analysis test"
    )
    config.addinivalue_line(
        "markers",
        "rls_policy: mark test as RLS policy test"
    )
    config.addinivalue_line(
        "markers",
        "data_migration: mark test as data migration test"
    )
    config.addinivalue_line(
        "markers",
        "migration_agent: mark test as migration agent test"
    )


# Ensure all tests run with event loop
@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()