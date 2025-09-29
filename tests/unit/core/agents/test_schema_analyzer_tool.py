"""
Unit tests for SchemaAnalyzerTool.

This module provides comprehensive unit tests for the schema analyzer tool
used in Supabase migration, including database connection, schema analysis,
and relationship extraction.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy import MetaData, Engine
from sqlalchemy.engine import Inspector

from core.agents.supabase.tools.schema_analyzer import (
    SchemaAnalyzerTool,
    TableInfo
)


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine."""
    mock_engine = Mock(spec=Engine)
    mock_engine.dispose = Mock()
    mock_engine.connect = Mock()
    return mock_engine


@pytest.fixture
def mock_inspector():
    """Create a mock SQLAlchemy inspector."""
    mock_inspector = Mock(spec=Inspector)

    # Mock table names
    mock_inspector.get_table_names.return_value = ['users', 'posts', 'comments']

    # Mock view names
    mock_inspector.get_view_names.return_value = ['user_stats', 'post_analytics']

    # Mock table columns
    mock_inspector.get_columns.side_effect = lambda table_name: {
        'users': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'default': None, 'autoincrement': True},
            {'name': 'email', 'type': 'VARCHAR(255)', 'nullable': False, 'default': None, 'autoincrement': False},
            {'name': 'created_at', 'type': 'TIMESTAMP', 'nullable': True, 'default': 'CURRENT_TIMESTAMP', 'autoincrement': False}
        ],
        'posts': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'default': None, 'autoincrement': True},
            {'name': 'user_id', 'type': 'INTEGER', 'nullable': False, 'default': None, 'autoincrement': False},
            {'name': 'title', 'type': 'VARCHAR(255)', 'nullable': False, 'default': None, 'autoincrement': False},
            {'name': 'content', 'type': 'TEXT', 'nullable': True, 'default': None, 'autoincrement': False}
        ],
        'comments': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False, 'default': None, 'autoincrement': True},
            {'name': 'post_id', 'type': 'INTEGER', 'nullable': False, 'default': None, 'autoincrement': False},
            {'name': 'content', 'type': 'TEXT', 'nullable': False, 'default': None, 'autoincrement': False}
        ],
        'user_stats': [
            {'name': 'user_id', 'type': 'INTEGER'},
            {'name': 'post_count', 'type': 'INTEGER'}
        ],
        'post_analytics': [
            {'name': 'post_id', 'type': 'INTEGER'},
            {'name': 'view_count', 'type': 'INTEGER'}
        ]
    }[table_name]

    # Mock primary keys
    mock_inspector.get_pk_constraint.side_effect = lambda table_name: {
        'users': {'constrained_columns': ['id'], 'name': 'pk_users'},
        'posts': {'constrained_columns': ['id'], 'name': 'pk_posts'},
        'comments': {'constrained_columns': ['id'], 'name': 'pk_comments'}
    }.get(table_name, None)

    # Mock foreign keys
    mock_inspector.get_foreign_keys.side_effect = lambda table_name: {
        'users': [],
        'posts': [{
            'name': 'fk_posts_user_id',
            'constrained_columns': ['user_id'],
            'referred_table': 'users',
            'referred_columns': ['id']
        }],
        'comments': [{
            'name': 'fk_comments_post_id',
            'constrained_columns': ['post_id'],
            'referred_table': 'posts',
            'referred_columns': ['id']
        }]
    }.get(table_name, [])

    # Mock indexes
    mock_inspector.get_indexes.side_effect = lambda table_name: {
        'users': [{'name': 'idx_users_email', 'column_names': ['email'], 'unique': True}],
        'posts': [{'name': 'idx_posts_user_id', 'column_names': ['user_id'], 'unique': False}],
        'comments': []
    }.get(table_name, [])

    # Mock unique constraints
    mock_inspector.get_unique_constraints.side_effect = lambda table_name: {
        'users': [{'name': 'uq_users_email', 'column_names': ['email']}],
        'posts': [],
        'comments': []
    }.get(table_name, [])

    # Mock check constraints
    mock_inspector.get_check_constraints.side_effect = lambda table_name: {
        'users': [{'name': 'ck_users_email_format', 'sqltext': "email LIKE '%@%'"}],
        'posts': [],
        'comments': []
    }.get(table_name, [])

    return mock_inspector


@pytest.fixture
def mock_connection():
    """Create a mock database connection."""
    mock_conn = Mock()

    # Mock query results
    def mock_execute(query):
        mock_result = Mock()

        if "COUNT(*)" in query:
            if "users" in query:
                mock_result.scalar.return_value = 1000
            elif "posts" in query:
                mock_result.scalar.return_value = 5000
            elif "comments" in query:
                mock_result.scalar.return_value = 15000
            else:
                mock_result.scalar.return_value = 0
        elif "pg_total_relation_size" in query:
            if "users" in query:
                mock_result.scalar.return_value = 65536
            elif "posts" in query:
                mock_result.scalar.return_value = 262144
            elif "comments" in query:
                mock_result.scalar.return_value = 524288
            else:
                mock_result.scalar.return_value = 0
        elif "information_schema.sequences" in query:
            mock_result.__iter__ = lambda: iter([
                ('user_id_seq', 'bigint', 1, 1, 9223372036854775807, 1),
                ('post_id_seq', 'bigint', 1, 1, 9223372036854775807, 1)
            ])
        elif "pg_type" in query and "pg_enum" in query:
            mock_result.__iter__ = lambda: iter([
                ('user_status', ['active', 'inactive', 'suspended']),
                ('post_status', ['draft', 'published', 'archived'])
            ])
        elif "information_schema.routines" in query:
            mock_result.__iter__ = lambda: iter([
                ('calculate_user_score', 'FUNCTION', 'integer'),
                ('update_post_stats', 'PROCEDURE', 'void')
            ])
        elif "information_schema.triggers" in query:
            mock_result.__iter__ = lambda: iter([
                ('update_user_timestamp', 'users', 'UPDATE', 'BEFORE'),
                ('log_post_changes', 'posts', 'INSERT', 'AFTER')
            ])
        elif "pg_views" in query:
            if "user_stats" in query:
                mock_result.fetchone.return_value = ("SELECT user_id, COUNT(*) as post_count FROM posts GROUP BY user_id",)
            elif "post_analytics" in query:
                mock_result.fetchone.return_value = ("SELECT post_id, COUNT(*) as view_count FROM post_views GROUP BY post_id",)
            else:
                mock_result.fetchone.return_value = None
        else:
            mock_result.scalar.return_value = 0
            mock_result.__iter__ = lambda: iter([])
            mock_result.fetchone.return_value = None

        return mock_result

    mock_conn.execute = mock_execute
    return mock_conn


@pytest.fixture
def sample_table_info():
    """Provide sample table information for testing."""
    return TableInfo(
        name='users',
        columns=[
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
            {'name': 'email', 'type': 'VARCHAR(255)', 'nullable': False},
            {'name': 'created_at', 'type': 'TIMESTAMP', 'nullable': True}
        ],
        constraints=[],
        indexes=[{'name': 'idx_users_email', 'column_names': ['email']}],
        row_count=1000,
        size_bytes=65536
    )


class TestSchemaAnalyzerTool:
    """Test cases for SchemaAnalyzerTool."""

    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = SchemaAnalyzerTool()

        assert isinstance(tool.metadata, MetaData)
        assert tool.engine is None

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_engine, mock_inspector, mock_connection):
        """Test successful schema analysis."""
        tool = SchemaAnalyzerTool()

        with patch('sqlalchemy.create_engine', return_value=mock_engine), \
             patch('sqlalchemy.inspect', return_value=mock_inspector), \
             patch.object(mock_engine, 'connect', return_value=mock_connection):

            # Mock async methods
            with patch.object(tool, '_get_row_count', new_callable=AsyncMock) as mock_row_count, \
                 patch.object(tool, '_get_table_size', new_callable=AsyncMock) as mock_table_size, \
                 patch.object(tool, '_get_sequences', new_callable=AsyncMock) as mock_sequences, \
                 patch.object(tool, '_get_enums', new_callable=AsyncMock) as mock_enums, \
                 patch.object(tool, '_get_functions', new_callable=AsyncMock) as mock_functions, \
                 patch.object(tool, '_get_triggers', new_callable=AsyncMock) as mock_triggers, \
                 patch.object(tool, '_get_view_definition', new_callable=AsyncMock) as mock_view_def:

                mock_row_count.side_effect = lambda table: {'users': 1000, 'posts': 5000, 'comments': 15000}[table]
                mock_table_size.side_effect = lambda table: {'users': 65536, 'posts': 262144, 'comments': 524288}[table]
                mock_sequences.return_value = [{'name': 'user_id_seq', 'data_type': 'bigint'}]
                mock_enums.return_value = [{'name': 'user_status', 'values': ['active', 'inactive']}]
                mock_functions.return_value = [{'name': 'calculate_score', 'type': 'FUNCTION'}]
                mock_triggers.return_value = [{'name': 'update_timestamp', 'table': 'users'}]
                mock_view_def.return_value = "SELECT * FROM users"

                result = await tool.analyze(
                    "postgresql://user:pass@localhost/test_db",
                    "test_db"
                )

                assert result['database'] == 'test_db'
                assert len(result['tables']) == 3
                assert len(result['views']) == 2
                assert len(result['sequences']) == 1
                assert len(result['enums']) == 1
                assert len(result['functions']) == 1
                assert len(result['triggers']) == 1

                # Check table details
                users_table = next(t for t in result['tables'] if t['name'] == 'users')
                assert len(users_table['columns']) == 3
                assert users_table['row_count'] == 1000
                assert users_table['size_bytes'] == 65536
                assert len(users_table['foreign_keys']) == 0

                posts_table = next(t for t in result['tables'] if t['name'] == 'posts')
                assert len(posts_table['foreign_keys']) == 1
                assert posts_table['foreign_keys'][0]['referred_table'] == 'users'

    @pytest.mark.asyncio
    async def test_analyze_failure(self, mock_engine):
        """Test schema analysis failure handling."""
        tool = SchemaAnalyzerTool()

        with patch('sqlalchemy.create_engine', return_value=mock_engine), \
             patch('sqlalchemy.inspect', side_effect=Exception("Connection failed")):

            with pytest.raises(Exception, match="Connection failed"):
                await tool.analyze(
                    "postgresql://invalid:conn@localhost/test_db",
                    "test_db"
                )

            # Ensure engine disposal is called
            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_relationships(self):
        """Test relationship extraction from schema."""
        tool = SchemaAnalyzerTool()

        schema = {
            'tables': [
                {
                    'name': 'users',
                    'primary_key': {'constrained_columns': ['id']},
                    'foreign_keys': [],
                    'unique_constraints': [{'name': 'uq_email', 'column_names': ['email']}]
                },
                {
                    'name': 'posts',
                    'primary_key': {'constrained_columns': ['id']},
                    'foreign_keys': [{
                        'name': 'fk_posts_user_id',
                        'constrained_columns': ['user_id'],
                        'referred_table': 'users',
                        'referred_columns': ['id']
                    }],
                    'unique_constraints': []
                }
            ]
        }

        relationships = await tool.extract_relationships(schema)

        assert len(relationships['foreign_keys']) == 1
        assert len(relationships['primary_keys']) == 2
        assert len(relationships['unique_constraints']) == 1

        # Check foreign key details
        fk = relationships['foreign_keys'][0]
        assert fk['source_table'] == 'posts'
        assert fk['target_table'] == 'users'
        assert fk['name'] == 'fk_posts_user_id'

        # Check dependencies
        assert relationships['dependencies']['users'] == []
        assert relationships['dependencies']['posts'] == ['users']

    @pytest.mark.asyncio
    async def test_analyze_table(self, mock_inspector, mock_connection, mock_engine):
        """Test individual table analysis."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection), \
             patch.object(tool, '_get_row_count', new_callable=AsyncMock) as mock_row_count, \
             patch.object(tool, '_get_table_size', new_callable=AsyncMock) as mock_table_size:

            mock_row_count.return_value = 1000
            mock_table_size.return_value = 65536

            table_info = await tool._analyze_table(mock_inspector, 'users')

            assert table_info['name'] == 'users'
            assert len(table_info['columns']) == 3
            assert table_info['row_count'] == 1000
            assert table_info['size_bytes'] == 65536
            assert table_info['primary_key']['constrained_columns'] == ['id']
            assert len(table_info['foreign_keys']) == 0
            assert len(table_info['indexes']) == 1
            assert len(table_info['unique_constraints']) == 1

    @pytest.mark.asyncio
    async def test_analyze_view(self, mock_inspector, mock_connection, mock_engine):
        """Test view analysis."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(tool, '_get_view_definition', new_callable=AsyncMock) as mock_view_def:
            mock_view_def.return_value = "SELECT user_id, COUNT(*) FROM posts GROUP BY user_id"

            view_info = await tool._analyze_view(mock_inspector, 'user_stats')

            assert view_info['name'] == 'user_stats'
            assert len(view_info['columns']) == 2
            assert 'COUNT(*)' in view_info['definition']

    @pytest.mark.asyncio
    async def test_get_sequences(self, mock_connection, mock_engine):
        """Test sequence retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            sequences = await tool._get_sequences()

            assert len(sequences) == 2
            assert sequences[0]['name'] == 'user_id_seq'
            assert sequences[0]['data_type'] == 'bigint'
            assert sequences[1]['name'] == 'post_id_seq'

    @pytest.mark.asyncio
    async def test_get_enums(self, mock_connection, mock_engine):
        """Test enum type retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            enums = await tool._get_enums()

            assert len(enums) == 2
            assert enums[0]['name'] == 'user_status'
            assert 'active' in enums[0]['values']
            assert enums[1]['name'] == 'post_status'

    @pytest.mark.asyncio
    async def test_get_functions(self, mock_connection, mock_engine):
        """Test function retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            functions = await tool._get_functions()

            assert len(functions) == 2
            assert functions[0]['name'] == 'calculate_user_score'
            assert functions[0]['type'] == 'FUNCTION'
            assert functions[1]['name'] == 'update_post_stats'

    @pytest.mark.asyncio
    async def test_get_triggers(self, mock_connection, mock_engine):
        """Test trigger retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            triggers = await tool._get_triggers()

            assert len(triggers) == 2
            assert triggers[0]['name'] == 'update_user_timestamp'
            assert triggers[0]['table'] == 'users'
            assert triggers[1]['name'] == 'log_post_changes'

    @pytest.mark.asyncio
    async def test_get_row_count(self, mock_connection, mock_engine):
        """Test row count retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            count = await tool._get_row_count('users')
            assert count == 1000

            count = await tool._get_row_count('posts')
            assert count == 5000

    @pytest.mark.asyncio
    async def test_get_table_size(self, mock_connection, mock_engine):
        """Test table size retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            size = await tool._get_table_size('users')
            assert size == 65536

            size = await tool._get_table_size('posts')
            assert size == 262144

    @pytest.mark.asyncio
    async def test_get_view_definition(self, mock_connection, mock_engine):
        """Test view definition retrieval."""
        tool = SchemaAnalyzerTool()
        tool.engine = mock_engine

        with patch.object(mock_engine, 'connect', return_value=mock_connection):
            definition = await tool._get_view_definition('user_stats')
            assert 'SELECT user_id, COUNT(*)' in definition

            definition = await tool._get_view_definition('nonexistent_view')
            assert definition is None

    def test_generate_migration_report_simple(self):
        """Test migration report generation for simple schema."""
        tool = SchemaAnalyzerTool()

        simple_schema = {
            'tables': [{'name': 'users'}, {'name': 'posts'}],
            'views': [],
            'functions': [],
            'triggers': [],
            'enums': []
        }

        report = tool.generate_migration_report(simple_schema)

        assert report['summary']['total_tables'] == 2
        assert report['summary']['total_views'] == 0
        assert report['summary']['total_functions'] == 0
        assert report['summary']['total_triggers'] == 0
        assert report['summary']['total_enums'] == 0
        assert len(report['complexity_factors']) == 0
        assert report['estimated_effort'] == 1.0  # 2 * 0.5

    def test_generate_migration_report_complex(self):
        """Test migration report generation for complex schema."""
        tool = SchemaAnalyzerTool()

        complex_schema = {
            'tables': [{'name': f'table_{i}'} for i in range(60)],
            'views': [{'name': f'view_{i}'} for i in range(5)],
            'functions': [{'name': f'func_{i}'} for i in range(15)],
            'triggers': [{'name': f'trigger_{i}'} for i in range(3)],
            'enums': [{'name': 'status_enum'}]
        }

        report = tool.generate_migration_report(complex_schema)

        assert report['summary']['total_tables'] == 60
        assert report['summary']['total_functions'] == 15
        assert report['summary']['total_triggers'] == 3

        # Check complexity factors
        factor_names = [f['factor'] for f in report['complexity_factors']]
        assert 'high_table_count' in factor_names
        assert 'triggers_present' in factor_names
        assert 'many_functions' in factor_names

        # Check recommendations
        assert len(report['recommendations']) >= 2
        assert any('phased migration' in rec for rec in report['recommendations'])
        assert any('trigger conversion' in rec for rec in report['recommendations'])

        # Check effort estimation
        expected_effort = 60 * 0.5 + 5 * 0.3 + 15 * 2 + 3 * 1  # 30 + 1.5 + 30 + 3 = 64.5
        assert report['estimated_effort'] == expected_effort

    def test_generate_migration_report_with_triggers(self):
        """Test migration report generation with triggers."""
        tool = SchemaAnalyzerTool()

        schema_with_triggers = {
            'tables': [{'name': 'users'}],
            'views': [],
            'functions': [],
            'triggers': [{'name': 'update_timestamp'}],
            'enums': []
        }

        report = tool.generate_migration_report(schema_with_triggers)

        factor_names = [f['factor'] for f in report['complexity_factors']]
        assert 'triggers_present' in factor_names

        recommendations = ' '.join(report['recommendations'])
        assert 'trigger conversion' in recommendations


class TestTableInfo:
    """Test cases for TableInfo dataclass."""

    def test_table_info_creation(self, sample_table_info):
        """Test TableInfo creation."""
        assert sample_table_info.name == 'users'
        assert len(sample_table_info.columns) == 3
        assert sample_table_info.row_count == 1000
        assert sample_table_info.size_bytes == 65536

    def test_table_info_with_all_fields(self):
        """Test TableInfo with all fields populated."""
        table_info = TableInfo(
            name='complex_table',
            columns=[
                {'name': 'id', 'type': 'UUID', 'nullable': False},
                {'name': 'data', 'type': 'JSONB', 'nullable': True}
            ],
            constraints=[
                {'name': 'ck_data_format', 'type': 'CHECK'}
            ],
            indexes=[
                {'name': 'idx_data_gin', 'type': 'GIN', 'columns': ['data']}
            ],
            row_count=50000,
            size_bytes=10485760
        )

        assert table_info.name == 'complex_table'
        assert len(table_info.columns) == 2
        assert len(table_info.constraints) == 1
        assert len(table_info.indexes) == 1
        assert table_info.row_count == 50000
        assert table_info.size_bytes == 10485760