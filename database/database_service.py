"""
Database Service Module

Provides a backwards-compatible database service wrapper used by legacy
endpoints that expect synchronous and asynchronous SQLAlchemy session
factories exposed on import.
"""

import logging
import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class DatabaseService:
    """Hybrid database service exposing sync and async session helpers."""

    def __init__(self, database_url: Optional[str] = None):
        self._database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev",
        )
        self._async_database_url = self._database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

        self.engine = None
        self.async_engine = None
        self.SessionLocal: Optional[sessionmaker] = None
        self.AsyncSessionLocal: Optional[async_sessionmaker] = None
        self.is_initialized = False

        self._setup_engines()

    def _setup_engines(self) -> None:
        """Initialise engine and session factories."""
        try:
            self.engine = create_engine(
                self._database_url,
                pool_size=10,
                max_overflow=20,
                echo=False,
            )
            self.async_engine = create_async_engine(
                self._async_database_url,
                pool_size=10,
                max_overflow=20,
                echo=False,
            )

            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )

            self.AsyncSessionLocal = async_sessionmaker(
                bind=self.async_engine,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            self.is_initialized = True
            logger.info("Database service engines ready")
        except Exception as exc:
            logger.error("Failed to initialise database service: %s", exc)
            raise

    async def initialize(self) -> None:
        """Compatibility method for legacy callers."""
        if not self.is_initialized:
            self._setup_engines()

    async def shutdown(self) -> None:
        """Dispose SQLAlchemy engines."""
        try:
            if self.engine:
                self.engine.dispose()
            if self.async_engine:
                await self.async_engine.dispose()
            self.is_initialized = False
            logger.info("Database service shut down successfully")
        except Exception as exc:
            logger.error("Failed to shut down database service: %s", exc)

    # ------------------------------------------------------------------ #
    # Session helpers
    # ------------------------------------------------------------------ #

    def get_session(self) -> Session:
        if not self.SessionLocal:
            raise RuntimeError("Database service not initialised")
        return self.SessionLocal()

    async def get_async_session(self) -> AsyncSession:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Database service not initialised")
        return self.AsyncSessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self.AsyncSessionLocal:
            raise RuntimeError("Database service not initialised")
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # Backwards compatible alias
    async_session_scope = async_session

    # Convenience aliases for historic API
    async def connect(self) -> None:
        await self.initialize()

    async def disconnect(self) -> None:
        await self.shutdown()

    async def close(self) -> None:
        await self.shutdown()


# Singleton instance for modules that import at top-level
database_service = DatabaseService()
db_service = database_service


async def get_async_session() -> AsyncSession:
    """Legacy helper mirroring archived implementation."""
    return await database_service.get_async_session()


def get_session() -> Session:
    return database_service.get_session()
