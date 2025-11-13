"""
Unit Tests for Compliance API Endpoints

Tests compliance status, reports, audit logs, and verification endpoints.

Phase 1 Week 1: Authentication & user management endpoint tests
Phase B: Converted to TestClient pattern
"""

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import router and models
from apps.backend.api.v1.endpoints.compliance import (
    router,
)
from apps.backend.core.security.jwt_handler import create_access_token
from tests.utils import APITestHelper


@pytest.fixture
def app():
    """Create FastAPI app with compliance router."""
    app = FastAPI()
    app.include_router(router, prefix="/compliance")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create admin JWT token."""
    return create_access_token(
        data={"sub": "admin", "role": "admin", "user_id": 1, "id": "admin-1"}
    )


@pytest.fixture
def admin_headers(admin_token):
    """Create authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# Test Get Compliance Status Endpoint
# ============================================================================


class TestGetComplianceStatus:
    """Test compliance status retrieval endpoint."""

    def test_get_compliance_status_all_categories(self, client):
        """Test getting all compliance statuses."""
        response = client.get("/compliance/status")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)
        assert len(data) > 0
        # Should have FERPA, COPPA, GDPR
        categories = [s["category"] for s in data]
        assert "FERPA" in categories
        assert "COPPA" in categories
        assert "GDPR" in categories

    def test_get_compliance_status_structure(self, client):
        """Test compliance status response structure."""
        response = client.get("/compliance/status")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        first_status = data[0]
        assert "compliant" in first_status
        assert "category" in first_status
        assert "last_checked" in first_status
        assert "issues" in first_status
        assert "recommendations" in first_status

    def test_get_compliance_status_filter_by_category(self, client):
        """Test filtering compliance status by category."""
        response = client.get("/compliance/status?category=FERPA")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)
        assert len(data) > 0
        # All results should be FERPA
        for status in data:
            assert status["category"].upper() == "FERPA"

    def test_get_compliance_status_filter_coppa(self, client):
        """Test filtering by COPPA category."""
        response = client.get("/compliance/status?category=COPPA")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        assert all(s["category"].upper() == "COPPA" for s in data)

    def test_get_compliance_status_filter_gdpr(self, client):
        """Test filtering by GDPR category."""
        response = client.get("/compliance/status?category=GDPR")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        assert all(s["category"].upper() == "GDPR" for s in data)

    def test_get_compliance_status_case_insensitive_filter(self, client):
        """Test that category filter is case insensitive."""
        response_upper = client.get("/compliance/status?category=FERPA")
        response_lower = client.get("/compliance/status?category=ferpa")
        response_mixed = client.get("/compliance/status?category=Ferpa")

        data_upper = response_upper.json()
        data_lower = response_lower.json()
        data_mixed = response_mixed.json()

        assert len(data_upper) == len(data_lower) == len(data_mixed)

    def test_get_compliance_status_unknown_category_returns_empty(self, client):
        """Test filtering by unknown category returns empty list."""
        response = client.get("/compliance/status?category=UNKNOWN")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_compliance_status_all_compliant(self, client):
        """Test that all default statuses are compliant."""
        response = client.get("/compliance/status")

        data = APITestHelper.assert_success_response(response)

        for status in data:
            assert status["compliant"] is True

    def test_get_compliance_status_has_recommendations(self, client):
        """Test that statuses include recommendations."""
        response = client.get("/compliance/status")

        data = APITestHelper.assert_success_response(response)

        for status in data:
            assert isinstance(status["recommendations"], list)
            # Default statuses should have recommendations
            if status["category"] in ["FERPA", "COPPA", "GDPR"]:
                assert len(status["recommendations"]) > 0


# ============================================================================
# Test Get Compliance Reports Endpoint
# ============================================================================


class TestGetComplianceReports:
    """Test compliance reports retrieval endpoint."""

    def test_get_compliance_reports_default(self, client):
        """Test getting compliance reports with default parameters."""
        response = client.get("/compliance/reports")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_compliance_reports_structure(self, client):
        """Test compliance report response structure."""
        response = client.get("/compliance/reports")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        report = data[0]
        assert "report_id" in report
        assert "generated_at" in report
        assert "school_id" in report
        assert "categories" in report
        assert "overall_compliant" in report
        assert "risk_level" in report

    def test_get_compliance_reports_with_school_filter(self, client):
        """Test filtering reports by school ID."""
        school_id = "SCH-001"
        response = client.get(f"/compliance/reports?school_id={school_id}")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        # All reports should have the specified school_id
        for report in data:
            assert report["school_id"] == school_id

    def test_get_compliance_reports_with_limit(self, client):
        """Test limiting number of reports returned."""
        response = client.get("/compliance/reports?limit=3")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)
        assert len(data) <= 3

    def test_get_compliance_reports_max_limit(self, client):
        """Test maximum limit constraint."""
        # Endpoint limits to minimum of requested limit and 5
        response = client.get("/compliance/reports?limit=100")

        data = APITestHelper.assert_success_response(response)

        assert len(data) <= 5  # Mock implementation caps at 5

    def test_get_compliance_reports_min_limit(self, client):
        """Test minimum limit of 1."""
        response = client.get("/compliance/reports?limit=1")

        data = APITestHelper.assert_success_response(response)

        assert len(data) == 1

    def test_get_compliance_reports_have_categories(self, client):
        """Test that reports include compliance categories."""
        response = client.get("/compliance/reports")

        data = APITestHelper.assert_success_response(response)

        for report in data:
            assert isinstance(report["categories"], list)
            assert len(report["categories"]) > 0

    def test_get_compliance_reports_default_compliant(self, client):
        """Test that default reports are compliant."""
        response = client.get("/compliance/reports")

        data = APITestHelper.assert_success_response(response)

        for report in data:
            assert report["overall_compliant"] is True
            assert report["risk_level"] == "low"

    def test_get_compliance_reports_have_valid_report_ids(self, client):
        """Test that reports have properly formatted IDs."""
        response = client.get("/compliance/reports")

        data = APITestHelper.assert_success_response(response)

        for report in data:
            assert report["report_id"].startswith("RPT-")
            assert "-" in report["report_id"]


# ============================================================================
# Test Generate Compliance Report Endpoint
# ============================================================================


class TestGenerateComplianceReport:
    """Test compliance report generation endpoint."""

    def test_generate_compliance_report_success(self, client):
        """Test successful compliance report generation."""
        response = client.post("/compliance/reports")

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_201_CREATED
        )

        assert "report_id" in data
        assert data["report_id"] is not None
        assert "generated_at" in data
        assert isinstance(data["categories"], list)

    def test_generate_compliance_report_with_school_id(self, client):
        """Test generating report with school ID."""
        school_id = "SCH-TEST-001"
        response = client.post(f"/compliance/reports?school_id={school_id}")

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_201_CREATED
        )

        assert data["school_id"] == school_id

    def test_generate_compliance_report_without_school_id(self, client):
        """Test generating report without school ID."""
        response = client.post("/compliance/reports")

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_201_CREATED
        )

        # School ID is optional
        assert data["school_id"] is None

    def test_generate_compliance_report_has_unique_id(self, client):
        """Test that generated reports have unique IDs."""
        response1 = client.post("/compliance/reports")
        response2 = client.post("/compliance/reports")

        data1 = response1.json()
        data2 = response2.json()

        assert data1["report_id"] != data2["report_id"]

    def test_generate_compliance_report_includes_all_categories(self, client):
        """Test that generated report includes all compliance categories."""
        response = client.post("/compliance/reports")

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_201_CREATED
        )

        categories = [c["category"] for c in data["categories"]]
        assert "FERPA" in categories
        assert "COPPA" in categories
        assert "GDPR" in categories

    def test_generate_compliance_report_default_values(self, client):
        """Test that generated report has expected default values."""
        response = client.post("/compliance/reports")

        data = APITestHelper.assert_success_response(
            response, expected_status=status.HTTP_201_CREATED
        )

        assert data["overall_compliant"] is True
        assert data["risk_level"] == "low"

    def test_generate_compliance_report_recent_timestamp(self, client):
        """Test that generated report has recent timestamp."""
        before = datetime.now()
        response = client.post("/compliance/reports")
        after = datetime.now()

        data = response.json()
        generated_at = datetime.fromisoformat(data["generated_at"])

        assert before <= generated_at <= after


# ============================================================================
# Test Get Audit Logs Endpoint
# ============================================================================


class TestGetAuditLogs:
    """Test audit logs retrieval endpoint."""

    def test_get_audit_logs_default(self, client):
        """Test getting audit logs with default parameters."""
        response = client.get("/compliance/audit-logs")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_audit_logs_structure(self, client):
        """Test audit log response structure."""
        response = client.get("/compliance/audit-logs")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        log = data[0]
        assert "log_id" in log
        assert "timestamp" in log
        assert "user_id" in log
        assert "action" in log
        assert "resource" in log
        assert "details" in log
        assert "ip_address" in log
        assert "user_agent" in log

    def test_get_audit_logs_filter_by_user_id(self, client):
        """Test filtering audit logs by user ID."""
        user_id = "USR-TEST-001"
        response = client.get(f"/compliance/audit-logs?user_id={user_id}")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        for log in data:
            assert log["user_id"] == user_id

    def test_get_audit_logs_filter_by_action(self, client):
        """Test filtering audit logs by action type."""
        action = "data_access"
        response = client.get(f"/compliance/audit-logs?action={action}")

        data = APITestHelper.assert_success_response(response)

        assert len(data) > 0
        for log in data:
            assert log["action"] == action

    def test_get_audit_logs_with_limit(self, client):
        """Test limiting number of audit logs."""
        response = client.get("/compliance/audit-logs?limit=5")

        data = APITestHelper.assert_success_response(response)

        assert len(data) <= 5

    def test_get_audit_logs_max_limit(self, client):
        """Test maximum limit for audit logs."""
        # Mock caps at 10 regardless of requested limit
        response = client.get("/compliance/audit-logs?limit=500")

        data = APITestHelper.assert_success_response(response)

        assert len(data) <= 10

    def test_get_audit_logs_with_date_filters(self, client):
        """Test filtering logs by date range."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        response = client.get(
            f"/compliance/audit-logs?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data, list)

    def test_get_audit_logs_have_details(self, client):
        """Test that audit logs include details."""
        response = client.get("/compliance/audit-logs")

        data = APITestHelper.assert_success_response(response)

        for log in data:
            assert isinstance(log["details"], dict)
            assert len(log["details"]) > 0

    def test_get_audit_logs_have_valid_log_ids(self, client):
        """Test that logs have properly formatted IDs."""
        response = client.get("/compliance/audit-logs")

        data = APITestHelper.assert_success_response(response)

        for log in data:
            assert log["log_id"].startswith("LOG-")


# ============================================================================
# Test Verify Compliance Endpoint
# ============================================================================


class TestVerifyCompliance:
    """Test compliance verification endpoint."""

    def test_verify_compliance_ferpa(self, client):
        """Test verifying FERPA compliance."""
        response = client.post("/compliance/verify/FERPA")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "FERPA"
        assert data["compliant"] is True

    def test_verify_compliance_coppa(self, client):
        """Test verifying COPPA compliance."""
        response = client.post("/compliance/verify/COPPA")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "COPPA"
        assert data["compliant"] is True

    def test_verify_compliance_gdpr(self, client):
        """Test verifying GDPR compliance."""
        response = client.post("/compliance/verify/GDPR")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "GDPR"
        assert data["compliant"] is True

    def test_verify_compliance_hipaa_fails(self, client):
        """Test HIPAA compliance verification (should fail)."""
        response = client.post("/compliance/verify/HIPAA")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "HIPAA"
        assert data["compliant"] is False
        assert len(data["issues"]) > 0
        assert len(data["recommendations"]) > 0

    def test_verify_compliance_with_force_check(self, client):
        """Test forcing a new compliance check."""
        response = client.post("/compliance/verify/FERPA?force_check=true")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "FERPA"

    def test_verify_compliance_uppercase_category(self, client):
        """Test that category is converted to uppercase."""
        response = client.post("/compliance/verify/ferpa")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "FERPA"

    def test_verify_compliance_has_recommendations(self, client):
        """Test that compliance verification includes recommendations."""
        response = client.post("/compliance/verify/FERPA")

        data = APITestHelper.assert_success_response(response)

        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

    def test_verify_compliance_hipaa_has_issues(self, client):
        """Test that failed compliance has issues listed."""
        response = client.post("/compliance/verify/HIPAA")

        data = APITestHelper.assert_success_response(response)

        assert data["compliant"] is False
        assert "Encryption" in data["issues"][0]

    def test_verify_compliance_hipaa_has_remediation_recommendations(self, client):
        """Test that failed compliance has remediation recommendations."""
        response = client.post("/compliance/verify/HIPAA")

        data = APITestHelper.assert_success_response(response)

        assert data["compliant"] is False
        recommendations = data["recommendations"]
        assert "encryption" in recommendations[0].lower() or "access" in recommendations[1].lower()


# ============================================================================
# Test Get Compliance Requirements Endpoint
# ============================================================================


class TestGetComplianceRequirements:
    """Test compliance requirements retrieval endpoint."""

    def test_get_compliance_requirements_ferpa(self, client):
        """Test getting FERPA requirements."""
        response = client.get("/compliance/requirements/FERPA")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "FERPA"
        assert "name" in data
        assert "requirements" in data
        assert isinstance(data["requirements"], list)
        assert len(data["requirements"]) > 0

    def test_get_compliance_requirements_coppa(self, client):
        """Test getting COPPA requirements."""
        response = client.get("/compliance/requirements/COPPA")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "COPPA"
        assert "Children's Online Privacy Protection Act" in data["name"]

    def test_get_compliance_requirements_gdpr(self, client):
        """Test getting GDPR requirements."""
        response = client.get("/compliance/requirements/GDPR")

        data = APITestHelper.assert_success_response(response)

        assert data["category"] == "GDPR"
        assert "General Data Protection Regulation" in data["name"]

    def test_get_compliance_requirements_unknown_category(self, client):
        """Test getting requirements for unknown category."""
        response = client.get("/compliance/requirements/UNKNOWN")

        APITestHelper.assert_error_response(
            response, expected_status=status.HTTP_404_NOT_FOUND, expected_detail="not found"
        )

    def test_get_compliance_requirements_case_insensitive(self, client):
        """Test that category lookup is case insensitive."""
        response_upper = client.get("/compliance/requirements/FERPA")
        response_lower = client.get("/compliance/requirements/ferpa")

        data_upper = response_upper.json()
        data_lower = response_lower.json()

        assert data_upper["category"] == data_lower["category"]

    def test_get_compliance_requirements_has_applies_to(self, client):
        """Test that requirements include applicability information."""
        response = client.get("/compliance/requirements/FERPA")

        data = APITestHelper.assert_success_response(response)

        assert "applies_to" in data
        assert isinstance(data["applies_to"], str)
        assert len(data["applies_to"]) > 0

    def test_get_compliance_requirements_has_timestamp(self, client):
        """Test that requirements include last_updated timestamp."""
        response = client.get("/compliance/requirements/FERPA")

        data = APITestHelper.assert_success_response(response)

        assert "last_updated" in data
        # Should be ISO format datetime string
        assert isinstance(data["last_updated"], str)

    def test_get_compliance_requirements_all_categories(self, client):
        """Test getting requirements for all supported categories."""
        categories = ["FERPA", "COPPA", "GDPR"]

        for category in categories:
            response = client.get(f"/compliance/requirements/{category}")
            data = response.json()
            assert data["category"] == category
            assert len(data["requirements"]) > 0


# ============================================================================
# Test Compliance Health Check Endpoint
# ============================================================================


class TestComplianceHealthCheck:
    """Test compliance service health check endpoint."""

    def test_compliance_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/compliance/health")

        data = APITestHelper.assert_success_response(response)

        assert data["status"] == "healthy"
        assert data["service"] == "compliance"

    def test_compliance_health_check_has_timestamp(self, client):
        """Test health check includes timestamp."""
        response = client.get("/compliance/health")

        data = APITestHelper.assert_success_response(response)

        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_compliance_health_check_recent_timestamp(self, client):
        """Test health check timestamp is recent."""
        before = datetime.now()
        response = client.get("/compliance/health")
        after = datetime.now()

        data = response.json()

        # Parse ISO format timestamp
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert before <= timestamp <= after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
