#!/usr/bin/env python3
"""
Dashboard Backend Test Suite
Comprehensive tests for the Dashboard FastAPI backend on port 8001
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from httpx import AsyncClient
import jwt
import redis
from unittest.mock import Mock, patch, AsyncMock

# Test configuration
TEST_CONFIG = {
    "API_URL": "http://127.0.0.1:8001",
    "MAIN_API_URL": "http://127.0.0.1:8008",
    "REDIS_URL": "redis://localhost:6379",
    "JWT_SECRET": "test-secret-key",
    "JWT_ALGORITHM": "HS256",
}


class TestDashboardBackend:
    """Test suite for Dashboard Backend API"""
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client"""
        from main import app
        async with AsyncClient(app=app, base_url=TEST_CONFIG["API_URL"]) as client:
            yield client
    
    @pytest.fixture
    def test_client(self):
        """Create synchronous test client"""
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Generate test authentication headers"""
        token = jwt.encode(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "role": "teacher",
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            TEST_CONFIG["JWT_SECRET"],
            algorithm=TEST_CONFIG["JWT_ALGORITHM"]
        )
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def student_auth_headers(self):
        """Generate student authentication headers"""
        token = jwt.encode(
            {
                "sub": "student-123",
                "email": "student@example.com",
                "role": "student",
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            TEST_CONFIG["JWT_SECRET"],
            algorithm=TEST_CONFIG["JWT_ALGORITHM"]
        )
        return {"Authorization": f"Bearer {token}"}

    # === Authentication Tests ===
    
    async def test_login_success(self, async_client: AsyncClient):
        """Test successful login"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@example.com", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "teacher@example.com"
    
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    async def test_token_refresh(self, async_client: AsyncClient):
        """Test JWT token refresh"""
        # First login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@example.com", "password": "password123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        assert "token" in response.json()
        assert "refresh_token" in response.json()
    
    async def test_logout(self, async_client: AsyncClient, auth_headers: Dict):
        """Test logout functionality"""
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"
    
    # === Class Management Tests ===
    
    async def test_create_class(self, async_client: AsyncClient, auth_headers: Dict):
        """Test class creation"""
        class_data = {
            "name": "Mathematics 101",
            "description": "Basic math concepts",
            "grade_level": 5,
            "subject": "Math",
            "schedule": "MWF 10:00-11:00"
        }
        
        response = await async_client.post(
            "/api/v1/classes",
            json=class_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mathematics 101"
        assert "id" in data
        assert data["teacher_id"] == "test-user-123"
    
    async def test_get_classes(self, async_client: AsyncClient, auth_headers: Dict):
        """Test fetching class list"""
        response = await async_client.get(
            "/api/v1/classes",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_class_details(self, async_client: AsyncClient, auth_headers: Dict):
        """Test fetching specific class details"""
        # Create a class first
        create_response = await async_client.post(
            "/api/v1/classes",
            json={"name": "Test Class", "grade_level": 5},
            headers=auth_headers
        )
        class_id = create_response.json()["id"]
        
        # Get class details
        response = await async_client.get(
            f"/api/v1/classes/{class_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["id"] == class_id
    
    async def test_update_class(self, async_client: AsyncClient, auth_headers: Dict):
        """Test updating class information"""
        # Create a class
        create_response = await async_client.post(
            "/api/v1/classes",
            json={"name": "Original Name", "grade_level": 5},
            headers=auth_headers
        )
        class_id = create_response.json()["id"]
        
        # Update class
        response = await async_client.patch(
            f"/api/v1/classes/{class_id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
    
    async def test_delete_class(self, async_client: AsyncClient, auth_headers: Dict):
        """Test class deletion"""
        # Create a class
        create_response = await async_client.post(
            "/api/v1/classes",
            json={"name": "To Delete", "grade_level": 5},
            headers=auth_headers
        )
        class_id = create_response.json()["id"]
        
        # Delete class
        response = await async_client.delete(
            f"/api/v1/classes/{class_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await async_client.get(
            f"/api/v1/classes/{class_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    # === Assessment Tests ===
    
    async def test_create_assessment(self, async_client: AsyncClient, auth_headers: Dict):
        """Test assessment creation"""
        assessment_data = {
            "title": "Math Quiz 1",
            "class_id": "class-123",
            "type": "quiz",
            "questions": [
                {
                    "question": "What is 2+2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": "4"
                }
            ],
            "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        response = await async_client.post(
            "/api/v1/assessments",
            json=assessment_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Math Quiz 1"
        assert len(data["questions"]) == 1
    
    async def test_submit_assessment(self, async_client: AsyncClient, student_auth_headers: Dict):
        """Test assessment submission by student"""
        submission_data = {
            "assessment_id": "assessment-123",
            "answers": [
                {"question_id": "q1", "answer": "4"}
            ],
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        response = await async_client.post(
            "/api/v1/assessments/submit",
            json=submission_data,
            headers=student_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "feedback" in data
    
    # === WebSocket Tests ===
    
    def test_websocket_connection(self, test_client):
        """Test WebSocket connection establishment"""
        with test_client.websocket_connect("/ws") as websocket:
            # Send test message
            websocket.send_json({"type": "ping"})
            
            # Receive response
            data = websocket.receive_json()
            assert data["type"] == "pong"
    
    def test_websocket_room_join(self, test_client, auth_headers):
        """Test joining WebSocket room"""
        with test_client.websocket_connect(
            "/ws",
            headers=auth_headers
        ) as websocket:
            # Join class room
            websocket.send_json({
                "type": "join_room",
                "room": "class-123"
            })
            
            data = websocket.receive_json()
            assert data["type"] == "room_joined"
            assert data["room"] == "class-123"
    
    def test_websocket_broadcast(self, test_client, auth_headers):
        """Test WebSocket message broadcasting"""
        with test_client.websocket_connect(
            "/ws",
            headers=auth_headers
        ) as ws1:
            with test_client.websocket_connect(
                "/ws",
                headers=auth_headers
            ) as ws2:
                # Both join same room
                ws1.send_json({"type": "join_room", "room": "test-room"})
                ws2.send_json({"type": "join_room", "room": "test-room"})
                
                # Clear join confirmations
                ws1.receive_json()
                ws2.receive_json()
                
                # Send broadcast message
                ws1.send_json({
                    "type": "broadcast",
                    "room": "test-room",
                    "message": "Hello everyone!"
                })
                
                # Both should receive
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                
                assert data1["message"] == "Hello everyone!"
                assert data2["message"] == "Hello everyone!"
    
    # === Roblox Integration Tests ===
    
    async def test_roblox_content_generation(self, async_client: AsyncClient, auth_headers: Dict):
        """Test Roblox content generation request"""
        request_data = {
            "class_id": "class-123",
            "subject": "Science",
            "grade_level": 7,
            "learning_objectives": ["Solar System", "Planets"],
            "environment_type": "space_station"
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "success": True,
                "world_id": "world-123",
                "scripts": ["script1.lua"]
            }
            
            response = await async_client.post(
                "/api/v1/roblox/generate",
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["world_id"] == "world-123"
    
    async def test_roblox_progress_sync(self, async_client: AsyncClient, student_auth_headers: Dict):
        """Test Roblox progress synchronization"""
        progress_data = {
            "world_id": "world-123",
            "progress": 75,
            "achievements": ["explorer", "problem_solver"],
            "time_spent": 1800  # 30 minutes
        }
        
        response = await async_client.post(
            "/api/v1/roblox/progress",
            json=progress_data,
            headers=student_auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Progress updated"
    
    # === Dashboard Overview Tests ===
    
    async def test_dashboard_overview(self, async_client: AsyncClient, auth_headers: Dict):
        """Test dashboard overview endpoint"""
        response = await async_client.get(
            "/api/v1/dashboard/overview",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_students" in data
        assert "total_classes" in data
        assert "active_assessments" in data
        assert "recent_activity" in data
    
    async def test_student_progress(self, async_client: AsyncClient, auth_headers: Dict):
        """Test student progress tracking"""
        response = await async_client.get(
            "/api/v1/students/student-123/progress",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "overall_progress" in data
        assert "achievements" in data
        assert "completed_assessments" in data
    
    # === Error Handling Tests ===
    
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test accessing protected endpoint without auth"""
        response = await async_client.get("/api/v1/classes")
        assert response.status_code == 401
    
    async def test_invalid_token(self, async_client: AsyncClient):
        """Test with invalid JWT token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get("/api/v1/classes", headers=headers)
        assert response.status_code == 401
    
    async def test_expired_token(self, async_client: AsyncClient):
        """Test with expired JWT token"""
        expired_token = jwt.encode(
            {
                "sub": "test-user",
                "exp": datetime.utcnow() - timedelta(hours=1)
            },
            TEST_CONFIG["JWT_SECRET"],
            algorithm=TEST_CONFIG["JWT_ALGORITHM"]
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/api/v1/classes", headers=headers)
        assert response.status_code == 401
    
    async def test_role_based_access(self, async_client: AsyncClient, student_auth_headers: Dict):
        """Test role-based access control"""
        # Student trying to create a class (teacher-only)
        response = await async_client.post(
            "/api/v1/classes",
            json={"name": "Test", "grade_level": 5},
            headers=student_auth_headers
        )
        assert response.status_code == 403
    
    # === Performance Tests ===
    
    async def test_concurrent_requests(self, async_client: AsyncClient, auth_headers: Dict):
        """Test handling concurrent requests"""
        tasks = []
        for i in range(10):
            task = async_client.get(
                "/api/v1/dashboard/overview",
                headers=auth_headers
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            assert response.status_code == 200
    
    async def test_rate_limiting(self, async_client: AsyncClient, auth_headers: Dict):
        """Test rate limiting"""
        # Send many requests quickly
        for i in range(100):
            response = await async_client.get(
                "/api/v1/dashboard/overview",
                headers=auth_headers
            )
            
            if response.status_code == 429:
                # Rate limit hit
                assert "Rate limit exceeded" in response.json()["detail"]
                break
        else:
            # Should have hit rate limit
            pytest.fail("Rate limit not enforced")


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests with main FastAPI backend"""
    
    async def test_cross_service_auth(self):
        """Test authentication across Dashboard and Main API"""
        # Login via Dashboard
        async with AsyncClient(base_url=TEST_CONFIG["API_URL"]) as client:
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": "teacher@example.com", "password": "password123"}
            )
            token = login_response.json()["token"]
        
        # Use token with Main API
        async with AsyncClient(base_url=TEST_CONFIG["MAIN_API_URL"]) as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/health", headers=headers)
            assert response.status_code == 200
    
    async def test_content_generation_flow(self):
        """Test complete content generation flow"""
        async with AsyncClient(base_url=TEST_CONFIG["API_URL"]) as dashboard_client:
            # Login
            login_response = await dashboard_client.post(
                "/api/v1/auth/login",
                json={"email": "teacher@example.com", "password": "password123"}
            )
            headers = {"Authorization": f"Bearer {login_response.json()['token']}"}
            
            # Request content generation
            generation_response = await dashboard_client.post(
                "/api/v1/roblox/generate",
                json={
                    "subject": "Math",
                    "grade_level": 5,
                    "learning_objectives": ["Addition", "Subtraction"]
                },
                headers=headers
            )
            
            assert generation_response.status_code == 200
            assert "world_id" in generation_response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])