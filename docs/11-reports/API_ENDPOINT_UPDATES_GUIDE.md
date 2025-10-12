# API Endpoint Updates for Multi-Tenant Isolation
## Organization Filtering Implementation Guide

**Date:** 2025-10-10
**Phase:** 1 - Multi-Tenant Data Isolation
**Target:** FastAPI Backend Endpoints
**Priority:** CRITICAL - Required for Production

---

## Executive Summary

After deploying the Phase 1 database schema migration, **all API endpoints must be updated** to include organization filtering. This document provides patterns and examples for updating endpoints to work with the new multi-tenant architecture.

### Critical Changes Required

1. ✅ Add `organization_id` to all database queries
2. ✅ Set PostgreSQL session variable for RLS enforcement
3. ✅ Update Pydantic response models to include `organization_id`
4. ✅ Use `TenantAwareQuery` helper for automatic filtering
5. ✅ Extract `organization_id` from authenticated user context

---

## Table of Contents

1. [Core Patterns](#core-patterns)
2. [Dependency Injection Updates](#dependency-injection-updates)
3. [Endpoint Update Examples](#endpoint-update-examples)
4. [Pydantic Model Updates](#pydantic-model-updates)
5. [Testing Updated Endpoints](#testing-updated-endpoints)
6. [Migration Checklist](#migration-checklist)

---

## Core Patterns

### Pattern 1: Extract Organization from Current User

**File:** `apps/backend/core/deps.py`

```python
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from apps.backend.core.auth import get_current_user
from database.models import User

def get_current_organization_id(
    current_user: User = Depends(get_current_user)
) -> UUID:
    """
    Extract organization_id from authenticated user

    Raises:
        HTTPException: If user does not belong to an organization
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization to access this resource"
        )

    return current_user.organization_id


def set_organization_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UUID:
    """
    Set organization context for RLS policies and return organization_id

    Sets PostgreSQL session variable: app.current_organization_id
    This enables Row Level Security policies to filter data automatically
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization"
        )

    # Set PostgreSQL session variable for RLS
    db.execute(
        f"SET app.current_organization_id = '{current_user.organization_id}'"
    )

    return current_user.organization_id
```

### Pattern 2: Using TenantAwareQuery Helper

```python
from uuid import UUID
from fastapi import APIRouter, Depends, Query as FastAPIQuery
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from database.tenant_aware_query import TenantAwareQuery
from database.models.agent_models import AgentInstance
from apps.backend.core.deps import get_current_organization_id

router = APIRouter()

@router.get("/agents/instances", response_model=List[AgentInstanceResponse])
def list_agent_instances(
    organization_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_db),
    status: Optional[str] = FastAPIQuery(None),
    agent_type: Optional[str] = FastAPIQuery(None),
    limit: int = FastAPIQuery(100, le=1000)
):
    """
    List agent instances for current organization

    Automatically filtered by organization_id from authenticated user
    """
    # Create tenant-aware query
    query = TenantAwareQuery(db, AgentInstance, organization_id)

    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if agent_type:
        query = query.filter_by(agent_type=agent_type)

    # Execute with limit
    agents = query.limit(limit).all()

    return agents
```

### Pattern 3: Manual Organization Filtering

```python
@router.get("/agents/instances", response_model=List[AgentInstanceResponse])
def list_agent_instances(
    organization_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_db)
):
    """List agent instances - manual filtering approach"""

    agents = db.query(AgentInstance).filter_by(
        organization_id=organization_id  # CRITICAL: Always include this
    ).all()

    return agents
```

### Pattern 4: Create with Organization Context

```python
from pydantic import BaseModel

class AgentInstanceCreate(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    # NOTE: Do NOT include organization_id in create model
    # It will be set from authenticated user context

@router.post("/agents/instances", response_model=AgentInstanceResponse)
def create_agent_instance(
    data: AgentInstanceCreate,
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create agent instance - automatically assigned to user's organization"""

    agent = AgentInstance(
        agent_id=data.agent_id,
        agent_type=data.agent_type,
        status=data.status,
        organization_id=organization_id,  # Set from current user
        created_by_id=current_user.id     # Audit trail
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent
```

### Pattern 5: Update with Organization Validation

```python
@router.patch("/agents/instances/{agent_id}", response_model=AgentInstanceResponse)
def update_agent_instance(
    agent_id: str,
    data: AgentInstanceUpdate,
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update agent instance - validates ownership"""

    # Query with organization filter
    agent = TenantAwareQuery(db, AgentInstance, organization_id).filter_by(
        agent_id=agent_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found in your organization"
        )

    # Update fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(agent, field, value)

    agent.updated_by_id = current_user.id  # Audit trail

    db.commit()
    db.refresh(agent)

    return agent
```

### Pattern 6: Delete with Organization Validation

```python
@router.delete("/agents/instances/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_instance(
    agent_id: str,
    organization_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_db)
):
    """Delete agent instance - validates ownership"""

    # Query with organization filter
    agent = TenantAwareQuery(db, AgentInstance, organization_id).filter_by(
        agent_id=agent_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found in your organization"
        )

    # Soft delete (set deleted_at) or hard delete
    agent.deleted_at = datetime.utcnow()  # Soft delete
    # OR: db.delete(agent)  # Hard delete

    db.commit()

    return None
```

---

## Dependency Injection Updates

### Update Authentication Dependencies

**File:** `apps/backend/core/deps.py`

```python
from typing import Generator
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from apps.backend.core.auth import get_current_user
from database.models import User

def get_db_with_org_context() -> Generator:
    """
    Get database session with organization context set

    Combines get_db() and set_organization_context() for convenience
    """
    db = next(get_db())
    try:
        current_user = get_current_user()
        if current_user and current_user.organization_id:
            db.execute(
                f"SET app.current_organization_id = '{current_user.organization_id}'"
            )
        yield db
    finally:
        db.close()


def verify_organization_access(
    resource_org_id: UUID,
    current_org_id: UUID = Depends(get_current_organization_id)
) -> bool:
    """
    Verify user has access to resource in specific organization

    Use when resource organization_id comes from path parameter
    """
    if resource_org_id != current_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization's resources"
        )
    return True
```

---

## Endpoint Update Examples

### Example 1: Agent Instances Endpoints

**File:** `apps/backend/api/v1/endpoints/agents.py`

```python
from fastapi import APIRouter, Depends, Query as FastAPIQuery, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from database.connection import get_db
from database.tenant_aware_query import TenantAwareQuery
from database.models.agent_models import AgentInstance
from apps.backend.core.deps import get_current_organization_id, get_current_user
from database.models import User

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/instances", response_model=List[AgentInstanceResponse])
def list_agent_instances(
    organization_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_db),
    agent_type: Optional[str] = FastAPIQuery(None),
    status: Optional[str] = FastAPIQuery(None),
    limit: int = FastAPIQuery(100, le=1000),
    offset: int = FastAPIQuery(0, ge=0)
):
    """List all agent instances for current organization"""

    query = TenantAwareQuery(db, AgentInstance, organization_id)

    if agent_type:
        query = query.filter_by(agent_type=agent_type)
    if status:
        query = query.filter_by(status=status)

    agents = query.limit(limit).offset(offset).all()

    return agents


@router.get("/instances/{agent_id}", response_model=AgentInstanceResponse)
def get_agent_instance(
    agent_id: str,
    organization_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_db)
):
    """Get specific agent instance"""

    agent = TenantAwareQuery(db, AgentInstance, organization_id).filter_by(
        agent_id=agent_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return agent


@router.post("/instances", response_model=AgentInstanceResponse, status_code=status.HTTP_201_CREATED)
def create_agent_instance(
    data: AgentInstanceCreate,
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new agent instance"""

    # Check if agent_id already exists in this organization
    existing = TenantAwareQuery(db, AgentInstance, organization_id).filter_by(
        agent_id=data.agent_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with ID {data.agent_id} already exists in your organization"
        )

    agent = AgentInstance(
        **data.dict(),
        organization_id=organization_id,
        created_by_id=current_user.id
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent
```

### Example 2: Roblox Environments Endpoints

**File:** `apps/backend/api/v1/endpoints/roblox_environment.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database.connection import get_db
from database.tenant_aware_query import TenantAwareQuery
from database.models.roblox_models import RobloxEnvironment
from apps.backend.core.deps import get_current_organization_id, get_current_user

router = APIRouter(prefix="/roblox", tags=["roblox"])


@router.get("/environments", response_model=List[RobloxEnvironmentResponse])
def list_roblox_environments(
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List Roblox environments for current organization"""

    # Show only environments user has access to
    environments = TenantAwareQuery(db, RobloxEnvironment, organization_id).filter_by(
        user_id=current_user.id  # User can only see their own environments
    ).all()

    return environments


@router.post("/environments", response_model=RobloxEnvironmentResponse, status_code=status.HTTP_201_CREATED)
def create_roblox_environment(
    data: RobloxEnvironmentCreate,
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new Roblox environment"""

    environment = RobloxEnvironment(
        user_id=current_user.id,
        name=data.name,
        place_id=data.place_id,
        organization_id=organization_id
    )

    db.add(environment)
    db.commit()
    db.refresh(environment)

    return environment
```

### Example 3: Customer/Payment Endpoints

**File:** `apps/backend/api/v1/endpoints/customers.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from database.connection import get_db
from database.tenant_aware_query import TenantAwareQuery
from database.models.payment import Customer, Subscription
from apps/backend.core.deps import get_current_organization_id, get_current_user

router = APIRouter(prefix="/customers", tags=["payments"])


@router.get("/me", response_model=CustomerResponse)
def get_current_customer(
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer record for current user"""

    customer = TenantAwareQuery(db, Customer, organization_id).filter_by(
        user_id=current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found"
        )

    return customer


@router.get("/me/subscriptions", response_model=List[SubscriptionResponse])
def get_current_customer_subscriptions(
    organization_id: UUID = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscriptions for current customer"""

    # First get customer
    customer = TenantAwareQuery(db, Customer, organization_id).filter_by(
        user_id=current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found"
        )

    # Get subscriptions
    subscriptions = TenantAwareQuery(db, Subscription, organization_id).filter_by(
        customer_id=customer.id
    ).all()

    return subscriptions
```

---

## Pydantic Model Updates

### Add organization_id to Response Models

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class AgentInstanceResponse(BaseModel):
    """Response model for AgentInstance"""

    id: UUID
    agent_id: str
    agent_type: str
    status: str
    organization_id: UUID  # NEW: Include in responses
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2


class RobloxEnvironmentResponse(BaseModel):
    """Response model for RobloxEnvironment"""

    id: int
    name: str
    place_id: str
    user_id: int
    organization_id: UUID  # NEW: Include in responses
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerResponse(BaseModel):
    """Response model for Customer"""

    id: int
    user_id: int
    stripe_customer_id: str
    email: str
    organization_id: UUID  # NEW: Include in responses

    class Config:
        from_attributes = True
```

### Do NOT Include organization_id in Create Models

```python
class AgentInstanceCreate(BaseModel):
    """Create model for AgentInstance"""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    status: str = Field(default="IDLE", description="Initial status")
    configuration: Optional[dict] = None

    # DO NOT include organization_id
    # It will be set from authenticated user context


class RobloxEnvironmentCreate(BaseModel):
    """Create model for RobloxEnvironment"""

    name: str
    place_id: str
    description: Optional[str] = None

    # DO NOT include organization_id or user_id
    # Both will be set from authenticated user context
```

---

## Testing Updated Endpoints

### Unit Test Example

```python
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from apps.backend.main import app
from database.models import Organization, User, AgentInstance

def test_list_agent_instances_filtered_by_organization(
    client: TestClient,
    test_organizations: tuple[Organization, Organization],
    test_users: tuple[User, User],
    db_session
):
    """Test agent instances are filtered by organization"""

    org1, org2 = test_organizations
    user1, user2 = test_users

    # Create agents in different organizations
    agent1 = AgentInstance(
        id=uuid4(),
        agent_id="org1-agent",
        agent_type="CONTENT_GENERATOR",
        status="IDLE",
        organization_id=org1.id
    )
    agent2 = AgentInstance(
        id=uuid4(),
        agent_id="org2-agent",
        agent_type="CONTENT_GENERATOR",
        status="IDLE",
        organization_id=org2.id
    )
    db_session.add_all([agent1, agent2])
    db_session.commit()

    # User1 should only see org1 agents
    response = client.get(
        "/api/v1/agents/instances",
        headers={"Authorization": f"Bearer {user1.token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["agent_id"] == "org1-agent"
    assert data[0]["organization_id"] == str(org1.id)


def test_create_agent_assigned_to_user_organization(
    client: TestClient,
    test_user: User,
    db_session
):
    """Test created agent is assigned to user's organization"""

    response = client.post(
        "/api/v1/agents/instances",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={
            "agent_id": "new-agent",
            "agent_type": "CONTENT_GENERATOR",
            "status": "IDLE"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["organization_id"] == str(test_user.organization_id)


def test_user_cannot_access_other_organization_agent(
    client: TestClient,
    test_organizations: tuple[Organization, Organization],
    test_users: tuple[User, User],
    db_session
):
    """Test user cannot access agent from different organization"""

    org1, org2 = test_organizations
    user1, user2 = test_users

    # Create agent in org2
    agent = AgentInstance(
        id=uuid4(),
        agent_id="org2-restricted",
        agent_type="CONTENT_GENERATOR",
        status="IDLE",
        organization_id=org2.id
    )
    db_session.add(agent)
    db_session.commit()

    # User1 (from org1) tries to access org2's agent
    response = client.get(
        f"/api/v1/agents/instances/{agent.agent_id}",
        headers={"Authorization": f"Bearer {user1.token}"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### Integration Test with RLS

```python
def test_rls_policies_enforce_organization_isolation(
    db_session,
    test_organizations: tuple[Organization, Organization],
    test_users: tuple[User, User]
):
    """Test PostgreSQL RLS policies enforce isolation"""

    org1, org2 = test_organizations
    user1, user2 = test_users

    # Create test data
    agent1 = AgentInstance(
        id=uuid4(),
        agent_id="rls-test-org1",
        agent_type="CONTENT_GENERATOR",
        status="IDLE",
        organization_id=org1.id
    )
    agent2 = AgentInstance(
        id=uuid4(),
        agent_id="rls-test-org2",
        agent_type="CONTENT_GENERATOR",
        status="IDLE",
        organization_id=org2.id
    )
    db_session.add_all([agent1, agent2])
    db_session.commit()

    # Set org1 context
    db_session.execute(f"SET app.current_organization_id = '{org1.id}'")

    # Should only see org1 data
    agents = db_session.query(AgentInstance).all()
    assert len(agents) == 1
    assert agents[0].agent_id == "rls-test-org1"

    # Set org2 context
    db_session.execute(f"SET app.current_organization_id = '{org2.id}'")

    # Should only see org2 data
    agents = db_session.query(AgentInstance).all()
    assert len(agents) == 1
    assert agents[0].agent_id == "rls-test-org2"

    # Reset context
    db_session.execute("RESET app.current_organization_id")
```

---

## Migration Checklist

### Phase 1: Update Core Dependencies

- [ ] Update `apps/backend/core/deps.py` with organization helpers
  - [ ] Add `get_current_organization_id()` function
  - [ ] Add `set_organization_context()` function
  - [ ] Add `verify_organization_access()` function

### Phase 2: Update Endpoint Modules

#### Agent Endpoints (`apps/backend/api/v1/endpoints/agents.py`)

- [ ] Add `organization_id` dependency to all endpoints
- [ ] Update list endpoint with `TenantAwareQuery`
- [ ] Update get endpoint with organization filter
- [ ] Update create endpoint to set `organization_id`
- [ ] Update update endpoint with ownership validation
- [ ] Update delete endpoint with ownership validation

#### Roblox Endpoints (`apps/backend/api/v1/endpoints/roblox_environment.py`)

- [ ] Add `organization_id` dependency to all endpoints
- [ ] Update environment list with tenant filtering
- [ ] Update environment create to set `organization_id`
- [ ] Update session endpoints with organization filter
- [ ] Update share endpoints with organization validation

#### Payment Endpoints (`apps/backend/api/v1/endpoints/stripe_*.py`)

- [ ] Add `organization_id` dependency to all endpoints
- [ ] Update customer endpoints with tenant filtering
- [ ] Update subscription endpoints with organization filter
- [ ] Update payment method endpoints with organization validation
- [ ] Update invoice endpoints with tenant filtering

#### Content Endpoints (`apps/backend/api/v1/endpoints/content.py`)

- [ ] Add `organization_id` dependency to all endpoints
- [ ] Update content generation with tenant filtering
- [ ] Update content feedback with organization filter
- [ ] Update learning profile endpoints with organization validation

### Phase 3: Update Pydantic Models

- [ ] Add `organization_id: UUID` to all response models
- [ ] Remove `organization_id` from all create/update models
- [ ] Update OpenAPI documentation

### Phase 4: Update Tests

- [ ] Add organization isolation tests for each endpoint
- [ ] Test cross-organization access is blocked
- [ ] Test RLS policy enforcement
- [ ] Update existing tests with organization context

### Phase 5: Documentation

- [ ] Update API documentation with organization requirements
- [ ] Document authentication flow with organization context
- [ ] Update developer guide with multi-tenant patterns
- [ ] Create runbook for troubleshooting organization issues

---

## Rollout Strategy

### Step 1: Update Dependencies (30 min)

1. Update `apps/backend/core/deps.py`
2. Test dependency functions work correctly
3. Deploy to staging

### Step 2: Update Endpoints in Batches (2-4 hours)

**Batch 1: Agent Endpoints** (1 hour)
- Update all agent-related endpoints
- Test thoroughly
- Deploy to staging

**Batch 2: Roblox Endpoints** (1 hour)
- Update all Roblox-related endpoints
- Test thoroughly
- Deploy to staging

**Batch 3: Payment Endpoints** (1 hour)
- Update all payment-related endpoints
- Test thoroughly
- Deploy to staging

**Batch 4: Content Endpoints** (1 hour)
- Update all content-related endpoints
- Test thoroughly
- Deploy to staging

### Step 3: Update Tests (2-3 hours)

- Update all existing tests
- Add new organization isolation tests
- Ensure 100% test pass rate

### Step 4: Production Deployment (1 hour)

- Deploy all updates to production
- Monitor error logs
- Verify organization filtering works

---

## Success Criteria

### Functional Requirements

- [ ] All endpoints include `organization_id` in queries
- [ ] Users can only access their organization's data
- [ ] Cross-organization access is blocked (returns 404)
- [ ] RLS policies enforce isolation at database level
- [ ] Response models include `organization_id`

### Security Requirements

- [ ] No cross-organization data leakage
- [ ] All queries filtered by `organization_id`
- [ ] Session variable set for RLS enforcement
- [ ] Audit trail preserved (created_by_id, updated_by_id)

### Performance Requirements

- [ ] Query performance within acceptable range (<200ms p95)
- [ ] Indexes used for organization filtering
- [ ] No full table scans on multi-tenant queries

---

**Document Version:** 1.0
**Last Updated:** 2025-10-10
**Review Status:** Ready for Implementation
**Maintainer:** Backend Team

---

*This guide provides comprehensive patterns for updating API endpoints to work with multi-tenant data isolation. Follow the migration checklist to ensure all endpoints are properly updated.*
