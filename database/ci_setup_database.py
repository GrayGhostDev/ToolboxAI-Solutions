#!/usr/bin/env python3
"""
CI Database Setup Script
Creates database tables for continuous integration testing
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from database.connection import DATABASE_URL
from database.models import Base


def create_tables_sync():
    """Create database tables synchronously for CI."""
    # Use synchronous URL
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    print(f"Creating database tables for CI testing...")
    print(f"Database URL: {sync_url.split('@')[1]}")  # Hide credentials in output

    try:
        # Create engine
        engine = create_engine(sync_url, echo=False)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
                )
            )
            tables = [row[0] for row in result]

            if tables:
                print(f"✅ Created {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table}")
            else:
                print("⚠️  No tables were created")

        engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


async def create_tables_async():
    """Create database tables asynchronously."""
    print(f"Creating database tables asynchronously...")

    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=False)

        # Test connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("✅ Async database connection successful")

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")

        # Verify tables
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
                )
            )
            tables = [row[0] for row in result]

            if tables:
                print(f"✅ Created {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("CI DATABASE SETUP")
    print("=" * 60)

    # Check if DATABASE_URL is set
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)

    # Try synchronous creation first (more compatible with CI)
    success = create_tables_sync()

    if not success:
        print("\nTrying async approach...")
        success = asyncio.run(create_tables_async())

    if success:
        print("\n" + "=" * 60)
        print("✅ CI DATABASE SETUP COMPLETE")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ CI DATABASE SETUP FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
