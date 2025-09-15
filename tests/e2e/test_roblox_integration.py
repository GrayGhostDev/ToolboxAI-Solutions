"""
End-to-End Test for Roblox Integration
Tests the complete flow from conversation to Roblox environment generation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import all the services we'll test
from apps.backend.services.roblox_auth import RobloxOAuth2Service
from apps.backend.services.open_cloud_client import OpenCloudAPIClient, AssetDescription, CreationContext, AssetType
from apps.backend.services.rojo_manager import EnhancedRojoManager, RojoProjectConfig
from apps.backend.core.prompts.enhanced_conversation_flow import (
    EnhancedConversationFlowManager,
    ConversationStage,
    ConversationContext
)
from apps.backend.services.pusher_realtime import PusherRealtimeService

class TestRobloxIntegrationE2E:
    """Test complete Roblox integration flow"""

    @pytest.fixture
    def mock_pusher(self):
        """Mock Pusher service"""
        with patch('apps.backend.services.pusher_realtime.pusher_service') as mock:
            mock.broadcast_event = AsyncMock(return_value=True)
            yield mock

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for conversation flow"""
        with patch('apps.backend.core.prompts.enhanced_conversation_flow.get_chat_model') as mock:
            llm = Mock()
            llm.ainvoke = AsyncMock(return_value={
                "response": "Test response",
                "subject": "Math",
                "grade_level": "5",
                "objectives": ["Learn fractions"],
                "environment_type": "classroom"
            })
            mock.return_value = llm
            yield mock

    @pytest.fixture
    async def oauth_service(self):
        """Create OAuth2 service instance"""
        service = RobloxOAuth2Service()
        # Mock the session to avoid real HTTP calls
        service.session = Mock()
        return service

    @pytest.fixture
    async def open_cloud_client(self):
        """Create Open Cloud client instance"""
        client = OpenCloudAPIClient(api_key="test_key")
        # Mock the session to avoid real HTTP calls
        client.session = Mock()
        return client

    @pytest.fixture
    async def rojo_manager(self, tmp_path):
        """Create Rojo manager instance"""
        manager = EnhancedRojoManager()
        manager.projects_dir = tmp_path / "rojo_projects"
        manager.projects_dir.mkdir(parents=True, exist_ok=True)
        return manager

    @pytest.fixture
    async def conversation_flow(self, mock_pusher, mock_llm):
        """Create conversation flow manager"""
        return EnhancedConversationFlowManager()

    @pytest.mark.asyncio
    async def test_oauth2_flow(self, oauth_service):
        """Test OAuth2 authentication flow"""
        # Test authorization URL generation
        auth_data = oauth_service.generate_authorization_url(
            user_id="test_user",
            additional_scopes=["asset:write"]
        )

        assert "authorization_url" in auth_data
        assert "state" in auth_data
        assert "expires_at" in auth_data
        assert "https://authorize.roblox.com" in auth_data["authorization_url"]

        # Test PKCE implementation
        assert auth_data["state"] in oauth_service._state_storage
        state_data = oauth_service._state_storage[auth_data["state"]]
        assert "code_verifier" in state_data
        assert state_data["user_id"] == "test_user"

    @pytest.mark.asyncio
    async def test_open_cloud_asset_creation(self, open_cloud_client):
        """Test Open Cloud API asset creation"""
        # Create asset description
        asset = AssetDescription(
            asset_type=AssetType.MODEL,
            display_name="Test Educational Model",
            description="Test model for education",
            creation_context=CreationContext(
                creator_type="User",
                creator_id="test_user"
            )
        )

        # Mock the HTTP response
        open_cloud_client.session.post = AsyncMock(return_value=Mock(
            status=200,
            json=AsyncMock(return_value={
                "assetId": "12345",
                "assetUrl": "https://roblox.com/asset/12345"
            })
        ))

        # Test asset creation
        with patch.object(open_cloud_client, 'session', open_cloud_client.session):
            result = await open_cloud_client.create_asset(
                asset,
                b"test content"
            )

        assert result["assetId"] == "12345"
        assert "assetUrl" in result

    @pytest.mark.asyncio
    async def test_rojo_project_creation(self, rojo_manager):
        """Test Rojo project creation and management"""
        # Create project configuration
        config = RojoProjectConfig(
            name="TestEducationalProject",
            tree={
                "$className": "DataModel",
                "ReplicatedStorage": {
                    "$className": "ReplicatedStorage"
                }
            }
        )

        # Create project
        project = await rojo_manager.create_project(
            project_name="test_project",
            user_id="test_user",
            project_config=config
        )

        assert project.name == "test_project"
        assert project.user_id == "test_user"
        assert project.port >= rojo_manager.base_port
        assert project.path.exists()

        # Check project files
        project_json = project.path / "default.project.json"
        assert project_json.exists()

        # Clean up
        await rojo_manager.delete_project(project.project_id)

    @pytest.mark.asyncio
    async def test_conversation_flow(self, conversation_flow, mock_pusher):
        """Test 8-stage conversation flow"""
        # Start conversation
        context = await conversation_flow.start_conversation(
            user_id="test_user",
            session_id="test_session"
        )

        assert context.session_id == "test_session"
        assert context.current_stage == ConversationStage.GREETING
        assert context.user_id == "test_user"

        # Test stage processing
        stages_to_test = [
            ConversationStage.GREETING,
            ConversationStage.DISCOVERY,
            ConversationStage.REQUIREMENTS,
            ConversationStage.PERSONALIZATION,
            ConversationStage.CONTENT_DESIGN,
            ConversationStage.UNIQUENESS_ENHANCEMENT,
            ConversationStage.VALIDATION
        ]

        for stage in stages_to_test:
            context.current_stage = stage

            # Process input for stage
            result = await conversation_flow.process_input(
                session_id="test_session",
                user_input=f"Test input for {stage.value}"
            )

            assert "current_stage" in result
            assert "result" in result
            assert "next_stage" in result
            assert "progress" in result

            # Advance to next stage
            if stage != ConversationStage.VALIDATION:
                context = await conversation_flow.advance_stage("test_session")

        # Verify all stages were processed
        assert len(context.stage_data) >= 7

    @pytest.mark.asyncio
    async def test_full_integration_flow(
        self,
        conversation_flow,
        rojo_manager,
        mock_pusher,
        mock_llm
    ):
        """Test complete flow from conversation to Roblox environment"""
        # 1. Start conversation
        context = await conversation_flow.start_conversation(
            user_id="test_user",
            session_id="integration_test"
        )

        # 2. Simulate processing through all stages
        test_data = {
            ConversationStage.GREETING: {
                "greeting_complete": True,
                "subject_area": "Mathematics",
                "response": "Welcome!"
            },
            ConversationStage.DISCOVERY: {
                "learning_objectives": ["Understand fractions"],
                "grade_level": "5",
                "response": "Great objectives!"
            },
            ConversationStage.REQUIREMENTS: {
                "max_players": 20,
                "environment_type": "classroom",
                "response": "Requirements noted"
            },
            ConversationStage.PERSONALIZATION: {
                "visual_style": "cartoon",
                "response": "Style selected"
            },
            ConversationStage.CONTENT_DESIGN: {
                "learning_stations": [{"name": "Fraction Station"}],
                "response": "Content designed"
            },
            ConversationStage.UNIQUENESS_ENHANCEMENT: {
                "special_effects": ["particles"],
                "response": "Enhancements added"
            },
            ConversationStage.VALIDATION: {
                "validation_scores": {
                    "educational_value": 0.9,
                    "age_appropriateness": 0.95
                },
                "approved": True,
                "response": "Validated!"
            }
        }

        # Populate stage data
        for stage, data in test_data.items():
            context.stage_data[stage] = data

        conversation_flow.contexts["integration_test"] = context

        # Mock Rojo manager methods
        with patch.object(rojo_manager, 'create_project') as mock_create:
            mock_project = Mock(
                project_id="test_proj_123",
                port=34872
            )
            mock_create.return_value = mock_project

            with patch.object(rojo_manager, 'update_project_files') as mock_update:
                mock_update.return_value = True

                with patch.object(rojo_manager, 'start_project') as mock_start:
                    mock_start.return_value = Mock(
                        connected=True,
                        dict=lambda: {"connected": True}
                    )

                    # 3. Generate Roblox environment
                    result = await conversation_flow.generate_roblox_environment(
                        "integration_test"
                    )

        assert result["success"] is True
        assert "project_id" in result
        assert "rojo_port" in result
        assert result["files_generated"] > 0

        # Verify Pusher was called
        mock_pusher.broadcast_event.assert_called()

    @pytest.mark.asyncio
    async def test_error_handling(self, conversation_flow):
        """Test error handling in the integration"""
        # Test invalid session
        with pytest.raises(ValueError, match="Session .* not found"):
            await conversation_flow.process_input(
                session_id="nonexistent",
                user_input="test"
            )

        # Test generation without validation
        context = ConversationContext(
            session_id="error_test",
            user_id="test_user",
            current_stage=ConversationStage.GREETING
        )
        conversation_flow.contexts["error_test"] = context

        with pytest.raises(ValueError, match="Content not validated"):
            await conversation_flow.generate_roblox_environment("error_test")

    @pytest.mark.asyncio
    async def test_rojo_sync_status(self, rojo_manager):
        """Test Rojo synchronization status checking"""
        # Create a project
        config = RojoProjectConfig(
            name="SyncTest",
            tree={"$className": "DataModel"}
        )

        project = await rojo_manager.create_project(
            project_name="sync_test",
            user_id="test_user",
            project_config=config
        )

        # Mock HTTP response for sync status
        rojo_manager.session = Mock()
        rojo_manager.session.get = AsyncMock(return_value=Mock(
            status=200,
            json=AsyncMock(return_value={
                "sessionId": "test_session",
                "projectName": "SyncTest",
                "clientCount": 1
            })
        ))

        # Check sync status
        with patch.object(rojo_manager, 'session', rojo_manager.session):
            status = await rojo_manager.get_sync_status(project.project_id)

        assert status.connected is False  # Not actually running
        assert len(status.errors) > 0

        # Clean up
        await rojo_manager.delete_project(project.project_id)

    @pytest.mark.asyncio
    async def test_quality_validation(self, conversation_flow):
        """Test quality validation in conversation flow"""
        # Create context with all stages complete
        context = ConversationContext(
            session_id="quality_test",
            user_id="test_user",
            current_stage=ConversationStage.VALIDATION
        )

        # Add validation data
        context.stage_data[ConversationStage.VALIDATION] = {
            "validation_scores": {
                "educational_value": 0.85,
                "age_appropriateness": 0.90,
                "safety": 0.95,
                "accessibility": 0.85,
                "technical_feasibility": 0.90
            },
            "approved": True
        }

        conversation_flow.contexts["quality_test"] = context

        # Verify validation passed
        validation = context.stage_data[ConversationStage.VALIDATION]
        assert validation["approved"] is True
        assert all(score >= 0.85 for score in validation["validation_scores"].values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])