# Multi-Tenancy Architecture Documentation

> **Version**: 1.0.0
> **Last Updated**: 2025-01-27
> **Status**: Implementation Complete ✅

## Table of Contents
1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Implementation Details](#implementation-details)
4. [Database Layer](#database-layer)
5. [API Layer](#api-layer)
6. [Security](#security)
7. [Usage Guide](#usage-guide)
8. [Testing](#testing)
9. [Performance Considerations](#performance-considerations)
10. [Migration Guide](#migration-guide)

## Overview

The ToolBoxAI Educational Platform implements a comprehensive multi-tenancy architecture using PostgreSQL Row-Level Security (RLS) combined with application-level tenant isolation. This approach provides data isolation, security, and scalability for supporting multiple educational organizations on a single platform instance.

### Key Features
- **Complete Data Isolation**: Organization data is completely isolated using database-level RLS
- **Subscription Management**: Tiered subscriptions (Free, Basic, Professional, Enterprise, Education)
- **Usage Tracking**: Real-time monitoring of resource usage per organization
- **Compliance Ready**: COPPA/FERPA compliance fields and audit logging
- **Performance Optimized**: Efficient queries with proper indexing and caching

### Technology Stack
- **Database**: PostgreSQL 15+ with Supabase (self-hosted or cloud)
- **Row-Level Security**: Native PostgreSQL RLS policies
- **ORM**: SQLAlchemy 2.0 with async support
- **Framework**: FastAPI with async request handling
- **Caching**: Redis with tenant namespacing (self-hosted)
- **Authentication**: JWT with organization context
- **File Storage**: Supabase Storage (no AWS S3 dependency)
- **Monitoring**: Prometheus + Grafana (self-hosted)
- **Background Jobs**: Celery + Redis (no AWS SQS/Lambda)

## Architecture Design

### Tenant Isolation Strategy

```
┌─────────────────────────────────────────────────┐
│                 API Request                      │
│                     ↓                            │
│            JWT Token Validation                  │
│                     ↓                            │
│           Tenant Middleware Layer                │
│         (Extract organization_id)                │
│                     ↓                            │
│            Set Tenant Context                    │
│              (ContextVar)                        │
│                     ↓                            │
│         Business Logic Layer                     │
│        (Tenant-aware operations)                 │
│                     ↓                            │
│          Database Access Layer                   │
│         (Auto-filtered by RLS)                   │
│                     ↓                            │
│      PostgreSQL with Row-Level Security          │
└─────────────────────────────────────────────────┘
```

### Data Model Hierarchy

```
Organization (Tenant Root)
    ├── Users (Members)
    ├── Classes
    │   └── Enrollments
    ├── Courses
    │   └── Lessons
    │       └── Content
    ├── Assessments
    │   └── Quiz Attempts
    ├── Roblox Environments
    └── File Storage
```

## Implementation Details

### Database Models

#### Organization Model
Located in `database/models/tenant.py`:

```python
class Organization(TenantBaseModel):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    max_users = Column(Integer, default=10)
    max_classes = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=1)
    max_api_calls_per_month = Column(Integer, default=10000)

    # Compliance fields
    coppa_compliant = Column(Boolean, default=False)
    ferpa_compliant = Column(Boolean, default=False)

    # Relationships
    users = relationship("User", back_populates="organization")
    invitations = relationship("OrganizationInvitation", back_populates="organization")
```

#### TenantMixin
All tenant-scoped models inherit from `TenantMixin`:

```python
class TenantMixin:
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
```

### Row-Level Security Policies

Located in `database/policies/tenant_policies.sql`:

```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policy
CREATE POLICY tenant_isolation ON users
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::uuid);
```

### Middleware Implementation

Located in `apps/backend/middleware/tenant.py`:

```python
class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract organization_id from JWT
        organization_id = await self.extract_organization_id(request)

        # Set tenant context
        tenant_context_var.set(organization_id)

        # Set database session variable
        if organization_id:
            request.state.organization_id = organization_id

        # Process request
        response = await call_next(request)
        return response
```

## API Layer

### Organization Management Endpoints

Located in `apps/backend/api/v1/endpoints/organizations.py`:

#### Create Organization
```http
POST /api/v1/organizations
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "Example School",
    "subscription_tier": "education",
    "admin_email": "admin@example.edu",
    "settings": {
        "timezone": "America/New_York",
        "academic_year_start": "2025-08-01"
    }
}
```

#### Get Current Organization
```http
GET /api/v1/organizations/current
Authorization: Bearer {token}
```

#### Invite User
```http
POST /api/v1/organizations/{org_id}/invitations
Content-Type: application/json
Authorization: Bearer {token}

{
    "email": "teacher@example.edu",
    "role": "teacher",
    "expires_in_days": 7
}
```

### Tenant Context in Endpoints

All endpoints automatically filter data by organization:

```python
@router.get("/classes")
async def list_classes(
    db: AsyncSession = Depends(get_tenant_db_session),
    current_org = Depends(get_current_organization)
):
    # Query automatically filtered by organization_id
    result = await db.execute(
        select(Class).where(Class.organization_id == current_org.id)
    )
    return result.scalars().all()
```

## Security

### Tenant Boundary Enforcement
- All database queries are automatically filtered by organization_id
- Cross-tenant data access is prevented at the database level
- API middleware validates organization membership

### Super Admin Access
Super admins can access any organization by setting a header:
```http
X-Organization-ID: {target_org_id}
X-Super-Admin-Token: {admin_token}
```

### Audit Logging
All tenant operations are logged:
```python
class OrganizationAuditLog(BaseModel):
    organization_id: UUID
    user_id: UUID
    action: str
    resource_type: str
    resource_id: UUID
    details: dict
    timestamp: datetime
```

## Usage Guide

### Creating a New Organization

```python
from database.services.tenant_service import TenantService

# Create organization with admin user
org_data = await TenantService.create_organization_with_admin(
    name="Example School District",
    admin_email="admin@district.edu",
    subscription_tier=SubscriptionTier.EDUCATION,
    settings={
        "timezone": "America/Chicago",
        "features": ["advanced_analytics", "api_access"]
    }
)
```

### Switching Organizations (Frontend)

```typescript
// Dashboard component for organization switching
const OrganizationSwitcher = () => {
    const switchOrganization = async (orgId: string) => {
        await api.post('/api/v1/auth/switch-organization', {
            organization_id: orgId
        });
        // Refresh token with new organization context
        await refreshAuth();
    };
};
```

### Tenant-Aware Queries

```python
# Repository pattern with automatic tenant filtering
from database.repositories.tenant_repository import TenantRepository

class ClassRepository(TenantRepository[Class]):
    async def get_by_teacher(self, teacher_id: UUID) -> List[Class]:
        # Automatically filtered by current organization
        return await self.query(
            Class.teacher_id == teacher_id
        ).all()
```

## Testing

### Unit Tests
Located in `database/tests/test_multi_tenancy.py`:

```python
async def test_tenant_isolation():
    # Create two organizations
    org1 = await create_test_organization("Org 1")
    org2 = await create_test_organization("Org 2")

    # Set context to org1
    tenant_context_var.set(org1.id)

    # Create data in org1
    class1 = await create_class("Math 101")

    # Switch to org2
    tenant_context_var.set(org2.id)

    # Verify org2 cannot see org1 data
    classes = await list_classes()
    assert len(classes) == 0
```

### Integration Tests
```bash
# Run multi-tenancy tests
pytest database/tests/test_multi_tenancy.py -v

# Test with different scenarios
pytest -k "tenant_isolation" -v
pytest -k "subscription_limits" -v
```

## Performance Considerations

### Indexing Strategy
```sql
-- Critical indexes for tenant queries
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_classes_organization_id ON classes(organization_id);
CREATE INDEX idx_content_organization_id ON content(organization_id);

-- Composite indexes for common queries
CREATE INDEX idx_classes_org_teacher ON classes(organization_id, teacher_id);
CREATE INDEX idx_enrollments_org_student ON enrollments(organization_id, student_id);
```

### Caching Strategy
```python
# Redis key namespacing by tenant
def get_cache_key(organization_id: UUID, key: str) -> str:
    return f"org:{organization_id}:{key}"

# Cache organization settings
async def get_organization_settings(org_id: UUID):
    cache_key = get_cache_key(org_id, "settings")
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    # Fetch from database if not cached
```

### Query Optimization
- Use SELECT with specific columns instead of SELECT *
- Implement pagination for large datasets
- Use database views for complex tenant queries
- Consider read replicas for reporting queries

## Migration Guide

### For Existing Single-Tenant Systems

1. **Backup Current Data**
   ```bash
   pg_dump educational_platform_dev > backup_before_multitenancy.sql
   ```

2. **Create Default Organization**
   ```python
   # Migration script
   default_org = Organization(
       name="Default Organization",
       subscription_tier=SubscriptionTier.ENTERPRISE
   )
   db.add(default_org)
   await db.commit()
   ```

3. **Update Existing Records**
   ```sql
   -- Add organization_id to existing records
   UPDATE users SET organization_id = (SELECT id FROM organizations LIMIT 1);
   UPDATE classes SET organization_id = (SELECT id FROM organizations LIMIT 1);
   ```

4. **Apply RLS Policies**
   ```bash
   psql educational_platform_dev < database/policies/tenant_policies.sql
   ```

5. **Update Application Code**
   - Add middleware to FastAPI app
   - Update JWT tokens to include organization_id
   - Modify queries to be tenant-aware

### Rollback Procedure
```sql
-- Disable RLS
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE classes DISABLE ROW LEVEL SECURITY;

-- Remove organization_id columns (if needed)
ALTER TABLE users DROP COLUMN organization_id;
ALTER TABLE classes DROP COLUMN organization_id;

-- Drop organizations table
DROP TABLE organizations CASCADE;
```

## Best Practices

### Do's ✅
- Always validate organization membership before operations
- Use database transactions for multi-table updates
- Implement proper error handling for tenant operations
- Cache frequently accessed organization data
- Monitor usage against subscription limits

### Don'ts ❌
- Never bypass RLS policies in production
- Don't store organization_id in frontend localStorage
- Avoid cross-tenant joins in queries
- Don't hardcode organization IDs
- Never share cache keys between tenants

## Troubleshooting

### Common Issues

#### Issue: Users can't access their data
```python
# Check tenant context is set
print(f"Current org: {tenant_context_var.get()}")

# Verify user belongs to organization
user_org = await db.execute(
    select(User.organization_id).where(User.id == user_id)
)
```

#### Issue: RLS policies not working
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';

-- View existing policies
SELECT * FROM pg_policies WHERE tablename = 'users';
```

#### Issue: Performance degradation
```sql
-- Check query plans
EXPLAIN ANALYZE SELECT * FROM classes WHERE organization_id = '...';

-- Update statistics
ANALYZE classes;
```

## Supabase Integration

### Supabase-Specific Configuration

The platform leverages Supabase for enhanced PostgreSQL capabilities without vendor lock-in:

```python
# From toolboxai_settings/settings.py
SUPABASE_ENABLE_RLS = True  # Enable Row-Level Security
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
```

### Storage Configuration

Instead of AWS S3, we use Supabase Storage:
```python
# Bucket configuration per tenant
storage_client = supabase.storage
bucket_name = f"org-{organization_id}"

# Create tenant bucket with RLS
await storage_client.create_bucket(
    bucket_name,
    public=False,
    file_size_limit=100_000_000,  # 100MB
    allowed_mime_types=["image/*", "application/pdf", "video/*"]
)
```

### Self-Hosted Alternative

For complete infrastructure independence:
```yaml
# docker-compose.yml for self-hosted Supabase
services:
  postgres:
    image: supabase/postgres:15.1.0.117
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  storage:
    image: supabase/storage-api:v0.43.11
    depends_on:
      - postgres
```

## Infrastructure Independence

### No Cloud Provider Lock-in

The architecture is designed to work with:
- **Self-hosted infrastructure**: Full control with Docker/Kubernetes
- **Supabase Cloud**: Managed PostgreSQL + Storage
- **Any PostgreSQL provider**: Digital Ocean, Render, Railway, etc.
- **On-premises**: Complete on-premises deployment supported

### Alternative Deployments

#### Docker Compose (Self-Hosted)
```yaml
services:
  postgres:
    image: postgres:15-alpine
    volumes:
      - ./database/policies/tenant_policies.sql:/docker-entrypoint-initdb.d/policies.sql

  redis:
    image: redis:7-alpine

  backend:
    build: ./apps/backend
    environment:
      DATABASE_URL: postgresql://user:pass@postgres/db
      REDIS_URL: redis://redis:6379
```

#### Kubernetes (Self-Managed)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tenant-config
data:
  enable_rls: "true"
  max_orgs_per_cluster: "1000"
```

## Support Resources

- **Database Documentation**: [PostgreSQL RLS Guide](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- **Supabase Documentation**: [Supabase RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- **FastAPI Middleware**: [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/tutorial/middleware/)
- **SQLAlchemy Async**: [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- **Self-Hosting Guide**: [Supabase Self-Hosting](https://supabase.com/docs/guides/self-hosting)
- **Internal Support**: Contact the platform team for multi-tenancy questions

## Version History

- **v1.0.0** (2025-01-27): Initial implementation with RLS and middleware
- **Future v1.1.0**: Add schema-per-tenant option for enterprise clients
- **Future v1.2.0**: Implement tenant data export/import tools