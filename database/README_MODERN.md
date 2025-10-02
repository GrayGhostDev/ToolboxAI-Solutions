# Modern Database Layer - SQLAlchemy 2.0 (2025 Standards)

Complete async database implementation using modern SQLAlchemy 2.0 patterns with full type safety.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Models](#models)
- [Session Management](#session-management)
- [Repository Pattern](#repository-pattern)
- [Caching](#caching)
- [Migrations](#migrations)
- [Best Practices](#best-practices)
- [Performance](#performance)

## Overview

This database layer provides:

- ✅ **SQLAlchemy 2.0**: Latest async patterns with Mapped type annotations
- ✅ **Type Safety**: Full type hints for IDE support and validation
- ✅ **Connection Pooling**: Optimized async connection management
- ✅ **Redis Caching**: Automatic caching with invalidation
- ✅ **Repository Pattern**: Clean separation of data access logic
- ✅ **Multi-tenancy**: Built-in tenant isolation with RLS support
- ✅ **Soft Deletes**: Data retention with audit trail
- ✅ **Performance**: Indexed queries, eager loading, query optimization

## Architecture

```
database/
├── models/
│   ├── base_modern.py          # Modern base classes with Mapped types
│   ├── user_modern.py          # User, UserProfile, UserSession
│   └── content_modern.py       # Educational content models
├── repositories/
│   ├── base_repository.py      # Generic repository pattern
│   └── user_repository.py      # User-specific operations
├── session_modern.py           # Async session management
├── cache_modern.py             # Redis caching layer
└── README_MODERN.md           # This file
```

## Quick Start

### 1. Import and Setup

```python
from database.session_modern import db_manager, get_async_session
from database.models.user_modern import User, UserRole
from database.repositories.user_repository import UserRepository
```

### 2. Create User (FastAPI Example)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.post("/users")
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    repo = UserRepository()

    user = await repo.create_user_with_profile(
        session=session,
        organization_id=current_org_id,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.STUDENT,
    )

    await session.commit()
    return user
```

### 3. Query Users

```python
@app.get("/users")
async def get_users(
    session: AsyncSession = Depends(get_async_session)
):
    repo = UserRepository()

    users = await repo.get_active_users(
        session=session,
        organization_id=current_org_id,
        role=UserRole.STUDENT,
        skip=0,
        limit=50,
    )

    return users
```

### 4. Update User

```python
@app.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    repo = UserRepository()

    user = await repo.update(
        session=session,
        id=user_id,
        **updates.dict(exclude_unset=True)
    )

    await session.commit()
    return user
```

## Models

### Base Classes

All models inherit from one of these base classes:

#### `BaseModel`
- UUID primary key
- Timestamps (created_at, updated_at)

#### `FullBaseModel`
- Everything in BaseModel
- Audit fields (created_by_id, updated_by_id)
- Soft delete (deleted_at, deleted_by_id)

#### `TenantBaseModel`
- Everything in FullBaseModel
- Multi-tenant (organization_id)
- Row-level security support

#### `GlobalBaseModel`
- Like FullBaseModel but without tenant isolation
- For system-wide data (Organization model, etc.)

### User Models

```python
from database.models.user_modern import User, UserProfile, UserSession

# User with full tenant support
class User(TenantBaseModel):
    email: Mapped[str]
    username: Mapped[str]
    hashed_password: Mapped[str]
    role: Mapped[UserRole]
    status: Mapped[UserStatus]
    # ... see user_modern.py for complete model
```

### Content Models

```python
from database.models.content_modern import (
    EducationalContent,
    ContentAttachment,
    ContentComment,
    ContentRating
)

# Educational content with full-text search
class EducationalContent(TenantBaseModel):
    title: Mapped[str]
    content: Mapped[str]
    status: Mapped[ContentStatus]
    difficulty_level: Mapped[DifficultyLevel]
    # Full-text search vector
    search_vector: Mapped[Optional[str]]
    # ... see content_modern.py for complete model
```

## Session Management

### Basic Session Usage

```python
from database.session_modern import db_manager

# Simple session
async with db_manager.session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

### Transaction Management

```python
# Automatic commit/rollback
async with db_manager.transaction() as session:
    user = User(email="test@example.com", ...)
    session.add(user)
    # Auto-commit on success, auto-rollback on error
```

### Tenant-Scoped Session

```python
# Automatic tenant filtering with RLS
async with db_manager.tenant_session(org_id) as session:
    # All queries automatically filtered by tenant
    users = await session.execute(select(User))
```

### FastAPI Dependency

```python
from fastapi import Depends
from database.session_modern import get_async_session

@app.get("/data")
async def get_data(session: AsyncSession = Depends(get_async_session)):
    # Session automatically managed
    result = await session.execute(select(Model))
    return result.scalars().all()
```

## Repository Pattern

### Using Base Repository

```python
from database.repositories.base_repository import BaseRepository
from database.models.user_modern import User

# Create repository
repo = BaseRepository(User)

# Get by ID
user = await repo.get_by_id(session, user_id)

# Create
user = await repo.create(
    session,
    email="new@example.com",
    username="newuser",
    ...
)

# Update
user = await repo.update(
    session,
    user_id,
    full_name="New Name"
)

# Delete (soft by default)
await repo.delete(session, user_id, soft=True)

# Find with filters
users = await repo.find(
    session,
    filters={"role": UserRole.STUDENT, "status": UserStatus.ACTIVE},
    skip=0,
    limit=10,
    order_by="created_at",
    descending=True
)
```

### Custom Repository

```python
from database.repositories.user_repository import UserRepository

repo = UserRepository()

# User-specific operations
user = await repo.get_by_email(session, "user@example.com", org_id)

user = await repo.create_user_with_profile(
    session,
    organization_id=org_id,
    email="new@example.com",
    username="newuser",
    hashed_password=hashed_pwd,
    bio="Student bio here"  # Profile data
)

# Get statistics
stats = await repo.get_user_statistics(session, org_id)
```

## Caching

### Cache Decorator

```python
from database.cache_modern import cache_result, invalidate_cache

# Cache function results
@cache_result(prefix="user", expire=600)
async def get_user(session: AsyncSession, user_id: UUID) -> User:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one()

# Invalidate cache after updates
@invalidate_cache(prefix="user")
async def update_user(session: AsyncSession, user_id: UUID, **data):
    # Update logic
    pass
```

### Manual Cache Operations

```python
from database.cache_modern import redis_cache

# Set value
await redis_cache.set("key", {"data": "value"}, expire=300)

# Get value
data = await redis_cache.get("key")

# Delete pattern
await redis_cache.delete_pattern("user:*")
```

## Migrations

### Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user roles"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current
```

### Migration Template

```python
"""Add user roles

Revision ID: abc123
Create Date: 2025-10-01 20:00:00
"""

def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('role', sa.String(20), nullable=False, server_default='student')
    )

def downgrade() -> None:
    op.drop_column('users', 'role')
```

## Best Practices

### 1. Always Use Type Hints

```python
# ✅ GOOD - Type-safe with Mapped
class User(TenantBaseModel):
    email: Mapped[str] = mapped_column(String(255))

# ❌ BAD - Old pattern without types
class OldUser(Base):
    email = Column(String(255))
```

### 2. Use Async Everywhere

```python
# ✅ GOOD - Async operations
async def get_user(session: AsyncSession, id: UUID):
    result = await session.execute(select(User).where(User.id == id))
    return result.scalar_one_or_none()

# ❌ BAD - Sync operations (blocks event loop)
def sync_get_user(session: Session, id: UUID):
    return session.query(User).filter(User.id == id).first()
```

### 3. Use Repository Pattern

```python
# ✅ GOOD - Repository encapsulates data access
repo = UserRepository()
user = await repo.get_by_email(session, email, org_id)

# ❌ BAD - Direct queries in business logic
result = await session.execute(
    select(User).where(User.email == email)
)
user = result.scalar_one_or_none()
```

### 4. Leverage Caching

```python
# ✅ GOOD - Cache expensive queries
@cache_result(prefix="stats", expire=300)
async def get_dashboard_stats(session: AsyncSession, org_id: UUID):
    # Expensive aggregations
    return stats

# Remember to invalidate when data changes
@invalidate_cache(prefix="stats")
async def update_content(...):
    # Update logic
```

### 5. Use Transactions Properly

```python
# ✅ GOOD - Explicit transaction boundary
async with db_manager.transaction() as session:
    user = User(...)
    session.add(user)

    profile = UserProfile(user_id=user.id, ...)
    session.add(profile)
    # Auto-commit on success

# ❌ BAD - Multiple small transactions
async with db_manager.session() as session:
    user = User(...)
    session.add(user)
    await session.commit()  # First commit

    profile = UserProfile(...)
    session.add(profile)
    await session.commit()  # Second commit (inefficient)
```

## Performance

### Query Optimization

```python
# ✅ GOOD - Eager load relationships
stmt = select(User).options(
    selectinload(User.profile),
    selectinload(User.sessions)
)

# ✅ GOOD - Use indexes
class User(TenantBaseModel):
    email: Mapped[str] = mapped_column(String(255), index=True)

# ✅ GOOD - Composite indexes for common queries
__table_args__ = (
    Index('idx_user_org_status', 'organization_id', 'status'),
)
```

### Connection Pooling

The database session manager uses optimized pool settings:

- **pool_size**: 20 permanent connections
- **max_overflow**: 10 additional connections
- **pool_timeout**: 30 seconds
- **pool_recycle**: 3600 seconds (1 hour)
- **pool_pre_ping**: True (verify connections)

### Caching Strategy

- Cache expensive queries (aggregations, joins)
- Use appropriate TTL (300-600 seconds typical)
- Invalidate on updates
- Monitor cache hit rates

## Health Checks

### Database Health

```python
# Check database connectivity
is_healthy = await db_manager.health_check()
```

### Redis Health

```python
# Check Redis connectivity
is_healthy = await redis_cache.health_check()
```

## Troubleshooting

### Common Issues

1. **"No such table" error**: Run migrations with `alembic upgrade head`

2. **Connection pool exhausted**: Increase `pool_size` or check for connection leaks

3. **Slow queries**: Add indexes, use `EXPLAIN ANALYZE` to optimize

4. **Cache misses**: Check TTL settings, verify cache keys are consistent

5. **Type errors**: Ensure all models use `Mapped[Type]` annotations

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Async SQLAlchemy Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/2.0/)
- [Redis Python Client](https://redis.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Version**: 2.0.0
**Last Updated**: 2025-10-01
**Status**: ✅ Production Ready
