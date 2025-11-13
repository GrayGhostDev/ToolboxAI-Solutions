"""Rename metadata fields to avoid SQLAlchemy conflict

Revision ID: c313efdda331
Revises: 2025_10_10_org_id
Create Date: 2025-10-11 21:21:01.139524

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c313efdda331"
down_revision: Union[str, None] = "2025_10_10_org_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename metadata field in educational_content table to content_metadata
    op.alter_column(
        "educational_content",
        "metadata",
        new_column_name="content_metadata",
        existing_type=sa.dialects.postgresql.JSONB,
        existing_nullable=False,
    )

    # Rename metadata field in content_attachment table to attachment_metadata
    op.alter_column(
        "content_attachment",
        "metadata",
        new_column_name="attachment_metadata",
        existing_type=sa.dialects.postgresql.JSONB,
        existing_nullable=False,
    )


def downgrade() -> None:
    # Revert content_metadata back to metadata in educational_content table
    op.alter_column(
        "educational_content",
        "content_metadata",
        new_column_name="metadata",
        existing_type=sa.dialects.postgresql.JSONB,
        existing_nullable=False,
    )

    # Revert attachment_metadata back to metadata in content_attachment table
    op.alter_column(
        "content_attachment",
        "attachment_metadata",
        new_column_name="metadata",
        existing_type=sa.dialects.postgresql.JSONB,
        existing_nullable=False,
    )
