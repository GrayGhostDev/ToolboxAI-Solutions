"""
Integration Tests: Multi-Tenant Data Isolation - Basic Verification
====================================================================

Core multi-tenant isolation tests using simplified schema.

Tests verify:
    1. Organization isolation via RLS policies
    2. Cross-organization data access prevention
    3. CASCADE delete for organization removal
    4. Query filtering with organization context

Tables Tested:
    - organizations: Master organization data
    - users: User accounts with organization_id FK
    - agent_instances: AI agents with organization_id FK
    - roblox_environments: Roblox environments with organization_id FK
    - customers: Payment customers with organization_id FK

Usage:
    pytest tests/integration/test_multi_tenant_basic.py -v
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dbuser_4qnrmosa:13y70agAhh2LSyjLw3LYtF1kRPra0qnNhdQcng6YNb0lMz5h@localhost:5434/toolboxai_6rmgje4u",
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create database session for each test"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.rollback()
    session.close()


@pytest.fixture
def test_organizations(db_session):
    """Create two test organizations"""
    org1_id = uuid4()
    org2_id = uuid4()

    # Insert organizations directly
    db_session.execute(
        text(
            """
        INSERT INTO organizations (id, name, slug, domain, is_active, created_at, updated_at)
        VALUES
            (:org1_id, 'Test Organization 1', 'test-org-1', 'test1.com', true, now(), now()),
            (:org2_id, 'Test Organization 2', 'test-org-2', 'test2.com', true, now(), now())
    """
        ),
        {"org1_id": org1_id, "org2_id": org2_id},
    )
    db_session.commit()

    yield {"org1": org1_id, "org2": org2_id}

    # Cleanup
    db_session.execute(
        text("DELETE FROM organizations WHERE id IN (:org1_id, :org2_id)"),
        {"org1_id": org1_id, "org2_id": org2_id},
    )
    db_session.commit()


@pytest.fixture
def test_users(db_session, test_organizations):
    """Create test users in each organization"""
    org1_id = test_organizations["org1"]
    org2_id = test_organizations["org2"]

    # Insert users
    result = db_session.execute(
        text(
            """
        INSERT INTO users (email, organization_id, created_at)
        VALUES
            ('user1@org1.com', :org1_id, now()),
            ('user2@org2.com', :org2_id, now())
        RETURNING id
    """
        ),
        {"org1_id": org1_id, "org2_id": org2_id},
    )

    user_ids = [row[0] for row in result]
    db_session.commit()

    yield {"user1_id": user_ids[0], "user2_id": user_ids[1]}

    # Cleanup
    db_session.execute(
        text("DELETE FROM users WHERE id IN (:id1, :id2)"), {"id1": user_ids[0], "id2": user_ids[1]}
    )
    db_session.commit()


# ============================================================================
# Organization Isolation Tests
# ============================================================================


def test_organizations_table_exists(db_session):
    """Verify organizations table exists with correct structure"""
    result = db_session.execute(
        text(
            """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'organizations'
        ORDER BY ordinal_position
    """
        )
    )

    columns = {row[0]: row[1] for row in result}

    assert "id" in columns, "organizations.id column missing"
    assert "name" in columns, "organizations.name column missing"
    assert (
        "organization_id" not in columns
    ), "organizations should not have organization_id (it's the root)"


def test_organization_isolation_policy_exists(db_session):
    """Verify RLS policy exists for organizations table"""
    result = db_session.execute(
        text(
            """
        SELECT policyname, tablename
        FROM pg_policies
        WHERE tablename = 'organizations' AND policyname = 'organizations_org_isolation'
    """
        )
    )

    policy = result.fetchone()
    assert policy is not None, "RLS policy 'organizations_org_isolation' not found"


def test_create_organizations(test_organizations):
    """Verify organizations were created successfully"""
    org1_id = test_organizations["org1"]
    org2_id = test_organizations["org2"]

    assert org1_id is not None, "Organization 1 ID is None"
    assert org2_id is not None, "Organization 2 ID is None"
    assert org1_id != org2_id, "Organization IDs should be unique"


# ============================================================================
# User Isolation Tests
# ============================================================================


def test_users_have_organization_id(db_session, test_users, test_organizations):
    """Verify users table has organization_id foreign key"""
    user1_id = test_users["user1_id"]

    result = db_session.execute(
        text(
            """
        SELECT organization_id FROM users WHERE id = :user_id
    """
        ),
        {"user_id": user1_id},
    )

    org_id = result.fetchone()[0]
    assert org_id == test_organizations["org1"], "User should belong to organization 1"


def test_cross_organization_user_isolation(db_session, test_users, test_organizations):
    """Verify users from different organizations are isolated"""
    org1_id = test_organizations["org1"]
    org2_id = test_organizations["org2"]

    # Set context to org1
    db_session.execute(text(f"SET app.current_organization_id = '{org1_id}'"))

    # Query all users (should only see org1 users due to RLS)
    result = db_session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.fetchone()[0]

    # Should only see 1 user (org1's user) due to RLS filtering
    assert count == 1, f"Expected 1 user visible, got {count} (RLS should filter org2 users)"

    # Set context to org2
    db_session.execute(text(f"SET app.current_organization_id = '{org2_id}'"))

    # Should only see org2's user
    result = db_session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.fetchone()[0]

    assert count == 1, f"Expected 1 user visible in org2, got {count}"


# ============================================================================
# Agent Instance Isolation Tests
# ============================================================================


def test_agent_instances_isolation(db_session, test_organizations, test_users):
    """Verify agent instances are properly isolated by organization"""
    org1_id = test_organizations["org1"]
    org2_id = test_organizations["org2"]
    user1_id = test_users["user1_id"]
    user2_id = test_users["user2_id"]

    # Create agents in each organization
    agent1_id = uuid4()
    agent2_id = uuid4()

    db_session.execute(
        text(
            """
        INSERT INTO agent_instances (id, agent_id, agent_type, status, organization_id, created_by_id, created_at)
        VALUES
            (:agent1_id, 'agent-org1', 'content', 'active', :org1_id, :user1_id, now()),
            (:agent2_id, 'agent-org2', 'content', 'active', :org2_id, :user2_id, now())
    """
        ),
        {
            "agent1_id": agent1_id,
            "agent2_id": agent2_id,
            "org1_id": org1_id,
            "org2_id": org2_id,
            "user1_id": user1_id,
            "user2_id": user2_id,
        },
    )
    db_session.commit()

    try:
        # Set context to org1
        db_session.execute(text(f"SET app.current_organization_id = '{org1_id}'"))

        # Should only see org1's agent
        result = db_session.execute(text("SELECT agent_id FROM agent_instances"))
        agents = [row[0] for row in result]

        assert len(agents) == 1, f"Expected 1 agent in org1, got {len(agents)}"
        assert agents[0] == "agent-org1", "Should only see org1's agent"

        # Set context to org2
        db_session.execute(text(f"SET app.current_organization_id = '{org2_id}'"))

        # Should only see org2's agent
        result = db_session.execute(text("SELECT agent_id FROM agent_instances"))
        agents = [row[0] for row in result]

        assert len(agents) == 1, f"Expected 1 agent in org2, got {len(agents)}"
        assert agents[0] == "agent-org2", "Should only see org2's agent"

    finally:
        # Cleanup
        db_session.execute(
            text("DELETE FROM agent_instances WHERE id IN (:id1, :id2)"),
            {"id1": agent1_id, "id2": agent2_id},
        )
        db_session.commit()


# ============================================================================
# Roblox Environment Isolation Tests
# ============================================================================


def test_roblox_environments_isolation(db_session, test_organizations, test_users):
    """Verify Roblox environments are properly isolated by organization"""
    org1_id = test_organizations["org1"]
    org2_id = test_organizations["org2"]
    user1_id = test_users["user1_id"]
    user2_id = test_users["user2_id"]

    # Create environments in each organization
    env1_id = uuid4()
    env2_id = uuid4()

    db_session.execute(
        text(
            """
        INSERT INTO roblox_environments (id, name, status, organization_id, user_id, created_at)
        VALUES
            (:env1_id, 'Environment Org1', 'active', :org1_id, :user1_id, now()),
            (:env2_id, 'Environment Org2', 'active', :org2_id, :user2_id, now())
    """
        ),
        {
            "env1_id": env1_id,
            "env2_id": env2_id,
            "org1_id": org1_id,
            "org2_id": org2_id,
            "user1_id": user1_id,
            "user2_id": user2_id,
        },
    )
    db_session.commit()

    try:
        # Set context to org1
        db_session.execute(text(f"SET app.current_organization_id = '{org1_id}'"))

        # Should only see org1's environment
        result = db_session.execute(text("SELECT name FROM roblox_environments"))
        envs = [row[0] for row in result]

        assert len(envs) == 1, f"Expected 1 environment in org1, got {len(envs)}"
        assert envs[0] == "Environment Org1", "Should only see org1's environment"

        # Set context to org2
        db_session.execute(text(f"SET app.current_organization_id = '{org2_id}'"))

        # Should only see org2's environment
        result = db_session.execute(text("SELECT name FROM roblox_environments"))
        envs = [row[0] for row in result]

        assert len(envs) == 1, f"Expected 1 environment in org2, got {len(envs)}"
        assert envs[0] == "Environment Org2", "Should only see org2's environment"

    finally:
        # Cleanup
        db_session.execute(
            text("DELETE FROM roblox_environments WHERE id IN (:id1, :id2)"),
            {"id1": env1_id, "id2": env2_id},
        )
        db_session.commit()


# ============================================================================
# Customer/Payment Isolation Tests
# ============================================================================


def test_customers_isolation(db_session, test_organizations, test_users):
    """Verify payment customers are properly isolated by organization"""
    org1_id = test_organizations["org1"]
    org2_id = test_organizations["org2"]
    user1_id = test_users["user1_id"]
    user2_id = test_users["user2_id"]

    # Create customers in each organization
    cust1_id = uuid4()
    cust2_id = uuid4()

    db_session.execute(
        text(
            """
        INSERT INTO customers (id, stripe_customer_id, user_id, organization_id, created_at)
        VALUES
            (:cust1_id, 'cus_org1_test', :user1_id, :org1_id, now()),
            (:cust2_id, 'cus_org2_test', :user2_id, :org2_id, now())
    """
        ),
        {
            "cust1_id": cust1_id,
            "cust2_id": cust2_id,
            "org1_id": org1_id,
            "org2_id": org2_id,
            "user1_id": user1_id,
            "user2_id": user2_id,
        },
    )
    db_session.commit()

    try:
        # Set context to org1
        db_session.execute(text(f"SET app.current_organization_id = '{org1_id}'"))

        # Should only see org1's customer
        result = db_session.execute(text("SELECT stripe_customer_id FROM customers"))
        customers = [row[0] for row in result]

        assert len(customers) == 1, f"Expected 1 customer in org1, got {len(customers)}"
        assert customers[0] == "cus_org1_test", "Should only see org1's customer"

        # Set context to org2
        db_session.execute(text(f"SET app.current_organization_id = '{org2_id}'"))

        # Should only see org2's customer
        result = db_session.execute(text("SELECT stripe_customer_id FROM customers"))
        customers = [row[0] for row in result]

        assert len(customers) == 1, f"Expected 1 customer in org2, got {len(customers)}"
        assert customers[0] == "cus_org2_test", "Should only see org2's customer"

    finally:
        # Cleanup
        db_session.execute(
            text("DELETE FROM customers WHERE id IN (:id1, :id2)"),
            {"id1": cust1_id, "id2": cust2_id},
        )
        db_session.commit()


# ============================================================================
# CASCADE Delete Tests
# ============================================================================


def test_organization_cascade_delete(db_session):
    """Verify deleting organization cascades to related records"""
    # Create test organization
    org_id = uuid4()
    user_id = None
    agent_id = uuid4()

    db_session.execute(
        text(
            """
        INSERT INTO organizations (id, name, slug, is_active, created_at, updated_at)
        VALUES (:org_id, 'Cascade Test Org', 'cascade-test', true, now(), now())
    """
        ),
        {"org_id": org_id},
    )
    db_session.commit()

    # Create user in this organization
    result = db_session.execute(
        text(
            """
        INSERT INTO users (email, organization_id, created_at)
        VALUES ('cascade@test.com', :org_id, now())
        RETURNING id
    """
        ),
        {"org_id": org_id},
    )
    user_id = result.fetchone()[0]
    db_session.commit()

    # Create agent in this organization
    db_session.execute(
        text(
            """
        INSERT INTO agent_instances (id, agent_id, organization_id, created_by_id, created_at)
        VALUES (:agent_id, 'cascade-agent', :org_id, :user_id, now())
    """
        ),
        {"agent_id": agent_id, "org_id": org_id, "user_id": user_id},
    )
    db_session.commit()

    # Verify records exist
    result = db_session.execute(
        text("SELECT COUNT(*) FROM users WHERE organization_id = :org_id"), {"org_id": org_id}
    )
    user_count = result.fetchone()[0]
    assert user_count == 1, "User should exist before cascade delete"

    result = db_session.execute(
        text("SELECT COUNT(*) FROM agent_instances WHERE organization_id = :org_id"),
        {"org_id": org_id},
    )
    agent_count = result.fetchone()[0]
    assert agent_count == 1, "Agent should exist before cascade delete"

    # Delete organization (should CASCADE to users and agents)
    db_session.execute(text("DELETE FROM organizations WHERE id = :org_id"), {"org_id": org_id})
    db_session.commit()

    # Verify CASCADE worked
    result = db_session.execute(
        text("SELECT COUNT(*) FROM users WHERE id = :user_id"), {"user_id": user_id}
    )
    user_count = result.fetchone()[0]
    assert user_count == 0, "User should be deleted via CASCADE"

    result = db_session.execute(
        text("SELECT COUNT(*) FROM agent_instances WHERE id = :agent_id"), {"agent_id": agent_id}
    )
    agent_count = result.fetchone()[0]
    assert agent_count == 0, "Agent should be deleted via CASCADE"


# ============================================================================
# Index Verification Tests
# ============================================================================


def test_organization_indexes_exist(db_session):
    """Verify performance indexes exist on organization_id columns"""
    expected_indexes = [
        ("users", "ix_users_organization_id"),
        ("agent_instances", "ix_agent_instances_organization_id"),
        ("roblox_environments", "ix_roblox_environments_organization_id"),
        ("customers", "ix_customers_organization_id"),
    ]

    for table_name, index_name in expected_indexes:
        result = db_session.execute(
            text(
                """
            SELECT indexname FROM pg_indexes
            WHERE tablename = :table_name AND indexname = :index_name
        """
            ),
            {"table_name": table_name, "index_name": index_name},
        )

        index = result.fetchone()
        assert index is not None, f"Index {index_name} missing on {table_name} table"


# ============================================================================
# Summary
# ============================================================================


def test_multi_tenant_summary(db_session):
    """Verify all multi-tenant components are in place"""
    checks = {
        "organizations_table": False,
        "users_organization_fk": False,
        "agents_organization_fk": False,
        "roblox_organization_fk": False,
        "customers_organization_fk": False,
        "rls_enabled": False,
    }

    # Check tables exist
    result = db_session.execute(
        text(
            """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name IN
        ('organizations', 'users', 'agent_instances', 'roblox_environments', 'customers')
    """
        )
    )
    tables = {row[0] for row in result}
    checks["organizations_table"] = len(tables) == 5

    # Check foreign keys exist
    result = db_session.execute(
        text(
            """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE column_name = 'organization_id' AND table_name != 'organizations'
    """
        )
    )
    fk_tables = {row[0] for row in result}
    checks["users_organization_fk"] = "users" in fk_tables
    checks["agents_organization_fk"] = "agent_instances" in fk_tables
    checks["roblox_organization_fk"] = "roblox_environments" in fk_tables
    checks["customers_organization_fk"] = "customers" in fk_tables

    # Check RLS enabled
    result = db_session.execute(
        text(
            """
        SELECT COUNT(*) FROM pg_policies WHERE tablename IN
        ('users', 'agent_instances', 'roblox_environments', 'customers')
    """
        )
    )
    policy_count = result.fetchone()[0]
    checks["rls_enabled"] = policy_count >= 4

    # All checks must pass
    for check_name, passed in checks.items():
        assert passed, f"Multi-tenant check failed: {check_name}"

    print("\n✅ All multi-tenant isolation checks passed:")
    for check_name in checks:
        print(f"  ✓ {check_name}")
