"""
Integration tests for Supabase migration system.

This module provides comprehensive integration tests for the complete
Supabase migration workflow, including end-to-end testing of all components.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.agents.supabase.supabase_migration_agent import (
    MigrationPlan,
    SupabaseMigrationAgent,
)
from core.agents.supabase.tools.data_migration import DataMigrationTool
from core.agents.supabase.tools.rls_policy_generator import RLSPolicyGeneratorTool
from core.agents.supabase.tools.schema_analyzer import SchemaAnalyzerTool
from core.sparc.state_manager import StateManager


@pytest.fixture
def mock_database_connections():
    """Mock database connections for testing."""
    return {
        "source": "postgresql://user:pass@localhost:5432/source_db",
        "target": "postgresql://user:pass@localhost:5433/target_db",
    }


@pytest.fixture
def sample_production_schema():
    """Provide a realistic production-like schema for testing."""
    return {
        "database": "educational_platform",
        "tables": [
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
                    {"name": "role", "type": "user_role", "nullable": False, "default": "student"},
                    {"name": "organization_id", "type": "UUID", "nullable": True},
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
                    {
                        "name": "updated_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
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
                "row_count": 10000,
                "size_bytes": 1048576,
            },
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
                    {
                        "name": "subscription_plan",
                        "type": "VARCHAR(50)",
                        "nullable": False,
                        "default": "free",
                    },
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
                    {
                        "name": "updated_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
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
                "row_count": 500,
                "size_bytes": 65536,
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
                    {
                        "name": "difficulty_level",
                        "type": "INTEGER",
                        "nullable": False,
                        "default": "1",
                    },
                    {"name": "estimated_duration", "type": "INTEGER", "nullable": True},
                    {"name": "created_by", "type": "UUID", "nullable": False},
                    {"name": "organization_id", "type": "UUID", "nullable": False},
                    {
                        "name": "status",
                        "type": "content_status",
                        "nullable": False,
                        "default": "draft",
                    },
                    {"name": "published_at", "type": "TIMESTAMP", "nullable": True},
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
                    {
                        "name": "updated_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
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
                    {"name": "idx_lessons_status", "column_names": ["status"], "unique": False},
                ],
                "unique_constraints": [],
                "check_constraints": [
                    {"name": "ck_lessons_difficulty", "sqltext": "difficulty_level BETWEEN 1 AND 5"}
                ],
                "row_count": 25000,
                "size_bytes": 10485760,
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
                    {
                        "name": "progress_percentage",
                        "type": "INTEGER",
                        "nullable": False,
                        "default": "0",
                    },
                    {"name": "completed_at", "type": "TIMESTAMP", "nullable": True},
                    {"name": "last_accessed_at", "type": "TIMESTAMP", "nullable": True},
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
                    {
                        "name": "updated_at",
                        "type": "TIMESTAMP",
                        "nullable": False,
                        "default": "NOW()",
                    },
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
                "row_count": 150000,
                "size_bytes": 20971520,
            },
        ],
        "views": [
            {
                "name": "user_progress_summary",
                "columns": [
                    {"name": "user_id", "type": "UUID"},
                    {"name": "total_lessons", "type": "BIGINT"},
                    {"name": "completed_lessons", "type": "BIGINT"},
                    {"name": "average_progress", "type": "NUMERIC"},
                ],
                "definition": """
                    SELECT
                        student_id as user_id,
                        COUNT(*) as total_lessons,
                        COUNT(completed_at) as completed_lessons,
                        AVG(progress_percentage) as average_progress
                    FROM enrollments
                    GROUP BY student_id
                """,
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
        "functions": [
            {"name": "calculate_user_progress", "type": "FUNCTION", "return_type": "numeric"},
            {"name": "update_lesson_statistics", "type": "PROCEDURE", "return_type": "void"},
        ],
        "triggers": [
            {
                "name": "update_user_timestamp",
                "table": "users",
                "event": "UPDATE",
                "timing": "BEFORE",
            },
            {
                "name": "enrollment_progress_trigger",
                "table": "enrollments",
                "event": "UPDATE",
                "timing": "AFTER",
            },
        ],
        "enums": [
            {"name": "user_role", "values": ["student", "teacher", "admin", "super_admin"]},
            {"name": "content_status", "values": ["draft", "review", "published", "archived"]},
        ],
    }


@pytest.fixture
def sample_access_patterns():
    """Provide realistic access patterns for testing."""
    return {
        "users": {
            "multi_tenant": True,
            "hierarchical": False,
            "time_based": False,
            "access_frequency": "high",
            "read_write_ratio": "70:30",
        },
        "organizations": {
            "multi_tenant": False,
            "hierarchical": True,
            "time_based": False,
            "access_frequency": "medium",
            "read_write_ratio": "90:10",
        },
        "lessons": {
            "multi_tenant": True,
            "hierarchical": False,
            "time_based": True,
            "access_frequency": "high",
            "read_write_ratio": "80:20",
        },
        "enrollments": {
            "multi_tenant": True,
            "hierarchical": False,
            "time_based": False,
            "access_frequency": "very_high",
            "read_write_ratio": "60:40",
        },
    }


class TestSupabaseMigrationIntegration:
    """Integration tests for the complete migration workflow."""

    @pytest.mark.asyncio
    async def test_full_migration_workflow(
        self, mock_database_connections, sample_production_schema, sample_access_patterns
    ):
        """Test the complete migration workflow from analysis to validation."""
        # Initialize agent
        state_manager = Mock(spec=StateManager)
        state_manager.update_state = Mock()
        state_manager.get_state = Mock(return_value={})

        agent = SupabaseMigrationAgent(state_manager=state_manager)

        # Mock all external dependencies
        with (
            patch.object(agent.schema_analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
            patch.object(
                agent.schema_analyzer, "extract_relationships", new_callable=AsyncMock
            ) as mock_relationships,
            patch.object(
                agent.rls_generator, "generate_policies", new_callable=AsyncMock
            ) as mock_policies,
            patch.object(
                agent.edge_converter, "convert_endpoints", new_callable=AsyncMock
            ) as mock_edge,
            patch.object(
                agent.storage_migrator, "plan_migration", new_callable=AsyncMock
            ) as mock_storage,
            patch.object(
                agent.type_generator, "generate_types", new_callable=AsyncMock
            ) as mock_types,
            patch.object(agent, "_sparc_reasoning", new_callable=AsyncMock) as mock_sparc,
        ):

            # Setup mock responses
            mock_analyze.return_value = sample_production_schema
            mock_relationships.return_value = self._extract_relationships_from_schema(
                sample_production_schema
            )
            mock_policies.return_value = self._generate_expected_policies()
            mock_edge.return_value = self._generate_expected_edge_functions()
            mock_storage.return_value = self._generate_expected_storage_buckets()
            mock_types.return_value = self._generate_expected_types()
            mock_sparc.return_value = Mock()

            # Step 1: Database Analysis
            analysis_results = await agent.analyze_database(
                mock_database_connections["source"], "educational_platform"
            )

            assert "schema" in analysis_results
            assert "relationships" in analysis_results
            assert "complexity" in analysis_results
            assert "recommendations" in analysis_results
            assert len(analysis_results["schema"]["tables"]) == 4

            # Step 2: Migration Plan Generation
            migration_plan = await agent.generate_migration_plan(
                analysis_results, {"migration_type": "full", "preserve_data": True}
            )

            assert isinstance(migration_plan, MigrationPlan)
            assert len(migration_plan.schema_mappings) > 0
            assert len(migration_plan.rls_policies) > 0
            assert len(migration_plan.edge_functions) > 0
            assert migration_plan.estimated_duration > 0
            assert "level" in migration_plan.risk_assessment

            # Step 3: Dry Run Execution
            dry_run_results = await agent.execute_migration(migration_plan, dry_run=True)

            assert dry_run_results["status"] == "completed"
            assert dry_run_results["dry_run"] is True
            assert len(dry_run_results["steps"]) == 7  # All migration phases

            # All steps should be simulated
            for step in dry_run_results["steps"]:
                assert step["status"] == "simulated"

            # Step 4: Validation
            validation_results = await agent.validate_migration(
                mock_database_connections["source"], mock_database_connections["target"]
            )

            assert validation_results["overall_status"] == "passed"
            assert "schema_validation" in validation_results
            assert "data_validation" in validation_results
            assert "security_validation" in validation_results

    @pytest.mark.asyncio
    async def test_schema_analysis_integration(
        self, mock_database_connections, sample_production_schema
    ):
        """Test schema analysis integration with realistic data."""
        tool = SchemaAnalyzerTool()

        with (
            patch("sqlalchemy.create_engine") as mock_engine,
            patch("sqlalchemy.inspect") as mock_inspect,
        ):

            # Mock engine and inspector
            mock_engine.return_value.dispose = Mock()
            mock_inspector_instance = Mock()
            mock_inspect.return_value = mock_inspector_instance

            # Setup inspector mock responses
            self._setup_inspector_mocks(mock_inspector_instance, sample_production_schema)

            # Mock async methods
            with (
                patch.object(tool, "_get_row_count", new_callable=AsyncMock) as mock_row_count,
                patch.object(tool, "_get_table_size", new_callable=AsyncMock) as mock_table_size,
                patch.object(tool, "_get_sequences", new_callable=AsyncMock) as mock_sequences,
                patch.object(tool, "_get_enums", new_callable=AsyncMock) as mock_enums,
                patch.object(tool, "_get_functions", new_callable=AsyncMock) as mock_functions,
                patch.object(tool, "_get_triggers", new_callable=AsyncMock) as mock_triggers,
                patch.object(tool, "_get_view_definition", new_callable=AsyncMock) as mock_view_def,
            ):

                # Setup async mock responses
                mock_row_count.side_effect = lambda table: {
                    "users": 10000,
                    "organizations": 500,
                    "lessons": 25000,
                    "enrollments": 150000,
                }[table]

                mock_table_size.side_effect = lambda table: {
                    "users": 1048576,
                    "organizations": 65536,
                    "lessons": 10485760,
                    "enrollments": 20971520,
                }[table]

                mock_sequences.return_value = sample_production_schema["sequences"]
                mock_enums.return_value = sample_production_schema["enums"]
                mock_functions.return_value = sample_production_schema["functions"]
                mock_triggers.return_value = sample_production_schema["triggers"]
                mock_view_def.return_value = sample_production_schema["views"][0]["definition"]

                # Execute analysis
                result = await tool.analyze(
                    mock_database_connections["source"], "educational_platform"
                )

                # Validate results
                assert result["database"] == "educational_platform"
                assert len(result["tables"]) == 4
                assert len(result["views"]) == 1
                assert len(result["sequences"]) == 1
                assert len(result["functions"]) == 2
                assert len(result["triggers"]) == 2
                assert len(result["enums"]) == 2

                # Validate table details
                users_table = next(t for t in result["tables"] if t["name"] == "users")
                assert users_table["row_count"] == 10000
                assert users_table["size_bytes"] == 1048576
                assert len(users_table["foreign_keys"]) == 1

                lessons_table = next(t for t in result["tables"] if t["name"] == "lessons")
                assert len(lessons_table["foreign_keys"]) == 2
                assert lessons_table["row_count"] == 25000

    @pytest.mark.asyncio
    async def test_rls_policy_generation_integration(
        self, sample_production_schema, sample_access_patterns
    ):
        """Test RLS policy generation with realistic schema."""
        tool = RLSPolicyGeneratorTool()

        policies = await tool.generate_policies(sample_production_schema, sample_access_patterns)

        # Validate policy generation
        assert len(policies) > 0

        # Check user table policies
        user_policies = [p for p in policies if p["table"] == "users"]
        assert len(user_policies) >= 3  # select_own, update_own, admin_all
        assert any("tenant_isolation" in p["name"] for p in user_policies)  # Multi-tenant pattern

        # Check lesson table policies
        lesson_policies = [p for p in policies if p["table"] == "lessons"]
        assert len(lesson_policies) >= 4  # content policies
        assert any("time_based" in p["name"] for p in lesson_policies)  # Time-based pattern

        # Check organization table policies
        org_policies = [p for p in policies if p["table"] == "organizations"]
        assert len(org_policies) >= 2
        assert any("hierarchical" in p["name"] for p in org_policies)  # Hierarchical pattern

        # Validate policy structure
        for policy in policies:
            assert "name" in policy
            assert "table" in policy
            assert "policy_type" in policy
            assert "roles" in policy
            assert "using_clause" in policy

        # Test SQL generation
        sql = tool.generate_sql(policies)
        assert "ALTER TABLE" in sql
        assert "CREATE POLICY" in sql
        assert "ENABLE ROW LEVEL SECURITY" in sql

        # Test policy validation
        validation_results = tool.validate_policies(policies, sample_production_schema)
        assert all(result["valid"] for result in validation_results)

    @pytest.mark.asyncio
    async def test_data_migration_integration(
        self, mock_database_connections, sample_production_schema
    ):
        """Test data migration with realistic schema and batch processing."""
        tool = DataMigrationTool(batch_size=1000, max_concurrent_batches=3)

        # Mock connections and data
        mock_conn = AsyncMock()

        with patch("asyncpg.connect", return_value=mock_conn):
            # Mock table list
            mock_conn.fetch.return_value = [
                {"table_name": "organizations"},
                {"table_name": "users"},
                {"table_name": "lessons"},
                {"table_name": "enrollments"},
            ]

            # Mock individual table migrations
            with patch.object(tool, "migrate_table", new_callable=AsyncMock) as mock_migrate:
                # Setup migration results for each table
                def get_migration_result(source, target, table_name, **kwargs):
                    row_counts = {
                        "organizations": 500,
                        "users": 10000,
                        "lessons": 25000,
                        "enrollments": 150000,
                    }

                    from core.agents.supabase.tools.data_migration import (
                        MigrationResult,
                        MigrationStatus,
                    )

                    return MigrationResult(
                        table_name=table_name,
                        total_rows=row_counts.get(table_name, 0),
                        migrated_rows=row_counts.get(table_name, 0),
                        failed_rows=0,
                        batches_completed=max(1, row_counts.get(table_name, 0) // 1000),
                        duration_seconds=row_counts.get(table_name, 0) / 1000,  # Simulate time
                        status=MigrationStatus.COMPLETED,
                    )

                mock_migrate.side_effect = get_migration_result

                # Execute database migration
                results = await tool.migrate_database(
                    mock_database_connections["source"],
                    mock_database_connections["target"],
                    dry_run=True,
                )

                # Validate results
                assert len(results) == 4
                assert all(
                    table in results
                    for table in ["organizations", "users", "lessons", "enrollments"]
                )

                # Check that all migrations completed successfully
                from core.agents.supabase.tools.data_migration import MigrationStatus

                assert all(
                    result.status == MigrationStatus.COMPLETED for result in results.values()
                )

                # Check total rows migrated
                total_migrated = sum(result.migrated_rows for result in results.values())
                assert total_migrated == 185500  # Sum of all table row counts

    @pytest.mark.asyncio
    async def test_migration_with_complex_dependencies(
        self, mock_database_connections, sample_production_schema
    ):
        """Test migration handling of complex foreign key dependencies."""
        agent = SupabaseMigrationAgent()

        # Extract dependency information from schema
        relationships = self._extract_relationships_from_schema(sample_production_schema)

        # Validate dependency ordering
        assert len(relationships["foreign_keys"]) > 0

        # Organizations should have no dependencies
        org_deps = relationships["dependencies"]["organizations"]
        assert len(org_deps) == 0

        # Users should depend on organizations
        user_deps = relationships["dependencies"]["users"]
        assert "organizations" in user_deps

        # Lessons should depend on both users and organizations
        lesson_deps = relationships["dependencies"]["lessons"]
        assert "users" in lesson_deps
        assert "organizations" in lesson_deps

        # Enrollments should depend on users and lessons
        enrollment_deps = relationships["dependencies"]["enrollments"]
        assert "users" in enrollment_deps
        assert "lessons" in enrollment_deps

    @pytest.mark.asyncio
    async def test_migration_rollback_integration(self, mock_database_connections):
        """Test migration rollback functionality."""
        agent = SupabaseMigrationAgent()

        # Create a test migration plan
        plan = MigrationPlan(
            schema_mappings={
                "users": {"original": {"name": "users"}, "supabase": {"name": "users"}},
                "lessons": {"original": {"name": "lessons"}, "supabase": {"name": "lessons"}},
            },
            rls_policies=[
                {"name": "users_select_own", "table": "users"},
                {"name": "lessons_public_select", "table": "lessons"},
            ],
        )

        # Mock rollback execution
        with patch.object(agent, "_execute_rollback", new_callable=AsyncMock) as mock_rollback:
            mock_rollback.return_value = {"status": "rolled_back", "procedures_executed": 2}

            # Simulate failed migration
            with patch.object(agent, "_migrate_schema", new_callable=AsyncMock) as mock_migrate:
                mock_migrate.side_effect = Exception("Migration failed")

                result = await agent.execute_migration(plan, dry_run=False)

                assert result["status"] == "failed"
                assert "rollback" in result
                assert result["rollback"]["status"] == "rolled_back"

    @pytest.mark.asyncio
    async def test_migration_validation_comprehensive(self, mock_database_connections):
        """Test comprehensive migration validation."""
        agent = SupabaseMigrationAgent()

        # Mock validation methods
        with (
            patch.object(agent, "_validate_schema", new_callable=AsyncMock) as mock_schema_val,
            patch.object(agent, "_validate_data", new_callable=AsyncMock) as mock_data_val,
            patch.object(agent, "_compare_performance", new_callable=AsyncMock) as mock_perf_val,
            patch.object(agent, "_validate_security", new_callable=AsyncMock) as mock_security_val,
        ):

            # Setup validation responses
            mock_schema_val.return_value = {
                "status": "passed",
                "tables_matched": True,
                "columns_matched": True,
                "constraints_verified": True,
            }

            mock_data_val.return_value = {
                "status": "passed",
                "row_counts_matched": True,
                "data_integrity": "verified",
                "sample_validation": {"accuracy": 0.999},
            }

            mock_perf_val.return_value = {
                "status": "passed",
                "query_performance": "improved",
                "latency_reduction": "25%",
                "throughput_increase": "15%",
            }

            mock_security_val.return_value = {
                "status": "passed",
                "rls_enabled": True,
                "encryption": "enabled",
                "audit_logging": "configured",
            }

            # Execute validation
            result = await agent.validate_migration(
                mock_database_connections["source"], mock_database_connections["target"]
            )

            # Validate comprehensive results
            assert result["overall_status"] == "passed"
            assert result["schema_validation"]["status"] == "passed"
            assert result["data_validation"]["status"] == "passed"
            assert result["performance_comparison"]["status"] == "passed"
            assert result["security_validation"]["status"] == "passed"

    @pytest.mark.asyncio
    async def test_migration_with_large_dataset_simulation(self, mock_database_connections):
        """Test migration behavior with large dataset simulation."""
        tool = DataMigrationTool(batch_size=5000, max_concurrent_batches=10)

        # Simulate large table migration
        large_table_data = {
            "table": "large_table",
            "total_rows": 1000000,  # 1 million rows
            "estimated_time": 100,  # 100 minutes
        }

        # Mock batch processing
        with (
            patch.object(tool, "_get_row_count", new_callable=AsyncMock) as mock_count,
            patch.object(tool, "_execute_migration", new_callable=AsyncMock) as mock_execute,
        ):

            mock_count.return_value = large_table_data["total_rows"]

            # Simulate successful large migration
            from core.agents.supabase.tools.data_migration import (
                MigrationResult,
                MigrationStatus,
            )

            mock_execute.return_value = MigrationResult(
                table_name=large_table_data["table"],
                total_rows=large_table_data["total_rows"],
                migrated_rows=large_table_data["total_rows"],
                failed_rows=0,
                batches_completed=200,  # 1M / 5K batch size
                duration_seconds=large_table_data["estimated_time"] * 60,
                status=MigrationStatus.COMPLETED,
            )

            # Execute migration
            result = await tool.migrate_table(
                mock_database_connections["source"],
                mock_database_connections["target"],
                large_table_data["table"],
                dry_run=True,
            )

            # Validate large dataset handling
            assert result.status == MigrationStatus.COMPLETED
            assert result.total_rows == 1000000
            assert result.batches_completed == 200

    def _extract_relationships_from_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Helper to extract relationships from schema for testing."""
        relationships = {
            "foreign_keys": [],
            "primary_keys": [],
            "unique_constraints": [],
            "check_constraints": [],
            "dependencies": {},
        }

        for table in schema["tables"]:
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

    def _generate_expected_policies(self) -> list[dict[str, Any]]:
        """Helper to generate expected RLS policies for testing."""
        return [
            {
                "name": "users_select_own",
                "table": "users",
                "policy_type": "SELECT",
                "roles": ["authenticated"],
                "using_clause": "auth.uid() = id",
            },
            {
                "name": "organizations_admin_only",
                "table": "organizations",
                "policy_type": "ALL",
                "roles": ["authenticated"],
                "using_clause": "auth.jwt() ->> 'role' = 'admin'",
            },
            {
                "name": "lessons_public_select",
                "table": "lessons",
                "policy_type": "SELECT",
                "roles": ["anon", "authenticated"],
                "using_clause": "status = 'published'",
            },
        ]

    def _generate_expected_edge_functions(self) -> list[dict[str, Any]]:
        """Helper to generate expected Edge Functions for testing."""
        return [
            {
                "name": "user-authentication",
                "endpoint": "/api/auth/login",
                "method": "POST",
                "description": "Handle user authentication",
            },
            {
                "name": "lesson-enrollment",
                "endpoint": "/api/lessons/enroll",
                "method": "POST",
                "description": "Handle lesson enrollment",
            },
        ]

    def _generate_expected_storage_buckets(self) -> list[dict[str, Any]]:
        """Helper to generate expected storage buckets for testing."""
        return [
            {"name": "lesson-content", "type": "private", "file_count": 1500},
            {"name": "user-avatars", "type": "public", "file_count": 500},
        ]

    def _generate_expected_types(self) -> dict[str, str]:
        """Helper to generate expected TypeScript types for testing."""
        return {
            "User": """
                interface User {
                    id: string;
                    email: string;
                    first_name?: string;
                    last_name?: string;
                    role: UserRole;
                    organization_id?: string;
                    created_at: string;
                    updated_at: string;
                }
            """,
            "Lesson": """
                interface Lesson {
                    id: string;
                    title: string;
                    description?: string;
                    content?: object;
                    difficulty_level: number;
                    created_by: string;
                    organization_id: string;
                    status: ContentStatus;
                    published_at?: string;
                    created_at: string;
                    updated_at: string;
                }
            """,
        }

    def _setup_inspector_mocks(self, inspector_mock, schema: dict[str, Any]):
        """Helper to setup SQLAlchemy inspector mocks."""
        # Mock table names
        inspector_mock.get_table_names.return_value = [table["name"] for table in schema["tables"]]

        # Mock view names
        inspector_mock.get_view_names.return_value = [view["name"] for view in schema["views"]]

        # Mock columns, keys, etc. for each table
        def get_columns(table_name):
            table = next(t for t in schema["tables"] if t["name"] == table_name)
            return table["columns"]

        def get_pk_constraint(table_name):
            table = next(t for t in schema["tables"] if t["name"] == table_name)
            return table.get("primary_key")

        def get_foreign_keys(table_name):
            table = next(t for t in schema["tables"] if t["name"] == table_name)
            return table.get("foreign_keys", [])

        inspector_mock.get_columns.side_effect = get_columns
        inspector_mock.get_pk_constraint.side_effect = get_pk_constraint
        inspector_mock.get_foreign_keys.side_effect = get_foreign_keys
