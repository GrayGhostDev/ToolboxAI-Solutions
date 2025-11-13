import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Integration Tests for Enhanced Content Generation Endpoints

Tests the complete enhanced content generation API endpoints including:
- Content generation pipeline initiation
- Status tracking and real-time updates
- Content validation
- Personalization features
- WebSocket connections
- Authentication and rate limiting

Author: ToolboxAI Team
Created: 2025-09-19
Version: 2.0.0
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from apps.backend.api.auth.auth import get_current_user
from apps.backend.main import app
from apps.backend.models.schemas import User


class TestEnhancedContentEndpoints:
    """Test suite for enhanced content generation endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return User(
            id="test-user-123",
            username="test_user",
            email="test@example.com",
            role="teacher",
            first_name="Test",
            last_name="User",
        )

    @pytest.fixture
    def mock_student_user(self):
        """Mock student user"""
        return User(
            id="student-123", username="test_student", email="student@example.com", role="student"
        )

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user"""
        return User(id="admin-123", username="admin", email="admin@example.com", role="admin")

    @pytest.fixture
    def valid_content_request(self):
        """Valid content generation request"""
        return {
            "subject": "Mathematics",
            "grade_level": "6-8",
            "content_type": "lesson",
            "learning_objectives": [
                "Understand basic algebraic concepts",
                "Solve simple equations",
                "Apply algebra to real-world problems",
            ],
            "difficulty_level": "medium",
            "duration_minutes": 45,
            "personalization_enabled": True,
            "roblox_requirements": {"environment_type": "classroom", "max_players": 25},
        }

    @pytest.fixture
    def valid_validation_request(self):
        """Valid content validation request"""
        return {
            "content": {
                "id": "test-content-123",
                "title": "Introduction to Algebra",
                "description": "Basic algebra concepts for middle school",
                "learning_objectives": ["Understand variables", "Solve simple equations"],
                "scripts": [
                    {
                        "name": "MainScript",
                        "code": "local game = require(game:GetService('ReplicatedStorage'):WaitForChild('GameModule'))",
                    }
                ],
                "assets": [{"name": "WhiteBoard", "type": "Model", "file_size_mb": 2.5}],
            },
            "content_type": "lesson",
            "target_age": 12,
        }

    def test_generate_content_success(self, client, mock_user, valid_content_request):
        """Test successful content generation initiation"""

        # Mock the authentication dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post("/api/v1/content/generate", json=valid_content_request)

            assert response.status_code == 200

            data = response.json()
            assert "pipeline_id" in data
            assert data["status"] == "initiated"
            assert data["current_stage"] == "ideation"
            assert data["progress_percentage"] == 0.0
            assert "pusher_channel" in data
            assert "websocket_url" in data

        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_generate_content_invalid_request(self, client, mock_user):
        """Test content generation with invalid request data"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Missing required fields
            invalid_request = {
                "subject": "Math"
                # Missing grade_level, content_type, learning_objectives
            }

            response = client.post("/api/v1/content/generate", json=invalid_request)

            assert response.status_code == 422  # Validation error

        finally:
            app.dependency_overrides.clear()

    def test_generate_content_invalid_content_type(self, client, mock_user, valid_content_request):
        """Test content generation with invalid content type"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            invalid_request = valid_content_request.copy()
            invalid_request["content_type"] = "invalid_type"

            response = client.post("/api/v1/content/generate", json=invalid_request)

            assert response.status_code == 422  # Validation error

        finally:
            app.dependency_overrides.clear()

    def test_generate_content_unauthorized(self, client, valid_content_request):
        """Test content generation without authentication"""

        response = client.post("/api/v1/content/generate", json=valid_content_request)

        assert response.status_code == 401

    @patch("apps.backend.api.v1.endpoints.enhanced_content.generation_sessions")
    def test_get_status_success(self, mock_sessions, client, mock_user):
        """Test successful pipeline status retrieval"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Mock pipeline session
            pipeline_id = "test-pipeline-123"
            mock_sessions.__contains__ = Mock(return_value=True)
            mock_sessions.__getitem__ = Mock(
                return_value={
                    "user_id": mock_user.id,
                    "status": "processing",
                    "current_stage": "generation",
                    "progress": 45.0,
                    "started_at": datetime.now(),
                    "pipeline_state": Mock(errors=[]),
                }
            )

            response = client.get(f"/api/v1/content/status/{pipeline_id}")

            assert response.status_code == 200

            data = response.json()
            assert data["pipeline_id"] == pipeline_id
            assert data["status"] == "processing"
            assert data["current_stage"] == "generation"
            assert data["progress_percentage"] == 45.0

        finally:
            app.dependency_overrides.clear()

    def test_get_status_not_found(self, client, mock_user):
        """Test pipeline status for non-existent pipeline"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.get("/api/v1/content/status/non-existent-pipeline")

            assert response.status_code == 404

        finally:
            app.dependency_overrides.clear()

    @patch("apps.backend.api.v1.endpoints.enhanced_content.generation_sessions")
    def test_get_status_access_denied(self, mock_sessions, client, mock_user):
        """Test pipeline status access denied for different user"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Mock pipeline session belonging to different user
            pipeline_id = "test-pipeline-123"
            mock_sessions.__contains__ = Mock(return_value=True)
            mock_sessions.__getitem__ = Mock(
                return_value={
                    "user_id": "different-user-123",  # Different user
                    "status": "processing",
                }
            )

            response = client.get(f"/api/v1/content/status/{pipeline_id}")

            assert response.status_code == 403

        finally:
            app.dependency_overrides.clear()

    @patch("apps.backend.api.v1.endpoints.enhanced_content.generation_sessions")
    def test_get_content_success(self, mock_sessions, client, mock_user):
        """Test successful content retrieval"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            content_id = "test-content-123"

            # Mock session data
            mock_session_data = {
                "user_id": mock_user.id,
                "pipeline_id": "test-pipeline-123",
                "request": {
                    "content_type": "lesson",
                    "subject": "Mathematics",
                    "grade_level": "6-8",
                },
                "started_at": datetime.now(),
                "quality_score": 0.85,
                "personalization_applied": True,
                "generation_time": 45.2,
                "pipeline_state": Mock(
                    final_content={"title": "Test Lesson"},
                    scripts=[{"name": "TestScript"}],
                    assets=[{"name": "TestAsset"}],
                ),
            }

            # Mock finding content in sessions
            for session in [mock_session_data]:
                session["content_id"] = content_id

            mock_sessions.values = Mock(return_value=[mock_session_data])

            response = client.get(f"/api/v1/content/{content_id}")

            assert response.status_code == 200

            data = response.json()
            assert data["content_id"] == content_id
            assert data["user_id"] == mock_user.id
            assert data["content_type"] == "lesson"
            assert data["quality_score"] == 0.85

        finally:
            app.dependency_overrides.clear()

    def test_validate_content_success(self, client, mock_user, valid_validation_request):
        """Test successful content validation"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "apps.backend.api.v1.endpoints.enhanced_content.get_quality_validator"
            ) as mock_validator:
                # Mock validation report
                mock_report = Mock()
                mock_report.overall_score = 0.85
                mock_report.educational_score = 0.90
                mock_report.technical_score = 0.80
                mock_report.safety_score = 0.95
                mock_report.engagement_score = 0.75
                mock_report.accessibility_score = 0.80
                mock_report.compliant = True
                mock_report.issues = []
                mock_report.warnings = []
                mock_report.recommendations = ["Add more interactive elements"]
                mock_report.__dict__ = {
                    "overall_score": 0.85,
                    "compliant": True,
                    "issues": [],
                    "recommendations": ["Add more interactive elements"],
                }

                mock_validator_instance = Mock()
                mock_validator_instance.validate_content = AsyncMock(return_value=mock_report)
                mock_validator.return_value = mock_validator_instance

                response = client.post("/api/v1/content/validate", json=valid_validation_request)

                assert response.status_code == 200

                data = response.json()
                assert "validation_id" in data
                assert data["overall_score"] == 0.85
                assert data["compliant"] == True
                assert len(data["recommendations"]) > 0

        finally:
            app.dependency_overrides.clear()

    @patch("apps.backend.api.v1.endpoints.enhanced_content.generation_sessions")
    def test_get_history_success(self, mock_sessions, client, mock_user):
        """Test successful content history retrieval"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Mock session data
            mock_sessions_data = [
                {
                    "user_id": mock_user.id,
                    "pipeline_id": "pipeline-1",
                    "content_id": "content-1",
                    "request": {
                        "content_type": "lesson",
                        "subject": "Mathematics",
                        "grade_level": "6-8",
                    },
                    "status": "completed",
                    "started_at": datetime.now(),
                    "quality_score": 0.85,
                },
                {
                    "user_id": "other-user",
                    "pipeline_id": "pipeline-2",
                    "request": {"content_type": "quiz"},
                },
            ]

            mock_sessions.values = Mock(return_value=mock_sessions_data)

            response = client.get("/api/v1/content/history")

            assert response.status_code == 200

            data = response.json()
            assert "items" in data
            assert "total_count" in data
            assert len(data["items"]) == 1  # Only user's content
            assert data["items"][0]["content_type"] == "lesson"

        finally:
            app.dependency_overrides.clear()

    @patch("apps.backend.api.v1.endpoints.enhanced_content.generation_sessions")
    def test_apply_personalization_success(self, mock_sessions, client, mock_user):
        """Test successful content personalization"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            content_id = "test-content-123"

            # Mock session data
            mock_session_data = {
                "user_id": mock_user.id,
                "content_id": content_id,
                "status": "completed",
            }

            mock_sessions.values = Mock(return_value=[mock_session_data])

            personalization_request = {
                "content_id": content_id,
                "personalization_params": {
                    "visual_style": "colorful",
                    "difficulty_adjustment": "easier",
                },
                "learning_style": "visual",
            }

            response = client.post("/api/v1/content/personalize", json=personalization_request)

            assert response.status_code == 200

            data = response.json()
            assert data["success"] == True
            assert data["content_id"] == content_id
            assert "personalization_id" in data

        finally:
            app.dependency_overrides.clear()

    def test_rate_limiting(self, client, mock_user, valid_content_request):
        """Test rate limiting on content generation endpoint"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # This test would need to be run with actual rate limiting enabled
            # For now, just test that the endpoint accepts the request
            response = client.post("/api/v1/content/generate", json=valid_content_request)

            # Should succeed (first request)
            assert response.status_code == 200

        finally:
            app.dependency_overrides.clear()

    def test_admin_access_other_user_content(self, client, mock_admin_user):
        """Test that admin users can access other users' content"""

        app.dependency_overrides[get_current_user] = lambda: mock_admin_user

        try:
            with patch(
                "apps.backend.api.v1.endpoints.enhanced_content.generation_sessions"
            ) as mock_sessions:
                # Mock another user's content
                mock_session_data = {
                    "user_id": "other-user-123",
                    "content_id": "content-123",
                    "request": {
                        "content_type": "lesson",
                        "subject": "Science",
                        "grade_level": "K-2",
                    },
                    "started_at": datetime.now(),
                    "pipeline_state": Mock(
                        final_content={"title": "Science Lesson"}, scripts=[], assets=[]
                    ),
                }

                mock_sessions.values = Mock(return_value=[mock_session_data])

                response = client.get("/api/v1/content/content-123")

                # Admin should have access
                assert response.status_code == 200

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time updates"""

        pipeline_id = "test-pipeline-123"

        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/content/ws/{pipeline_id}") as websocket:
                # Should accept connection

                # Send ping
                websocket.send_text("ping")
                response = websocket.receive_text()
                assert response == "pong"

                # Request status
                websocket.send_text("status")
                # Should receive JSON response (exact content depends on session state)

    def test_content_types_validation(self, client, mock_user, valid_content_request):
        """Test validation of different content types"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            valid_types = [
                "lesson",
                "quiz",
                "activity",
                "scenario",
                "assessment",
                "project",
                "simulation",
            ]

            for content_type in valid_types:
                request = valid_content_request.copy()
                request["content_type"] = content_type

                response = client.post("/api/v1/content/generate", json=request)

                assert response.status_code == 200, f"Failed for content_type: {content_type}"

        finally:
            app.dependency_overrides.clear()

    def test_grade_level_validation(self, client, mock_user, valid_content_request):
        """Test validation of grade levels"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            valid_grades = ["K-2", "3-5", "6-8", "9-12", "college", "adult"]

            for grade in valid_grades:
                request = valid_content_request.copy()
                request["grade_level"] = grade

                response = client.post("/api/v1/content/generate", json=request)

                assert response.status_code == 200, f"Failed for grade_level: {grade}"

        finally:
            app.dependency_overrides.clear()

    def test_learning_objectives_validation(self, client, mock_user, valid_content_request):
        """Test validation of learning objectives"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Test with too few objectives
            request = valid_content_request.copy()
            request["learning_objectives"] = []  # Empty list should fail

            response = client.post("/api/v1/content/generate", json=request)

            assert response.status_code == 422  # Validation error

            # Test with too many objectives
            request["learning_objectives"] = [f"Objective {i}" for i in range(15)]  # More than max

            response = client.post("/api/v1/content/generate", json=request)

            assert response.status_code == 422  # Validation error

        finally:
            app.dependency_overrides.clear()

    def test_duration_validation(self, client, mock_user, valid_content_request):
        """Test validation of duration limits"""

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Test with too short duration
            request = valid_content_request.copy()
            request["duration_minutes"] = 2  # Below minimum

            response = client.post("/api/v1/content/generate", json=request)

            assert response.status_code == 422

            # Test with too long duration
            request["duration_minutes"] = 150  # Above maximum

            response = client.post("/api/v1/content/generate", json=request)

            assert response.status_code == 422

        finally:
            app.dependency_overrides.clear()


@pytest.mark.integration
class TestEnhancedContentIntegration:
    """Integration tests for enhanced content endpoints with real components"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("core.agents.enhanced_content_pipeline"),
        reason="Enhanced content pipeline not available",
    )
    async def test_full_pipeline_integration(self):
        """Test integration with actual pipeline components"""

        # This would test the actual integration with the pipeline
        # when the components are fully implemented
        pass

    @pytest.mark.asyncio
    async def test_database_integration(self):
        """Test integration with database models"""

        # This would test actual database operations
        # when database session management is implemented
        pass

    @pytest.mark.asyncio
    async def test_pusher_integration(self):
        """Test integration with Pusher for real-time updates"""

        # This would test actual Pusher integration
        # when Pusher service is available
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
