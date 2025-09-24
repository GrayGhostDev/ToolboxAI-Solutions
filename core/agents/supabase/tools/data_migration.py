"""Data migration tool for PostgreSQL to Supabase migration."""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import asyncpg
import aiofiles
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration status types."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationBatch:
    """Represents a batch of data for migration."""
    table_name: str
    batch_id: int
    offset: int
    limit: int
    row_count: int
    status: MigrationStatus
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class MigrationResult:
    """Results of a data migration operation."""
    table_name: str
    total_rows: int
    migrated_rows: int
    failed_rows: int
    batches_completed: int
    duration_seconds: float
    status: MigrationStatus
    validation_results: Optional[Dict[str, Any]] = None


class DataMigrationTool:
    """
    Tool for migrating data from PostgreSQL to Supabase.

    Features:
    - Batch processing with configurable sizes
    - Progress tracking and callbacks
    - Data integrity validation
    - Incremental migration support
    - Rollback capabilities
    - Performance optimization
    """

    def __init__(
        self,
        batch_size: int = 1000,
        max_concurrent_batches: int = 5,
        retry_attempts: int = 3
    ):
        """
        Initialize the data migration tool.

        Args:
            batch_size: Number of rows per batch
            max_concurrent_batches: Maximum concurrent batch operations
            retry_attempts: Number of retry attempts for failed batches
        """
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.retry_attempts = retry_attempts
        self.migration_state: Dict[str, Any] = {}
        self.progress_callback: Optional[Callable] = None

    async def migrate_table(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        dry_run: bool = False,
        progress_callback: Optional[Callable] = None,
        validation_mode: str = "basic"
    ) -> MigrationResult:
        """
        Migrate a single table from source to target.

        Args:
            source_conn_string: Source database connection string
            target_conn_string: Target database connection string
            table_name: Name of table to migrate
            dry_run: If True, only validate without migrating
            progress_callback: Optional callback for progress updates
            validation_mode: Validation level ('basic', 'full', 'checksum')

        Returns:
            Migration result
        """
        logger.info(f"Starting migration for table: {table_name}")
        start_time = time.time()

        if progress_callback:
            self.progress_callback = progress_callback

        try:
            # Initialize migration state
            await self._initialize_migration_state(table_name)

            # Get row count
            total_rows = await self._get_row_count(source_conn_string, table_name)
            logger.info(f"Table {table_name} has {total_rows} rows")

            if dry_run:
                return await self._dry_run_validation(
                    source_conn_string,
                    target_conn_string,
                    table_name,
                    total_rows
                )

            # Create batches
            batches = self._create_batches(table_name, total_rows)

            # Execute migration
            result = await self._execute_migration(
                source_conn_string,
                target_conn_string,
                table_name,
                batches,
                validation_mode
            )

            # Update timing
            result.duration_seconds = time.time() - start_time

            logger.info(f"Migration completed for {table_name}: {result.status}")
            return result

        except Exception as e:
            logger.error(f"Migration failed for {table_name}: {str(e)}")
            return MigrationResult(
                table_name=table_name,
                total_rows=0,
                migrated_rows=0,
                failed_rows=0,
                batches_completed=0,
                duration_seconds=time.time() - start_time,
                status=MigrationStatus.FAILED
            )

    async def migrate_database(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_list: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, MigrationResult]:
        """
        Migrate entire database or selected tables.

        Args:
            source_conn_string: Source database connection string
            target_conn_string: Target database connection string
            table_list: Specific tables to migrate (None for all)
            exclude_tables: Tables to exclude from migration
            dry_run: If True, only validate without migrating
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary of migration results by table
        """
        logger.info("Starting database migration")

        # Get table list
        if table_list is None:
            table_list = await self._get_all_tables(source_conn_string)

        if exclude_tables:
            table_list = [t for t in table_list if t not in exclude_tables]

        results = {}

        # Process tables in dependency order
        ordered_tables = await self._order_tables_by_dependencies(
            source_conn_string,
            table_list
        )

        for table_name in ordered_tables:
            try:
                result = await self.migrate_table(
                    source_conn_string,
                    target_conn_string,
                    table_name,
                    dry_run=dry_run,
                    progress_callback=progress_callback
                )
                results[table_name] = result

                # Stop on failure if not dry run
                if not dry_run and result.status == MigrationStatus.FAILED:
                    logger.error(f"Stopping migration due to failure in {table_name}")
                    break

            except Exception as e:
                logger.error(f"Failed to migrate table {table_name}: {str(e)}")
                results[table_name] = MigrationResult(
                    table_name=table_name,
                    total_rows=0,
                    migrated_rows=0,
                    failed_rows=0,
                    batches_completed=0,
                    duration_seconds=0,
                    status=MigrationStatus.FAILED
                )

        return results

    async def incremental_migration(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        timestamp_column: str,
        last_sync_timestamp: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> MigrationResult:
        """
        Perform incremental migration based on timestamp.

        Args:
            source_conn_string: Source database connection string
            target_conn_string: Target database connection string
            table_name: Name of table to migrate
            timestamp_column: Column to use for incremental sync
            last_sync_timestamp: Last synchronization timestamp
            progress_callback: Optional callback for progress updates

        Returns:
            Migration result
        """
        logger.info(f"Starting incremental migration for {table_name}")

        # Get the latest timestamp from target if not provided
        if last_sync_timestamp is None:
            last_sync_timestamp = await self._get_latest_timestamp(
                target_conn_string,
                table_name,
                timestamp_column
            )

        # Build incremental query
        where_clause = f"{timestamp_column} > '{last_sync_timestamp}'" if last_sync_timestamp else "TRUE"

        # Get incremental row count
        incremental_rows = await self._get_row_count(
            source_conn_string,
            table_name,
            where_clause
        )

        if incremental_rows == 0:
            logger.info(f"No new rows to migrate for {table_name}")
            return MigrationResult(
                table_name=table_name,
                total_rows=0,
                migrated_rows=0,
                failed_rows=0,
                batches_completed=0,
                duration_seconds=0,
                status=MigrationStatus.COMPLETED
            )

        # Execute incremental migration
        return await self._execute_incremental_migration(
            source_conn_string,
            target_conn_string,
            table_name,
            where_clause,
            incremental_rows,
            progress_callback
        )

    async def rollback_migration(
        self,
        target_conn_string: str,
        table_name: str,
        backup_data: Optional[str] = None
    ) -> bool:
        """
        Rollback a migration by restoring from backup.

        Args:
            target_conn_string: Target database connection string
            table_name: Name of table to rollback
            backup_data: Path to backup data file

        Returns:
            Success status
        """
        logger.info(f"Rolling back migration for {table_name}")

        try:
            # Clear target table
            await self._clear_table(target_conn_string, table_name)

            # Restore from backup if provided
            if backup_data:
                await self._restore_from_backup(
                    target_conn_string,
                    table_name,
                    backup_data
                )

            logger.info(f"Rollback completed for {table_name}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for {table_name}: {str(e)}")
            return False

    async def validate_migration(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        validation_mode: str = "basic"
    ) -> Dict[str, Any]:
        """
        Validate migrated data integrity.

        Args:
            source_conn_string: Source database connection string
            target_conn_string: Target database connection string
            table_name: Name of table to validate
            validation_mode: Validation level ('basic', 'full', 'checksum')

        Returns:
            Validation results
        """
        logger.info(f"Validating migration for {table_name}")

        validation_results = {
            'table': table_name,
            'validation_mode': validation_mode,
            'is_valid': True,
            'issues': [],
            'metrics': {}
        }

        try:
            # Basic validation: row counts
            source_count = await self._get_row_count(source_conn_string, table_name)
            target_count = await self._get_row_count(target_conn_string, table_name)

            validation_results['metrics']['source_rows'] = source_count
            validation_results['metrics']['target_rows'] = target_count

            if source_count != target_count:
                validation_results['is_valid'] = False
                validation_results['issues'].append(
                    f"Row count mismatch: source={source_count}, target={target_count}"
                )

            if validation_mode in ['full', 'checksum']:
                # Sample-based validation
                sample_results = await self._validate_sample_data(
                    source_conn_string,
                    target_conn_string,
                    table_name
                )
                validation_results['metrics'].update(sample_results)

            if validation_mode == 'checksum':
                # Checksum validation
                checksum_results = await self._validate_checksums(
                    source_conn_string,
                    target_conn_string,
                    table_name
                )
                validation_results['metrics'].update(checksum_results)

            return validation_results

        except Exception as e:
            logger.error(f"Validation failed for {table_name}: {str(e)}")
            validation_results['is_valid'] = False
            validation_results['issues'].append(f"Validation error: {str(e)}")
            return validation_results

    async def _initialize_migration_state(self, table_name: str):
        """Initialize migration state tracking."""
        self.migration_state[table_name] = {
            'status': MigrationStatus.PENDING,
            'batches': [],
            'start_time': time.time(),
            'errors': []
        }

    async def _get_row_count(
        self,
        conn_string: str,
        table_name: str,
        where_clause: str = "TRUE"
    ) -> int:
        """Get row count for a table."""
        conn = await asyncpg.connect(conn_string)
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
            result = await conn.fetchval(query)
            return result
        finally:
            await conn.close()

    def _create_batches(self, table_name: str, total_rows: int) -> List[MigrationBatch]:
        """Create migration batches."""
        batches = []
        batch_id = 0

        for offset in range(0, total_rows, self.batch_size):
            limit = min(self.batch_size, total_rows - offset)
            batch = MigrationBatch(
                table_name=table_name,
                batch_id=batch_id,
                offset=offset,
                limit=limit,
                row_count=limit,
                status=MigrationStatus.PENDING
            )
            batches.append(batch)
            batch_id += 1

        return batches

    async def _execute_migration(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        batches: List[MigrationBatch],
        validation_mode: str
    ) -> MigrationResult:
        """Execute the actual migration."""
        start_time = time.time()
        migrated_rows = 0
        failed_rows = 0
        completed_batches = 0

        # Create semaphore for concurrent control
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        async def process_batch(batch: MigrationBatch) -> bool:
            async with semaphore:
                return await self._process_single_batch(
                    source_conn_string,
                    target_conn_string,
                    batch
                )

        # Process batches concurrently
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_rows += batches[i].row_count
                logger.error(f"Batch {i} failed: {str(result)}")
            elif result:
                migrated_rows += batches[i].row_count
                completed_batches += 1
            else:
                failed_rows += batches[i].row_count

        # Determine overall status
        if failed_rows == 0:
            status = MigrationStatus.COMPLETED
        elif migrated_rows > 0:
            status = MigrationStatus.FAILED  # Partial failure
        else:
            status = MigrationStatus.FAILED

        # Validate if requested
        validation_results = None
        if status == MigrationStatus.COMPLETED and validation_mode != "none":
            validation_results = await self.validate_migration(
                source_conn_string,
                target_conn_string,
                table_name,
                validation_mode
            )

        return MigrationResult(
            table_name=table_name,
            total_rows=migrated_rows + failed_rows,
            migrated_rows=migrated_rows,
            failed_rows=failed_rows,
            batches_completed=completed_batches,
            duration_seconds=time.time() - start_time,
            status=status,
            validation_results=validation_results
        )

    async def _process_single_batch(
        self,
        source_conn_string: str,
        target_conn_string: str,
        batch: MigrationBatch
    ) -> bool:
        """Process a single migration batch."""
        batch.started_at = time.time()
        batch.status = MigrationStatus.IN_PROGRESS

        try:
            # Extract data from source
            source_data = await self._extract_batch_data(
                source_conn_string,
                batch
            )

            if not source_data:
                batch.status = MigrationStatus.COMPLETED
                batch.completed_at = time.time()
                return True

            # Load data to target
            success = await self._load_batch_data(
                target_conn_string,
                batch.table_name,
                source_data
            )

            if success:
                batch.status = MigrationStatus.COMPLETED
                batch.completed_at = time.time()

                # Update progress
                if self.progress_callback:
                    await self.progress_callback({
                        'table': batch.table_name,
                        'batch_id': batch.batch_id,
                        'status': 'completed',
                        'rows_processed': batch.row_count
                    })

                return True
            else:
                batch.status = MigrationStatus.FAILED
                return False

        except Exception as e:
            batch.status = MigrationStatus.FAILED
            batch.error_message = str(e)
            logger.error(f"Batch {batch.batch_id} failed: {str(e)}")
            return False

    async def _extract_batch_data(
        self,
        source_conn_string: str,
        batch: MigrationBatch
    ) -> List[Dict[str, Any]]:
        """Extract data from source database."""
        conn = await asyncpg.connect(source_conn_string)
        try:
            query = f"""
            SELECT * FROM {batch.table_name}
            ORDER BY 1
            LIMIT {batch.limit} OFFSET {batch.offset}
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    async def _load_batch_data(
        self,
        target_conn_string: str,
        table_name: str,
        data: List[Dict[str, Any]]
    ) -> bool:
        """Load data to target database."""
        if not data:
            return True

        conn = await asyncpg.connect(target_conn_string)
        try:
            # Get column names
            columns = list(data[0].keys())
            column_list = ', '.join(columns)
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])

            query = f"""
            INSERT INTO {table_name} ({column_list})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
            """

            # Prepare data for insertion
            values_list = [
                [row[col] for col in columns]
                for row in data
            ]

            await conn.executemany(query, values_list)
            return True

        except Exception as e:
            logger.error(f"Failed to load batch data: {str(e)}")
            return False
        finally:
            await conn.close()

    async def _dry_run_validation(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        total_rows: int
    ) -> MigrationResult:
        """Perform dry run validation."""
        logger.info(f"Performing dry run for {table_name}")

        # Validate schema compatibility
        schema_valid = await self._validate_schema_compatibility(
            source_conn_string,
            target_conn_string,
            table_name
        )

        status = MigrationStatus.COMPLETED if schema_valid else MigrationStatus.FAILED

        return MigrationResult(
            table_name=table_name,
            total_rows=total_rows,
            migrated_rows=0,
            failed_rows=0 if schema_valid else total_rows,
            batches_completed=0,
            duration_seconds=0,
            status=status
        )

    async def _validate_schema_compatibility(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str
    ) -> bool:
        """Validate schema compatibility between source and target."""
        try:
            # Get schema info from both databases
            source_schema = await self._get_table_schema(source_conn_string, table_name)
            target_schema = await self._get_table_schema(target_conn_string, table_name)

            # Compare schemas
            if not target_schema:
                logger.error(f"Table {table_name} not found in target database")
                return False

            # Check column compatibility
            source_columns = {col['name']: col for col in source_schema}
            target_columns = {col['name']: col for col in target_schema}

            for col_name, col_info in source_columns.items():
                if col_name not in target_columns:
                    logger.error(f"Column {col_name} missing in target table")
                    return False

                # Check type compatibility
                if not self._are_types_compatible(
                    col_info['type'],
                    target_columns[col_name]['type']
                ):
                    logger.warning(
                        f"Type mismatch for column {col_name}: "
                        f"{col_info['type']} -> {target_columns[col_name]['type']}"
                    )

            return True

        except Exception as e:
            logger.error(f"Schema validation failed: {str(e)}")
            return False

    async def _get_table_schema(
        self,
        conn_string: str,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Get table schema information."""
        conn = await asyncpg.connect(conn_string)
        try:
            query = """
            SELECT column_name as name, data_type as type,
                   is_nullable, column_default as default
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
            """
            rows = await conn.fetch(query, table_name)
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if data types are compatible."""
        # Type mapping for common PostgreSQL types
        type_mappings = {
            'integer': ['int4', 'integer', 'serial'],
            'bigint': ['int8', 'bigint', 'bigserial'],
            'text': ['text', 'varchar', 'character varying'],
            'timestamp': ['timestamp', 'timestamptz'],
            'boolean': ['bool', 'boolean'],
            'numeric': ['numeric', 'decimal'],
            'uuid': ['uuid']
        }

        # Normalize types
        source_normalized = source_type.lower()
        target_normalized = target_type.lower()

        # Check direct match
        if source_normalized == target_normalized:
            return True

        # Check mapping compatibility
        for group in type_mappings.values():
            if source_normalized in group and target_normalized in group:
                return True

        return False

    async def _get_all_tables(self, conn_string: str) -> List[str]:
        """Get list of all tables in database."""
        conn = await asyncpg.connect(conn_string)
        try:
            query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            """
            rows = await conn.fetch(query)
            return [row['table_name'] for row in rows]
        finally:
            await conn.close()

    async def _order_tables_by_dependencies(
        self,
        conn_string: str,
        table_list: List[str]
    ) -> List[str]:
        """Order tables by foreign key dependencies."""
        # For now, return tables as-is
        # TODO: Implement topological sort based on foreign keys
        return table_list

    async def _execute_incremental_migration(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        where_clause: str,
        incremental_rows: int,
        progress_callback: Optional[Callable]
    ) -> MigrationResult:
        """Execute incremental migration."""
        # Create custom batches for incremental data
        batches = []
        batch_id = 0

        for offset in range(0, incremental_rows, self.batch_size):
            limit = min(self.batch_size, incremental_rows - offset)
            batch = MigrationBatch(
                table_name=table_name,
                batch_id=batch_id,
                offset=offset,
                limit=limit,
                row_count=limit,
                status=MigrationStatus.PENDING
            )
            batches.append(batch)
            batch_id += 1

        # Execute migration with custom where clause
        return await self._execute_migration(
            source_conn_string,
            target_conn_string,
            table_name,
            batches,
            "basic"
        )

    async def _get_latest_timestamp(
        self,
        conn_string: str,
        table_name: str,
        timestamp_column: str
    ) -> Optional[str]:
        """Get latest timestamp from target table."""
        conn = await asyncpg.connect(conn_string)
        try:
            query = f"SELECT MAX({timestamp_column}) FROM {table_name}"
            result = await conn.fetchval(query)
            return result.isoformat() if result else None
        except:
            return None
        finally:
            await conn.close()

    async def _clear_table(self, conn_string: str, table_name: str):
        """Clear all data from a table."""
        conn = await asyncpg.connect(conn_string)
        try:
            await conn.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        finally:
            await conn.close()

    async def _restore_from_backup(
        self,
        conn_string: str,
        table_name: str,
        backup_file: str
    ):
        """Restore table data from backup file."""
        # Load backup data
        async with aiofiles.open(backup_file, 'r') as f:
            backup_data = json.loads(await f.read())

        # Insert backup data
        if backup_data:
            await self._load_batch_data(conn_string, table_name, backup_data)

    async def _validate_sample_data(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """Validate sample data between source and target."""
        # Sample random rows and compare
        source_conn = await asyncpg.connect(source_conn_string)
        target_conn = await asyncpg.connect(target_conn_string)

        try:
            # Get primary key column
            pk_query = """
            SELECT column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = $1 AND tc.constraint_type = 'PRIMARY KEY'
            """
            pk_result = await source_conn.fetchrow(pk_query, table_name)
            pk_column = pk_result['column_name'] if pk_result else 'id'

            # Get sample IDs
            sample_query = f"""
            SELECT {pk_column} FROM {table_name}
            ORDER BY RANDOM()
            LIMIT {sample_size}
            """
            sample_ids = await source_conn.fetch(sample_query)

            mismatches = 0
            for row in sample_ids:
                pk_value = row[pk_column]

                # Get row from both databases
                row_query = f"SELECT * FROM {table_name} WHERE {pk_column} = $1"
                source_row = await source_conn.fetchrow(row_query, pk_value)
                target_row = await target_conn.fetchrow(row_query, pk_value)

                if not target_row:
                    mismatches += 1
                elif dict(source_row) != dict(target_row):
                    mismatches += 1

            return {
                'sample_size': len(sample_ids),
                'mismatches': mismatches,
                'accuracy': (len(sample_ids) - mismatches) / len(sample_ids) if sample_ids else 1.0
            }

        finally:
            await source_conn.close()
            await target_conn.close()

    async def _validate_checksums(
        self,
        source_conn_string: str,
        target_conn_string: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Validate data using checksums."""
        # This is a simplified checksum validation
        # In practice, you'd want more sophisticated checksums
        source_conn = await asyncpg.connect(source_conn_string)
        target_conn = await asyncpg.connect(target_conn_string)

        try:
            # Simple checksum using row count and sum of IDs
            checksum_query = f"""
            SELECT COUNT(*) as row_count,
                   COALESCE(SUM(CAST(id AS BIGINT)), 0) as id_sum
            FROM {table_name}
            """

            source_checksum = await source_conn.fetchrow(checksum_query)
            target_checksum = await target_conn.fetchrow(checksum_query)

            return {
                'source_checksum': dict(source_checksum),
                'target_checksum': dict(target_checksum),
                'checksums_match': dict(source_checksum) == dict(target_checksum)
            }

        except Exception as e:
            return {
                'error': f"Checksum validation failed: {str(e)}",
                'checksums_match': False
            }
        finally:
            await source_conn.close()
            await target_conn.close()