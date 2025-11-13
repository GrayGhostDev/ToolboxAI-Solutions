"""
Integration Tests for Multi-Tenant API Isolation

Tests that verify organization-scoped data isolation across all API endpoints.
Each test creates resources for multiple organizations and verifies that:
1. Users can only access their own organization's data
2. Attempts to access other organizations' data fail with 403/404
3. RLS policies are enforced at database level
4. Audit trails are properly maintained

Run with: pytest tests/integration/test_multi_tenant_api_isolation.py -v
"""

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.main import app
from database.models.agent_models import AgentInstance
from database.models.content_pipeline_models import ContentGeneration
from database.models.models import User
from database.models.payment import Subscription
from database.models.roblox_models import RobloxEnvironment

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def org_a_id() -> UUID:
    """Organization A UUID"""
    return uuid4()


@pytest.fixture
async def org_b_id() -> UUID:
    """Organization B UUID"""
    return uuid4()


@pytest.fixture
async def user_org_a(db_session: AsyncSession, org_a_id: UUID) -> User:
    """User belonging to Organization A"""
    user = User(
        id=uuid4(),
        email="user_a@orga.com",
        username="user_a",
        organization_id=org_a_id,
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_org_b(db_session: AsyncSession, org_b_id: UUID) -> User:
    """User belonging to Organization B"""
    user = User(
        id=uuid4(),
        email="user_b@orgb.com",
        username="user_b",
        organization_id=org_b_id,
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_token_org_a(user_org_a: User) -> str:
    """JWT token for Organization A user"""
    from apps.backend.core.auth import create_access_token

    return create_access_token(
        {"sub": str(user_org_a.id), "organization_id": str(user_org_a.organization_id)}
    )


@pytest.fixture
async def auth_token_org_b(user_org_b: User) -> str:
    """JWT token for Organization B user"""
    from apps.backend.core.auth import create_access_token

    return create_access_token(
        {"sub": str(user_org_b.id), "organization_id": str(user_org_b.organization_id)}
    )


@pytest.fixture
async def client() -> AsyncClient:
    """HTTP client for API requests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Agent Instance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_agent_instances_organization_isolation(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """Test that agent instances are isolated by organization"""

    # Create agent instance for Organization A
    agent_a = AgentInstance(
        agent_id="agent-org-a",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    db_session.add(agent_a)

    # Create agent instance for Organization B
    agent_b = AgentInstance(
        agent_id="agent-org-b",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_b_id,
        created_by_id=user_org_b.id,
    )
    db_session.add(agent_b)
    await db_session.commit()

    # Test 1: User A can list only their organization's agents
    response = await client.get(
        "/api/v1/agent-instances",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) == 1
    assert data["agents"][0]["agent_id"] == "agent-org-a"

    # Test 2: User B can list only their organization's agents
    response = await client.get(
        "/api/v1/agent-instances",
        headers={"Authorization": f"Bearer {auth_token_org_b}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) == 1
    assert data["agents"][0]["agent_id"] == "agent-org-b"

    # Test 3: User A cannot access User B's agent
    response = await client.get(
        f"/api/v1/agent-instances/agent-org-b",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
    )
    assert response.status_code == 404  # Not found (doesn't reveal existence)

    # Test 4: User B cannot access User A's agent
    response = await client.get(
        f"/api/v1/agent-instances/agent-org-a",
        headers={"Authorization": f"Bearer {auth_token_org_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_agent_instance_creation_scoped_to_organization(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    auth_token_org_a: str,
    user_org_a: User,
):
    """Test that created agent instances are automatically scoped to current organization"""

    # Create agent via API
    response = await client.post(
        "/api/v1/agent-instances",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
        json={
            "agent_id": "new-agent",
            "agent_type": "content_reviewer",
            "configuration": {"max_tokens": 1000},
        },
    )
    assert response.status_code == 201
    data = response.json()

    # Verify organization_id is set correctly
    agent = await db_session.get(AgentInstance, data["id"])
    assert agent.organization_id == org_a_id
    assert agent.created_by_id == user_org_a.id


@pytest.mark.asyncio
async def test_agent_instance_update_prevents_cross_org_modification(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """Test that users cannot update agents from other organizations"""

    # Create agent for Organization A
    agent_a = AgentInstance(
        agent_id="agent-to-update",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    db_session.add(agent_a)
    await db_session.commit()

    # Attempt to update from Organization B (should fail)
    response = await client.put(
        f"/api/v1/agent-instances/{agent_a.agent_id}",
        headers={"Authorization": f"Bearer {auth_token_org_b}"},
        json={"status": "SUSPENDED"},
    )
    assert response.status_code in [403, 404]  # Forbidden or Not Found

    # Verify agent was not updated
    await db_session.refresh(agent_a)
    assert agent_a.status == "ACTIVE"  # Unchanged


@pytest.mark.asyncio
async def test_agent_instance_deletion_scoped_to_organization(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """Test that users cannot delete agents from other organizations"""

    # Create agent for Organization A
    agent_a = AgentInstance(
        agent_id="agent-to-delete",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    db_session.add(agent_a)
    await db_session.commit()

    # Attempt to delete from Organization B (should fail)
    response = await client.delete(
        f"/api/v1/agent-instances/{agent_a.agent_id}",
        headers={"Authorization": f"Bearer {auth_token_org_b}"},
    )
    assert response.status_code in [403, 404]

    # Verify agent still exists
    agent = await db_session.get(AgentInstance, agent_a.id)
    assert agent is not None


# ============================================================================
# Roblox Environment Tests
# ============================================================================


@pytest.mark.asyncio
async def test_roblox_environments_organization_isolation(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """Test that Roblox environments are isolated by organization"""

    # Create environment for Organization A
    env_a = RobloxEnvironment(
        id=uuid4(),
        environment_id="env-org-a",
        name="Org A Environment",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    db_session.add(env_a)

    # Create environment for Organization B
    env_b = RobloxEnvironment(
        id=uuid4(),
        environment_id="env-org-b",
        name="Org B Environment",
        organization_id=org_b_id,
        created_by_id=user_org_b.id,
    )
    db_session.add(env_b)
    await db_session.commit()

    # Test: User A can list only their organization's environments
    response = await client.get(
        "/api/v1/roblox/environments",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["environments"]) == 1
    assert data["environments"][0]["environment_id"] == "env-org-a"

    # Test: User B can list only their organization's environments
    response = await client.get(
        "/api/v1/roblox/environments",
        headers={"Authorization": f"Bearer {auth_token_org_b}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["environments"]) == 1
    assert data["environments"][0]["environment_id"] == "env-org-b"


# ============================================================================
# Content Generation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_content_generation_organization_isolation(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """Test that content generation records are isolated by organization"""

    # Create content generation for Organization A
    content_a = ContentGeneration(
        id=uuid4(),
        request_id=str(uuid4()),
        content_type="lesson",
        prompt="Teach fractions",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    db_session.add(content_a)

    # Create content generation for Organization B
    content_b = ContentGeneration(
        id=uuid4(),
        request_id=str(uuid4()),
        content_type="lesson",
        prompt="Teach algebra",
        organization_id=org_b_id,
        created_by_id=user_org_b.id,
    )
    db_session.add(content_b)
    await db_session.commit()

    # Test: User A can list only their organization's content
    response = await client.get(
        "/api/v1/content/generations",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["generations"]) == 1
    assert data["generations"][0]["prompt"] == "Teach fractions"


# ============================================================================
# Payment Tests
# ============================================================================


@pytest.mark.asyncio
async def test_subscriptions_organization_isolation(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """Test that subscriptions are isolated by organization"""

    # Create subscription for Organization A
    sub_a = Subscription(
        id=uuid4(),
        organization_id=org_a_id,
        plan_name="Pro Plan",
        status="active",
        stripe_subscription_id="sub_a",
    )
    db_session.add(sub_a)

    # Create subscription for Organization B
    sub_b = Subscription(
        id=uuid4(),
        organization_id=org_b_id,
        plan_name="Enterprise Plan",
        status="active",
        stripe_subscription_id="sub_b",
    )
    db_session.add(sub_b)
    await db_session.commit()

    # Test: User A can view only their organization's subscription
    response = await client.get(
        "/api/v1/billing/subscription",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["plan_name"] == "Pro Plan"

    # Test: User B can view only their organization's subscription
    response = await client.get(
        "/api/v1/billing/subscription",
        headers={"Authorization": f"Bearer {auth_token_org_b}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["plan_name"] == "Enterprise Plan"


# ============================================================================
# RLS Policy Tests (Database Level)
# ============================================================================


@pytest.mark.asyncio
async def test_rls_policies_enforce_isolation(
    db_session: AsyncSession,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
):
    """Test that RLS policies enforce organization isolation at database level"""

    # Create agent instances for both organizations
    agent_a = AgentInstance(
        agent_id="agent-rls-a",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    agent_b = AgentInstance(
        agent_id="agent-rls-b",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_b_id,
        created_by_id=user_org_b.id,
    )
    db_session.add_all([agent_a, agent_b])
    await db_session.commit()

    # Set RLS context for Organization A
    await db_session.execute(f"SET app.current_organization_id = '{org_a_id}'")

    # Query should only return Organization A's agents (RLS enforced)
    result = await db_session.execute(select(AgentInstance))
    agents = result.scalars().all()

    # Note: This test assumes RLS policies are enabled
    # If RLS is not enabled, this test will fail
    # In that case, the test serves as a reminder to enable RLS
    assert len(agents) <= 1  # Should see at most 1 agent (own organization)


# ============================================================================
# Audit Trail Tests
# ============================================================================


@pytest.mark.asyncio
async def test_audit_trail_tracks_organization_actions(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    user_org_a: User,
    auth_token_org_a: str,
):
    """Test that audit trails properly track created_by_id and updated_by_id"""

    # Create agent via API
    response = await client.post(
        "/api/v1/agent-instances",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
        json={
            "agent_id": "audit-test-agent",
            "agent_type": "content_generator",
            "configuration": {},
        },
    )
    assert response.status_code == 201
    data = response.json()

    # Verify audit fields are set
    agent = await db_session.get(AgentInstance, data["id"])
    assert agent.created_by_id == user_org_a.id
    assert agent.organization_id == org_a_id

    # Update agent via API
    response = await client.put(
        f"/api/v1/agent-instances/{agent.agent_id}",
        headers={"Authorization": f"Bearer {auth_token_org_a}"},
        json={"status": "SUSPENDED"},
    )
    assert response.status_code == 200

    # Verify updated_by_id is set
    await db_session.refresh(agent)
    assert agent.updated_by_id == user_org_a.id
    assert agent.status == "SUSPENDED"


# ============================================================================
# Cross-Organization Access Prevention Tests
# ============================================================================


@pytest.mark.asyncio
async def test_cross_organization_resource_access_blocked(
    db_session: AsyncSession,
    client: AsyncClient,
    org_a_id: UUID,
    org_b_id: UUID,
    user_org_a: User,
    user_org_b: User,
    auth_token_org_a: str,
    auth_token_org_b: str,
):
    """
    Comprehensive test that verifies all resource types are protected
    from cross-organization access.
    """

    # Create various resources for Organization A
    agent_a = AgentInstance(
        agent_id="protected-agent",
        agent_type="content_generator",
        status="ACTIVE",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    env_a = RobloxEnvironment(
        id=uuid4(),
        environment_id="protected-env",
        name="Protected Environment",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )
    content_a = ContentGeneration(
        id=uuid4(),
        request_id=str(uuid4()),
        content_type="quiz",
        prompt="Protected content",
        organization_id=org_a_id,
        created_by_id=user_org_a.id,
    )

    db_session.add_all([agent_a, env_a, content_a])
    await db_session.commit()

    # Attempt cross-organization access from User B (should all fail)
    endpoints_to_test = [
        f"/api/v1/agent-instances/{agent_a.agent_id}",
        f"/api/v1/roblox/environments/{env_a.environment_id}",
        f"/api/v1/content/generations/{content_a.id}",
    ]

    for endpoint in endpoints_to_test:
        response = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {auth_token_org_b}"},
        )
        assert response.status_code in [
            403,
            404,
        ], f"Endpoint {endpoint} should block cross-org access"
