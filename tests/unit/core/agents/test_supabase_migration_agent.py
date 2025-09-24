"""
Unit tests for SupabaseMigrationAgent.

This module provides comprehensive unit tests for the Supabase migration agent,
including initialization, database analysis, migration planning, and execution.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from core.agents.supabase.supabase_migration_agent import (
    SupabaseMigrationAgent,
    MigrationPlan
)
from core.sparc.state_manager import StateManager
from core.coordinators.base_coordinator import TaskOutput


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    mock_manager = Mock(spec=StateManager)
    mock_manager.update_state = Mock()
    mock_manager.get_state = Mock(return_value={})
    return mock_manager


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock_llm = AsyncMock()
    mock_llm.agenerate = AsyncMock(return_value=Mock(generations=[[Mock(text="Test response")]]))
    return mock_llm


@pytest.fixture
def sample_schema_data():
    """Provide sample schema data for testing."""
    return {
        'database': 'test_db',
        'tables': [
            {
                'name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'nullable': False},
                    {'name': 'email', 'type': 'VARCHAR(255)', 'nullable': False},
                    {'name': 'created_at', 'type': 'TIMESTAMP', 'nullable': True}
                ],
                'primary_key': {'constrained_columns': ['id']},
                'foreign_keys': [],
                'indexes': [],
                'unique_constraints': [],
                'check_constraints': [],
                'row_count': 1000,
                'size_bytes': 65536
            },
            {
                'name': 'posts',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER', 'nullable': False},
                    {'name': 'user_id', 'type': 'INTEGER', 'nullable': False},
                    {'name': 'title', 'type': 'VARCHAR(255)', 'nullable': False},
                    {'name': 'content', 'type': 'TEXT', 'nullable': True}
                ],
                'primary_key': {'constrained_columns': ['id']},
                'foreign_keys': [{
                    'name': 'fk_posts_user_id',
                    'constrained_columns': ['user_id'],
                    'referred_table': 'users',
                    'referred_columns': ['id']
                }],
                'indexes': [],
                'unique_constraints': [],
                'check_constraints': [],
                'row_count': 5000,
                'size_bytes': 262144
            }
        ],
        'views': [],
        'sequences': [],
        'functions': [],
        'triggers': [],
        'enums': []
    }


@pytest.fixture
def sample_analysis_results(sample_schema_data):
    """Provide sample analysis results for testing."""
    return {
        'schema': sample_schema_data,
        'relationships': {
            'foreign_keys': [{
                'source_table': 'posts',
                'source_column': ['user_id'],
                'target_table': 'users',
                'target_column': ['id'],
                'name': 'fk_posts_user_id'
            }],
            'primary_keys': [
                {'table': 'users', 'columns': ['id']},
                {'table': 'posts', 'columns': ['id']}
            ],
            'unique_constraints': [],
            'check_constraints': [],
            'dependencies': {
                'users': [],
                'posts': ['users']
            }
        },
        'complexity': {
            'level': 'medium',
            'factors': ['foreign_keys'],
            'estimated_effort': 75
        },
        'recommendations': ['Plan careful foreign key migration with dependency ordering']
    }


class TestSupabaseMigrationAgent:
    """Test cases for SupabaseMigrationAgent."""

    def test_agent_initialization(self, mock_llm, mock_state_manager):
        """Test agent initialization with proper tools and state."""
        agent = SupabaseMigrationAgent(
            llm=mock_llm,
            state_manager=mock_state_manager
        )

        assert agent.name == "SupabaseMigrationAgent"
        assert agent.description == "Orchestrates PostgreSQL to Supabase migration"
        assert agent.llm == mock_llm
        assert agent.state_manager == mock_state_manager

        # Check tools are initialized
        assert hasattr(agent, 'schema_analyzer')
        assert hasattr(agent, 'rls_generator')
        assert hasattr(agent, 'data_migrator')
        assert hasattr(agent, 'vector_tool')
        assert hasattr(agent, 'edge_converter')
        assert hasattr(agent, 'storage_migrator')
        assert hasattr(agent, 'type_generator')

        # Check state tracking
        assert agent.current_migration is None
        assert agent.migration_history == []

    def test_agent_initialization_without_params(self):
        """Test agent initialization with default parameters."""
        agent = SupabaseMigrationAgent()

        assert agent.name == "SupabaseMigrationAgent"
        assert hasattr(agent, 'schema_analyzer')
        assert agent.current_migration is None

    @pytest.mark.asyncio
    async def test_analyze_database_success(self, mock_state_manager, sample_schema_data):
        """Test successful database analysis."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        # Mock the schema analyzer
        with patch.object(agent.schema_analyzer, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = sample_schema_data

            with patch.object(agent.schema_analyzer, 'extract_relationships', new_callable=AsyncMock) as mock_relationships:
                mock_relationships.return_value = {
                    'foreign_keys': [],
                    'primary_keys': [],
                    'unique_constraints': [],
                    'check_constraints': [],
                    'dependencies': {}
                }

                result = await agent.analyze_database(
                    "postgresql://user:pass@localhost/test",
                    "test_db"
                )

                assert 'schema' in result
                assert 'relationships' in result
                assert 'complexity' in result
                assert 'recommendations' in result

                # Verify state updates
                assert mock_state_manager.update_state.call_count >= 2

                # Check analyze was called correctly
                mock_analyze.assert_called_once_with(
                    "postgresql://user:pass@localhost/test",
                    "test_db"
                )

    @pytest.mark.asyncio
    async def test_analyze_database_failure(self, mock_state_manager):
        """Test database analysis failure handling."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        # Mock the schema analyzer to raise an exception
        with patch.object(agent.schema_analyzer, 'analyze', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception, match="Database connection failed"):
                await agent.analyze_database(
                    "postgresql://invalid:conn@localhost/test",
                    "test_db"
                )

            # Verify error state was set
            error_call = None
            for call in mock_state_manager.update_state.call_args_list:
                if 'error' in call[0][0]:
                    error_call = call[0][0]
                    break

            assert error_call is not None
            assert error_call['status'] == 'failed'
            assert 'Database connection failed' in error_call['error']

    def test_assess_complexity_low(self):
        """Test complexity assessment for simple schema."""
        agent = SupabaseMigrationAgent()

        simple_schema = {
            'tables': [
                {'name': 'users', 'columns': [{'name': 'id', 'type': 'INTEGER'}]}
            ]
        }
        simple_relationships = {'foreign_keys': []}

        complexity = agent._assess_complexity(simple_schema, simple_relationships)

        assert complexity['level'] == 'medium'  # Default level
        assert complexity['estimated_effort'] == 10  # 1 table * 10

    def test_assess_complexity_high(self):
        """Test complexity assessment for complex schema."""
        agent = SupabaseMigrationAgent()

        complex_schema = {
            'tables': [{'name': f'table_{i}', 'columns': []} for i in range(60)]
        }
        complex_relationships = {
            'foreign_keys': [{'name': f'fk_{i}'} for i in range(150)]
        }

        complexity = agent._assess_complexity(complex_schema, complex_relationships)

        assert complexity['level'] == 'high'
        assert 'high_table_count' in complexity['factors']
        assert 'complex_relationships' in complexity['factors']
        assert complexity['estimated_effort'] == 1350  # 60*10 + 150*5

    def test_assess_complexity_with_jsonb(self):
        """Test complexity assessment with JSONB columns."""
        agent = SupabaseMigrationAgent()

        schema_with_jsonb = {
            'tables': [{
                'name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'INTEGER'},
                    {'name': 'metadata', 'type': 'JSONB'}
                ]
            }]
        }
        relationships = {'foreign_keys': []}

        complexity = agent._assess_complexity(schema_with_jsonb, relationships)

        assert 'jsonb_columns' in complexity['factors']

    def test_generate_recommendations(self):
        """Test recommendation generation based on complexity."""
        agent = SupabaseMigrationAgent()

        # High complexity recommendations
        high_complexity = {
            'level': 'high',
            'factors': ['high_table_count', 'jsonb_columns', 'complex_relationships']
        }

        recommendations = agent._generate_recommendations(high_complexity)

        assert len(recommendations) == 3
        assert any('phased migration approach' in rec for rec in recommendations)
        assert any('JSONB column usage' in rec for rec in recommendations)
        assert any('foreign key migration' in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_migration_plan(self, mock_state_manager, sample_analysis_results):
        """Test migration plan generation."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        # Mock all tool methods
        with patch.object(agent, '_sparc_reasoning', new_callable=AsyncMock) as mock_sparc, \
             patch.object(agent.rls_generator, 'generate_policies', new_callable=AsyncMock) as mock_rls, \
             patch.object(agent.edge_converter, 'convert_endpoints', new_callable=AsyncMock) as mock_edge, \
             patch.object(agent.storage_migrator, 'plan_migration', new_callable=AsyncMock) as mock_storage, \
             patch.object(agent.type_generator, 'generate_types', new_callable=AsyncMock) as mock_types:

            # Setup return values
            mock_sparc.return_value = Mock()
            mock_rls.return_value = [{'name': 'user_policy', 'table': 'users'}]
            mock_edge.return_value = [{'name': 'user_api', 'endpoint': '/api/users'}]
            mock_storage.return_value = [{'name': 'user_files', 'type': 'public'}]
            mock_types.return_value = {'User': 'interface User { id: number; email: string; }'}

            plan = await agent.generate_migration_plan(sample_analysis_results)

            assert isinstance(plan, MigrationPlan)
            assert len(plan.rls_policies) == 1
            assert len(plan.edge_functions) == 1
            assert len(plan.storage_buckets) == 1
            assert len(plan.type_definitions) == 1
            assert plan.estimated_duration > 0
            assert 'level' in plan.risk_assessment

            # Verify the plan was stored
            assert agent.current_migration == plan
            assert len(agent.migration_history) == 1

    @pytest.mark.asyncio
    async def test_execute_migration_dry_run(self, mock_state_manager):
        """Test migration execution in dry run mode."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        plan = MigrationPlan(
            schema_mappings={'users': {'name': 'users'}},
            rls_policies=[{'name': 'user_policy'}],
            data_migrations=[{'table': 'users', 'row_count': 1000}],
            edge_functions=[{'name': 'user_api'}],
            storage_buckets=[{'name': 'user_files'}]
        )

        result = await agent.execute_migration(plan, dry_run=True)

        assert result['status'] == 'completed'
        assert result['dry_run'] is True
        assert 'start_time' in result
        assert 'end_time' in result
        assert len(result['steps']) == 7  # All migration phases

        # All steps should be simulated
        for step in result['steps']:
            assert step['status'] == 'simulated'

    @pytest.mark.asyncio
    async def test_execute_migration_actual(self, mock_state_manager):
        """Test actual migration execution."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        plan = MigrationPlan(
            schema_mappings={'users': {'name': 'users'}},
            rls_policies=[{'name': 'user_policy'}],
            data_migrations=[{'table': 'users', 'row_count': 1000}],
            edge_functions=[{'name': 'user_api'}],
            storage_buckets=[{'name': 'user_files'}]
        )

        result = await agent.execute_migration(plan, dry_run=False)

        assert result['status'] == 'completed'
        assert result['dry_run'] is False

        # All steps should be completed
        for step in result['steps']:
            assert step['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_execute_migration_with_failure(self, mock_state_manager):
        """Test migration execution with failure and rollback."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        plan = MigrationPlan()

        # Mock a step to fail
        with patch.object(agent, '_migrate_schema', new_callable=AsyncMock) as mock_schema:
            mock_schema.side_effect = Exception("Schema migration failed")

            result = await agent.execute_migration(plan, dry_run=False)

            assert result['status'] == 'failed'
            assert 'Schema migration failed' in result['error']
            assert 'rollback' in result

    @pytest.mark.asyncio
    async def test_validate_migration(self, mock_state_manager):
        """Test migration validation."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        result = await agent.validate_migration(
            "postgresql://source@localhost/source_db",
            "postgresql://target@localhost/target_db"
        )

        assert 'schema_validation' in result
        assert 'data_validation' in result
        assert 'performance_comparison' in result
        assert 'security_validation' in result
        assert result['overall_status'] == 'passed'

    def test_generate_schema_mappings(self, sample_schema_data):
        """Test schema mapping generation."""
        agent = SupabaseMigrationAgent()

        # Mock the async methods called within _generate_schema_mappings
        async def run_test():
            with patch.object(agent, '_convert_table_schema', new_callable=AsyncMock) as mock_convert:
                mock_convert.return_value = {'name': 'users', 'rls_enabled': True}

                mappings = await agent._generate_schema_mappings(sample_schema_data)

                assert 'users' in mappings
                assert 'posts' in mappings
                assert mappings['users']['original']['name'] == 'users'
                assert 'supabase' in mappings['users']
                assert 'modifications' in mappings['users']

        # Run the async test
        asyncio.run(run_test())

    def test_identify_modifications(self):
        """Test identification of required modifications."""
        agent = SupabaseMigrationAgent()

        # Table without UUID primary key
        table_without_uuid = {
            'name': 'users',
            'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'email', 'type': 'VARCHAR(255)'}
            ]
        }

        modifications = agent._identify_modifications(table_without_uuid)

        assert 'add_uuid_primary_key' in modifications
        assert 'add_timestamps' in modifications

    def test_identify_modifications_with_timestamps(self):
        """Test identification when timestamps already exist."""
        agent = SupabaseMigrationAgent()

        table_with_timestamps = {
            'name': 'users',
            'columns': [
                {'name': 'id', 'type': 'UUID'},
                {'name': 'created_at', 'type': 'TIMESTAMP'},
                {'name': 'updated_at', 'type': 'TIMESTAMP'}
            ]
        }

        modifications = agent._identify_modifications(table_with_timestamps)

        assert 'add_timestamps' not in modifications

    def test_estimate_duration(self):
        """Test duration estimation."""
        agent = SupabaseMigrationAgent()

        plan = MigrationPlan(
            schema_mappings={'table1': {}, 'table2': {}},
            data_migrations=[
                {'estimated_time': 15},
                {'estimated_time': 25}
            ],
            edge_functions=[{'name': 'func1'}, {'name': 'func2'}]
        )

        duration = agent._estimate_duration(plan)

        # 2 tables * 1 min + 40 min data + 2 functions * 2 min + 20% buffer
        expected = int((2 + 40 + 4) * 1.2)
        assert duration == expected

    def test_assess_risks_low(self):
        """Test risk assessment for low-risk migration."""
        agent = SupabaseMigrationAgent()

        plan = MigrationPlan(
            data_migrations=[{'row_count': 1000}],
            edge_functions=[{'name': 'simple_func'}]
        )

        risks = agent._assess_risks(plan)

        assert risks['level'] == 'low'
        assert len(risks['factors']) == 0

    def test_assess_risks_high_data_volume(self):
        """Test risk assessment for high data volume."""
        agent = SupabaseMigrationAgent()

        plan = MigrationPlan(
            data_migrations=[{'row_count': 2000000}],
            edge_functions=[{'name': f'func_{i}' for i in range(25)}]
        )

        risks = agent._assess_risks(plan)

        assert risks['level'] == 'medium'
        assert 'high_data_volume' in risks['factors']
        assert 'many_edge_functions' in risks['factors']
        assert 'batch processing' in ' '.join(risks['mitigations'])

    def test_get_rollback_commands(self):
        """Test rollback command generation."""
        agent = SupabaseMigrationAgent()

        plan = MigrationPlan(
            schema_mappings={'users': {}, 'posts': {}},
            rls_policies=[
                {'name': 'user_policy'},
                {'name': 'post_policy'}
            ]
        )

        schema_commands = agent._get_rollback_commands('schema', plan)
        rls_commands = agent._get_rollback_commands('rls', plan)

        assert len(schema_commands) == 2
        assert all('DROP TABLE' in cmd for cmd in schema_commands)

        assert len(rls_commands) == 2
        assert all('DROP POLICY' in cmd for cmd in rls_commands)

    @pytest.mark.asyncio
    async def test_process_task_analyze(self, mock_state_manager):
        """Test task processing for analysis."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        with patch.object(agent, 'analyze_database', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {'status': 'completed'}

            context = {
                'connection_string': 'postgresql://test@localhost/db',
                'database_name': 'test_db'
            }

            result = await agent.process_task('analyze database schema', context)

            assert isinstance(result, TaskOutput)
            assert result.success is True
            assert result.result['status'] == 'completed'
            assert result.metadata['agent'] == 'SupabaseMigrationAgent'

    @pytest.mark.asyncio
    async def test_process_task_plan(self, mock_state_manager, sample_analysis_results):
        """Test task processing for migration planning."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        with patch.object(agent, 'generate_migration_plan', new_callable=AsyncMock) as mock_plan:
            mock_plan.return_value = MigrationPlan()

            context = {
                'analysis_results': sample_analysis_results,
                'options': {'phased': True}
            }

            result = await agent.process_task('plan migration', context)

            assert isinstance(result, TaskOutput)
            assert result.success is True
            assert isinstance(result.result, MigrationPlan)

    @pytest.mark.asyncio
    async def test_process_task_execute(self, mock_state_manager):
        """Test task processing for migration execution."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)
        agent.current_migration = MigrationPlan()

        with patch.object(agent, 'execute_migration', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {'status': 'completed'}

            context = {'dry_run': True}

            result = await agent.process_task('execute migration', context)

            assert isinstance(result, TaskOutput)
            assert result.success is True
            assert result.result['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_process_task_validate(self, mock_state_manager):
        """Test task processing for validation."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        with patch.object(agent, 'validate_migration', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = {'overall_status': 'passed'}

            context = {
                'source_connection': 'postgresql://source@localhost/db',
                'target_connection': 'postgresql://target@localhost/db'
            }

            result = await agent.process_task('validate migration', context)

            assert isinstance(result, TaskOutput)
            assert result.success is True
            assert result.result['overall_status'] == 'passed'

    @pytest.mark.asyncio
    async def test_process_task_unknown(self, mock_state_manager):
        """Test task processing for unknown task type."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        result = await agent.process_task('unknown task', {})

        assert isinstance(result, TaskOutput)
        assert result.success is True
        assert 'Unknown task type' in result.result['error']

    @pytest.mark.asyncio
    async def test_process_task_with_exception(self, mock_state_manager):
        """Test task processing with exception handling."""
        agent = SupabaseMigrationAgent(state_manager=mock_state_manager)

        with patch.object(agent, 'analyze_database', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("Database error")

            context = {
                'connection_string': 'postgresql://test@localhost/db',
                'database_name': 'test_db'
            }

            result = await agent.process_task('analyze database', context)

            assert isinstance(result, TaskOutput)
            assert result.success is False
            assert 'Database error' in result.error


class TestMigrationPlan:
    """Test cases for MigrationPlan dataclass."""

    def test_migration_plan_defaults(self):
        """Test MigrationPlan initialization with defaults."""
        plan = MigrationPlan()

        assert plan.schema_mappings == {}
        assert plan.rls_policies == []
        assert plan.data_migrations == []
        assert plan.edge_functions == []
        assert plan.storage_buckets == []
        assert plan.type_definitions == {}
        assert plan.rollback_procedures == []
        assert plan.estimated_duration == 0
        assert plan.risk_assessment == {}

    def test_migration_plan_with_data(self):
        """Test MigrationPlan initialization with data."""
        plan = MigrationPlan(
            schema_mappings={'users': {'name': 'users'}},
            rls_policies=[{'name': 'user_policy'}],
            estimated_duration=120,
            risk_assessment={'level': 'medium'}
        )

        assert plan.schema_mappings == {'users': {'name': 'users'}}
        assert len(plan.rls_policies) == 1
        assert plan.estimated_duration == 120
        assert plan.risk_assessment['level'] == 'medium'