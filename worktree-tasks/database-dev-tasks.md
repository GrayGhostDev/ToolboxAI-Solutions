# Database Development Worktree Tasks
**Branch**: development-infrastructure-dashboard
**Ports**: Backend(8016), Dashboard(5187), MCP(9884), Coordinator(8895)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` before writing ANY code!

**Requirements**:
- ✅ PostgreSQL 16+ with modern features
- ✅ SQLAlchemy 2.0 with async patterns
- ✅ Alembic for migrations
- ✅ Python 3.12 with type hints
- ✅ Pydantic v2 for validation
- ✅ Redis 7+ for caching
- ✅ Auto-accept enabled for corrections
- ❌ NO sync-only database code or old SQLAlchemy 1.x patterns

## Primary Objectives

### 1. **Modern Database Architecture (SQLAlchemy 2.0)**
   - Implement async database sessions
   - Use declarative base with Mapped columns
   - Design normalized schema
   - Implement proper indexing strategy
   - Add full-text search capabilities

### 2. **Migration Management**
   - Setup Alembic with async support
   - Create version control for schema changes
   - Implement rollback strategies
   - Document migration procedures
   - Add data migration scripts

### 3. **Performance Optimization**
   - Query optimization and analysis
   - Implement connection pooling
   - Add query result caching with Redis
   - Create database indexes
   - Setup query logging and monitoring

### 4. **Data Integrity & Security**
   - Implement row-level security
   - Add audit logging
   - Encrypt sensitive data
   - Implement soft deletes
   - Add data validation layers

## Current Tasks

### Phase 1: Database Schema Design (Priority: HIGH)
- [ ] Review existing models in `database/models.py`
- [ ] Analyze current schema and relationships
- [ ] Design improved schema with normalization
- [ ] Create ERD (Entity Relationship Diagram)
- [ ] Document table relationships
- [ ] Plan indexing strategy
- [ ] Design partition strategy for large tables

### Phase 2: SQLAlchemy 2.0 Migration (Priority: HIGH)
- [ ] Update all models to use `Mapped` type annotations
- [ ] Replace `Column()` with `mapped_column()`
- [ ] Implement async session management
- [ ] Update query patterns to use `select()`
- [ ] Add relationship configurations
- [ ] Implement proper type hints
- [ ] Create base model with common fields:
  ```python
  class BaseModel:
      id: Mapped[int] = mapped_column(primary_key=True)
      created_at: Mapped[datetime] = mapped_column(server_default=func.now())
      updated_at: Mapped[datetime] = mapped_column(onupdate=func.now())
      is_deleted: Mapped[bool] = mapped_column(default=False)
  ```

### Phase 3: Core Models Implementation (Priority: HIGH)

#### User Management
- [ ] Create User model with modern patterns
- [ ] Implement UserProfile with one-to-one relationship
- [ ] Add UserRole and Permission models
- [ ] Create UserSession for tracking
- [ ] Implement email verification system
- [ ] Add password reset tokens
- [ ] Create audit log for user actions

#### Content Management
- [ ] Design EducationalContent model
- [ ] Create ContentCategory with hierarchy
- [ ] Implement ContentTag with many-to-many
- [ ] Add ContentVersion for revision history
- [ ] Create ContentAttachment model
- [ ] Implement ContentComment and Rating
- [ ] Add content workflow states

#### Analytics & Metrics
- [ ] Create UserActivity tracking
- [ ] Implement PageView analytics
- [ ] Add PerformanceMetric model
- [ ] Create DashboardMetric aggregations
- [ ] Implement EventLog for system events
- [ ] Add custom metric definitions

### Phase 4: Advanced Features (Priority: MEDIUM)
- [ ] Implement full-text search with PostgreSQL:
  ```python
  from sqlalchemy import Index
  from sqlalchemy.dialects.postgresql import TSVECTOR

  class Article(Base):
      __tablename__ = "articles"

      search_vector: Mapped[TSVECTOR] = mapped_column(
          TSVECTOR,
          Computed("to_tsvector('english', title || ' ' || content)")
      )

      __table_args__ = (
          Index('idx_article_search', 'search_vector', postgresql_using='gin'),
      )
  ```

- [ ] Add JSONB columns for flexible data
- [ ] Implement array columns where appropriate
- [ ] Create composite types for complex data
- [ ] Add generated columns for computed values
- [ ] Implement range types for dates/numbers

### Phase 5: Migrations (Priority: HIGH)
- [ ] Setup Alembic with async configuration
- [ ] Create initial migration from current schema
- [ ] Implement migration templates
- [ ] Add data migration utilities
- [ ] Create rollback procedures
- [ ] Document migration process
- [ ] Add migration testing scripts

### Phase 6: Performance Optimization (Priority: HIGH)
- [ ] Analyze slow queries with EXPLAIN
- [ ] Create indexes for frequent queries:
  - Primary keys (auto)
  - Foreign keys
  - Search fields
  - Sort/filter columns
  - Composite indexes for multi-column queries
- [ ] Implement query result caching with Redis
- [ ] Add connection pooling configuration
- [ ] Setup read replicas for scaling
- [ ] Implement database partitioning
- [ ] Add query timeout limits

### Phase 7: Caching Layer (Priority: MEDIUM)
- [ ] Setup Redis 7 connection with async support
- [ ] Implement cache decorators for models
- [ ] Create cache invalidation strategies
- [ ] Add cache warming for common queries
- [ ] Implement distributed locking
- [ ] Setup pub/sub for cache updates
- [ ] Add cache monitoring and metrics

### Phase 8: Data Services (Priority: MEDIUM)
- [ ] Create repository pattern for data access
- [ ] Implement service layer for business logic
- [ ] Add transaction management utilities
- [ ] Create bulk operation helpers
- [ ] Implement data import/export services
- [ ] Add data validation services
- [ ] Create database health check endpoints

### Phase 9: Testing (Priority: HIGH)
- [ ] Setup test database with fixtures
- [ ] Create factory patterns for test data
- [ ] Write model tests with pytest-asyncio
- [ ] Add migration tests
- [ ] Test constraint violations
- [ ] Implement integration tests
- [ ] Add performance benchmarks

### Phase 10: Security & Compliance (Priority: HIGH)
- [ ] Implement row-level security (RLS)
- [ ] Add audit logging for all changes
- [ ] Encrypt sensitive columns
- [ ] Implement data retention policies
- [ ] Add GDPR compliance features
- [ ] Create data anonymization tools
- [ ] Implement backup/restore procedures

## File Locations

### Database Files
- **Models**: `database/models/`
  - `user.py` - User and auth models
  - `content.py` - Content models
  - `analytics.py` - Analytics models
  - `base.py` - Base model classes
- **Migrations**: `database/migrations/versions/`
- **Services**: `database/services/`
- **Repositories**: `database/repositories/`
- **Utils**: `database/utils/`

### Configuration
- `database/connection.py` - Database connection setup
- `database/session.py` - Session management
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment

## Technology Stack (2025)

### Core Database
```python
dependencies = {
    "sqlalchemy": "^2.0.35",
    "asyncpg": "^0.30.0",          # Async PostgreSQL driver
    "alembic": "^1.14.0",          # Migrations
    "redis": "^5.2.0",             # Caching
    "psycopg2-binary": "^2.9.9",   # PostgreSQL adapter
}
```

### Validation & Types
```python
dependencies = {
    "pydantic": "^2.10.0",
    "pydantic-settings": "^2.7.0",
    "python-dotenv": "^1.0.0",
}
```

### Testing
```python
dev_dependencies = {
    "pytest-asyncio": "^0.24.0",
    "pytest-postgresql": "^6.1.0",
    "factory-boy": "^3.3.0",
    "faker": "^30.8.0",
}
```

## Modern SQLAlchemy 2.0 Patterns

### Model Definition
```python
# ✅ CORRECT - SQLAlchemy 2.0 with type annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    # Primary key with auto-increment
    id: Mapped[int] = mapped_column(primary_key=True)

    # Required fields
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    # Optional fields
    full_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Boolean with default
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps with server defaults
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    profile: Mapped["UserProfile"] = relationship(back_populates="user")
    posts: Mapped[List["Post"]] = relationship(back_populates="author")

# ❌ WRONG - Old SQLAlchemy 1.x pattern
class OldUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)  # DO NOT USE
    email = Column(String(255))              # DO NOT USE
```

### Async Session Usage
```python
# ✅ CORRECT - Async session with SQLAlchemy 2.0
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select

# Engine setup
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=True,
    pool_size=20,
    max_overflow=10
)

# Query patterns
async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_active_users(session: AsyncSession) -> List[User]:
    stmt = select(User).where(User.is_active == True).order_by(User.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

# Transaction management
async def create_user_with_profile(session: AsyncSession, user_data: dict) -> User:
    async with session.begin():
        user = User(**user_data)
        session.add(user)
        await session.flush()  # Get user.id

        profile = UserProfile(user_id=user.id)
        session.add(profile)

        await session.commit()
        return user
```

### Relationships
```python
# ✅ CORRECT - Modern relationship patterns
from sqlalchemy.orm import relationship, Mapped

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # One-to-One
    profile: Mapped["UserProfile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # One-to-Many
    posts: Mapped[List["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan"
    )

    # Many-to-Many
    roles: Mapped[List["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users"
    )

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    user: Mapped["User"] = relationship(back_populates="profile")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="posts")
```

### Migration Example
```python
# ✅ CORRECT - Alembic migration with async
"""add user profile table

Revision ID: abc123
Revises: xyz789
Create Date: 2025-10-01 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'])

def downgrade() -> None:
    op.drop_index('idx_user_profiles_user_id')
    op.drop_table('user_profiles')
```

### Redis Caching
```python
# ✅ CORRECT - Modern Redis caching
from redis.asyncio import Redis
from functools import wraps
import json

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

def cache_result(expire: int = 300):
    """Cache decorator for async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache first
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await redis_client.setex(
                cache_key,
                expire,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

@cache_result(expire=600)
async def get_user_stats(user_id: int) -> dict:
    # Expensive query
    return stats
```

## Commands

### Database Management
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Upgrade database
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history

# SQL generation (don't apply)
alembic upgrade head --sql
```

### Development
```bash
# Start PostgreSQL (Docker)
docker compose up -d postgres

# Start Redis (Docker)
docker compose up -d redis

# Connect to database
psql postgresql://user:pass@localhost/db

# Database shell
python -m database.shell

# Run seeds
python -m database.seeds
```

### Testing
```bash
# Run database tests
pytest tests/database/ -v

# Test migrations
pytest tests/database/test_migrations.py

# Performance benchmarks
pytest tests/database/benchmarks.py --benchmark-only
```

## Performance Targets

- **Query Response**: < 100ms for simple queries
- **Complex Queries**: < 500ms with proper indexes
- **Connection Pool**: 20-50 connections
- **Cache Hit Rate**: > 80% for common queries
- **Migration Time**: < 5 minutes for schema changes
- **Backup Time**: < 30 minutes for full backup

## Success Metrics

- ✅ All models migrated to SQLAlchemy 2.0
- ✅ 100% async database operations
- ✅ All queries under 500ms with indexes
- ✅ > 80% cache hit rate for common queries
- ✅ Zero N+1 query problems
- ✅ Full migration rollback capability
- ✅ Comprehensive test coverage (>90%)
- ✅ Database health monitoring active

---

**REMEMBER**: Use ONLY SQLAlchemy 2.0 patterns. Auto-accept is enabled. Async operations only!
