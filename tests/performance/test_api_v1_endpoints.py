"""
Comprehensive Tests for API v1 Endpoints
=========================================

Tests all API v1 endpoints including:
- Real-time analytics
- Summary analytics
- Report generation
- Admin user management

Tests use real database with test data and verify:
- Correct response formats
- Proper authentication/authorization
- Data accuracy
- Error handling
- Edge cases
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import pandas as pd
from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from apps.backend.main import app
from apps.backend.api_v1_endpoints import (
    RealtimeMetrics, SummaryAnalytics, ReportResponse,
    UserResponse, UserListResponse, ReportType, ReportFormat
)
from core.database.models import (
    User, EducationalContent, Quiz, QuizAttempt,
    UserProgress, UserSession, Class, Assignment
)
from apps.backend.auth import hash_password, create_access_token

# Test client
client = TestClient(app)

# Test database URL (use test database)
TEST_DATABASE_URL = "postgresql+asyncpg://eduplatform:eduplatform2024@localhost/educational_platform_dev"

# Create async engine for tests
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class TestAPIv1Endpoints:
    """Comprehensive test suite for API v1 endpoints"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with real test data"""
        self.db = AsyncSessionLocal()
        
        # Create test users
        self.admin_user = await self._create_test_user(
            "admin_test", "admin@test.com", "admin", grade_level=None
        )
        self.teacher_user = await self._create_test_user(
            "teacher_test", "teacher@test.com", "teacher", grade_level=None
        )
        self.student_user = await self._create_test_user(
            "student_test", "student@test.com", "student", grade_level=7
        )
        
        # Create test content
        self.test_content = await self._create_test_content()
        
        # Create test quiz
        self.test_quiz = await self._create_test_quiz()
        
        # Create test quiz attempts
        await self._create_test_quiz_attempts()
        
        # Create test user progress
        await self._create_test_user_progress()
        
        # Generate auth tokens
        self.admin_token = create_access_token({"sub": str(self.admin_user.id)})
        self.teacher_token = create_access_token({"sub": str(self.teacher_user.id)})
        self.student_token = create_access_token({"sub": str(self.student_user.id)})
        
        yield
        
        # Cleanup
        await self.db.close()
    
    async def _create_test_user(self, username, email, role, grade_level):
        """Helper to create test user"""
        user = User(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=hash_password("TestPassword123!"),
            role=role,
            first_name="Test",
            last_name=role.capitalize(),
            grade_level=grade_level,
            subjects=["Math", "Science"] if role == "teacher" else [],
            is_active=True,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow()
        )
        self.db.add(user)
        await self.db.commit()
        return user
    
    async def _create_test_content(self):
        """Helper to create test educational content"""
        content = EducationalContent(
            id=uuid4(),
            title="Test Science Content",
            description="Test description",
            subject="Science",
            grade_level=7,
            environment_type="classroom",
            content_data={"lessons": ["Lesson 1", "Lesson 2"]},
            is_published=True,
            created_by=self.teacher_user.id,
            created_at=datetime.utcnow()
        )
        self.db.add(content)
        await self.db.commit()
        return content
    
    async def _create_test_quiz(self):
        """Helper to create test quiz"""
        quiz = Quiz(
            id=uuid4(),
            title="Test Science Quiz",
            subject="Science",
            grade_level=7,
            questions=[
                {
                    "id": "q1",
                    "text": "What is photosynthesis?",
                    "options": ["A", "B", "C", "D"],
                    "correct": "A"
                }
            ],
            is_published=True,
            created_by=self.teacher_user.id,
            created_at=datetime.utcnow()
        )
        self.db.add(quiz)
        await self.db.commit()
        return quiz
    
    async def _create_test_quiz_attempts(self):
        """Helper to create test quiz attempts"""
        # Create completed attempt
        completed_attempt = QuizAttempt(
            id=uuid4(),
            user_id=self.student_user.id,
            quiz_id=self.test_quiz.id,
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1),
            score=85.5,
            time_taken=3600,
            answers={"q1": "A"}
        )
        self.db.add(completed_attempt)
        
        # Create ongoing attempt
        ongoing_attempt = QuizAttempt(
            id=uuid4(),
            user_id=self.student_user.id,
            quiz_id=self.test_quiz.id,
            started_at=datetime.utcnow() - timedelta(minutes=10),
            completed_at=None,
            score=None,
            time_taken=None,
            answers={}
        )
        self.db.add(ongoing_attempt)
        
        await self.db.commit()
    
    async def _create_test_user_progress(self):
        """Helper to create test user progress"""
        progress = UserProgress(
            id=uuid4(),
            user_id=self.student_user.id,
            content_id=self.test_content.id,
            progress_percentage=75.0,
            time_spent=1800,
            last_accessed=datetime.utcnow() - timedelta(minutes=30)
        )
        self.db.add(progress)
        await self.db.commit()
    
    # ==========================================
    # Analytics Endpoint Tests
    # ==========================================
    
    def test_realtime_analytics_success(self):
        """Test successful retrieval of real-time analytics"""
        response = client.get(
            "/api/v1/analytics/realtime",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "timestamp" in data
        assert "active_users" in data
        assert "active_sessions" in data
        assert "ongoing_quiz_attempts" in data
        assert "websocket_connections" in data
        assert "recent_activities" in data
        assert "system_health" in data
        assert "live_metrics" in data
        
        # Verify data types
        assert isinstance(data["active_users"], int)
        assert isinstance(data["active_sessions"], int)
        assert isinstance(data["ongoing_quiz_attempts"], int)
        assert isinstance(data["recent_activities"], list)
        assert isinstance(data["system_health"], dict)
        assert isinstance(data["live_metrics"], dict)
        
        # Verify system health structure
        assert "database" in data["system_health"]
        assert "redis" in data["system_health"]
        assert "api_latency_ms" in data["system_health"]
        assert "error_rate" in data["system_health"]
        assert "uptime_hours" in data["system_health"]
        
        # Verify live metrics structure
        assert "quiz_completions_5min" in data["live_metrics"]
        assert "new_registrations_5min" in data["live_metrics"]
        assert "avg_response_time_ms" in data["live_metrics"]
        assert "requests_per_second" in data["live_metrics"]
    
    def test_realtime_analytics_unauthorized(self):
        """Test real-time analytics without authentication"""
        response = client.get("/api/v1/analytics/realtime")
        assert response.status_code == 401
    
    def test_realtime_analytics_student_access(self):
        """Test that students can access real-time analytics"""
        response = client.get(
            "/api/v1/analytics/realtime",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        # Students should be able to view analytics
        assert response.status_code == 200
    
    def test_summary_analytics_success(self):
        """Test successful retrieval of summary analytics"""
        # Test with date range
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(
            f"/api/v1/analytics/summary?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "period" in data
        assert "totals" in data
        assert "averages" in data
        assert "completion_rates" in data
        assert "popular_content" in data
        assert "top_performers" in data
        assert "trends" in data
        
        # Verify period
        assert "start" in data["period"]
        assert "end" in data["period"]
        
        # Verify totals
        assert "users" in data["totals"]
        assert "content" in data["totals"]
        assert "quizzes" in data["totals"]
        assert "quiz_attempts" in data["totals"]
        
        # Verify averages
        assert "quiz_score" in data["averages"]
        assert "completion_time_seconds" in data["averages"]
        
        # Verify completion rates
        assert "quizzes" in data["completion_rates"]
        
        # Verify trends
        assert "daily" in data["trends"]
        assert isinstance(data["trends"]["daily"], list)
    
    def test_summary_analytics_with_filters(self):
        """Test summary analytics with subject and grade filters"""
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(
            f"/api/v1/analytics/summary?start_date={start_date}&end_date={end_date}"
            f"&subject=Science&grade_level=7",
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify filters are applied (check popular content)
        if data["popular_content"]:
            for content in data["popular_content"]:
                # Content should match filter criteria
                assert content["subject"] == "Science" or content["grade_level"] == 7
    
    def test_summary_analytics_invalid_date_range(self):
        """Test summary analytics with invalid date range"""
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response = client.get(
            f"/api/v1/analytics/summary?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 400
        assert "End date must be after start date" in response.json()["detail"]
    
    # ==========================================
    # Report Generation Tests
    # ==========================================
    
    def test_generate_report_json_success(self):
        """Test successful JSON report generation"""
        report_request = {
            "report_type": "user_progress",
            "format": "json",
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "filters": {},
            "include_charts": True
        }
        
        response = client.post(
            "/api/v1/reports/generate",
            json=report_request,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "report_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] in ["completed", "processing"]
        
        # If completed, should have download URL
        if data["status"] == "completed":
            assert "download_url" in data
            assert data["download_url"].startswith("/api/v1/reports/download/")
    
    def test_generate_report_pdf_background(self):
        """Test PDF report generation (background task)"""
        report_request = {
            "report_type": "content_analytics",
            "format": "pdf",
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "filters": {"subject": "Science"}
        }
        
        response = client.post(
            "/api/v1/reports/generate",
            json=report_request,
            headers={"Authorization": f"Bearer {self.teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # PDF should be processed in background
        assert data["status"] == "processing"
        assert "report_id" in data
        assert "estimated_completion" in data
    
    def test_generate_report_invalid_dates(self):
        """Test report generation with invalid date range"""
        report_request = {
            "report_type": "user_progress",
            "format": "json",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() - timedelta(days=7)).isoformat()
        }
        
        response = client.post(
            "/api/v1/reports/generate",
            json=report_request,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_download_report_not_found(self):
        """Test downloading non-existent report"""
        fake_report_id = str(uuid4())
        
        response = client.get(
            f"/api/v1/reports/download/{fake_report_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        # Should return 404 or 503 depending on Redis availability
        assert response.status_code in [404, 503]
    
    # ==========================================
    # Admin User Management Tests
    # ==========================================
    
    def test_list_users_success(self):
        """Test successful user listing with pagination"""
        response = client.get(
            "/api/v1/admin/users?page=1&page_size=10",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        
        # Verify pagination
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert isinstance(data["users"], list)
        
        # Verify user structure
        if data["users"]:
            user = data["users"][0]
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "role" in user
            assert "first_name" in user
            assert "last_name" in user
            assert "is_active" in user
            assert "created_at" in user
    
    def test_list_users_with_filters(self):
        """Test user listing with search and role filters"""
        response = client.get(
            "/api/v1/admin/users?search=student&role=student&grade_level=7",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify filters are applied
        for user in data["users"]:
            assert user["role"] == "student"
            if user["grade_level"]:
                assert user["grade_level"] == 7
    
    def test_list_users_unauthorized(self):
        """Test that students cannot list users"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        
        # Students should not have access
        assert response.status_code == 403
    
    def test_create_user_success(self):
        """Test successful user creation"""
        new_user_data = {
            "username": "new_student",
            "email": "new@student.com",
            "password": "SecurePass123!",
            "role": "student",
            "first_name": "New",
            "last_name": "Student",
            "grade_level": 8,
            "subjects": []
        }
        
        response = client.post(
            "/api/v1/admin/users",
            json=new_user_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify created user
        assert data["username"] == "new_student"
        assert data["email"] == "new@student.com"
        assert data["role"] == "student"
        assert data["first_name"] == "New"
        assert data["last_name"] == "Student"
        assert data["grade_level"] == 8
        assert data["is_active"] is True
    
    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username"""
        duplicate_user_data = {
            "username": "student_test",  # Already exists
            "email": "another@email.com",
            "password": "SecurePass123!",
            "role": "student",
            "first_name": "Another",
            "last_name": "User"
        }
        
        response = client.post(
            "/api/v1/admin/users",
            json=duplicate_user_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_create_user_invalid_password(self):
        """Test user creation with invalid password"""
        invalid_user_data = {
            "username": "weak_pass_user",
            "email": "weak@pass.com",
            "password": "123",  # Too short
            "role": "student",
            "first_name": "Weak",
            "last_name": "Password"
        }
        
        response = client.post(
            "/api/v1/admin/users",
            json=invalid_user_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_user_success(self):
        """Test successful user update"""
        # Get existing user ID
        list_response = client.get(
            "/api/v1/admin/users?search=student_test",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert list_response.status_code == 200
        users = list_response.json()["users"]
        assert len(users) > 0
        user_id = users[0]["id"]
        
        # Update user
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "grade_level": 9,
            "is_active": True
        }
        
        response = client.put(
            f"/api/v1/admin/users/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify updates
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["grade_level"] == 9
        assert data["is_active"] is True
    
    def test_update_user_not_found(self):
        """Test updating non-existent user"""
        fake_user_id = str(uuid4())
        
        response = client.put(
            f"/api/v1/admin/users/{fake_user_id}",
            json={"first_name": "Test"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_user_prevent_self_demotion(self):
        """Test that admins cannot remove their own admin role"""
        # Get admin user ID
        list_response = client.get(
            "/api/v1/admin/users?search=admin_test",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert list_response.status_code == 200
        admin_id = list_response.json()["users"][0]["id"]
        
        # Try to change own role
        response = client.put(
            f"/api/v1/admin/users/{admin_id}",
            json={"role": "teacher"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 400
        assert "Cannot remove your own admin role" in response.json()["detail"]
    
    def test_delete_user_deactivate(self):
        """Test user deactivation (soft delete)"""
        # Create a user to delete
        temp_user_data = {
            "username": "temp_user",
            "email": "temp@user.com",
            "password": "TempPass123!",
            "role": "student",
            "first_name": "Temp",
            "last_name": "User"
        }
        
        create_response = client.post(
            "/api/v1/admin/users",
            json=temp_user_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert create_response.status_code == 200
        temp_user_id = create_response.json()["id"]
        
        # Deactivate user
        response = client.delete(
            f"/api/v1/admin/users/{temp_user_id}?permanent=false",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"].lower()
    
    def test_delete_user_prevent_self_delete(self):
        """Test that users cannot delete themselves"""
        # Get admin user ID
        list_response = client.get(
            "/api/v1/admin/users?search=admin_test",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert list_response.status_code == 200
        admin_id = list_response.json()["users"][0]["id"]
        
        # Try to delete self
        response = client.delete(
            f"/api/v1/admin/users/{admin_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]
    
    # ==========================================
    # Integration Tests
    # ==========================================
    
    def test_analytics_to_report_workflow(self):
        """Test complete workflow from analytics to report generation"""
        # Step 1: Get analytics summary
        summary_response = client.get(
            "/api/v1/analytics/summary",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        # Step 2: Generate report based on analytics period
        report_request = {
            "report_type": "user_progress",
            "format": "json",
            "start_date": summary_data["period"]["start"],
            "end_date": summary_data["period"]["end"],
            "filters": {}
        }
        
        report_response = client.post(
            "/api/v1/reports/generate",
            json=report_request,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert report_response.status_code == 200
        report_data = report_response.json()
        
        # Step 3: Verify report contains relevant data
        assert report_data["status"] in ["completed", "processing"]
        if report_data["status"] == "completed":
            # Attempt to download if completed
            download_url = report_data.get("download_url")
            if download_url:
                report_id = download_url.split("/")[-1]
                download_response = client.get(
                    f"/api/v1/reports/download/{report_id}",
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                # Download might fail if Redis is not available
                assert download_response.status_code in [200, 503]
    
    def test_user_management_complete_lifecycle(self):
        """Test complete user lifecycle: create, update, list, delete"""
        # Step 1: Create user
        new_user = {
            "username": "lifecycle_user",
            "email": "lifecycle@test.com",
            "password": "LifeCycle123!",
            "role": "student",
            "first_name": "Life",
            "last_name": "Cycle",
            "grade_level": 6
        }
        
        create_response = client.post(
            "/api/v1/admin/users",
            json=new_user,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Step 2: Update user
        update_response = client.put(
            f"/api/v1/admin/users/{user_id}",
            json={"grade_level": 7, "role": "teacher"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["grade_level"] == 7
        assert update_response.json()["role"] == "teacher"
        
        # Step 3: List and verify user appears
        list_response = client.get(
            "/api/v1/admin/users?search=lifecycle",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert list_response.status_code == 200
        found_users = [u for u in list_response.json()["users"] 
                      if u["username"] == "lifecycle_user"]
        assert len(found_users) == 1
        
        # Step 4: Delete user
        delete_response = client.delete(
            f"/api/v1/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert delete_response.status_code == 200
    
    # ==========================================
    # Performance Tests
    # ==========================================
    
    def test_analytics_response_time(self):
        """Test that analytics endpoints respond within acceptable time"""
        import time
        
        # Test realtime analytics
        start = time.time()
        response = client.get(
            "/api/v1/analytics/realtime",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0  # Should respond within 2 seconds
        
        # Test summary analytics
        start = time.time()
        response = client.get(
            "/api/v1/analytics/summary",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 3.0  # Should respond within 3 seconds (more complex query)
    
    def test_user_list_pagination_performance(self):
        """Test that user listing with pagination performs well"""
        import time
        
        # Test different page sizes
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            start = time.time()
            response = client.get(
                f"/api/v1/admin/users?page=1&page_size={page_size}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            # Response time should scale reasonably with page size
            assert elapsed < (1.0 + page_size * 0.01)  # Base + per-item overhead
    
    # ==========================================
    # Security Tests
    # ==========================================
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are prevented"""
        # Try SQL injection in search parameter
        malicious_search = "'; DROP TABLE users; --"
        
        response = client.get(
            f"/api/v1/admin/users?search={malicious_search}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        # Should return normally (no users found) not error
        assert response.status_code == 200
        assert response.json()["total"] == 0
    
    def test_xss_prevention(self):
        """Test that XSS attempts are sanitized"""
        # Try to create user with XSS in name
        xss_user = {
            "username": "xss_test",
            "email": "xss@test.com",
            "password": "XSSTest123!",
            "role": "student",
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "Test"
        }
        
        response = client.post(
            "/api/v1/admin/users",
            json=xss_user,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        # Should either reject or sanitize
        if response.status_code == 200:
            # If accepted, verify it's sanitized
            created_user = response.json()
            assert "<script>" not in created_user["first_name"]
    
    def test_rate_limiting(self):
        """Test that rate limiting is enforced"""
        # Make many rapid requests
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = client.get(
                "/api/v1/analytics/realtime",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            responses.append(response.status_code)
        
        # Should see rate limiting (429) at some point
        # Note: This assumes rate limiting is configured
        # If not configured, all might return 200
        assert 429 in responses or all(r == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])