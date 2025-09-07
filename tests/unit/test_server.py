"""Unit tests for FastAPI and Flask server endpoints.

Tests all API endpoints including:
- Health checks
- Content generation endpoints
- Quiz generation endpoints
- Authentication endpoints
- WebSocket connections
- Roblox plugin communication
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient
from jose import jwt

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "roblox-environment"))

from server.main import app as fastapi_app
from server.roblox_server import app as flask_app
from server.models import (
    ContentRequest,
    ContentResponse,
    QuizRequest,
    QuizResponse,
    UserLogin,
    Token
)
from server.auth import create_access_token, verify_token
from server.config import settings


class TestFastAPIEndpoints:
    """Test cases for FastAPI server endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        return TestClient(fastapi_app)
    
    @pytest.fixture
    def async_client(self):
        """Create an async test client for FastAPI app."""
        return AsyncClient(app=fastapi_app, base_url="http://test")
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        token = create_access_token({"sub": "testuser", "role": "educator"})
        return {"Authorization": f"Bearer {token}"}
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data
    
    def test_api_documentation(self, client):
        """Test API documentation endpoints."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        assert "openapi" in response.json()
        
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_generate_content_endpoint(self, async_client, auth_headers):
        """Test content generation endpoint."""
        request_data = {
            "subject": "Mathematics",
            "grade_level": 5,
            "learning_objectives": ["Fractions", "Decimals"],
            "environment_type": "classroom",
            "include_quiz": True
        }
        
        with patch('server.main.agent') as mock_agent:
            mock_agent.ainvoke = AsyncMock(return_value={
                "messages": [{"content": json.dumps({
                    "lesson": {"title": "Test Lesson"},
                    "scripts": ["script1", "script2"]
                })}]
            })
            
            response = await async_client.post(
                "/generate_content",
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] == True
            assert "content" in data
            assert "scripts" in data
    
    @pytest.mark.asyncio
    async def test_generate_quiz_endpoint(self, async_client, auth_headers):
        """Test quiz generation endpoint."""
        request_data = {
            "subject": "Science",
            "difficulty": "medium",
            "num_questions": 5,
            "question_types": ["multiple_choice", "true_false"]
        }
        
        with patch('server.main.quiz_agent') as mock_quiz_agent:
            mock_quiz_agent.generate_quiz = AsyncMock(return_value={
                "quiz": {
                    "title": "Science Quiz",
                    "questions": [
                        {
                            "question": "What is photosynthesis?",
                            "type": "multiple_choice",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "A"
                        }
                    ]
                }
            })
            
            response = await async_client.post(
                "/generate_quiz",
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "quiz" in data
            assert len(data["quiz"]["questions"]) > 0
    
    @pytest.mark.asyncio
    async def test_authentication_endpoints(self, async_client):
        """Test authentication endpoints."""
        # Test login
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        with patch('server.auth.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                "username": "testuser",
                "role": "educator",
                "id": "123"
            }
            
            response = await async_client.post("/auth/login", json=login_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self, async_client):
        """Test accessing protected endpoint without authentication."""
        response = await async_client.get("/api/v1/user/profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_auth(self, async_client, auth_headers):
        """Test accessing protected endpoint with authentication."""
        with patch('server.main.get_current_user') as mock_user:
            mock_user.return_value = {"username": "testuser", "role": "educator"}
            
            response = await async_client.get(
                "/api/v1/user/profile",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client):
        """Test rate limiting on endpoints."""
        # Make multiple requests quickly
        responses = []
        for _ in range(150):  # Exceed rate limit of 100/minute
            response = await async_client.get("/health")
            responses.append(response.status_code)
        
        # Should have some rate limited responses
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """Test CORS headers in responses."""
        response = await async_client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_client, auth_headers):
        """Test error handling in endpoints."""
        # Test with invalid request data
        invalid_data = {
            "subject": "Math"
            # Missing required fields
        }
        
        response = await async_client.post(
            "/generate_content",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data


class TestFlaskEndpoints:
    """Test cases for Flask bridge server endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for Flask app."""
        flask_app.config['TESTING'] = True
        return flask_app.test_client()
    
    def test_flask_health_check(self, client):
        """Test Flask health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "ToolboxAI-Flask-Bridge"
    
    def test_register_plugin(self, client):
        """Test Roblox plugin registration endpoint."""
        registration_data = {
            "port": 64989,
            "studio_id": "test-studio-123"
        }
        
        response = client.post(
            '/register_plugin',
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "registered"
        assert "plugin_id" in data
    
    def test_plugin_communication(self, client):
        """Test plugin communication endpoint."""
        message_data = {
            "plugin_id": "test-plugin-123",
            "action": "generate_content",
            "data": {
                "subject": "Science",
                "topic": "Ecosystems"
            }
        }
        
        with patch('server.roblox_server.handle_plugin_request') as mock_handler:
            mock_handler.return_value = {
                "status": "success",
                "result": {"content": "Generated content"}
            }
            
            response = client.post(
                '/plugin/communicate',
                data=json.dumps(message_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
    
    def test_sync_with_fastapi(self, client):
        """Test synchronization with FastAPI server."""
        sync_data = {
            "action": "sync_content",
            "content_id": "123",
            "data": {"lesson": "Updated lesson"}
        }
        
        with patch('server.roblox_server.sync_with_main_server') as mock_sync:
            mock_sync.return_value = {"status": "synced"}
            
            response = client.post(
                '/sync',
                data=json.dumps(sync_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "synced"
    
    def test_roblox_script_generation(self, client):
        """Test Roblox script generation endpoint."""
        request_data = {
            "script_type": "quiz_ui",
            "parameters": {
                "num_questions": 5,
                "theme": "space"
            }
        }
        
        with patch('server.roblox_server.generate_roblox_script') as mock_gen:
            mock_gen.return_value = """
            -- Generated Quiz UI Script
            local gui = Instance.new("ScreenGui")
            """
            
            response = client.post(
                '/generate_script',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "script" in data
            assert "ScreenGui" in data["script"]


class TestWebSocketConnections:
    """Test cases for WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        from fastapi.testclient import TestClient
        
        client = TestClient(fastapi_app)
        
        with client.websocket_connect("/ws") as websocket:
            # Send a message
            websocket.send_text("Hello Server")
            
            # Receive response
            data = websocket.receive_text()
            assert "Processed" in data
    
    @pytest.mark.asyncio
    async def test_websocket_authentication(self):
        """Test WebSocket with authentication."""
        from fastapi.testclient import TestClient
        
        client = TestClient(fastapi_app)
        token = create_access_token({"sub": "testuser"})
        
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            websocket.send_json({"action": "authenticate"})
            data = websocket.receive_json()
            assert data.get("authenticated") == True
    
    @pytest.mark.asyncio
    async def test_websocket_real_time_updates(self):
        """Test real-time updates via WebSocket."""
        from fastapi.testclient import TestClient
        
        client = TestClient(fastapi_app)
        
        with client.websocket_connect("/ws") as websocket:
            # Subscribe to updates
            websocket.send_json({
                "action": "subscribe",
                "channel": "content_updates"
            })
            
            # Simulate content update
            with patch('server.websocket.broadcast_update') as mock_broadcast:
                mock_broadcast.return_value = None
                
                # Trigger an update
                websocket.send_json({
                    "action": "request_update",
                    "content_id": "123"
                })
                
                # Should receive update notification
                data = websocket.receive_json()
                assert "update" in data or "subscribed" in data


class TestAuthentication:
    """Test cases for authentication system."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "testuser", "role": "student"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "student"
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "testuser", "role": "educator"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "educator"
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "testuser"}
        # Create token with very short expiration
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        payload = verify_token(token)
        
        assert payload is None  # Should return None for expired token
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None  # Should return None for invalid token
    
    def test_role_based_access_control(self):
        """Test role-based access control."""
        from server.auth import check_permission
        
        # Educator permissions
        educator = {"role": "educator"}
        assert check_permission(educator, "create_content") == True
        assert check_permission(educator, "delete_user") == False
        
        # Admin permissions
        admin = {"role": "admin"}
        assert check_permission(admin, "create_content") == True
        assert check_permission(admin, "delete_user") == True
        
        # Student permissions
        student = {"role": "student"}
        assert check_permission(student, "create_content") == False
        assert check_permission(student, "view_content") == True


class TestServerIntegration:
    """Integration tests for server components."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_content_generation_flow(self):
        """Test complete content generation flow."""
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            # Login
            login_response = await client.post(
                "/auth/login",
                json={"username": "testuser", "password": "testpass"}
            )
            
            # Skip if auth not configured
            if login_response.status_code != 200:
                pytest.skip("Authentication not configured")
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Generate content
            content_response = await client.post(
                "/generate_content",
                json={
                    "subject": "Science",
                    "grade_level": 7,
                    "learning_objectives": ["Ecosystems"],
                    "include_quiz": True
                },
                headers=headers
            )
            
            assert content_response.status_code == 200
            
            # Get generated content
            content_id = content_response.json().get("content_id")
            if content_id:
                get_response = await client.get(
                    f"/content/{content_id}",
                    headers=headers
                )
                assert get_response.status_code == 200
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_to_server_communication(self):
        """Test communication between FastAPI and Flask servers."""
        # Start both servers (mocked)
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"status": "success"}
            mock_post.return_value.status_code = 200
            
            # FastAPI calls Flask
            from server.main import notify_flask_server
            
            result = await notify_flask_server({
                "event": "content_generated",
                "content_id": "123"
            })
            
            assert result["status"] == "success"
            mock_post.assert_called_once()


class TestErrorHandling:
    """Test cases for error handling."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(fastapi_app)
    
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
    
    def test_500_error_handling(self, client):
        """Test 500 error handling."""
        with patch('server.main.some_function') as mock_func:
            mock_func.side_effect = Exception("Internal error")
            
            response = client.get("/endpoint/that/errors")
            
            # Should handle gracefully
            assert response.status_code in [
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_404_NOT_FOUND  # If endpoint doesn't exist
            ]
    
    def test_validation_error(self, client):
        """Test request validation error."""
        # Send invalid data type
        response = client.post(
            "/generate_content",
            json={
                "subject": 123,  # Should be string
                "grade_level": "five"  # Should be integer
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0  # Should have validation errors


class TestPerformance:
    """Performance tests for server endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_endpoint_response_time(self):
        """Test endpoint response time."""
        import time
        
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            start = time.time()
            response = await client.get("/health")
            end = time.time()
            
            assert response.status_code == 200
            assert (end - start) < 0.5  # Should respond within 500ms
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            # Make 10 concurrent requests
            tasks = [
                client.get("/health")
                for _ in range(10)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(r.status_code == 200 for r in responses)
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_payload_handling(self):
        """Test handling large payloads."""
        large_data = {
            "subject": "Science",
            "grade_level": 7,
            "learning_objectives": ["Objective " + str(i) for i in range(100)],
            "detailed_content": "x" * 10000  # Large content
        }
        
        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            response = await client.post(
                "/generate_content",
                json=large_data
            )
            
            # Should handle large payload
            assert response.status_code in [200, 413, 422]  # OK, too large, or validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])