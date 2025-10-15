# API Endpoints Organization Filtering Guide
## Phase 1 Task 1.4 - Update API Endpoints with Multi-Tenant Support

**Date:** 2025-10-10
**Phase:** 1 - Multi-Tenant Data Isolation
**Task:** 1.4 - Update API Endpoints
**Status:** 🚧 In Progress

---

## Overview

This guide provides patterns and examples for updating FastAPI endpoints to support multi-tenant organization filtering using the dependencies created in Phase 1, Task 1.3.

### What This Task Accomplishes

- ✅ Add organization_id filtering to all GET endpoints
- ✅ Set organization_id automatically on POST/PUT endpoints
- ✅ Verify organization ownership on single-resource GET/PUT/DELETE
- ✅ Enable RLS context for database-level security
- ✅ Maintain backward compatibility where possible

---

## Updated Dependencies Available

The following dependencies are now available in `apps/backend/core/deps.py`:

```python
# Async version (for async endpoints)
async def get_current_organization_id(
    current_user: User = Depends(get_current_user),
    db: Optional[AsyncSession] = Depends(get_async_db),
) -> UUID

# Sync version (for sync endpoints)
def get_current_organization_id_sync(
    current_user: User = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
) -> UUID

# Verify resource ownership
async def verify_organization_access(
    resource_org_id: UUID,
    current_org_id: UUID = Depends(get_current_organization_id),
) -> bool

# Combined role + organization check
def require_admin_or_own_organization(
    current_user: User = Depends(get_current_user),
    current_org_id: UUID = Depends(get_current_organization_id),
)
```

---

## Update Patterns

### Pattern 1: List Endpoint (GET /resources)

**Before:**
```python
@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all agent instances"""
    # ❌ No organization filtering - returns all agents
    result = await db.execute(select(AgentInstance))
    agents = result.scalars().all()
    return agents
```

**After (Method 1 - Manual Filtering):**
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

@router.get("/agents")
async def list_agents(
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List agent instances for current organization"""
    # ✅ Filtered by organization_id - RLS also enforces this
    result = await db.execute(
        select(AgentInstance).filter_by(organization_id=org_id)
    )
    agents = result.scalars().all()
    return agents
```

**After (Method 2 - Using TenantAwareQuery for Sync):**
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id_sync
from database.tenant_aware_query import TenantAwareQuery

@router.get("/agents")
def list_agents_sync(
    org_id: UUID = Depends(get_current_organization_id_sync),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List agent instances for current organization"""
    # ✅ TenantAwareQuery automatically filters
    query = TenantAwareQuery(db, AgentInstance, org_id)
    agents = query.all()
    return agents
```

### Pattern 2: Create Endpoint (POST /resources)

**Before:**
```python
@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new agent instance"""
    # ❌ No organization_id set - violates multi-tenant isolation
    agent = AgentInstance(
        agent_id=data.agent_id,
        agent_type=data.agent_type,
        status="INITIALIZING",
        created_by_id=current_user.id
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent
```

**After:**
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreateSchema,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new agent instance"""
    # ✅ organization_id automatically set from current user
    agent = AgentInstance(
        agent_id=data.agent_id,
        agent_type=data.agent_type,
        status="INITIALIZING",
        organization_id=org_id,  # Required!
        created_by_id=current_user.id
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent
```

### Pattern 3: Get Single Resource (GET /resources/{id})

**Before:**
```python
@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get agent instance by ID"""
    # ❌ No organization check - can access other orgs' agents
    agent = await db.get(AgentInstance, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
```

**After (Method 1 - Explicit Check):**
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get agent instance by ID"""
    # ✅ Verify agent belongs to current organization
    agent = await db.get(AgentInstance, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.organization_id != org_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this agent"
        )

    return agent
```

**After (Method 2 - Query with Filter):**
```python
from uuid import UUID
from sqlalchemy import select
from apps.backend.core.deps import get_current_organization_id

@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get agent instance by ID"""
    # ✅ Query includes organization filter
    result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    return agent
```

### Pattern 4: Update Endpoint (PUT/PATCH /resources/{id})

**Before:**
```python
@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    data: AgentUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update agent instance"""
    # ❌ No organization check - can update other orgs' agents
    agent = await db.get(AgentInstance, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = data.status
    agent.configuration = data.configuration
    await db.commit()
    return agent
```

**After:**
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    data: AgentUpdateSchema,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update agent instance"""
    # ✅ Verify organization ownership before update
    result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    # Update fields
    agent.status = data.status
    agent.configuration = data.configuration
    agent.updated_by_id = current_user.id  # Audit trail
    await db.commit()
    await db.refresh(agent)
    return agent
```

### Pattern 5: Delete Endpoint (DELETE /resources/{id})

**Before:**
```python
@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete agent instance"""
    # ❌ No organization check - can delete other orgs' agents
    agent = await db.get(AgentInstance, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(agent)
    await db.commit()
```

**After:**
```python
from uuid import UUID
from apps.backend.core.deps import get_current_organization_id

@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete agent instance"""
    # ✅ Verify organization ownership before delete
    result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    await db.delete(agent)
    await db.commit()
```

---

## Model-Specific Patterns

### Agent Endpoints (`/api/v1/agents`)

**Files to Update:**
- `apps/backend/api/v1/endpoints/agents.py`
- `apps/backend/api/v1/endpoints/ai_agent_orchestration.py`
- `apps/backend/api/v1/endpoints/agent_swarm.py`
- `apps/backend/api/v1/endpoints/direct_agents.py`
- `apps/backend/api/v1/endpoints/roblox_agents.py`

**Models Affected:**
- AgentInstance
- AgentExecution
- AgentMetrics
- AgentTaskQueue
- AgentConfiguration

**Key Changes:**
```python
# All list endpoints
org_id: UUID = Depends(get_current_organization_id)
# Filter: .filter_by(organization_id=org_id)

# All create endpoints
organization_id=org_id  # Add to model creation

# All get/update/delete endpoints
# Verify: agent.organization_id == org_id
```

### Roblox Endpoints (`/api/v1/roblox`)

**Files to Update:**
- `apps/backend/api/v1/endpoints/roblox_environment.py`
- `apps/backend/api/v1/endpoints/roblox_studio.py`

**Models Affected:**
- RobloxEnvironment
- RobloxSession
- EnvironmentShare
- EnvironmentTemplate

**Key Changes:**
```python
# Environment creation
environment = RobloxEnvironment(
    user_id=current_user.id,
    name=data.name,
    place_id=data.place_id,
    organization_id=org_id  # Add this
)

# Environment sharing
share = EnvironmentShare(
    environment_id=env.id,
    shared_with_user_id=data.user_id,
    permission=data.permission,
    organization_id=org_id  # Add this
)
```

### Payment Endpoints (`/api/v1/stripe`, `/api/v1/billing`)

**Files to Update:**
- `apps/backend/api/v1/endpoints/stripe_webhooks.py`
- Any billing/payment endpoints

**Models Affected:**
- Customer
- Subscription
- SubscriptionItem
- CustomerPaymentMethod
- Payment
- Invoice
- InvoiceItem
- Refund
- UsageRecord

**Key Changes:**
```python
# Customer creation
customer = Customer(
    user_id=current_user.id,
    stripe_customer_id=stripe_customer.id,
    email=current_user.email,
    organization_id=org_id  # Add this
)

# Subscription queries
subscriptions = await db.execute(
    select(Subscription)
    .filter_by(organization_id=org_id, status='active')
)
```

**Special Case - Coupons:**
```python
# Platform-wide coupon (admin only)
if current_user.role == 'admin' and data.is_platform_wide:
    coupon = Coupon(
        code=data.code,
        discount_percent=data.discount,
        organization_id=None  # NULL for platform-wide
    )
else:
    # Organization-specific coupon
    coupon = Coupon(
        code=data.code,
        discount_percent=data.discount,
        organization_id=org_id  # Scoped to organization
    )
```

### Content Pipeline Endpoints

**Files to Update:**
- `apps/backend/api/v1/endpoints/content.py`
- Any content generation endpoints

**Models Affected:**
- EnhancedContentGeneration
- ContentQualityMetrics
- LearningProfile
- ContentPersonalizationLog
- ContentFeedback
- ContentGenerationBatch

**Key Changes:**
```python
# Content generation
content = EnhancedContentGeneration(
    user_id=current_user.id,
    topic=data.topic,
    difficulty_level=data.difficulty,
    organization_id=org_id  # Add this
)

# Learning profile
profile = LearningProfile(
    student_id=current_user.id,
    learning_style=data.style,
    organization_id=org_id  # Add this
)
```

---

## Complete Example: Agent Endpoints Update

Here's a complete example showing how to update the agents endpoint file:

```python
"""
Agent system endpoints with multi-tenant organization filtering
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from apps.backend.core.deps import (
    get_current_user,
    get_current_active_user,
    get_current_organization_id,
    get_async_db,
)
from database.models.agent_models import AgentInstance, AgentExecution
from database.models import User

router = APIRouter()


# Schemas
class AgentCreateSchema(BaseModel):
    agent_id: str
    agent_type: str
    configuration: Optional[dict] = {}


class AgentUpdateSchema(BaseModel):
    status: Optional[str]
    configuration: Optional[dict]


class AgentResponse(BaseModel):
    id: UUID
    agent_id: str
    agent_type: str
    status: str
    organization_id: UUID
    created_at: str

    class Config:
        from_attributes = True


# List agents for current organization
@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    status_filter: Optional[str] = None,
    agent_type_filter: Optional[str] = None,
):
    """
    List all agent instances for the current organization.

    Query Parameters:
        status_filter: Filter by agent status (IDLE, BUSY, ERROR, etc.)
        agent_type_filter: Filter by agent type

    Returns:
        List of agent instances belonging to current organization
    """
    query = select(AgentInstance).filter_by(organization_id=org_id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    if agent_type_filter:
        query = query.filter_by(agent_type=agent_type_filter)

    result = await db.execute(query)
    agents = result.scalars().all()

    return agents


# Create agent
@router.post("/agents", status_code=status.HTTP_201_CREATED, response_model=AgentResponse)
async def create_agent(
    data: AgentCreateSchema,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new agent instance for the current organization.

    Automatically sets organization_id from authenticated user.
    """
    # Check if agent_id already exists in this organization
    existing = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=data.agent_id, organization_id=org_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Agent with ID '{data.agent_id}' already exists in your organization"
        )

    # Create agent with organization_id
    agent = AgentInstance(
        agent_id=data.agent_id,
        agent_type=data.agent_type,
        status="INITIALIZING",
        configuration=data.configuration,
        organization_id=org_id,  # Multi-tenant isolation
        created_by_id=current_user.id
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return agent


# Get single agent
@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get agent instance by ID.

    Only returns agents belonging to current organization.
    """
    result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    return agent


# Update agent
@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    data: AgentUpdateSchema,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update agent instance.

    Only updates agents belonging to current organization.
    """
    result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    # Update fields
    if data.status is not None:
        agent.status = data.status

    if data.configuration is not None:
        agent.configuration = data.configuration

    agent.updated_by_id = current_user.id

    await db.commit()
    await db.refresh(agent)

    return agent


# Delete agent
@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete agent instance.

    Only deletes agents belonging to current organization.
    """
    result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    await db.delete(agent)
    await db.commit()


# Get agent executions
@router.get("/agents/{agent_id}/executions")
async def get_agent_executions(
    agent_id: str,
    org_id: UUID = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get execution history for an agent.

    Only returns executions for agents in current organization.
    """
    # First verify agent belongs to current organization
    agent_result = await db.execute(
        select(AgentInstance)
        .filter_by(agent_id=agent_id, organization_id=org_id)
    )
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found or you don't have access"
        )

    # Get executions (also filtered by organization_id for defense in depth)
    exec_result = await db.execute(
        select(AgentExecution)
        .filter_by(agent_instance_id=agent.id, organization_id=org_id)
        .order_by(AgentExecution.created_at.desc())
    )
    executions = exec_result.scalars().all()

    return executions
```

---

## Testing the Updates

### Manual Testing

```bash
# Test 1: Create agent in org1
curl -X POST http://localhost:8009/api/v1/agents \
  -H "Authorization: Bearer $ORG1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent-org1",
    "agent_type": "CONTENT_GENERATOR",
    "configuration": {}
  }'

# Test 2: List agents from org1 (should see test-agent-org1)
curl http://localhost:8009/api/v1/agents \
  -H "Authorization: Bearer $ORG1_TOKEN"

# Test 3: Try to access from org2 (should NOT see test-agent-org1)
curl http://localhost:8009/api/v1/agents \
  -H "Authorization: Bearer $ORG2_TOKEN"

# Test 4: Try to get org1's agent from org2 (should get 404)
curl http://localhost:8009/api/v1/agents/test-agent-org1 \
  -H "Authorization: Bearer $ORG2_TOKEN"
# Expected: 404 "Agent not found or you don't have access"
```

### Integration Tests

Create test file: `tests/integration/test_api_organization_filtering.py`

```python
import pytest
from httpx import AsyncClient
from uuid import uuid4

async def test_agent_list_filtering(client: AsyncClient, org1_token, org2_token):
    """Test agents are filtered by organization"""

    # Create agent in org1
    response = await client.post(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {org1_token}"},
        json={"agent_id": "test-org1", "agent_type": "CONTENT_GENERATOR"}
    )
    assert response.status_code == 201

    # List from org1 (should see it)
    response = await client.get(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {org1_token}"}
    )
    assert response.status_code == 200
    agents = response.json()
    assert any(a["agent_id"] == "test-org1" for a in agents)

    # List from org2 (should NOT see it)
    response = await client.get(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {org2_token}"}
    )
    assert response.status_code == 200
    agents = response.json()
    assert not any(a["agent_id"] == "test-org1" for a in agents)
```

---

## Checklist for Each Endpoint File

- [ ] Import `UUID` from `uuid`
- [ ] Import `get_current_organization_id` or `get_current_organization_id_sync`
- [ ] Add `org_id: UUID = Depends(get_current_organization_id)` to all endpoints
- [ ] Update list endpoints: Add `.filter_by(organization_id=org_id)`
- [ ] Update create endpoints: Add `organization_id=org_id` to model creation
- [ ] Update get/update/delete endpoints: Verify `resource.organization_id == org_id`
- [ ] Update docstrings to mention organization scope
- [ ] Add integration tests for cross-organization isolation
- [ ] Test manually with different organization tokens

---

## Deployment Checklist

- [ ] All endpoint files updated
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] API documentation updated
- [ ] Migration deployed (schema + data + RLS)
- [ ] Monitor API response times
- [ ] Monitor error logs for authorization failures

---

## Next Steps

After completing API endpoint updates (Task 1.4):

1. **Task 1.5:** Performance Testing
   - Benchmark query performance
   - Verify index usage
   - Optimize slow queries

2. **Task 1.6:** Security Audit
   - Penetration testing
   - Verify data isolation
   - Review audit logs

---

**Document Version:** 1.0
**Last Updated:** 2025-10-10
**Status:** 🚧 Work in Progress

---

*This guide provides comprehensive patterns for updating API endpoints with organization filtering for Phase 1, Task 1.4.*
