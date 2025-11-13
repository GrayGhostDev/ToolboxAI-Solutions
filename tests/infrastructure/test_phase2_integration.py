"""
Phase 2 Infrastructure Integration Tests

Tests the complete monitoring and secrets management infrastructure:
- HashiCorp Vault (secrets management)
- Prometheus (metrics collection)
- PostgreSQL Exporter (database metrics)
- Redis Exporter (cache metrics)
- End-to-end monitoring pipeline

Run with: pytest tests/infrastructure/test_phase2_integration.py -v

Prerequisites:
- Docker Compose stack running
- Vault initialized and unsealed
- All exporters healthy
"""

import time

import hvac
import pytest
import requests
from prometheus_client.parser import text_string_to_metric_families

# ============================================
# Configuration
# ============================================

VAULT_ADDR = "http://localhost:8200"
VAULT_TOKEN = "devtoken"  # Development mode token
PROMETHEUS_ADDR = "http://localhost:9090"
POSTGRES_EXPORTER_ADDR = "http://localhost:9187"
REDIS_EXPORTER_ADDR = "http://localhost:9121"

# Timeout settings
REQUEST_TIMEOUT = 10
HEALTH_CHECK_RETRIES = 3
HEALTH_CHECK_INTERVAL = 2


# ============================================
# Fixtures
# ============================================


@pytest.fixture(scope="module")
def vault_client():
    """Initialize Vault client for tests."""
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
    return client


@pytest.fixture(scope="module")
def wait_for_services():
    """Wait for all services to be healthy before running tests."""
    services = {
        "Vault": f"{VAULT_ADDR}/v1/sys/health",
        "Prometheus": f"{PROMETHEUS_ADDR}/-/healthy",
        "PostgreSQL Exporter": f"{POSTGRES_EXPORTER_ADDR}/metrics",
        "Redis Exporter": f"{REDIS_EXPORTER_ADDR}/metrics",
    }

    for service_name, health_url in services.items():
        for attempt in range(HEALTH_CHECK_RETRIES):
            try:
                response = requests.get(health_url, timeout=REQUEST_TIMEOUT)
                if response.status_code in [200, 429]:  # 429 = standby Vault
                    print(f"✓ {service_name} is healthy")
                    break
            except requests.exceptions.RequestException as e:
                if attempt == HEALTH_CHECK_RETRIES - 1:
                    pytest.skip(f"{service_name} not available: {e}")
                time.sleep(HEALTH_CHECK_INTERVAL)

    yield
    # Teardown - nothing needed


# ============================================
# Test Class: Vault Integration
# ============================================


class TestVaultIntegration:
    """Test Vault secrets management functionality."""

    def test_vault_healthy(self):
        """Verify Vault health endpoint responds correctly."""
        response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code in [200, 429, 473, 501, 503]

        health_data = response.json()
        assert "initialized" in health_data
        assert "sealed" in health_data

    def test_vault_initialized(self):
        """Verify Vault is initialized."""
        response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)
        health_data = response.json()
        assert health_data.get("initialized") is True, "Vault is not initialized"

    def test_vault_unsealed(self):
        """Verify Vault is unsealed and ready."""
        response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)
        health_data = response.json()
        assert health_data.get("sealed") is False, "Vault is sealed"

    def test_vault_authentication(self, vault_client):
        """Test Vault client authentication."""
        assert vault_client.is_authenticated(), "Vault client not authenticated"

    def test_vault_kv_engine_enabled(self, vault_client):
        """Verify KV v2 secrets engine is enabled."""
        mounts = vault_client.sys.list_mounted_secrets_engines()
        assert "secret/" in mounts, "KV v2 engine not mounted at secret/"
        assert mounts["secret/"]["type"] == "kv", "Secret engine is not KV type"

    def test_vault_read_write_secret(self, vault_client):
        """Test writing and reading a test secret."""
        test_path = "test/integration"
        test_data = {"test_key": "test_value", "timestamp": str(time.time())}

        # Write secret
        vault_client.secrets.kv.v2.create_or_update_secret(path=test_path, secret=test_data)

        # Read secret
        read_response = vault_client.secrets.kv.v2.read_secret_version(path=test_path)

        assert read_response["data"]["data"]["test_key"] == "test_value"

        # Cleanup
        vault_client.secrets.kv.v2.delete_metadata_and_all_versions(path=test_path)

    def test_vault_backend_secrets_exist(self, vault_client):
        """Verify essential backend secrets are configured."""
        required_paths = [
            "backend/database",
            "backend/redis",
            "backend/api",
        ]

        for path in required_paths:
            try:
                secret = vault_client.secrets.kv.v2.read_secret_version(path=path)
                assert secret is not None, f"Secret at {path} is None"
                assert "data" in secret, f"Secret at {path} has no data field"
            except Exception as e:
                pytest.skip(f"Backend secret {path} not populated yet: {e}")

    def test_vault_integration_secrets_exist(self, vault_client):
        """Verify integration API keys are configured."""
        integration_paths = [
            "integrations/openai",
            "integrations/pusher",
        ]

        for path in integration_paths:
            try:
                secret = vault_client.secrets.kv.v2.read_secret_version(path=path)
                assert secret is not None, f"Integration secret at {path} is None"
            except Exception as e:
                pytest.skip(f"Integration secret {path} not populated yet: {e}")

    def test_vault_metrics_endpoint(self):
        """Verify Vault exposes Prometheus metrics."""
        response = requests.get(
            f"{VAULT_ADDR}/v1/sys/metrics?format=prometheus",
            headers={"X-Vault-Token": VAULT_TOKEN},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code == 200
        assert "vault_core_unsealed" in response.text


# ============================================
# Test Class: Prometheus Integration
# ============================================


class TestPrometheusIntegration:
    """Test Prometheus metrics collection."""

    def test_prometheus_healthy(self):
        """Verify Prometheus health endpoint."""
        response = requests.get(f"{PROMETHEUS_ADDR}/-/healthy", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        assert response.text == "Prometheus is Healthy."

    def test_prometheus_ready(self):
        """Verify Prometheus is ready to serve traffic."""
        response = requests.get(f"{PROMETHEUS_ADDR}/-/ready", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        assert response.text == "Prometheus is Ready."

    def test_prometheus_config_loaded(self):
        """Verify Prometheus configuration is loaded."""
        response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/status/config", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "yaml" in data["data"]

    def test_prometheus_targets_discovered(self):
        """Verify all expected targets are discovered."""
        response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/targets", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        active_targets = data["data"]["activeTargets"]
        job_names = {target["scrapePool"] for target in active_targets}

        expected_jobs = {
            "prometheus",
            "backend",
            "postgres-exporter",
            "redis-exporter",
            "vault",
        }

        for job in expected_jobs:
            assert job in job_names, f"Job '{job}' not found in active targets"

    def test_prometheus_targets_healthy(self):
        """Verify all targets are up and healthy."""
        response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/targets", timeout=REQUEST_TIMEOUT)
        data = response.json()
        active_targets = data["data"]["activeTargets"]

        unhealthy_targets = [target for target in active_targets if target["health"] != "up"]

        if unhealthy_targets:
            unhealthy_info = [f"{t['scrapePool']}: {t['lastError']}" for t in unhealthy_targets]
            pytest.fail(f"Unhealthy targets found: {unhealthy_info}")

    def test_prometheus_scrape_successful(self):
        """Verify Prometheus is successfully scraping metrics."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "up"}, timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        results = data["data"]["result"]
        assert len(results) > 0, "No metrics being scraped"

        # All targets should be up (value=1)
        down_targets = [r["metric"]["job"] for r in results if r["value"][1] == "0"]
        assert len(down_targets) == 0, f"Targets down: {down_targets}"

    def test_prometheus_alert_rules_loaded(self):
        """Verify alert rules are loaded."""
        response = requests.get(f"{PROMETHEUS_ADDR}/api/v1/rules", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Alert rules should be loaded from alert_rules.yml
        groups = data["data"]["groups"]
        assert len(groups) > 0, "No alert rule groups loaded"


# ============================================
# Test Class: PostgreSQL Exporter
# ============================================


class TestPostgreSQLExporter:
    """Test PostgreSQL metrics exporter."""

    def test_postgres_exporter_healthy(self):
        """Verify PostgreSQL exporter is healthy."""
        response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200

    def test_postgres_exporter_metrics_available(self):
        """Verify PostgreSQL metrics are being collected."""
        response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Parse metrics
        families = list(text_string_to_metric_families(metrics_text))
        metric_names = {family.name for family in families}

        # Essential PostgreSQL metrics
        essential_metrics = [
            "pg_up",  # Database is up
            "pg_stat_database_numbackends",  # Active connections
            "pg_stat_database_xact_commit",  # Transaction commits
            "pg_stat_database_blks_read",  # Blocks read
            "pg_stat_database_blks_hit",  # Cache hits
        ]

        for metric in essential_metrics:
            assert metric in metric_names, f"Metric '{metric}' not found"

    def test_postgres_database_up(self):
        """Verify PostgreSQL database is accessible."""
        response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Check pg_up metric
        assert "pg_up 1" in metrics_text, "PostgreSQL database is down (pg_up != 1)"

    def test_postgres_connections_metric(self):
        """Verify connection metrics are being collected."""
        response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Should have connection metrics
        assert "pg_stat_database_numbackends" in metrics_text

    def test_postgres_cache_hit_ratio_calculable(self):
        """Verify we can calculate cache hit ratio from metrics."""
        response = requests.get(f"{POSTGRES_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Need both blks_hit and blks_read to calculate ratio
        assert "pg_stat_database_blks_hit" in metrics_text
        assert "pg_stat_database_blks_read" in metrics_text


# ============================================
# Test Class: Redis Exporter
# ============================================


class TestRedisExporter:
    """Test Redis metrics exporter."""

    def test_redis_exporter_healthy(self):
        """Verify Redis exporter is healthy."""
        response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200

    def test_redis_exporter_metrics_available(self):
        """Verify Redis metrics are being collected."""
        response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Parse metrics
        families = list(text_string_to_metric_families(metrics_text))
        metric_names = {family.name for family in families}

        # Essential Redis metrics
        essential_metrics = [
            "redis_up",  # Redis is up
            "redis_connected_clients",  # Connected clients
            "redis_memory_used_bytes",  # Memory usage
            "redis_commands_processed_total",  # Commands processed
            "redis_keyspace_hits_total",  # Cache hits
            "redis_keyspace_misses_total",  # Cache misses
        ]

        for metric in essential_metrics:
            assert metric in metric_names, f"Metric '{metric}' not found"

    def test_redis_database_up(self):
        """Verify Redis database is accessible."""
        response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Check redis_up metric
        assert "redis_up 1" in metrics_text, "Redis database is down (redis_up != 1)"

    def test_redis_memory_metrics(self):
        """Verify memory usage metrics are available."""
        response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Should have memory metrics
        assert "redis_memory_used_bytes" in metrics_text
        assert "redis_memory_max_bytes" in metrics_text

    def test_redis_cache_hit_rate_calculable(self):
        """Verify we can calculate cache hit rate from metrics."""
        response = requests.get(f"{REDIS_EXPORTER_ADDR}/metrics", timeout=REQUEST_TIMEOUT)
        metrics_text = response.text

        # Need both hits and misses to calculate hit rate
        assert "redis_keyspace_hits_total" in metrics_text
        assert "redis_keyspace_misses_total" in metrics_text


# ============================================
# Test Class: End-to-End Monitoring Pipeline
# ============================================


class TestEndToEndMonitoring:
    """Test complete monitoring pipeline from source to Prometheus."""

    def test_vault_metrics_in_prometheus(self):
        """Verify Vault metrics are being scraped by Prometheus."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query",
            params={"query": "vault_core_unsealed"},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        results = data["data"]["result"]
        assert len(results) > 0, "Vault metrics not found in Prometheus"

        # Vault should be unsealed
        vault_unsealed = results[0]["value"][1]
        assert vault_unsealed == "1", "Vault is sealed according to Prometheus"

    def test_postgres_metrics_in_prometheus(self):
        """Verify PostgreSQL metrics are being scraped by Prometheus."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "pg_up"}, timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        results = data["data"]["result"]
        assert len(results) > 0, "PostgreSQL metrics not found in Prometheus"

        # PostgreSQL should be up
        pg_up = results[0]["value"][1]
        assert pg_up == "1", "PostgreSQL is down according to Prometheus"

    def test_redis_metrics_in_prometheus(self):
        """Verify Redis metrics are being scraped by Prometheus."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "redis_up"}, timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        results = data["data"]["result"]
        assert len(results) > 0, "Redis metrics not found in Prometheus"

        # Redis should be up
        redis_up = results[0]["value"][1]
        assert redis_up == "1", "Redis is down according to Prometheus"

    def test_backend_metrics_in_prometheus(self):
        """Verify backend application metrics are being scraped."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query",
            params={"query": 'up{job="backend"}'},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code == 200
        data = response.json()

        results = data["data"]["result"]
        if len(results) > 0:
            backend_up = results[0]["value"][1]
            assert backend_up == "1", "Backend is down according to Prometheus"
        else:
            pytest.skip("Backend not running or not exposing metrics yet")

    def test_prometheus_self_monitoring(self):
        """Verify Prometheus is monitoring itself."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query",
            params={"query": 'up{job="prometheus"}'},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        results = data["data"]["result"]
        assert len(results) > 0, "Prometheus self-monitoring not working"

        prom_up = results[0]["value"][1]
        assert prom_up == "1", "Prometheus self-check failed"

    def test_all_scrape_targets_successful(self):
        """Verify all configured scrape targets are being scraped successfully."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "up"}, timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        results = data["data"]["result"]

        # Create summary
        target_status = {}
        for result in results:
            job = result["metric"]["job"]
            instance = result["metric"].get("instance", "unknown")
            status = "UP" if result["value"][1] == "1" else "DOWN"
            target_status[f"{job} ({instance})"] = status

        # All should be up
        down_targets = [target for target, status in target_status.items() if status == "DOWN"]

        assert len(down_targets) == 0, f"Targets down: {down_targets}"

    def test_monitoring_data_freshness(self):
        """Verify monitoring data is fresh (recently scraped)."""
        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "up"}, timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        results = data["data"]["result"]

        current_time = time.time()
        stale_threshold = 60  # Metrics older than 60 seconds are stale

        for result in results:
            metric_timestamp = float(result["value"][0])
            age = current_time - metric_timestamp

            job = result["metric"]["job"]
            assert age < stale_threshold, f"Metrics for {job} are stale ({age:.1f}s old)"


# ============================================
# Test Class: Performance and Resource Usage
# ============================================


class TestPerformanceMetrics:
    """Test performance characteristics of monitoring infrastructure."""

    def test_prometheus_query_performance(self):
        """Verify Prometheus queries respond quickly."""
        start_time = time.time()

        response = requests.get(
            f"{PROMETHEUS_ADDR}/api/v1/query", params={"query": "up"}, timeout=REQUEST_TIMEOUT
        )

        query_time = time.time() - start_time

        assert response.status_code == 200
        assert query_time < 1.0, f"Query took too long: {query_time:.2f}s"

    def test_exporter_response_time(self):
        """Verify exporters respond quickly to metrics requests."""
        exporters = {
            "PostgreSQL": POSTGRES_EXPORTER_ADDR,
            "Redis": REDIS_EXPORTER_ADDR,
        }

        for name, addr in exporters.items():
            start_time = time.time()

            response = requests.get(f"{addr}/metrics", timeout=REQUEST_TIMEOUT)

            response_time = time.time() - start_time

            assert response.status_code == 200
            assert response_time < 2.0, f"{name} exporter too slow: {response_time:.2f}s"

    def test_vault_api_performance(self):
        """Verify Vault API responds quickly."""
        start_time = time.time()

        response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=REQUEST_TIMEOUT)

        response_time = time.time() - start_time

        assert response.status_code in [200, 429]
        assert response_time < 1.0, f"Vault API too slow: {response_time:.2f}s"


# ============================================
# Test Summary Report
# ============================================


@pytest.fixture(scope="session", autouse=True)
def print_test_summary(request):
    """Print test summary at the end of the session."""
    yield

    # This runs after all tests
    if hasattr(request.session, "testscollected"):
        print("\n" + "=" * 60)
        print("Phase 2 Infrastructure Integration Test Summary")
        print("=" * 60)
        print(f"Total tests collected: {request.session.testscollected}")
        print("\nComponents tested:")
        print("  ✓ HashiCorp Vault (secrets management)")
        print("  ✓ Prometheus (metrics collection)")
        print("  ✓ PostgreSQL Exporter (database metrics)")
        print("  ✓ Redis Exporter (cache metrics)")
        print("  ✓ End-to-end monitoring pipeline")
        print("  ✓ Performance characteristics")
        print("=" * 60 + "\n")
