"""OWASP Security Testing Suite for ToolBoxAI.

This module implements comprehensive security tests based on OWASP Top 10
vulnerabilities to ensure the application is protected against common attacks.
"""

import json
import time
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from apps.backend.main import app


class OWASPSecurityTester:
    """OWASP security testing implementation."""

    def __init__(self, client: TestClient):
        self.client = client
        self.vulnerabilities: list[dict] = []

    def report_vulnerability(
        self,
        category: str,
        severity: str,
        description: str,
        endpoint: str,
        payload: str | None = None,
    ):
        """Record a discovered vulnerability."""
        self.vulnerabilities.append(
            {
                "category": category,
                "severity": severity,
                "description": description,
                "endpoint": endpoint,
                "payload": payload,
                "timestamp": time.time(),
            }
        )


@pytest.fixture
def security_tester():
    """Provide OWASP security tester."""
    client = TestClient(app)
    return OWASPSecurityTester(client)


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Provide authenticated headers for testing."""
    token = mock_jwt_token(user_id=1, role="student")
    return {"Authorization": f"Bearer {token}"}


# ============================================
# A01:2021 – Broken Access Control
# ============================================


@pytest.mark.security
class TestBrokenAccessControl:
    """Test for broken access control vulnerabilities."""

    def test_should_prevent_unauthorized_access_to_admin_endpoints(self, security_tester):
        """Test that non-admin users cannot access admin endpoints."""
        # Test without authentication
        response = security_tester.client.get("/api/v1/admin/users")
        assert response.status_code in [401, 403], "Admin endpoint accessible without auth"

        # Test with student role
        student_token = "Bearer test-student-token"
        response = security_tester.client.get(
            "/api/v1/admin/users", headers={"Authorization": student_token}
        )
        assert response.status_code == 403, "Admin endpoint accessible to students"

    def test_should_prevent_horizontal_privilege_escalation(self, security_tester, auth_headers):
        """Test that users cannot access other users' data."""
        # Try to access another user's profile
        response = security_tester.client.get("/api/v1/users/2/profile", headers=auth_headers)
        assert response.status_code in [403, 404], "Can access other user's profile"

        # Try to modify another user's data
        response = security_tester.client.put(
            "/api/v1/users/2/profile",
            json={"email": "hacked@example.com"},
            headers=auth_headers,
        )
        assert response.status_code in [403, 404], "Can modify other user's data"

    def test_should_enforce_cors_policy(self, security_tester):
        """Test CORS policy enforcement."""
        # Test from unauthorized origin
        response = security_tester.client.get(
            "/api/v1/content", headers={"Origin": "http://evil.com"}
        )
        assert (
            "Access-Control-Allow-Origin" not in response.headers
            or response.headers.get("Access-Control-Allow-Origin") != "http://evil.com"
        )


# ============================================
# A02:2021 – Cryptographic Failures
# ============================================


@pytest.mark.security
class TestCryptographicFailures:
    """Test for cryptographic vulnerabilities."""

    def test_should_not_expose_sensitive_data_in_responses(self, security_tester, auth_headers):
        """Test that sensitive data is not exposed."""
        response = security_tester.client.get("/api/v1/users/me", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            # Check that password hashes are not exposed
            assert "password" not in data
            assert "password_hash" not in data
            assert "salt" not in data

    def test_should_use_secure_jwt_configuration(self, security_tester):
        """Test JWT security configuration."""
        # Test that weak algorithms are rejected
        weak_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0."
        response = security_tester.client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {weak_token}"}
        )
        assert response.status_code == 401, "Accepts 'none' algorithm JWT"

    def test_should_enforce_https_in_production(self, security_tester):
        """Test HTTPS enforcement."""
        response = security_tester.client.get("/api/v1/health")
        # Check for security headers
        assert response.headers.get("Strict-Transport-Security"), "Missing HSTS header"


# ============================================
# A03:2021 – Injection
# ============================================


@pytest.mark.security
class TestInjection:
    """Test for injection vulnerabilities."""

    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "' OR 1=1--",
        "1' AND '1' = '1",
    ]

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//",
        "<iframe src=javascript:alert('XSS')>",
    ]

    def test_should_prevent_sql_injection(self, security_tester, auth_headers):
        """Test SQL injection prevention."""
        for payload in self.SQL_INJECTION_PAYLOADS:
            # Test in search parameter
            response = security_tester.client.get(
                f"/api/v1/content/search?q={quote(payload)}", headers=auth_headers
            )
            assert response.status_code != 500, f"SQL injection possible with: {payload}"

            # Test in POST body
            response = security_tester.client.post(
                "/api/v1/content",
                json={"title": payload, "content": "test"},
                headers=auth_headers,
            )
            assert response.status_code != 500, f"SQL injection in POST with: {payload}"

    def test_should_prevent_xss_attacks(self, security_tester, auth_headers):
        """Test XSS prevention."""
        for payload in self.XSS_PAYLOADS:
            # Test in content creation
            response = security_tester.client.post(
                "/api/v1/content",
                json={"title": "Test", "content": payload},
                headers=auth_headers,
            )

            if response.status_code == 201:
                # Verify the payload is properly escaped
                created_content = response.json()
                assert payload not in str(created_content).replace(
                    "\\", ""
                ), f"XSS payload not escaped: {payload}"

    def test_should_prevent_command_injection(self, security_tester, auth_headers):
        """Test command injection prevention."""
        command_payloads = [
            "; ls -la",
            "| whoami",
            "$(cat /etc/passwd)",
            "`rm -rf /`",
        ]

        for payload in command_payloads:
            response = security_tester.client.post(
                "/api/v1/agents/execute",
                json={"command": payload},
                headers=auth_headers,
            )
            # Should either reject or safely handle
            assert response.status_code in [
                400,
                403,
                422,
            ], f"Command injection possible with: {payload}"


# ============================================
# A04:2021 – Insecure Design
# ============================================


@pytest.mark.security
class TestInsecureDesign:
    """Test for insecure design patterns."""

    def test_should_implement_rate_limiting(self, security_tester):
        """Test rate limiting implementation."""
        # Make multiple rapid requests
        endpoint = "/api/v1/auth/login"
        for i in range(100):
            response = security_tester.client.post(
                endpoint,
                json={"username": "test", "password": "wrong"},
            )
            if response.status_code == 429:
                # Rate limiting is working
                return

        pytest.fail("No rate limiting detected after 100 requests")

    def test_should_validate_business_logic(self, security_tester, auth_headers):
        """Test business logic validation."""
        # Try to submit negative values
        response = security_tester.client.post(
            "/api/v1/assessments/submit",
            json={"score": -100, "assessment_id": 1},
            headers=auth_headers,
        )
        assert response.status_code in [400, 422], "Accepts negative scores"

        # Try to submit score > 100
        response = security_tester.client.post(
            "/api/v1/assessments/submit",
            json={"score": 999999, "assessment_id": 1},
            headers=auth_headers,
        )
        assert response.status_code in [400, 422], "Accepts invalid high scores"


# ============================================
# A05:2021 – Security Misconfiguration
# ============================================


@pytest.mark.security
class TestSecurityMisconfiguration:
    """Test for security misconfiguration."""

    def test_should_not_expose_debug_information(self, security_tester):
        """Test that debug information is not exposed."""
        # Trigger an error
        response = security_tester.client.get("/api/v1/nonexistent")

        if response.status_code >= 400:
            error_text = response.text.lower()
            # Check for stack traces or sensitive info
            assert "traceback" not in error_text, "Stack trace exposed"
            assert "sqlalchemy" not in error_text, "Database details exposed"
            assert "/home/" not in error_text, "File paths exposed"

    def test_should_have_security_headers(self, security_tester):
        """Test presence of security headers."""
        response = security_tester.client.get("/api/v1/health")

        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
        ]

        missing_headers = []
        for header in required_headers:
            if header not in response.headers:
                missing_headers.append(header)

        assert not missing_headers, f"Missing security headers: {missing_headers}"

    def test_should_not_have_default_credentials(self, security_tester):
        """Test for default credentials."""
        default_creds = [
            ("admin", "admin"),
            ("admin", "password"),
            ("test", "test"),
            ("demo", "demo"),
        ]

        for username, password in default_creds:
            response = security_tester.client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            assert response.status_code != 200, f"Default credentials work: {username}/{password}"


# ============================================
# A06:2021 – Vulnerable Components
# ============================================


@pytest.mark.security
class TestVulnerableComponents:
    """Test for vulnerable and outdated components."""

    def test_should_not_expose_component_versions(self, security_tester):
        """Test that component versions are not exposed."""
        response = security_tester.client.get("/api/v1/health")

        # Check response headers
        assert (
            "Server" not in response.headers
            or "version" not in response.headers.get("Server", "").lower()
        )
        assert "X-Powered-By" not in response.headers


# ============================================
# A07:2021 – Identification and Authentication
# ============================================


@pytest.mark.security
class TestAuthenticationFailures:
    """Test for authentication and identification failures."""

    def test_should_enforce_password_complexity(self, security_tester):
        """Test password complexity requirements."""
        weak_passwords = [
            "password",
            "12345678",
            "qwerty123",
            "admin123",
        ]

        for password in weak_passwords:
            response = security_tester.client.post(
                "/api/v1/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": password,
                },
            )
            assert response.status_code in [400, 422], f"Weak password accepted: {password}"

    def test_should_prevent_user_enumeration(self, security_tester):
        """Test that user enumeration is prevented."""
        # Test with existing user
        response1 = security_tester.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        # Test with non-existing user
        response2 = security_tester.client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistentuser123", "password": "wrongpassword"},
        )

        # Response should be identical to prevent enumeration
        assert response1.status_code == response2.status_code
        # Response time should be similar (within 100ms)
        # This would require timing measurements

    def test_should_implement_account_lockout(self, security_tester):
        """Test account lockout after failed attempts."""
        username = "testuser"

        # Make multiple failed login attempts
        for i in range(10):
            response = security_tester.client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": "wrongpassword"},
            )

        # Account should be locked or rate limited
        response = security_tester.client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "correctpassword"},
        )
        assert response.status_code in [403, 429], "No account lockout implemented"


# ============================================
# Test Runner and Reporting
# ============================================


@pytest.mark.security
def test_generate_security_report(security_tester):
    """Generate a security testing report."""
    # Run all security tests and collect results
    report = {
        "timestamp": time.time(),
        "owasp_version": "2021",
        "tests_run": 0,
        "vulnerabilities_found": len(security_tester.vulnerabilities),
        "severity_breakdown": {},
        "recommendations": [],
    }

    # Analyze vulnerabilities by severity
    for vuln in security_tester.vulnerabilities:
        severity = vuln["severity"]
        report["severity_breakdown"][severity] = report["severity_breakdown"].get(severity, 0) + 1

    # Add recommendations
    if report["vulnerabilities_found"] > 0:
        report["recommendations"] = [
            "Review and fix all critical vulnerabilities immediately",
            "Implement automated security testing in CI/CD pipeline",
            "Schedule regular security audits",
            "Keep all dependencies up to date",
        ]

    # Save report
    with open("security_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*60}")
    print("OWASP Security Test Report")
    print(f"{'='*60}")
    print(f"Vulnerabilities Found: {report['vulnerabilities_found']}")
    print(f"Severity Breakdown: {report['severity_breakdown']}")
    print(f"{'='*60}\n")
