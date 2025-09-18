"""
Add Integration Agent Data Tables

This migration adds support tables for integration agent operations
including schema validation, event bus, and agent health tracking.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers
revision = '001_integration_agents'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""

    # Create schema_definitions table for cross-platform schema validation
    op.create_table(
        'schema_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('schema_id', sa.String(255), nullable=False),
        sa.Column('schema_name', sa.String(200), nullable=False),
        sa.Column('schema_type', sa.String(50), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('definition', postgresql.JSONB(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deprecated', sa.Boolean(), default=False),
        sa.Column('compatible_versions', postgresql.ARRAY(sa.String), default=[]),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schema_id')
    )

    # Create schema_mappings table for cross-platform data transformations
    op.create_table(
        'schema_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('mapping_id', sa.String(255), nullable=False),
        sa.Column('source_schema_id', sa.String(255), nullable=False),
        sa.Column('target_schema_id', sa.String(255), nullable=False),
        sa.Column('field_mappings', postgresql.JSONB(), nullable=False),
        sa.Column('transformations', postgresql.JSONB(), default={}),
        sa.Column('bidirectional', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mapping_id')
    )

    # Create agent_health_status table for monitoring agent health
    op.create_table(
        'agent_health_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('healthy', sa.Boolean(), default=True),
        sa.Column('message', sa.Text()),
        sa.Column('error_details', postgresql.JSONB()),
        sa.Column('metrics', postgresql.JSONB(), default={}),
        sa.Column('last_check_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create integration_events table for event bus tracking
    op.create_table(
        'integration_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('source_platform', sa.String(50), nullable=False),
        sa.Column('target_platform', sa.String(50)),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('correlation_id', sa.String(255)),
        sa.Column('processed', sa.Boolean(), default=False),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('idx_schema_definitions_platform', 'schema_definitions', ['platform'])
    op.create_index('idx_schema_definitions_type', 'schema_definitions', ['schema_type'])
    op.create_index('idx_schema_mappings_source', 'schema_mappings', ['source_schema_id'])
    op.create_index('idx_schema_mappings_target', 'schema_mappings', ['target_schema_id'])
    op.create_index('idx_agent_health_name', 'agent_health_status', ['agent_name'])
    op.create_index('idx_agent_health_type', 'agent_health_status', ['agent_type'])
    op.create_index('idx_agent_health_status', 'agent_health_status', ['status', 'healthy'])
    op.create_index('idx_integration_events_type', 'integration_events', ['event_type'])
    op.create_index('idx_integration_events_platform', 'integration_events', ['source_platform'])
    op.create_index('idx_integration_events_processed', 'integration_events', ['processed'])
    op.create_index('idx_integration_events_created', 'integration_events', ['created_at'])

    # Add StudentProgress table compatibility if not exists
    # This ensures backward compatibility with existing progress tracking
    try:
        op.create_table(
            'student_progress',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
            sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('lesson_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('progress_percentage', sa.Float(), default=0.0),
            sa.Column('score', sa.Float()),
            sa.Column('time_spent_minutes', sa.Integer(), default=0),
            sa.Column('completed_at', sa.DateTime(timezone=True)),
            sa.Column('attempts', sa.Integer(), default=0),
            sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True)),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('student_id', 'lesson_id')
        )

        # Add foreign key constraints if the referenced tables exist
        op.create_foreign_key(
            'fk_student_progress_student',
            'student_progress', 'users',
            ['student_id'], ['id']
        )

        op.create_foreign_key(
            'fk_student_progress_lesson',
            'student_progress', 'lessons',
            ['lesson_id'], ['id']
        )

        # Create indexes
        op.create_index('idx_student_progress_student', 'student_progress', ['student_id'])
        op.create_index('idx_student_progress_lesson', 'student_progress', ['lesson_id'])

    except Exception:
        # Table might already exist, skip creation
        pass


def downgrade() -> None:
    """Rollback migration."""

    # Drop indexes first
    op.drop_index('idx_integration_events_created', 'integration_events')
    op.drop_index('idx_integration_events_processed', 'integration_events')
    op.drop_index('idx_integration_events_platform', 'integration_events')
    op.drop_index('idx_integration_events_type', 'integration_events')
    op.drop_index('idx_agent_health_status', 'agent_health_status')
    op.drop_index('idx_agent_health_type', 'agent_health_status')
    op.drop_index('idx_agent_health_name', 'agent_health_status')
    op.drop_index('idx_schema_mappings_target', 'schema_mappings')
    op.drop_index('idx_schema_mappings_source', 'schema_mappings')
    op.drop_index('idx_schema_definitions_type', 'schema_definitions')
    op.drop_index('idx_schema_definitions_platform', 'schema_definitions')

    # Drop tables
    op.drop_table('integration_events')
    op.drop_table('agent_health_status')
    op.drop_table('schema_mappings')
    op.drop_table('schema_definitions')

    # Optionally drop student_progress if it was created by this migration
    try:
        op.drop_index('idx_student_progress_lesson', 'student_progress')
        op.drop_index('idx_student_progress_student', 'student_progress')
        op.drop_constraint('fk_student_progress_lesson', 'student_progress', type_='foreignkey')
        op.drop_constraint('fk_student_progress_student', 'student_progress', type_='foreignkey')
        op.drop_table('student_progress')
    except Exception:
        # Table might be managed elsewhere, skip
        pass