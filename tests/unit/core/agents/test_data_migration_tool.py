"""
Unit tests for DataMigrationTool.

This module provides comprehensive unit tests for the data migration tool
used in Supabase migration, including batch processing, validation, and rollback.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from core.agents.supabase.tools.data_migration import (
    DataMigrationTool,
    MigrationBatch,
    MigrationResult,
    MigrationStatus
)


@pytest.fixture
def migration_tool():
    """Create a data migration tool instance for testing."""
    return DataMigrationTool(
        batch_size=100,
        max_concurrent_batches=3,
        retry_attempts=2
    )


@pytest.fixture
def sample_migration_batch():
    """Create a sample migration batch for testing."""
    return MigrationBatch(
        table_name='test_table',
        batch_id=0,
        offset=0,
        limit=100,
        row_count=100,
        status=MigrationStatus.PENDING
    )


@pytest.fixture
def mock_asyncpg_connection():
    """Create a mock asyncpg connection."""
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.executemany = AsyncMock()
    mock_conn.close = AsyncMock()
    return mock_conn


@pytest.fixture
def sample_table_data():
    """Provide sample table data for testing."""
    return [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'},
        {'id': 3, 'name': 'Bob Wilson', 'email': 'bob@example.com'}
    ]


class TestDataMigrationTool:
    """Test cases for DataMigrationTool."""

    def test_tool_initialization(self):
        """Test tool initialization with custom parameters."""
        tool = DataMigrationTool(
            batch_size=500,
            max_concurrent_batches=10,
            retry_attempts=5
        )

        assert tool.batch_size == 500
        assert tool.max_concurrent_batches == 10
        assert tool.retry_attempts == 5
        assert tool.migration_state == {}
        assert tool.progress_callback is None

    def test_tool_initialization_defaults(self):
        """Test tool initialization with default parameters."""
        tool = DataMigrationTool()

        assert tool.batch_size == 1000
        assert tool.max_concurrent_batches == 5
        assert tool.retry_attempts == 3

    @pytest.mark.asyncio
    async def test_migrate_table_dry_run(self, migration_tool, mock_asyncpg_connection):
        """Test table migration in dry run mode."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock row count
            mock_asyncpg_connection.fetchval.return_value = 1000

            # Mock schema validation
            with patch.object(migration_tool, '_validate_schema_compatibility', new_callable=AsyncMock) as mock_validate:
                mock_validate.return_value = True

                result = await migration_tool.migrate_table(
                    'postgresql://source',
                    'postgresql://target',
                    'test_table',
                    dry_run=True
                )

                assert isinstance(result, MigrationResult)
                assert result.table_name == 'test_table'
                assert result.total_rows == 1000
                assert result.migrated_rows == 0
                assert result.status == MigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_migrate_table_actual(self, migration_tool, mock_asyncpg_connection, sample_table_data):
        """Test actual table migration."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock row count
            mock_asyncpg_connection.fetchval.return_value = 300

            # Mock data extraction
            with patch.object(migration_tool, '_extract_batch_data', new_callable=AsyncMock) as mock_extract, \
                 patch.object(migration_tool, '_load_batch_data', new_callable=AsyncMock) as mock_load:

                mock_extract.return_value = sample_table_data
                mock_load.return_value = True

                result = await migration_tool.migrate_table(
                    'postgresql://source',
                    'postgresql://target',
                    'test_table',
                    dry_run=False
                )

                assert isinstance(result, MigrationResult)
                assert result.table_name == 'test_table'
                assert result.total_rows == 300
                assert result.migrated_rows == 300
                assert result.failed_rows == 0
                assert result.status == MigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_migrate_table_with_progress_callback(self, migration_tool, mock_asyncpg_connection):
        """Test table migration with progress callback."""
        progress_updates = []

        async def progress_callback(update):
            progress_updates.append(update)

        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.fetchval.return_value = 200

            with patch.object(migration_tool, '_extract_batch_data', new_callable=AsyncMock) as mock_extract, \
                 patch.object(migration_tool, '_load_batch_data', new_callable=AsyncMock) as mock_load:

                mock_extract.return_value = [{'id': 1, 'name': 'test'}]
                mock_load.return_value = True

                await migration_tool.migrate_table(
                    'postgresql://source',
                    'postgresql://target',
                    'test_table',
                    dry_run=False,
                    progress_callback=progress_callback
                )

                assert len(progress_updates) > 0
                assert all('table' in update for update in progress_updates)
                assert all('status' in update for update in progress_updates)

    @pytest.mark.asyncio
    async def test_migrate_table_failure(self, migration_tool, mock_asyncpg_connection):
        """Test table migration failure handling."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock connection failure
            mock_asyncpg_connection.fetchval.side_effect = Exception("Connection failed")

            result = await migration_tool.migrate_table(
                'postgresql://invalid',
                'postgresql://target',
                'test_table',
                dry_run=False
            )

            assert result.status == MigrationStatus.FAILED
            assert result.migrated_rows == 0

    @pytest.mark.asyncio
    async def test_migrate_database(self, migration_tool, mock_asyncpg_connection):
        """Test database migration with multiple tables."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock table list
            mock_asyncpg_connection.fetch.return_value = [
                {'table_name': 'users'},
                {'table_name': 'posts'},
                {'table_name': 'comments'}
            ]

            # Mock individual table migrations
            with patch.object(migration_tool, 'migrate_table', new_callable=AsyncMock) as mock_migrate:
                mock_migrate.return_value = MigrationResult(
                    table_name='test',
                    total_rows=100,
                    migrated_rows=100,
                    failed_rows=0,
                    batches_completed=1,
                    duration_seconds=1.0,
                    status=MigrationStatus.COMPLETED
                )

                results = await migration_tool.migrate_database(
                    'postgresql://source',
                    'postgresql://target',
                    dry_run=True
                )

                assert len(results) == 3
                assert 'users' in results
                assert 'posts' in results
                assert 'comments' in results
                assert all(result.status == MigrationStatus.COMPLETED for result in results.values())

    @pytest.mark.asyncio
    async def test_migrate_database_with_exclusions(self, migration_tool, mock_asyncpg_connection):
        """Test database migration with table exclusions."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.fetch.return_value = [
                {'table_name': 'users'},
                {'table_name': 'temp_table'},
                {'table_name': 'posts'}
            ]

            with patch.object(migration_tool, 'migrate_table', new_callable=AsyncMock) as mock_migrate:
                mock_migrate.return_value = MigrationResult(
                    table_name='test',
                    total_rows=100,
                    migrated_rows=100,
                    failed_rows=0,
                    batches_completed=1,
                    duration_seconds=1.0,
                    status=MigrationStatus.COMPLETED
                )

                results = await migration_tool.migrate_database(
                    'postgresql://source',
                    'postgresql://target',
                    exclude_tables=['temp_table'],
                    dry_run=True
                )

                assert len(results) == 2
                assert 'users' in results
                assert 'posts' in results
                assert 'temp_table' not in results

    @pytest.mark.asyncio
    async def test_migrate_database_specific_tables(self, migration_tool):
        """Test database migration with specific table list."""
        with patch.object(migration_tool, 'migrate_table', new_callable=AsyncMock) as mock_migrate:
            mock_migrate.return_value = MigrationResult(
                table_name='test',
                total_rows=100,
                migrated_rows=100,
                failed_rows=0,
                batches_completed=1,
                duration_seconds=1.0,
                status=MigrationStatus.COMPLETED
            )

            results = await migration_tool.migrate_database(
                'postgresql://source',
                'postgresql://target',
                table_list=['users', 'posts'],
                dry_run=True
            )

            assert len(results) == 2
            assert mock_migrate.call_count == 2

    @pytest.mark.asyncio
    async def test_incremental_migration(self, migration_tool, mock_asyncpg_connection):
        """Test incremental migration based on timestamp."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock timestamp and row count
            mock_asyncpg_connection.fetchval.side_effect = [
                '2023-01-01T00:00:00',  # Latest timestamp
                50  # Incremental row count
            ]

            with patch.object(migration_tool, '_execute_incremental_migration', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = MigrationResult(
                    table_name='test_table',
                    total_rows=50,
                    migrated_rows=50,
                    failed_rows=0,
                    batches_completed=1,
                    duration_seconds=1.0,
                    status=MigrationStatus.COMPLETED
                )

                result = await migration_tool.incremental_migration(
                    'postgresql://source',
                    'postgresql://target',
                    'test_table',
                    'updated_at'
                )

                assert result.total_rows == 50
                assert result.status == MigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_incremental_migration_no_changes(self, migration_tool, mock_asyncpg_connection):
        """Test incremental migration when no new data exists."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock no incremental rows
            mock_asyncpg_connection.fetchval.side_effect = [
                '2023-01-01T00:00:00',  # Latest timestamp
                0  # No incremental rows
            ]

            result = await migration_tool.incremental_migration(
                'postgresql://source',
                'postgresql://target',
                'test_table',
                'updated_at'
            )

            assert result.total_rows == 0
            assert result.migrated_rows == 0
            assert result.status == MigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_rollback_migration(self, migration_tool, mock_asyncpg_connection):
        """Test migration rollback."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            with patch.object(migration_tool, '_clear_table', new_callable=AsyncMock) as mock_clear, \
                 patch.object(migration_tool, '_restore_from_backup', new_callable=AsyncMock) as mock_restore:

                success = await migration_tool.rollback_migration(
                    'postgresql://target',
                    'test_table',
                    '/path/to/backup.json'
                )

                assert success is True
                mock_clear.assert_called_once()
                mock_restore.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_migration_failure(self, migration_tool, mock_asyncpg_connection):
        """Test migration rollback failure handling."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            with patch.object(migration_tool, '_clear_table', new_callable=AsyncMock) as mock_clear:
                mock_clear.side_effect = Exception("Rollback failed")

                success = await migration_tool.rollback_migration(
                    'postgresql://target',
                    'test_table'
                )

                assert success is False

    @pytest.mark.asyncio
    async def test_validate_migration_basic(self, migration_tool, mock_asyncpg_connection):
        """Test basic migration validation."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock row counts
            mock_asyncpg_connection.fetchval.side_effect = [1000, 1000]  # Source and target counts

            result = await migration_tool.validate_migration(
                'postgresql://source',
                'postgresql://target',
                'test_table',
                'basic'
            )

            assert result['is_valid'] is True
            assert result['metrics']['source_rows'] == 1000
            assert result['metrics']['target_rows'] == 1000
            assert len(result['issues']) == 0

    @pytest.mark.asyncio
    async def test_validate_migration_count_mismatch(self, migration_tool, mock_asyncpg_connection):
        """Test migration validation with row count mismatch."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock different row counts
            mock_asyncpg_connection.fetchval.side_effect = [1000, 950]  # Source and target counts

            result = await migration_tool.validate_migration(
                'postgresql://source',
                'postgresql://target',
                'test_table',
                'basic'
            )

            assert result['is_valid'] is False
            assert result['metrics']['source_rows'] == 1000
            assert result['metrics']['target_rows'] == 950
            assert len(result['issues']) == 1
            assert 'Row count mismatch' in result['issues'][0]

    @pytest.mark.asyncio
    async def test_validate_migration_full_mode(self, migration_tool, mock_asyncpg_connection):
        """Test migration validation in full mode."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.fetchval.side_effect = [1000, 1000]

            with patch.object(migration_tool, '_validate_sample_data', new_callable=AsyncMock) as mock_sample:
                mock_sample.return_value = {
                    'sample_size': 100,
                    'mismatches': 0,
                    'accuracy': 1.0
                }

                result = await migration_tool.validate_migration(
                    'postgresql://source',
                    'postgresql://target',
                    'test_table',
                    'full'
                )

                assert result['is_valid'] is True
                assert 'sample_size' in result['metrics']
                assert result['metrics']['accuracy'] == 1.0

    def test_create_batches(self, migration_tool):
        """Test batch creation for migration."""
        batches = migration_tool._create_batches('test_table', 250)

        assert len(batches) == 3  # 250 rows / 100 batch_size = 3 batches

        # Check first batch
        assert batches[0].table_name == 'test_table'
        assert batches[0].batch_id == 0
        assert batches[0].offset == 0
        assert batches[0].limit == 100
        assert batches[0].row_count == 100
        assert batches[0].status == MigrationStatus.PENDING

        # Check last batch
        assert batches[2].offset == 200
        assert batches[2].limit == 50  # Remaining rows
        assert batches[2].row_count == 50

    @pytest.mark.asyncio
    async def test_get_row_count(self, migration_tool, mock_asyncpg_connection):
        """Test row count retrieval."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.fetchval.return_value = 1500

            count = await migration_tool._get_row_count(
                'postgresql://test',
                'test_table'
            )

            assert count == 1500

    @pytest.mark.asyncio
    async def test_get_row_count_with_where_clause(self, migration_tool, mock_asyncpg_connection):
        """Test row count retrieval with where clause."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.fetchval.return_value = 750

            count = await migration_tool._get_row_count(
                'postgresql://test',
                'test_table',
                'created_at > \'2023-01-01\''
            )

            assert count == 750

    @pytest.mark.asyncio
    async def test_extract_batch_data(self, migration_tool, mock_asyncpg_connection, sample_table_data):
        """Test batch data extraction."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock fetch result
            mock_rows = [Mock(spec=dict) for _ in sample_table_data]
            for i, mock_row in enumerate(mock_rows):
                mock_row.__getitem__ = lambda self, key, data=sample_table_data[i]: data[key]
                mock_row.keys = lambda data=sample_table_data[i]: data.keys()

            mock_asyncpg_connection.fetch.return_value = mock_rows

            batch = MigrationBatch(
                table_name='test_table',
                batch_id=0,
                offset=0,
                limit=3,
                row_count=3,
                status=MigrationStatus.PENDING
            )

            # Mock dict conversion
            with patch('builtins.dict', side_effect=sample_table_data):
                data = await migration_tool._extract_batch_data(
                    'postgresql://source',
                    batch
                )

                assert len(data) == 3
                assert data == sample_table_data

    @pytest.mark.asyncio
    async def test_load_batch_data(self, migration_tool, mock_asyncpg_connection, sample_table_data):
        """Test batch data loading."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            success = await migration_tool._load_batch_data(
                'postgresql://target',
                'test_table',
                sample_table_data
            )

            assert success is True
            mock_asyncpg_connection.executemany.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_batch_data_empty(self, migration_tool, mock_asyncpg_connection):
        """Test batch data loading with empty data."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            success = await migration_tool._load_batch_data(
                'postgresql://target',
                'test_table',
                []
            )

            assert success is True
            mock_asyncpg_connection.executemany.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_batch_data_failure(self, migration_tool, mock_asyncpg_connection, sample_table_data):
        """Test batch data loading failure."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.executemany.side_effect = Exception("Insert failed")

            success = await migration_tool._load_batch_data(
                'postgresql://target',
                'test_table',
                sample_table_data
            )

            assert success is False

    @pytest.mark.asyncio
    async def test_validate_schema_compatibility_success(self, migration_tool, mock_asyncpg_connection):
        """Test schema compatibility validation success."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock schema data
            schema_data = [
                {'name': 'id', 'type': 'integer', 'is_nullable': 'NO', 'default': None},
                {'name': 'name', 'type': 'text', 'is_nullable': 'YES', 'default': None}
            ]
            mock_asyncpg_connection.fetch.return_value = [Mock(spec=dict) for _ in schema_data]

            # Mock dict conversion for schema data
            with patch('builtins.dict', side_effect=schema_data * 2):  # Source and target schemas
                result = await migration_tool._validate_schema_compatibility(
                    'postgresql://source',
                    'postgresql://target',
                    'test_table'
                )

                assert result is True

    @pytest.mark.asyncio
    async def test_validate_schema_compatibility_missing_table(self, migration_tool, mock_asyncpg_connection):
        """Test schema compatibility validation with missing target table."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock source schema exists, target doesn't
            source_schema = [{'name': 'id', 'type': 'integer'}]

            def mock_fetch_side_effect(*args, **kwargs):
                if 'source' in str(args):
                    return [Mock(spec=dict)]
                else:
                    return []  # Target table not found

            mock_asyncpg_connection.fetch.side_effect = mock_fetch_side_effect

            with patch('builtins.dict', side_effect=[source_schema[0]]):
                with patch.object(migration_tool, '_get_table_schema', new_callable=AsyncMock) as mock_schema:
                    mock_schema.side_effect = [source_schema, []]  # Source has schema, target empty

                    result = await migration_tool._validate_schema_compatibility(
                        'postgresql://source',
                        'postgresql://target',
                        'test_table'
                    )

                    assert result is False

    def test_are_types_compatible(self, migration_tool):
        """Test data type compatibility checking."""
        # Direct matches
        assert migration_tool._are_types_compatible('integer', 'integer') is True
        assert migration_tool._are_types_compatible('text', 'text') is True

        # Compatible types
        assert migration_tool._are_types_compatible('integer', 'int4') is True
        assert migration_tool._are_types_compatible('text', 'varchar') is True
        assert migration_tool._are_types_compatible('timestamp', 'timestamptz') is True

        # Incompatible types
        assert migration_tool._are_types_compatible('integer', 'text') is False
        assert migration_tool._are_types_compatible('boolean', 'numeric') is False

    @pytest.mark.asyncio
    async def test_get_all_tables(self, migration_tool, mock_asyncpg_connection):
        """Test getting all tables from database."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            mock_asyncpg_connection.fetch.return_value = [
                {'table_name': 'users'},
                {'table_name': 'posts'},
                {'table_name': 'comments'}
            ]

            tables = await migration_tool._get_all_tables('postgresql://test')

            assert tables == ['users', 'posts', 'comments']

    @pytest.mark.asyncio
    async def test_initialize_migration_state(self, migration_tool):
        """Test migration state initialization."""
        await migration_tool._initialize_migration_state('test_table')

        assert 'test_table' in migration_tool.migration_state
        state = migration_tool.migration_state['test_table']
        assert state['status'] == MigrationStatus.PENDING
        assert state['batches'] == []
        assert 'start_time' in state
        assert state['errors'] == []

    @pytest.mark.asyncio
    async def test_process_single_batch_success(self, migration_tool, sample_migration_batch, sample_table_data):
        """Test single batch processing success."""
        with patch.object(migration_tool, '_extract_batch_data', new_callable=AsyncMock) as mock_extract, \
             patch.object(migration_tool, '_load_batch_data', new_callable=AsyncMock) as mock_load:

            mock_extract.return_value = sample_table_data
            mock_load.return_value = True

            success = await migration_tool._process_single_batch(
                'postgresql://source',
                'postgresql://target',
                sample_migration_batch
            )

            assert success is True
            assert sample_migration_batch.status == MigrationStatus.COMPLETED
            assert sample_migration_batch.started_at is not None
            assert sample_migration_batch.completed_at is not None

    @pytest.mark.asyncio
    async def test_process_single_batch_empty_data(self, migration_tool, sample_migration_batch):
        """Test single batch processing with empty data."""
        with patch.object(migration_tool, '_extract_batch_data', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = []

            success = await migration_tool._process_single_batch(
                'postgresql://source',
                'postgresql://target',
                sample_migration_batch
            )

            assert success is True
            assert sample_migration_batch.status == MigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_single_batch_failure(self, migration_tool, sample_migration_batch):
        """Test single batch processing failure."""
        with patch.object(migration_tool, '_extract_batch_data', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = Exception("Extract failed")

            success = await migration_tool._process_single_batch(
                'postgresql://source',
                'postgresql://target',
                sample_migration_batch
            )

            assert success is False
            assert sample_migration_batch.status == MigrationStatus.FAILED
            assert sample_migration_batch.error_message == "Extract failed"

    @pytest.mark.asyncio
    async def test_clear_table(self, migration_tool, mock_asyncpg_connection):
        """Test table clearing."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            await migration_tool._clear_table('postgresql://test', 'test_table')

            mock_asyncpg_connection.execute.assert_called_once_with(
                'TRUNCATE TABLE test_table CASCADE'
            )

    @pytest.mark.asyncio
    async def test_validate_sample_data(self, migration_tool, mock_asyncpg_connection):
        """Test sample data validation."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock primary key query
            mock_asyncpg_connection.fetchrow.side_effect = [
                {'column_name': 'id'},  # Primary key result
                {'id': 1, 'name': 'test'},  # Source row
                {'id': 1, 'name': 'test'},  # Target row (matching)
                {'id': 2, 'name': 'test2'},  # Source row
                {'id': 2, 'name': 'test2'},  # Target row (matching)
            ]

            # Mock sample IDs
            mock_asyncpg_connection.fetch.return_value = [
                {'id': 1},
                {'id': 2}
            ]

            result = await migration_tool._validate_sample_data(
                'postgresql://source',
                'postgresql://target',
                'test_table',
                2
            )

            assert result['sample_size'] == 2
            assert result['mismatches'] == 0
            assert result['accuracy'] == 1.0

    @pytest.mark.asyncio
    async def test_validate_checksums(self, migration_tool, mock_asyncpg_connection):
        """Test checksum validation."""
        with patch('asyncpg.connect', return_value=mock_asyncpg_connection):
            # Mock checksum results
            checksum_data = {'row_count': 1000, 'id_sum': 500500}
            mock_asyncpg_connection.fetchrow.return_value = checksum_data

            result = await migration_tool._validate_checksums(
                'postgresql://source',
                'postgresql://target',
                'test_table'
            )

            assert result['source_checksum'] == checksum_data
            assert result['target_checksum'] == checksum_data
            assert result['checksums_match'] is True


class TestMigrationBatch:
    """Test cases for MigrationBatch dataclass."""

    def test_migration_batch_creation(self):
        """Test MigrationBatch creation."""
        batch = MigrationBatch(
            table_name='test_table',
            batch_id=5,
            offset=500,
            limit=100,
            row_count=100,
            status=MigrationStatus.PENDING
        )

        assert batch.table_name == 'test_table'
        assert batch.batch_id == 5
        assert batch.offset == 500
        assert batch.limit == 100
        assert batch.row_count == 100
        assert batch.status == MigrationStatus.PENDING
        assert batch.started_at is None
        assert batch.completed_at is None
        assert batch.error_message is None

    def test_migration_batch_timing(self):
        """Test MigrationBatch timing tracking."""
        batch = MigrationBatch(
            table_name='test_table',
            batch_id=0,
            offset=0,
            limit=100,
            row_count=100,
            status=MigrationStatus.IN_PROGRESS,
            started_at=time.time(),
            completed_at=time.time() + 1.5
        )

        assert batch.started_at is not None
        assert batch.completed_at is not None
        assert batch.completed_at > batch.started_at


class TestMigrationResult:
    """Test cases for MigrationResult dataclass."""

    def test_migration_result_creation(self):
        """Test MigrationResult creation."""
        result = MigrationResult(
            table_name='test_table',
            total_rows=1000,
            migrated_rows=950,
            failed_rows=50,
            batches_completed=9,
            duration_seconds=45.7,
            status=MigrationStatus.COMPLETED
        )

        assert result.table_name == 'test_table'
        assert result.total_rows == 1000
        assert result.migrated_rows == 950
        assert result.failed_rows == 50
        assert result.batches_completed == 9
        assert result.duration_seconds == 45.7
        assert result.status == MigrationStatus.COMPLETED
        assert result.validation_results is None

    def test_migration_result_with_validation(self):
        """Test MigrationResult with validation results."""
        validation_data = {
            'is_valid': True,
            'issues': [],
            'metrics': {'accuracy': 0.99}
        }

        result = MigrationResult(
            table_name='test_table',
            total_rows=100,
            migrated_rows=100,
            failed_rows=0,
            batches_completed=1,
            duration_seconds=5.0,
            status=MigrationStatus.COMPLETED,
            validation_results=validation_data
        )

        assert result.validation_results == validation_data
        assert result.validation_results['is_valid'] is True


class TestMigrationStatus:
    """Test cases for MigrationStatus enum."""

    def test_migration_status_values(self):
        """Test MigrationStatus enum values."""
        assert MigrationStatus.PENDING.value == "pending"
        assert MigrationStatus.IN_PROGRESS.value == "in_progress"
        assert MigrationStatus.COMPLETED.value == "completed"
        assert MigrationStatus.FAILED.value == "failed"
        assert MigrationStatus.ROLLED_BACK.value == "rolled_back"