"""Add agent system tables

Revision ID: 003_add_agent_system_tables
Revises: 002_roblox_integration_manual
Create Date: 2025-09-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_agent_system_tables'
down_revision: Union[str, None] = '002_roblox_integration_manual'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_instances table
    op.create_table('agent_instances',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('agent_id', sa.String(length=100), nullable=False),
    sa.Column('agent_type', sa.Enum('CONTENT_GENERATOR', 'QUIZ_GENERATOR', 'TERRAIN_GENERATOR', 'SCRIPT_GENERATOR', 'CODE_REVIEWER', 'ROBLOX_ASSET', 'ROBLOX_TESTING', 'ROBLOX_ANALYTICS', name='agenttype'), nullable=False),
    sa.Column('status', sa.Enum('INITIALIZING', 'IDLE', 'BUSY', 'PROCESSING', 'WAITING', 'ERROR', 'OFFLINE', 'MAINTENANCE', name='agentstatus'), nullable=False),
    sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('resource_limits', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('performance_thresholds', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('current_task_id', sa.String(length=100), nullable=True),
    sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_tasks_completed', sa.Integer(), nullable=True),
    sa.Column('total_tasks_failed', sa.Integer(), nullable=True),
    sa.Column('total_execution_time', sa.Float(), nullable=True),
    sa.Column('average_execution_time', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('agent_id')
    )
    
    # Create indexes for agent_instances
    op.create_index('idx_agent_type_status', 'agent_instances', ['agent_type', 'status'], unique=False)
    op.create_index('idx_agent_last_activity', 'agent_instances', ['last_activity'], unique=False)
    op.create_index('idx_agent_performance', 'agent_instances', ['total_tasks_completed', 'total_tasks_failed'], unique=False)
    op.create_index(op.f('ix_agent_instances_agent_id'), 'agent_instances', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_instances_agent_type'), 'agent_instances', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_instances_current_task_id'), 'agent_instances', ['current_task_id'], unique=False)
    op.create_index(op.f('ix_agent_instances_last_activity'), 'agent_instances', ['last_activity'], unique=False)
    op.create_index(op.f('ix_agent_instances_status'), 'agent_instances', ['status'], unique=False)

    # Create agent_executions table
    op.create_table('agent_executions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('task_id', sa.String(length=100), nullable=False),
    sa.Column('agent_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('agent_type', sa.Enum('CONTENT_GENERATOR', 'QUIZ_GENERATOR', 'TERRAIN_GENERATOR', 'SCRIPT_GENERATOR', 'CODE_REVIEWER', 'ROBLOX_ASSET', 'ROBLOX_TESTING', 'ROBLOX_ANALYTICS', name='agenttype'), nullable=False),
    sa.Column('task_type', sa.String(length=100), nullable=False),
    sa.Column('priority', sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', 'CRITICAL', name='taskpriority'), nullable=True),
    sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'RETRYING', name='taskstatus'), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('execution_time_seconds', sa.Float(), nullable=True),
    sa.Column('memory_usage_mb', sa.Float(), nullable=True),
    sa.Column('cpu_usage_percent', sa.Float(), nullable=True),
    sa.Column('quality_score', sa.Float(), nullable=True),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('user_rating', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('session_id', sa.String(length=100), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('max_retries', sa.Integer(), nullable=True),
    sa.Column('parent_task_id', sa.String(length=100), nullable=True),
    sa.CheckConstraint('execution_time_seconds >= 0', name='check_positive_execution_time'),
    sa.CheckConstraint('quality_score >= 0 AND quality_score <= 1', name='check_quality_score_range'),
    sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score_range'),
    sa.CheckConstraint('user_rating >= 1 AND user_rating <= 5', name='check_user_rating_range'),
    sa.CheckConstraint('retry_count >= 0', name='check_positive_retry_count'),
    sa.ForeignKeyConstraint(['agent_instance_id'], ['agent_instances.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_id')
    )
    
    # Create indexes for agent_executions
    op.create_index('idx_execution_status_created', 'agent_executions', ['status', 'created_at'], unique=False)
    op.create_index('idx_execution_agent_task_type', 'agent_executions', ['agent_type', 'task_type'], unique=False)
    op.create_index('idx_execution_user_session', 'agent_executions', ['user_id', 'session_id'], unique=False)
    op.create_index('idx_execution_performance', 'agent_executions', ['execution_time_seconds', 'quality_score'], unique=False)
    op.create_index(op.f('ix_agent_executions_agent_instance_id'), 'agent_executions', ['agent_instance_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_agent_type'), 'agent_executions', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_executions_completed_at'), 'agent_executions', ['completed_at'], unique=False)
    op.create_index(op.f('ix_agent_executions_created_at'), 'agent_executions', ['created_at'], unique=False)
    op.create_index(op.f('ix_agent_executions_parent_task_id'), 'agent_executions', ['parent_task_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_priority'), 'agent_executions', ['priority'], unique=False)
    op.create_index(op.f('ix_agent_executions_session_id'), 'agent_executions', ['session_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_started_at'), 'agent_executions', ['started_at'], unique=False)
    op.create_index(op.f('ix_agent_executions_status'), 'agent_executions', ['status'], unique=False)
    op.create_index(op.f('ix_agent_executions_task_id'), 'agent_executions', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_task_type'), 'agent_executions', ['task_type'], unique=False)
    op.create_index(op.f('ix_agent_executions_user_id'), 'agent_executions', ['user_id'], unique=False)

    # Create agent_metrics table
    op.create_table('agent_metrics',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('agent_instance_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('agent_type', sa.Enum('CONTENT_GENERATOR', 'QUIZ_GENERATOR', 'TERRAIN_GENERATOR', 'SCRIPT_GENERATOR', 'CODE_REVIEWER', 'ROBLOX_ASSET', 'ROBLOX_TESTING', 'ROBLOX_ANALYTICS', name='agenttype'), nullable=False),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('period_duration_minutes', sa.Integer(), nullable=False),
    sa.Column('tasks_completed', sa.Integer(), nullable=True),
    sa.Column('tasks_failed', sa.Integer(), nullable=True),
    sa.Column('tasks_cancelled', sa.Integer(), nullable=True),
    sa.Column('total_tasks', sa.Integer(), nullable=True),
    sa.Column('success_rate', sa.Float(), nullable=True),
    sa.Column('error_rate', sa.Float(), nullable=True),
    sa.Column('average_execution_time', sa.Float(), nullable=True),
    sa.Column('median_execution_time', sa.Float(), nullable=True),
    sa.Column('p95_execution_time', sa.Float(), nullable=True),
    sa.Column('tasks_per_minute', sa.Float(), nullable=True),
    sa.Column('tasks_per_hour', sa.Float(), nullable=True),
    sa.Column('average_quality_score', sa.Float(), nullable=True),
    sa.Column('average_confidence_score', sa.Float(), nullable=True),
    sa.Column('average_user_rating', sa.Float(), nullable=True),
    sa.Column('average_memory_usage_mb', sa.Float(), nullable=True),
    sa.Column('peak_memory_usage_mb', sa.Float(), nullable=True),
    sa.Column('average_cpu_usage_percent', sa.Float(), nullable=True),
    sa.Column('peak_cpu_usage_percent', sa.Float(), nullable=True),
    sa.Column('uptime_percentage', sa.Float(), nullable=True),
    sa.Column('availability_percentage', sa.Float(), nullable=True),
    sa.Column('custom_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('success_rate >= 0 AND success_rate <= 100', name='check_success_rate_range'),
    sa.CheckConstraint('error_rate >= 0 AND error_rate <= 100', name='check_error_rate_range'),
    sa.CheckConstraint('uptime_percentage >= 0 AND uptime_percentage <= 100', name='check_uptime_range'),
    sa.CheckConstraint('availability_percentage >= 0 AND availability_percentage <= 100', name='check_availability_range'),
    sa.CheckConstraint('period_end > period_start', name='check_valid_period'),
    sa.ForeignKeyConstraint(['agent_instance_id'], ['agent_instances.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('agent_instance_id', 'period_start', name='uq_agent_period')
    )
    
    # Create indexes for agent_metrics
    op.create_index('idx_metrics_period', 'agent_metrics', ['period_start', 'period_end'], unique=False)
    op.create_index('idx_metrics_performance', 'agent_metrics', ['success_rate', 'average_execution_time'], unique=False)
    op.create_index(op.f('ix_agent_metrics_agent_instance_id'), 'agent_metrics', ['agent_instance_id'], unique=False)
    op.create_index(op.f('ix_agent_metrics_agent_type'), 'agent_metrics', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_metrics_period_end'), 'agent_metrics', ['period_end'], unique=False)
    op.create_index(op.f('ix_agent_metrics_period_start'), 'agent_metrics', ['period_start'], unique=False)

    # Create agent_task_queue table
    op.create_table('agent_task_queue',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('task_id', sa.String(length=100), nullable=False),
    sa.Column('agent_type', sa.Enum('CONTENT_GENERATOR', 'QUIZ_GENERATOR', 'TERRAIN_GENERATOR', 'SCRIPT_GENERATOR', 'CODE_REVIEWER', 'ROBLOX_ASSET', 'ROBLOX_TESTING', 'ROBLOX_ANALYTICS', name='agenttype'), nullable=False),
    sa.Column('task_type', sa.String(length=100), nullable=False),
    sa.Column('priority', sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', 'CRITICAL', name='taskpriority'), nullable=True),
    sa.Column('task_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'RETRYING', name='taskstatus'), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
    sa.Column('max_execution_time_seconds', sa.Integer(), nullable=True),
    sa.Column('assigned_agent_id', sa.String(length=100), nullable=True),
    sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('depends_on', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('blocks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('max_retries', sa.Integer(), nullable=True),
    sa.Column('retry_delay_seconds', sa.Integer(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('session_id', sa.String(length=100), nullable=True),
    sa.Column('callback_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('max_retries >= 0', name='check_positive_max_retries'),
    sa.CheckConstraint('retry_count >= 0', name='check_positive_retry_count'),
    sa.CheckConstraint('max_execution_time_seconds > 0', name='check_positive_execution_time'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('task_id')
    )
    
    # Create indexes for agent_task_queue
    op.create_index('idx_queue_priority_created', 'agent_task_queue', ['priority', 'created_at'], unique=False)
    op.create_index('idx_queue_agent_status', 'agent_task_queue', ['agent_type', 'status'], unique=False)
    op.create_index('idx_queue_scheduled', 'agent_task_queue', ['scheduled_at', 'status'], unique=False)
    op.create_index('idx_queue_user_session', 'agent_task_queue', ['user_id', 'session_id'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_agent_type'), 'agent_task_queue', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_assigned_agent_id'), 'agent_task_queue', ['assigned_agent_id'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_created_at'), 'agent_task_queue', ['created_at'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_deadline'), 'agent_task_queue', ['deadline'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_priority'), 'agent_task_queue', ['priority'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_scheduled_at'), 'agent_task_queue', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_session_id'), 'agent_task_queue', ['session_id'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_status'), 'agent_task_queue', ['status'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_task_id'), 'agent_task_queue', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_task_type'), 'agent_task_queue', ['task_type'], unique=False)
    op.create_index(op.f('ix_agent_task_queue_user_id'), 'agent_task_queue', ['user_id'], unique=False)

    # Create system_health table
    op.create_table('system_health',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('period_minutes', sa.Integer(), nullable=True),
    sa.Column('total_agents', sa.Integer(), nullable=True),
    sa.Column('active_agents', sa.Integer(), nullable=True),
    sa.Column('idle_agents', sa.Integer(), nullable=True),
    sa.Column('busy_agents', sa.Integer(), nullable=True),
    sa.Column('error_agents', sa.Integer(), nullable=True),
    sa.Column('total_tasks', sa.Integer(), nullable=True),
    sa.Column('completed_tasks', sa.Integer(), nullable=True),
    sa.Column('failed_tasks', sa.Integer(), nullable=True),
    sa.Column('queued_tasks', sa.Integer(), nullable=True),
    sa.Column('running_tasks', sa.Integer(), nullable=True),
    sa.Column('system_success_rate', sa.Float(), nullable=True),
    sa.Column('system_error_rate', sa.Float(), nullable=True),
    sa.Column('average_response_time', sa.Float(), nullable=True),
    sa.Column('p95_response_time', sa.Float(), nullable=True),
    sa.Column('tasks_per_minute', sa.Float(), nullable=True),
    sa.Column('tasks_per_hour', sa.Float(), nullable=True),
    sa.Column('total_memory_usage_mb', sa.Float(), nullable=True),
    sa.Column('total_cpu_usage_percent', sa.Float(), nullable=True),
    sa.Column('disk_usage_percent', sa.Float(), nullable=True),
    sa.Column('network_io_mbps', sa.Float(), nullable=True),
    sa.Column('queue_length', sa.Integer(), nullable=True),
    sa.Column('average_queue_wait_time', sa.Float(), nullable=True),
    sa.Column('queue_processing_rate', sa.Float(), nullable=True),
    sa.Column('overall_health_score', sa.Float(), nullable=True),
    sa.Column('availability_percentage', sa.Float(), nullable=True),
    sa.Column('active_alerts', sa.Integer(), nullable=True),
    sa.Column('critical_issues', sa.Integer(), nullable=True),
    sa.Column('warnings', sa.Integer(), nullable=True),
    sa.Column('custom_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.CheckConstraint('overall_health_score >= 0 AND overall_health_score <= 100', name='check_health_score_range'),
    sa.CheckConstraint('availability_percentage >= 0 AND availability_percentage <= 100', name='check_availability_range'),
    sa.CheckConstraint('system_success_rate >= 0 AND system_success_rate <= 100', name='check_system_success_rate'),
    sa.CheckConstraint('system_error_rate >= 0 AND system_error_rate <= 100', name='check_system_error_rate'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for system_health
    op.create_index('idx_health_timestamp', 'system_health', ['timestamp'], unique=False)
    op.create_index('idx_health_score', 'system_health', ['overall_health_score', 'availability_percentage'], unique=False)
    op.create_index(op.f('ix_system_health_timestamp'), 'system_health', ['timestamp'], unique=False)

    # Create agent_configurations table
    op.create_table('agent_configurations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('version', sa.String(length=20), nullable=False),
    sa.Column('agent_type', sa.Enum('CONTENT_GENERATOR', 'QUIZ_GENERATOR', 'TERRAIN_GENERATOR', 'SCRIPT_GENERATOR', 'CODE_REVIEWER', 'ROBLOX_ASSET', 'ROBLOX_TESTING', 'ROBLOX_ANALYTICS', name='agenttype'), nullable=False),
    sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('resource_limits', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('performance_thresholds', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('environment', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('schema_version', sa.String(length=20), nullable=True),
    sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'version', 'agent_type', name='uq_config_name_version_type')
    )
    
    # Create indexes for agent_configurations
    op.create_index('idx_config_active', 'agent_configurations', ['is_active', 'agent_type'], unique=False)
    op.create_index('idx_config_environment', 'agent_configurations', ['environment', 'is_active'], unique=False)
    op.create_index(op.f('ix_agent_configurations_agent_type'), 'agent_configurations', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agent_configurations_created_by'), 'agent_configurations', ['created_by'], unique=False)
    op.create_index(op.f('ix_agent_configurations_environment'), 'agent_configurations', ['environment'], unique=False)
    op.create_index(op.f('ix_agent_configurations_is_active'), 'agent_configurations', ['is_active'], unique=False)
    op.create_index(op.f('ix_agent_configurations_is_default'), 'agent_configurations', ['is_default'], unique=False)
    op.create_index(op.f('ix_agent_configurations_name'), 'agent_configurations', ['name'], unique=False)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('agent_configurations')
    op.drop_table('system_health')
    op.drop_table('agent_task_queue')
    op.drop_table('agent_metrics')
    op.drop_table('agent_executions')
    op.drop_table('agent_instances')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS agenttype')
    op.execute('DROP TYPE IF EXISTS agentstatus')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS taskpriority')
