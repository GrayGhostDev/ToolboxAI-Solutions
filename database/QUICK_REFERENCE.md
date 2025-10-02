# Database Layer Quick Reference - SQLAlchemy 2.0

**2025 Modern Patterns** | **Async First** | **Type Safe**

## 🚀 Quick Start

### Import Everything You Need

```python
from database.session_modern import db_manager, get_async_session
from database.models.user_modern import User, UserProfile, UserRole
from database.models.content_modern import EducationalContent, ContentStatus
from database.repositories.user_repository import UserRepository
from database.repositories.base_repository import BaseRepository
from database.cache_modern import redis_cache, cache_result
```

## 📦 Common Patterns

### 1. Create a User

```python
async with db_manager.transaction() as session:
    repo = UserRepository()

    user = await repo.create_user_with_profile(
        session=session,
        organization_id=org_id,
        email="user@example.com",
        username="username",
        hashed_password=hashed_pwd,
        full_name="Full Name",
        role=UserRole.STUDENT,
        bio="Student bio",  # Profile field
        skills=["Python", "SQL"],  # Profile field
    )
```

### 2. Query Users

```python
async with db_manager.session() as session:
    repo = UserRepository()

    # Get by email
    user = await repo.get_by_email(session, "user@example.com", org_id)

    # Get active users
    users = await repo.get_active_users(
        session, org_id, role=UserRole.STUDENT, skip=0, limit=10
    )

    # Advanced filtering
    users = await repo.find(
        session,
        filters={"status": UserStatus.ACTIVE, "role": UserRole.STUDENT},
        order_by="created_at",
        descending=True,
    )
```

### 3. Update a User

```python
async with db_manager.transaction() as session:
    repo = UserRepository()

    user = await repo.update(
        session,
        user_id,
        full_name="New Name",
        status=UserStatus.ACTIVE,
    )
```

### 4. Delete (Soft)

```python
async with db_manager.transaction() as session:
    repo = BaseRepository(User)

    # Soft delete (default)
    await repo.delete(session, user_id, soft=True, deleted_by_id=admin_id)

    # Hard delete
    await repo.delete(session, user_id, soft=False)
```

### 5. Create Content

```python
async with db_manager.transaction() as session:
    repo = BaseRepository(EducationalContent)

    content = await repo.create(
        session=session,
        organization_id=org_id,
        title="Lesson Title",
        slug="lesson-title",
        content="Lesson body...",
        content_type=ContentType.LESSON,
        difficulty_level=DifficultyLevel.BEGINNER,
        author_id=user_id,
        tags=["python", "async"],
    )
```

### 6. Add Caching

```python
from database.cache_modern import cache_result, invalidate_cache

# Cache expensive queries
@cache_result(prefix="stats", expire=600)
async def get_dashboard_stats(session, org_id):
    # Expensive aggregation query
    return stats

# Invalidate cache on updates
@invalidate_cache(prefix="stats")
async def update_content(session, content_id, **data):
    # Update logic
    pass
```

## 🔧 FastAPI Integration

### Setup

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session_modern import get_async_session

app = FastAPI()
```

### Endpoint Examples

```python
@app.post("/users")
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    repo = UserRepository()

    user = await repo.create_user_with_profile(
        session=session,
        organization_id=current_org_id,
        **user_data.dict()
    )

    await session.commit()
    return user


@app.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    repo = UserRepository()
    user = await repo.get_by_id(session, user_id)

    if not user:
        raise HTTPException(404, "User not found")

    return user


@app.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    repo = UserRepository()

    user = await repo.update(
        session,
        user_id,
        **updates.dict(exclude_unset=True)
    )

    await session.commit()
    return user


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    repo = BaseRepository(User)

    deleted = await repo.delete(session, user_id, soft=True)

    await session.commit()
    return {"deleted": deleted}
```

## 🎯 Repository Cheat Sheet

### Generic Repository (All Models)

```python
repo = BaseRepository(YourModel)

# Create
instance = await repo.create(session, **data)

# Get by ID
instance = await repo.get_by_id(session, id)

# Get all (paginated)
instances = await repo.get_all(session, skip=0, limit=100)

# Update
instance = await repo.update(session, id, **updates)

# Delete
deleted = await repo.delete(session, id, soft=True)

# Restore
instance = await repo.restore(session, id)

# Find with filters
instances = await repo.find(
    session,
    filters={"field": "value"},
    order_by="created_at",
    descending=True,
    limit=10
)

# Count
count = await repo.count(session)

# Bulk create
instances = await repo.create_many(session, [data1, data2, ...])
```

### User Repository (Specialized)

```python
repo = UserRepository()

# Get by email
user = await repo.get_by_email(session, email, org_id)

# Get by username
user = await repo.get_by_username(session, username, org_id)

# Create with profile
user = await repo.create_user_with_profile(
    session, org_id, email, username, hashed_pwd, **profile_data
)

# Verify email
success = await repo.verify_email(session, user_id)

# Record login
session_obj = await repo.record_login(
    session, user_id, ip, user_agent, token_jti, expires_at
)

# Get active sessions
sessions = await repo.get_active_sessions(session, user_id)

# Invalidate sessions
count = await repo.invalidate_user_sessions(session, user_id)

# Get statistics
stats = await repo.get_user_statistics(session, org_id)
```

## 💾 Session Management

```python
# Simple session
async with db_manager.session() as session:
    result = await session.execute(select(User))

# Transaction (auto-commit/rollback)
async with db_manager.transaction() as session:
    user = User(...)
    session.add(user)
    # Auto-commits on success

# Tenant-scoped session
async with db_manager.tenant_session(org_id) as session:
    # All queries filtered by organization_id

# FastAPI dependency
@app.get("/data")
async def get_data(session: AsyncSession = Depends(get_async_session)):
    # Session automatically managed
```

## 🗄️ Redis Cache

```python
# Direct cache operations
await redis_cache.set("key", value, expire=300)
value = await redis_cache.get("key")
await redis_cache.delete("key")
await redis_cache.delete_pattern("prefix:*")

# Exists check
exists = await redis_cache.exists("key")

# Increment counter
new_value = await redis_cache.increment("counter", amount=1)

# Health check
healthy = await redis_cache.health_check()
```

## 📝 Model Definitions

### User Model

```python
from database.models.user_modern import User, UserRole, UserStatus

class User(TenantBaseModel):
    email: Mapped[str]
    username: Mapped[str]
    hashed_password: Mapped[str]
    full_name: Mapped[Optional[str]]
    role: Mapped[UserRole]
    status: Mapped[UserStatus]
    email_verified: Mapped[bool]
    # ... more fields
```

### Content Model

```python
from database.models.content_modern import EducationalContent, ContentStatus

class EducationalContent(TenantBaseModel):
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str]
    status: Mapped[ContentStatus]
    difficulty_level: Mapped[DifficultyLevel]
    tags: Mapped[List[str]]  # PostgreSQL array
    metadata: Mapped[Dict[str, Any]]  # JSONB
    # ... more fields
```

## 🧪 Testing

```python
import pytest
from database.session_modern import db_manager

@pytest.fixture
async def session():
    async with db_manager.session() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_create_user(session):
    repo = UserRepository()

    user = await repo.create(
        session,
        organization_id=org_id,
        email="test@example.com",
        username="test",
        hashed_password="$2b$12$...",
        role=UserRole.STUDENT,
    )

    assert user.id is not None
    assert user.email == "test@example.com"
```

## ⚡ Performance Tips

### 1. Use Indexes

```python
class User(TenantBaseModel):
    email: Mapped[str] = mapped_column(String(255), index=True)

    __table_args__ = (
        Index('idx_user_org_status', 'organization_id', 'status'),
    )
```

### 2. Eager Load Relationships

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(
    selectinload(User.profile),
    selectinload(User.sessions)
)
```

### 3. Cache Expensive Queries

```python
@cache_result(prefix="expensive", expire=600)
async def expensive_query(session, org_id):
    # Complex aggregations
    return results
```

### 4. Use Bulk Operations

```python
# Bulk insert
users = await repo.create_many(session, [data1, data2, data3])

# Better than individual inserts
```

## 🔒 Security Checklist

- ✅ Always use hashed passwords (never plain text)
- ✅ Validate organization_id matches current user's tenant
- ✅ Use soft delete for audit trail
- ✅ Track who created/updated records
- ✅ Implement session expiration
- ✅ Use HTTPS for all connections
- ✅ Validate all input data with Pydantic
- ✅ Use parameterized queries (SQLAlchemy does this)

## 📚 Common Queries

### Find Users by Role

```python
students = await repo.find(
    session,
    filters={"organization_id": org_id, "role": UserRole.STUDENT},
    order_by="created_at",
    descending=True
)
```

### Search Content by Tags

```python
from sqlalchemy import and_

stmt = select(EducationalContent).where(
    and_(
        EducationalContent.organization_id == org_id,
        EducationalContent.tags.contains(["python"])
    )
)
result = await session.execute(stmt)
content_list = result.scalars().all()
```

### Count Active Users

```python
count = await repo.count(
    session,
    filters={"organization_id": org_id, "status": UserStatus.ACTIVE}
)
```

## 🆘 Troubleshooting

### Connection Pool Exhausted

```python
# Check pool status
engine = db_manager.engine
print(engine.pool.status())

# Increase pool size if needed
# Edit session_modern.py pool_size/max_overflow
```

### Slow Queries

```python
# Enable SQL logging
from database.session_modern import db_manager
engine = db_manager._create_engine()  # echo=True in DEBUG mode

# Add indexes
# Use EXPLAIN ANALYZE in PostgreSQL
```

### Cache Misses

```python
# Check cache connectivity
healthy = await redis_cache.health_check()

# Verify TTL settings
# Check cache key consistency
```

---

**Quick Reference Version**: 2.0.0
**Last Updated**: 2025-10-01
**For Full Documentation**: See `database/README_MODERN.md`
