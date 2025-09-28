"""Performance monitoring and test metrics tables

Revision ID: 003_performance_monitoring
Revises: 002_gpt_migration
Create Date: 2025-09-20 22:06:30.000000

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, ENUM


# revision identifiers, used by Alembic.
revision: str = '003_performance_monitoring'
down_revision: Union[str, None] = '002_gpt_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance monitoring and test metrics tables"""

    # Create ENUM types for monitoring
    performance_status_enum = ENUM(
        'healthy', 'warning', 'critical', 'degraded', 'unknown',
        name='performance_status_type'
    )
    performance_status_enum.create(op.get_bind())

    test_status_enum = ENUM(
        'passed', 'failed', 'skipped', 'error', 'timeout',
        name='test_status_type'
    )
    test_status_enum.create(op.get_bind())

    # Create system performance metrics table
    op.create_table(
        'system_performance_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('service_name', sa.String(100), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False, default='production'),
        sa.Column('timestamp', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('status', performance_status_enum, nullable=False, default='healthy'),
        sa.Column('threshold_warning', sa.Float, nullable=True),
        sa.Column('threshold_critical', sa.Float, nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('baseline_value', sa.Float, nullable=True),
        sa.Column('trend_direction', sa.String(20), nullable=True),  # 'up', 'down', 'stable'
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

    # Create indexes for performance metrics
    op.create_index('idx_performance_metrics_name_service', 'system_performance_metrics', ['metric_name', 'service_name'])
    op.create_index('idx_performance_metrics_timestamp', 'system_performance_metrics', ['timestamp'])
    op.create_index('idx_performance_metrics_status', 'system_performance_metrics', ['status'])
    op.create_index('idx_performance_metrics_environment', 'system_performance_metrics', ['environment'])

    # Create database performance baselines table
    op.create_table(
        'database_performance_baselines',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('baseline_name', sa.String(100), nullable=False, unique=True),
        sa.Column('database_version', sa.String(20), nullable=False),  # PostgreSQL 15, 16, etc.
        sa.Column('measurement_date', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('query_performance', JSONB, nullable=False),  # Query execution times
        sa.Column('connection_metrics', JSONB, nullable=False),  # Pool stats, active connections
        sa.Column('index_performance', JSONB, nullable=False),  # Index usage, scan ratios
        sa.Column('jit_metrics', JSONB, nullable=True),  # JIT compilation stats (PG16+)
        sa.Column('parallel_query_metrics', JSONB, nullable=True),  # Parallel processing stats
        sa.Column('io_metrics', JSONB, nullable=True),  # pg_stat_io data (PG16+)
        sa.Column('cache_hit_ratio', sa.Float, nullable=False),
        sa.Column('avg_response_time_ms', sa.Float, nullable=False),
        sa.Column('transactions_per_second', sa.Float, nullable=False),
        sa.Column('active_connections', sa.Integer, nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=False, default='system')
    )

    # Create index for database baselines
    op.create_index('idx_db_baselines_name', 'database_performance_baselines', ['baseline_name'])
    op.create_index('idx_db_baselines_version', 'database_performance_baselines', ['database_version'])
    op.create_index('idx_db_baselines_date', 'database_performance_baselines', ['measurement_date'])

    # Create test metrics table
    op.create_table(
        'test_execution_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('test_run_id', sa.String(100), nullable=False),
        sa.Column('test_suite', sa.String(100), nullable=False),
        sa.Column('test_name', sa.String(200), nullable=False),
        sa.Column('test_file', sa.String(500), nullable=False),
        sa.Column('status', test_status_enum, nullable=False),
        sa.Column('execution_time_ms', sa.Float, nullable=False),
        sa.Column('memory_usage_mb', sa.Float, nullable=True),
        sa.Column('cpu_usage_percent', sa.Float, nullable=True),
        sa.Column('database_queries', sa.Integer, nullable=True),
        sa.Column('api_calls', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('stack_trace', sa.Text, nullable=True),
        sa.Column('coverage_data', JSONB, nullable=True),
        sa.Column('environment_info', JSONB, nullable=False),
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

    # Create indexes for test metrics
    op.create_index('idx_test_metrics_run_id', 'test_execution_metrics', ['test_run_id'])
    op.create_index('idx_test_metrics_suite', 'test_execution_metrics', ['test_suite'])
    op.create_index('idx_test_metrics_status', 'test_execution_metrics', ['status'])
    op.create_index('idx_test_metrics_started_at', 'test_execution_metrics', ['started_at'])
    op.create_index('idx_test_metrics_execution_time', 'test_execution_metrics', ['execution_time_ms'])

    # Create Redis performance tracking table
    op.create_table(
        'redis_performance_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('redis_version', sa.String(20), nullable=False),
        sa.Column('instance_name', sa.String(100), nullable=False),
        sa.Column('measurement_timestamp', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('memory_usage_mb', sa.Float, nullable=False),
        sa.Column('connected_clients', sa.Integer, nullable=False),
        sa.Column('commands_per_second', sa.Float, nullable=False),
        sa.Column('keyspace_hits', sa.BigInteger, nullable=False),
        sa.Column('keyspace_misses', sa.BigInteger, nullable=False),
        sa.Column('hit_rate_percent', sa.Float, nullable=False),
        sa.Column('evicted_keys', sa.BigInteger, nullable=False),
        sa.Column('pub_sub_channels', sa.Integer, nullable=False),
        sa.Column('pub_sub_patterns', sa.Integer, nullable=False),
        sa.Column('acl_users', sa.Integer, nullable=True),  # Redis 7+ feature
        sa.Column('functions_count', sa.Integer, nullable=True),  # Redis 7+ feature
        sa.Column('performance_data', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

    # Create indexes for Redis metrics
    op.create_index('idx_redis_metrics_instance', 'redis_performance_metrics', ['instance_name'])
    op.create_index('idx_redis_metrics_timestamp', 'redis_performance_metrics', ['measurement_timestamp'])
    op.create_index('idx_redis_metrics_version', 'redis_performance_metrics', ['redis_version'])

    # Insert baseline performance records
    op.execute(f"""
        INSERT INTO database_performance_baselines (
            baseline_name,
            database_version,
            measurement_date,
            query_performance,
            connection_metrics,
            index_performance,
            cache_hit_ratio,
            avg_response_time_ms,
            transactions_per_second,
            active_connections,
            notes,
            created_by
        ) VALUES (
            'phase2_postgresql15_baseline',
            'PostgreSQL 15',
            '{datetime.utcnow().isoformat()}',
            '{{"avg_query_time_ms": 0, "slow_queries": 0, "query_cache_enabled": true}}',
            '{{"max_connections": 100, "pool_size": 20, "pool_overflow": 0}}',
            '{{"index_scans": 0, "seq_scans": 0, "index_hit_rate": 0.95}}',
            0.95,
            0.0,
            0.0,
            0,
            'Baseline measurements before PostgreSQL 16 migration',
            'alembic_migration'
        );
    """)

    # Insert initial system performance metrics
    current_time = datetime.utcnow().isoformat()
    op.execute(f"""
        INSERT INTO system_performance_metrics (
            metric_name,
            service_name,
            environment,
            timestamp,
            value,
            unit,
            status,
            threshold_warning,
            threshold_critical,
            metadata,
            baseline_value
        ) VALUES
        ('response_time_ms', 'backend_api', 'production', '{current_time}', 0.0, 'milliseconds', 'healthy', 500.0, 1000.0, '{{"phase": "2", "baseline": true}}', 0.0),
        ('cpu_usage_percent', 'backend_api', 'production', '{current_time}', 0.0, 'percent', 'healthy', 70.0, 90.0, '{{"phase": "2", "baseline": true}}', 0.0),
        ('memory_usage_mb', 'backend_api', 'production', '{current_time}', 0.0, 'megabytes', 'healthy', 512.0, 1024.0, '{{"phase": "2", "baseline": true}}', 0.0),
        ('database_connections', 'postgresql', 'production', '{current_time}', 0.0, 'count', 'healthy', 80.0, 95.0, '{{"phase": "2", "baseline": true}}', 0.0);
    """)


def downgrade() -> None:
    """Remove performance monitoring tables"""

    # Drop indexes
    op.drop_index('idx_redis_metrics_version')
    op.drop_index('idx_redis_metrics_timestamp')
    op.drop_index('idx_redis_metrics_instance')

    op.drop_index('idx_test_metrics_execution_time')
    op.drop_index('idx_test_metrics_started_at')
    op.drop_index('idx_test_metrics_status')
    op.drop_index('idx_test_metrics_suite')
    op.drop_index('idx_test_metrics_run_id')

    op.drop_index('idx_db_baselines_date')
    op.drop_index('idx_db_baselines_version')
    op.drop_index('idx_db_baselines_name')

    op.drop_index('idx_performance_metrics_environment')
    op.drop_index('idx_performance_metrics_status')
    op.drop_index('idx_performance_metrics_timestamp')
    op.drop_index('idx_performance_metrics_name_service')

    # Drop tables
    op.drop_table('redis_performance_metrics')
    op.drop_table('test_execution_metrics')
    op.drop_table('database_performance_baselines')
    op.drop_table('system_performance_metrics')

    # Drop ENUM types
    test_status_enum = ENUM(name='test_status_type')
    test_status_enum.drop(op.get_bind())

    performance_status_enum = ENUM(name='performance_status_type')
    performance_status_enum.drop(op.get_bind())