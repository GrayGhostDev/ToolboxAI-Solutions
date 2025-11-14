"""
Database Connection Manager for ToolboxAI Roblox Environment

Provides centralized database connection management across all services.
Supports multiple databases, connection pooling, and health monitoring.
"""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote_plus

import pymongo
import redis
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, QueuePool

# Import optimized pool configuration
from .pool_config import PoolMonitor, get_database_pool_config

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
# Also load from config directory
load_dotenv("config/database.env")


class DatabaseConnectionManager:
    """Manages database connections for all ToolboxAI services."""

    def __init__(self):
        """Initialize the database connection manager."""
        self.engines: dict[str, Engine] = {}
        self.async_engines: dict[str, AsyncEngine] = {}
        self.session_factories: dict[str, sessionmaker] = {}
        self.async_session_factories: dict[str, async_sessionmaker] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.mongo_client: Optional[pymongo.MongoClient] = None
        self.pool_monitors: dict[str, PoolMonitor] = {}
        self._initialized = False
        self.environment = os.getenv("ENVIRONMENT", "production")

    def initialize(self) -> None:
        """Initialize all database connections."""
        if self._initialized:
            return

        print("🚀 Initializing database connections...")

        # Initialize PostgreSQL databases
        self._initialize_postgresql_databases()

        # Initialize Redis
        self._initialize_redis()

        # Initialize MongoDB (optional)
        self._initialize_mongodb()

        self._initialized = True
        print("✅ Database connections initialized successfully!")

    def _initialize_postgresql_databases(self) -> None:
        """Initialize PostgreSQL database connections."""
        databases = {
            "ghost": {
                "host": os.getenv("GHOST_DB_HOST", "localhost"),
                "port": int(os.getenv("GHOST_DB_PORT", 5432)),
                "database": os.getenv("GHOST_DB_NAME", "ghost_backend"),
                "username": os.getenv("GHOST_DB_USER", "ghost_user"),
                "password": os.getenv("GHOST_DB_PASSWORD", ""),
                "echo": os.getenv("GHOST_DB_ECHO", "false").lower() == "true",
            },
            "education": {
                "host": os.getenv("EDU_DB_HOST", "localhost"),
                "port": int(os.getenv("EDU_DB_PORT", 5432)),
                "database": os.getenv("EDU_DB_NAME", "educational_platform"),
                "username": os.getenv("EDU_DB_USER", "eduplatform"),
                "password": os.getenv("EDU_DB_PASSWORD", "eduplatform2024"),
                "echo": os.getenv("EDU_DB_ECHO", "false").lower() == "true",
            },
            "roblox": {
                "host": os.getenv("ROBLOX_DB_HOST", "localhost"),
                "port": int(os.getenv("ROBLOX_DB_PORT", 5432)),
                "database": os.getenv("ROBLOX_DB_NAME", "roblox_data"),
                "username": os.getenv("ROBLOX_DB_USER", "roblox_user"),
                "password": os.getenv("ROBLOX_DB_PASSWORD", ""),
                "echo": os.getenv("ROBLOX_DB_ECHO", "false").lower() == "true",
            },
            "development": {
                "host": os.getenv("DEV_DB_HOST", "localhost"),
                "port": int(os.getenv("DEV_DB_PORT", 5432)),
                "database": os.getenv("DEV_DB_NAME", "toolboxai_dev"),
                "username": os.getenv("DEV_DB_USER", "postgres"),
                "password": os.getenv("DEV_DB_PASSWORD", ""),
                "echo": os.getenv("DEV_DB_ECHO", "true").lower() == "true",
            },
        }

        for db_name, config in databases.items():
            try:
                # Get optimized pool configuration following 2025 best practices
                pool_config = get_database_pool_config(
                    environment=self.environment,
                    database_type="postgresql"
                )
                
                # Create pool monitor
                self.pool_monitors[db_name] = PoolMonitor(pool_config)
                
                # Create sync engine with SQLAlchemy 2.0 optimizations
                sync_url = self._build_postgresql_url(config)
                engine_kwargs = pool_config.to_engine_kwargs()
                engine_kwargs["echo"] = config["echo"]
                engine_kwargs["poolclass"] = QueuePool
                engine_kwargs["future"] = True  # SQLAlchemy 2.0 mode
                
                sync_engine = create_engine(sync_url, **engine_kwargs)
                
                # Register pool event listeners for monitoring (SQLAlchemy 2.0 best practice)
                if pool_config.enable_pool_events:
                    self._register_pool_events(sync_engine, db_name)

                # Create async engine with asyncpg optimizations
                # Build async URL with asyncpg driver specifically
                async_url = self._build_async_postgresql_url(config)
                async_kwargs = pool_config.to_async_engine_kwargs()
                async_kwargs["echo"] = config["echo"]
                async_kwargs["poolclass"] = AsyncAdaptedQueuePool
                
                async_engine = create_async_engine(async_url, **async_kwargs)
                
                # Register async pool events
                if pool_config.enable_pool_events:
                    self._register_async_pool_events(async_engine, db_name)

                # Create session factories
                session_factory = sessionmaker(
                    bind=sync_engine,
                    expire_on_commit=False,
                )

                async_session_factory = async_sessionmaker(
                    bind=async_engine,
                    expire_on_commit=False,
                )

                # Store connections
                self.engines[db_name] = sync_engine
                self.async_engines[db_name] = async_engine
                self.session_factories[db_name] = session_factory
                self.async_session_factories[db_name] = async_session_factory

                print(f"✅ Connected to {db_name} database")

            except Exception as e:
                print(f"❌ Failed to connect to {db_name} database: {e}")

    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_db = int(os.getenv("REDIS_DB", 0))
            redis_password = os.getenv("REDIS_PASSWORD", "")

            if redis_password:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True,
                    max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
                )
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
                )

            # Test connection
            self.redis_client.ping()
            print("✅ Connected to Redis")

        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    def _initialize_mongodb(self) -> None:
        """Initialize MongoDB connection (optional)."""
        try:
            mongo_host = os.getenv("MONGO_HOST")
            mongo_port = int(os.getenv("MONGO_PORT", 27017))
            mongo_database = os.getenv("MONGO_DATABASE", "toolboxai")
            mongo_username = os.getenv("MONGO_USERNAME", "")
            mongo_password = os.getenv("MONGO_PASSWORD", "")

            if not mongo_host:
                print("ℹ️  MongoDB not configured, skipping...")
                return

            # Build connection string
            if mongo_username and mongo_password:
                mongo_url = f"mongodb://{mongo_username}:{quote_plus(mongo_password)}@{mongo_host}:{mongo_port}/{mongo_database}"
            else:
                mongo_url = f"mongodb://{mongo_host}:{mongo_port}/{mongo_database}"

            self.mongo_client = pymongo.MongoClient(mongo_url)

            # Test connection
            self.mongo_client.server_info()
            print("✅ Connected to MongoDB")

        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None

    def _build_postgresql_url(self, config: dict[str, Any]) -> str:
        """
        Build PostgreSQL connection URL.
        Supports both psycopg3 and psycopg2 drivers.
        """
        password = quote_plus(config["password"]) if config["password"] else ""
        password_part = f":{password}" if password else ""
        
        # Try to use psycopg3 first, fall back to psycopg2
        try:
            import psycopg
            driver = "postgresql+psycopg"  # psycopg3 driver
            logger.debug(f"Using psycopg3 driver for {config.get('database', 'unknown')}")
        except ImportError:
            driver = "postgresql"  # Default to psycopg2
            logger.debug(f"Using psycopg2 driver for {config.get('database', 'unknown')}")

        return f"{driver}://{config['username']}{password_part}@{config['host']}:{config['port']}/{config['database']}"
    
    def _build_async_postgresql_url(self, config: dict[str, Any]) -> str:
        """
        Build async PostgreSQL connection URL for asyncpg.
        Always uses asyncpg driver for async connections.
        """
        password = quote_plus(config["password"]) if config["password"] else ""
        password_part = f":{password}" if password else ""
        
        # Always use asyncpg for async connections
        return f"postgresql+asyncpg://{config['username']}{password_part}@{config['host']}:{config['port']}/{config['database']}"
    
    def _register_pool_events(self, engine: Engine, db_name: str) -> None:
        """
        Register SQLAlchemy 2.0 pool event listeners for monitoring
        Following best practices from: https://docs.sqlalchemy.org/en/20/core/events.html#pool-events
        """
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Called once for each new DB-API connection."""
            connection_record.info['connect_time'] = datetime.now()
            if db_name in self.pool_monitors:
                self.pool_monitors[db_name].metrics["connections_created"] += 1
            logger.debug(f"[{db_name}] New connection created")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Called when a connection is checked out from the pool."""
            checkout_time = datetime.now()
            connection_record.info['checkout_time'] = checkout_time
            if db_name in self.pool_monitors:
                self.pool_monitors[db_name].metrics["checkout_count"] += 1
            
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Called when a connection is checked back into the pool."""
            if 'checkout_time' in connection_record.info:
                duration = (datetime.now() - connection_record.info['checkout_time']).total_seconds()
                if db_name in self.pool_monitors:
                    self.pool_monitors[db_name].metrics["total_checkout_time"] += duration
                if duration > 1.0:  # Log slow checkouts
                    logger.warning(f"[{db_name}] Slow connection checkout: {duration:.2f}s")
        
        @event.listens_for(engine, "reset")
        def receive_reset(dbapi_conn, connection_record):
            """Called when a connection is reset (rollback)."""
            logger.debug(f"[{db_name}] Connection reset")
        
        @event.listens_for(engine, "invalidate")
        def receive_invalidate(dbapi_conn, connection_record, exception):
            """Called when a connection is invalidated."""
            if db_name in self.pool_monitors:
                self.pool_monitors[db_name].metrics["connection_errors"] += 1
            logger.error(f"[{db_name}] Connection invalidated: {exception}")
    
    def _register_async_pool_events(self, engine: AsyncEngine, db_name: str) -> None:
        """
        Register async pool event listeners for monitoring
        Async version of pool events for AsyncEngine
        """
        @event.listens_for(engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            connection_record.info['connect_time'] = datetime.now()
            if db_name in self.pool_monitors:
                self.pool_monitors[db_name].metrics["connections_created"] += 1
            logger.debug(f"[{db_name}] Async connection created")
        
        @event.listens_for(engine.sync_engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            connection_record.info['checkout_time'] = datetime.now()
            if db_name in self.pool_monitors:
                self.pool_monitors[db_name].metrics["checkout_count"] += 1
        
        @event.listens_for(engine.sync_engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            if 'checkout_time' in connection_record.info:
                duration = (datetime.now() - connection_record.info['checkout_time']).total_seconds()
                if db_name in self.pool_monitors:
                    self.pool_monitors[db_name].metrics["total_checkout_time"] += duration

    @contextmanager
    def get_session(self, database: str = "education") -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        if not self._initialized:
            self.initialize()

        if database not in self.session_factories:
            raise ValueError(f"Database '{database}' not configured")

        session = self.session_factories[database]()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(
        self, database: str = "education"
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with automatic cleanup."""
        if not self._initialized:
            self.initialize()

        if database not in self.async_session_factories:
            raise ValueError(f"Database '{database}' not configured")

        async with self.async_session_factories[database]() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client."""
        if not self._initialized:
            self.initialize()
        return self.redis_client

    def get_mongo_client(self) -> Optional[pymongo.MongoClient]:
        """Get MongoDB client."""
        if not self._initialized:
            self.initialize()
        return self.mongo_client

    def get_engine(self, database: str = "education") -> Engine:
        """Get SQLAlchemy engine."""
        if not self._initialized:
            self.initialize()

        if database not in self.engines:
            raise ValueError(f"Database '{database}' not configured")

        return self.engines[database]

    def get_async_engine(self, database: str = "education") -> AsyncEngine:
        """Get async SQLAlchemy engine."""
        if not self._initialized:
            self.initialize()

        if database not in self.async_engines:
            raise ValueError(f"Database '{database}' not configured")

        return self.async_engines[database]

    def health_check(self) -> dict[str, Any]:
        """Check health of all database connections."""
        results = {}

        # Check PostgreSQL databases with pool status
        for db_name, engine in self.engines.items():
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # Add pool status if available
                pool_status = {}
                if hasattr(engine.pool, 'size'):
                    pool_status = {
                        "size": engine.pool.size(),
                        "checked_in": engine.pool.checkedin(),
                        "overflow": engine.pool.overflow(),
                        "total": engine.pool.size() + engine.pool.overflow()
                    }
                
                results[f"postgresql_{db_name}"] = {
                    "healthy": True,
                    "pool": pool_status
                }
                
                # Log pool status if monitor exists
                if db_name in self.pool_monitors:
                    self.pool_monitors[db_name].log_pool_status(engine.pool)
                    
            except Exception as e:
                print(f"❌ PostgreSQL {db_name} health check failed: {e}")
                results[f"postgresql_{db_name}"] = {
                    "healthy": False,
                    "error": str(e)
                }

        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                results["redis"] = True
            except Exception as e:
                print(f"❌ Redis health check failed: {e}")
                results["redis"] = False
        else:
            results["redis"] = False

        # Check MongoDB
        if self.mongo_client:
            try:
                self.mongo_client.server_info()
                results["mongodb"] = True
            except Exception as e:
                print(f"❌ MongoDB health check failed: {e}")
                results["mongodb"] = False
        else:
            results["mongodb"] = False

        return results

    def close_all(self) -> None:
        """Close all database connections."""
        print("🔄 Closing database connections...")

        # Close PostgreSQL engines
        for db_name, engine in self.engines.items():
            try:
                engine.dispose()
                print(f"✅ Closed {db_name} database connection")
            except Exception as e:
                print(f"❌ Error closing {db_name} database: {e}")

        # Close async engines
        for db_name, engine in self.async_engines.items():
            try:
                # Check if there's a running event loop
                try:
                    asyncio.get_running_loop()
                    # If we're in an async context, create a task
                    asyncio.create_task(engine.dispose())
                except RuntimeError:
                    # No running loop, run in a new one
                    asyncio.run(engine.dispose())
                print(f"✅ Closed {db_name} async database connection")
            except Exception as e:
                print(f"❌ Error closing {db_name} async database: {e}")

        # Close Redis
        if self.redis_client:
            try:
                self.redis_client.close()
                print("✅ Closed Redis connection")
            except Exception as e:
                print(f"❌ Error closing Redis: {e}")

        # Close MongoDB
        if self.mongo_client:
            try:
                self.mongo_client.close()
                print("✅ Closed MongoDB connection")
            except Exception as e:
                print(f"❌ Error closing MongoDB: {e}")

        self._initialized = False
        print("✅ All database connections closed")


# Global instance
db_manager = DatabaseConnectionManager()


# Convenience functions
def get_session(database: str = "education"):
    """Get a database session."""
    return db_manager.get_session(database)


def get_async_session(database: str = "education"):
    """Get an async database session."""
    return db_manager.get_async_session(database)


def get_redis_client():
    """Get Redis client."""
    return db_manager.get_redis_client()


def get_mongo_client():
    """Get MongoDB client."""
    return db_manager.get_mongo_client()


def get_engine(database: str = "education"):
    """Get SQLAlchemy engine."""
    return db_manager.get_engine(database)


def get_async_engine(database: str = "education"):
    """Get async SQLAlchemy engine."""
    return db_manager.get_async_engine(database)


def health_check():
    """Check health of all database connections."""
    return db_manager.health_check()


def initialize_databases():
    """Initialize all database connections."""
    db_manager.initialize()


def close_databases():
    """Close all database connections."""
    db_manager.close_all()


if __name__ == "__main__":
    # Test database connections
    print("🧪 Testing database connections...")

    # Initialize connections
    initialize_databases()

    # Run health check
    results = health_check()

    print("\n📊 Health Check Results:")
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'Healthy' if status else 'Unhealthy'}")

    # Close connections
    close_databases()
