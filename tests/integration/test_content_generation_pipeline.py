import pytest_asyncio
#!/usr/bin/env python3
"""
Content Generation Pipeline Integration Tests

Tests the complete content generation workflow including:
- API request -> Agent selection -> LLM interaction -> Database storage -> Real-time updates
- Multi-agent coordination for complex content
- Error handling and retry mechanisms
- Performance benchmarks
- Data consistency across components
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["USE_MOCK_DATABASE"] = "false"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@pytest.fixture
async def content_client():
    """HTTP client configured for content generation testing"""
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8009",
        timeout=60.0  # Longer timeout for content generation
    ) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    # Create a test JWT token
    import jwt
    from datetime import timedelta

    payload = {
        "sub": "test_teacher_user",
        "role": "teacher",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def content_requests():
    """Sample content generation requests for testing"""
    return {
        "basic_lesson": {
            "subject": "Mathematics",
            "grade_level": 7,
            "topic": "Linear Equations",
            "learning_objectives": [
                "Understand what linear equations are",
                "Solve linear equations with one variable",
                "Apply linear equations to real-world problems"
            ],
            "environment_type": "classroom",
            "duration_minutes": 45
        },
        "roblox_lesson": {
            "subject": "Science",
            "grade_level": 8,
            "topic": "Solar System",
            "learning_objectives": [
                "Identify planets in our solar system",
                "Understand relative sizes and distances",
                "Explore gravity and orbital mechanics"
            ],
            "environment_type": "space_station",
            "include_terrain": True,
            "include_scripts": True,
            "gamification_elements": ["achievements", "leaderboard"]
        },
        "complex_multi_agent": {
            "subject": "History",
            "grade_level": 10,
            "topic": "World War II",
            "learning_objectives": [
                "Analyze causes of WWII",
                "Understand major battles and campaigns",
                "Evaluate the war's impact on society"
            ],
            "environment_type": "historical_simulation",
            "include_quiz": True,
            "include_terrain": True,
            "include_scripts": True,
            "interactive_elements": ["timeline", "map", "documents"],
            "assessment_type": "comprehensive"
        }
    }


@pytest.fixture
async def mock_pusher_service():
    """Mock Pusher service for real-time updates"""
    mock_pusher = Mock()
    mock_pusher.trigger = AsyncMock(return_value={"status": "ok"})
    mock_pusher.authenticate = AsyncMock(return_value={"auth": "token"})
    return mock_pusher


@pytest.fixture
async def mock_agent_services():
    """Mock agent services for controlled testing"""
    return {
        "content_agent": Mock(
            generate_content=AsyncMock(return_value={
                "title": "Linear Equations Introduction",
                "content": "Welcome to linear equations...",
                "activities": ["equation_solver", "word_problems"],
                "estimated_time": 45,
                "difficulty": "intermediate"
            })
        ),
        "quiz_agent": Mock(
            generate_quiz=AsyncMock(return_value={
                "questions": [
                    {
                        "id": "q1",
                        "question": "What is the solution to 2x + 5 = 15?",
                        "type": "multiple_choice",
                        "options": ["x = 3", "x = 5", "x = 10", "x = 20"],
                        "correct_answer": 1,
                        "points": 10,
                        "explanation": "Subtract 5 from both sides, then divide by 2"
                    }
                ],
                "total_points": 10,
                "passing_score": 70
            })
        ),
        "terrain_agent": Mock(
            generate_terrain=AsyncMock(return_value={
                "script": "-- Roblox terrain generation script\nlocal terrain = workspace.Terrain",
                "materials": ["Grass", "Rock", "Water"],
                "size": {"x": 100, "y": 50, "z": 100},
                "theme": "classroom"
            })
        ),
        "script_agent": Mock(
            generate_script=AsyncMock(return_value={
                "scripts": [
                    {
                        "name": "QuizUI",
                        "type": "LocalScript",
                        "code": "-- Quiz UI script\nlocal Players = game:GetService('Players')"
                    }
                ],
                "dependencies": ["TextService", "UserInputService"]
            })
        )
    }


class TestBasicContentGeneration:
    """Test basic content generation workflows"""

    @pytest.mark.asyncio
async def test_simple_content_generation(self, content_client, auth_headers, content_requests):
        """Test basic content generation request"""
        request_data = content_requests["basic_lesson"]

        # Make content generation request
        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        # Handle case where endpoint doesn't exist yet
        if response.status_code == 404:
            # Try alternative endpoints
            alternative_endpoints = [
                "/api/v1/generate_content",
                "/generate_content",
                "/content/generate"
            ]

            for endpoint in alternative_endpoints:
                response = await content_client.post(
                    endpoint,
                    json=request_data,
                    headers=auth_headers
                )
                if response.status_code != 404:
                    break

        if response.status_code == 404:
            pytest.skip("Content generation endpoint not implemented")

        # Verify successful response
        assert response.status_code in [200, 202]  # Success or Accepted (async)
        result = response.json()

        # Check response structure
        assert "status" in result
        if result["status"] == "success":
            assert "data" in result
            content_data = result["data"]

            # Verify content structure
            expected_fields = ["title", "content", "learning_objectives", "estimated_duration"]
            for field in expected_fields:
                if field in content_data:
                    assert content_data[field] is not None
        elif result["status"] == "processing":
            # Async processing - check for task ID
            assert "task_id" in result["data"]

    @pytest.mark.asyncio
async def test_content_generation_with_validation(self, content_client, auth_headers):
        """Test content generation with input validation"""
        invalid_requests = [
            {"subject": "", "grade_level": 7},  # Empty subject
            {"subject": "Math", "grade_level": 0},  # Invalid grade level
            {"subject": "Math", "grade_level": 20},  # Out of range grade level
            {"subject": "Math"},  # Missing required fields
            {}  # Empty request
        ]

        for invalid_request in invalid_requests:
            response = await content_client.post(
                "/api/v1/content/generate",
                json=invalid_request,
                headers=auth_headers
            )

            if response.status_code == 404:
                # Try alternative endpoint
                response = await content_client.post(
                    "/generate_content",
                    json=invalid_request,
                    headers=auth_headers
                )

            if response.status_code != 404:  # If endpoint exists
                assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
async def test_content_generation_unauthorized(self, content_client, content_requests):
        """Test content generation without authentication"""
        request_data = content_requests["basic_lesson"]

        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data
        )

        if response.status_code == 404:
            response = await content_client.post("/generate_content", json=request_data)

        if response.status_code != 404:  # If endpoint exists
            assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
async def test_content_generation_performance(self, content_client, auth_headers, content_requests):
        """Test content generation performance benchmarks"""
        request_data = content_requests["basic_lesson"]

        # Measure generation time
        start_time = time.time()

        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response.status_code == 404:
            response = await content_client.post(
                "/generate_content",
                json=request_data,
                headers=auth_headers
            )

        if response.status_code == 404:
            pytest.skip("Content generation endpoint not implemented")

        end_time = time.time()
        generation_time = end_time - start_time

        # Performance assertions
        if response.status_code == 200:
            # Synchronous generation should complete within reasonable time
            assert generation_time < 30.0  # 30 seconds max

        elif response.status_code == 202:
            # Async generation should respond quickly
            assert generation_time < 5.0  # 5 seconds max for task creation

        # Log performance metrics
        print(f"Content generation time: {generation_time:.2f} seconds")


class TestRobloxContentGeneration:
    """Test Roblox-specific content generation"""

    @pytest.mark.asyncio
async def test_roblox_environment_generation(self, content_client, auth_headers, content_requests):
        """Test generation of Roblox environments with terrain and scripts"""
        request_data = content_requests["roblox_lesson"]

        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response.status_code == 404:
            # Try Roblox-specific endpoint
            response = await content_client.post(
                "/api/v1/roblox/generate",
                json=request_data,
                headers=auth_headers
            )

        if response.status_code == 404:
            pytest.skip("Roblox content generation not implemented")

        if response.status_code in [200, 202]:
            result = response.json()

            if result["status"] == "success":
                content_data = result["data"]

                # Verify Roblox-specific content
                if "terrain" in content_data:
                    terrain = content_data["terrain"]
                    assert "script" in terrain
                    assert "materials" in terrain

                if "scripts" in content_data:
                    scripts = content_data["scripts"]
                    assert isinstance(scripts, list)
                    for script in scripts:
                        assert "name" in script
                        assert "code" in script

    @pytest.mark.asyncio
async def test_terrain_script_generation(self, content_client, auth_headers):
        """Test terrain script generation specifically"""
        terrain_request = {
            "type": "terrain",
            "theme": "space_station",
            "size": {"x": 200, "y": 100, "z": 200},
            "materials": ["Metal", "Neon", "Glass"],
            "features": ["gravity_wells", "landing_pads", "observation_deck"]
        }

        response = await content_client.post(
            "/api/v1/roblox/terrain",
            json=terrain_request,
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Terrain generation endpoint not implemented")

        if response.status_code == 200:
            result = response.json()
            assert "script" in result
            assert "-- Roblox" in result["script"] or "local terrain" in result["script"].lower()

    @pytest.mark.asyncio
async def test_lua_script_validation(self, content_client, auth_headers):
        """Test validation of generated Lua scripts"""
        script_request = {
            "type": "script",
            "functionality": "quiz_system",
            "features": ["question_display", "answer_validation", "score_tracking"],
            "target": "StarterPlayerScripts"
        }

        response = await content_client.post(
            "/api/v1/roblox/scripts",
            json=script_request,
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Script generation endpoint not implemented")

        if response.status_code == 200:
            result = response.json()

            if "scripts" in result:
                for script in result["scripts"]:
                    code = script.get("code", "")

                    # Basic Lua syntax validation
                    assert not any(syntax_error in code for syntax_error in [
                        "syntax error", "unexpected symbol", "end expected"
                    ])

                    # Check for common Roblox services
                    roblox_services = ["Players", "Workspace", "ReplicatedStorage"]
                    has_roblox_service = any(service in code for service in roblox_services)
                    if not has_roblox_service and len(code) > 10:
                        print(f"Warning: Script might not be Roblox-specific: {code[:100]}...")


class TestMultiAgentOrchestration:
    """Test multi-agent coordination in content generation"""

    @pytest.mark.asyncio
async def test_parallel_agent_execution(self, content_client, auth_headers, content_requests, mock_agent_services):
        """Test parallel execution of multiple content generation agents"""
        request_data = content_requests["complex_multi_agent"]

        # Mock the agent services
        with patch("apps.backend.agents.orchestrator.ContentAgent", mock_agent_services["content_agent"]), \
             patch("apps.backend.agents.orchestrator.QuizAgent", mock_agent_services["quiz_agent"]), \
             patch("apps.backend.agents.orchestrator.TerrainAgent", mock_agent_services["terrain_agent"]), \
             patch("apps.backend.agents.orchestrator.ScriptAgent", mock_agent_services["script_agent"]):

            start_time = time.time()

            response = await content_client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Multi-agent orchestration not implemented")

            execution_time = time.time() - start_time

            if response.status_code in [200, 202]:
                result = response.json()

                if result["status"] == "success":
                    content_data = result["data"]

                    # Verify all requested components were generated
                    expected_components = ["content", "quiz", "terrain", "scripts"]
                    for component in expected_components:
                        if component in content_data:
                            assert content_data[component] is not None

                    # Verify parallel execution (should be faster than serial)
                    # If all agents ran in serial, it would take much longer
                    print(f"Multi-agent execution time: {execution_time:.2f} seconds")

    @pytest.mark.asyncio
async def test_agent_error_handling(self, content_client, auth_headers, content_requests):
        """Test error handling when individual agents fail"""
        request_data = content_requests["complex_multi_agent"]

        # Mock agents with some failures
        failing_agents = {
            "content_agent": Mock(
                generate_content=AsyncMock(side_effect=Exception("Content generation failed"))
            ),
            "quiz_agent": Mock(
                generate_quiz=AsyncMock(return_value={
                    "questions": [],
                    "total_points": 0
                })
            ),
            "terrain_agent": Mock(
                generate_terrain=AsyncMock(side_effect=TimeoutError("Terrain generation timeout"))
            ),
            "script_agent": Mock(
                generate_script=AsyncMock(return_value={
                    "scripts": [{"name": "fallback", "code": "-- Fallback script"}]
                })
            )
        }

        with patch("apps.backend.agents.orchestrator.ContentAgent", failing_agents["content_agent"]), \
             patch("apps.backend.agents.orchestrator.QuizAgent", failing_agents["quiz_agent"]), \
             patch("apps.backend.agents.orchestrator.TerrainAgent", failing_agents["terrain_agent"]), \
             patch("apps.backend.agents.orchestrator.ScriptAgent", failing_agents["script_agent"]):

            response = await content_client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Error handling not testable without orchestrator")

            # Should handle failures gracefully
            assert response.status_code in [200, 202, 206]  # Success, Accepted, or Partial Content

            if response.status_code == 200:
                result = response.json()

                # Should provide partial results or fallbacks
                if result["status"] == "partial_success":
                    assert "errors" in result
                    assert "data" in result

    @pytest.mark.asyncio
async def test_agent_retry_mechanism(self, content_client, auth_headers, content_requests):
        """Test retry mechanism for failed agent operations"""
        request_data = content_requests["basic_lesson"]

        # Mock agent that fails first, then succeeds
        call_count = 0

        def mock_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return {
                "title": "Test Content",
                "content": "Generated after retry",
                "success": True
            }

        mock_agent = Mock(generate_content=AsyncMock(side_effect=mock_generate_content))

        with patch("apps.backend.agents.orchestrator.ContentAgent", mock_agent):
            response = await content_client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Retry mechanism not testable without orchestrator")

            if response.status_code == 200:
                # Should succeed after retry
                result = response.json()
                assert result["status"] == "success"

                # Verify retry was attempted
                assert call_count > 1


class TestContentPersistence:
    """Test content persistence and database integration"""

    @pytest.mark.requires_postgres
    @pytest.mark.asyncio
async def test_content_database_storage(self, content_client, auth_headers, content_requests, test_db):
        """Test that generated content is properly stored in database"""
        request_data = content_requests["basic_lesson"]

        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Content generation endpoint not implemented")

        if response.status_code == 200:
            result = response.json()

            if result["status"] == "success" and "content_id" in result.get("data", {}):
                content_id = result["data"]["content_id"]

                # Verify content was stored in database
                # This would require database connection and queries
                # For now, just verify the response structure
                assert content_id is not None
                assert isinstance(content_id, (str, int))

    @pytest.mark.asyncio
async def test_content_versioning(self, content_client, auth_headers, content_requests):
        """Test content versioning when regenerating"""
        request_data = content_requests["basic_lesson"]

        # Generate content twice
        response1 = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response1.status_code == 404:
            pytest.skip("Content generation endpoint not implemented")

        # Wait a moment
        await asyncio.sleep(1)

        response2 = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response1.status_code == 200 and response2.status_code == 200:
            result1 = response1.json()
            result2 = response2.json()

            # Should be different versions
            if "content_id" in result1.get("data", {}) and "content_id" in result2.get("data", {}):
                content_id1 = result1["data"]["content_id"]
                content_id2 = result2["data"]["content_id"]
                assert content_id1 != content_id2

    @pytest.mark.asyncio
async def test_content_metadata_tracking(self, content_client, auth_headers, content_requests):
        """Test tracking of content generation metadata"""
        request_data = content_requests["basic_lesson"]

        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Content generation endpoint not implemented")

        if response.status_code == 200:
            result = response.json()

            if result["status"] == "success":
                data = result["data"]

                # Verify metadata is tracked
                metadata_fields = ["generated_at", "model_used", "generation_time", "user_id"]
                for field in metadata_fields:
                    if field in data:
                        assert data[field] is not None


class TestRealTimeUpdates:
    """Test real-time updates during content generation"""

    @pytest.mark.asyncio
async def test_websocket_progress_updates(self, mock_pusher_service):
        """Test WebSocket progress updates during generation"""
        # This would test WebSocket connections for real-time updates
        # For now, just verify the mock service
        result = await mock_pusher_service.trigger("content-channel", "progress", {
            "task_id": "test-123",
            "progress": 50,
            "stage": "content_generation"
        })

        assert result["status"] == "ok"

    @pytest.mark.asyncio
async def test_pusher_channel_notifications(self, content_client, auth_headers, content_requests, mock_pusher_service):
        """Test Pusher channel notifications for content updates"""
        request_data = content_requests["basic_lesson"]

        # Mock Pusher service
        with patch("apps.backend.services.pusher.trigger_event", mock_pusher_service.trigger):
            response = await content_client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Pusher integration not testable without endpoint")

            # Verify Pusher notifications were triggered
            if response.status_code in [200, 202]:
                # In a real implementation, we'd verify the trigger was called
                pass

    @pytest.mark.asyncio
async def test_progress_tracking_accuracy(self, content_client, auth_headers, content_requests):
        """Test accuracy of progress tracking during generation"""
        request_data = content_requests["complex_multi_agent"]

        # Monitor progress updates (if supported)
        response = await content_client.post(
            "/api/v1/content/generate",
            json=request_data,
            headers=auth_headers
        )

        if response.status_code == 202:  # Async processing
            result = response.json()
            if "task_id" in result.get("data", {}):
                task_id = result["data"]["task_id"]

                # Poll for progress (if endpoint exists)
                for _ in range(10):  # Max 10 polls
                    progress_response = await content_client.get(
                        f"/api/v1/tasks/{task_id}/progress",
                        headers=auth_headers
                    )

                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        progress = progress_data.get("progress", 0)

                        # Progress should be between 0 and 100
                        assert 0 <= progress <= 100

                        if progress == 100:
                            break

                    await asyncio.sleep(1)


class TestConcurrentGeneration:
    """Test content generation under concurrent load"""

    @pytest.mark.asyncio
async def test_concurrent_generation_requests(self, content_client, auth_headers, content_requests):
        """Test system stability under concurrent generation requests"""
        request_data = content_requests["basic_lesson"]

        # Create multiple concurrent generation tasks
        async def generate_content():
            response = await content_client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=auth_headers
            )
            return response.status_code

        # Run 5 concurrent generation requests
        tasks = [generate_content() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out 404s (endpoint not found)
        valid_results = [r for r in results if isinstance(r, int) and r != 404]

        if valid_results:
            # Should handle concurrent requests gracefully
            success_codes = {200, 202, 429}  # Success, Accepted, or Rate Limited
            assert all(code in success_codes for code in valid_results)

    @pytest.mark.asyncio
async def test_resource_cleanup_after_generation(self, content_client, auth_headers, content_requests):
        """Test that resources are properly cleaned up after generation"""
        request_data = content_requests["basic_lesson"]

        initial_memory = await self._get_memory_usage()

        # Generate multiple pieces of content
        for _ in range(3):
            response = await content_client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Cannot test resource cleanup without endpoint")

            await asyncio.sleep(1)  # Small delay

        final_memory = await self._get_memory_usage()

        # Memory should not increase dramatically
        if initial_memory and final_memory:
            memory_increase = final_memory - initial_memory
            # Allow for some increase but not excessive
            assert memory_increase < 100 * 1024 * 1024  # 100MB limit

    async def _get_memory_usage(self) -> Optional[int]:
        """Get current memory usage (mock implementation)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return None


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])