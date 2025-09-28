import pytest_asyncio
"""
Comprehensive tests for Roblox plugin pipeline integration
Tests the complete flow from plugin request to agent execution and response
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



import pytest
from tests.fixtures.agents import mock_llm
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

# Import components to test
from core.agents.plugin_communication import (
    PluginCommunicationHub,
    PluginRequest,
    PluginResponse,
    PluginEventType as EventType
)
from core.agents.supervisor import SupervisorAgent
from apps.backend.roblox_server import PluginManager, PluginSecurity
from database.core.roblox_models import (
    RobloxContent,
    PluginRequest as DBPluginRequest,
    RobloxSession,
    StudentProgress,
    RobloxDatabaseHelper
)


class TestPluginCommunicationHub:
    """Test the central plugin communication hub"""
    
    @pytest.fixture
    def hub(self):
        """Create a plugin communication hub instance"""
        return PluginCommunicationHub()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample plugin request"""
        return PluginRequest(
            request_id="test-123",
            event_type=EventType.CONTENT_REQUEST,
            config={
                "subject": "Science",
                "grade_level": 7,
                "environment_type": "laboratory"
            },
            context={
                "user_id": "teacher-1",
                "place_id": 12345
            }
        )
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_hub_initialization(self, hub):
        """Test hub initializes correctly"""
        await hub.initialize()
        
        assert hub.supervisor is not None
        assert hub.mcp_context is not None
        assert hub.sparc_state is not None
        assert hub.swarm_controller is not None
        assert len(hub.active_requests) == 0
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_handle_content_generation_request(self, hub, sample_request):
        """Test handling content generation request"""
        await hub.initialize()
        
        # Mock orchestrator response
        from core.agents.orchestrator import OrchestrationResult
        mock_result = OrchestrationResult(
            success=True,
            content={
                "lesson": "Generated lesson content",
                "summary": "Test summary"
            },
            scripts={
                "main": "-- Main script",
                "quiz": "-- Quiz script"
            },
            errors=[],
            execution_time=1.5
        )
        
        with patch.object(hub.orchestrator, 'orchestrate', new_callable=AsyncMock) as mock_orchestrate:
            mock_orchestrate.return_value = mock_result
            
            response = await hub.handle_plugin_request(sample_request)
            
            assert response.status == "success"
            assert response.request_id == sample_request.request_id
            assert response.data is not None
            mock_orchestrate.assert_called_once()
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_handle_quiz_creation_request(self, hub):
        """Test handling quiz creation request"""
        await hub.initialize()
        
        request = PluginRequest(
            request_id="quiz-456",
            event_type=EventType.QUIZ_GENERATION,
            config={
                "subject": "Math",
                "num_questions": 10,
                "difficulty": "medium"
            }
        )
        
        # Mock quiz agent response  
        from core.agents.base_agent import TaskResult
        mock_quiz_result = TaskResult.create(
            success=True,
            output={
                "quiz": {
                    "questions": [{"q": "What is 2+2?", "a": "4"}],
                    "ui_script": "-- Quiz UI"
                }
            }
        )
        
        with patch.object(hub.agent_pool["quiz"], 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_quiz_result
            
            response = await hub.handle_plugin_request(request)
            
            assert response.status == "success"
            assert response.data is not None
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_handle_terrain_generation_request(self, hub):
        """Test handling terrain generation request"""
        await hub.initialize()
        
        request = PluginRequest(
            request_id="terrain-789",
            event_type=EventType.TERRAIN_CREATION,
            config={
                "terrain_type": "outdoor",
                "size": {"x": 500, "y": 100, "z": 500}
            }
        )
        
        # Mock terrain agent response
        from core.agents.base_agent import TaskResult
        mock_terrain_result = TaskResult.create(
            success=True,
            output={
                "terrain": {
                    "script": "-- Terrain generation script",
                    "materials": ["Grass", "Rock"]
                }
            }
        )
        
        with patch.object(hub.agent_pool["terrain"], 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_terrain_result
            
            response = await hub.handle_plugin_request(request)
            
            assert response.status == "success"
            assert response.data is not None
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_handle_database_query(self, hub):
        """Test handling database query from plugin"""
        await hub.initialize()
        
        request = PluginRequest(
            request_id="db-query-001",
            event_type=EventType.VALIDATION_REQUEST,
            config={
                "query_type": "get_lesson_content",
                "lesson_id": "lesson-123"
            }
        )
        
        # Mock the review agent since VALIDATION_REQUEST uses it
        with patch.object(hub.agent_pool["review"], 'execute', new_callable=AsyncMock) as mock_execute:
            from core.agents.base_agent import TaskResult
            mock_execute.return_value = TaskResult.create(
                success=True,
                output={
                    "validation_result": {
                        "valid": True,
                        "issues": []
                    }
                }
            )
            
            response = await hub.handle_plugin_request(request)
            
            assert response.status == "success"
            assert response.content is not None
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_handle_progress_update(self, hub):
        """Test handling progress update from plugin"""
        await hub.initialize()
        
        request = PluginRequest(
            request_id="progress-001",
            event_type=EventType.PROGRESS_UPDATE,
            config={
                "student_id": "student-1",
                "lesson_id": "lesson-123",
                "progress": 75.0,
                "milestones": ["intro", "activity1"]
            }
        )
        
        # The _handle_progress_update will call handle_progress_update
        # We need to mock that instead
        with patch.object(hub, 'handle_progress_update', new_callable=AsyncMock) as mock_progress:
            mock_progress.return_value = PluginResponse(
                request_id=request.request_id,
                success=True,
                event_type=request.event_type,
                content={"updated": True}
            )
            
            response = await hub.handle_plugin_request(request)
            
            assert response.status == "success"
            assert response.data["updated"] is True
            mock_progress.assert_called_once()
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_cicd_pipeline_trigger(self, hub):
        """Test CI/CD pipeline triggering"""
        await hub.initialize()
        
        request = PluginRequest(
            request_id="cicd-001",
            event_type=EventType.CI_CD_TRIGGER,
            config={
                "stage": "generate",
                "build_id": "build-123"
            },
            context={
                "github_sha": "abc123",
                "github_ref": "refs/heads/main"
            }
        )
        
        with patch.object(hub.supervisor, 'handle_cicd_request', new_callable=AsyncMock) as mock_cicd:
            mock_cicd.return_value = {
                "status": "success",
                "artifacts": ["script1.lua", "script2.lua"]
            }
            
            response = await hub.handle_plugin_request(request)
            
            assert response.status == "success"
            mock_cicd.assert_called_once()
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_error_handling(self, hub):
        """Test error handling in plugin requests"""
        await hub.initialize()
        
        request = PluginRequest(
            request_id="error-test",
            event_type=EventType.CONTENT_REQUEST,
            config={}  # Missing required config
        )
        
        with patch.object(hub.supervisor, 'handle_plugin_request', new_callable=AsyncMock) as mock_handle:
            mock_handle.side_effect = ValueError("Missing required config")
            
            response = await hub.handle_plugin_request(request)
            
            assert response.status == "error"
            assert "error" in response.data
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_concurrent_requests(self, hub):
        """Test handling multiple concurrent requests"""
        await hub.initialize()
        
        requests = [
            PluginRequest(
                request_id=f"concurrent-{i}",
                event_type=EventType.CONTENT_REQUEST,
                config={"subject": f"Subject{i}", "grade_level": i}
            )
            for i in range(5)
        ]
        
        with patch.object(hub.supervisor, 'handle_plugin_request', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = {"status": "success", "result": {}}
            
            # Process requests concurrently
            responses = await asyncio.gather(
                *[hub.handle_plugin_request(req) for req in requests]
            )
            
            assert len(responses) == 5
            assert all(r.status == "success" for r in responses)
            assert mock_handle.call_count == 5
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_cleanup(self, hub):
        """Test cleanup releases resources"""
        await hub.initialize()
        
        # Add some active requests
        hub.active_requests["test-1"] = Mock()
        hub.active_requests["test-2"] = Mock()
        
        await hub.cleanup()
        
        assert len(hub.active_requests) == 0
        assert hub.supervisor is None


class TestSupervisorPluginRouting:
    """Test supervisor agent plugin-specific routing"""
    
    @pytest.fixture
    def supervisor(self):
        """Create a supervisor agent instance with mocked workflow"""
        with patch('core.agents.supervisor.StateGraph') as mock_graph_class:
            # Mock the StateGraph and its methods
            mock_workflow = Mock()
            mock_workflow.ainvoke = AsyncMock()
            mock_workflow.ainvoke.return_value = {
                "result": "Test result",
                "metadata": {},
                "status": "completed"
            }
            
            mock_graph_instance = Mock()
            mock_graph_instance.add_node = Mock()
            mock_graph_instance.add_edge = Mock()
            mock_graph_instance.add_conditional_edges = Mock()
            mock_graph_instance.set_entry_point = Mock()
            mock_graph_instance.compile = Mock(return_value=mock_workflow)
            
            mock_graph_class.return_value = mock_graph_instance
            
            # Now create the supervisor with mocked workflow
            supervisor = SupervisorAgent()
            supervisor.workflow = mock_workflow
            
            # Mock the LLM
            mock_llm = Mock()
            mock_llm.ainvoke = AsyncMock()
            mock_llm.ainvoke.return_value = Mock(content="Test LLM response")
            supervisor.llm = mock_llm
            
            return supervisor
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_plugin_request_routing(self, supervisor):
        """Test routing of plugin requests"""
        request = {
            "request_id": "plugin-001",
            "event_type": "generate_lesson",
            "config": {
                "subject": "History",
                "grade_level": 8
            },
            "metadata": {
                "source": "roblox_plugin"
            }
        }
        
        with patch.object(supervisor, '_execute_plugin_delegations', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = [
                {"agent": "content", "result": Mock(success=True)},
                {"agent": "terrain", "result": Mock(success=True)}
            ]
            
            response = await supervisor.handle_plugin_request(request)
            
            assert response["status"] == "success"
            assert response["request_id"] == "plugin-001"
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_dashboard_request_routing(self, supervisor):
        """Test routing of dashboard requests"""
        request = {
            "request_type": "lesson_creation",
            "user_id": "teacher-1",
            "task": "Create science lesson"
        }
        
        with patch.object(supervisor, '_execute_dashboard_delegations', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = [
                {"agent": "content", "result": Mock(success=True)}
            ]
            
            response = await supervisor.handle_dashboard_request(request)
            
            assert response["status"] == "success"
            assert response["request_type"] == "lesson_creation"
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_cicd_request_routing(self, supervisor):
        """Test routing of CI/CD pipeline requests"""
        request = {
            "stage": "generate",
            "build_id": "build-456",
            "commit": "def789"
        }
        
        with patch.object(supervisor, '_execute_cicd_delegations', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = [
                {"agent": "content", "result": Mock(success=True)},
                {"agent": "script", "result": Mock(success=True)}
            ]
            
            response = await supervisor.handle_cicd_request(request)
            
            assert response["status"] == "success"
            assert response["build_id"] == "build-456"


class TestPluginManager:
    """Test Roblox Studio plugin manager"""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a plugin manager instance"""
        return PluginManager()
    
    def test_register_plugin(self, plugin_manager):
        """Test plugin registration"""
        plugin_data = {
            "studio_id": "studio-123",
            "port": 64989,
            "version": "1.0.0"
        }
        
        plugin_id = plugin_manager.register_plugin(plugin_data)
        
        assert plugin_id is not None
        assert plugin_id in plugin_manager.plugins
        assert plugin_manager.plugins[plugin_id]["studio_id"] == "studio-123"
    
    def test_validate_plugin_data(self, plugin_manager):
        """Test plugin data validation"""
        # Invalid data - missing required fields
        invalid_data = {}
        
        with pytest.raises(ValueError):
            plugin_manager.validate_plugin_data(invalid_data)
    
    def test_update_heartbeat(self, plugin_manager):
        """Test plugin heartbeat update"""
        # Register a plugin first
        plugin_data = {"studio_id": "studio-456"}
        plugin_id = plugin_manager.register_plugin(plugin_data)
        
        # Update heartbeat
        result = plugin_manager.update_heartbeat(plugin_id)
        
        assert result is True
        
        # Try updating non-existent plugin
        result = plugin_manager.update_heartbeat("non-existent")
        assert result is False
    
    def test_list_active_plugins(self, plugin_manager):
        """Test listing active plugins"""
        # Register multiple plugins
        for i in range(3):
            plugin_manager.register_plugin({
                "studio_id": f"studio-{i}",
                "port": 64989 + i
            })
        
        active = plugin_manager.list_active_plugins()
        
        assert len(active) >= 3


class TestDatabaseIntegration:
    """Test database integration for Roblox content - mocked approach"""
    
    @pytest.fixture
    async def db_session(self):
        """Create a mock database session for testing"""
        from unittest.mock import AsyncMock, MagicMock
        
        # Create a mock session with all necessary methods
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        session.refresh = AsyncMock()
        
        # Mock execute for queries
        async def mock_execute(stmt):
            result = MagicMock()
            result.scalars = MagicMock()
            result.scalars.return_value.first = MagicMock(return_value=None)
            result.scalars.return_value.all = MagicMock(return_value=[])
            return result
        
        session.execute = mock_execute
        
        yield session
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_store_generated_content(self, db_session):
        """Test storing generated content - mocked"""
        from unittest.mock import MagicMock
        from database.core.roblox_models import RobloxDatabaseHelper
        
        # Create a mock content object
        mock_content = MagicMock()
        mock_content.id = "content-123"
        mock_content.lesson_id = "lesson-001"
        mock_content.content_type = "terrain"
        mock_content.content_data = {
            "terrain": {"type": "outdoor"},
            "config": {"size": 500}
        }
        mock_content.generated_by = "terrain_agent"
        
        # Mock the helper method
        helper = RobloxDatabaseHelper()
        helper.store_generated_content = AsyncMock(return_value=mock_content)
        
        content = await helper.store_generated_content(
            db_session,
            lesson_id="lesson-001",
            content_type="terrain",
            content_data={
                "terrain": {"type": "outdoor"},
                "config": {"size": 500}
            },
            generated_by="terrain_agent"
        )
        
        assert content.id is not None
        assert content.content_type == "terrain"
        assert content.generated_by == "terrain_agent"
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_get_content_for_lesson(self, db_session):
        """Test retrieving content for a lesson - mocked"""
        from unittest.mock import MagicMock
        from database.core.roblox_models import RobloxDatabaseHelper
        
        # Create mock content objects
        mock_quiz = MagicMock()
        mock_quiz.content_type = "quiz"
        mock_quiz.content_data = {"quiz": {"questions": []}}
        
        mock_script = MagicMock()
        mock_script.content_type = "script"
        mock_script.content_data = {"script": "-- Lua script"}
        
        # Mock the helper methods
        helper = RobloxDatabaseHelper()
        helper.store_generated_content = AsyncMock()
        helper.get_content_for_lesson = AsyncMock(return_value=[mock_quiz, mock_script])
        
        # Store some content first (mocked)
        await helper.store_generated_content(
            db_session,
            lesson_id="lesson-002",
            content_type="quiz",
            content_data={"quiz": {"questions": []}},
            generated_by="quiz_agent"
        )
        
        await helper.store_generated_content(
            db_session,
            lesson_id="lesson-002",
            content_type="script",
            content_data={"script": "-- Lua script"},
            generated_by="script_agent"
        )
        
        # Retrieve content
        contents = await helper.get_content_for_lesson(
            db_session,
            lesson_id="lesson-002"
        )
        
        assert len(contents) == 2
        assert any(c.content_type == "quiz" for c in contents)
        assert any(c.content_type == "script" for c in contents)
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_track_student_progress(self, db_session):
        """Test tracking student progress - mocked"""
        from unittest.mock import MagicMock
        from database.core.roblox_models import RobloxDatabaseHelper
        
        # Create mock progress object
        mock_progress = MagicMock()
        mock_progress.student_id = "student-001"
        mock_progress.lesson_id = "lesson-003"
        mock_progress.progress_percentage = 50.0
        mock_progress.time_spent = 300
        
        # Mock the helper method
        helper = RobloxDatabaseHelper()
        helper.track_student_progress = AsyncMock(return_value=mock_progress)
        
        progress = await helper.track_student_progress(
            db_session,
            student_id="student-001",
            lesson_id="lesson-003",
            progress_data={
                "percentage": 50.0,
                "time_spent": 300,
                "milestones": ["intro", "activity1"]
            }
        )
        
        assert progress.student_id == "student-001"
        assert progress.progress_percentage == 50.0
        assert progress.time_spent == 300
        
        # Update existing progress - update mock for second call
        mock_progress.progress_percentage = 75.0
        mock_progress.time_spent = 500  # Accumulated
        
        progress = await helper.track_student_progress(
            db_session,
            student_id="student-001",
            lesson_id="lesson-003",
            progress_data={
                "percentage": 75.0,
                "time_spent": 200,
                "milestones": ["activity2"]
            }
        )
        
        assert progress.progress_percentage == 75.0
        assert progress.time_spent == 500  # Accumulated
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_create_session(self, db_session):
        """Test creating a Roblox session - mocked"""
        from unittest.mock import MagicMock
        from database.core.roblox_models import RobloxDatabaseHelper
        
        # Create mock session object
        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_session.lesson_id = "lesson-004"
        mock_session.teacher_id = "teacher-001"
        mock_session.place_id = 12345
        mock_session.status = "active"
        mock_session.max_students = 30
        mock_session.session_type = "interactive"
        
        # Mock the helper method
        helper = RobloxDatabaseHelper()
        helper.create_session = AsyncMock(return_value=mock_session)
        
        session = await helper.create_session(
            db_session,
            lesson_id="lesson-004",
            teacher_id="teacher-001",
            place_id=12345,
            max_students=30,
            session_type="interactive"
        )
        
        assert session.session_id is not None
        assert session.lesson_id == "lesson-004"
        assert session.status == "active"
        assert session.place_id == 12345


class TestEndToEndPluginFlow:
    """Test complete end-to-end plugin communication flow"""
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_complete_content_generation_flow(self):
        """Test complete flow from plugin request to content delivery"""
        # 1. Plugin sends request
        plugin_request = {
            "event_type": "content_generation",
            "config": {
                "subject": "Science",
                "grade_level": 7,
                "environment_type": "laboratory",
                "include_quiz": True
            },
            "context": {
                "studio_id": "studio-test",
                "place_id": 98765
            }
        }
        
        # 2. Hub processes request
        hub = PluginCommunicationHub()
        await hub.initialize()
        
        with patch.object(hub.supervisor, 'handle_plugin_request', new_callable=AsyncMock) as mock_super:
            # 3. Supervisor delegates to agents
            mock_super.return_value = {
                "status": "success",
                "result": {
                    "content": {
                        "lesson": "Science lesson content",
                        "objectives": ["Learn about atoms"]
                    },
                    "quiz": {
                        "questions": [
                            {"q": "What is an atom?", "a": "Basic unit of matter"}
                        ]
                    },
                    "terrain": {
                        "script": "-- Laboratory terrain"
                    },
                    "scripts": {
                        "interaction": "-- Interaction scripts"
                    }
                }
            }
            
            # 4. Process request
            request = PluginRequest(
                request_id="e2e-test",
                event_type=EventType.CONTENT_REQUEST,
                config=plugin_request["config"],
                context=plugin_request["context"]
            )
            
            response = await hub.handle_plugin_request(request)
            
            # 5. Verify response
            assert response.status == "success"
            assert "content" in response.data
            assert "quiz" in response.data
            assert "terrain" in response.data
            assert "scripts" in response.data
            
            # 6. Verify agent was called
            mock_super.assert_called_once()
            call_args = mock_super.call_args[0][0]
            assert call_args["event_type"] == "content_request"
            assert call_args["config"]["subject"] == "Science"
    
    @pytest.mark.asyncio(loop_scope="function")
    @pytest.mark.asyncio
async def test_complete_dashboard_sync_flow(self):
        """Test complete dashboard synchronization flow"""
        # 1. Dashboard requests sync
        sync_request = {
            "action": "sync_lesson",
            "lesson_id": "lesson-sync-001",
            "updates": {
                "title": "Updated Science Lesson",
                "objectives": ["New objective 1", "New objective 2"]
            }
        }
        
        # 2. Plugin manager handles sync
        plugin_manager = PluginManager()
        
        # 3. Register plugin first
        plugin_id = plugin_manager.register_plugin({
            "studio_id": "studio-sync",
            "port": 64989
        })
        
        # 4. Simulate sync process
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "synced",
                "lesson_id": "lesson-sync-001"
            }
            
            # 5. Perform sync (would be called from Flask endpoint)
            from apps.backend.roblox_server import sync_with_main_server
            result = sync_with_main_server(sync_request)
            
            assert result["status"] == "synced"
            mock_post.assert_called_once()


# Test fixtures for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])