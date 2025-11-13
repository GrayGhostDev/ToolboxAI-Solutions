"""
Fixtures for Supabase migration testing.

This module provides comprehensive fixtures for testing the Supabase migration
system, including mock data, connections, and test utilities.
"""

import json
import tempfile
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from core.agents.supabase.supabase_migration_agent import (
    MigrationPlan,
    SupabaseMigrationAgent,
)
from core.sparc.state_manager import StateManager


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    mock_manager = Mock(spec=StateManager)
    mock_manager.update_state = Mock()
    mock_manager.get_state = Mock(return_value={})
    return mock_manager


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = AsyncMock()
    mock_client.embeddings.create = AsyncMock(
        return_value=Mock(data=[Mock(embedding=[0.1] * 1536) for _ in range(10)])
    )
    return mock_client


@pytest.fixture
def mock_database_config():
    """Provide database configuration for testing."""
    return {
        "source": {
            "host": "localhost",
            "port": 5432,
            "database": "source_db",
            "user": "test_user",
            "password": "test_pass",
            "connection_string": "postgresql://test_user:test_pass@localhost:5432/source_db",
        },
        "target": {
            "host": "localhost",
            "port": 5433,
            "database": "target_db",
            "user": "test_user",
            "password": "test_pass",
            "connection_string": "postgresql://test_user:test_pass@localhost:5433/target_db",
        },
    }


@pytest.fixture
def educational_platform_schema():
    """Provide a comprehensive educational platform schema for testing."""
    return {
        "database": "educational_platform",
        "tables": [
            {
                "name": "organizations",
                "columns": [
                    {
                        "name": "id",
                        "type": "UUID",
                        "nullable": False,
                        "default": "gen_random_uuid()",
                    },
                    {"name": "name", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "domain", "type": "VARCHAR(255)", "nullable": True},
                    {"name": "subscription_plan", "type": "VARCHAR(50)", "nullable": False},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                    {"name": "updated_at", "type": "TIMESTAMP", "nullable": False},
                ],
                "primary_key": {"constrained_columns": ["id"]},
                "foreign_keys": [],
                "indexes": [
                    {"name": "idx_organizations_domain", "column_names": ["domain"], "unique": True}
                ],
                "unique_constraints": [
                    {"name": "uq_organizations_domain", "column_names": ["domain"]}
                ],
                "check_constraints": [],
                "row_count": 100,
                "size_bytes": 32768,
            },
            {
                "name": "users",
                "columns": [
                    {
                        "name": "id",
                        "type": "UUID",
                        "nullable": False,
                        "default": "gen_random_uuid()",
                    },
                    {"name": "email", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "encrypted_password", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "first_name", "type": "VARCHAR(100)", "nullable": True},
                    {"name": "last_name", "type": "VARCHAR(100)", "nullable": True},
                    {"name": "role", "type": "user_role", "nullable": False},
                    {"name": "organization_id", "type": "UUID", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                    {"name": "updated_at", "type": "TIMESTAMP", "nullable": False},
                ],
                "primary_key": {"constrained_columns": ["id"]},
                "foreign_keys": [
                    {
                        "name": "fk_users_organization_id",
                        "constrained_columns": ["organization_id"],
                        "referred_table": "organizations",
                        "referred_columns": ["id"],
                    }
                ],
                "indexes": [
                    {"name": "idx_users_email", "column_names": ["email"], "unique": True},
                    {
                        "name": "idx_users_organization_id",
                        "column_names": ["organization_id"],
                        "unique": False,
                    },
                ],
                "unique_constraints": [{"name": "uq_users_email", "column_names": ["email"]}],
                "check_constraints": [],
                "row_count": 5000,
                "size_bytes": 524288,
            },
            {
                "name": "lessons",
                "columns": [
                    {
                        "name": "id",
                        "type": "UUID",
                        "nullable": False,
                        "default": "gen_random_uuid()",
                    },
                    {"name": "title", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "description", "type": "TEXT", "nullable": True},
                    {"name": "content", "type": "JSONB", "nullable": True},
                    {"name": "difficulty_level", "type": "INTEGER", "nullable": False},
                    {"name": "created_by", "type": "UUID", "nullable": False},
                    {"name": "organization_id", "type": "UUID", "nullable": False},
                    {"name": "status", "type": "content_status", "nullable": False},
                    {"name": "published_at", "type": "TIMESTAMP", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                    {"name": "updated_at", "type": "TIMESTAMP", "nullable": False},
                ],
                "primary_key": {"constrained_columns": ["id"]},
                "foreign_keys": [
                    {
                        "name": "fk_lessons_created_by",
                        "constrained_columns": ["created_by"],
                        "referred_table": "users",
                        "referred_columns": ["id"],
                    },
                    {
                        "name": "fk_lessons_organization_id",
                        "constrained_columns": ["organization_id"],
                        "referred_table": "organizations",
                        "referred_columns": ["id"],
                    },
                ],
                "indexes": [
                    {
                        "name": "idx_lessons_organization_id",
                        "column_names": ["organization_id"],
                        "unique": False,
                    },
                    {
                        "name": "idx_lessons_created_by",
                        "column_names": ["created_by"],
                        "unique": False,
                    },
                ],
                "unique_constraints": [],
                "check_constraints": [
                    {"name": "ck_lessons_difficulty", "sqltext": "difficulty_level BETWEEN 1 AND 5"}
                ],
                "row_count": 10000,
                "size_bytes": 5242880,
            },
            {
                "name": "enrollments",
                "columns": [
                    {
                        "name": "id",
                        "type": "UUID",
                        "nullable": False,
                        "default": "gen_random_uuid()",
                    },
                    {"name": "student_id", "type": "UUID", "nullable": False},
                    {"name": "lesson_id", "type": "UUID", "nullable": False},
                    {"name": "progress_percentage", "type": "INTEGER", "nullable": False},
                    {"name": "completed_at", "type": "TIMESTAMP", "nullable": True},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                    {"name": "updated_at", "type": "TIMESTAMP", "nullable": False},
                ],
                "primary_key": {"constrained_columns": ["id"]},
                "foreign_keys": [
                    {
                        "name": "fk_enrollments_student_id",
                        "constrained_columns": ["student_id"],
                        "referred_table": "users",
                        "referred_columns": ["id"],
                    },
                    {
                        "name": "fk_enrollments_lesson_id",
                        "constrained_columns": ["lesson_id"],
                        "referred_table": "lessons",
                        "referred_columns": ["id"],
                    },
                ],
                "indexes": [
                    {
                        "name": "idx_enrollments_student_id",
                        "column_names": ["student_id"],
                        "unique": False,
                    },
                    {
                        "name": "idx_enrollments_lesson_id",
                        "column_names": ["lesson_id"],
                        "unique": False,
                    },
                ],
                "unique_constraints": [
                    {
                        "name": "uq_enrollments_student_lesson",
                        "column_names": ["student_id", "lesson_id"],
                    }
                ],
                "check_constraints": [
                    {
                        "name": "ck_enrollments_progress",
                        "sqltext": "progress_percentage BETWEEN 0 AND 100",
                    }
                ],
                "row_count": 50000,
                "size_bytes": 8388608,
            },
        ],
        "views": [
            {
                "name": "user_progress_summary",
                "columns": [
                    {"name": "user_id", "type": "UUID"},
                    {"name": "total_lessons", "type": "BIGINT"},
                    {"name": "completed_lessons", "type": "BIGINT"},
                ],
                "definition": "SELECT student_id as user_id, COUNT(*) as total_lessons FROM enrollments GROUP BY student_id",
            }
        ],
        "sequences": [
            {
                "name": "lesson_order_seq",
                "data_type": "bigint",
                "start_value": 1,
                "min_value": 1,
                "max_value": 9223372036854775807,
                "increment": 1,
            }
        ],
        "functions": [{"name": "calculate_progress", "type": "FUNCTION", "return_type": "numeric"}],
        "triggers": [
            {
                "name": "update_user_timestamp",
                "table": "users",
                "event": "UPDATE",
                "timing": "BEFORE",
            }
        ],
        "enums": [
            {"name": "user_role", "values": ["student", "teacher", "admin"]},
            {"name": "content_status", "values": ["draft", "published", "archived"]},
        ],
    }


@pytest.fixture
def sample_access_patterns():
    """Provide sample access patterns for RLS policy generation."""
    return {
        "users": {"multi_tenant": True, "hierarchical": False, "time_based": False},
        "lessons": {"multi_tenant": True, "hierarchical": False, "time_based": True},
        "enrollments": {"multi_tenant": True, "hierarchical": False, "time_based": False},
        "organizations": {"multi_tenant": False, "hierarchical": True, "time_based": False},
    }


@pytest.fixture
def sample_migration_options():
    """Provide sample migration options for testing."""
    return {
        "migration_type": "full",
        "preserve_data": True,
        "enable_realtime": True,
        "create_api": True,
        "batch_size": 1000,
        "max_concurrent_batches": 5,
        "enable_rls": True,
        "create_storage_buckets": True,
        "generate_types": True,
    }


@pytest.fixture
def sample_table_data():
    """Provide sample table data for migration testing."""
    return {
        "organizations": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Example University",
                "domain": "example.edu",
                "subscription_plan": "premium",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Test School",
                "domain": "test.edu",
                "subscription_plan": "basic",
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
            },
        ],
        "users": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440011",
                "email": "admin@example.edu",
                "encrypted_password": "hashed_password_1",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin",
                "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440012",
                "email": "teacher@example.edu",
                "encrypted_password": "hashed_password_2",
                "first_name": "Jane",
                "last_name": "Smith",
                "role": "teacher",
                "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440013",
                "email": "student@example.edu",
                "encrypted_password": "hashed_password_3",
                "first_name": "John",
                "last_name": "Doe",
                "role": "student",
                "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            },
        ],
        "lessons": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440021",
                "title": "Introduction to Python",
                "description": "Learn the basics of Python programming",
                "content": {"chapters": ["Variables", "Functions", "Classes"]},
                "difficulty_level": 1,
                "created_by": "550e8400-e29b-41d4-a716-446655440012",
                "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "published",
                "published_at": "2023-01-03T00:00:00Z",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-03T00:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440022",
                "title": "Advanced JavaScript",
                "description": "Deep dive into JavaScript concepts",
                "content": {"chapters": ["Closures", "Promises", "Async/Await"]},
                "difficulty_level": 3,
                "created_by": "550e8400-e29b-41d4-a716-446655440012",
                "organization_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "published",
                "published_at": "2023-01-04T00:00:00Z",
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-04T00:00:00Z",
            },
        ],
        "enrollments": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440031",
                "student_id": "550e8400-e29b-41d4-a716-446655440013",
                "lesson_id": "550e8400-e29b-41d4-a716-446655440021",
                "progress_percentage": 75,
                "completed_at": None,
                "created_at": "2023-01-05T00:00:00Z",
                "updated_at": "2023-01-10T00:00:00Z",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440032",
                "student_id": "550e8400-e29b-41d4-a716-446655440013",
                "lesson_id": "550e8400-e29b-41d4-a716-446655440022",
                "progress_percentage": 100,
                "completed_at": "2023-01-15T00:00:00Z",
                "created_at": "2023-01-06T00:00:00Z",
                "updated_at": "2023-01-15T00:00:00Z",
            },
        ],
    }


@pytest.fixture
def mock_migration_plan():
    """Create a comprehensive migration plan for testing."""
    return MigrationPlan(
        schema_mappings={
            "organizations": {
                "original": {"name": "organizations"},
                "supabase": {"name": "organizations", "rls_enabled": True},
                "modifications": ["add_timestamps"],
            },
            "users": {
                "original": {"name": "users"},
                "supabase": {"name": "users", "rls_enabled": True},
                "modifications": ["add_uuid_primary_key"],
            },
            "lessons": {
                "original": {"name": "lessons"},
                "supabase": {"name": "lessons", "rls_enabled": True},
                "modifications": ["add_timestamps"],
            },
            "enrollments": {
                "original": {"name": "enrollments"},
                "supabase": {"name": "enrollments", "rls_enabled": True},
                "modifications": [],
            },
        },
        rls_policies=[
            {
                "name": "users_select_own",
                "table": "users",
                "policy_type": "SELECT",
                "roles": ["authenticated"],
                "using_clause": "auth.uid() = id",
            },
            {
                "name": "lessons_public_select",
                "table": "lessons",
                "policy_type": "SELECT",
                "roles": ["anon", "authenticated"],
                "using_clause": "status = 'published'",
            },
            {
                "name": "enrollments_student_own",
                "table": "enrollments",
                "policy_type": "ALL",
                "roles": ["authenticated"],
                "using_clause": "auth.uid() = student_id",
            },
        ],
        data_migrations=[
            {
                "table": "organizations",
                "estimated_rows": 100,
                "estimated_time": 1,
                "batch_size": 1000,
            },
            {"table": "users", "estimated_rows": 5000, "estimated_time": 5, "batch_size": 1000},
            {"table": "lessons", "estimated_rows": 10000, "estimated_time": 10, "batch_size": 1000},
            {
                "table": "enrollments",
                "estimated_rows": 50000,
                "estimated_time": 50,
                "batch_size": 1000,
            },
        ],
        edge_functions=[
            {"name": "user-authentication", "endpoint": "/api/auth/login", "method": "POST"},
            {"name": "lesson-enrollment", "endpoint": "/api/lessons/enroll", "method": "POST"},
        ],
        storage_buckets=[
            {"name": "lesson-content", "type": "private", "file_count": 1000},
            {"name": "user-avatars", "type": "public", "file_count": 500},
        ],
        type_definitions={
            "User": "interface User { id: string; email: string; role: UserRole; }",
            "Lesson": "interface Lesson { id: string; title: string; status: ContentStatus; }",
            "Enrollment": "interface Enrollment { id: string; student_id: string; lesson_id: string; }",
        },
        rollback_procedures=[
            {
                "step": "schema",
                "procedure": "rollback_schema",
                "commands": [
                    "DROP TABLE IF EXISTS users CASCADE;",
                    "DROP TABLE IF EXISTS lessons CASCADE;",
                ],
            },
            {
                "step": "rls",
                "procedure": "rollback_rls",
                "commands": [
                    "DROP POLICY IF EXISTS users_select_own;",
                    "DROP POLICY IF EXISTS lessons_public_select;",
                ],
            },
        ],
        estimated_duration=66,  # Sum of all data migration times
        risk_assessment={
            "level": "medium",
            "factors": ["large_data_volume", "complex_relationships"],
            "mitigations": ["Use batch processing", "Test rollback procedures"],
        },
    )


@pytest.fixture
def mock_asyncpg_connection():
    """Create a comprehensive mock asyncpg connection."""
    mock_conn = AsyncMock()

    # Default return values
    mock_conn.fetchval.return_value = 1000
    mock_conn.fetch.return_value = []
    mock_conn.fetchrow.return_value = None
    mock_conn.execute.return_value = None
    mock_conn.executemany.return_value = None
    mock_conn.close.return_value = None

    return mock_conn


@pytest.fixture
def migration_validation_scenarios():
    """Provide various validation scenarios for testing."""
    return {
        "successful_validation": {
            "schema_validation": {
                "status": "passed",
                "tables_matched": True,
                "columns_matched": True,
            },
            "data_validation": {
                "status": "passed",
                "row_counts_matched": True,
                "data_integrity": "verified",
            },
            "performance_comparison": {
                "status": "passed",
                "query_performance": "improved",
                "latency_reduction": "15%",
            },
            "security_validation": {
                "status": "passed",
                "rls_enabled": True,
                "encryption": "enabled",
            },
        },
        "failed_validation": {
            "schema_validation": {
                "status": "failed",
                "tables_matched": False,
                "issues": ["Missing table: user_sessions"],
            },
            "data_validation": {
                "status": "failed",
                "row_counts_matched": False,
                "issues": ["Row count mismatch in users table: 5000 vs 4995"],
            },
            "performance_comparison": {"status": "passed", "query_performance": "similar"},
            "security_validation": {
                "status": "failed",
                "rls_enabled": False,
                "issues": ["RLS not enabled on sensitive tables"],
            },
        },
    }


@pytest.fixture
def migration_complexity_scenarios():
    """Provide various complexity scenarios for testing."""
    return {
        "simple": {
            "table_count": 5,
            "relationship_count": 3,
            "total_rows": 10000,
            "expected_level": "low",
            "expected_duration": 30,
        },
        "medium": {
            "table_count": 25,
            "relationship_count": 35,
            "total_rows": 500000,
            "expected_level": "medium",
            "expected_duration": 180,
        },
        "complex": {
            "table_count": 75,
            "relationship_count": 150,
            "total_rows": 5000000,
            "expected_level": "high",
            "expected_duration": 720,
        },
    }


@pytest.fixture
async def temp_backup_files():
    """Create temporary backup files for testing."""
    backup_files = {}

    for table_name in ["users", "lessons", "enrollments"]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            backup_data = [{"id": f"test-{i}", "name": f"Test {i}"} for i in range(10)]
            json.dump(backup_data, f)
            backup_files[table_name] = f.name

    yield backup_files

    # Cleanup
    import os

    for file_path in backup_files.values():
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass


@pytest.fixture
def performance_metrics():
    """Provide performance metrics for testing."""
    return {
        "baseline": {
            "avg_query_time": 150,  # milliseconds
            "throughput": 1000,  # queries per second
            "connection_pool_usage": 60,  # percentage
            "memory_usage": 512,  # MB
        },
        "target": {
            "avg_query_time": 120,  # 20% improvement
            "throughput": 1200,  # 20% improvement
            "connection_pool_usage": 45,  # Better efficiency
            "memory_usage": 480,  # Lower memory usage
        },
    }


class SupabaseMigrationTestHelper:
    """Helper class for Supabase migration testing."""

    @staticmethod
    def create_mock_agent(state_manager=None):
        """Create a mock migration agent for testing."""
        if state_manager is None:
            state_manager = Mock(spec=StateManager)
            state_manager.update_state = Mock()
            state_manager.get_state = Mock(return_value={})

        agent = SupabaseMigrationAgent(state_manager=state_manager)
        return agent

    @staticmethod
    def extract_relationships_from_schema(schema: dict[str, Any]) -> dict[str, Any]:
        """Extract relationships from schema for testing."""
        relationships = {
            "foreign_keys": [],
            "primary_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "dependencies": {},
        }

        for table in schema.get("tables", []):
            table_name = table["name"]

            # Extract foreign keys
            for fk in table.get("foreign_keys", []):
                relationships["foreign_keys"].append(
                    {
                        "source_table": table_name,
                        "source_column": fk["constrained_columns"],
                        "target_table": fk["referred_table"],
                        "target_column": fk["referred_columns"],
                        "name": fk["name"],
                    }
                )

            # Extract primary keys
            if table.get("primary_key"):
                relationships["primary_keys"].append(
                    {"table": table_name, "columns": table["primary_key"]["constrained_columns"]}
                )

            # Build dependencies
            relationships["dependencies"][table_name] = [
                fk["referred_table"] for fk in table.get("foreign_keys", [])
            ]

        return relationships

    @staticmethod
    def validate_migration_plan(plan: MigrationPlan) -> dict[str, Any]:
        """Validate a migration plan structure."""
        validation = {"is_valid": True, "issues": []}

        # Check required fields
        if not plan.schema_mappings:
            validation["is_valid"] = False
            validation["issues"].append("No schema mappings defined")

        if not plan.rls_policies:
            validation["is_valid"] = False
            validation["issues"].append("No RLS policies defined")

        if plan.estimated_duration <= 0:
            validation["is_valid"] = False
            validation["issues"].append("Invalid estimated duration")

        # Validate risk assessment
        if "level" not in plan.risk_assessment:
            validation["is_valid"] = False
            validation["issues"].append("Risk assessment missing level")

        return validation

    @staticmethod
    def calculate_migration_metrics(plan: MigrationPlan) -> dict[str, Any]:
        """Calculate migration metrics from plan."""
        total_tables = len(plan.schema_mappings)
        total_policies = len(plan.rls_policies)
        total_functions = len(plan.edge_functions)
        total_buckets = len(plan.storage_buckets)

        total_rows = sum(migration.get("estimated_rows", 0) for migration in plan.data_migrations)

        return {
            "total_tables": total_tables,
            "total_policies": total_policies,
            "total_functions": total_functions,
            "total_buckets": total_buckets,
            "total_rows": total_rows,
            "estimated_duration": plan.estimated_duration,
            "complexity_score": (total_tables * 2) + (total_policies * 1) + (total_functions * 3),
        }


@pytest.fixture
def migration_test_helper():
    """Provide the migration test helper."""
    return SupabaseMigrationTestHelper
