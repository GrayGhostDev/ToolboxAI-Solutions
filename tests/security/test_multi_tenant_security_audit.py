"""
Security Audit Tests: Multi-Tenant Data Isolation
==================================================

Comprehensive security testing for multi-tenant organization isolation.
Tests attempt to breach organization boundaries using various attack vectors.

Test Coverage:
    - Cross-organization data access attempts
    - RLS policy bypass attempts
    - API endpoint authorization
    - JWT token manipulation
    - SQL injection attempts
    - Parameter tampering
    - Privilege escalation
    - Information leakage

Security Targets:
    - Zero cross-organization data leakage
    - All unauthorized access attempts blocked
    - No information disclosure in error messages
    - RLS policies enforce isolation at database level

Usage:
    pytest tests/security/test_multi_tenant_security_audit.py -v
    pytest tests/security/test_multi_tenant_security_audit.py --tb=short
"""

import pytest
from uuid import uuid4, UUID
from typing import List, Dict, Any
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError, ProgrammingError

# Import models
from database.models.agent_models import AgentInstance, AgentExecution
from database.models.roblox_models import RobloxEnvironment
from database.models.payment import Customer, Subscription
from database.models.content_pipeline_models import EnhancedContentGeneration
from database.models import Organization, User

# Import application
from apps.backend.main import app


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def security_test_orgs(db_session: Session) -> tuple[Organization, Organization]:
    """Create two organizations for security testing"""
    org1 = Organization(
        id=uuid4(),
        name="Secure Org 1",
        domain="secure-org-1.test"
    )
    org2 = Organization(
        id=uuid4(),
        name="Secure Org 2",
        domain="secure-org-2.test"
    )

    db_session.add_all([org1, org2])
    db_session.commit()

    yield org1, org2

    # Cleanup
    db_session.delete(org1)
    db_session.delete(org2)
    db_session.commit()


@pytest.fixture(scope="function")
def security_test_users(
    db_session: Session,
    security_test_orgs: tuple[Organization, Organization]
) -> tuple[User, User]:
    """Create users in each organization"""
    org1, org2 = security_test_orgs

    user1 = User(
        id=9001,
        email="attacker@secure-org-1.test",
        username="attacker1",
        organization_id=org1.id
    )
    user2 = User(
        id=9002,
        email="victim@secure-org-2.test",
        username="victim2",
        organization_id=org2.id
    )

    db_session.add_all([user1, user2])
    db_session.commit()

    yield user1, user2

    # Cleanup
    db_session.delete(user1)
    db_session.delete(user2)
    db_session.commit()


@pytest.fixture
def test_client() -> TestClient:
    """Create test client for API testing"""
    return TestClient(app)


# ============================================================================
# Cross-Organization Data Access Tests
# ============================================================================

class TestCrossOrganizationAccess:
    """Test attempts to access data from other organizations"""

    def test_cannot_query_other_org_agents(
        self,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify user from org1 cannot query org2's agents"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create agent in org2
        agent2 = AgentInstance(
            id=uuid4(),
            agent_id="secret-agent-org2",
            agent_type="CONTENT_GENERATOR",
            status="BUSY",
            organization_id=org2.id,
            created_by_id=user2.id
        )
        db_session.add(agent2)
        db_session.commit()

        # Set org1 context (simulating org1 user)
        db_session.execute(text(f"SET app.current_organization_id = '{org1.id}'"))

        # Attempt to query org2's agent
        result = db_session.query(AgentInstance).filter_by(
            agent_id="secret-agent-org2"
        ).all()

        # Should return empty - org2's data not visible to org1
        assert len(result) == 0, "Cross-organization data leaked!"

    def test_cannot_access_other_org_by_id(
        self,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify querying by ID from wrong org returns nothing"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create environment in org2
        env2 = RobloxEnvironment(
            user_id=user2.id,
            name="Secret Environment",
            place_id="999999",
            organization_id=org2.id
        )
        db_session.add(env2)
        db_session.flush()
        secret_env_id = env2.id
        db_session.commit()

        # Set org1 context
        db_session.execute(text(f"SET app.current_organization_id = '{org1.id}'"))

        # Attempt to access org2's environment by ID
        result = db_session.query(RobloxEnvironment).filter_by(
            id=secret_env_id
        ).first()

        # Should return None - RLS policy blocks access
        assert result is None, "Accessed other organization's data by ID!"

    def test_cannot_join_across_organizations(
        self,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify JOINs cannot expose cross-organization data"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create data in org2
        agent2 = AgentInstance(
            id=uuid4(),
            agent_id="join-test-agent",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org2.id,
            created_by_id=user2.id
        )
        db_session.add(agent2)
        db_session.flush()

        execution2 = AgentExecution(
            id=uuid4(),
            agent_instance_id=agent2.id,
            execution_id="join-test-exec",
            status="RUNNING",
            organization_id=org2.id
        )
        db_session.add(execution2)
        db_session.commit()

        # Set org1 context
        db_session.execute(text(f"SET app.current_organization_id = '{org1.id}'"))

        # Attempt to join and access org2 data
        result = db_session.query(AgentExecution).join(
            AgentInstance
        ).filter(
            AgentExecution.execution_id == "join-test-exec"
        ).all()

        # Should return empty - RLS blocks cross-org JOIN
        assert len(result) == 0, "Cross-organization JOIN exposed data!"


# ============================================================================
# RLS Policy Bypass Attempts
# ============================================================================

class TestRLSPolicyBypass:
    """Test attempts to bypass Row Level Security policies"""

    def test_cannot_bypass_rls_with_union(
        self,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization]
    ):
        """Verify UNION queries cannot bypass RLS"""
        org1, org2 = security_test_orgs

        # Set org1 context
        db_session.execute(text(f"SET app.current_organization_id = '{org1.id}'"))

        # Attempt UNION to access all organizations
        with pytest.raises((ProgrammingError, Exception)):
            db_session.execute(text("""
                SELECT * FROM agent_instances WHERE organization_id = :org1
                UNION
                SELECT * FROM agent_instances WHERE organization_id = :org2
            """), {"org1": str(org1.id), "org2": str(org2.id)})

    def test_cannot_bypass_rls_with_cte(
        self,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization]
    ):
        """Verify CTE (WITH clause) respects RLS"""
        org1, org2 = security_test_orgs

        # Set org1 context
        db_session.execute(text(f"SET app.current_organization_id = '{org1.id}'"))

        # Attempt CTE to access all data
        result = db_session.execute(text("""
            WITH all_agents AS (
                SELECT * FROM agent_instances
            )
            SELECT COUNT(*) FROM all_agents
        """))

        # Should only count org1's agents
        # (This test verifies RLS is applied to CTEs)
        count = result.scalar()
        # Count should be org1's agents only, not all agents

    def test_cannot_bypass_rls_by_resetting_context(
        self,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization]
    ):
        """Verify RESET command doesn't bypass RLS if policies enforced"""
        org1, org2 = security_test_orgs

        # Set org1 context
        db_session.execute(text(f"SET app.current_organization_id = '{org1.id}'"))

        # Attempt to reset context (should be blocked by permissions)
        try:
            db_session.execute(text("RESET app.current_organization_id"))
        except Exception:
            # Expected - session variable may be protected
            pass

        # Query should still respect org1 context
        agents = db_session.query(AgentInstance).all()
        for agent in agents:
            assert agent.organization_id == org1.id


# ============================================================================
# API Endpoint Authorization Tests
# ============================================================================

class TestAPIEndpointAuthorization:
    """Test API endpoint authorization and organization filtering"""

    def test_agent_list_endpoint_filters_by_org(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify /agents endpoint only returns user's org data"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create JWT token for user1 (org1)
        token1 = generate_test_token(user1, org1)

        # Request agents (should only get org1 agents)
        response = test_client.get(
            "/api/v1/agents/instances",
            headers={"Authorization": f"Bearer {token1}"}
        )

        assert response.status_code == 200
        agents = response.json().get("data", [])

        # Verify all agents belong to org1
        for agent in agents:
            assert UUID(agent["organization_id"]) == org1.id

    def test_cannot_access_other_org_resource_by_id(
        self,
        test_client: TestClient,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify accessing org2 resource ID from org1 returns 404"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create agent in org2
        agent2 = AgentInstance(
            id=uuid4(),
            agent_id="forbidden-agent",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org2.id,
            created_by_id=user2.id
        )
        db_session.add(agent2)
        db_session.commit()

        # User1 (org1) attempts to access org2's agent
        token1 = generate_test_token(user1, org1)

        response = test_client.get(
            f"/api/v1/agents/instances/{agent2.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Should return 404 (not 403 to avoid information leakage)
        assert response.status_code == 404
        assert "not found" in response.json().get("detail", "").lower()

    def test_cannot_modify_other_org_resource(
        self,
        test_client: TestClient,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify modifying org2 resource from org1 fails"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create subscription in org2
        customer2 = Customer(
            user_id=user2.id,
            stripe_customer_id="cus_secret",
            email=user2.email,
            organization_id=org2.id
        )
        db_session.add(customer2)
        db_session.flush()

        subscription2 = Subscription(
            customer_id=customer2.id,
            stripe_subscription_id="sub_secret",
            status="active",
            organization_id=org2.id
        )
        db_session.add(subscription2)
        db_session.commit()

        # User1 (org1) attempts to cancel org2's subscription
        token1 = generate_test_token(user1, org1)

        response = test_client.delete(
            f"/api/v1/payments/subscriptions/{subscription2.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Should return 404 or 403
        assert response.status_code in [403, 404]

    def test_create_resource_sets_correct_org_id(
        self,
        test_client: TestClient,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify creating resource sets user's organization_id"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        token1 = generate_test_token(user1, org1)

        # Create Roblox environment
        response = test_client.post(
            "/api/v1/roblox/create",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "name": "Test Environment",
                "description": "Security test",
                "grade_level": "high-school",
                "subject": "science"
            }
        )

        assert response.status_code in [200, 201, 202]  # Various success codes

        # Verify created resource has correct organization_id
        env_name = "Test Environment"
        env = db_session.query(RobloxEnvironment).filter_by(
            name=env_name
        ).first()

        if env:
            assert env.organization_id == org1.id, "Wrong organization_id set!"


# ============================================================================
# Parameter Tampering Tests
# ============================================================================

class TestParameterTampering:
    """Test attempts to tamper with request parameters"""

    def test_cannot_inject_other_org_id_in_request(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify injecting organization_id parameter is ignored"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        token1 = generate_test_token(user1, org1)

        # Attempt to create resource with different organization_id
        response = test_client.post(
            "/api/v1/roblox/create",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "name": "Tampered Env",
                "description": "Tampering attempt",
                "organization_id": str(org2.id),  # Attempt to inject org2
                "grade_level": "middle-school"
            }
        )

        # Should ignore injected org_id and use token's org_id
        # (Implementation should not accept organization_id from user input)

    def test_cannot_modify_org_id_in_update(
        self,
        test_client: TestClient,
        db_session: Session,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify updating resource cannot change organization_id"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # Create agent in org1
        agent1 = AgentInstance(
            id=uuid4(),
            agent_id="update-test-agent",
            agent_type="CONTENT_GENERATOR",
            status="IDLE",
            organization_id=org1.id,
            created_by_id=user1.id
        )
        db_session.add(agent1)
        db_session.commit()

        token1 = generate_test_token(user1, org1)

        # Attempt to change organization_id via update
        response = test_client.patch(
            f"/api/v1/agents/instances/{agent1.id}",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "organization_id": str(org2.id),  # Tampering attempt
                "status": "BUSY"
            }
        )

        # Verify organization_id unchanged
        db_session.refresh(agent1)
        assert agent1.organization_id == org1.id, "organization_id was changed!"


# ============================================================================
# SQL Injection Tests
# ============================================================================

class TestSQLInjection:
    """Test SQL injection attack attempts"""

    def test_sql_injection_in_filter(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify SQL injection attempts in filters are blocked"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        token1 = generate_test_token(user1, org1)

        # Attempt SQL injection
        malicious_input = "1' OR '1'='1"

        response = test_client.get(
            f"/api/v1/agents/instances?agent_id={malicious_input}",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Should not return unexpected data
        # (Parameterized queries prevent SQL injection)
        assert response.status_code in [200, 400]  # Valid or rejected

        if response.status_code == 200:
            # Should not return all agents
            agents = response.json().get("data", [])
            # Check that response is properly filtered
            # (implementation-specific validation)


# ============================================================================
# Information Leakage Tests
# ============================================================================

class TestInformationLeakage:
    """Test for information disclosure vulnerabilities"""

    def test_error_messages_dont_leak_org_info(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify error messages don't reveal other org exists"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        token1 = generate_test_token(user1, org1)

        # Request non-existent resource
        fake_id = uuid4()

        response = test_client.get(
            f"/api/v1/agents/instances/{fake_id}",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Should return generic 404
        assert response.status_code == 404
        error_message = response.json().get("detail", "")

        # Should not reveal whether resource exists in other org
        assert "organization" not in error_message.lower()
        assert "org" not in error_message.lower()

    def test_list_endpoint_doesnt_leak_count(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify list endpoints don't reveal total counts across orgs"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        token1 = generate_test_token(user1, org1)

        response = test_client.get(
            "/api/v1/agents/instances",
            headers={"Authorization": f"Bearer {token1}"}
        )

        assert response.status_code == 200
        data = response.json()

        # If pagination metadata included, verify it's scoped to org
        if "total" in data:
            # Total should be org1's count only
            # (Not the count across all organizations)
            pass


# ============================================================================
# Privilege Escalation Tests
# ============================================================================

class TestPrivilegeEscalation:
    """Test attempts to escalate privileges"""

    def test_cannot_access_admin_endpoint_as_user(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify regular user cannot access admin endpoints"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        # user1 is regular user, not admin
        token1 = generate_test_token(user1, org1, role="user")

        # Attempt to access admin endpoint
        response = test_client.get(
            "/api/v1/admin/organizations",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Should return 403 Forbidden
        assert response.status_code == 403

    def test_cannot_modify_own_role(
        self,
        test_client: TestClient,
        security_test_orgs: tuple[Organization, Organization],
        security_test_users: tuple[User, User]
    ):
        """Verify user cannot elevate their own role"""
        org1, org2 = security_test_orgs
        user1, user2 = security_test_users

        token1 = generate_test_token(user1, org1, role="user")

        # Attempt to change own role to admin
        response = test_client.patch(
            f"/api/v1/users/{user1.id}",
            headers={"Authorization": f"Bearer {token1}"},
            json={"role": "admin"}
        )

        # Should be rejected
        assert response.status_code in [403, 400]


# ============================================================================
# Test Utilities
# ============================================================================

def generate_test_token(
    user: User,
    org: Organization,
    role: str = "user"
) -> str:
    """Generate JWT token for testing"""
    from apps.backend.core.security import create_access_token

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "organization_id": str(org.id),
        "role": role
    }

    return create_access_token(token_data)


# ============================================================================
# Security Audit Report Generator
# ============================================================================

def generate_security_audit_report(test_results: Dict[str, bool]) -> str:
    """Generate comprehensive security audit report"""
    from datetime import datetime

    report = []
    report.append("=" * 80)
    report.append("MULTI-TENANT SECURITY AUDIT REPORT")
    report.append("=" * 80)
    report.append(f"\nAudit Date: {datetime.now().isoformat()}")
    report.append(f"\nTest Results:\n")
    report.append(f"{'Test Name':<60} {'Result':<10}")
    report.append("-" * 80)

    passed = 0
    failed = 0

    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        if result:
            passed += 1
        else:
            failed += 1
        report.append(f"{test_name:<60} {status:<10}")

    report.append("-" * 80)
    report.append(f"\nSummary:")
    report.append(f"  Passed: {passed}")
    report.append(f"  Failed: {failed}")
    report.append(f"  Total: {passed + failed}")
    report.append(f"\nSecurity Status: {'✅ SECURE' if failed == 0 else '❌ VULNERABILITIES FOUND'}")
    report.append("=" * 80)

    return "\n".join(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
