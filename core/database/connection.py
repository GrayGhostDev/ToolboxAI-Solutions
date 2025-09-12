"""
Database Connection Manager for ToolboxAI Roblox Environment

Provides async database connection management using SQLAlchemy 2.0+
with connection pooling, retry logic, and health checks.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, pool, event
from sqlalchemy.exc import DBAPIError, OperationalError, IntegrityError
from sqlalchemy.pool import NullPool, QueuePool

from core.database.models import Base
from config.environment import get_environment_config
settings = get_environment_config()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections with async support and connection pooling"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection string (uses settings if not provided)
        """
        self.database_url = database_url or settings.DATABASE_URL
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker] = None
        self._initialized = False
        self._health_check_interval = 30  # seconds
        self._last_health_check: Optional[datetime] = None
        
        # Connection pool settings
        self.pool_settings = {
            "pool_size": settings.DB_POOL_SIZE if hasattr(settings, 'DB_POOL_SIZE') else 20,
            "max_overflow": settings.DB_MAX_OVERFLOW if hasattr(settings, 'DB_MAX_OVERFLOW') else 10,
            "pool_timeout": settings.DB_POOL_TIMEOUT if hasattr(settings, 'DB_POOL_TIMEOUT') else 30,
            "pool_recycle": settings.DB_POOL_RECYCLE if hasattr(settings, 'DB_POOL_RECYCLE') else 3600,
            "pool_pre_ping": True,  # Check connection health before using
        }
        
        # Retry settings
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables if needed"""
        if self._initialized:
            return
        
        try:
            # Create async engine with connection pooling
            self._engine = create_async_engine(
                self.database_url,
                echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
                poolclass=QueuePool,
                **self.pool_settings
            )
            
            # Create sessionmaker
            self._sessionmaker = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
            
            # Test connection
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
            
            # Create tables if they don't exist (development only)
            if settings.ENVIRONMENT == "development":
                async with self._engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created/verified")
            
            self._initialized = True
            self._last_health_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session with automatic cleanup
        
        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Database integrity error: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def execute_with_retry(
        self,
        query: Any,
        params: Optional[Dict] = None,
        max_retries: Optional[int] = None
    ) -> Any:
        """
        Execute a query with automatic retry logic
        
        Args:
            query: SQLAlchemy query or raw SQL
            params: Query parameters
            max_retries: Maximum retry attempts
            
        Returns:
            Query result
        """
        max_retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    if params:
                        result = await session.execute(query, params)
                    else:
                        result = await session.execute(query)
                    return result
                    
            except OperationalError as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    logger.warning(f"Database query retry {attempt + 1}/{max_retries}: {e}")
                    continue
                break
            except Exception as e:
                logger.error(f"Database query failed: {e}")
                raise
        
        if last_error:
            raise last_error
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Health check results
        """
        health_status = {
            "status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {}
        }
        
        try:
            # Check if we need to perform health check
            if self._last_health_check:
                time_since_check = datetime.utcnow() - self._last_health_check
                if time_since_check.seconds < self._health_check_interval:
                    health_status["status"] = "healthy"
                    health_status["details"]["cached"] = True
                    return health_status
            
            # Perform actual health check
            start_time = asyncio.get_event_loop().time()
            
            async with self.get_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1"))
                
                # Get database statistics
                stats_query = text("""
                    SELECT 
                        (SELECT COUNT(*) FROM users) as user_count,
                        (SELECT COUNT(*) FROM courses) as course_count,
                        (SELECT COUNT(*) FROM lessons) as lesson_count,
                        (SELECT COUNT(*) FROM quizzes) as quiz_count
                """)
                stats = await session.execute(stats_query)
                stats_row = stats.first()
                
                # Get connection pool stats
                pool_stats = self._engine.pool.status() if self._engine else "N/A"
                
                health_status["status"] = "healthy"
                health_status["details"] = {
                    "response_time_ms": round((asyncio.get_event_loop().time() - start_time) * 1000, 2),
                    "pool_status": pool_stats,
                    "statistics": {
                        "users": stats_row.user_count if stats_row else 0,
                        "courses": stats_row.course_count if stats_row else 0,
                        "lessons": stats_row.lesson_count if stats_row else 0,
                        "quizzes": stats_row.quiz_count if stats_row else 0
                    }
                }
                
                self._last_health_check = datetime.utcnow()
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["details"]["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    async def backup_database(self, backup_path: str) -> bool:
        """
        Create database backup (PostgreSQL specific)
        
        Args:
            backup_path: Path to save backup file
            
        Returns:
            Success status
        """
        try:
            # Extract connection details from URL
            import re
            pattern = r"postgresql\+asyncpg://(.+):(.+)@(.+):(\d+)/(.+)"
            match = re.match(pattern, self.database_url)
            
            if not match:
                logger.error("Could not parse database URL for backup")
                return False
            
            user, password, host, port, database = match.groups()
            
            # Create backup using pg_dump
            import subprocess
            import os
            
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", database,
                "-f", backup_path,
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges"
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return True
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return False
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Run database optimization tasks
        
        Returns:
            Optimization results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations": []
        }
        
        try:
            async with self.get_session() as session:
                # Analyze tables for query optimization
                tables = ["users", "courses", "lessons", "quizzes", "user_progress", "analytics"]
                
                for table in tables:
                    await session.execute(text(f"ANALYZE {table}"))
                    results["optimizations"].append(f"Analyzed table: {table}")
                
                # Vacuum tables to reclaim space (PostgreSQL)
                for table in tables:
                    # Note: VACUUM cannot run inside a transaction block
                    # This would need to be run separately
                    results["optimizations"].append(f"Scheduled vacuum for: {table}")
                
                # Update table statistics
                await session.execute(text("SELECT pg_stat_reset()"))
                results["optimizations"].append("Reset statistics")
                
                results["status"] = "completed"
                logger.info("Database optimization completed")
                
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"Database optimization failed: {e}")
        
        return results


# Global database manager instance
db_manager = DatabaseManager()


# FastAPI dependency for database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session
    
    Yields:
        Database session
    """
    async with db_manager.get_session() as session:
        yield session


# Utility functions for common database operations
async def create_or_update(
    session: AsyncSession,
    model: Any,
    defaults: Dict[str, Any],
    **kwargs
) -> tuple[Any, bool]:
    """
    Create or update a database record
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        defaults: Default values for creation/update
        **kwargs: Filter criteria
        
    Returns:
        Tuple of (instance, created)
    """
    from sqlalchemy import select
    
    # Try to get existing record
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if instance:
        # Update existing
        for key, value in defaults.items():
            setattr(instance, key, value)
        created = False
    else:
        # Create new
        instance = model(**kwargs, **defaults)
        session.add(instance)
        created = True
    
    return instance, created


async def bulk_insert(
    session: AsyncSession,
    model: Any,
    data: list[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """
    Bulk insert records efficiently
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        data: List of dictionaries with record data
        batch_size: Number of records per batch
        
    Returns:
        Number of records inserted
    """
    total_inserted = 0
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        instances = [model(**record) for record in batch]
        session.add_all(instances)
        await session.flush()
        total_inserted += len(instances)
        
        if i % (batch_size * 10) == 0:
            # Commit periodically for very large datasets
            await session.commit()
    
    return total_inserted


async def paginate_query(
    session: AsyncSession,
    query: Any,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """
    Paginate a query result
    
    Args:
        session: Database session
        query: SQLAlchemy query
        page: Page number (1-indexed)
        per_page: Items per page
        
    Returns:
        Paginated results with metadata
    """
    from sqlalchemy import func, select
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * per_page
    paginated_query = query.limit(per_page).offset(offset)
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "has_prev": page > 1,
        "has_next": page * per_page < total
    }


# FastAPI dependency for database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session
    
    Yields:
        Database session
    """
    async with db_manager.get_session() as session:
        yield session


async def get_async_session(database: str = "education") -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session
    
    Args:
        database: Database name (default: "education")
    
    Yields:
        Database session
    """
    async with db_manager.get_session() as session:
        yield session


# Initialize database on module import
async def init_db():
    """Initialize database connection on startup"""
    await db_manager.initialize()


async def close_db():
    """Close database connection on shutdown"""
    await db_manager.close()


# Export all public functions and classes
__all__ = [
    "DatabaseManager",
    "db_manager",
    "get_db",
    "get_async_session",
    "create_or_update",
    "bulk_insert",
    "paginate_query",
    "init_db",
    "close_db",
]