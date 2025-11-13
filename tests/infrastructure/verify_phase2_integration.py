#!/usr/bin/env python3
"""
Phase 2 Infrastructure Verification Script

Validates that all monitoring infrastructure components are working correctly.
This script bypasses pytest/conftest issues by directly testing infrastructure.

Run with: python tests/infrastructure/verify_phase2_integration.py
"""

import sys

import requests

# Configuration
VAULT_ADDR = "http://localhost:8200"
VAULT_TOKEN = "devtoken"
PROMETHEUS_ADDR = "http://localhost:9090"
POSTGRES_EXPORTER_ADDR = "http://localhost:9187"
REDIS_EXPORTER_ADDR = "http://localhost:9121"

REQUEST_TIMEOUT = 10

# Test results
passed = 0
failed = 0
skipped = 0


def test(name: str):
    """Decorator to mark test functions."""

    def decorator(func):
        func.__test_name__ = name
        return func

    return decorator


def print_header(title: str):
    """Print a test section header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def print_test(name: str, passed: bool, message: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"      {message}")


def run_test(func):
    """Run a test function and track results."""
    global passed, failed, skipped

    test_name = getattr(func, "__test_name__", func.__name__)
    try:
        result = func()
        if result is None or result is True:
            passed += 1
            print_test(test_name, True)
        elif result == "skip":
            skipped += 1
            print_test(test_name, True, "(skipped)")
        else:
            failed += 1
            print_test(test_name, False, str(result))
    except Exception as e:
        failed += 1
        print_test(test_name, False, str(e))


# ============================================
# Vault Tests
# ============================================

print_header("Vault Integration Tests")


@test("Vault health endpoint responds")
def test_vault_healthy():
    response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)
    if response.status_code not in [200, 429, 473, 501, 503]:
        return f"Unexpected status code: {response.status_code}"
    return True


@test("Vault is initialized")
def test_vault_initialized():
    response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)
    health_data = response.json()
    if not health_data.get("initialized"):
        return "Vault is not initialized"
    return True


@test("Vault is unsealed")
def test_vault_unsealed():
    response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)
    health_data = response.json()
    if health_data.get("sealed"):
        return "Vault is sealed"
    return True


@test("Vault exposes Prometheus metrics")
def test_vault_metrics():
    response = requests.get(
        f"{VAULT_ADDR}/v1/sys/metrics?format=prometheus",
        headers={"X-Vault-Token": VAULT_TOKEN},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        return f"Status code: {response.status_code}"
    if "vault_core_unsealed" not in response.text:
        return "vault_core_unsealed metric not found"
    return True


run_test(test_vault_healthy)
run_test(test_vault_initialized)
run_test(test_vault_unsealed)
run_test(test_vault_metrics)


# ============================================
# Prometheus Tests
# ============================================

print_header("Prometheus Integration Tests")


@test("Prometheus health endpoint")
def test_prometheus_healthy():
    response = requests.get(f"{PROMETHEUS_ADDR}/-/healthy", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        return f"Status code: {response.status_code}"
    if "Healthy" not in response.text:
        return "Unexpected response"
    return True


@test("Prometheus ready endpoint")
def test_prometheus_ready():
    response = requests.get(f"{PROMETHEUS_ADDR}/-/ready", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        return f"Status code: {response.status_code}"
    return True


@test("Prometheus configuration loaded")
def test_prometheus_config():
    response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/status/config", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        return f"Status code: {response.status_code}"
    data = response.json()
    if data["status"] != "success":
        return f"Config status: {data['status']}"
    return True


@test("Prometheus targets discovered")
def test_prometheus_targets():
    response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/targets", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        return f"Status code: {response.status_code}"

    data = response.json()
    active_targets = data["data"]["activeTargets"]
    job_names = {target["scrapePool"] for target in active_targets}

    expected_jobs = {"prometheus", "postgres-exporter", "redis-exporter", "vault"}
    missing_jobs = expected_jobs - job_names

    if missing_jobs:
        return f"Missing jobs: {missing_jobs}"
    return True


@test("All Prometheus targets are healthy")
def test_prometheus_targets_health():
    response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/targets", timeout=REQUEST_TIMEOUT)
    data = response.json()
    active_targets = data["data"]["activeTargets"]

    unhealthy = [t for t in active_targets if t["health"] != "up"]
    if unhealthy:
        unhealthy_jobs = [f"{t['scrapePool']}: {t.get('lastError', 'unknown')}" for t in unhealthy]
        return f"Unhealthy targets: {unhealthy_jobs}"
    return True


run_test(test_prometheus_healthy)
run_test(test_prometheus_ready)
run_test(test_prometheus_config)
run_test(test_prometheus_targets)
run_test(test_prometheus_targets_health)


# ============================================
# PostgreSQL Exporter Tests
# ============================================

print_header("PostgreSQL Exporter Tests")


@test("PostgreSQL exporter responds")
def test_postgres_exporter_healthy():
    response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        return f"Status code: {response.status_code}"
    return True


@test("PostgreSQL metrics available")
def test_postgres_metrics():
    response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
    metrics_text = response.text

    required_metrics = ["pg_up", "pg_stat_database_numbackends", "pg_stat_database_blks_hit"]
    missing = [m for m in required_metrics if m not in metrics_text]

    if missing:
        return f"Missing metrics: {missing}"
    return True


@test("PostgreSQL database is up")
def test_postgres_up():
    response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
    if "pg_up 1" not in response.text:
        return "PostgreSQL is down (pg_up != 1)"
    return True


run_test(test_postgres_exporter_healthy)
run_test(test_postgres_metrics)
run_test(test_postgres_up)


# ============================================
# Redis Exporter Tests
# ============================================

print_header("Redis Exporter Tests")


@test("Redis exporter responds")
def test_redis_exporter_healthy():
    response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        return f"Status code: {response.status_code}"
    return True


@test("Redis metrics available")
def test_redis_metrics():
    response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
    metrics_text = response.text

    required_metrics = ["redis_up", "redis_connected_clients", "redis_memory_used_bytes"]
    missing = [m for m in required_metrics if m not in metrics_text]

    if missing:
        return f"Missing metrics: {missing}"
    return True


@test("Redis database is up")
def test_redis_up():
    response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
    if "redis_up 1" not in response.text:
        return "Redis is down (redis_up != 1)"
    return True


run_test(test_redis_exporter_healthy)
run_test(test_redis_metrics)
run_test(test_redis_up)


# ============================================
# End-to-End Monitoring Tests
# ============================================

print_header("End-to-End Monitoring Pipeline Tests")


@test("Vault metrics in Prometheus")
def test_vault_metrics_in_prometheus():
    response = requests.get(
        f"{PROMETHEUS_ADDR}/api/v1/query",
        params={"query": "vault_core_unsealed"},
        timeout=REQUEST_TIMEOUT,
    )
    data = response.json()
    results = data["data"]["result"]

    if not results:
        return "Vault metrics not found in Prometheus"

    vault_unsealed = results[0]["value"][1]
    if vault_unsealed != "1":
        return f"Vault is sealed according to Prometheus: {vault_unsealed}"
    return True


@test("PostgreSQL metrics in Prometheus")
def test_postgres_metrics_in_prometheus():
    response = requests.get(
        f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "pg_up"}, timeout=REQUEST_TIMEOUT
    )
    data = response.json()
    results = data["data"]["result"]

    if not results:
        return "PostgreSQL metrics not found in Prometheus"

    pg_up = results[0]["value"][1]
    if pg_up != "1":
        return f"PostgreSQL is down: {pg_up}"
    return True


@test("Redis metrics in Prometheus")
def test_redis_metrics_in_prometheus():
    response = requests.get(
        f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "redis_up"}, timeout=REQUEST_TIMEOUT
    )
    data = response.json()
    results = data["data"]["result"]

    if not results:
        return "Redis metrics not found in Prometheus"

    redis_up = results[0]["value"][1]
    if redis_up != "1":
        return f"Redis is down: {redis_up}"
    return True


@test("All scrape targets successful")
def test_all_targets_up():
    response = requests.get(
        f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "up"}, timeout=REQUEST_TIMEOUT
    )
    data = response.json()
    results = data["data"]["result"]

    down_targets = [
        f"{r['metric']['job']} ({r['metric'].get('instance', 'unknown')})"
        for r in results
        if r["value"][1] == "0"
    ]

    if down_targets:
        return f"Targets down: {down_targets}"
    return True


run_test(test_vault_metrics_in_prometheus)
run_test(test_postgres_metrics_in_prometheus)
run_test(test_redis_metrics_in_prometheus)
run_test(test_all_targets_up)


# ============================================
# Summary
# ============================================

print_header("Test Summary")
print(f"✅ Passed:  {passed}")
print(f"❌ Failed:  {failed}")
print(f"⏭️  Skipped: {skipped}")
print(f"📊 Total:   {passed + failed + skipped}")

if failed > 0:
    print(f"\n❌ Phase 2 Infrastructure Tests FAILED ({failed} failures)")
    sys.exit(1)
else:
    print(f"\n✅ Phase 2 Infrastructure Tests PASSED")
    print(f"\nAll monitoring infrastructure components are operational:")
    print(f"  ✓ HashiCorp Vault (secrets management)")
    print(f"  ✓ Prometheus (metrics collection)")
    print(f"  ✓ PostgreSQL Exporter (database metrics)")
    print(f"  ✓ Redis Exporter (cache metrics)")
    print(f"  ✓ End-to-end monitoring pipeline")
    sys.exit(0)
