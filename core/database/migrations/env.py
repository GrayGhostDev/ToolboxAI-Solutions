"""
Alembic Environment Configuration for Async SQLAlchemy (2025 Best Practices)

This configuration follows the latest Alembic async template for SQLAlchemy 2.0+
with proper async engine handling and migration support.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import your models here to ensure they're registered with metadata
from core.database.models import Base

# Import all models to ensure they're registered - critical for autogenerate
# Import models directly to avoid duplicate table issues
import core.database.models
import core.database.roblox_models

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Configure naming conventions for consistency (2025 best practice)
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Apply naming convention to metadata
target_metadata.naming_convention = naming_convention


def get_database_url():
    """
    Get database URL from environment variables.
    Supports both DATABASE_URL and component-based configuration.
    """
    # Try DATABASE_URL first (standard for 2025 deployments)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        # For async, convert to async driver
        if "postgresql://" in database_url and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url

    # Fallback to component-based configuration
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "educational_platform_dev")
    username = os.getenv("DB_USER", "eduplatform")
    password = os.getenv("DB_PASSWORD", "eduplatform2024")

    # Use asyncpg driver for async operations
    return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Compare column types
        compare_server_default=True,  # Compare server defaults
        include_schemas=True,  # Include schema information
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations using the provided connection.
    This function is called by run_sync in async mode.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect server default changes
        include_schemas=True,  # Include schema information
        # 2025 best practice: Include these for better autogenerate
        render_as_batch=True,  # Use batch operations for SQLite compatibility
        include_object=include_object,  # Custom object filtering
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    Custom function to filter objects for autogenerate.
    This is a 2025 best practice to have fine control over what gets migrated.
    """
    # Skip alembic_version table
    if type_ == "table" and name == "alembic_version":
        return False
    
    # Skip system schemas
    if hasattr(object, "schema") and object.schema in ["information_schema", "pg_catalog"]:
        return False
    
    # Include everything else
    return True


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.
    
    This is the 2025 recommended approach for async SQLAlchemy projects.
    Creates an async Engine and associates a connection with the context.
    """
    # Create configuration dictionary
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    # Create async engine with optimized pool settings
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Use NullPool for migrations to avoid connection issues
        future=True,  # Use SQLAlchemy 2.0 style
        echo=os.getenv("ALEMBIC_ECHO", "false").lower() == "true",  # Control SQL echo via env
    )

    async with connectable.connect() as connection:
        # Run migrations using run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    This function determines whether to use async or sync migrations
    based on the database URL and runs the appropriate migration function.
    """
    # Check if we're using async driver
    database_url = get_database_url()
    
    if "asyncpg" in database_url or "aiopg" in database_url:
        # Run async migrations for async drivers (2025 standard)
        asyncio.run(run_async_migrations())
    else:
        # Fallback to sync migrations for sync drivers
        from sqlalchemy import engine_from_config
        
        configuration = config.get_section(config.config_ini_section)
        configuration["sqlalchemy.url"] = database_url
        
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                include_schemas=True,
            )

            with context.begin_transaction():
                context.run_migrations()


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()