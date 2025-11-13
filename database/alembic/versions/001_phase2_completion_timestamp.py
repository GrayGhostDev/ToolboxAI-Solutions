"""Phase 2 completion timestamp tracking

Revision ID: 001_phase2
Revises: baseline
Create Date: 2025-09-20 22:06:00.000000

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

# revision identifiers, used by Alembic.
revision: str = "001_phase2"
down_revision: Union[str, None] = "baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 2 completion tracking tables and columns"""

    # Create phase_completions table for tracking completion timestamps
    op.create_table(
        "phase_completions",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("phase_name", sa.String(50), nullable=False, unique=True),
        sa.Column("completion_timestamp", TIMESTAMP(timezone=True), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("features_completed", JSONB, nullable=False, default={}),
        sa.Column("performance_metrics", JSONB, nullable=True),
        sa.Column("rollback_point", sa.String(100), nullable=True),
        sa.Column("created_at", TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("created_by", sa.String(100), nullable=False, default="system"),
        sa.Column("notes", sa.Text, nullable=True),
    )

    # Create index for efficient phase lookups
    op.create_index("idx_phase_completions_phase_name", "phase_completions", ["phase_name"])
    op.create_index(
        "idx_phase_completions_completion_timestamp", "phase_completions", ["completion_timestamp"]
    )

    # Add Phase 2 completion columns to existing users table if it exists
    try:
        op.add_column(
            "users",
            sa.Column("phase2_migration_status", sa.String(20), nullable=True, default="pending"),
        )
        op.add_column(
            "users", sa.Column("phase2_completion_date", TIMESTAMP(timezone=True), nullable=True)
        )
        op.add_column("users", sa.Column("phase2_performance_score", sa.Float, nullable=True))
    except Exception:
        # Table might not exist yet, skip for now
        pass

    # Insert Phase 2 baseline entry
    op.execute(
        f"""
        INSERT INTO phase_completions (
            phase_name,
            completion_timestamp,
            version,
            features_completed,
            created_by,
            notes
        ) VALUES (
            'phase2_baseline',
            '{datetime.utcnow().isoformat()}',
            '2.0.0-beta',
            '{{"database_modernization": "in_progress", "postgresql16": "preparing", "redis7": "preparing", "monitoring": "enhanced"}}',
            'alembic_migration',
            'Phase 2 baseline migration - tracking infrastructure setup'
        );
    """
    )


def downgrade() -> None:
    """Remove Phase 2 completion tracking"""

    # Remove added columns from users table
    try:
        op.drop_column("users", "phase2_performance_score")
        op.drop_column("users", "phase2_completion_date")
        op.drop_column("users", "phase2_migration_status")
    except Exception:
        # Columns might not exist, continue
        pass

    # Drop indexes
    op.drop_index("idx_phase_completions_completion_timestamp")
    op.drop_index("idx_phase_completions_phase_name")

    # Drop table
    op.drop_table("phase_completions")
