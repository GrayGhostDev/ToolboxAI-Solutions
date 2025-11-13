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
Test Database Connection Pool Configuration
Tests SQLAlchemy 2.0 and PostgreSQL 16+ optimizations (2025 best practices)
"""

import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from database.connection_manager import (
    cleanup_databases,
    db_manager,
    get_async_session,
    get_session,
    health_check,
    initialize_databases,
)
from database.core.pool_config import (
    PoolConfig,
    PoolConfigFactory,
    PoolMonitor,
    PoolStrategy,
    get_database_pool_config,
)
from tests.test_logger import TestLogger

# Initialize test logger
logger = TestLogger(__name__, "integration")


class TestDatabasePool2025:
    """Test database connection pool with 2025 best practices"""

    def setup_method(self, method=None):
        """Setup for each test"""
        test_name = method.__name__ if method else "test"
        logger.start_test(test_name)
        # Reset database manager
        db_manager.close_all()
        db_manager._initialized = False

    def teardown_method(self, method=None):
        """Teardown for each test"""
        test_name = method.__name__ if method else "test"
        # Cleanup
        db_manager.close_all()
        logger.end_test(test_name, "completed")

    def test_pool_config_creation(self):
        """Test that pool configurations follow 2025 best practices"""
        logger.logger.info("Testing pool configuration creation")

        # Test production configuration
        prod_config = PoolConfigFactory.create_config(
            strategy=PoolStrategy.OPTIMIZED,
            environment="production"
        )

        # Verify SQLAlchemy 2.0 settings
        assert prod_config.pool_pre_ping == True, "Pre-ping should be enabled for cloud databases"
        assert prod_config.use_lifo == True, "LIFO should be enabled for better connection reuse"
        assert prod_config.connect_args is not None, "Should have connection args"

        # Verify PostgreSQL 16+ settings
        assert prod_config.pg_lock_timeout == 10000, "Lock timeout should be set"
        assert prod_config.pg_idle_in_transaction_timeout == 60000, "Idle transaction timeout should be set"
        assert prod_config.prepared_statement_cache_size == 512, "Prepared statement cache should be configured"
        assert prod_config.jit == "off", "JIT should be disabled for consistent performance"

        # Verify monitoring settings
        assert prod_config.enable_pool_events == True, "Pool events should be enabled for monitoring"
        assert prod_config.slow_query_threshold == 1.0, "Slow query threshold should be set"

        logger.logger.info("✅ Pool configuration follows 2025 best practices")

    def test_engine_kwargs_generation(self):
        """Test that engine kwargs are properly generated for SQLAlchemy 2.0"""
        logger.logger.info("Testing engine kwargs generation")

        config = get_database_pool_config(environment="production")

        # Test sync engine kwargs
        sync_kwargs = config.to_engine_kwargs()

        assert "pool_size" in sync_kwargs
        assert "pool_recycle" in sync_kwargs
        assert "connect_args" in sync_kwargs
        assert "execution_options" in sync_kwargs

        # Verify PostgreSQL settings are in options string
        connect_args = sync_kwargs["connect_args"]
        assert "options" in connect_args
        options = connect_args["options"]
        assert "statement_timeout" in options
        assert "lock_timeout" in options or prod_config.pg_lock_timeout > 0
        assert prod_config.pg_idle_in_transaction_timeout > 0
        assert "application_name=toolboxai" in options

        # Verify execution options
        exec_opts = sync_kwargs["execution_options"]
        assert exec_opts["isolation_level"] == "READ COMMITTED"
        assert "max_row_buffer" in exec_opts

        logger.logger.info("✅ Engine kwargs properly configured for SQLAlchemy 2.0")

    def test_async_engine_kwargs_generation(self):
        """Test async engine kwargs for asyncpg driver"""
        logger.logger.info("Testing async engine kwargs generation")

        config = get_database_pool_config(environment="production")
        async_kwargs = config.to_async_engine_kwargs()

        # Verify pool settings
        assert "pool_size" in async_kwargs
        assert "max_overflow" in async_kwargs
        assert "pool_pre_ping" in async_kwargs

        # Verify asyncpg specific settings in connect_args
        connect_args = async_kwargs["connect_args"]
        assert "server_settings" in connect_args
        assert "statement_cache_size" in connect_args
        assert "max_cached_statement_lifetime" in connect_args
        assert "timeout" in connect_args
        assert "command_timeout" in connect_args

        # Verify server settings format for asyncpg
        server_settings = connect_args["server_settings"]
        assert "application_name" in server_settings
        assert "statement_timeout" in server_settings
        assert server_settings["statement_timeout"].endswith("ms")  # Should be in milliseconds format

        logger.logger.info("✅ Async engine kwargs properly configured for asyncpg")

    def test_database_initialization(self):
        """Test database initialization with new pool configuration"""
        logger.logger.info("Testing database initialization")

        # Initialize databases
        initialize_databases()

        # Verify pools are created
        assert "educational_platform" in db_manager.pools
        assert "educational_platform" in db_manager.configs

        # Run health check
        results = health_check()

        # Check that pool information is included
        for db_name in ["education", "ghost", "roblox"]:
            key = f"postgresql_{db_name}"
            if key in results and isinstance(results[key], dict):
                if results[key].get("healthy"):
                    assert "pool" in results[key], f"Pool status should be included for {db_name}"

        logger.logger.info("✅ Database initialization successful with pool monitoring")

    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_connection_pool_monitoring(self):
        """Test that pool monitoring events are working"""
        logger.logger.info("Testing connection pool monitoring")

        # Initialize databases
        initialize_databases()

        # Get initial metrics from the monitor
        monitor = db_manager.monitor
        initial_checkouts = monitor.metrics.get("checkout_count", 0)

        # Perform some database operations using async session
        async for session in get_async_session("educational_platform"):
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            break

        # Check that metrics were updated
        final_checkouts = monitor.metrics.get("checkout_count", 0)
        assert final_checkouts >= initial_checkouts, "Checkout count should not decrease"

        logger.logger.info(f"✅ Pool monitoring active: {final_checkouts - initial_checkouts} checkouts tracked")

    def test_pool_optimization_calculator(self):
        """Test pool optimization calculations"""
        logger.logger.info("Testing pool optimization calculator")

        config = get_database_pool_config(environment="production")
        monitor = PoolMonitor(config)

        # Test optimization calculations
        recommendations = monitor.calculate_optimal_size(
            concurrent_requests=100,
            avg_query_time=0.05  # 50ms average query time
        )

        assert "pool_size" in recommendations
        assert "max_overflow" in recommendations
        assert "total_connections" in recommendations

        # Verify recommendations are reasonable
        assert 5 <= recommendations["pool_size"] <= 100
        assert recommendations["max_overflow"] > 0
        assert recommendations["total_connections"] == recommendations["pool_size"] + recommendations["max_overflow"]

        logger.logger.info(f"✅ Pool optimization calculator working: recommended size {recommendations['pool_size']}")

    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_async_connection_pool(self):
        """Test async connection pool with asyncpg"""
        logger.logger.info("Testing async connection pool")

        # Initialize databases
        initialize_databases()

        # Test async session using async generator
        async for session in get_async_session("education"):
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            break  # Only need one iteration

        logger.logger.info("✅ Async connection pool working with asyncpg")

    def test_connection_pool_stress(self):
        """Stress test the connection pool with concurrent connections"""
        logger.logger.info("Starting connection pool stress test")

        # Initialize databases
        initialize_databases()

        def perform_query(i: int):
            """Perform a simple query"""
            with get_session("education") as session:
                result = session.execute(text(f"SELECT {i}"))
                return result.scalar()

        # Test with concurrent connections
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_query, i) for i in range(20)]
            results = []

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except Exception as e:
                    logger.logger.error(f"Query failed: {e}")

        # Verify all queries completed
        assert len(results) == 20, f"Expected 20 results, got {len(results)}"

        # Check pool metrics
        monitor = db_manager.pool_monitors.get("education")
        if monitor:
            metrics = monitor.metrics
            logger.logger.info(f"Pool metrics after stress test:")
            logger.logger.info(f"  - Connections created: {metrics.get('connections_created', 0)}")
            logger.logger.info(f"  - Total checkouts: {metrics.get('checkout_count', 0)}")
            logger.logger.info(f"  - Connection errors: {metrics.get('connection_errors', 0)}")

            # Get recommendations based on metrics
            recommendations = monitor.get_recommendations()
            if recommendations["recommendations"]:
                logger.logger.warning("Pool optimization recommendations:")
                for rec in recommendations["recommendations"]:
                    logger.logger.warning(f"  - {rec['issue']}: {rec['suggestion']}")

        logger.logger.info("✅ Connection pool stress test completed")

    def test_pool_recycle_and_timeout(self):
        """Test pool recycle and timeout settings"""
        logger.logger.info("Testing pool recycle and timeout settings")

        config = get_database_pool_config(environment="production")

        # Verify recycle time is appropriate for cloud databases
        assert config.pool_recycle <= 1800, "Pool recycle should be 30 minutes or less for cloud databases"

        # Verify timeout settings are reasonable
        assert config.pool_timeout >= 10, "Pool timeout should be at least 10 seconds"
        assert config.connect_timeout >= 5, "Connect timeout should be at least 5 seconds"

        logger.logger.info("✅ Pool recycle and timeout settings are appropriate")


if __name__ == "__main__":
    # Run tests
    test = TestDatabasePool2025()

    # List of test methods
    test_methods = [
        test.test_pool_config_creation,
        test.test_engine_kwargs_generation,
        test.test_async_engine_kwargs_generation,
        test.test_database_initialization,
        test.test_connection_pool_monitoring,
        test.test_pool_optimization_calculator,
        test.test_connection_pool_stress,
        test.test_pool_recycle_and_timeout,
    ]

    failed_tests = []

    for test_method in test_methods:
        try:
            # Setup
            test.setup_method(test_method)

            # Run test
            if asyncio.iscoroutinefunction(test_method):
                asyncio.run(test_method())
            else:
                test_method()

            print(f"✅ {test_method.__name__} passed")

        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed_tests.append(test_method.__name__)
        finally:
            # Teardown
            test.teardown_method(test_method)

    # Run async test separately
    try:
        test.setup_method(test.test_async_connection_pool)
        asyncio.run(test.test_async_connection_pool())
        print(f"✅ test_async_connection_pool passed")
    except Exception as e:
        print(f"❌ test_async_connection_pool failed: {e}")
        failed_tests.append("test_async_connection_pool")
    finally:
        test.teardown_method(test.test_async_connection_pool)

    # Generate report
    logger.generate_report()

    # Summary
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} tests failed: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        print("\n✅ All database pool tests passed!")
