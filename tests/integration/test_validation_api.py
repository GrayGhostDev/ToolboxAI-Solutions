import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Integration tests for the Validation API

Tests the REST API endpoints for Roblox script validation.
"""

import asyncio
import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app and validation router
try:
    from apps.backend.api.v1.endpoints.validation import validation_router
    from apps.backend.main import app
except ImportError:
    # Create a minimal test app if main app is not available
    from fastapi import FastAPI

    from apps.backend.api.v1.endpoints.validation import validation_router

    app = FastAPI()
    app.include_router(validation_router, prefix="/api/v1")


class TestValidationAPI:
    """Integration tests for validation API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {"email": "teacher@test.com", "role": "teacher", "id": "test_teacher_123"}

    @pytest.fixture
    def sample_script_request(self):
        """Sample script validation request"""
        return {
            "script_code": """
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function greetPlayer(player)
    print("Hello, " .. player.Name .. "!")
end

game.Players.PlayerAdded:Connect(greetPlayer)
            """,
            "script_name": "greeting_script.lua",
            "validation_type": "comprehensive",
            "grade_level": "elementary",
            "subject": "computer_science",
            "learning_objectives": ["Learn basic Roblox scripting", "Understand event connections"],
            "strict_mode": False,
            "include_suggestions": True,
            "educational_context": True,
        }

    @pytest.fixture
    def mock_validation_report(self):
        """Mock validation report"""
        return {
            "script_name": "greeting_script.lua",
            "validation_timestamp": "2024-01-01T12:00:00",
            "validation_duration_ms": 150.0,
            "overall_status": "passed",
            "overall_score": 85.0,
            "syntax_validation": {
                "success": True,
                "issues": [],
                "syntax_valid": True,
                "api_compatible": True,
                "performance_score": 90.0,
                "memory_score": 85.0,
                "complexity_score": 80.0,
                "total_lines": 8,
                "function_count": 1,
                "variable_count": 2,
            },
            "security_analysis": {
                "overall_score": 95.0,
                "threat_level": "low",
                "findings": [],
                "remote_events_secure": True,
                "recommendations": [],
            },
            "quality_assessment": {
                "overall_score": 85.0,
                "quality_level": "good",
                "issues": [],
                "recommendations": [],
            },
            "compliance_check": {
                "overall_compliance": "compliant",
                "violations": [],
                "platform_ready": True,
            },
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "auto_fix_suggestions": [],
            "scores": {
                "syntax": 90.0,
                "security": 95.0,
                "quality": 85.0,
                "compliance": 100.0,
                "educational": 88.0,
            },
            "deployment_ready": True,
            "educational_ready": True,
            "platform_compliant": True,
        }

    def test_validate_script_success(
        self, client, sample_script_request, mock_validation_report, mock_user
    ):
        """Test successful script validation"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            # Mock authentication
            mock_auth.return_value = Mock(**mock_user)

            # Mock validation engine
            mock_engine.validate_script.return_value = Mock(**mock_validation_report)
            mock_engine.export_report.return_value = json.dumps(mock_validation_report)

            # Make request
            response = client.post("/api/v1/validation/validate", json=sample_script_request)

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "validation_id" in data
            assert data["summary"]["script_name"] == "greeting_script.lua"
            assert data["summary"]["overall_status"] == "passed"
            assert data["summary"]["overall_score"] == 85.0
            assert data["summary"]["deployment_ready"] is True
            assert "report" in data

    def test_validate_script_unauthorized(self, client, sample_script_request):
        """Test validation with unauthorized user"""
        with patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth:
            # Mock unauthorized user
            mock_auth.return_value = Mock(
                email="student@test.com", role="student", id="student_123"
            )

            # Make request
            response = client.post("/api/v1/validation/validate", json=sample_script_request)

            # Assertions
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]

    def test_validate_script_invalid_request(self, client, mock_user):
        """Test validation with invalid request data"""
        with patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(**mock_user)

            # Request with missing required fields
            invalid_request = {
                "script_name": "test.lua"
                # Missing script_code
            }

            # Make request
            response = client.post("/api/v1/validation/validate", json=invalid_request)

            # Assertions
            assert response.status_code == 422  # Validation error

    def test_validate_script_with_security_issues(self, client, sample_script_request, mock_user):
        """Test validation with security issues"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Mock report with security issues
            security_report = {
                "script_name": "insecure_script.lua",
                "validation_timestamp": "2024-01-01T12:00:00",
                "validation_duration_ms": 200.0,
                "overall_status": "failed",
                "overall_score": 25.0,
                "critical_issues": ["loadstring usage detected", "No input validation"],
                "warnings": ["Performance issues detected"],
                "deployment_ready": False,
                "educational_ready": False,
                "platform_compliant": False,
                "scores": {"syntax": 90.0, "security": 20.0, "quality": 60.0, "compliance": 30.0},
            }

            mock_engine.validate_script.return_value = Mock(**security_report)
            mock_engine.export_report.return_value = json.dumps(security_report)

            # Update request with insecure code
            sample_script_request["script_code"] = "loadstring('malicious code')()"
            sample_script_request["script_name"] = "insecure_script.lua"

            # Make request
            response = client.post("/api/v1/validation/validate", json=sample_script_request)

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["summary"]["overall_status"] == "failed"
            assert data["summary"]["overall_score"] == 25.0
            assert data["summary"]["deployment_ready"] is False
            assert data["summary"]["critical_issues_count"] == 2

    def test_batch_validation_success(self, client, sample_script_request, mock_user):
        """Test successful batch validation"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Mock batch validation
            mock_reports = [
                Mock(
                    script_name="script1.lua",
                    overall_status="passed",
                    overall_score=85.0,
                    validation_duration_ms=100.0,
                    critical_issues=[],
                    warnings=[],
                    deployment_ready=True,
                    educational_ready=True,
                    platform_compliant=True,
                ),
                Mock(
                    script_name="script2.lua",
                    overall_status="passed_with_warnings",
                    overall_score=75.0,
                    validation_duration_ms=120.0,
                    critical_issues=[],
                    warnings=["Minor performance issue"],
                    deployment_ready=True,
                    educational_ready=True,
                    platform_compliant=True,
                ),
            ]

            mock_engine.batch_validate.return_value = mock_reports

            # Create batch request
            batch_request = {
                "scripts": [
                    sample_script_request.copy(),
                    {**sample_script_request, "script_name": "script2.lua"},
                ],
                "parallel_processing": True,
            }

            # Make request
            response = client.post("/api/v1/validation/validate/batch", json=batch_request)

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "batch_id" in data
            assert data["total_scripts"] == 2
            assert data["processed_scripts"] == 2
            assert data["failed_scripts"] == 0
            assert len(data["results"]) == 2

    def test_batch_validation_with_failures(self, client, sample_script_request, mock_user):
        """Test batch validation with some failures"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Mock batch validation with mixed results
            mock_reports = [
                Mock(
                    script_name="script1.lua",
                    overall_status="passed",
                    overall_score=85.0,
                    validation_duration_ms=100.0,
                    critical_issues=[],
                    warnings=[],
                    deployment_ready=True,
                    educational_ready=True,
                    platform_compliant=True,
                ),
                Mock(
                    script_name="script2.lua",
                    overall_status="failed",
                    overall_score=30.0,
                    validation_duration_ms=150.0,
                    critical_issues=["Syntax error"],
                    warnings=[],
                    deployment_ready=False,
                    educational_ready=False,
                    platform_compliant=False,
                ),
            ]

            mock_engine.batch_validate.return_value = mock_reports

            # Create batch request
            batch_request = {
                "scripts": [
                    sample_script_request.copy(),
                    {
                        **sample_script_request,
                        "script_name": "script2.lua",
                        "script_code": "invalid syntax",
                    },
                ],
                "parallel_processing": True,
            }

            # Make request
            response = client.post("/api/v1/validation/validate/batch", json=batch_request)

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["total_scripts"] == 2
            assert data["processed_scripts"] == 2
            assert data["failed_scripts"] == 1

    def test_get_validation_statistics(self, client, mock_user):
        """Test getting validation statistics"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Mock statistics
            mock_stats = {
                "total_validations": 150,
                "passed_validations": 120,
                "failed_validations": 30,
                "average_score": 78.5,
                "common_issues": {
                    "Missing input validation": 15,
                    "Performance issues": 8,
                    "Code style violations": 12,
                },
            }

            mock_engine.get_validation_statistics.return_value = mock_stats

            # Make request
            response = client.get("/api/v1/validation/statistics")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["total_validations"] == 150
            assert data["passed_validations"] == 120
            assert data["failed_validations"] == 30
            assert data["average_score"] == 78.5
            assert "common_issues" in data

    def test_generate_secure_template(self, client, mock_user):
        """Test generating secure code templates"""
        with patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(**mock_user)

            # Make request
            response = client.post(
                "/api/v1/validation/templates/secure", params={"template_type": "remote_event"}
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["template_type"] == "remote_event"
            assert "code" in data
            assert "RemoteEvent" in data["code"]
            assert "rate limiting" in data["code"].lower()

    def test_generate_invalid_template(self, client, mock_user):
        """Test generating invalid template type"""
        with patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(**mock_user)

            # Make request
            response = client.post(
                "/api/v1/validation/templates/secure", params={"template_type": "invalid_template"}
            )

            # Assertions
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_security_checklist(self, client, mock_user):
        """Test getting security checklist"""
        with patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(**mock_user)

            # Make request
            response = client.get("/api/v1/validation/checklists/security")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, dict)
            assert "Input Validation" in data
            assert "Remote Events" in data
            assert isinstance(data["Input Validation"], list)

    def test_get_compliance_checklist(self, client, mock_user):
        """Test getting compliance checklist"""
        with patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth:
            mock_auth.return_value = Mock(**mock_user)

            # Make request
            response = client.get("/api/v1/validation/checklists/compliance")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, dict)
            assert "Community Standards" in data
            assert "Safety Requirements" in data
            assert isinstance(data["Community Standards"], list)

    def test_validation_engine_error(self, client, sample_script_request, mock_user):
        """Test handling of validation engine errors"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Mock validation engine to raise an exception
            mock_engine.validate_script.side_effect = Exception("Engine failure")

            # Make request
            response = client.post("/api/v1/validation/validate", json=sample_script_request)

            # Assertions
            assert response.status_code == 500
            assert "Validation failed" in response.json()["detail"]

    def test_validation_report_formats(
        self, client, sample_script_request, mock_validation_report, mock_user
    ):
        """Test different validation report formats"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)
            mock_engine.validate_script.return_value = Mock(**mock_validation_report)

            # Test JSON format
            mock_engine.export_report.return_value = json.dumps(mock_validation_report)
            response = client.post(
                "/api/v1/validation/validate?report_format=json", json=sample_script_request
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["report"], dict)

            # Test summary format
            mock_engine.export_report.return_value = "Summary report text"
            response = client.post(
                "/api/v1/validation/validate?report_format=summary", json=sample_script_request
            )
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data["report"]

    def test_large_script_validation(self, client, mock_user):
        """Test validation of large scripts"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Create large script request
            large_script = "print('Hello')\n" * 1000  # 1000 lines
            large_request = {
                "script_code": large_script,
                "script_name": "large_script.lua",
                "validation_type": "comprehensive",
                "educational_context": False,
            }

            # Mock successful validation
            mock_report = Mock(
                script_name="large_script.lua",
                overall_status="passed",
                overall_score=80.0,
                validation_duration_ms=500.0,
                critical_issues=[],
                warnings=["Large script detected"],
                deployment_ready=True,
                educational_ready=True,
                platform_compliant=True,
            )

            mock_engine.validate_script.return_value = mock_report
            mock_engine.export_report.return_value = json.dumps({})

            # Make request
            response = client.post("/api/v1/validation/validate", json=large_request)

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["summary"]["script_name"] == "large_script.lua"

    def test_concurrent_validations(self, client, sample_script_request, mock_user):
        """Test handling of concurrent validation requests"""
        with (
            patch("apps.backend.api.v1.endpoints.validation.get_current_user") as mock_auth,
            patch("apps.backend.api.v1.endpoints.validation.validation_engine") as mock_engine,
        ):

            mock_auth.return_value = Mock(**mock_user)

            # Mock validation with slight delay
            async def mock_validate(request):
                await asyncio.sleep(0.1)  # Simulate processing time
                return Mock(
                    script_name=request.script_name,
                    overall_status="passed",
                    overall_score=85.0,
                    validation_duration_ms=100.0,
                    critical_issues=[],
                    warnings=[],
                    deployment_ready=True,
                    educational_ready=True,
                    platform_compliant=True,
                )

            mock_engine.validate_script.side_effect = mock_validate
            mock_engine.export_report.return_value = json.dumps({})

            # Make multiple concurrent requests
            requests = []
            for i in range(3):
                req = sample_script_request.copy()
                req["script_name"] = f"concurrent_script_{i}.lua"
                requests.append(req)

            # Send requests concurrently (in real scenario would use async client)
            responses = []
            for req in requests:
                response = client.post("/api/v1/validation/validate", json=req)
                responses.append(response)

            # Assertions
            assert all(r.status_code == 200 for r in responses)
            assert all(r.json()["success"] for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
