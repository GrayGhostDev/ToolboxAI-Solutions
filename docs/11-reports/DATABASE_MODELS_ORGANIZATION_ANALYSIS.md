# Database Models Organization Analysis
## Phase 1, Task 1.3: Organization Column Integration

**Date:** 2025-10-10
**Purpose:** Identify which models need organization_id for multi-tenant isolation
**Status:** Analysis Complete - Migration Required

---

## Executive Summary

**Current State:**
- ✅ **6 models** already have organization_id via TenantBaseModel
- ❌ **70+ models** missing organization_id (multi-tenant isolation BROKEN)
- 🔴 **CRITICAL SECURITY GAP**: Agent, Roblox, Payment, and Legacy models lack tenant isolation

**Required Action:**
- Add organization_id to 70+ models across 5 model files
- Generate Alembic migration for schema changes
- Update all queries to enforce organization filtering
- Deploy RLS policies from Task 1.2

---

## Models WITH Organization ID ✅

### File: `database/models/storage.py` (3 models)
Already using TenantBaseModel - **NO CHANGES NEEDED**

1. **File** (line 80)
   - Inherits: `TenantBaseModel, TimestampMixin, AuditMixin`
   - Has: `organization_id` via TenantMixin
   - Status: ✅ Complete

2. **FileVersion** (line 178)
   - Inherits: `TenantBaseModel, TimestampMixin`
   - Has: `organization_id` via TenantMixin
   - Status: ✅ Complete

3. **FileShare** (line 205)
   - Inherits: `TenantBaseModel, TimestampMixin`
   - Has: `organization_id` via TenantMixin
   - Status: ✅ Complete

### File: `database/models/user_modern.py` (3 models)
Already using TenantBaseModel - **NO CHANGES NEEDED**

4. **User** (line 41)
   - Inherits: `TenantBaseModel`
   - Has: `organization_id` via TenantMixin
   - Status: ✅ Complete

5. **UserProfile** (line 236)
   - Inherits: `TenantBaseModel`
   - Has: `organization_id` via TenantMixin
   - Status: ✅ Complete

6. **UserSession** (line 305)
   - Inherits: `TenantBaseModel`
   - Has: `organization_id` via TenantMixin
   - Status: ✅ Complete

### File: `database/models/content_modern.py` (4+ models)
Already using TenantBaseModel - **NO CHANGES NEEDED**

7. **EducationalContent** (line 64)
   - Inherits: `TenantBaseModel`
   - Status: ✅ Complete

8. **ContentAttachment** (line 323)
   - Inherits: `TenantBaseModel`
   - Status: ✅ Complete

9. **ContentComment** (line 400)
   - Inherits: `TenantBaseModel`
   - Status: ✅ Complete

10. **ContentRating** (line 475)
    - Inherits: `TenantBaseModel`
    - Status: ✅ Complete

---

## Models MISSING Organization ID ❌

### Critical Security Gap: 70+ Models Without Tenant Isolation

### File: `database/models/agent_models.py` (6 models)
**Status:** 🔴 CRITICAL - No tenant isolation for agent system

1. **AgentInstance** (line 82)
   - Inherits: `Base` (OLD BASE - NOT TENANT AWARE)
   - Missing: `organization_id`
   - Impact: Agents can access data across all organizations
   - **Action Required:** Add organization_id column

2. **AgentExecution** (line 137)
   - Inherits: `Base`
   - Missing: `organization_id`
   - Impact: Task executions not isolated by tenant
   - **Action Required:** Add organization_id column

3. **AgentMetrics** (line 221)
   - Inherits: `Base`
   - Missing: `organization_id`
   - Impact: Metrics visible across all tenants
   - **Action Required:** Add organization_id column

4. **AgentTaskQueue** (line 299)
   - Inherits: `Base`
   - Missing: `organization_id`
   - Impact: Task queue not tenant-scoped
   - **Action Required:** Add organization_id column

5. **SystemHealth** (line 374)
   - Inherits: `Base`
   - Missing: `organization_id`
   - Decision: **KEEP GLOBAL** - System-wide health monitoring
   - No changes needed

6. **AgentConfiguration** (line 447)
   - Inherits: `Base`
   - Missing: `organization_id`
   - Impact: Agent configs not tenant-scoped
   - **Action Required:** Add organization_id column

**Agent Models Summary:**
- **5 models** need organization_id
- **1 model** remains global (SystemHealth)

---

### File: `database/models/roblox_models.py` (4 models)
**Status:** 🔴 CRITICAL - No tenant isolation for Roblox environments

1. **RobloxEnvironment** (line 37)
   - Inherits: `Base` (OLD BASE)
   - Has: `user_id` only (NOT organization_id)
   - Impact: Environments not scoped to organizations
   - **Action Required:** Add organization_id column + index

2. **RobloxSession** (line 130)
   - Inherits: `Base`
   - Has: `user_id`, `environment_id` only
   - Impact: Sessions not tenant-isolated
   - **Action Required:** Add organization_id column

3. **EnvironmentShare** (line 173)
   - Inherits: `Base`
   - Has: `environment_id`, `user_id` only
   - Impact: Sharing permissions not tenant-scoped
   - **Action Required:** Add organization_id column

4. **EnvironmentTemplate** (line 209)
   - Inherits: `Base`
   - Has: `created_by_user_id` only
   - Impact: Templates not organization-scoped
   - **Action Required:** Add organization_id column

**Roblox Models Summary:**
- **4 models** need organization_id
- All models CRITICAL for multi-tenant security

---

### File: `database/models/payment.py` (10 models)
**Status:** 🔴 CRITICAL - Payment data not tenant-isolated

1. **Customer** (line 71)
   - Inherits: `Base`
   - Has: `user_id` only
   - Impact: Customer records not organization-scoped
   - **Action Required:** Add organization_id column

2. **Subscription** (line 113)
   - Inherits: `Base`
   - Has: `customer_id` only
   - Impact: Subscriptions not tenant-isolated
   - **Action Required:** Add organization_id column

3. **SubscriptionItem** (line 171)
   - Inherits: `Base`
   - Has: `subscription_id` only
   - **Action Required:** Add organization_id column

4. **CustomerPaymentMethod** (line 198)
   - Inherits: `Base`
   - Has: `customer_id` only
   - **Action Required:** Add organization_id column

5. **Payment** (line 247)
   - Inherits: `Base`
   - Has: `customer_id` only
   - Impact: Payment transactions not tenant-scoped
   - **Action Required:** Add organization_id column

6. **Invoice** (line 316)
   - Inherits: `Base`
   - Has: `customer_id` only
   - **Action Required:** Add organization_id column

7. **InvoiceItem** (line 387)
   - Inherits: `Base`
   - Has: `invoice_id` only
   - **Action Required:** Add organization_id column

8. **Refund** (line 422)
   - Inherits: `Base`
   - Has: `payment_id` only
   - **Action Required:** Add organization_id column

9. **UsageRecord** (line 455)
   - Inherits: `Base`
   - Has: `subscription_item_id` only
   - **Action Required:** Add organization_id column

10. **Coupon** (line 482)
    - Inherits: `Base`
    - Decision: **KEEP GLOBAL** or add organization_id
    - Consider: Platform-wide vs org-specific coupons
    - **Recommendation:** Add organization_id with nullable=True

**Payment Models Summary:**
- **9-10 models** need organization_id
- CRITICAL for financial data security

---

### File: `database/models/models.py` (37+ models)
**Status:** 🔴 LEGACY MODELS - Complete overhaul needed

#### Educational Models (13 models)
1. **User** (line 103) - Migrate to user_modern.py User model
2. **Course** (line 165) - Add organization_id
3. **Lesson** (line 202) - Add organization_id
4. **Content** (line 252) - Migrate to content_modern.py
5. **Quiz** (line 292) - Add organization_id
6. **QuizQuestion** (line 333) - Add organization_id
7. **QuizAttempt** (line 370) - Add organization_id
8. **QuizResponse** (line 402) - Add organization_id
9. **UserProgress** (line 429) - Add organization_id
10. **Analytics** (line 462) - Add organization_id
11. **Achievement** (line 496) - Add organization_id
12. **UserAchievement** (line 528) - Add organization_id
13. **Leaderboard** (line 555) - Add organization_id

#### Platform Models (3 models)
14. **Enrollment** (line 596) - Add organization_id
15. **Session** (line 630) - Add organization_id
16. **Class** (line 1231) - Add organization_id
17. **ClassEnrollment** (line 1265) - Add organization_id

#### Roblox Legacy Models (12 models)
18. **RobloxSession** (line 669) - Migrate to roblox_models.py
19. **RobloxContent** (line 734) - Add organization_id
20. **RobloxPlayerProgress** (line 795) - Add organization_id
21. **RobloxQuizResult** (line 868) - Add organization_id
22. **RobloxAchievement** (line 945) - Add organization_id
23. **RobloxTemplate** (line 1005) - Migrate to roblox_models.py
24. **RobloxDeployment** (line 1315) - Add organization_id
25. **PluginRequest** (line 1301) - Add organization_id
26. **TerrainTemplate** (line 1329) - Add organization_id
27. **QuizTemplate** (line 1343) - Add organization_id
28. **StudentProgress** (line 1096) - Add organization_id

#### System Models (5 models)
29. **SchemaDefinition** (line 1128) - KEEP GLOBAL
30. **SchemaMapping** (line 1154) - KEEP GLOBAL
31. **AgentHealthStatus** (line 1177) - KEEP GLOBAL (migrate to agent_models.py)
32. **IntegrationEvent** (line 1201) - Add organization_id
33. **EnhancedContentGeneration** (line 1362) - Add organization_id
34. **ContentGenerationBatch** (line 1394) - Add organization_id

**Legacy Models Summary:**
- **30+ models** need organization_id
- **4 models** should remain global
- **Several duplicates** to consolidate with modern models

---

### File: `database/models/content_pipeline_models.py` (7 models)
**Status:** 🟡 MODERATE - Content pipeline needs tenant isolation

1. **EnhancedContentGeneration** (line 17)
   - Inherits: `Base`
   - Has: `user_id` only
   - **Action Required:** Add organization_id

2. **ContentQualityMetrics** (line 73)
   - Inherits: `Base`
   - Has: `content_id` only
   - **Action Required:** Add organization_id

3. **LearningProfile** (line 121)
   - Inherits: `Base`
   - Has: `user_id` only
   - **Action Required:** Add organization_id

4. **ContentPersonalizationLog** (line 164)
   - Inherits: `Base`
   - Has: `user_id`, `content_id`
   - **Action Required:** Add organization_id

5. **ContentFeedback** (line 198)
   - Inherits: `Base`
   - Has: `content_id`, `user_id`
   - **Action Required:** Add organization_id

6. **ContentGenerationBatch** (line 239)
   - Inherits: `Base`
   - Has: `user_id` only
   - **Action Required:** Add organization_id

7. **ContentCache** (line 271)
   - Inherits: `Base`
   - Decision: **KEEP GLOBAL** - System-wide cache
   - No changes needed

**Content Pipeline Summary:**
- **6 models** need organization_id
- **1 model** remains global (ContentCache)

---

### File: `database/models/tenant.py` (3 models)
**Status:** ✅ CORRECT - Organization models should NOT have organization_id

1. **Organization** (line 42)
   - Inherits: `Base`
   - Purpose: Defines organizations themselves
   - **No changes needed** - Correct design

2. **OrganizationInvitation** (line 269)
   - Inherits: `Base`
   - Has: `organization_id` already (explicit column, not via mixin)
   - **No changes needed** - Already has org reference

3. **OrganizationUsageLog** (line 326)
   - Inherits: `Base`
   - Has: `organization_id` already (explicit column)
   - **No changes needed** - Already has org reference

---

## Migration Strategy

### Approach 1: Convert to TenantBaseModel (RECOMMENDED)
**Pros:**
- Automatic organization_id, timestamps, audit fields, soft delete
- Consistent with modern models
- Reduces code duplication

**Cons:**
- Larger schema change (adds 8+ columns per table)
- More complex migration

**Models to Convert:**
- All agent_models.py models (except SystemHealth)
- All roblox_models.py models
- All payment.py models
- All content_pipeline_models.py models (except ContentCache)
- Select legacy models.py models

### Approach 2: Add organization_id Column Only (SIMPLER)
**Pros:**
- Minimal schema change
- Faster migration
- Less risk

**Cons:**
- Missing audit fields, soft delete
- Inconsistent with modern models
- Future refactoring needed

**Recommendation:** Use for legacy models.py only

---

## Migration Plan

### Step 1: Update Model Definitions

#### Phase 1A: Agent Models (Highest Priority)
```python
# database/models/agent_models.py

# Change imports
from database.models.base import TenantBaseModel, GlobalBaseModel

# Update model classes
class AgentInstance(TenantBaseModel):  # Changed from Base
    """Agent instance with multi-tenant isolation"""
    __tablename__ = "agent_instances"

    # Remove: id, created_at, updated_at (inherited from TenantBaseModel)
    # organization_id automatically added

    agent_id = Column(String(100), unique=True, nullable=False, index=True)
    # ... rest of fields unchanged

class AgentExecution(TenantBaseModel):  # Changed from Base
    __tablename__ = "agent_executions"
    # Same pattern...

class AgentMetrics(TenantBaseModel):
    __tablename__ = "agent_metrics"
    # Same pattern...

class AgentTaskQueue(TenantBaseModel):
    __tablename__ = "agent_task_queue"
    # Same pattern...

class SystemHealth(GlobalBaseModel):  # Use GlobalBaseModel
    """System-wide health monitoring (not tenant-scoped)"""
    __tablename__ = "system_health"
    # No organization_id - shared across all tenants

class AgentConfiguration(TenantBaseModel):
    __tablename__ = "agent_configuration"
    # Same pattern...
```

#### Phase 1B: Roblox Models
```python
# database/models/roblox_models.py

from database.models.base import TenantBaseModel

class RobloxEnvironment(TenantBaseModel):  # Changed from Base
    __tablename__ = "roblox_environments"

    # Remove duplicate fields (inherited from TenantBaseModel):
    # - id
    # - created_at, updated_at
    # - created_by_id, updated_by_id
    # - deleted_at

    # organization_id automatically added

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    # ... rest unchanged

class RobloxSession(TenantBaseModel):
    __tablename__ = "roblox_sessions"
    # Same pattern...

class EnvironmentShare(TenantBaseModel):
    __tablename__ = "environment_shares"
    # Same pattern...

class EnvironmentTemplate(TenantBaseModel):
    __tablename__ = "environment_templates"
    # Same pattern...
```

#### Phase 1C: Payment Models
```python
# database/models/payment.py

from database.models.base import TenantBaseModel, GlobalBaseModel

class Customer(TenantBaseModel):
    __tablename__ = "customers"
    # organization_id automatically added
    # ... fields

class Subscription(TenantBaseModel):
    __tablename__ = "subscriptions"
    # ... fields

# Continue for all payment models...

class Coupon(TenantBaseModel):
    __tablename__ = "coupons"

    # Allow nullable organization_id for platform-wide coupons
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,  # Platform-wide coupons have NULL
        index=True
    )
```

#### Phase 1D: Content Pipeline Models
```python
# database/models/content_pipeline_models.py

from database.models.base import TenantBaseModel, GlobalBaseModel

class EnhancedContentGeneration(TenantBaseModel):
    __tablename__ = "enhanced_content_generation"
    # ... fields

class ContentQualityMetrics(TenantBaseModel):
    __tablename__ = "content_quality_metrics"
    # ... fields

# Continue for tenant-scoped models...

class ContentCache(GlobalBaseModel):
    """System-wide content cache (not tenant-scoped)"""
    __tablename__ = "content_cache"
    # No organization_id
```

#### Phase 1E: Legacy Models (Minimal Changes)
```python
# database/models/models.py

# Add organization_id column to each model explicitly
# (Don't convert to TenantBaseModel to minimize changes)

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)

    # ADD THIS:
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ... existing fields unchanged

# Repeat for all 30+ legacy models
```

---

### Step 2: Generate Alembic Migration

```bash
# From project root
alembic revision --autogenerate -m "Add organization_id for multi-tenant isolation"
```

**Expected Migration Content:**
```python
# alembic/versions/XXXX_add_organization_id.py

def upgrade():
    # Agent models
    op.add_column('agent_instances', sa.Column('organization_id', UUID(as_uuid=True), nullable=False))
    op.create_foreign_key(None, 'agent_instances', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_agent_instances_organization_id'), 'agent_instances', ['organization_id'])

    # Repeat for all 70+ models...

    # Add indexes for performance
    op.create_index('idx_agent_exec_org_status', 'agent_executions', ['organization_id', 'status'])
    op.create_index('idx_roblox_env_org_user', 'roblox_environments', ['organization_id', 'user_id'])
    # ... more indexes

def downgrade():
    # Drop columns in reverse order
    op.drop_column('agent_instances', 'organization_id')
    # ... etc
```

---

### Step 3: Data Migration

**CRITICAL:** Before adding NOT NULL constraints, populate organization_id for existing data.

```sql
-- Example: Populate organization_id based on user's organization

-- Agent models (link via user)
UPDATE agent_executions ae
SET organization_id = u.organization_id
FROM users u
WHERE ae.user_id = u.id;

-- Roblox environments (link via user)
UPDATE roblox_environments re
SET organization_id = u.organization_id
FROM users u
WHERE re.user_id = u.id;

-- Payment models (link via user)
UPDATE customers c
SET organization_id = u.organization_id
FROM users u
WHERE c.user_id = u.id;

-- Content pipeline (link via user)
UPDATE enhanced_content_generation ecg
SET organization_id = u.organization_id
FROM users u
WHERE ecg.user_id = u.id;

-- For orphaned records (no user link):
-- Option 1: Assign to default organization
UPDATE agent_executions
SET organization_id = (SELECT id FROM organizations WHERE name = 'System' LIMIT 1)
WHERE organization_id IS NULL;

-- Option 2: Delete orphaned records
DELETE FROM agent_executions WHERE organization_id IS NULL;
```

---

### Step 4: Update Queries

**All queries must enforce organization filtering:**

```python
# Before (INSECURE):
executions = session.query(AgentExecution).filter(
    AgentExecution.status == 'running'
).all()

# After (SECURE):
executions = session.query(AgentExecution).filter(
    AgentExecution.organization_id == current_org_id,
    AgentExecution.status == 'running'
).all()

# Or use TenantAwareQuery helper:
from database.models.base import TenantAwareQuery

query = session.query(AgentExecution).filter(
    AgentExecution.status == 'running'
)
executions = TenantAwareQuery.tenant_scoped_query(
    query,
    current_org_id,
    include_deleted=False
).all()
```

**Search ALL Python files for queries:**
```bash
# Find all queries that need organization_id filtering
grep -r "session.query(Agent" apps/backend/
grep -r "session.query(Roblox" apps/backend/
grep -r "session.query(Customer" apps/backend/
grep -r "session.query(Payment" apps/backend/
```

---

### Step 5: Deploy RLS Policies

After migration completes, deploy RLS policies from Task 1.2:

```bash
# Deploy RLS policies
psql $DATABASE_URL < database/supabase/migrations/002_enhanced_rls_policies.sql

# Validate policies
psql $DATABASE_URL < scripts/database/validate_rls_policies.sql
```

---

## Security Impact

### Current Vulnerabilities (Before Migration)
- 🔴 **Cross-Tenant Data Access**: Agents can read/modify other organizations' data
- 🔴 **Financial Data Leakage**: Payment information not isolated
- 🔴 **Roblox Environment Access**: Users can access other orgs' environments
- 🔴 **Content Leakage**: Educational content visible across tenants

### After Migration (Mitigated)
- ✅ **Database-Level Isolation**: Organization filtering enforced at query level
- ✅ **RLS Policy Protection**: Row-level security prevents unauthorized access
- ✅ **Audit Trail**: All access attempts logged
- ✅ **FERPA/COPPA Compliance**: Student data properly isolated

---

## Performance Considerations

### Indexes Required

**Critical Indexes:**
```sql
-- Multi-column indexes for common queries
CREATE INDEX idx_agent_exec_org_status ON agent_executions(organization_id, status);
CREATE INDEX idx_agent_exec_org_created ON agent_executions(organization_id, created_at DESC);
CREATE INDEX idx_roblox_env_org_user ON roblox_environments(organization_id, user_id);
CREATE INDEX idx_roblox_env_org_status ON roblox_environments(organization_id, status);
CREATE INDEX idx_payment_org_customer ON payments(organization_id, customer_id);
CREATE INDEX idx_subscription_org_status ON subscriptions(organization_id, status);

-- Composite indexes for filtering + sorting
CREATE INDEX idx_agent_metrics_org_timestamp ON agent_metrics(organization_id, recorded_at DESC);
CREATE INDEX idx_content_gen_org_created ON enhanced_content_generation(organization_id, created_at DESC);
```

### Query Performance Impact

**Before Migration:**
- Queries scan entire table
- No organization filtering overhead

**After Migration:**
- Index seek on organization_id (FAST)
- Reduced result set size (FASTER)
- RLS policy check (minimal overhead)

**Net Result:** Queries may be FASTER due to smaller result sets.

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/models/test_tenant_isolation.py

async def test_agent_execution_requires_organization():
    """Test that AgentExecution requires organization_id"""
    execution = AgentExecution(
        task_id="test-task",
        agent_instance_id=agent_id,
        # Missing organization_id
    )

    with pytest.raises(IntegrityError):
        session.add(execution)
        await session.commit()

async def test_query_filters_by_organization():
    """Test that queries enforce organization filtering"""
    org1_id = uuid4()
    org2_id = uuid4()

    # Create executions for org1
    exec1 = create_execution(organization_id=org1_id)

    # Create executions for org2
    exec2 = create_execution(organization_id=org2_id)

    # Query as org1 - should only see org1 data
    results = session.query(AgentExecution).filter(
        AgentExecution.organization_id == org1_id
    ).all()

    assert len(results) == 1
    assert results[0].organization_id == org1_id
```

### Integration Tests
```python
# tests/integration/test_rls_policies.py

async def test_rls_prevents_cross_tenant_access():
    """Test RLS policies block unauthorized access"""
    # Set user context for org1
    await session.execute(text("SET SESSION my.organization_id = :org_id"), {"org_id": str(org1_id)})

    # Try to query org2 data
    results = session.query(RobloxEnvironment).filter(
        RobloxEnvironment.organization_id == org2_id
    ).all()

    # RLS should block this
    assert len(results) == 0
```

### Load Tests
```bash
# Test query performance with organization filtering
pytest tests/performance/test_tenant_queries.py --benchmark
```

---

## Rollback Plan

### Emergency Rollback

```bash
# Revert migration
alembic downgrade -1

# Verify rollback
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'agent_executions' AND column_name = 'organization_id';"
# Should return 0 rows
```

### Partial Rollback

If only specific models have issues:

```sql
-- Remove organization_id from specific table
ALTER TABLE agent_executions DROP COLUMN organization_id;

-- Keep organization_id on other tables
-- Fix the problematic model code
-- Re-run migration for just that table
```

---

## Success Criteria

✅ **Migration Successful When:**
1. All 70+ models have organization_id column
2. Alembic migration runs without errors
3. All existing data has valid organization_id
4. All queries updated with organization filtering
5. RLS policies deployed and validated
6. Unit tests pass (100% coverage on new columns)
7. Integration tests confirm tenant isolation
8. Performance benchmarks meet targets (<100ms p95)

---

## Next Steps

### Immediate Actions
1. ✅ **Complete this analysis** (DONE)
2. 🔄 **Update model definitions** (IN PROGRESS - Next)
3. ⏳ **Generate Alembic migration**
4. ⏳ **Test migration in development**
5. ⏳ **Update all queries with org filtering**
6. ⏳ **Deploy to staging**
7. ⏳ **Run integration tests**
8. ⏳ **Deploy to production**

### Files to Modify
- `database/models/agent_models.py` - 5 models
- `database/models/roblox_models.py` - 4 models
- `database/models/payment.py` - 9-10 models
- `database/models/content_pipeline_models.py` - 6 models
- `database/models/models.py` - 30+ models (legacy)

### Estimated Effort
- **Model Updates:** 4-6 hours
- **Migration Generation:** 1 hour
- **Data Migration Script:** 2-3 hours
- **Query Updates:** 6-8 hours
- **Testing:** 4-6 hours
- **Total:** 17-24 hours

---

## Appendix A: Model Count Summary

| File | Total Models | With org_id | Missing org_id | Global Models |
|------|--------------|-------------|----------------|---------------|
| storage.py | 5 | 3 | 0 | 2 |
| user_modern.py | 3 | 3 | 0 | 0 |
| content_modern.py | 4+ | 4+ | 0 | 0 |
| agent_models.py | 6 | 0 | 5 | 1 |
| roblox_models.py | 4 | 0 | 4 | 0 |
| payment.py | 10 | 0 | 9-10 | 0-1 |
| content_pipeline_models.py | 7 | 0 | 6 | 1 |
| models.py (legacy) | 37+ | 0 | 30+ | 4-7 |
| tenant.py | 3 | 2* | 0 | 1 |
| **TOTAL** | **79+** | **12+** | **54-60** | **9-12** |

*tenant.py models have organization_id as explicit column, not via mixin

---

## Appendix B: Migration File Size Estimates

**Estimated Migration File:**
- Add organization_id: ~60 columns × 5 lines each = 300 lines
- Add foreign keys: ~60 constraints × 3 lines each = 180 lines
- Add indexes: ~80 indexes × 3 lines each = 240 lines
- Data migration: ~60 UPDATE statements × 5 lines each = 300 lines
- **Total:** ~1,020 lines of migration code

**Estimated Execution Time:**
- Column additions: 5-10 seconds per table = 5-10 minutes
- Data population: Depends on table size, estimate 10-30 minutes
- Index creation: 5-10 seconds per index = 6-13 minutes
- **Total:** 21-53 minutes for full migration

---

**Report Generated:** 2025-10-10
**Generated By:** Claude Code Assistant (Task 1.3 Analysis)
**Next Action:** Update model definitions in Phase 1A-1E
