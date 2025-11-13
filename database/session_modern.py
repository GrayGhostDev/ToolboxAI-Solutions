"""
Modern Async Database Session Management (SQLAlchemy 2.0)

Provides async session factory and connection pooling for PostgreSQL.
Uses SQLAlchemy 2.0+ async patterns with proper context management.

Reference: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy import event, exc
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import QueuePool

from toolboxai_settings.settings import settings

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """
    Manages async database sessions with connection pooling.

    Provides:
    - Async engine with optimized pool settings
    - Session factory with proper configuration
    - Context managers for sessions and transactions
    - Tenant context support for RLS
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database session manager.

        Args:
            database_url: PostgreSQL connection URL (asyncpg driver)
                         If None, uses settings.DATABASE_URL
        """
        self._database_url = database_url or self._get_database_url()
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
        self._current_tenant_id: Optional[UUID] = None

    def _get_database_url(self) -> str:
        """
        Get async database URL from settings.

        Converts psycopg2 URLs to asyncpg format if needed.
        """
        url = settings.DATABASE_URL

        # Convert postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            raise ValueError(f"Database URL must use asyncpg driver. Got: {url[:20]}...")

        return url

    def _create_engine(self) -> AsyncEngine:
        """
        Create async SQLAlchemy engine with optimized pool settings.

        Pool settings:
        - pool_size: Number of permanent connections (20)
        - max_overflow: Additional connections when pool is full (10)
        - pool_timeout: Seconds to wait for connection (30)
        - pool_recycle: Recycle connections after seconds (3600)
        - pool_pre_ping: Test connections before use (True)
        """
        engine = create_async_engine(
            self._database_url,
            echo=settings.DEBUG,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle after 1 hour
            pool_pre_ping=True,  # Verify connections before use
        )

        # Set up event listeners
        self._setup_event_listeners(engine)

        return engine

    def _setup_event_listeners(self, engine: AsyncEngine) -> None:
        """
        Set up SQLAlchemy event listeners for monitoring and debugging.

        Args:
            engine: Async SQLAlchemy engine
        """

        @event.listens_for(engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log new database connections."""
            logger.debug("New database connection established")

        @event.listens_for(engine.sync_engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checkout from pool."""
            logger.debug("Connection checked out from pool")

        @event.listens_for(engine.sync_engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection return to pool."""
            logger.debug("Connection returned to pool")

    @property
    def engine(self) -> AsyncEngine:
        """
        Get async engine, creating if needed.

        Returns:
            Async SQLAlchemy engine
        """
        if self._engine is None:
            self._engine = self._create_engine()
            logger.info("Database engine created successfully")

        return self._engine

    @property
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        """
        Get session factory, creating if needed.

        Returns:
            Async session factory
        """
        if self._sessionmaker is None:
            self._sessionmaker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit
                autoflush=False,  # Manual flush control for better performance
                autocommit=False,  # Use explicit transactions
            )
            logger.info("Session factory created successfully")

        return self._sessionmaker

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.

        Usage:
            async with db_manager.session() as session:
                result = await session.execute(stmt)

        Yields:
            AsyncSession instance

        Handles:
            - Automatic cleanup on exit
            - Transaction rollback on error
            - Proper resource cleanup
        """
        async with self.sessionmaker() as session:
            try:
                yield session
            except exc.SQLAlchemyError as e:
                logger.error(f"Database error in session: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database transactions.

        Automatically commits on success, rolls back on error.

        Usage:
            async with db_manager.transaction() as session:
                await session.execute(stmt)
                # Automatic commit on success

        Yields:
            AsyncSession instance with active transaction

        Handles:
            - Automatic commit on success
            - Automatic rollback on error
            - Proper transaction cleanup
        """
        async with self.session() as session:
            async with session.begin():
                try:
                    yield session
                    # Commit happens automatically if no exception
                except exc.SQLAlchemyError as e:
                    logger.error(f"Transaction error: {e}")
                    # Rollback happens automatically
                    raise

    def set_tenant_context(self, tenant_id: UUID) -> None:
        """
        Set current tenant ID for Row-Level Security.

        Args:
            tenant_id: Organization UUID to set as current tenant
        """
        self._current_tenant_id = tenant_id
        logger.debug(f"Tenant context set to: {tenant_id}")

    def clear_tenant_context(self) -> None:
        """Clear current tenant context."""
        self._current_tenant_id = None
        logger.debug("Tenant context cleared")

    def get_current_tenant(self) -> Optional[UUID]:
        """
        Get current tenant ID from context.

        Returns:
            Current tenant UUID or None
        """
        return self._current_tenant_id

    @asynccontextmanager
    async def tenant_session(self, tenant_id: UUID) -> AsyncGenerator[AsyncSession, None]:
        """
        Create session with tenant context for RLS.

        Args:
            tenant_id: Organization UUID for tenant isolation

        Usage:
            async with db_manager.tenant_session(org_id) as session:
                # All queries automatically filtered by tenant
                result = await session.execute(stmt)

        Yields:
            AsyncSession with tenant context set
        """
        previous_tenant = self._current_tenant_id

        try:
            self.set_tenant_context(tenant_id)

            async with self.session() as session:
                # Set tenant context in PostgreSQL session
                await session.execute(f"SET app.current_tenant = '{tenant_id}'")
                yield session
        finally:
            # Restore previous tenant context
            if previous_tenant:
                self.set_tenant_context(previous_tenant)
            else:
                self.clear_tenant_context()

    async def close(self) -> None:
        """
        Close database engine and cleanup resources.

        Should be called on application shutdown.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
            logger.info("Database engine closed successfully")

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            async with self.session() as session:
                await session.execute("SELECT 1")
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global session manager instance
db_manager = DatabaseSessionManager()


# Convenience function for getting sessions
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get async database sessions.

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(User))
            return result.scalars().all()

    Yields:
        AsyncSession instance
    """
    async with db_manager.session() as session:
        yield session


# Convenience function for transactions
async def get_async_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get async database transactions.

    Usage in FastAPI:
        @app.post("/users")
        async def create_user(
            user_data: UserCreate,
            session: AsyncSession = Depends(get_async_transaction)
        ):
            user = User(**user_data.dict())
            session.add(user)
            # Auto-commit on success, auto-rollback on error
            return user

    Yields:
        AsyncSession with active transaction
    """
    async with db_manager.transaction() as session:
        yield session


# Export public API
__all__ = [
    "DatabaseSessionManager",
    "db_manager",
    "get_async_session",
    "get_async_transaction",
]
