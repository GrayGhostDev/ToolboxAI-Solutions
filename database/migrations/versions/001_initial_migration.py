"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-09-07 04:36:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema."""
    # This is a placeholder migration since we've already deployed the schemas
    # In a real scenario, this would contain the actual schema changes
    pass


def downgrade():
    """Downgrade database schema."""
    # This is a placeholder migration since we've already deployed the schemas
    # In a real scenario, this would contain the rollback changes
    pass
