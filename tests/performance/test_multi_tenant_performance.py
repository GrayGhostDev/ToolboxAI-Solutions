"""
Performance Tests: Multi-Tenant Query Benchmarking
===================================================

Comprehensive performance testing for multi-tenant organization filtering.

Test Coverage:
    - Query performance with organization filters
    - Index utilization verification
    - RLS policy overhead measurement
    - Load testing with multiple organizations
    - Concurrent access patterns
    - Large dataset performance

Performance Targets:
    - Single org filter query: < 50ms (p95)
    - Multi-org aggregation: < 200ms (p95)
    - Index hit rate: > 95%
    - RLS overhead: < 10ms per query
    - Concurrent queries (10 orgs): < 100ms (p95)

Usage:
    pytest tests/performance/test_multi_tenant_performance.py -v
    pytest tests/performance/test_multi_tenant_performance.py --benchmark-only
"""

import statistics
import time
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import Organization, User

# Import models
from database.models.agent_models import AgentInstance
from database.models.roblox_models import RobloxEnvironment
from database.tenant_aware_query import TenantAwareQuery

# ============================================================================
# Test Configuration
# ============================================================================

PERFORMANCE_TARGETS = {
    "single_org_query_p95": 50,  # milliseconds
    "multi_org_aggregation_p95": 200,  # milliseconds
    "index_hit_rate_min": 0.95,  # 95%
    "rls_overhead_max": 10,  # milliseconds
    "concurrent_query_p95": 100,  # milliseconds
}

# Test data scale
NUM_ORGANIZATIONS = 10
NUM_USERS_PER_ORG = 50
NUM_AGENTS_PER_ORG = 100
NUM_ENVIRONMENTS_PER_ORG = 50
NUM_SUBSCRIPTIONS_PER_ORG = 30


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def performance_organizations(db_session: Session) -> list[Organization]:
    """Create multiple organizations for performance testing"""
    organizations = []
    for i in range(NUM_ORGANIZATIONS):
        org = Organization(id=uuid4(), name=f"Performance Org {i}", domain=f"perf-org-{i}.test")
        organizations.append(org)

    db_session.add_all(organizations)
    db_session.commit()

    yield organizations

    # Cleanup
    for org in organizations:
        db_session.delete(org)
    db_session.commit()


@pytest.fixture(scope="module")
def performance_users(
    db_session: Session, performance_organizations: list[Organization]
) -> dict[UUID, list[User]]:
    """Create users for each organization"""
    users_by_org = {}

    user_id_counter = 10000  # Start high to avoid conflicts

    for org in performance_organizations:
        users = []
        for i in range(NUM_USERS_PER_ORG):
            user = User(
                id=user_id_counter,
                email=f"user{i}@{org.domain}",
                username=f"perfuser{user_id_counter}",
                organization_id=org.id,
            )
            users.append(user)
            user_id_counter += 1

        users_by_org[org.id] = users
        db_session.add_all(users)

    db_session.commit()

    yield users_by_org

    # Cleanup
    for users in users_by_org.values():
        for user in users:
            db_session.delete(user)
    db_session.commit()


@pytest.fixture(scope="module")
def performance_agents(
    db_session: Session,
    performance_organizations: list[Organization],
    performance_users: dict[UUID, list[User]],
) -> dict[UUID, list[AgentInstance]]:
    """Create agent instances for each organization"""
    agents_by_org = {}

    for org in performance_organizations:
        agents = []
        users = performance_users[org.id]

        for i in range(NUM_AGENTS_PER_ORG):
            agent = AgentInstance(
                id=uuid4(),
                agent_id=f"perf-agent-{org.id}-{i}",
                agent_type="CONTENT_GENERATOR",
                status="IDLE" if i % 2 == 0 else "BUSY",
                organization_id=org.id,
                created_by_id=users[i % len(users)].id,
            )
            agents.append(agent)

        agents_by_org[org.id] = agents
        db_session.add_all(agents)

    db_session.commit()

    yield agents_by_org

    # Cleanup
    for agents in agents_by_org.values():
        for agent in agents:
            db_session.delete(agent)
    db_session.commit()


@pytest.fixture(scope="module")
def performance_environments(
    db_session: Session,
    performance_organizations: list[Organization],
    performance_users: dict[UUID, list[User]],
) -> dict[UUID, list[RobloxEnvironment]]:
    """Create Roblox environments for each organization"""
    envs_by_org = {}

    for org in performance_organizations:
        environments = []
        users = performance_users[org.id]

        for i in range(NUM_ENVIRONMENTS_PER_ORG):
            env = RobloxEnvironment(
                user_id=users[i % len(users)].id,
                name=f"Perf Env {org.id[:8]} {i}",
                place_id=f"{1000000 + i}",
                organization_id=org.id,
            )
            environments.append(env)

        envs_by_org[org.id] = environments
        db_session.add_all(environments)

    db_session.commit()

    yield envs_by_org

    # Cleanup
    for envs in envs_by_org.values():
        for env in envs:
            db_session.delete(env)
    db_session.commit()


# ============================================================================
# Performance Testing Utilities
# ============================================================================


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration_ms = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000


def measure_query_performance(func, iterations: int = 100) -> dict[str, float]:
    """Measure query performance statistics"""
    timings = []

    for _ in range(iterations):
        timer = PerformanceTimer()
        with timer:
            func()
        timings.append(timer.duration_ms)

    timings.sort()

    return {
        "min": min(timings),
        "max": max(timings),
        "mean": statistics.mean(timings),
        "median": statistics.median(timings),
        "p95": timings[int(len(timings) * 0.95)],
        "p99": timings[int(len(timings) * 0.99)],
        "std_dev": statistics.stdev(timings),
    }


def verify_index_usage(db_session: Session, query_str: str) -> dict[str, Any]:
    """Verify that query uses appropriate indexes"""
    # Get query execution plan
    explain_query = f"EXPLAIN (FORMAT JSON) {query_str}"
    result = db_session.execute(text(explain_query)).fetchone()

    plan = result[0] if result else {}

    # Parse plan to check for index scans
    uses_index = "Index Scan" in str(plan) or "Index Only Scan" in str(plan)
    uses_seq_scan = "Seq Scan" in str(plan)

    return {
        "uses_index": uses_index,
        "uses_seq_scan": uses_seq_scan,
        "plan": plan,
    }


# ============================================================================
# Single Organization Query Performance
# ============================================================================


class TestSingleOrgQueryPerformance:
    """Test query performance for single organization filtering"""

    def test_agent_query_performance(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Benchmark agent queries with organization filter"""
        org = performance_organizations[0]

        def query_agents():
            return db_session.query(AgentInstance).filter_by(organization_id=org.id).all()

        stats = measure_query_performance(query_agents, iterations=100)

        print(f"\n=== Agent Query Performance ===")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"P95: {stats['p95']:.2f}ms")
        print(f"P99: {stats['p99']:.2f}ms")

        # Verify performance target
        assert stats["p95"] < PERFORMANCE_TARGETS["single_org_query_p95"], (
            f"Agent query P95 ({stats['p95']:.2f}ms) exceeds target "
            f"({PERFORMANCE_TARGETS['single_org_query_p95']}ms)"
        )

    def test_environment_query_performance(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_environments: dict[UUID, list[RobloxEnvironment]],
    ):
        """Benchmark Roblox environment queries"""
        org = performance_organizations[0]

        def query_environments():
            return db_session.query(RobloxEnvironment).filter_by(organization_id=org.id).all()

        stats = measure_query_performance(query_environments, iterations=100)

        print(f"\n=== Environment Query Performance ===")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"P95: {stats['p95']:.2f}ms")

        assert stats["p95"] < PERFORMANCE_TARGETS["single_org_query_p95"]

    def test_tenant_aware_query_performance(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Benchmark TenantAwareQuery wrapper performance"""
        org = performance_organizations[0]

        def query_with_wrapper():
            return TenantAwareQuery(db_session, AgentInstance, org.id).all()

        stats = measure_query_performance(query_with_wrapper, iterations=100)

        print(f"\n=== TenantAwareQuery Performance ===")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"P95: {stats['p95']:.2f}ms")

        assert stats["p95"] < PERFORMANCE_TARGETS["single_org_query_p95"]


# ============================================================================
# Index Utilization Tests
# ============================================================================


class TestIndexUtilization:
    """Verify that queries utilize database indexes effectively"""

    def test_agent_organization_index(
        self, db_session: Session, performance_organizations: list[Organization]
    ):
        """Verify agent queries use organization_id index"""
        org = performance_organizations[0]

        # Build query string
        query_str = f"""
        SELECT * FROM agent_instances
        WHERE organization_id = '{org.id}'
        AND agent_type = 'CONTENT_GENERATOR'
        """

        plan = verify_index_usage(db_session, query_str)

        print(f"\n=== Agent Index Usage ===")
        print(f"Uses Index: {plan['uses_index']}")
        print(f"Uses Seq Scan: {plan['uses_seq_scan']}")

        # Should use index, not sequential scan
        assert plan["uses_index"], "Query should use index on organization_id"
        assert not plan["uses_seq_scan"], "Query should not use sequential scan"

    def test_environment_organization_index(
        self, db_session: Session, performance_organizations: list[Organization]
    ):
        """Verify Roblox environment queries use organization_id index"""
        org = performance_organizations[0]

        query_str = f"""
        SELECT * FROM roblox_environments
        WHERE organization_id = '{org.id}'
        AND deleted_at IS NULL
        """

        plan = verify_index_usage(db_session, query_str)

        print(f"\n=== Environment Index Usage ===")
        print(f"Uses Index: {plan['uses_index']}")

        assert plan["uses_index"], "Query should use index on organization_id"


# ============================================================================
# RLS Policy Overhead Tests
# ============================================================================


class TestRLSPolicyOverhead:
    """Measure performance overhead of RLS policies"""

    def test_query_with_rls_context(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Measure overhead of setting RLS context"""
        org = performance_organizations[0]

        # Measure query without RLS context
        def query_without_rls():
            return db_session.query(AgentInstance).filter_by(organization_id=org.id).all()

        stats_without = measure_query_performance(query_without_rls, iterations=50)

        # Measure query with RLS context
        def query_with_rls():
            db_session.execute(text(f"SET app.current_organization_id = '{org.id}'"))
            result = db_session.query(AgentInstance).filter_by(organization_id=org.id).all()
            db_session.execute(text("RESET app.current_organization_id"))
            return result

        stats_with = measure_query_performance(query_with_rls, iterations=50)

        overhead = stats_with["mean"] - stats_without["mean"]

        print(f"\n=== RLS Overhead ===")
        print(f"Without RLS: {stats_without['mean']:.2f}ms")
        print(f"With RLS: {stats_with['mean']:.2f}ms")
        print(f"Overhead: {overhead:.2f}ms")

        assert overhead < PERFORMANCE_TARGETS["rls_overhead_max"], (
            f"RLS overhead ({overhead:.2f}ms) exceeds target "
            f"({PERFORMANCE_TARGETS['rls_overhead_max']}ms)"
        )


# ============================================================================
# Multi-Organization Aggregation Tests
# ============================================================================


class TestMultiOrgAggregation:
    """Test performance of queries spanning multiple organizations"""

    def test_cross_org_analytics_query(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Benchmark analytics queries across all organizations"""

        def aggregate_all_orgs():
            # Count agents by status for each organization
            results = {}
            for org in performance_organizations:
                counts = (
                    db_session.query(AgentInstance.status).filter_by(organization_id=org.id).count()
                )
                results[org.id] = counts
            return results

        stats = measure_query_performance(aggregate_all_orgs, iterations=50)

        print(f"\n=== Multi-Org Aggregation Performance ===")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"P95: {stats['p95']:.2f}ms")

        assert stats["p95"] < PERFORMANCE_TARGETS["multi_org_aggregation_p95"]


# ============================================================================
# Concurrent Access Tests
# ============================================================================


class TestConcurrentAccess:
    """Test performance under concurrent multi-tenant access"""

    def test_concurrent_org_queries(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Simulate concurrent queries from multiple organizations"""
        import concurrent.futures

        def query_org_data(org_id: UUID):
            timer = PerformanceTimer()
            with timer:
                # Simulate typical user query
                agents = (
                    db_session.query(AgentInstance)
                    .filter_by(organization_id=org_id)
                    .limit(20)
                    .all()
                )
            return timer.duration_ms

        # Execute concurrent queries
        timings = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_org_data, org.id) for org in performance_organizations]
            timings = [f.result() for f in concurrent.futures.as_completed(futures)]

        timings.sort()
        p95 = timings[int(len(timings) * 0.95)]

        print(f"\n=== Concurrent Query Performance ===")
        print(f"Mean: {statistics.mean(timings):.2f}ms")
        print(f"P95: {p95:.2f}ms")

        assert p95 < PERFORMANCE_TARGETS["concurrent_query_p95"]


# ============================================================================
# Large Dataset Performance Tests
# ============================================================================


class TestLargeDatasetPerformance:
    """Test performance with large datasets per organization"""

    def test_pagination_performance(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Test pagination performance with organization filter"""
        org = performance_organizations[0]
        page_size = 20

        def paginated_query(offset: int):
            return (
                db_session.query(AgentInstance)
                .filter_by(organization_id=org.id)
                .limit(page_size)
                .offset(offset)
                .all()
            )

        # Test first page (likely in cache)
        stats_first = measure_query_performance(lambda: paginated_query(0), iterations=50)

        # Test last page (less likely in cache)
        last_offset = NUM_AGENTS_PER_ORG - page_size
        stats_last = measure_query_performance(lambda: paginated_query(last_offset), iterations=50)

        print(f"\n=== Pagination Performance ===")
        print(f"First Page P95: {stats_first['p95']:.2f}ms")
        print(f"Last Page P95: {stats_last['p95']:.2f}ms")

        # Both should meet performance targets
        assert stats_first["p95"] < PERFORMANCE_TARGETS["single_org_query_p95"]
        assert stats_last["p95"] < PERFORMANCE_TARGETS["single_org_query_p95"]


# ============================================================================
# Performance Regression Detection
# ============================================================================


class TestPerformanceBaseline:
    """Establish and verify performance baselines"""

    def test_establish_baseline(
        self,
        db_session: Session,
        performance_organizations: list[Organization],
        performance_agents: dict[UUID, list[AgentInstance]],
    ):
        """Establish performance baseline for future regression testing"""
        org = performance_organizations[0]

        # Standard query pattern
        def standard_query():
            return (
                db_session.query(AgentInstance)
                .filter_by(organization_id=org.id, status="IDLE")
                .all()
            )

        stats = measure_query_performance(standard_query, iterations=100)

        baseline = {
            "test": "standard_org_filter_query",
            "timestamp": datetime.now().isoformat(),
            "dataset_size": NUM_AGENTS_PER_ORG,
            "statistics": stats,
        }

        print(f"\n=== Performance Baseline ===")
        print(f"Test: {baseline['test']}")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"P95: {stats['p95']:.2f}ms")
        print(f"P99: {stats['p99']:.2f}ms")

        # Save baseline for comparison
        # (In production, save to file or database)

        # Verify meets current targets
        assert stats["p95"] < PERFORMANCE_TARGETS["single_org_query_p95"]


# ============================================================================
# Performance Summary Report
# ============================================================================


def generate_performance_report(test_results: dict[str, dict[str, float]]) -> str:
    """Generate comprehensive performance report"""
    report = []
    report.append("=" * 70)
    report.append("MULTI-TENANT PERFORMANCE TEST REPORT")
    report.append("=" * 70)
    report.append(f"\nTest Date: {datetime.now().isoformat()}")
    report.append(f"Dataset Scale:")
    report.append(f"  - Organizations: {NUM_ORGANIZATIONS}")
    report.append(f"  - Users per Org: {NUM_USERS_PER_ORG}")
    report.append(f"  - Agents per Org: {NUM_AGENTS_PER_ORG}")
    report.append(f"  - Environments per Org: {NUM_ENVIRONMENTS_PER_ORG}")

    report.append(f"\n{'Test Name':<40} {'P95 (ms)':<10} {'Status':<10}")
    report.append("-" * 70)

    for test_name, stats in test_results.items():
        p95 = stats.get("p95", 0)
        target = PERFORMANCE_TARGETS.get(test_name, float("inf"))
        status = "PASS" if p95 < target else "FAIL"
        report.append(f"{test_name:<40} {p95:>8.2f}   {status:<10}")

    report.append("=" * 70)

    return "\n".join(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
