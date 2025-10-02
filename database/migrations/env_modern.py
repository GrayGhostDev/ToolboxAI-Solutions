"""
Modern Async Alembic Environment (2025 Standards)

Async migration support for SQLAlchemy 2.0 with proper type safety.

Reference: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
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

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import modern base and all models
from database.models.base_modern import Base
from database.models.user_modern import User, UserProfile, UserSession
from database.models.content_modern import (
    EducationalContent,
    ContentAttachment,
    ContentComment,
    ContentRating,
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata from modern base
target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get database URL from environment variables.

    Priority:
    1. DATABASE_URL environment variable
    2. Individual components (POSTGRES_*)
    3. Default values

    Returns:
        PostgreSQL connection URL with asyncpg driver
    """
    # Try DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Convert to asyncpg if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return database_url

    # Build from components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "educational_platform_dev")
    username = os.getenv("POSTGRES_USER", "eduplatform")
    password = os.getenv("POSTGRES_PASSWORD", "eduplatform2024")

    return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with given connection.

    Args:
        connection: SQLAlchemy connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # Render item for comparison
        render_item=lambda type_, obj, autogen_context: obj,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.

    Creates an async engine and executes migrations
    within an async connection.
    """
    # Override database URL
    config.set_main_option("sqlalchemy.url", get_database_url())

    # Create async engine
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Uses asyncio to run async migrations.
    """
    asyncio.run(run_async_migrations())


# Determine mode and run migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
