# API Endpoint Update Checklist - Organization Filtering

**Phase:** 1.4 - Update API Endpoints with Multi-Tenant Isolation
**Status:** In Progress (Testing Complete, Implementation Starting)
**Created:** 2025-10-11

## Overview

This document provides a practical, file-by-file checklist for updating all API endpoints with organization filtering. Each section indicates what changes are needed and provides direct code patterns.

## Progress Tracking

- ✅ **Foundation Complete**
  - Organization filtering dependencies created (`apps/backend/core/deps.py`)
  - Legacy `database/database_service.py` restored to keep existing endpoints operational while async session manager migrates
  - Implementation guide created with all patterns
  - Example implementation created (`agent_instances.py`)
  - Integration tests created (`test_multi_tenant_api_isolation.py`)

- 🚧 **In Progress**
  - Updating actual endpoint files

- ⏳ **Pending**
  - Running integration tests
  - Performance validation
  - Security audit

---

## Files Requiring Updates

### 1. Agent Endpoints (Priority: HIGH)

#### ❌ `apps/backend/api/v1/endpoints/agents.py`
**Type:** Service-based (uses `get_agent_service()`)
**Database Access:** Indirect via agent service
**Estimated Time:** 30-45 minutes

**Required Changes:**
```python
# 1. Add import
from uuid import UUID
from apps.backend/core.deps import get_current_organization_id

# 2. Update each endpoint to include org_id dependency
@router.get("/health")
async def get_agents_health(
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_current_active_user)
):
    # Pass org_id to service methods
    health_data = await get_agent_health(organization_id=org_id)
    ...

# 3. Update /list endpoint
@router.get("/list")
async def list_agents(
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_current_active_user)
):
    agent_service = get_agent_service()
    agents = await agent_service.list_agents(organization_id=org_id)  # FILTER
    ...

# 4. Update /{agent_id}/status endpoint
@router.get("/{agent_id}/status")
async def get_agent_status(
    agent_id: str = Depends(validate_agent_id),
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_current_active_user),
):
    status_info = await agent_service.get_agent_status(agent_id, organization_id=org_id)
    ...

# 5. Update /{agent_id}/restart endpoint (admin only)
@router.post("/{agent_id}/restart")
async def restart_agent(
    agent_id: str = Depends(validate_agent_id),
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_admin_user)
):
    # Verify agent belongs to organization before restarting
    ...
```

**Service Layer Updates Required:**
- Update `apps/backend/services/agent_service.py` to accept and filter by `organization_id`
- Add organization validation to all service methods

**Testing:**
```bash
# After updating
pytest tests/integration/test_multi_tenant_api_isolation.py::test_agent_instances_organization_isolation -v
```

---

#### ❌ `apps/backend/api/v1/endpoints/ai_agent_orchestration.py`
**Type:** Agent orchestration logic
**Database Access:** Likely indirect via services
**Estimated Time:** 45-60 minutes

**Required Changes:**
```python
# 1. Add organization_id dependency to all endpoints
# 2. Pass organization_id to orchestration methods
# 3. Ensure orchestrated agents are scoped to organization
```

**Notes:**
- May require updates to orchestration coordinator
- Need to ensure swarm agents respect organization boundaries

---

#### ❌ `apps/backend/api/v1/endpoints/agent_swarm.py`
**Type:** Multi-agent swarm coordination
**Database Access:** Likely indirect
**Estimated Time:** 45-60 minutes

**Required Changes:**
```python
# 1. Add organization filtering to swarm creation
# 2. Ensure swarm members are all from same organization
# 3. Update swarm listing to filter by organization
```

---

#### ❌ `apps/backend/api/v1/endpoints/direct_agents.py`
**Type:** Direct agent communication
**Database Access:** Unknown (need to review)
**Estimated Time:** 30-45 minutes

**Required Changes:**
- Review file structure
- Add organization filtering based on access pattern

---

#### ❌ `apps/backend/api/v1/endpoints/roblox_agents.py`
**Type:** Roblox-specific agent operations
**Database Access:** Unknown (need to review)
**Estimated Time:** 30-45 minutes

**Required Changes:**
- Review file structure
- Add organization filtering
- Ensure Roblox environment access is organization-scoped

---

### 2. Roblox Endpoints (Priority: HIGH)

#### ❌ `apps/backend/api/v1/endpoints/roblox_environment.py`
**Type:** Roblox environment creation and management
**Database Access:** Via `rojo_api_service`
**Estimated Time:** 45-60 minutes

**Required Changes:**
```python
# 1. Add import
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

# 2. Update /preview endpoint
@router.post("/preview")
async def preview_environment(
    request: EnvironmentCreationRequest,
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_current_user)
):
    # Pass org_id to rojo service
    async with rojo_api_service as rojo:
        parsed_components = await rojo._parse_environment_description(
            request.description,
            organization_id=org_id  # ADD THIS
        )
    ...

# 3. Update /create endpoint
@router.post("/create")
async def create_environment(
    request: EnvironmentCreationRequest,
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
):
    # Store org_id when creating environment
    environment = await rojo._create_environment(
        ...,
        organization_id=org_id,  # ADD THIS
        created_by_id=current_user.id
    )
    ...

# 4. Update /status/{environment_name} endpoint
@router.get("/status/{environment_name}")
async def get_environment_status(
    environment_name: str,
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    current_user: User = Depends(get_current_user)
):
    # Verify environment belongs to organization
    ...
```

**Service Layer Updates:**
- Update `apps/backend/services/rojo_api.py` to handle organization_id
- Add organization validation to environment operations

---

#### ❌ `apps/backend/api/v1/endpoints/roblox_studio.py`
**Type:** Roblox Studio integration
**Database Access:** Unknown (need to review)
**Estimated Time:** 30-45 minutes

**Required Changes:**
- Review file (may not exist yet)
- Add organization filtering if it accesses RobloxEnvironment or RobloxAsset models

---

### 3. Payment Endpoints (Priority: MEDIUM)

#### ❌ `apps/backend/api/v1/endpoints/stripe_webhooks.py`
**Type:** Stripe webhook handler
**Database Access:** Direct to Subscription, Invoice models
**Estimated Time:** 45-60 minutes

**Status:** Already modified (per git status), but needs verification

**Required Changes:**
```python
# 1. Add organization_id filtering to subscription lookups
# 2. Ensure webhook events are scoped to correct organization
# 3. Validate organization ownership before processing payments

# Example: Subscription lookup
@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_database_session)
):
    # ... verify webhook signature ...

    if event_type == "customer.subscription.updated":
        subscription_id = event_data["object"]["id"]

        # Look up subscription WITH organization_id
        result = await db.execute(
            select(Subscription).filter_by(
                stripe_subscription_id=subscription_id,
                organization_id=org_id  # ADD THIS FILTER
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            # Log potential cross-org access attempt
            logger.warning(f"Subscription {subscription_id} not found or access denied")
            return {"status": "ignored"}
        ...
```

**Important:** Webhook endpoints don't have user context, so organization_id must come from the resource being updated (e.g., subscription's organization_id)

---

#### ❌ `apps/backend/api/v1/endpoints/payments.py`
**Type:** Payment management (if exists)
**Database Access:** Direct to payment models
**Estimated Time:** 30-45 minutes

**Required Changes:**
```python
# 1. Add org_id dependency to all endpoints
# 2. Filter payment history by organization
# 3. Ensure refunds/updates are organization-scoped
```

---

### 4. Content Endpoints (Priority: MEDIUM)

#### ❌ `apps/backend/api/v1/endpoints/content.py`
**Type:** Content generation and management
**Database Access:** Direct to ContentGeneration model
**Estimated Time:** 45-60 minutes

**Required Changes:**
```python
# 1. Add import
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

# 2. Update content listing
@router.get("/generations")
async def list_content_generations(
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(ContentGeneration)
        .filter_by(organization_id=org_id)  # ADD THIS FILTER
        .offset(skip)
        .limit(limit)
    )
    generations = result.scalars().all()
    return {"generations": generations}

# 3. Update content creation
@router.post("/generate")
async def generate_content(
    request: ContentGenerationRequest,
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user),
):
    content = ContentGeneration(
        request_id=str(uuid4()),
        content_type=request.content_type,
        prompt=request.prompt,
        organization_id=org_id,  # ADD THIS
        created_by_id=current_user.id,  # ADD THIS
    )
    db.add(content)
    await db.commit()
    ...

# 4. Update content retrieval
@router.get("/generations/{generation_id}")
async def get_content_generation(
    generation_id: str,
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ContentGeneration).filter_by(
            id=generation_id,
            organization_id=org_id  # ADD THIS FILTER
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=404,
            detail="Content generation not found or you don't have access"
        )
    return content
```

---

### 5. Organization Management Endpoints (Priority: LOW)

#### ✅ `apps/backend/api/v1/endpoints/organizations.py`
**Type:** Organization CRUD
**Database Access:** Direct to Organization model
**Estimated Time:** N/A (Special handling required)

**Notes:**
- Organization endpoints have special semantics
- Users should only see/update their own organization
- Admin users may see all organizations
- Requires different filtering logic than other resources

**Required Changes:**
```python
# Current user's organization endpoint
@router.get("/me")
async def get_my_organization(
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_database_session),
):
    org = await db.get(Organization, org_id)
    return org

# Admin: list all organizations
@router.get("/")
async def list_organizations(
    current_user: User = Depends(get_admin_user),  # Admin only
    db: AsyncSession = Depends(get_database_session),
):
    # Admins can see all organizations
    result = await db.execute(select(Organization))
    return result.scalars().all()
```

---

### 6. Other Endpoints (Priority: LOW)

#### ❌ `apps/backend/api/v1/endpoints/classes.py`
**Database Access:** Direct to Class model
**Estimated Time:** 30-45 minutes

#### ❌ `apps/backend/api/v1/endpoints/uploads.py`
**Database Access:** Storage service + File model
**Estimated Time:** 30-45 minutes

#### ❌ `apps/backend/api/v1/endpoints/mobile.py`
**Database Access:** Various models
**Estimated Time:** 30-45 minutes

---

## Update Process (Standard Workflow)

For each endpoint file:

### Step 1: Read and Analyze (5-10 minutes)
```bash
# Read the file
code apps/backend/api/v1/endpoints/[filename].py

# Identify:
# - Which models are accessed
# - Whether database queries are direct or via services
# - Which endpoints need organization filtering
```

### Step 2: Update Imports (1 minute)
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id
```

### Step 3: Update Each Endpoint (5-10 minutes per endpoint)
```python
# Add org_id parameter to EVERY endpoint
@router.[method]("/path")
async def endpoint_function(
    # ... existing parameters ...
    org_id: UUID = Depends(get_current_organization_id),  # ADD THIS LINE
    # ... other dependencies ...
):
    # Update query/service calls to filter by org_id
    ...
```

### Step 4: Update Service Calls (if applicable)
```python
# Before
result = await service.get_items()

# After
result = await service.get_items(organization_id=org_id)
```

### Step 5: Add Audit Trail Fields (for create/update)
```python
# Create
item = Model(
    ...,
    organization_id=org_id,
    created_by_id=current_user.id,
)

# Update
item.updated_by_id = current_user.id
```

### Step 6: Test the Endpoint (5 minutes)
```bash
# Run integration tests for this endpoint
pytest tests/integration/test_multi_tenant_api_isolation.py::[test_name] -v

# Manual test with curl
curl -H "Authorization: Bearer $TOKEN" http://localhost:8009/api/v1/[endpoint]
```

---

## Testing Strategy

### Unit Tests
```bash
# Test individual endpoint functions
pytest tests/unit/api/v1/endpoints/test_[endpoint].py -v
```

### Integration Tests
```bash
# Test multi-tenant isolation
pytest tests/integration/test_multi_tenant_api_isolation.py -v

# Test specific resource type
pytest tests/integration/test_multi_tenant_api_isolation.py::test_agent_instances_organization_isolation -v
```

### Manual Testing
```bash
# 1. Create test organizations and users
# 2. Generate JWT tokens for each user
# 3. Test cross-organization access attempts (should fail)
# 4. Test same-organization access (should succeed)

# Example: Test agent endpoint
export TOKEN_ORG_A="eyJ..."
export TOKEN_ORG_B="eyJ..."

# Create agent for Org A
curl -X POST http://localhost:8009/api/v1/agent-instances \
  -H "Authorization: Bearer $TOKEN_ORG_A" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test-agent", "agent_type": "content_generator"}'

# Try to access from Org B (should fail with 404)
curl http://localhost:8009/api/v1/agent-instances/test-agent \
  -H "Authorization: Bearer $TOKEN_ORG_B"
```

---

## Common Pitfalls

### ❌ Forgetting to Add org_id Dependency
```python
# WRONG - No organization filtering
@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_database_session)):
    return await db.execute(select(Item)).scalars().all()

# CORRECT
@router.get("/items")
async def list_items(
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_database_session)
):
    return await db.execute(select(Item).filter_by(organization_id=org_id)).scalars().all()
```

### ❌ Not Filtering Subqueries
```python
# WRONG - Parent filtered, but not related items
@router.get("/agents/{agent_id}/executions")
async def get_executions(agent_id: str, org_id: UUID = Depends(get_current_organization_id)):
    agent = await db.get(AgentInstance, agent_id)
    # Missing: Verify agent.organization_id == org_id
    return agent.executions  # Could leak cross-org data

# CORRECT
@router.get("/agents/{agent_id}/executions")
async def get_executions(agent_id: str, org_id: UUID = Depends(get_current_organization_id)):
    result = await db.execute(
        select(AgentInstance).filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent.executions
```

### ❌ Revealing Resource Existence Across Organizations
```python
# WRONG - Error message reveals resource exists
if agent.organization_id != org_id:
    raise HTTPException(403, "You don't have access to this agent")

# CORRECT - Generic message
if not agent or agent.organization_id != org_id:
    raise HTTPException(404, "Agent not found or you don't have access")
```

---

## Completion Criteria

An endpoint file is considered **COMPLETE** when:

- [ ] All endpoints have `org_id = Depends(get_current_organization_id)` parameter
- [ ] All database queries filter by `organization_id`
- [ ] All create operations set `organization_id` and `created_by_id`
- [ ] All update operations set `updated_by_id`
- [ ] Service calls (if any) pass `organization_id`
- [ ] Integration tests pass for that endpoint
- [ ] Manual testing confirms cross-org access is blocked
- [ ] Error messages don't leak information about other organizations
- [ ] Code review approved

---

## Next Steps

1. **Start with high-priority files** (agents, roblox_environment)
2. **Update one file at a time**
3. **Test after each file** before moving to next
4. **Document any service layer changes needed**
5. **Update progress in `PHASE1_TASK1.4_PROGRESS.md`**

---

## Questions & Decisions

### Q: What about endpoints that don't access database?
**A:** If an endpoint doesn't store/retrieve organization-specific data, it may not need filtering. However, add the dependency for consistency and future-proofing.

### Q: What about admin-only endpoints?
**A:** Admin endpoints should still include `org_id` dependency if they operate on organization-scoped resources. Admins may need to specify which organization they're operating on.

### Q: What about webhook endpoints without user context?
**A:** Webhooks must extract organization_id from the resource being updated (e.g., subscription's organization_id). Never trust organization_id from external webhook payload.

### Q: Should we update service layer first or endpoints first?
**A:** Update endpoints first, then service layer. This makes it clear which service methods need organization filtering.

---

**Last Updated:** 2025-10-11
**Next Review:** After completing agent endpoint updates
