"""GPT model version transition tracking

Revision ID: 002_gpt_migration
Revises: 001_phase2
Create Date: 2025-09-20 22:06:15.000000

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP, ENUM


# revision identifiers, used by Alembic.
revision: str = '002_gpt_migration'
down_revision: Union[str, None] = '001_phase2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add GPT model migration tracking infrastructure"""

    # Create ENUM for GPT model versions
    gpt_model_enum = ENUM(
        'gpt-4', 'gpt-4-turbo', 'gpt-4.1', 'gpt-4.5', 'gpt-5',
        'claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus', 'claude-4',
        name='gpt_model_type'
    )
    gpt_model_enum.create(op.get_bind())

    migration_status_enum = ENUM(
        'pending', 'in_progress', 'completed', 'failed', 'rollback',
        name='migration_status_type'
    )
    migration_status_enum.create(op.get_bind())

    # Create GPT migration tracking table
    op.create_table(
        'gpt_migration_tracking',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('migration_id', sa.String(100), nullable=False, unique=True),
        sa.Column('from_model', gpt_model_enum, nullable=False),
        sa.Column('to_model', gpt_model_enum, nullable=False),
        sa.Column('migration_status', migration_status_enum, nullable=False, default='pending'),
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('deadline', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),
        sa.Column('affected_services', sa.ARRAY(sa.String(50)), nullable=False),
        sa.Column('performance_baseline', JSONB, nullable=True),
        sa.Column('performance_current', JSONB, nullable=True),
        sa.Column('cost_impact', JSONB, nullable=True),
        sa.Column('rollback_plan', sa.Text, nullable=True),
        sa.Column('migration_notes', sa.Text, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=False, default='system')
    )

    # Create indexes for efficient querying
    op.create_index('idx_gpt_migration_migration_id', 'gpt_migration_tracking', ['migration_id'])
    op.create_index('idx_gpt_migration_status', 'gpt_migration_tracking', ['migration_status'])
    op.create_index('idx_gpt_migration_deadline', 'gpt_migration_tracking', ['deadline'])
    op.create_index('idx_gpt_migration_priority', 'gpt_migration_tracking', ['priority'])
    op.create_index('idx_gpt_migration_models', 'gpt_migration_tracking', ['from_model', 'to_model'])

    # Create GPT model usage tracking table
    op.create_table(
        'gpt_model_usage',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_version', gpt_model_enum, nullable=False),
        sa.Column('service_name', sa.String(100), nullable=False),
        sa.Column('usage_date', sa.Date, nullable=False),
        sa.Column('request_count', sa.Integer, nullable=False, default=0),
        sa.Column('token_count', sa.BigInteger, nullable=False, default=0),
        sa.Column('cost_usd', sa.Numeric(10, 4), nullable=False, default=0),
        sa.Column('avg_response_time_ms', sa.Float, nullable=True),
        sa.Column('error_count', sa.Integer, nullable=False, default=0),
        sa.Column('performance_metrics', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create unique constraint and indexes for usage tracking
    op.create_unique_constraint(
        'uq_gpt_usage_model_service_date',
        'gpt_model_usage',
        ['model_version', 'service_name', 'usage_date']
    )
    op.create_index('idx_gpt_usage_model_version', 'gpt_model_usage', ['model_version'])
    op.create_index('idx_gpt_usage_service_name', 'gpt_model_usage', ['service_name'])
    op.create_index('idx_gpt_usage_date', 'gpt_model_usage', ['usage_date'])

    # Insert critical GPT-4.5 deprecation migration record
    op.execute(f"""
        INSERT INTO gpt_migration_tracking (
            migration_id,
            from_model,
            to_model,
            migration_status,
            started_at,
            deadline,
            priority,
            affected_services,
            rollback_plan,
            migration_notes,
            created_by
        ) VALUES (
            'GPT45_DEPRECATION_2025',
            'gpt-4.5',
            'gpt-4.1',
            'pending',
            '{datetime.utcnow().isoformat()}',
            '2025-07-14T00:00:00Z',
            'critical',
            ARRAY['backend_api', 'content_generation', 'user_assistance', 'code_review'],
            'Gradual rollback using feature flags, A/B testing for performance validation',
            'Critical migration due to GPT-4.5 deprecation on July 14, 2025. 297 days remaining.',
            'alembic_migration'
        );
    """)

    # Insert baseline usage tracking entry
    op.execute(f"""
        INSERT INTO gpt_model_usage (
            model_version,
            service_name,
            usage_date,
            request_count,
            token_count,
            cost_usd,
            performance_metrics,
            created_at
        ) VALUES (
            'gpt-4.1',
            'baseline_measurement',
            CURRENT_DATE,
            0,
            0,
            0.0,
            '{{"baseline_established": true, "migration_ready": true}}',
            NOW()
        );
    """)


def downgrade() -> None:
    """Remove GPT migration tracking infrastructure"""

    # Drop indexes
    op.drop_index('idx_gpt_usage_date')
    op.drop_index('idx_gpt_usage_service_name')
    op.drop_index('idx_gpt_usage_model_version')
    op.drop_constraint('uq_gpt_usage_model_service_date', 'gpt_model_usage')

    op.drop_index('idx_gpt_migration_models')
    op.drop_index('idx_gpt_migration_priority')
    op.drop_index('idx_gpt_migration_deadline')
    op.drop_index('idx_gpt_migration_status')
    op.drop_index('idx_gpt_migration_migration_id')

    # Drop tables
    op.drop_table('gpt_model_usage')
    op.drop_table('gpt_migration_tracking')

    # Drop ENUM types
    migration_status_enum = ENUM(name='migration_status_type')
    migration_status_enum.drop(op.get_bind())

    gpt_model_enum = ENUM(name='gpt_model_type')
    gpt_model_enum.drop(op.get_bind())