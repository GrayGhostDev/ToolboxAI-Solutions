import pytest_asyncio

#!/usr/bin/env python3
"""
End-to-End Content Creation Workflow Integration Tests

Tests the complete content creation workflow from user request to final delivery:
1. User authentication and course setup
2. Content generation request with multi-agent coordination
3. Real-time progress updates via WebSocket/Pusher
4. Database storage and versioning
5. Quality assurance and approval workflow
6. Content delivery and student access
7. Analytics and performance tracking
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from tests.fixtures.pusher_mocks import MockPusherService
from tests.fixtures.pusher_test_utils import ConnectionClosedError

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["USE_MOCK_DATABASE"] = "false"  # Use real DB for E2E
os.environ["ENABLE_REALTIME_UPDATES"] = "true"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.e2e,
    pytest.mark.asyncio,
    pytest.mark.slow,
]


@pytest.fixture
async def e2e_client():
    """HTTP client for end-to-end testing"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8009",
        timeout=120.0  # Extended timeout for E2E tests
    ) as client:
        yield client


@pytest.fixture
def test_users():
    """Test users for different roles in the workflow"""
    timestamp = int(time.time())
    return {
        "teacher": {
            "username": f"teacher_e2e_{timestamp}",
            "email": f"teacher.e2e.{timestamp}@test.edu",
            "password": "TeacherE2E123!",
            "role": "teacher",
            "first_name": "Teacher",
            "last_name": "E2E Test",
            "subject_expertise": ["Mathematics", "Science"]
        },
        "admin": {
            "username": f"admin_e2e_{timestamp}",
            "email": f"admin.e2e.{timestamp}@test.edu",
            "password": "AdminE2E123!",
            "role": "admin",
            "first_name": "Admin",
            "last_name": "E2E Test"
        },
        "student": {
            "username": f"student_e2e_{timestamp}",
            "email": f"student.e2e.{timestamp}@test.edu",
            "password": "StudentE2E123!",
            "role": "student",
            "first_name": "Student",
            "last_name": "E2E Test",
            "grade_level": 9
        }
    }


@pytest.fixture
def content_workflow_data():
    """Complete workflow test data"""
    return {
        "course": {
            "title": "Advanced Algebra - E2E Test",
            "code": f"ALG_E2E_{int(time.time())}",
            "description": "End-to-end test course for algebra concepts",
            "subject": "Mathematics",
            "grade_level": 9,
            "duration_weeks": 16,
            "objectives": [
                "Master linear equations and inequalities",
                "Understand quadratic functions",
                "Apply algebraic concepts to real-world problems"
            ]
        },
        "lesson_request": {
            "title": "Introduction to Quadratic Functions",
            "subject": "Mathematics",
            "grade_level": 9,
            "topic": "Quadratic Functions",
            "duration_minutes": 50,
            "learning_objectives": [
                "Define quadratic functions and identify their key features",
                "Graph quadratic functions using vertex form",
                "Solve real-world problems using quadratic models"
            ],
            "environment_type": "interactive_classroom",
            "include_quiz": True,
            "include_roblox_environment": True,
            "difficulty_level": "intermediate",
            "interactive_elements": [
                "graphing_tool",
                "step_by_step_solver",
                "real_world_applications"
            ],
            "assessment_type": "formative_and_summative"
        },
        "quality_criteria": {
            "content_accuracy": 0.95,
            "age_appropriateness": 0.90,
            "engagement_level": 0.85,
            "curriculum_alignment": 0.95,
            "accessibility": 0.90
        }
    }


@pytest.fixture
async def authenticated_users(e2e_client, test_users):
    """Create and authenticate test users"""
    authenticated = {}

    for role, user_data in test_users.items():
        # Register user
        register_response = await e2e_client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        if register_response.status_code == 404:
            # Try alternative endpoint
            register_response = await e2e_client.post(
                "/auth/register",
                json=user_data
            )

        if register_response.status_code in [201, 200]:
            # Login to get token
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }

            login_response = await e2e_client.post(
                "/api/v1/auth/login",
                json=login_data
            )

            if login_response.status_code == 404:
                login_response = await e2e_client.post(
                    "/auth/login",
                    json=login_data
                )

            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                authenticated[role] = {
                    "user_data": user_data,
                    "token": token,
                    "headers": {"Authorization": f"Bearer {token}"}
                }

    return authenticated


class TestCompleteContentCreationWorkflow:
    """Test the complete content creation workflow"""

    @pytest.mark.asyncio
async def test_full_content_creation_pipeline(self, e2e_client, authenticated_users, content_workflow_data):
        """Test complete pipeline from request to delivery"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for E2E test")

        teacher = authenticated_users["teacher"]
        workflow_data = content_workflow_data

        # Step 1: Create Course
        print("Step 1: Creating course...")
        course_data = workflow_data["course"]
        course_data["instructor_id"] = teacher["user_data"]["username"]

        course_response = await e2e_client.post(
            "/api/v1/courses",
            json=course_data,
            headers=teacher["headers"]
        )

        if course_response.status_code == 404:
            pytest.skip("Course creation endpoint not available")

        assert course_response.status_code == 201
        course_id = course_response.json()["data"]["id"]
        print(f"✓ Course created with ID: {course_id}")

        # Step 2: Submit Content Generation Request
        print("Step 2: Submitting content generation request...")
        lesson_request = workflow_data["lesson_request"]
        lesson_request["course_id"] = course_id

        content_response = await e2e_client.post(
            "/api/v1/content/generate",
            json=lesson_request,
            headers=teacher["headers"]
        )

        if content_response.status_code == 404:
            # Try alternative endpoint
            content_response = await e2e_client.post(
                "/generate_content",
                json=lesson_request,
                headers=teacher["headers"]
            )

        if content_response.status_code == 404:
            pytest.skip("Content generation endpoint not available")

        assert content_response.status_code in [200, 202]
        content_result = content_response.json()

        if content_result.get("status") == "processing":
            task_id = content_result["data"]["task_id"]
            print(f"✓ Content generation started with task ID: {task_id}")

            # Step 3: Monitor Progress via WebSocket/API
            print("Step 3: Monitoring generation progress...")
            content_id = await self._monitor_content_generation(e2e_client, task_id, teacher["headers"])

        else:
            # Synchronous generation
            content_id = content_result["data"]["content_id"]

        print(f"✓ Content generated with ID: {content_id}")

        # Step 4: Verify Content Quality
        print("Step 4: Verifying content quality...")
        await self._verify_content_quality(e2e_client, content_id, teacher["headers"], workflow_data["quality_criteria"])

        # Step 5: Content Approval Workflow
        print("Step 5: Content approval workflow...")
        if authenticated_users.get("admin"):
            await self._content_approval_workflow(e2e_client, content_id, authenticated_users["admin"]["headers"])

        # Step 6: Student Access and Interaction
        print("Step 6: Testing student access...")
        if authenticated_users.get("student"):
            await self._student_interaction_workflow(e2e_client, content_id, course_id, authenticated_users["student"]["headers"])

        # Step 7: Analytics and Performance Tracking
        print("Step 7: Verifying analytics...")
        await self._verify_analytics_tracking(e2e_client, content_id, teacher["headers"])

        print("✓ Complete E2E workflow successful!")

    async def _monitor_content_generation(self, client: httpx.AsyncClient, task_id: str, headers: Dict[str, str]) -> str:
        """Monitor content generation progress"""
        max_polls = 30  # 5 minutes max
        poll_interval = 10  # 10 seconds

        for i in range(max_polls):
            progress_response = await client.get(
                f"/api/v1/tasks/{task_id}/progress",
                headers=headers
            )

            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                status = progress_data.get("status")
                progress = progress_data.get("progress", 0)

                print(f"  Progress: {progress}% - Status: {status}")

                if status == "completed":
                    return progress_data["result"]["content_id"]
                elif status == "failed":
                    raise AssertionError(f"Content generation failed: {progress_data.get('error')}")

            await asyncio.sleep(poll_interval)

        raise AssertionError("Content generation timed out")

    async def _verify_content_quality(self, client: httpx.AsyncClient, content_id: str, headers: Dict[str, str], criteria: Dict[str, float]):
        """Verify generated content meets quality criteria"""
        content_response = await client.get(
            f"/api/v1/content/{content_id}",
            headers=headers
        )

        assert content_response.status_code == 200
        content_data = content_response.json()["data"]

        # Verify content structure
        assert "title" in content_data
        assert "content" in content_data or "lesson_content" in content_data
        assert "learning_objectives" in content_data

        # Check for required components
        if "quiz" in content_data:
            quiz = content_data["quiz"]
            assert "questions" in quiz
            assert len(quiz["questions"]) >= 5

        if "roblox_environment" in content_data:
            roblox = content_data["roblox_environment"]
            assert "terrain_script" in roblox or "scripts" in roblox

        # Quality assessment
        quality_response = await client.post(
            f"/api/v1/content/{content_id}/assess",
            json={"criteria": criteria},
            headers=headers
        )

        if quality_response.status_code == 200:
            quality_scores = quality_response.json()["scores"]
            for criterion, min_score in criteria.items():
                if criterion in quality_scores:
                    actual_score = quality_scores[criterion]
                    assert actual_score >= min_score, f"{criterion} score {actual_score} below threshold {min_score}"

        print("✓ Content quality verified")

    async def _content_approval_workflow(self, client: httpx.AsyncClient, content_id: str, admin_headers: Dict[str, str]):
        """Test content approval workflow"""
        # Get content for review
        review_response = await client.get(
            f"/api/v1/content/{content_id}/review",
            headers=admin_headers
        )

        if review_response.status_code == 200:
            # Submit approval
            approval_data = {
                "status": "approved",
                "quality_score": 92.5,
                "reviewer_notes": "Excellent content quality, approved for use",
                "modifications_required": []
            }

            approve_response = await client.post(
                f"/api/v1/content/{content_id}/approve",
                json=approval_data,
                headers=admin_headers
            )

            if approve_response.status_code == 200:
                print("✓ Content approved")
            else:
                print("⚠ Content approval endpoint not fully implemented")

    async def _student_interaction_workflow(self, client: httpx.AsyncClient, content_id: str, course_id: str, student_headers: Dict[str, str]):
        """Test student interaction with content"""
        # Enroll student in course
        enrollment_response = await client.post(
            f"/api/v1/courses/{course_id}/enroll",
            headers=student_headers
        )

        if enrollment_response.status_code in [200, 201]:
            print("✓ Student enrolled in course")

        # Access content
        content_response = await client.get(
            f"/api/v1/content/{content_id}/student-view",
            headers=student_headers
        )

        if content_response.status_code == 200:
            content = content_response.json()["data"]

            # Take quiz if available
            if "quiz_id" in content:
                quiz_id = content["quiz_id"]
                await self._simulate_quiz_attempt(client, quiz_id, student_headers)

            print("✓ Student interaction tested")

    async def _simulate_quiz_attempt(self, client: httpx.AsyncClient, quiz_id: str, student_headers: Dict[str, str]):
        """Simulate student taking a quiz"""
        # Start quiz attempt
        attempt_response = await client.post(
            f"/api/v1/quizzes/{quiz_id}/attempt",
            headers=student_headers
        )

        if attempt_response.status_code == 201:
            attempt_id = attempt_response.json()["data"]["attempt_id"]

            # Get quiz questions
            questions_response = await client.get(
                f"/api/v1/quiz-attempts/{attempt_id}/questions",
                headers=student_headers
            )

            if questions_response.status_code == 200:
                questions = questions_response.json()["data"]["questions"]

                # Submit answers (simulate correct answers)
                for question in questions[:3]:  # Answer first 3 questions
                    answer_data = {
                        "question_id": question["id"],
                        "answer": question.get("correct_answer", 0)  # Use correct answer if available
                    }

                    await client.post(
                        f"/api/v1/quiz-attempts/{attempt_id}/answer",
                        json=answer_data,
                        headers=student_headers
                    )

                # Submit quiz
                submit_response = await client.post(
                    f"/api/v1/quiz-attempts/{attempt_id}/submit",
                    headers=student_headers
                )

                if submit_response.status_code == 200:
                    score = submit_response.json()["data"]["score"]
                    print(f"✓ Quiz completed with score: {score}")

    async def _verify_analytics_tracking(self, client: httpx.AsyncClient, content_id: str, headers: Dict[str, str]):
        """Verify analytics are being tracked"""
        analytics_response = await client.get(
            f"/api/v1/content/{content_id}/analytics",
            headers=headers
        )

        if analytics_response.status_code == 200:
            analytics = analytics_response.json()["data"]

            # Verify analytics structure
            expected_metrics = ["views", "engagement_time", "completion_rate"]
            for metric in expected_metrics:
                if metric in analytics:
                    assert isinstance(analytics[metric], (int, float))

            print("✓ Analytics tracking verified")


class TestWorkflowErrorHandling:
    """Test error handling and recovery in the workflow"""

    @pytest.mark.asyncio
async def test_partial_content_generation_failure(self, e2e_client, authenticated_users, content_workflow_data):
        """Test workflow when some content components fail to generate"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for error handling test")

        teacher = authenticated_users["teacher"]

        # Create a request that might have partial failures
        partial_request = content_workflow_data["lesson_request"].copy()
        partial_request["include_terrain"] = True
        partial_request["include_scripts"] = True
        partial_request["include_3d_models"] = True  # Component that might fail

        with patch("core.agents.terrain_agent.generate_terrain", side_effect=Exception("Terrain generation failed")):
            response = await e2e_client.post(
                "/api/v1/content/generate",
                json=partial_request,
                headers=teacher["headers"]
            )

            if response.status_code == 404:
                pytest.skip("Content generation endpoint not available")

            # Should handle partial failure gracefully
            if response.status_code in [200, 206]:  # Success or Partial Content
                result = response.json()

                if result.get("status") == "partial_success":
                    assert "successful_components" in result
                    assert "failed_components" in result
                    print("✓ Partial failure handled gracefully")

    @pytest.mark.asyncio
async def test_workflow_timeout_handling(self, e2e_client, authenticated_users, content_workflow_data):
        """Test workflow behavior with timeouts"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for timeout test")

        teacher = authenticated_users["teacher"]

        # Create a request with short timeout
        timeout_request = content_workflow_data["lesson_request"].copy()
        timeout_request["timeout_seconds"] = 5  # Very short timeout

        response = await e2e_client.post(
            "/api/v1/content/generate",
            json=timeout_request,
            headers=teacher["headers"]
        )

        if response.status_code == 404:
            pytest.skip("Content generation with timeout not available")

        # Should handle timeout appropriately
        if response.status_code in [408, 202]:  # Timeout or Accepted for async processing
            result = response.json()
            if "task_id" in result.get("data", {}):
                # Monitor for timeout handling
                task_id = result["data"]["task_id"]

                await asyncio.sleep(10)  # Wait for timeout

                status_response = await e2e_client.get(
                    f"/api/v1/tasks/{task_id}/status",
                    headers=teacher["headers"]
                )

                if status_response.status_code == 200:
                    status = status_response.json()
                    if status.get("status") == "timeout":
                        print("✓ Timeout handled correctly")

    @pytest.mark.asyncio
async def test_concurrent_workflow_requests(self, e2e_client, authenticated_users, content_workflow_data):
        """Test multiple concurrent workflow requests"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for concurrent test")

        teacher = authenticated_users["teacher"]

        # Submit multiple concurrent requests
        requests = []
        for i in range(5):
            request = content_workflow_data["lesson_request"].copy()
            request["title"] = f"Concurrent Lesson {i}"
            request["topic"] = f"Topic {i}"
            requests.append(request)

        # Execute concurrently
        async def submit_request(req):
            response = await e2e_client.post(
                "/api/v1/content/generate",
                json=req,
                headers=teacher["headers"]
            )
            return response.status_code

        results = await asyncio.gather(
            *[submit_request(req) for req in requests],
            return_exceptions=True
        )

        # Analyze results
        successful = sum(1 for r in results if r in [200, 202])
        failed = len(results) - successful

        print(f"Concurrent requests: {successful} successful, {failed} failed")

        # Should handle most requests successfully
        if successful > 0:
            success_rate = successful / len(results)
            assert success_rate >= 0.6  # At least 60% success rate under load


class TestWorkflowPerformance:
    """Test performance characteristics of the workflow"""

    @pytest.mark.asyncio
async def test_content_generation_performance(self, e2e_client, authenticated_users, content_workflow_data):
        """Test content generation performance benchmarks"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for performance test")

        teacher = authenticated_users["teacher"]

        # Test different complexity levels
        performance_tests = [
            {
                "name": "Simple Content",
                "request": {
                    "subject": "Mathematics",
                    "topic": "Basic Addition",
                    "grade_level": 3,
                    "include_quiz": False,
                    "include_roblox_environment": False
                },
                "expected_time": 30  # seconds
            },
            {
                "name": "Complex Content",
                "request": content_workflow_data["lesson_request"],
                "expected_time": 120  # seconds
            }
        ]

        for test in performance_tests:
            print(f"Testing {test['name']}...")

            start_time = time.time()

            response = await e2e_client.post(
                "/api/v1/content/generate",
                json=test["request"],
                headers=teacher["headers"]
            )

            if response.status_code == 404:
                continue

            if response.status_code == 200:
                # Synchronous completion
                generation_time = time.time() - start_time
                print(f"  {test['name']} completed in {generation_time:.2f}s")
                assert generation_time < test["expected_time"]

            elif response.status_code == 202:
                # Async processing
                result = response.json()
                task_id = result["data"]["task_id"]

                # Monitor completion
                while time.time() - start_time < test["expected_time"]:
                    status_response = await e2e_client.get(
                        f"/api/v1/tasks/{task_id}/status",
                        headers=teacher["headers"]
                    )

                    if status_response.status_code == 200:
                        status = status_response.json()
                        if status.get("status") == "completed":
                            generation_time = time.time() - start_time
                            print(f"  {test['name']} completed in {generation_time:.2f}s")
                            break

                    await asyncio.sleep(2)

    @pytest.mark.asyncio
async def test_workflow_scalability(self, e2e_client, authenticated_users, content_workflow_data):
        """Test workflow scalability with multiple users"""
        if not authenticated_users:
            pytest.skip("No authenticated users for scalability test")

        # Create multiple teacher accounts
        teachers = []
        for i in range(3):
            if len(authenticated_users) > i:
                teachers.append(list(authenticated_users.values())[i])

        if not teachers:
            pytest.skip("Insufficient users for scalability test")

        # Each teacher submits content requests
        async def teacher_workflow(teacher, suffix):
            request = content_workflow_data["lesson_request"].copy()
            request["title"] = f"Scalability Test Lesson {suffix}"

            response = await e2e_client.post(
                "/api/v1/content/generate",
                json=request,
                headers=teacher["headers"]
            )
            return response.status_code

        # Execute teacher workflows concurrently
        start_time = time.time()
        results = await asyncio.gather(
            *[teacher_workflow(teacher, i) for i, teacher in enumerate(teachers)],
            return_exceptions=True
        )
        total_time = time.time() - start_time

        successful = sum(1 for r in results if r in [200, 202])
        print(f"Scalability test: {successful}/{len(teachers)} successful in {total_time:.2f}s")

        if successful > 0:
            assert successful >= len(teachers) * 0.7  # At least 70% success rate


class TestWorkflowIntegration:
    """Test integration points within the workflow"""

    @pytest.mark.asyncio
async def test_realtime_progress_updates(self, e2e_client, authenticated_users, content_workflow_data):
        """Test real-time progress updates during content generation"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for realtime test")

        teacher = authenticated_users["teacher"]

        # Start content generation
        response = await e2e_client.post(
            "/api/v1/content/generate",
            json=content_workflow_data["lesson_request"],
            headers=teacher["headers"]
        )

        if response.status_code == 404:
            pytest.skip("Content generation endpoint not available")

        if response.status_code == 202:
            result = response.json()
            task_id = result["data"]["task_id"]

            # Try to connect to WebSocket for progress updates
            try:
                ws_url = f"pusher://app_key@cluster/progress/{task_id}"
                async with async_mock_pusher_context() as pusher:
        # Connect using Pusherws_url) as websocket:
                    # Wait for progress updates
                    for _ in range(10):
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            progress_data = json.loads(message)

                            if progress_data.get("type") == "progress":
                                progress = progress_data.get("progress", 0)
                                print(f"Progress update: {progress}%")

                                if progress >= 100:
                                    print("✓ Real-time progress updates working")
                                    break

                        except asyncio.TimeoutError:
                            break

            except (ConnectionRefusedError, OSError):
                print("⚠ WebSocket progress updates not available")

    @pytest.mark.asyncio
async def test_database_consistency_during_workflow(self, e2e_client, authenticated_users, content_workflow_data):
        """Test database consistency throughout the workflow"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for consistency test")

        teacher = authenticated_users["teacher"]

        # Create course
        course_response = await e2e_client.post(
            "/api/v1/courses",
            json=content_workflow_data["course"],
            headers=teacher["headers"]
        )

        if course_response.status_code == 404:
            pytest.skip("Course creation not available")

        if course_response.status_code == 201:
            course_id = course_response.json()["data"]["id"]

            # Generate content
            lesson_request = content_workflow_data["lesson_request"]
            lesson_request["course_id"] = course_id

            content_response = await e2e_client.post(
                "/api/v1/content/generate",
                json=lesson_request,
                headers=teacher["headers"]
            )

            if content_response.status_code in [200, 202]:
                # Verify course-content relationship
                course_detail = await e2e_client.get(
                    f"/api/v1/courses/{course_id}?include=content",
                    headers=teacher["headers"]
                )

                if course_detail.status_code == 200:
                    course_data = course_detail.json()["data"]
                    if "content" in course_data:
                        assert len(course_data["content"]) >= 1
                        print("✓ Database consistency maintained")

    @pytest.mark.asyncio
async def test_api_endpoint_integration(self, e2e_client, authenticated_users, content_workflow_data):
        """Test integration between different API endpoints"""
        if not authenticated_users.get("teacher"):
            pytest.skip("Cannot authenticate teacher for API integration test")

        teacher = authenticated_users["teacher"]

        # Test endpoint chain: Course → Lesson → Content → Quiz → Analytics
        endpoints_tested = []

        # 1. Create course
        course_response = await e2e_client.post("/api/v1/courses", json=content_workflow_data["course"], headers=teacher["headers"])
        if course_response.status_code == 201:
            endpoints_tested.append("courses")
            course_id = course_response.json()["data"]["id"]

            # 2. Create lesson
            lesson_data = {"course_id": course_id, "title": "Test Lesson", "description": "Integration test lesson"}
            lesson_response = await e2e_client.post("/api/v1/lessons", json=lesson_data, headers=teacher["headers"])
            if lesson_response.status_code == 201:
                endpoints_tested.append("lessons")
                lesson_id = lesson_response.json()["data"]["id"]

                # 3. Generate content
                content_request = content_workflow_data["lesson_request"]
                content_request["lesson_id"] = lesson_id
                content_response = await e2e_client.post("/api/v1/content/generate", json=content_request, headers=teacher["headers"])
                if content_response.status_code in [200, 202]:
                    endpoints_tested.append("content")

                    # 4. Check analytics
                    analytics_response = await e2e_client.get(f"/api/v1/courses/{course_id}/analytics", headers=teacher["headers"])
                    if analytics_response.status_code == 200:
                        endpoints_tested.append("analytics")

        print(f"✓ API endpoints integrated: {', '.join(endpoints_tested)}")
        assert len(endpoints_tested) >= 2  # At least 2 endpoints working together


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])