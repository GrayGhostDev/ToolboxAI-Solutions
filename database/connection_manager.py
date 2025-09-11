"""
Database Connection Manager for ToolboxAI Roblox Environment

Provides centralized database connection management across all services.
Supports multiple databases, connection pooling, and health monitoring.
"""

import asyncio
import os
from contextlib import asynccontextmanager, contextmanager
from typing import Dict, Optional, Any, List, Union, Generator, AsyncGenerator
from urllib.parse import quote_plus

import redis
import pymongo
from sqlalchemy import create_engine, MetaData, text, Engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Also load from config directory
load_dotenv("config/database.env")


class DatabaseConnectionManager:
    """Manages database connections for all ToolboxAI services."""

    def __init__(self):
        """Initialize the database connection manager."""
        self.engines: Dict[str, Engine] = {}
        self.async_engines: Dict[str, AsyncEngine] = {}
        self.session_factories: Dict[str, sessionmaker] = {}
        self.async_session_factories: Dict[str, async_sessionmaker] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.mongo_client: Optional[pymongo.MongoClient] = None
        self._initialized = False

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
                # Create sync engine
                sync_url = self._build_postgresql_url(config)
                sync_engine = create_engine(
                    sync_url,
                    poolclass=QueuePool,
                    pool_size=int(os.getenv("DB_POOL_SIZE", 20)),
                    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 40)),
                    pool_pre_ping=True,
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=config["echo"],
                )

                # Create async engine
                async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")
                async_engine = create_async_engine(
                    async_url,
                    pool_size=int(os.getenv("DB_POOL_SIZE", 20)),
                    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 40)),
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=config["echo"],
                )

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

    def _build_postgresql_url(self, config: Dict[str, Any]) -> str:
        """Build PostgreSQL connection URL."""
        password = quote_plus(config["password"]) if config["password"] else ""
        password_part = f":{password}" if password else ""

        return f"postgresql://{config['username']}{password_part}@{config['host']}:{config['port']}/{config['database']}"

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

    def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        results = {}

        # Check PostgreSQL databases
        for db_name, engine in self.engines.items():
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                results[f"postgresql_{db_name}"] = True
            except Exception as e:
                print(f"❌ PostgreSQL {db_name} health check failed: {e}")
                results[f"postgresql_{db_name}"] = False

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
                asyncio.create_task(engine.dispose())
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
