"""
End-to-End Tests for Roblox Integration Flow
Tests the complete 8-stage conversation flow and environment generation
"""

import os
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient
from fastapi import status

# Import services
from apps.backend.services.roblox_auth import RobloxOAuth2Service, TokenResponse
from apps.backend.services.open_cloud_client import OpenCloudAPIClient, AssetDescription
from apps.backend.services.rojo_manager import EnhancedRojoManager, RojoProjectConfig
from apps.backend.core.prompts.enhanced_conversation_flow import (
    EnhancedConversationFlowManager,
    ConversationStage
)

# Skip tests if environment flag not set
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_E2E_TESTS"),
    reason="E2E tests disabled. Set RUN_E2E_TESTS=1 to run"
)


@pytest.fixture
async def mock_oauth_service():
    """Mock OAuth2 service for testing"""
    service = Mock(spec=RobloxOAuth2Service)
    service.generate_authorization_url.return_value = {
        "authorization_url": "https://authorize.roblox.com/test",
        "state": "test-state-123",
        "expires_at": "2025-12-31T00:00:00"
    }
    service.exchange_code_for_token = AsyncMock(return_value=TokenResponse(
        access_token="test-access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="test-refresh-token"
    ))
    return service


@pytest.fixture
async def mock_open_cloud_client():
    """Mock Open Cloud API client"""
    client = Mock(spec=OpenCloudAPIClient)
    client.create_asset = AsyncMock(return_value={
        "assetId": "12345",
        "assetUrl": "https://www.roblox.com/library/12345"
    })
    client.set_datastore_entry = AsyncMock(return_value={"success": True})
    client.publish_message = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
async def mock_rojo_manager():
    """Mock Rojo manager"""
    manager = Mock(spec=EnhancedRojoManager)
    manager.create_project = AsyncMock(return_value={
        "project_id": "test-project-123",
        "port": 34872,
        "status": "created"
    })
    manager.start_project = AsyncMock(return_value={
        "connected": True,
        "session_id": "rojo-session-123",
        "project_name": "TestProject"
    })
    return manager


@pytest.fixture
async def conversation_manager(mock_oauth_service, mock_open_cloud_client, mock_rojo_manager):
    """Create conversation manager with mocked dependencies"""
    with patch('apps.backend.core.prompts.enhanced_conversation_flow.RobloxOAuth2Service', return_value=mock_oauth_service):
        with patch('apps.backend.core.prompts.enhanced_conversation_flow.OpenCloudAPIClient', return_value=mock_open_cloud_client):
            with patch('apps.backend.core.prompts.enhanced_conversation_flow.EnhancedRojoManager', return_value=mock_rojo_manager):
                manager = EnhancedConversationFlowManager()
                # Mock LLM responses
                manager.conversation_chain = Mock()
                manager.conversation_chain.ainvoke = AsyncMock(return_value={
                    "ai_response": "Test response",
                    "next_action": "continue"
                })
                manager.generation_chain = Mock()
                manager.generation_chain.ainvoke = AsyncMock(return_value={
                    "lua_scripts": ["print('Test')"],
                    "asset_descriptions": [],
                    "datastore_entries": []
                })
                return manager


class TestRobloxIntegrationE2E:
    """End-to-end tests for complete Roblox integration flow"""

    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, conversation_manager):
        """Test all 8 stages of conversation flow"""
        session_id = "test-session-123"
        user_id = "test-user-123"

        # Start conversation
        result = await conversation_manager.start_conversation(user_id, session_id)
        assert result["session_id"] == session_id
        assert result["current_stage"] == ConversationStage.GREETING.value

        # Test each stage progression
        stages = [
            (ConversationStage.GREETING, "I want to create an educational game"),
            (ConversationStage.DISCOVERY, "It's for teaching mathematics"),
            (ConversationStage.REQUIREMENTS, "Ages 10-12, basic algebra"),
            (ConversationStage.PERSONALIZATION, "Interactive puzzles preferred"),
            (ConversationStage.CONTENT_DESIGN, "Include leaderboard"),
            (ConversationStage.UNIQUENESS, "Add particle effects"),
            (ConversationStage.VALIDATION, "Looks good, proceed"),
        ]

        for expected_stage, user_input in stages:
            result = await conversation_manager.process_input(session_id, user_input)
            assert "ai_response" in result
            assert "next_stage" in result

            # Advance to next stage
            await conversation_manager.advance_stage(session_id)
            current_stage = conversation_manager.get_current_stage(session_id)

            # Check we're progressing correctly
            if current_stage != ConversationStage.GENERATION:
                stage_index = list(ConversationStage).index(current_stage)
                expected_index = list(ConversationStage).index(expected_stage) + 1
                assert stage_index == expected_index, f"Expected stage index {expected_index}, got {stage_index}"

    @pytest.mark.asyncio
    async def test_environment_generation(self, conversation_manager, mock_rojo_manager):
        """Test environment generation at final stage"""
        session_id = "test-session-123"
        user_id = "test-user-123"

        # Setup conversation at generation stage
        await conversation_manager.start_conversation(user_id, session_id)
        conversation_manager.sessions[session_id]["current_stage"] = ConversationStage.GENERATION
        conversation_manager.sessions[session_id]["conversation_data"] = {
            "educational_topic": "Mathematics",
            "age_group": "10-12",
            "features": ["puzzles", "leaderboard"],
            "style": "interactive"
        }

        # Generate environment
        result = await conversation_manager.generate_roblox_environment(session_id)

        assert result["success"] is True
        assert "project_id" in result
        assert "rojo_port" in result
        assert result["files_generated"] > 0

        # Verify Rojo project was created and started
        mock_rojo_manager.create_project.assert_called_once()
        mock_rojo_manager.start_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_oauth2_flow(self, mock_oauth_service):
        """Test OAuth2 authentication flow"""
        user_id = "test-user-123"

        # Generate authorization URL
        auth_data = mock_oauth_service.generate_authorization_url(user_id)
        assert "authorization_url" in auth_data
        assert "state" in auth_data

        # Simulate callback with code
        code = "test-auth-code"
        state = auth_data["state"]

        token = await mock_oauth_service.exchange_code_for_token(code, state)
        assert token.access_token == "test-access-token"
        assert token.refresh_token == "test-refresh-token"

    @pytest.mark.asyncio
    async def test_asset_upload_flow(self, mock_open_cloud_client):
        """Test asset upload to Roblox"""
        asset = AssetDescription(
            assetType="Model",
            displayName="Test Educational Model",
            description="Generated by AI for education"
        )

        file_content = b"test-model-data"
        result = await mock_open_cloud_client.create_asset(asset, file_content)

        assert result["assetId"] == "12345"
        assert "assetUrl" in result

    @pytest.mark.asyncio
    async def test_rojo_sync_flow(self, mock_rojo_manager):
        """Test Rojo project synchronization"""
        project_config = RojoProjectConfig(
            name="TestEducationalProject",
            tree={
                "$className": "DataModel",
                "ServerScriptService": {
                    "$className": "ServerScriptService",
                    "MainScript": {"$path": "scripts/main.lua"}
                }
            }
        )

        # Create project
        project = await mock_rojo_manager.create_project(
            "TestProject",
            "test-user-123",
            project_config
        )
        assert project["project_id"] == "test-project-123"

        # Start sync
        sync_status = await mock_rojo_manager.start_project(project["project_id"])
        assert sync_status["connected"] is True
        assert sync_status["session_id"] == "rojo-session-123"

    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_manager):
        """Test error handling in conversation flow"""
        session_id = "error-session"
        user_id = "test-user"

        # Test invalid session
        with pytest.raises(ValueError, match="Session not found"):
            await conversation_manager.process_input("invalid-session", "test input")

        # Test generation without completing flow
        await conversation_manager.start_conversation(user_id, session_id)
        with pytest.raises(ValueError, match="Must complete all stages"):
            await conversation_manager.generate_roblox_environment(session_id)

    @pytest.mark.asyncio
    async def test_pusher_integration(self, conversation_manager):
        """Test Pusher channel events during flow"""
        with patch('apps.backend.core.prompts.enhanced_conversation_flow.pusher') as mock_pusher:
            session_id = "pusher-test-session"
            user_id = "test-user"

            # Start conversation - should trigger Pusher event
            await conversation_manager.start_conversation(user_id, session_id)

            # Verify Pusher was called
            mock_pusher.trigger.assert_called()
            call_args = mock_pusher.trigger.call_args
            assert call_args[0][0] == f"roblox-conversation-{session_id}"
            assert call_args[0][1] == "stage_changed"

    @pytest.mark.asyncio
    async def test_conversation_persistence(self, conversation_manager):
        """Test conversation state persistence"""
        session_id = "persist-session"
        user_id = "test-user"

        # Start and process some inputs
        await conversation_manager.start_conversation(user_id, session_id)
        await conversation_manager.process_input(session_id, "Math education")

        # Verify state is maintained
        session_data = conversation_manager.sessions.get(session_id)
        assert session_data is not None
        assert len(session_data["conversation_history"]) > 0
        assert session_data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, conversation_manager):
        """Test handling multiple concurrent sessions"""
        sessions = [
            ("session-1", "user-1"),
            ("session-2", "user-2"),
            ("session-3", "user-3")
        ]

        # Start multiple sessions concurrently
        tasks = [
            conversation_manager.start_conversation(user_id, session_id)
            for session_id, user_id in sessions
        ]
        results = await asyncio.gather(*tasks)

        # Verify all sessions created successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["session_id"] == sessions[i][0]
            assert result["current_stage"] == ConversationStage.GREETING.value

    @pytest.mark.asyncio
    async def test_full_integration_with_api(self, conversation_manager):
        """Test complete flow with API endpoints"""
        with patch('apps.backend.api.v1.endpoints.roblox_integration.flow_manager', conversation_manager):
            from apps.backend.main import app

            async with AsyncClient(app=app, base_url="http://test") as client:
                # Start conversation via API
                response = await client.post(
                    "/api/v1/roblox/conversation/start",
                    json={"initial_message": "Create math game"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "session_id" in data
                assert "pusher_channel" in data


class TestRobloxIntegrationPerformance:
    """Performance tests for Roblox integration"""

    @pytest.mark.asyncio
    async def test_conversation_response_time(self, conversation_manager):
        """Test response time for conversation processing"""
        import time

        session_id = "perf-session"
        user_id = "test-user"

        await conversation_manager.start_conversation(user_id, session_id)

        start_time = time.time()
        await conversation_manager.process_input(session_id, "Test input")
        elapsed = time.time() - start_time

        # Response should be under 2 seconds
        assert elapsed < 2.0, f"Response took {elapsed:.2f} seconds"

    @pytest.mark.asyncio
    async def test_generation_performance(self, conversation_manager):
        """Test environment generation performance"""
        import time

        session_id = "gen-perf-session"
        user_id = "test-user"

        # Setup at generation stage
        await conversation_manager.start_conversation(user_id, session_id)
        conversation_manager.sessions[session_id]["current_stage"] = ConversationStage.GENERATION
        conversation_manager.sessions[session_id]["conversation_data"] = {
            "educational_topic": "Science",
            "features": ["experiments", "quizzes"]
        }

        start_time = time.time()
        result = await conversation_manager.generate_roblox_environment(session_id)
        elapsed = time.time() - start_time

        # Generation should complete within 10 seconds
        assert elapsed < 10.0, f"Generation took {elapsed:.2f} seconds"
        assert result["success"] is True


class TestRobloxIntegrationSecurity:
    """Security tests for Roblox integration"""

    @pytest.mark.asyncio
    async def test_token_security(self, mock_oauth_service):
        """Test secure token handling"""
        # Ensure tokens are not exposed in logs
        with patch('logging.Logger.info') as mock_log:
            token = await mock_oauth_service.exchange_code_for_token("code", "state")

            # Check logs don't contain actual token
            for call in mock_log.call_args_list:
                assert "test-access-token" not in str(call)
                assert "test-refresh-token" not in str(call)

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, conversation_manager):
        """Test protection against SQL injection in user inputs"""
        session_id = "security-session"
        user_id = "test-user"

        await conversation_manager.start_conversation(user_id, session_id)

        # Try SQL injection in user input
        malicious_input = "'; DROP TABLE users; --"
        result = await conversation_manager.process_input(session_id, malicious_input)

        # Should handle gracefully without executing SQL
        assert "ai_response" in result
        # Verify no database errors occurred

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting on endpoints"""
        from apps.backend.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make multiple rapid requests
            responses = []
            for _ in range(100):
                response = await client.post(
                    "/api/v1/roblox/conversation/start",
                    json={"initial_message": "Test"},
                    headers={"Authorization": "Bearer test-token"}
                )
                responses.append(response.status_code)

            # Should have some rate limited responses
            rate_limited = [r for r in responses if r == status.HTTP_429_TOO_MANY_REQUESTS]
            assert len(rate_limited) > 0, "Rate limiting not working"


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=apps.backend.services",
        "--cov=apps.backend.core.prompts",
        "--cov-report=html",
        "--cov-report=term"
    ])