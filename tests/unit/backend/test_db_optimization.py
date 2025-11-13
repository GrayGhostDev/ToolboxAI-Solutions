"""
Comprehensive test suite for Database Optimization module.

Tests connection pooling, query caching, prepared statements, performance monitoring,
and database optimization utilities.

Target: >95% code coverage for database optimization components.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.pool import QueuePool

from apps.backend.core.db_optimization import (
    DatabaseConfig,
    DatabaseOptimizer,
    OptimizedAsyncEngine,
    PreparedStatements,
    QueryCache,
    QueryStats,
    _db_engine,
    _prepared_statements,
    _query_cache,
    _query_stats,
    cached_query,
    get_db_health,
    get_user_dashboard_optimized,
    initialize_db_optimization,
    setup_prepared_statements,
)


@pytest.mark.unit
class TestDatabaseConfig:
    """Test database configuration constants and settings."""

    def test_connection_pool_settings(self):
        """Test connection pool configuration values."""
        assert DatabaseConfig.POOL_SIZE == 20
        assert DatabaseConfig.MAX_OVERFLOW == 30
        assert DatabaseConfig.POOL_TIMEOUT == 30
        assert DatabaseConfig.POOL_RECYCLE == 3600
        assert DatabaseConfig.POOL_PRE_PING is True

    def test_query_timeout_settings(self):
        """Test query timeout configuration."""
        assert DatabaseConfig.QUERY_TIMEOUT == 30
        assert DatabaseConfig.SLOW_QUERY_THRESHOLD == 0.5

    def test_connection_parameters(self):
        """Test connection optimization parameters."""
        params = DatabaseConfig.CONNECTION_PARAMS
        assert "command_timeout" in params
        assert "server_settings" in params
        assert params["command_timeout"] == 60

        server_settings = params["server_settings"]
        assert server_settings["application_name"] == "toolboxai_backend"
        assert server_settings["jit"] == "off"
        assert server_settings["work_mem"] == "256MB"


@pytest.mark.unit
class TestQueryStats:
    """Test query performance statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = QueryStats()
        assert stats.query_count == 0
        assert stats.total_time == 0.0
        assert stats.slow_queries == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.prepared_statement_usage == 0

    def test_record_query_normal(self):
        """Test recording normal query execution."""
        stats = QueryStats()
        stats.record_query(duration=0.1, was_slow=False, from_cache=False, prepared=False)

        assert stats.query_count == 1
        assert stats.total_time == 0.1
        assert stats.slow_queries == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 1

    def test_record_query_slow(self):
        """Test recording slow query execution."""
        stats = QueryStats()
        stats.record_query(duration=0.8, was_slow=True, from_cache=False, prepared=False)

        assert stats.query_count == 1
        assert stats.slow_queries == 1

    def test_record_query_cached(self):
        """Test recording cached query result."""
        stats = QueryStats()
        stats.record_query(duration=0.001, was_slow=False, from_cache=True, prepared=False)

        assert stats.cache_hits == 1
        assert stats.cache_misses == 0

    def test_record_query_prepared(self):
        """Test recording prepared statement usage."""
        stats = QueryStats()
        stats.record_query(duration=0.05, was_slow=False, from_cache=False, prepared=True)

        assert stats.prepared_statement_usage == 1

    def test_avg_query_time_calculation(self):
        """Test average query time calculation."""
        stats = QueryStats()
        stats.record_query(0.1)
        stats.record_query(0.2)
        stats.record_query(0.3)

        assert stats.avg_query_time == 0.2  # (0.1 + 0.2 + 0.3) / 3

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        stats = QueryStats()
        stats.record_query(0.001, from_cache=True)  # Hit
        stats.record_query(0.001, from_cache=True)  # Hit
        stats.record_query(0.1, from_cache=False)  # Miss

        assert stats.cache_hit_rate == 2 / 3  # 2 hits out of 3 total

    def test_cache_hit_rate_no_queries(self):
        """Test cache hit rate with no queries."""
        stats = QueryStats()
        assert stats.cache_hit_rate == 0.0

    def test_to_dict_conversion(self):
        """Test statistics dictionary conversion."""
        stats = QueryStats()
        stats.record_query(0.1, was_slow=False, from_cache=True)
        stats.record_query(0.6, was_slow=True, from_cache=False, prepared=True)

        data = stats.to_dict()
        assert data["query_count"] == 2
        assert data["total_time"] == 0.7
        assert data["avg_query_time_ms"] == 350.0  # 0.35 * 1000
        assert data["slow_queries"] == 1
        assert data["slow_query_rate"] == 0.5
        assert data["cache_hits"] == 1
        assert data["cache_misses"] == 1
        assert data["cache_hit_rate"] == 0.5
        assert data["prepared_statement_usage"] == 1


@pytest.mark.unit
class TestOptimizedAsyncEngine:
    """Test optimized SQLAlchemy engine functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock database settings."""
        with patch("apps.backend.core.db_optimization.settings") as mock:
            mock.DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test"
            yield mock

    @pytest.fixture
    def engine_instance(self):
        """Create fresh engine instance for testing."""
        return OptimizedAsyncEngine()

    @patch("sqlalchemy.ext.asyncio.create_async_engine")
    @patch("sqlalchemy.ext.asyncio.async_sessionmaker")
    async def test_initialize_success(
        self, mock_sessionmaker, mock_create_engine, engine_instance, mock_settings
    ):
        """Test successful engine initialization."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_maker = Mock()
        mock_sessionmaker.return_value = mock_session_maker

        await engine_instance.initialize()

        assert engine_instance._initialized is True
        assert engine_instance.engine == mock_engine
        assert engine_instance.session_maker == mock_session_maker

        # Verify engine was created with correct parameters
        mock_create_engine.assert_called_once()
        call_args = mock_create_engine.call_args
        assert call_args[0][0] == mock_settings.DATABASE_URL
        assert call_args[1]["poolclass"] == QueuePool
        assert call_args[1]["pool_size"] == DatabaseConfig.POOL_SIZE

    async def test_initialize_already_initialized(self, engine_instance, mock_settings):
        """Test that double initialization is prevented."""
        engine_instance._initialized = True
        original_engine = Mock()
        engine_instance.engine = original_engine

        await engine_instance.initialize()

        # Engine should remain the same
        assert engine_instance.engine == original_engine

    @patch("sqlalchemy.ext.asyncio.create_async_engine")
    async def test_initialize_error(self, mock_create_engine, engine_instance, mock_settings):
        """Test initialization with database connection error."""
        mock_create_engine.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await engine_instance.initialize()

        assert engine_instance._initialized is False

    async def test_get_session_not_initialized(self, engine_instance):
        """Test getting session when engine not initialized."""
        with patch.object(engine_instance, "initialize") as mock_init:
            mock_session_maker = Mock()
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_session_maker.return_value.__aexit__.return_value = None

            engine_instance.session_maker = mock_session_maker

            async with engine_instance.get_session() as session:
                assert session == mock_session

            mock_init.assert_called_once()

    async def test_get_session_with_error(self, engine_instance):
        """Test session handling with error and rollback."""
        mock_session = AsyncMock()
        mock_session_maker = Mock()

        # Mock context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = None
        mock_session_maker.return_value = mock_context

        engine_instance._initialized = True
        engine_instance.session_maker = mock_session_maker

        class TestError(Exception):
            pass

        try:
            async with engine_instance.get_session() as session:
                raise TestError("Test error")
        except TestError:
            pass

        # Verify rollback was called during cleanup
        mock_session.rollback.assert_called_once()

    def test_setup_event_listeners(self, engine_instance):
        """Test SQLAlchemy event listener setup."""
        mock_engine = Mock()
        mock_engine.sync_engine = Mock()
        engine_instance.engine = mock_engine

        # Test that event listeners are set up
        with patch("sqlalchemy.engine.events.event.listens_for") as mock_listens_for:
            engine_instance._setup_event_listeners()

            # Should set up before and after cursor execute listeners
            assert mock_listens_for.call_count == 2


@pytest.mark.unit
class TestQueryCache:
    """Test database query result caching."""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache instance."""
        return AsyncMock()

    @pytest.fixture
    def query_cache(self, mock_cache):
        """Create query cache instance with mock cache."""
        cache = QueryCache()
        cache.cache = mock_cache
        return cache

    def test_generate_query_key_simple(self, query_cache):
        """Test simple query key generation."""
        query = "SELECT * FROM users WHERE id = %s"
        params = (123,)

        key = query_cache._generate_query_key(query, params)

        assert key.startswith("query:")
        assert len(key.split(":")) == 3  # prefix:query_hash:params_hash

    def test_generate_query_key_no_params(self, query_cache):
        """Test query key generation without parameters."""
        query = "SELECT COUNT(*) FROM users"

        key = query_cache._generate_query_key(query)

        assert key.startswith("query:")
        assert len(key.split(":")) == 2  # prefix:query_hash

    def test_generate_query_key_normalization(self, query_cache):
        """Test query normalization for consistent keys."""
        query1 = "SELECT    *    FROM   users   WHERE  id = 1"
        query2 = "select * from users where id = 1"

        key1 = query_cache._generate_query_key(query1)
        key2 = query_cache._generate_query_key(query2)

        assert key1 == key2  # Should be identical after normalization

    async def test_get_cached_result_hit(self, query_cache, mock_cache):
        """Test getting cached query result (hit)."""
        cached_data = [{"id": 1, "name": "John"}]
        mock_cache.get.return_value = cached_data

        with patch("apps.backend.core.db_optimization._query_stats") as mock_stats:
            result = await query_cache.get_cached_result("SELECT * FROM users", (1,))

            assert result == cached_data
            mock_stats.record_query.assert_called_once_with(0.001, from_cache=True)

    async def test_get_cached_result_miss(self, query_cache, mock_cache):
        """Test getting cached query result (miss)."""
        mock_cache.get.return_value = None

        result = await query_cache.get_cached_result("SELECT * FROM users", (1,))

        assert result is None

    async def test_cache_result(self, query_cache, mock_cache):
        """Test caching query result."""
        query = "SELECT * FROM users"
        params = (1,)
        result_data = [{"id": 1, "name": "John"}]

        await query_cache.cache_result(query, params, result_data, 600)

        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][1] == result_data  # Second arg should be result data
        assert call_args[0][2] == 600  # Third arg should be TTL

    async def test_invalidate_pattern(self, query_cache, mock_cache):
        """Test invalidating cached queries by pattern."""
        mock_cache.delete_pattern.return_value = 5

        result = await query_cache.invalidate_pattern("users")

        mock_cache.delete_pattern.assert_called_once_with("query:*users*")
        assert result == 5


@pytest.mark.unit
class TestPreparedStatements:
    """Test prepared statement management."""

    @pytest.fixture
    def statements(self):
        """Create fresh prepared statements manager."""
        return PreparedStatements()

    def test_register_statement(self, statements):
        """Test registering prepared statements."""
        query = "SELECT * FROM users WHERE id = :user_id"
        statements.register_statement("get_user", query)

        assert "get_user" in statements.statements
        assert statements._usage_count["get_user"] == 0

    def test_get_statement_exists(self, statements):
        """Test getting existing prepared statement."""
        query = "SELECT * FROM users WHERE id = :user_id"
        statements.register_statement("get_user", query)

        with patch("apps.backend.core.db_optimization._query_stats") as mock_stats:
            statement = statements.get_statement("get_user")

            assert statement is not None
            assert statements._usage_count["get_user"] == 1
            mock_stats.record_query.assert_called_once_with(0.0, prepared=True)

    def test_get_statement_not_exists(self, statements):
        """Test getting non-existent prepared statement."""
        statement = statements.get_statement("nonexistent")
        assert statement is None

    def test_get_usage_stats(self, statements):
        """Test getting usage statistics."""
        statements.register_statement("stmt1", "SELECT 1")
        statements.register_statement("stmt2", "SELECT 2")

        # Use statements
        statements.get_statement("stmt1")
        statements.get_statement("stmt1")
        statements.get_statement("stmt2")

        stats = statements.get_usage_stats()
        assert stats["stmt1"] == 2
        assert stats["stmt2"] == 1


@pytest.mark.unit
class TestSetupPreparedStatements:
    """Test prepared statement setup functionality."""

    @patch("apps.backend.core.db_optimization._prepared_statements")
    def test_setup_prepared_statements(self, mock_statements):
        """Test that all expected prepared statements are registered."""
        setup_prepared_statements()

        # Verify statements were registered
        assert mock_statements.register_statement.call_count >= 5

        # Check for specific statements
        call_args = [call[0][0] for call in mock_statements.register_statement.call_args_list]
        assert "get_user_by_email" in call_args
        assert "get_user_dashboard_base" in call_args
        assert "get_student_progress" in call_args
        assert "get_teacher_classes" in call_args
        assert "get_recent_assignments" in call_args


@pytest.mark.unit
class TestDatabaseOptimizer:
    """Test database optimizer functionality."""

    @pytest.fixture
    def mock_engine(self):
        """Mock database engine."""
        engine = Mock()
        engine.get_session = AsyncMock()
        return engine

    @pytest.fixture
    def mock_query_cache(self):
        """Mock query cache."""
        return AsyncMock()

    @pytest.fixture
    def optimizer_instance(self, mock_engine, mock_query_cache):
        """Create optimizer instance with mocked dependencies."""
        optimizer = DatabaseOptimizer()
        optimizer.engine = mock_engine
        optimizer.query_cache = mock_query_cache
        return optimizer

    async def test_execute_optimized_query_cache_hit(self, optimizer_instance, mock_query_cache):
        """Test optimized query execution with cache hit."""
        cached_result = [{"id": 1, "name": "John"}]
        mock_query_cache.get_cached_result.return_value = cached_result

        result = await optimizer_instance.execute_optimized_query(
            "SELECT * FROM users", {"id": 1}, use_cache=True
        )

        assert result == cached_result
        mock_query_cache.get_cached_result.assert_called_once()

    async def test_execute_optimized_query_cache_miss(
        self, optimizer_instance, mock_engine, mock_query_cache
    ):
        """Test optimized query execution with cache miss."""
        mock_query_cache.get_cached_result.return_value = None

        # Mock session and result
        mock_session = AsyncMock()
        mock_engine.get_session.return_value.__aenter__.return_value = mock_session
        mock_engine.get_session.return_value.__aexit__.return_value = None

        mock_result = Mock()
        mock_result.fetchall.return_value = [Mock(_mapping={"id": 1, "name": "John"})]
        mock_session.execute.return_value = mock_result

        with patch("apps.backend.core.db_optimization._query_stats") as mock_stats:
            result = await optimizer_instance.execute_optimized_query(
                "SELECT * FROM users", {"id": 1}, use_cache=True
            )

            assert result == [{"id": 1, "name": "John"}]
            mock_query_cache.cache_result.assert_called_once()
            mock_stats.record_query.assert_called_once()

    async def test_execute_optimized_query_no_cache(
        self, optimizer_instance, mock_engine, mock_query_cache
    ):
        """Test optimized query execution without caching."""
        mock_session = AsyncMock()
        mock_engine.get_session.return_value.__aenter__.return_value = mock_session
        mock_engine.get_session.return_value.__aexit__.return_value = None

        mock_result = Mock()
        mock_result.fetchall.return_value = [Mock(_mapping={"id": 1, "name": "John"})]
        mock_session.execute.return_value = mock_result

        result = await optimizer_instance.execute_optimized_query(
            "SELECT * FROM users", {"id": 1}, use_cache=False
        )

        assert result == [{"id": 1, "name": "John"}]
        mock_query_cache.get_cached_result.assert_not_called()
        mock_query_cache.cache_result.assert_not_called()

    async def test_execute_optimized_query_slow_query_warning(
        self, optimizer_instance, mock_engine, mock_query_cache
    ):
        """Test slow query warning logging."""
        mock_query_cache.get_cached_result.return_value = None

        mock_session = AsyncMock()
        mock_engine.get_session.return_value.__aenter__.return_value = mock_session
        mock_engine.get_session.return_value.__aexit__.return_value = None

        # Simulate slow query
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(0.6)  # Longer than SLOW_QUERY_THRESHOLD
            mock_result = Mock()
            mock_result.fetchall.return_value = []
            return mock_result

        mock_session.execute = slow_execute

        with patch("apps.backend.core.db_optimization.logger") as mock_logger:
            with patch("apps.backend.core.db_optimization._query_stats") as mock_stats:
                await optimizer_instance.execute_optimized_query("SELECT * FROM users")

                # Should log warning for slow query
                mock_logger.warning.assert_called()
                mock_stats.record_query.assert_called()
                call_args = mock_stats.record_query.call_args[0]
                assert call_args[1] is True  # was_slow should be True

    async def test_execute_prepared_statement_success(self, optimizer_instance):
        """Test executing prepared statement."""
        with patch("apps.backend.core.db_optimization._prepared_statements") as mock_statements:
            mock_statement = text("SELECT * FROM users WHERE id = :user_id")
            mock_statements.get_statement.return_value = mock_statement

            with patch.object(optimizer_instance, "execute_optimized_query") as mock_execute:
                mock_execute.return_value = [{"id": 1, "name": "John"}]

                result = await optimizer_instance.execute_prepared_statement(
                    "get_user", {"user_id": 1}
                )

                assert result == [{"id": 1, "name": "John"}]
                mock_statements.get_statement.assert_called_once_with("get_user")
                mock_execute.assert_called_once()

    async def test_execute_prepared_statement_not_found(self, optimizer_instance):
        """Test executing non-existent prepared statement."""
        with patch("apps.backend.core.db_optimization._prepared_statements") as mock_statements:
            mock_statements.get_statement.return_value = None

            with pytest.raises(ValueError, match="Prepared statement 'nonexistent' not found"):
                await optimizer_instance.execute_prepared_statement("nonexistent")

    async def test_warm_query_cache(self, optimizer_instance):
        """Test warming query cache with common queries."""
        queries = [
            ("SELECT COUNT(*) FROM users", {}),
            ("SELECT * FROM users WHERE active = :active", {"active": True}),
        ]

        with patch.object(optimizer_instance, "execute_optimized_query") as mock_execute:
            mock_execute.return_value = [{"count": 100}]

            await optimizer_instance.warm_query_cache(queries)

            assert mock_execute.call_count == 2

    async def test_warm_query_cache_with_errors(self, optimizer_instance):
        """Test cache warming with some queries failing."""
        queries = [
            ("SELECT COUNT(*) FROM users", {}),
            ("INVALID SQL QUERY", {}),
            ("SELECT * FROM profiles", {}),
        ]

        with patch.object(optimizer_instance, "execute_optimized_query") as mock_execute:
            mock_execute.side_effect = [
                [{"count": 100}],  # Success
                Exception("SQL syntax error"),  # Error
                [{"id": 1}],  # Success
            ]

            with patch("apps.backend.core.db_optimization.logger") as mock_logger:
                await optimizer_instance.warm_query_cache(queries)

                # Should log error but continue with other queries
                mock_logger.error.assert_called_once()
                assert mock_execute.call_count == 3

    async def test_get_connection_pool_stats(self, optimizer_instance):
        """Test getting connection pool statistics."""
        mock_pool = Mock()
        mock_pool.size.return_value = 20
        mock_pool.checkedin.return_value = 15
        mock_pool.checkedout.return_value = 5
        mock_pool.overflow.return_value = 2
        mock_pool.invalidated.return_value = 0

        optimizer_instance.engine.engine = Mock()
        optimizer_instance.engine.engine.pool = mock_pool

        stats = await optimizer_instance.get_connection_pool_stats()

        assert stats["pool_size"] == 20
        assert stats["checked_in"] == 15
        assert stats["checked_out"] == 5
        assert stats["overflow"] == 2
        assert stats["total_connections"] == 22  # size + overflow
        assert stats["invalid_connections"] == 0

    async def test_get_connection_pool_stats_not_initialized(self, optimizer_instance):
        """Test getting pool stats when engine not initialized."""
        optimizer_instance.engine.engine = None

        stats = await optimizer_instance.get_connection_pool_stats()

        assert stats == {"status": "not_initialized"}

    def test_get_query_stats(self, optimizer_instance):
        """Test getting query performance statistics."""
        with patch("apps.backend.core.db_optimization._query_stats") as mock_stats:
            mock_stats.to_dict.return_value = {"query_count": 100, "avg_time": 0.05}

            stats = optimizer_instance.get_query_stats()

            assert stats == {"query_count": 100, "avg_time": 0.05}
            mock_stats.to_dict.assert_called_once()

    def test_get_prepared_statement_stats(self, optimizer_instance):
        """Test getting prepared statement statistics."""
        with patch("apps.backend.core.db_optimization._prepared_statements") as mock_statements:
            mock_statements.statements = {"stmt1": Mock(), "stmt2": Mock()}
            mock_statements.get_usage_stats.return_value = {"stmt1": 10, "stmt2": 5}

            stats = optimizer_instance.get_prepared_statement_stats()

            assert stats["registered_statements"] == 2
            assert stats["usage_stats"] == {"stmt1": 10, "stmt2": 5}
            assert stats["total_usage"] == 15


@pytest.mark.unit
class TestCachedQueryDecorator:
    """Test the @cached_query decorator."""

    @patch("apps.backend.core.db_optimization.cache")
    @patch("apps.backend.core.db_optimization._query_stats")
    async def test_cached_query_decorator_hit(self, mock_stats, mock_cache):
        """Test cached query decorator with cache hit."""
        mock_cache.get.return_value = [{"id": 1, "name": "John"}]

        @cached_query(ttl=600)
        async def get_user(user_id: int):
            return [{"id": user_id, "name": f"User {user_id}"}]

        result = await get_user(1)

        assert result == [{"id": 1, "name": "John"}]
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()
        mock_stats.record_query.assert_called_once_with(0.001, from_cache=True)

    @patch("apps.backend.core.db_optimization.cache")
    @patch("apps.backend.core.db_optimization._query_stats")
    async def test_cached_query_decorator_miss(self, mock_stats, mock_cache):
        """Test cached query decorator with cache miss."""
        mock_cache.get.return_value = None

        @cached_query(ttl=600)
        async def get_user(user_id: int):
            await asyncio.sleep(0.1)  # Simulate query time
            return [{"id": user_id, "name": f"User {user_id}"}]

        result = await get_user(1)

        assert result == [{"id": 1, "name": "User 1"}]
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
        mock_stats.record_query.assert_called_once()
        # Should record actual execution time, not cache time
        call_args = mock_stats.record_query.call_args[0]
        assert call_args[0] >= 0.1  # Execution time


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test convenience functions for common database operations."""

    @patch("apps.backend.core.db_optimization.get_cached_dashboard")
    @patch("apps.backend.core.db_optimization.optimizer")
    async def test_get_user_dashboard_optimized_cached(self, mock_optimizer, mock_get_cached):
        """Test dashboard retrieval with cached data."""
        cached_data = {"user_id": 123, "role": "student", "cached": True}
        mock_get_cached.return_value = cached_data

        result = await get_user_dashboard_optimized(123, "student")

        assert result == cached_data
        mock_optimizer.execute_prepared_statement.assert_not_called()

    @patch("apps.backend.core.db_optimization.get_cached_dashboard")
    @patch("apps.backend.core.db_optimization.cache_dashboard")
    @patch("apps.backend.core.db_optimization.optimizer")
    async def test_get_user_dashboard_optimized_not_cached(
        self, mock_optimizer, mock_cache_dashboard, mock_get_cached
    ):
        """Test dashboard retrieval without cached data."""
        mock_get_cached.return_value = None
        mock_optimizer.execute_prepared_statement.return_value = [
            {"id": 123, "username": "testuser", "role": "student"}
        ]

        result = await get_user_dashboard_optimized(123, "student")

        assert result == {"user": {"id": 123, "username": "testuser", "role": "student"}}
        mock_optimizer.execute_prepared_statement.assert_called_with(
            "get_user_dashboard_base", {"user_id": 123}
        )
        mock_cache_dashboard.assert_called_once()

    @patch("apps.backend.core.db_optimization.get_cached_dashboard")
    @patch("apps.backend.core.db_optimization.optimizer")
    async def test_get_user_dashboard_optimized_user_not_found(
        self, mock_optimizer, mock_get_cached
    ):
        """Test dashboard retrieval when user not found."""
        mock_get_cached.return_value = None
        mock_optimizer.execute_prepared_statement.return_value = []

        result = await get_user_dashboard_optimized(123, "student")

        assert result is None


@pytest.mark.unit
class TestInitializationAndHealth:
    """Test database optimization initialization and health checking."""

    @patch("apps.backend.core.db_optimization._db_engine")
    @patch("apps.backend.core.db_optimization.setup_prepared_statements")
    async def test_initialize_db_optimization_success(self, mock_setup, mock_engine):
        """Test successful database optimization initialization."""
        mock_engine.initialize.return_value = None

        await initialize_db_optimization()

        mock_engine.initialize.assert_called_once()
        mock_setup.assert_called_once()

    @patch("apps.backend.core.db_optimization._db_engine")
    async def test_initialize_db_optimization_error(self, mock_engine):
        """Test database optimization initialization with error."""
        mock_engine.initialize.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await initialize_db_optimization()

    @patch("apps.backend.core.db_optimization.optimizer")
    async def test_get_db_health_success(self, mock_optimizer):
        """Test successful database health check."""
        mock_optimizer.get_connection_pool_stats.return_value = {"pool_size": 20, "checked_out": 5}
        mock_optimizer.get_query_stats.return_value = {"query_count": 100, "avg_time": 0.05}
        mock_optimizer.get_prepared_statement_stats.return_value = {
            "registered_statements": 5,
            "total_usage": 50,
        }

        health = await get_db_health()

        assert health["status"] == "healthy"
        assert health["optimization_enabled"] is True
        assert health["connection_pool"]["pool_size"] == 20
        assert health["query_performance"]["query_count"] == 100
        assert health["prepared_statements"]["registered_statements"] == 5

    @patch("apps.backend.core.db_optimization.optimizer")
    async def test_get_db_health_error(self, mock_optimizer):
        """Test database health check with error."""
        mock_optimizer.get_connection_pool_stats.side_effect = Exception("Database error")

        health = await get_db_health()

        assert health["status"] == "unhealthy"
        assert health["optimization_enabled"] is False
        assert "error" in health


@pytest.mark.unit
class TestGlobalInstances:
    """Test global instance management and singleton behavior."""

    def test_global_instances_exist(self):
        """Test that global instances are properly initialized."""
        assert _db_engine is not None
        assert _query_cache is not None
        assert _prepared_statements is not None
        assert _query_stats is not None

    def test_optimizer_uses_global_instances(self):
        """Test that optimizer uses global instances."""
        from apps.backend.core.db_optimization import optimizer

        assert optimizer.engine == _db_engine
        assert optimizer.query_cache == _query_cache


@pytest.mark.integration
class TestDatabaseOptimizationIntegration:
    """Integration tests for database optimization components."""

    @pytest.fixture
    def mock_database_setup(self):
        """Setup mock database environment for integration testing."""
        with patch("apps.backend.core.db_optimization.settings") as mock_settings:
            mock_settings.DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test"

            with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine

                with patch("sqlalchemy.ext.asyncio.async_sessionmaker") as mock_sessionmaker:
                    mock_session_maker = Mock()
                    mock_sessionmaker.return_value = mock_session_maker

                    yield {
                        "engine": mock_engine,
                        "session_maker": mock_session_maker,
                        "settings": mock_settings,
                    }

    async def test_full_optimization_workflow(self, mock_database_setup):
        """Test complete optimization workflow integration."""
        # Initialize fresh optimizer
        optimizer = DatabaseOptimizer()
        optimizer.engine = OptimizedAsyncEngine()

        # Mock successful initialization
        with patch.object(optimizer.engine, "initialize"):
            # Test query execution with caching
            mock_session = AsyncMock()
            optimizer.engine.get_session = AsyncMock()
            optimizer.engine.get_session.return_value.__aenter__.return_value = mock_session
            optimizer.engine.get_session.return_value.__aexit__.return_value = None

            mock_result = Mock()
            mock_result.fetchall.return_value = [Mock(_mapping={"id": 1, "name": "John"})]
            mock_session.execute.return_value = mock_result

            # First query - cache miss
            result1 = await optimizer.execute_optimized_query(
                "SELECT * FROM users WHERE id = :id", {"id": 1}
            )

            assert result1 == [{"id": 1, "name": "John"}]

            # Mock cache hit for second query
            optimizer.query_cache = AsyncMock()
            optimizer.query_cache.get_cached_result.return_value = [
                {"id": 1, "name": "John", "cached": True}
            ]

            # Second query - cache hit
            result2 = await optimizer.execute_optimized_query(
                "SELECT * FROM users WHERE id = :id", {"id": 1}, use_cache=True
            )

            assert result2 == [{"id": 1, "name": "John", "cached": True}]

    async def test_prepared_statement_integration(self, mock_database_setup):
        """Test prepared statement integration."""
        # Setup prepared statements
        statements = PreparedStatements()
        statements.register_statement("get_user", "SELECT * FROM users WHERE id = :user_id")

        # Test statement usage
        statement = statements.get_statement("get_user")
        assert statement is not None
        assert statements._usage_count["get_user"] == 1

        # Test usage statistics
        stats = statements.get_usage_stats()
        assert stats["get_user"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
