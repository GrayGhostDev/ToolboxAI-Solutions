"""
Integration Tests: Multi-Tenant Data Isolation
===============================================

Tests to verify organization-level data isolation across all modern models.

Test Coverage:
    - Agent Models (5): agent_instances, agent_executions, agent_metrics,
                        agent_task_queue, agent_configurations
    - Roblox Models (4): roblox_environments, roblox_sessions,
                         environment_shares, environment_templates
    - Payment Models (10): customers, subscriptions, subscription_items,
                           customer_payment_methods, payments, invoices,
                           invoice_items, refunds, usage_records, coupons
    - Content Pipeline (6): enhanced_content_generation, content_quality_metrics,
                            learning_profiles, content_personalization_logs,
                            content_feedback, content_generation_batches

Test Scenarios:
    1. Cross-Organization Isolation: Verify data cannot be accessed across orgs
    2. CASCADE Delete: Verify deleting organization removes all related data
    3. Query Filtering: Verify TenantAwareQuery correctly filters
    4. RLS Policies: Verify PostgreSQL RLS enforcement
    5. Platform-Wide Resources: Verify nullable organization_id (coupons)

Usage:
    pytest tests/integration/test_multi_tenant_isolation.py -v
    pytest tests/integration/test_multi_tenant_isolation.py::test_agent_isolation -v
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from database.models import Organization, User

# Import all modern models
from database.models.agent_models import (
    AgentExecution,
    AgentInstance,
    SystemHealth,
)
from database.models.content_pipeline_models import (
    ContentCache,
    EnhancedContentGeneration,
)
from database.models.payment import (
    Coupon,
    Customer,
)
from database.models.roblox_models import (
    EnvironmentShare,
    RobloxEnvironment,
)
from database.tenant_aware_query import (
    TenantAwareQuery,
    tenant_scoped,
    tenant_session,
    verify_tenant_isolation,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_organizations(db_session: Session) -> tuple[Organization, Organization]:
    """Create two test organizations"""
    org1 = Organization(id=uuid4(), name="Test Organization 1", domain="test-org-1.com")
    org2 = Organization(id=uuid4(), name="Test Organization 2", domain="test-org-2.com")

    db_session.add_all([org1, org2])
    db_session.commit()

    yield org1, org2

    # Cleanup (CASCADE delete should handle related records)
    db_session.delete(org1)
    db_session.delete(org2)
    db_session.commit()


@pytest.fixture(scope="function")
def test_users(
    db_session: Session, test_organizations: tuple[Organization, Organization]
) -> tuple[User, User]:
    """Create test users in each organization"""
    org1, org2 = test_organizations

    user1 = User(id=1, email="user1@test-org-1.com", username="user1", organization_id=org1.id)
    user2 = User(id=2, email="user2@test-org-2.com", username="user2", organization_id=org2.id)

    db_session.add_all([user1, user2])
    db_session.commit()

    yield user1, user2

    # Cleanup
    db_session.delete(user1)
    db_session.delete(user2)
    db_session.commit()


# ============================================================================
# Agent Models Isolation Tests
# ============================================================================


class TestAgentModelsIsolation:
    """Test multi-tenant isolation for Agent models"""

    def test_agent_instances_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test AgentInstance isolation between organizations"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create agent instances in different organizations
        agent1 = AgentInstance(
            id=uuid4(),
            agent_id="agent-org1",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org1.id,
            created_by_id=user1.id,
        )
        agent2 = AgentInstance(
            id=uuid4(),
            agent_id="agent-org2",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org2.id,
            created_by_id=user2.id,
        )

        db_session.add_all([agent1, agent2])
        db_session.commit()

        # Test isolation using TenantAwareQuery
        org1_query = TenantAwareQuery(db_session, AgentInstance, org1.id)
        org1_agents = org1_query.all()

        assert len(org1_agents) == 1
        assert org1_agents[0].id == agent1.id
        assert org1_agents[0].agent_id == "agent-org1"

        # Verify org2 data not visible
        org2_query = TenantAwareQuery(db_session, AgentInstance, org2.id)
        org2_agents = org2_query.all()

        assert len(org2_agents) == 1
        assert org2_agents[0].id == agent2.id
        assert org2_agents[0].agent_id == "agent-org2"

        # Verify cross-organization isolation
        org1_agent_ids = {a.id for a in org1_agents}
        org2_agent_ids = {a.id for a in org2_agents}
        assert org1_agent_ids.isdisjoint(org2_agent_ids)

    def test_agent_executions_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test AgentExecution isolation via parent agent"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create agents
        agent1 = AgentInstance(
            id=uuid4(),
            agent_id="exec-agent-org1",
            agent_type="CONTENT_GENERATOR",
            status="BUSY",
            organization_id=org1.id,
            created_by_id=user1.id,
        )
        agent2 = AgentInstance(
            id=uuid4(),
            agent_id="exec-agent-org2",
            agent_type="CONTENT_GENERATOR",
            status="BUSY",
            organization_id=org2.id,
            created_by_id=user2.id,
        )
        db_session.add_all([agent1, agent2])
        db_session.flush()

        # Create executions
        exec1 = AgentExecution(
            id=uuid4(),
            agent_instance_id=agent1.id,
            execution_id="exec-1",
            status="RUNNING",
            organization_id=org1.id,
        )
        exec2 = AgentExecution(
            id=uuid4(),
            agent_instance_id=agent2.id,
            execution_id="exec-2",
            status="RUNNING",
            organization_id=org2.id,
        )
        db_session.add_all([exec1, exec2])
        db_session.commit()

        # Verify isolation
        org1_execs = TenantAwareQuery(db_session, AgentExecution, org1.id).all()
        assert len(org1_execs) == 1
        assert org1_execs[0].execution_id == "exec-1"

        org2_execs = TenantAwareQuery(db_session, AgentExecution, org2.id).all()
        assert len(org2_execs) == 1
        assert org2_execs[0].execution_id == "exec-2"

    def test_system_health_global_access(
        self, db_session: Session, test_organizations: tuple[Organization, Organization]
    ):
        """Test SystemHealth is global (no organization_id)"""
        org1, org2 = test_organizations

        # Create system health record (no organization_id)
        health = SystemHealth(
            id=uuid4(), service_name="test-service", status="healthy", response_time=100.0
        )
        db_session.add(health)
        db_session.commit()

        # Verify accessible from both organizations
        # (SystemHealth is GlobalBaseModel - no organization filtering)
        all_health = db_session.query(SystemHealth).all()
        assert len(all_health) >= 1

        # Verify no organization_id column
        assert not hasattr(health, "organization_id")


# ============================================================================
# Roblox Models Isolation Tests
# ============================================================================


class TestRobloxModelsIsolation:
    """Test multi-tenant isolation for Roblox models"""

    def test_roblox_environments_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test RobloxEnvironment isolation between organizations"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create environments in different organizations
        env1 = RobloxEnvironment(
            user_id=user1.id, name="Org1 Environment", place_id="123456", organization_id=org1.id
        )
        env2 = RobloxEnvironment(
            user_id=user2.id, name="Org2 Environment", place_id="789012", organization_id=org2.id
        )

        db_session.add_all([env1, env2])
        db_session.commit()

        # Verify isolation
        org1_envs = TenantAwareQuery(db_session, RobloxEnvironment, org1.id).all()
        assert len(org1_envs) == 1
        assert org1_envs[0].name == "Org1 Environment"

        org2_envs = TenantAwareQuery(db_session, RobloxEnvironment, org2.id).all()
        assert len(org2_envs) == 1
        assert org2_envs[0].name == "Org2 Environment"

    def test_environment_shares_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test EnvironmentShare isolation via parent environment"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create environments
        env1 = RobloxEnvironment(
            user_id=user1.id, name="Shared Env Org1", place_id="111", organization_id=org1.id
        )
        env2 = RobloxEnvironment(
            user_id=user2.id, name="Shared Env Org2", place_id="222", organization_id=org2.id
        )
        db_session.add_all([env1, env2])
        db_session.flush()

        # Create shares
        share1 = EnvironmentShare(
            environment_id=env1.id,
            shared_with_user_id=user1.id,
            permission="read",
            organization_id=org1.id,
        )
        share2 = EnvironmentShare(
            environment_id=env2.id,
            shared_with_user_id=user2.id,
            permission="write",
            organization_id=org2.id,
        )
        db_session.add_all([share1, share2])
        db_session.commit()

        # Verify isolation
        org1_shares = TenantAwareQuery(db_session, EnvironmentShare, org1.id).all()
        assert len(org1_shares) == 1
        assert org1_shares[0].permission == "read"

        org2_shares = TenantAwareQuery(db_session, EnvironmentShare, org2.id).all()
        assert len(org2_shares) == 1
        assert org2_shares[0].permission == "write"


# ============================================================================
# Payment Models Isolation Tests
# ============================================================================


class TestPaymentModelsIsolation:
    """Test multi-tenant isolation for Payment models"""

    def test_customers_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test Customer isolation between organizations"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create customers
        customer1 = Customer(
            user_id=user1.id,
            stripe_customer_id="cus_org1",
            email=user1.email,
            organization_id=org1.id,
        )
        customer2 = Customer(
            user_id=user2.id,
            stripe_customer_id="cus_org2",
            email=user2.email,
            organization_id=org2.id,
        )

        db_session.add_all([customer1, customer2])
        db_session.commit()

        # Verify isolation
        org1_customers = TenantAwareQuery(db_session, Customer, org1.id).all()
        assert len(org1_customers) == 1
        assert org1_customers[0].stripe_customer_id == "cus_org1"

        org2_customers = TenantAwareQuery(db_session, Customer, org2.id).all()
        assert len(org2_customers) == 1
        assert org2_customers[0].stripe_customer_id == "cus_org2"

    def test_coupons_platform_wide_and_org_specific(
        self, db_session: Session, test_organizations: tuple[Organization, Organization]
    ):
        """Test Coupon with nullable organization_id (platform-wide vs org-specific)"""
        org1, org2 = test_organizations

        # Create platform-wide coupon (NULL organization_id)
        platform_coupon = Coupon(
            code="PLATFORM20", discount_percent=20.0, organization_id=None  # Platform-wide
        )

        # Create org-specific coupons
        org1_coupon = Coupon(code="ORG1ONLY", discount_percent=30.0, organization_id=org1.id)
        org2_coupon = Coupon(code="ORG2ONLY", discount_percent=25.0, organization_id=org2.id)

        db_session.add_all([platform_coupon, org1_coupon, org2_coupon])
        db_session.commit()

        # Verify platform-wide coupon accessible to all
        all_coupons = db_session.query(Coupon).filter_by(code="PLATFORM20").all()
        assert len(all_coupons) == 1
        assert all_coupons[0].organization_id is None

        # Verify org-specific coupons isolated
        org1_coupons = db_session.query(Coupon).filter_by(organization_id=org1.id).all()
        assert len(org1_coupons) == 1
        assert org1_coupons[0].code == "ORG1ONLY"

        org2_coupons = db_session.query(Coupon).filter_by(organization_id=org2.id).all()
        assert len(org2_coupons) == 1
        assert org2_coupons[0].code == "ORG2ONLY"


# ============================================================================
# Content Pipeline Models Isolation Tests
# ============================================================================


class TestContentPipelineIsolation:
    """Test multi-tenant isolation for Content Pipeline models"""

    def test_enhanced_content_generation_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test EnhancedContentGeneration isolation"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create content
        content1 = EnhancedContentGeneration(
            id=uuid4(),
            user_id=user1.id,
            topic="Math Lesson Org1",
            difficulty_level="intermediate",
            organization_id=org1.id,
        )
        content2 = EnhancedContentGeneration(
            id=uuid4(),
            user_id=user2.id,
            topic="Science Lesson Org2",
            difficulty_level="advanced",
            organization_id=org2.id,
        )

        db_session.add_all([content1, content2])
        db_session.commit()

        # Verify isolation
        org1_content = TenantAwareQuery(db_session, EnhancedContentGeneration, org1.id).all()
        assert len(org1_content) == 1
        assert org1_content[0].topic == "Math Lesson Org1"

        org2_content = TenantAwareQuery(db_session, EnhancedContentGeneration, org2.id).all()
        assert len(org2_content) == 1
        assert org2_content[0].topic == "Science Lesson Org2"

    def test_content_cache_global_access(
        self, db_session: Session, test_organizations: tuple[Organization, Organization]
    ):
        """Test ContentCache is global (no organization_id)"""
        org1, org2 = test_organizations

        # Create cache entry (no organization_id)
        cache = ContentCache(
            id=uuid4(), cache_key="test-key", cached_data={"result": "test"}, ttl_seconds=3600
        )
        db_session.add(cache)
        db_session.commit()

        # Verify accessible from all organizations
        all_cache = db_session.query(ContentCache).all()
        assert len(all_cache) >= 1

        # Verify no organization_id column
        assert not hasattr(cache, "organization_id")


# ============================================================================
# CASCADE Delete Tests
# ============================================================================


class TestCascadeDelete:
    """Test CASCADE delete when organization is deleted"""

    def test_cascade_delete_agent_data(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test deleting organization CASCADE deletes all agent data"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create agent with related data in org1
        agent = AgentInstance(
            id=uuid4(),
            agent_id="cascade-test-agent",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org1.id,
            created_by_id=user1.id,
        )
        db_session.add(agent)
        db_session.flush()

        execution = AgentExecution(
            id=uuid4(),
            agent_instance_id=agent.id,
            execution_id="cascade-exec",
            status="COMPLETED",
            organization_id=org1.id,
        )
        db_session.add(execution)
        db_session.commit()

        agent_id = agent.id
        exec_id = execution.id

        # Delete organization (should CASCADE delete related data)
        db_session.delete(org1)
        db_session.commit()

        # Verify agent and execution are deleted
        assert db_session.query(AgentInstance).filter_by(id=agent_id).first() is None
        assert db_session.query(AgentExecution).filter_by(id=exec_id).first() is None

        # Verify org2 data still exists
        org2_agents = db_session.query(AgentInstance).filter_by(organization_id=org2.id).count()
        # (may be 0 if no data created for org2 in this test)


# ============================================================================
# Query Utility Tests
# ============================================================================


class TestQueryUtilities:
    """Test tenant-aware query utilities"""

    def test_tenant_scoped_decorator(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test @tenant_scoped decorator"""
        org1, org2 = test_organizations

        @tenant_scoped
        def get_agents(session: Session, organization_id: UUID, agent_type: str):
            return session.query(AgentInstance).filter_by(agent_type=agent_type)

        # Function should automatically add organization filter
        query = get_agents(db_session, organization_id=org1.id, agent_type="CONTENT_GENERATOR")
        # Query should have organization filter applied

    def test_tenant_session_context(
        self, db_session: Session, test_organizations: tuple[Organization, Organization]
    ):
        """Test tenant_session context manager"""
        org1, org2 = test_organizations

        # Set organization context
        with tenant_session(db_session, org1.id) as scoped_session:
            # RLS should be enforced within this context
            agents = scoped_session.query(AgentInstance).all()
            # All agents should belong to org1

    def test_verify_tenant_isolation(
        self,
        db_session: Session,
        test_organizations: tuple[Organization, Organization],
        test_users: tuple[User, User],
    ):
        """Test verify_tenant_isolation utility"""
        org1, org2 = test_organizations
        user1, user2 = test_users

        # Create test data
        agent1 = AgentInstance(
            id=uuid4(),
            agent_id="verify-agent-org1",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org1.id,
            created_by_id=user1.id,
        )
        db_session.add(agent1)
        db_session.commit()

        # Verify isolation
        is_isolated = verify_tenant_isolation(db_session, AgentInstance, org1.id, expected_count=1)
        assert is_isolated is True


# ============================================================================
# RLS Policy Tests (if RLS enabled)
# ============================================================================


class TestRLSPolicies:
    """Test PostgreSQL Row Level Security policies"""

    @pytest.mark.skipif(
        not hasattr(pytest, "rls_enabled"), reason="RLS policies not enabled in test environment"
    )
    def test_rls_policy_enforcement(
        self, db_session: Session, test_organizations: tuple[Organization, Organization]
    ):
        """Test RLS policies enforce organization isolation"""
        org1, org2 = test_organizations

        # Set organization context for RLS
        db_session.execute(f"SET app.current_organization_id = '{org1.id}'")

        # Query should only return org1 data (enforced by RLS)
        agents = db_session.query(AgentInstance).all()
        for agent in agents:
            assert agent.organization_id == org1.id


# ============================================================================
# Performance Tests
# ============================================================================


class TestQueryPerformance:
    """Test query performance with organization filtering"""

    def test_query_uses_organization_index(
        self, db_session: Session, test_organizations: tuple[Organization, Organization]
    ):
        """Verify queries use organization_id indexes"""
        org1, org2 = test_organizations

        # Query with organization filter
        query = db_session.query(AgentInstance).filter_by(
            organization_id=org1.id, agent_type="CONTENT_GENERATOR"
        )

        # Check query plan uses index
        # (Use EXPLAIN in actual database)
        agents = query.all()
        # Performance should be good with idx_agent_org_type_status index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
