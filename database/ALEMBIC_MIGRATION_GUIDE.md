# Alembic Migration Guide - Modern Async Setup (2025)

Complete guide for database migrations using Alembic with async SQLAlchemy 2.0.

## 📋 Table of Contents

- [Setup](#setup)
- [Creating Migrations](#creating-migrations)
- [Running Migrations](#running-migrations)
- [Migration Patterns](#migration-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Setup

### Files Created

1. **`database/alembic_modern.ini`** - Modern Alembic configuration
2. **`database/migrations/env_modern.py`** - Async environment setup
3. **Migration templates** - Auto-formatting with Black

### Configuration

The modern setup uses:
- **Async engine**: `postgresql+asyncpg://`
- **Auto-formatting**: Black for generated migrations
- **Type hints**: Full type annotations in migrations
- **Environment-based URLs**: Reads from `DATABASE_URL` or `POSTGRES_*` vars

## Creating Migrations

### Auto-generate from Model Changes

```bash
# Using modern async configuration
alembic -c database/alembic_modern.ini revision --autogenerate -m "Add user roles"

# Check what would be generated (dry run)
alembic -c database/alembic_modern.ini revision --autogenerate -m "Test" --sql
```

### Create Empty Migration

```bash
# For custom data migrations or complex changes
alembic -c database/alembic_modern.ini revision -m "Custom migration"
```

### Migration File Location

Migrations are created in: `database/migrations/versions/`

File format: `YYYYMMDD_HHMM-{revision}_{slug}.py`

Example: `20251001_2130-abc123def456_add_user_roles.py`

## Running Migrations

### Upgrade Database

```bash
# Upgrade to latest version
alembic -c database/alembic_modern.ini upgrade head

# Upgrade one version
alembic -c database/alembic_modern.ini upgrade +1

# Upgrade to specific revision
alembic -c database/alembic_modern.ini upgrade abc123
```

### Downgrade Database

```bash
# Downgrade one version
alembic -c database/alembic_modern.ini downgrade -1

# Downgrade to specific revision
alembic -c database/alembic_modern.ini downgrade abc123

# Downgrade to base (empty database)
alembic -c database/alembic_modern.ini downgrade base
```

### Check Current Version

```bash
# Show current revision
alembic -c database/alembic_modern.ini current

# Show revision history
alembic -c database/alembic_modern.ini history

# Show detailed history
alembic -c database/alembic_modern.ini history --verbose
```

### Generate SQL Without Running

```bash
# Preview SQL for upgrade
alembic -c database/alembic_modern.ini upgrade head --sql > upgrade.sql

# Preview SQL for downgrade
alembic -c database/alembic_modern.ini downgrade -1 --sql > downgrade.sql
```

## Migration Patterns

### 1. Add Table

```python
"""Add user profiles table

Revision ID: abc123
Create Date: 2025-10-01 21:00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'abc123'
down_revision: Union[str, None] = None


def upgrade() -> None:
    """Create user_profiles table."""
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('skills', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'],
                               ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_user_profiles_user_id'),
    )

    # Add index
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'])


def downgrade() -> None:
    """Drop user_profiles table."""
    op.drop_index('idx_user_profiles_user_id', 'user_profiles')
    op.drop_table('user_profiles')
```

### 2. Add Column

```python
"""Add email_verified column to users

Revision ID: def456
Create Date: 2025-10-01 21:15:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'def456'
down_revision: Union[str, None] = 'abc123'


def upgrade() -> None:
    """Add email_verified column."""
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(),
                 nullable=False, server_default='false')
    )

    op.add_column(
        'users',
        sa.Column('email_verified_at', sa.DateTime(timezone=True),
                 nullable=True)
    )


def downgrade() -> None:
    """Remove email_verified columns."""
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
```

### 3. Add Index

```python
"""Add composite index for user queries

Revision ID: ghi789
Create Date: 2025-10-01 21:30:00
"""

from typing import Sequence, Union
from alembic import op

revision: str = 'ghi789'
down_revision: Union[str, None] = 'def456'


def upgrade() -> None:
    """Add composite index."""
    op.create_index(
        'idx_users_org_status',
        'users',
        ['organization_id', 'status'],
        unique=False
    )

    # Partial index (PostgreSQL specific)
    op.create_index(
        'idx_users_active',
        'users',
        ['organization_id', 'status'],
        postgresql_where=sa.text("status = 'active'")
    )


def downgrade() -> None:
    """Drop indexes."""
    op.drop_index('idx_users_active', 'users')
    op.drop_index('idx_users_org_status', 'users')
```

### 4. Add Enum Type

```python
"""Add user role enum

Revision ID: jkl012
Create Date: 2025-10-01 21:45:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'jkl012'
down_revision: Union[str, None] = 'ghi789'


def upgrade() -> None:
    """Add user_role enum and column."""
    # Create enum type
    user_role_enum = sa.Enum(
        'student', 'teacher', 'admin', 'parent',
        name='user_role',
        create_type=True
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Add column
    op.add_column(
        'users',
        sa.Column('role', user_role_enum,
                 nullable=False, server_default='student')
    )

    # Add index
    op.create_index('idx_users_role', 'users', ['role'])


def downgrade() -> None:
    """Remove role column and enum."""
    op.drop_index('idx_users_role', 'users')
    op.drop_column('users', 'role')

    # Drop enum type
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
```

### 5. Data Migration

```python
"""Migrate user status values

Revision ID: mno345
Create Date: 2025-10-01 22:00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'mno345'
down_revision: Union[str, None] = 'jkl012'


def upgrade() -> None:
    """Update user status values."""
    # Use raw SQL for data migration
    conn = op.get_bind()

    # Update status from old to new values
    conn.execute(
        sa.text(
            "UPDATE users SET status = 'active' "
            "WHERE status = 'enabled'"
        )
    )

    conn.execute(
        sa.text(
            "UPDATE users SET status = 'inactive' "
            "WHERE status = 'disabled'"
        )
    )


def downgrade() -> None:
    """Revert status values."""
    conn = op.get_bind()

    conn.execute(
        sa.text(
            "UPDATE users SET status = 'enabled' "
            "WHERE status = 'active'"
        )
    )

    conn.execute(
        sa.text(
            "UPDATE users SET status = 'disabled' "
            "WHERE status = 'inactive'"
        )
    )
```

### 6. Full-Text Search

```python
"""Add full-text search to content

Revision ID: pqr678
Create Date: 2025-10-01 22:15:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'pqr678'
down_revision: Union[str, None] = 'mno345'


def upgrade() -> None:
    """Add full-text search support."""
    # Add tsvector column with computed value
    op.add_column(
        'educational_content',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR,
            sa.Computed(
                "to_tsvector('english', "
                "coalesce(title, '') || ' ' || "
                "coalesce(description, '') || ' ' || "
                "coalesce(content, ''))",
                persisted=True
            ),
            nullable=True
        )
    )

    # Add GIN index for fast full-text search
    op.create_index(
        'idx_content_search',
        'educational_content',
        ['search_vector'],
        postgresql_using='gin'
    )


def downgrade() -> None:
    """Remove full-text search."""
    op.drop_index('idx_content_search', 'educational_content')
    op.drop_column('educational_content', 'search_vector')
```

## Best Practices

### 1. Always Test Migrations

```bash
# Test upgrade
alembic -c database/alembic_modern.ini upgrade head

# Test downgrade
alembic -c database/alembic_modern.ini downgrade -1

# Test upgrade again
alembic -c database/alembic_modern.ini upgrade head
```

### 2. Use Transactions

Migrations run in transactions by default. For operations that can't run in transactions:

```python
def upgrade() -> None:
    """Create index concurrently (no transaction)."""
    # Disable transaction for this migration
    op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users(email)")
```

### 3. Handle Nullable Columns Carefully

```python
def upgrade() -> None:
    """Add non-null column safely."""
    # Step 1: Add as nullable
    op.add_column('users', sa.Column('new_field', sa.String(50), nullable=True))

    # Step 2: Populate data
    op.execute("UPDATE users SET new_field = 'default' WHERE new_field IS NULL")

    # Step 3: Make non-nullable
    op.alter_column('users', 'new_field', nullable=False)
```

### 4. Document Complex Migrations

```python
"""Complex migration with multiple steps

This migration performs the following:
1. Adds new user_type column
2. Migrates data from old role system
3. Removes deprecated columns
4. Updates indexes

Revision ID: xyz123
Create Date: 2025-10-01 22:30:00
"""
```

### 5. Use Batch Operations for SQLite

```python
from alembic import op

def upgrade() -> None:
    """Use batch for SQLite compatibility."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(50)))
        batch_op.create_index('idx_new_field', ['new_field'])
```

## Environment Variables

Set these before running migrations:

```bash
# Option 1: Full DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"

# Option 2: Individual components
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="educational_platform_dev"
export POSTGRES_USER="eduplatform"
export POSTGRES_PASSWORD="eduplatform2024"
```

## Troubleshooting

### Issue: "Target database is not up to date"

```bash
# Check current version
alembic -c database/alembic_modern.ini current

# Check history
alembic -c database/alembic_modern.ini history

# Stamp database to specific version
alembic -c database/alembic_modern.ini stamp head
```

### Issue: "Can't locate revision"

```bash
# Clear pycache
find database/migrations -type d -name __pycache__ -exec rm -rf {} +

# Regenerate script
alembic -c database/alembic_modern.ini revision -m "Your migration"
```

### Issue: Migration fails partway

```bash
# Check database state
alembic -c database/alembic_modern.ini current

# If needed, manually fix database then stamp
alembic -c database/alembic_modern.ini stamp <revision>
```

### Issue: Asyncio errors

Make sure you're using the modern config:
```bash
# ✅ Correct
alembic -c database/alembic_modern.ini upgrade head

# ❌ Wrong (uses old sync env.py)
alembic upgrade head
```

## Migration Workflow

### Development

```bash
# 1. Make model changes in database/models/
# 2. Generate migration
alembic -c database/alembic_modern.ini revision --autogenerate -m "Description"

# 3. Review generated migration file
# 4. Test upgrade
alembic -c database/alembic_modern.ini upgrade head

# 5. Test downgrade
alembic -c database/alembic_modern.ini downgrade -1

# 6. Test upgrade again
alembic -c database/alembic_modern.ini upgrade head

# 7. Commit migration file
git add database/migrations/versions/YYYYMMDD_*.py
git commit -m "Add migration: Description"
```

### Production

```bash
# 1. Backup database first!
pg_dump dbname > backup.sql

# 2. Preview SQL
alembic -c database/alembic_modern.ini upgrade head --sql > migration.sql

# 3. Review migration.sql

# 4. Run migration
alembic -c database/alembic_modern.ini upgrade head

# 5. Verify
alembic -c database/alembic_modern.ini current
```

## Quick Reference

```bash
# Create migration
alembic -c database/alembic_modern.ini revision --autogenerate -m "msg"

# Upgrade
alembic -c database/alembic_modern.ini upgrade head

# Downgrade
alembic -c database/alembic_modern.ini downgrade -1

# Check status
alembic -c database/alembic_modern.ini current

# History
alembic -c database/alembic_modern.ini history

# SQL preview
alembic -c database/alembic_modern.ini upgrade head --sql
```

---

**Version**: 2.0.0
**Last Updated**: 2025-10-01
**Status**: ✅ Ready for Production
