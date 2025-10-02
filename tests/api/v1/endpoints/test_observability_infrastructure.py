"""
Tests for Infrastructure Observability Endpoints

Tests the infrastructure monitoring and metrics endpoints
including system metrics, process metrics, and health checks.

Created: October 1, 2025
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
import psutil


@pytest.fixture
def mock_infrastructure_metrics():
    """Mock infrastructure metrics collector"""
    with patch('apps.backend.api.v1.endpoints.observability.infrastructure_metrics') as mock:
        # Mock system metrics
        mock.collect_system_metrics = AsyncMock(return_value=Mock(
            cpu_percent=45.2,
            cpu_count=8,
            cpu_freq_current=2400.0,
            memory_total_gb=16.0,
            memory_used_gb=8.5,
            memory_available_gb=7.5,
            memory_percent=53.1,
            disk_total_gb=500.0,
            disk_used_gb=250.0,
            disk_free_gb=250.0,
            disk_percent=50.0,
            network_bytes_sent=1024000000,
            network_bytes_recv=2048000000,
            network_connections=42,
            uptime_seconds=86400.0,
            boot_time=datetime.now(timezone.utc),
            timestamp=datetime.now(timezone.utc)
        ))

        # Mock process metrics
        mock.collect_process_metrics = AsyncMock(return_value=Mock(
            pid=12345,
            name="python",
            status="running",
            cpu_percent=12.5,
            memory_mb=512.0,
            memory_percent=3.2,
            num_threads=8,
            num_fds=156,
            create_time=datetime.now(timezone.utc),
            timestamp=datetime.now(timezone.utc)
        ))

        # Mock platform info
        mock.get_platform_info = AsyncMock(return_value={
            "system": "Linux",
            "release": "5.15.0",
            "version": "Ubuntu 22.04",
            "machine": "x86_64",
            "processor": "Intel Core i7",
            "python_version": "3.12.0",
            "hostname": "toolboxai-backend-1",
            "architecture": "64bit"
        })

        # Mock summary
        mock.get_metrics_summary = AsyncMock(return_value={
            "time_window_minutes": 5,
            "sample_count": 30,
            "cpu": {"avg": 45.0, "min": 30.0, "max": 60.0},
            "memory": {"avg": 50.0, "min": 45.0, "max": 55.0},
            "disk": {"avg": 50.0, "min": 50.0, "max": 50.0},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Mock health check
        mock.check_resource_thresholds = AsyncMock(return_value={
            "status": "healthy",
            "warnings": [],
            "critical": [],
            "thresholds": {
                "cpu_warning": 70.0,
                "cpu_critical": 90.0,
                "memory_warning": 75.0,
                "memory_critical": 90.0,
                "disk_warning": 80.0,
                "disk_critical": 95.0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Mock comprehensive report
        mock.get_comprehensive_report = AsyncMock(return_value={
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": {
                "system": "Linux",
                "hostname": "toolboxai-backend-1"
            },
            "system": {
                "cpu_percent": 45.2,
                "memory_percent": 53.1,
                "disk_percent": 50.0
            },
            "process": {
                "pid": 12345,
                "cpu_percent": 12.5
            },
            "threshold_check": {
                "status": "healthy",
                "warnings": [],
                "critical": []
            },
            "health_score": 85.5
        })

        yield mock


@pytest.mark.asyncio
class TestInfrastructureSystemMetrics:
    """Tests for system metrics endpoint"""

    async def test_get_system_metrics_success(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test successful retrieval of system metrics"""
        response = client.get(
            "/api/v1/observability/infrastructure/system",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "data" in data

        # Verify CPU metrics
        assert "cpu" in data["data"]
        assert data["data"]["cpu"]["percent"] == 45.2
        assert data["data"]["cpu"]["count"] == 8

        # Verify memory metrics
        assert "memory" in data["data"]
        assert data["data"]["memory"]["total_gb"] == 16.0
        assert data["data"]["memory"]["percent"] == 53.1

        # Verify disk metrics
        assert "disk" in data["data"]
        assert data["data"]["disk"]["percent"] == 50.0

        # Verify network metrics
        assert "network" in data["data"]
        assert data["data"]["network"]["connections"] == 42

    async def test_get_system_metrics_unauthorized(self, client: TestClient):
        """Test system metrics without authentication"""
        response = client.get("/api/v1/observability/infrastructure/system")
        assert response.status_code == 401

    async def test_get_system_metrics_error_handling(
        self, client: TestClient, auth_headers: dict
    ):
        """Test system metrics error handling"""
        with patch('apps.backend.api.v1.endpoints.observability.infrastructure_metrics') as mock:
            mock.collect_system_metrics = AsyncMock(
                side_effect=Exception("System error")
            )

            response = client.get(
                "/api/v1/observability/infrastructure/system",
                headers=auth_headers
            )

            assert response.status_code == 500


@pytest.mark.asyncio
class TestInfrastructureProcessMetrics:
    """Tests for process metrics endpoint"""

    async def test_get_process_metrics_success(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test successful retrieval of process metrics"""
        response = client.get(
            "/api/v1/observability/infrastructure/process",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "data" in data

        # Verify process info
        assert data["data"]["pid"] == 12345
        assert data["data"]["name"] == "python"
        assert data["data"]["status"] == "running"

        # Verify resource usage
        assert data["data"]["cpu_percent"] == 12.5
        assert data["data"]["memory_mb"] == 512.0
        assert data["data"]["threads"] == 8
        assert data["data"]["file_descriptors"] == 156


@pytest.mark.asyncio
class TestInfrastructurePlatformInfo:
    """Tests for platform info endpoint"""

    async def test_get_platform_info_success(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test successful retrieval of platform information"""
        response = client.get(
            "/api/v1/observability/infrastructure/platform",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "data" in data

        # Verify platform details
        assert data["data"]["system"] == "Linux"
        assert data["data"]["machine"] == "x86_64"
        assert data["data"]["python_version"] == "3.12.0"
        assert data["data"]["hostname"] == "toolboxai-backend-1"


@pytest.mark.asyncio
class TestInfrastructureSummary:
    """Tests for metrics summary endpoint"""

    async def test_get_summary_default_window(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test metrics summary with default time window"""
        response = client.get(
            "/api/v1/observability/infrastructure/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "data" in data

        # Verify aggregations
        assert data["data"]["time_window_minutes"] == 5
        assert data["data"]["sample_count"] == 30
        assert "cpu" in data["data"]
        assert "memory" in data["data"]
        assert "disk" in data["data"]

    async def test_get_summary_custom_window(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test metrics summary with custom time window"""
        response = client.get(
            "/api/v1/observability/infrastructure/summary?time_window=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        mock_infrastructure_metrics.get_metrics_summary.assert_called_with(
            time_window_minutes=10
        )

    async def test_get_summary_invalid_window(
        self, client: TestClient, auth_headers: dict
    ):
        """Test metrics summary with invalid time window"""
        response = client.get(
            "/api/v1/observability/infrastructure/summary?time_window=0",
            headers=auth_headers
        )

        # Should reject invalid time window (< 1 or > 60)
        assert response.status_code == 422


@pytest.mark.asyncio
class TestInfrastructureHealth:
    """Tests for infrastructure health check endpoint"""

    async def test_health_check_healthy(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test health check with healthy status"""
        response = client.get(
            "/api/v1/observability/infrastructure/health",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["status"] == "healthy"
        assert data["data"]["warnings"] == []
        assert data["data"]["critical"] == []
        assert "thresholds" in data["data"]

    async def test_health_check_with_warnings(
        self, client: TestClient, auth_headers: dict
    ):
        """Test health check with warning conditions"""
        with patch('apps.backend.api.v1.endpoints.observability.infrastructure_metrics') as mock:
            mock.check_resource_thresholds = AsyncMock(return_value={
                "status": "degraded",
                "warnings": ["CPU usage high: 75.3%"],
                "critical": [],
                "thresholds": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            response = client.get(
                "/api/v1/observability/infrastructure/health",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "degraded"
            assert len(data["data"]["warnings"]) == 1

    async def test_health_check_critical(
        self, client: TestClient, auth_headers: dict
    ):
        """Test health check with critical conditions"""
        with patch('apps.backend.api.v1.endpoints.observability.infrastructure_metrics') as mock:
            mock.check_resource_thresholds = AsyncMock(return_value={
                "status": "unhealthy",
                "warnings": [],
                "critical": ["Memory usage critical: 95.2%"],
                "thresholds": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            response = client.get(
                "/api/v1/observability/infrastructure/health",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "unhealthy"
            assert len(data["data"]["critical"]) == 1


@pytest.mark.asyncio
class TestInfrastructureReport:
    """Tests for comprehensive infrastructure report endpoint"""

    async def test_comprehensive_report_success(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test successful comprehensive report retrieval"""
        response = client.get(
            "/api/v1/observability/infrastructure/report",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "data" in data

        # Verify all report sections
        assert "platform" in data["data"]
        assert "system" in data["data"]
        assert "process" in data["data"]
        assert "threshold_check" in data["data"]
        assert "health_score" in data["data"]

        # Verify health score
        assert data["data"]["health_score"] == 85.5

        # Verify platform info
        assert data["data"]["platform"]["system"] == "Linux"

        # Verify threshold check
        assert data["data"]["threshold_check"]["status"] == "healthy"

    async def test_comprehensive_report_cached_data(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test that report data is collected efficiently"""
        # Make multiple requests
        for _ in range(3):
            response = client.get(
                "/api/v1/observability/infrastructure/report",
                headers=auth_headers
            )
            assert response.status_code == 200

        # Verify the mock was called for each request
        assert mock_infrastructure_metrics.get_comprehensive_report.call_count == 3


@pytest.mark.asyncio
class TestInfrastructureMetricsIntegration:
    """Integration tests for infrastructure metrics"""

    async def test_metrics_consistency(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test that metrics are consistent across endpoints"""
        # Get system metrics
        system_response = client.get(
            "/api/v1/observability/infrastructure/system",
            headers=auth_headers
        )

        # Get comprehensive report
        report_response = client.get(
            "/api/v1/observability/infrastructure/report",
            headers=auth_headers
        )

        assert system_response.status_code == 200
        assert report_response.status_code == 200

        system_data = system_response.json()["data"]
        report_data = report_response.json()["data"]

        # Verify CPU metrics match
        assert system_data["cpu"]["percent"] == report_data["system"]["cpu_percent"]

    async def test_all_endpoints_authenticated(
        self, client: TestClient, auth_headers: dict, mock_infrastructure_metrics
    ):
        """Test that all infrastructure endpoints require authentication"""
        endpoints = [
            "/api/v1/observability/infrastructure/system",
            "/api/v1/observability/infrastructure/process",
            "/api/v1/observability/infrastructure/platform",
            "/api/v1/observability/infrastructure/summary",
            "/api/v1/observability/infrastructure/health",
            "/api/v1/observability/infrastructure/report",
        ]

        for endpoint in endpoints:
            # Without auth headers
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"

            # With auth headers
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200, f"Endpoint {endpoint} should succeed with auth"


# Fixtures for test client and authentication
@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def client(mock_infrastructure_metrics):
    """Test client with mocked dependencies"""
    from apps.backend.main import app
    return TestClient(app)
