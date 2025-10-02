"""Add infrastructure metrics models

Revision ID: infra_metrics_001
Revises: b6d899aab2fb
Create Date: 2025-10-01 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'infra_metrics_001'
down_revision = 'b6d899aab2fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add infrastructure metrics tables for monitoring and observability
    """

    # Create MetricType enum
    metric_type_enum = postgresql.ENUM(
        'system', 'process', 'network', 'disk', 'custom',
        name='metrictype',
        create_type=False
    )
    metric_type_enum.create(op.get_bind(), checkfirst=True)

    # Create HealthStatus enum
    health_status_enum = postgresql.ENUM(
        'healthy', 'degraded', 'unhealthy', 'unknown',
        name='healthstatus',
        create_type=False
    )
    health_status_enum.create(op.get_bind(), checkfirst=True)

    # 1. System Metrics History
    op.create_table(
        'system_metrics_history',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),

        # CPU Metrics
        sa.Column('cpu_percent', sa.Float(), nullable=False),
        sa.Column('cpu_count', sa.Integer(), nullable=False),
        sa.Column('cpu_freq_mhz', sa.Float(), nullable=True),

        # Memory Metrics (GB)
        sa.Column('memory_total_gb', sa.Float(), nullable=False),
        sa.Column('memory_used_gb', sa.Float(), nullable=False),
        sa.Column('memory_available_gb', sa.Float(), nullable=False),
        sa.Column('memory_percent', sa.Float(), nullable=False),

        # Disk Metrics (GB)
        sa.Column('disk_total_gb', sa.Float(), nullable=False),
        sa.Column('disk_used_gb', sa.Float(), nullable=False),
        sa.Column('disk_free_gb', sa.Float(), nullable=False),
        sa.Column('disk_percent', sa.Float(), nullable=False),

        # Network Metrics
        sa.Column('network_bytes_sent', sa.Integer(), nullable=False),
        sa.Column('network_bytes_recv', sa.Integer(), nullable=False),
        sa.Column('network_connections', sa.Integer(), nullable=False),

        # System Info
        sa.Column('uptime_seconds', sa.Float(), nullable=False),
        sa.Column('boot_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for system_metrics_history
    op.create_index(
        'idx_system_metrics_timestamp',
        'system_metrics_history',
        ['timestamp']
    )
    op.create_index(
        'idx_system_metrics_cpu_percent',
        'system_metrics_history',
        ['cpu_percent']
    )
    op.create_index(
        'idx_system_metrics_memory_percent',
        'system_metrics_history',
        ['memory_percent']
    )

    # 2. Process Metrics History
    op.create_table(
        'process_metrics_history',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),

        # Process Info
        sa.Column('pid', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),

        # Resource Usage
        sa.Column('cpu_percent', sa.Float(), nullable=False),
        sa.Column('memory_mb', sa.Float(), nullable=False),
        sa.Column('memory_percent', sa.Float(), nullable=False),

        # Thread and FD Info
        sa.Column('num_threads', sa.Integer(), nullable=False),
        sa.Column('num_fds', sa.Integer(), nullable=True, default=0),

        # Process Lifecycle
        sa.Column('create_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for process_metrics_history
    op.create_index(
        'idx_process_metrics_timestamp',
        'process_metrics_history',
        ['timestamp']
    )
    op.create_index(
        'idx_process_metrics_pid',
        'process_metrics_history',
        ['pid']
    )
    op.create_index(
        'idx_process_metrics_cpu_percent',
        'process_metrics_history',
        ['cpu_percent']
    )

    # 3. Infrastructure Health
    op.create_table(
        'infrastructure_health',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),

        # Overall Status
        sa.Column('status', health_status_enum, nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False),

        # Issues
        sa.Column('warnings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('critical', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Thresholds
        sa.Column('thresholds', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # System Snapshot
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('memory_percent', sa.Float(), nullable=True),
        sa.Column('disk_percent', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for infrastructure_health
    op.create_index(
        'idx_infra_health_timestamp',
        'infrastructure_health',
        ['timestamp']
    )
    op.create_index(
        'idx_infra_health_status',
        'infrastructure_health',
        ['status']
    )
    op.create_index(
        'idx_infra_health_score',
        'infrastructure_health',
        ['health_score']
    )

    # 4. Infrastructure Alerts
    op.create_table(
        'infrastructure_alerts',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        # Alert Info
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),

        # Metric Details
        sa.Column('metric_name', sa.String(100), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, default=False),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),

        # Resolution
        sa.Column('resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for infrastructure_alerts
    op.create_index(
        'idx_alerts_created_at',
        'infrastructure_alerts',
        ['created_at']
    )
    op.create_index(
        'idx_alerts_severity',
        'infrastructure_alerts',
        ['severity']
    )
    op.create_index(
        'idx_alerts_is_active',
        'infrastructure_alerts',
        ['is_active']
    )
    op.create_index(
        'idx_alerts_acknowledged',
        'infrastructure_alerts',
        ['acknowledged']
    )

    # 5. Metric Aggregations
    op.create_table(
        'metric_aggregations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),

        # Time Window
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('aggregation_period', sa.String(20), nullable=False),

        # Metric Type
        sa.Column('metric_type', metric_type_enum, nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),

        # Aggregated Values
        sa.Column('min_value', sa.Float(), nullable=False),
        sa.Column('max_value', sa.Float(), nullable=False),
        sa.Column('avg_value', sa.Float(), nullable=False),
        sa.Column('median_value', sa.Float(), nullable=True),
        sa.Column('stddev_value', sa.Float(), nullable=True),

        # Sample Count
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for metric_aggregations
    op.create_index(
        'idx_agg_timestamp_period',
        'metric_aggregations',
        ['timestamp', 'aggregation_period']
    )
    op.create_index(
        'idx_agg_metric_type_name',
        'metric_aggregations',
        ['metric_type', 'metric_name']
    )


def downgrade() -> None:
    """
    Remove infrastructure metrics tables
    """
    # Drop tables in reverse order
    op.drop_index('idx_agg_metric_type_name', table_name='metric_aggregations')
    op.drop_index('idx_agg_timestamp_period', table_name='metric_aggregations')
    op.drop_table('metric_aggregations')

    op.drop_index('idx_alerts_acknowledged', table_name='infrastructure_alerts')
    op.drop_index('idx_alerts_is_active', table_name='infrastructure_alerts')
    op.drop_index('idx_alerts_severity', table_name='infrastructure_alerts')
    op.drop_index('idx_alerts_created_at', table_name='infrastructure_alerts')
    op.drop_table('infrastructure_alerts')

    op.drop_index('idx_infra_health_score', table_name='infrastructure_health')
    op.drop_index('idx_infra_health_status', table_name='infrastructure_health')
    op.drop_index('idx_infra_health_timestamp', table_name='infrastructure_health')
    op.drop_table('infrastructure_health')

    op.drop_index('idx_process_metrics_cpu_percent', table_name='process_metrics_history')
    op.drop_index('idx_process_metrics_pid', table_name='process_metrics_history')
    op.drop_index('idx_process_metrics_timestamp', table_name='process_metrics_history')
    op.drop_table('process_metrics_history')

    op.drop_index('idx_system_metrics_memory_percent', table_name='system_metrics_history')
    op.drop_index('idx_system_metrics_cpu_percent', table_name='system_metrics_history')
    op.drop_index('idx_system_metrics_timestamp', table_name='system_metrics_history')
    op.drop_table('system_metrics_history')

    # Drop enums
    health_status_enum = postgresql.ENUM(name='healthstatus')
    health_status_enum.drop(op.get_bind(), checkfirst=True)

    metric_type_enum = postgresql.ENUM(name='metrictype')
    metric_type_enum.drop(op.get_bind(), checkfirst=True)
