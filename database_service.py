"""
Database Service Module
Provides database connection and session management
"""

import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for managing connections and sessions"""

    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self.is_initialized = False

        # Get database URL from environment
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev'
        )

        # Create async URL
        self.async_database_url = self.database_url.replace(
            'postgresql://', 'postgresql+asyncpg://'
        )

    async def initialize(self):
        """Initialize database connections"""
        try:
            # Create sync engine
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                echo=False
            )

            # Create async engine
            self.async_engine = create_async_engine(
                self.async_database_url,
                pool_size=10,
                max_overflow=20,
                echo=False
            )

            # Create session factories
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            self.AsyncSessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.async_engine,
                expire_on_commit=False
            )

            self.is_initialized = True
            logger.info("Database service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise

    async def shutdown(self):
        """Shutdown database connections"""
        try:
            if self.engine:
                self.engine.dispose()

            if self.async_engine:
                await self.async_engine.dispose()

            self.is_initialized = False
            logger.info("Database service shut down successfully")

        except Exception as e:
            logger.error(f"Error shutting down database service: {e}")

    def get_session(self) -> Session:
        """Get sync database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database service not initialized")
        return self.SessionLocal()

    async def get_async_session(self) -> AsyncSession:
        """Get async database session"""
        if not self.AsyncSessionLocal:
            raise RuntimeError("Database service not initialized")
        return self.AsyncSessionLocal()

    @asynccontextmanager
    async def async_session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager for database sessions"""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def session_scope(self):
        """Context manager for sync database sessions"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.async_session_scope() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Create global instance
database_service = DatabaseService()

# Export for compatibility
async def get_async_session() -> AsyncSession:
    """Get async database session (compatibility function)"""
    return await database_service.get_async_session()

def get_session() -> Session:
    """Get sync database session (compatibility function)"""
    return database_service.get_session()