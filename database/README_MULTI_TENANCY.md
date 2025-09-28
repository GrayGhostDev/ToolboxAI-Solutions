# Multi-Tenancy Implementation Guide

## Overview

This guide documents the multi-tenancy implementation for the ToolBoxAI Educational Platform. The system uses organization-based tenancy with PostgreSQL Row Level Security (RLS) to ensure complete data isolation between tenants.

## Architecture

### Key Components

1. **Organization Model** (`database/models/tenant.py`)
   - Central tenant entity with subscription management
   - Usage tracking and billing capabilities
   - Feature flags and configuration per tenant

2. **Base Models** (`database/models/base.py`)
   - `TenantMixin` - Adds organization_id to models
   - `TenantBaseModel` - Complete base with tenant isolation
   - `TenantContext` - Context management for tenant operations

3. **RLS Policies** (`database/policies/tenant_policies.sql`)
   - Automatic tenant filtering at database level
   - Super admin bypass capabilities
   - Performance-optimized policy functions

4. **Service Layer** (`database/services/tenant_service.py`)
   - High-level business logic for tenant operations
   - Organization lifecycle management
   - User invitation and provisioning

5. **Repository Layer** (`database/repositories/tenant_repository.py`)
   - Tenant-aware CRUD operations
   - Automatic context management
   - Type-safe repository patterns

## Database Schema

### Core Tables

#### Organizations
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_tier subscription_tier DEFAULT 'free',
    status organization_status DEFAULT 'trial',
    -- Usage limits
    max_users INTEGER DEFAULT 10,
    max_classes INTEGER DEFAULT 5,
    max_storage_gb FLOAT DEFAULT 1.0,
    -- Current usage
    current_users INTEGER DEFAULT 0,
    current_classes INTEGER DEFAULT 0,
    current_storage_gb FLOAT DEFAULT 0.0,
    -- Timestamps and audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    -- ... additional fields
);
```

#### Tenant-Scoped Tables
All existing tables get an `organization_id` column:
```sql
ALTER TABLE users ADD COLUMN organization_id UUID NOT NULL
    REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE classes ADD COLUMN organization_id UUID NOT NULL
    REFERENCES organizations(id) ON DELETE CASCADE;
-- ... for all tenant-scoped tables
```

### Row Level Security

Each tenant table has RLS policies:
```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policy
CREATE POLICY users_tenant_isolation_policy ON users
FOR ALL TO public
USING (can_access_organization(organization_id))
WITH CHECK (can_access_organization(organization_id));
```

## Implementation Guide

### 1. Database Migration

Apply the multi-tenancy migration:
```bash
# Run the migration
alembic upgrade head

# Apply RLS policies
psql -d your_database -f database/policies/tenant_policies.sql
```

### 2. Application Integration

#### Setting Tenant Context
```python
from database.services.tenant_service import TenantContextService

async def set_tenant_for_request(session: AsyncSession, organization_id: UUID):
    await TenantContextService.set_tenant_context(session, organization_id)
```

#### Using Tenant-Aware Repositories
```python
from database.repositories.tenant_repository import TenantContextManager

async def get_organization_users(session: AsyncSession, organization_id: UUID):
    async with TenantContextManager(session, organization_id) as ctx:
        user_repo = ctx.get_repository(User)
        return await user_repo.get_all()
```

#### API Integration
```python
from database.examples.tenant_api_integration import TenantContextMiddleware

app = FastAPI()
app.add_middleware(TenantContextMiddleware)
```

### 3. Creating Organizations

```python
from database.services.tenant_service import TenantService

async def create_new_organization(session: AsyncSession):
    tenant_service = TenantService(session)

    org, admin_user = await tenant_service.create_organization(
        name="Acme School District",
        admin_email="admin@acme.edu",
        admin_password="secure_password_123",
        admin_first_name="Jane",
        admin_last_name="Admin",
        organization_type="education",
        subscription_tier=SubscriptionTier.EDUCATION
    )

    return org, admin_user
```

### 4. User Management

#### Inviting Users
```python
async def invite_teacher(
    session: AsyncSession,
    organization_id: UUID,
    admin_user_id: UUID
):
    tenant_service = TenantService(session)

    invitation = await tenant_service.invite_user(
        organization_id=organization_id,
        email="teacher@acme.edu",
        role=UserRole.TEACHER,
        invited_by_id=admin_user_id,
        invitation_message="Welcome to our learning platform!"
    )

    return invitation
```

#### Accepting Invitations
```python
async def accept_teacher_invitation(session: AsyncSession, token: str):
    tenant_service = TenantService(session)

    user, org = await tenant_service.accept_invitation(
        invitation_token=token,
        user_id=uuid4(),
        password="teacher_password_123",
        first_name="John",
        last_name="Teacher"
    )

    return user, org
```

## Configuration

### Subscription Tiers

Configure subscription limits in `database/config/multi_tenant_config.py`:

```python
SUBSCRIPTION_LIMITS = {
    SubscriptionTier.FREE: {
        'max_users': 5,
        'max_classes': 2,
        'max_storage_gb': 0.5,
        'features': ['basic_lessons', 'basic_quizzes']
    },
    SubscriptionTier.PROFESSIONAL: {
        'max_users': 100,
        'max_classes': 50,
        'max_storage_gb': 25.0,
        'features': ['advanced_analytics', 'custom_branding', 'sso']
    }
}
```

### Environment Variables

```bash
# Multi-tenancy configuration
ENABLE_MULTI_TENANCY=true
ENABLE_RLS=true
ENABLE_USAGE_TRACKING=true

# Trial configuration
TRIAL_DURATION_DAYS=30

# Security
TENANT_CONTEXT_REQUIRED=true
ALLOW_CROSS_TENANT_QUERIES=false
```

## Usage Patterns

### 1. Tenant Context in Middleware

```python
class TenantContextMiddleware:
    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        # Extract organization ID from subdomain, header, or JWT
        org_id = self.extract_organization_id(request)

        if org_id:
            request.state.organization_id = org_id

        await self.app(scope, receive, send)
```

### 2. Repository Pattern

```python
class UserService:
    def __init__(self, session: AsyncSession, organization_id: UUID):
        self.session = session
        self.organization_id = organization_id

    async def get_users(self) -> List[User]:
        async with TenantContextManager(self.session, self.organization_id) as ctx:
            user_repo = ctx.get_repository(User)
            return await user_repo.get_all()
```

### 3. Service Layer

```python
class ClassService:
    async def create_class(
        self,
        session: AsyncSession,
        organization_id: UUID,
        class_data: dict
    ):
        async with TenantContextManager(session, organization_id) as ctx:
            class_repo = ctx.get_repository(Class)

            # Check limits
            org_repo = ctx.get_organization_repository()
            if not await org_repo.check_limits(organization_id, 'classes'):
                raise ValueError("Class limit exceeded")

            # Create class
            new_class = await class_repo.create(**class_data)

            # Update usage
            await org_repo.update_usage(organization_id, 'classes', 1)

            return new_class
```

## Security Considerations

### 1. RLS Policy Validation

Test tenant isolation:
```sql
-- Validate RLS policies are working
SELECT * FROM validate_tenant_isolation();

-- Test with specific organizations
SELECT * FROM test_tenant_isolation(
    'org1-uuid'::UUID,
    'org2-uuid'::UUID,
    'users'
);
```

### 2. Context Validation

Always validate tenant context:
```python
async def validate_tenant_access(session: AsyncSession, organization_id: UUID):
    current_tenant = await TenantContextService.get_current_tenant(session)
    if current_tenant != organization_id:
        raise SecurityError("Tenant context mismatch")
```

### 3. Super Admin Access

For administrative operations:
```python
async def admin_operation(session: AsyncSession):
    # Set super admin context
    await session.execute(
        text("SELECT set_config('app.is_super_admin', 'true', true)")
    )

    try:
        # Perform cross-tenant operation
        result = await session.execute(select(Organization))
        return result.scalars().all()
    finally:
        # Clear super admin context
        await session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )
```

## Monitoring and Analytics

### 1. Usage Tracking

```python
async def track_daily_usage():
    """Daily cron job to track organization usage"""
    async with get_db_session() as session:
        org_repo = OrganizationRepository(session)

        # Get all active organizations
        orgs = await session.execute(
            select(Organization).where(Organization.is_active == True)
        )

        for org in orgs.scalars():
            await org_repo.log_usage(org.id, "daily")
```

### 2. Usage Reports

```python
async def generate_monthly_report(organization_id: UUID):
    async with get_db_session() as session:
        tenant_service = TenantService(session)

        report = await tenant_service.generate_usage_report(
            organization_id=organization_id,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )

        return report
```

### 3. Limit Monitoring

```python
async def check_usage_alerts():
    """Check for organizations approaching limits"""
    async with get_db_session() as session:
        tenant_service = TenantService(session)

        # Get organizations with high usage
        high_usage_orgs = await session.execute(
            select(Organization).where(
                or_(
                    Organization.current_users / Organization.max_users > 0.8,
                    Organization.current_storage_gb / Organization.max_storage_gb > 0.8
                )
            )
        )

        for org in high_usage_orgs.scalars():
            await send_usage_warning(org)
```

## Performance Optimization

### 1. Database Indexes

Critical indexes for multi-tenant performance:
```sql
-- Tenant filtering performance
CREATE INDEX CONCURRENTLY idx_users_org_active
ON users(organization_id) WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY idx_classes_org_active
ON classes(organization_id) WHERE deleted_at IS NULL;

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY idx_users_org_role_active
ON users(organization_id, role) WHERE deleted_at IS NULL AND is_active = true;
```

### 2. Query Optimization

Use EXPLAIN ANALYZE to verify RLS performance:
```sql
-- Should use organization_id index
EXPLAIN ANALYZE SELECT * FROM users WHERE organization_id = 'uuid';

-- Verify RLS policies are efficient
EXPLAIN ANALYZE SELECT * FROM users; -- with tenant context set
```

### 3. Connection Pooling

Configure separate pools for different tenant sizes:
```python
# Large tenant pool
large_tenant_pool = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30
)

# Small tenant pool
small_tenant_pool = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

## Testing

### 1. Unit Tests

Run the test suite:
```bash
pytest database/tests/test_multi_tenancy.py -v
```

### 2. Integration Tests

Test complete workflows:
```python
async def test_complete_tenant_workflow():
    # Create organization
    # Invite users
    # Test isolation
    # Upgrade subscription
    # Verify limits
```

### 3. Performance Tests

Test with realistic data volumes:
```python
async def test_tenant_performance():
    # Create 1000 organizations
    # 10,000 users per large organization
    # Verify query performance
    # Test RLS overhead
```

## Migration from Single-Tenant

### 1. Data Migration

```python
async def migrate_existing_data():
    """Migrate existing single-tenant data to multi-tenant"""

    # 1. Create default organization
    default_org = await create_default_organization()

    # 2. Update all existing records
    await session.execute(
        update(User).values(organization_id=default_org.id)
    )

    # 3. Enable RLS
    await session.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
```

### 2. Application Updates

1. Add tenant context to all request handlers
2. Update repository patterns to use tenant-aware repositories
3. Add organization management endpoints
4. Update authentication to include organization context

### 3. Gradual Rollout

1. Deploy with multi-tenancy disabled
2. Run data migration
3. Enable RLS in read-only mode
4. Test thoroughly
5. Enable full multi-tenancy

## Troubleshooting

### Common Issues

1. **RLS Policy Not Working**
   ```sql
   -- Check if RLS is enabled
   SELECT schemaname, tablename, rowlevel
   FROM pg_tables pt
   JOIN pg_class pc ON pc.relname = pt.tablename
   LEFT JOIN pg_rowlevel_policy rls ON rls.tablename = pt.tablename
   WHERE pt.tablename = 'users';
   ```

2. **Tenant Context Not Set**
   ```python
   # Always verify context before queries
   current_tenant = await TenantContextService.get_current_tenant(session)
   if not current_tenant:
       raise ValueError("Tenant context required")
   ```

3. **Performance Issues**
   ```sql
   -- Check for missing indexes
   SELECT * FROM pg_stat_user_tables WHERE relname IN ('users', 'classes');

   -- Verify RLS policy performance
   EXPLAIN ANALYZE SELECT * FROM users LIMIT 100;
   ```

### Debug Queries

```sql
-- Check current tenant context
SELECT current_setting('app.current_organization_id', true);

-- List all RLS policies
SELECT schemaname, tablename, policyname, cmd, qual
FROM pg_policies WHERE tablename = 'users';

-- Monitor RLS performance
SELECT * FROM pg_stat_user_tables WHERE relname = 'users';
```

## Best Practices

1. **Always Use Tenant Context**
   - Set context at request start
   - Validate context before operations
   - Clear context appropriately

2. **Monitor Usage Proactively**
   - Set up automated alerts
   - Track usage trends
   - Plan capacity upgrades

3. **Test Isolation Thoroughly**
   - Regular isolation tests
   - Performance benchmarks
   - Security audits

4. **Plan for Scale**
   - Monitor database performance
   - Consider sharding for very large tenants
   - Optimize queries continuously

5. **Backup and Recovery**
   - Per-tenant backup strategies
   - Test restore procedures
   - Document recovery processes

## Support

For issues with multi-tenancy implementation:

1. Check the test suite for examples
2. Review RLS policy logs
3. Validate tenant context setup
4. Monitor performance metrics
5. Consult the troubleshooting section

## Future Enhancements

Planned improvements:

1. **Automatic Scaling**
   - Dynamic resource allocation
   - Auto-scaling based on usage

2. **Enhanced Analytics**
   - Real-time usage dashboards
   - Predictive capacity planning

3. **Advanced Security**
   - Field-level encryption
   - Advanced audit logging

4. **Performance Optimization**
   - Query result caching
   - Connection pool optimization
   - Database sharding support