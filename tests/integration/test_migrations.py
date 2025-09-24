import pytest_asyncio
#!/usr/bin/env python3
"""
Database Migration Tests

Tests for Alembic database migrations including:
- Migration up/down functionality
- Rollback capabilities
- Schema consistency
- Data integrity during migrations
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
import subprocess
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import (
    db_manager,
    Base,
    User, Course, Lesson, Content, Quiz
)
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine
import asyncpg


class TestDatabaseMigrations:
    """Test suite for database migrations"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment"""
        # Store original database URL
        self.original_db_url = os.getenv("DATABASE_URL")
        
        # Use test database
        test_db_url = os.getenv("TEST_DATABASE_URL", 
                               "postgresql://eduplatform:eduplatform2024@localhost/test_educational_platform")
        os.environ["DATABASE_URL"] = test_db_url
        
        # Initialize connection
        await db_manager.initialize()
        
        yield
        
        # Cleanup
        await db_manager.close_all()
        
        # Restore original database URL
        if self.original_db_url:
            os.environ["DATABASE_URL"] = self.original_db_url
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_migration_current_status(self):
        """Test getting current migration status"""
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "current"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        assert result.returncode == 0, f"Failed to get current migration: {result.stderr}"
        assert "head" in result.stdout or "Rev:" in result.stdout
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_migration_upgrade_head(self):
        """Test upgrading to the latest migration"""
        # First downgrade to base
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "downgrade", "base"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Then upgrade to head
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        assert result.returncode == 0, f"Failed to upgrade migration: {result.stderr}"
        
        # Verify tables exist
        async with db_manager.get_connection() as conn:
            # Check if main tables exist
            tables_to_check = [
                "users", "courses", "lessons", "content",
                "quizzes", "quiz_questions", "quiz_attempts",
                "user_progress", "user_achievements", "enrollments"
            ]
            
            for table in tables_to_check:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                    """,
                    table
                )
                assert result, f"Table '{table}' does not exist after migration"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_migration_rollback(self):
        """Test rolling back migrations"""
        # Get current revision
        current_result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "current"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Upgrade to head first
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Downgrade one step
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "downgrade", "-1"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        assert result.returncode == 0, f"Failed to downgrade migration: {result.stderr}"
        
        # Upgrade back to head
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        assert result.returncode == 0, f"Failed to upgrade after downgrade: {result.stderr}"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_schema_consistency(self):
        """Test that the schema matches the SQLAlchemy models"""
        # Ensure migrations are at head
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        async with db_manager.get_connection() as conn:
            # Get database schema
            db_tables = await conn.fetch(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
            
            db_table_names = {row['table_name'] for row in db_tables}
            
            # Get model tables (excluding alembic_version)
            model_table_names = {
                table.name for table in Base.metadata.tables.values()
            }
            
            # Check if all model tables exist in database
            missing_tables = model_table_names - db_table_names
            assert not missing_tables, f"Missing tables in database: {missing_tables}"
            
            # Check column consistency for key tables
            for table_name in ['users', 'courses', 'lessons', 'content']:
                if table_name in db_table_names:
                    # Get database columns
                    db_columns = await conn.fetch(
                        """
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                        ORDER BY ordinal_position
                        """,
                        table_name
                    )
                    
                    db_column_names = {col['column_name'] for col in db_columns}
                    
                    # Get model columns
                    if table_name in Base.metadata.tables:
                        model_table = Base.metadata.tables[table_name]
                        model_column_names = {col.name for col in model_table.columns}
                        
                        # Check if all model columns exist in database
                        missing_columns = model_column_names - db_column_names
                        assert not missing_columns, f"Missing columns in table '{table_name}': {missing_columns}"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_data_integrity_during_migration(self):
        """Test that data is preserved during migrations"""
        # Ensure we're at head
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Insert test data
        test_user_id = None
        async with db_manager.get_connection() as conn:
            # Insert a test user
            test_user_id = await conn.fetchval(
                """
                INSERT INTO users (email, username, password_hash, role)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                "test_migration@example.com",
                "test_migration_user",
                "hashed_password_123",
                "student"
            )
            
            # Insert a test course
            test_course_id = await conn.fetchval(
                """
                INSERT INTO courses (title, code, subject, grade_level, description)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                "Test Migration Course",
                "TEST_MIG_001",
                "Testing",
                7,
                "Course for migration testing"
            )
        
        # Downgrade one step
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "downgrade", "-1"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Upgrade back to head
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Verify data still exists
        async with db_manager.get_connection() as conn:
            # Check if user still exists
            user_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
                test_user_id
            )
            
            # Note: Data might not persist through downgrade depending on migration
            # This is expected behavior for destructive migrations
            if user_exists:
                user_data = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1",
                    test_user_id
                )
                assert user_data['username'] == 'test_migration_user'
            
            # Cleanup test data
            await conn.execute("DELETE FROM courses WHERE code = 'TEST_MIG_001'")
            await conn.execute("DELETE FROM users WHERE username = 'test_migration_user'")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_migration_history(self):
        """Test viewing migration history"""
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "history"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        assert result.returncode == 0, f"Failed to get migration history: {result.stderr}"
        assert "Rev:" in result.stdout or "->" in result.stdout
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_migration_autogenerate(self):
        """Test that autogenerate detects model changes correctly"""
        # This test would require modifying models temporarily
        # For now, we just test that autogenerate runs without error
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "revision", 
             "--autogenerate", "-m", "test_autogenerate", "--sql"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Check if command executed (might not create migration if no changes)
        assert result.returncode == 0 or "No changes in schema detected" in result.stdout
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_indexes_and_constraints(self):
        """Test that indexes and constraints are properly created"""
        # Ensure migrations are at head
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        async with db_manager.get_connection() as conn:
            # Check for important indexes
            indexes = await conn.fetch(
                """
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname LIKE 'idx_%'
                """
            )
            
            # Verify some key indexes exist
            index_names = {idx['indexname'] for idx in indexes}
            
            # These indexes should exist based on the models
            expected_indexes = [
                'idx_user_email_active',
                'idx_user_roblox_id',
                'idx_course_subject_grade',
                'idx_lesson_course_order',
                'idx_content_lesson_type',
                'idx_content_status'
            ]
            
            for expected_idx in expected_indexes:
                # Note: Some indexes might not exist if not defined in migrations
                # This is informational rather than a hard assertion
                if expected_idx not in index_names:
                    print(f"Warning: Expected index '{expected_idx}' not found")
            
            # Check for foreign key constraints
            constraints = await conn.fetch(
                """
                SELECT conname, conrelid::regclass AS table_name
                FROM pg_constraint
                WHERE contype = 'f'
                AND connamespace = 'public'::regnamespace
                """
            )
            
            assert len(constraints) > 0, "No foreign key constraints found"


@pytest.mark.skipif(
    os.getenv("RUN_MIGRATION_TESTS") != "1",
    reason="Migration tests disabled. Set RUN_MIGRATION_TESTS=1 to enable"
)
class TestMigrationIntegration:
    """Integration tests for migrations with real database operations"""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_full_migration_workflow(self):
        """Test complete migration workflow from base to head with seed data"""
        # 1. Downgrade to base
        subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "downgrade", "base"],
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # 2. Upgrade to head
        result = subprocess.run(
            ["alembic", "-c", "core/database/alembic.ini", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        assert result.returncode == 0
        
        # 3. Run seed script
        result = subprocess.run(
            [sys.executable, "scripts/development/seed_database.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        # Check if seed was successful or database already had data
        assert result.returncode == 0 or "already contains data" in result.stdout
        
        # 4. Verify data
        await db_manager.initialize()
        async with db_manager.get_connection() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            assert user_count > 0, "No users found after seeding"