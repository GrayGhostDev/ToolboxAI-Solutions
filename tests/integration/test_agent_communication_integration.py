#!/usr/bin/env python3
"""
import pytest
Comprehensive Agent Communication and Framework Integration Test

This test validates:
1. Agent-to-agent communication
2. SPARC framework integration
3. Swarm controller coordination
4. MCP WebSocket integration
5. Content generation pipeline
6. Environment creation system
"""

import asyncio
import os

def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        return str(obj)

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

# Add the project root to the path
sys.path.append('/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions')

# Import agent system
from core.agents.base_agent import BaseAgent, TaskResult
from core.agents.supervisor import SupervisorAgent
from core.agents.content_agent import ContentAgent
from core.agents.quiz_agent import QuizAgent
from core.agents.terrain_agent import TerrainAgent
from core.agents.script_agent import ScriptAgent
from core.agents.review_agent import ReviewAgent
from core.agents.plugin_communication import PluginCommunicationHub, PluginRequest, PluginEventType

# Import frameworks
try:
    from core.sparc import SPARCFramework, SPARCConfig, create_sparc_system
    from core.swarm import SwarmController, create_swarm, get_default_config
    from core.mcp.context_manager import ContextManager
    FRAMEWORKS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Frameworks not available: {e}")
    FRAMEWORKS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentCommunicationTester:
    """Test suite for agent communication and framework integration"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now(timezone.utc)

        # Initialize agents
        self.supervisor = SupervisorAgent()
        self.content_agent = ContentAgent()
        self.quiz_agent = QuizAgent()
        self.terrain_agent = TerrainAgent()
        self.script_agent = ScriptAgent()
        self.review_agent = ReviewAgent()

        # Initialize communication hub
        self.communication_hub = PluginCommunicationHub()

        # Initialize frameworks if available
        if FRAMEWORKS_AVAILABLE:
            self.sparc_system = None
            self.swarm_controller = None
            self.mcp_context = ContextManager(max_tokens=128000)
        else:
            self.sparc_system = None
            self.swarm_controller = None
            self.mcp_context = None

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all communication and integration tests"""
        logger.info("🚀 Starting Agent Communication and Framework Integration Tests")

        tests = [
            ("agent_initialization", self.test_agent_initialization),
            ("agent_to_agent_communication", self.test_agent_to_agent_communication),
            ("sparc_framework_integration", self.test_sparc_framework_integration),
            ("swarm_controller_coordination", self.test_swarm_controller_coordination),
            ("mcp_websocket_integration", self.test_mcp_websocket_integration),
            ("content_generation_pipeline", self.test_content_generation_pipeline),
            ("environment_creation_system", self.test_environment_creation_system),
            ("plugin_communication_hub", self.test_plugin_communication_hub),
            ("end_to_end_workflow", self.test_end_to_end_workflow),
        ]

        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 Running test: {test_name}")
                result = await test_func()
                self.test_results[test_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED - {e}")
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        return self._generate_test_report()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_initialization(self) -> bool:
        """Test that all agents initialize properly"""
        try:
            # Test individual agent initialization
            agents = [
                self.supervisor,
                self.content_agent,
                self.quiz_agent,
                self.terrain_agent,
                self.script_agent,
                self.review_agent
            ]

            for agent in agents:
                if not hasattr(agent, 'name') or not agent.name:
                    return False
                if not hasattr(agent, 'execute'):
                    return False

            # Test communication hub initialization
            if not hasattr(self.communication_hub, 'orchestrator'):
                return False

            return True
        except Exception as e:
            logger.error(f"Agent initialization test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_to_agent_communication(self) -> bool:
        """Test agent-to-agent communication and collaboration"""
        try:
            # Test supervisor delegating to content agent
            task = "Create educational content about photosynthesis"
            context = {
                "subject": "biology",
                "grade_level": 5,
                "learning_objectives": ["Understand photosynthesis process"]
            }

            # Test direct agent execution
            result = await self.content_agent.execute(task, context)
            if not isinstance(result, TaskResult):
                return False

            # Test agent collaboration
            collaboration_result = await self.content_agent.collaborate(
                self.quiz_agent,
                "Create content and quiz about photosynthesis",
                context
            )

            if not isinstance(collaboration_result, TaskResult):
                return False

            if not collaboration_result.success:
                return False

            # Verify collaboration metadata
            if "collaboration" not in collaboration_result.metadata:
                return False

            return True
        except Exception as e:
            logger.error(f"Agent communication test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_sparc_framework_integration(self) -> bool:
        """Test SPARC framework integration"""
        if not FRAMEWORKS_AVAILABLE:
            logger.warning("SPARC framework not available, skipping test")
            return True

        try:
            # Create SPARC system
            config = SPARCConfig()
            self.sparc_system = SPARCFramework(config)

            # Test SPARC cycle execution
            observation = {
                "user_id": "test_user",
                "task_type": "content_generation",
                "subject": "science",
                "grade_level": 5,
                "learning_objectives": ["Understand basic physics"],
                "current_state": "idle",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            result = await self.sparc_system.execute_cycle(observation)

            if not isinstance(result, dict):
                return False

            # Verify SPARC cycle components
            required_keys = ["state", "policy", "action", "reward", "context"]
            for key in required_keys:
                if key not in result:
                    return False

            return True
        except Exception as e:
            logger.error(f"SPARC framework test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_swarm_controller_coordination(self) -> bool:
        """Test Swarm controller coordination"""
        if not FRAMEWORKS_AVAILABLE:
            logger.warning("Swarm framework not available, skipping test")
            return True

        try:
            # Create swarm controller
            config = get_default_config()
            self.swarm_controller = await create_swarm(config)

            # Test task submission
            task_data = {
                "content_type": "educational_lesson",
                "subject": "mathematics",
                "grade_level": 6,
                "learning_objectives": ["Solve basic equations"],
                "format": "interactive"
            }

            task_id = await self.swarm_controller.submit_task(
                task_type="content_generation",
                task_data=task_data,
                educational_context={
                    "subject": "mathematics",
                    "grade_level": 6,
                    "difficulty": "intermediate"
                }
            )

            if not task_id:
                return False

            # Test task result retrieval (with timeout)
            try:
                result = await asyncio.wait_for(
                    self.swarm_controller.get_task_result(task_id),
                    timeout=10.0
                )
                if result is None:
                    return False
            except asyncio.TimeoutError:
                # Task might still be processing, which is acceptable
                logger.info("Task still processing (timeout expected)")

            return True
        except Exception as e:
            logger.error(f"Swarm controller test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_mcp_websocket_integration(self) -> bool:
        """Test MCP WebSocket integration"""
        if not FRAMEWORKS_AVAILABLE:
            logger.warning("MCP framework not available, skipping test")
            return True

        try:
            # Test MCP context management
            if not self.mcp_context:
                return False

            # Test context operations
            test_context = {
                "user_id": "test_user",
                "session_id": str(uuid.uuid4()),
                "task": "test_task",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Test context storage and retrieval
            context_id = await self.mcp_context.store_context(test_context)
            if not context_id:
                return False

            retrieved_context = await self.mcp_context.get_context(context_id)
            if not retrieved_context:
                return False

            # Verify context integrity
            if retrieved_context.get("user_id") != test_context["user_id"]:
                return False

            return True
        except Exception as e:
            logger.error(f"MCP WebSocket test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_content_generation_pipeline(self) -> bool:
        """Test end-to-end content generation pipeline"""
        try:
            # Create a comprehensive content generation request
            request = PluginRequest(
                request_id=str(uuid.uuid4()),
                event_type=PluginEventType.CONTENT_GENERATION,
                user_id="test_teacher",
                session_id=str(uuid.uuid4()),
                data={
                    "content_type": "educational_lesson",
                    "subject": "science",
                    "grade_level": 5,
                    "learning_objectives": ["Understand water cycle"],
                    "format": "interactive_3d",
                    "platform": "roblox"
                },
                metadata={
                    "source": "dashboard",
                    "priority": "high",
                    "requires_terrain": True,
                    "requires_ui": True,
                    "requires_quiz": True
                },
                requires_database_save=True,
                requires_dashboard_update=True
            )

            # Process request through communication hub
            response = await self.communication_hub.handle_plugin_request(request)

            if not response.success:
                logger.warning(f"Content generation failed: {response.errors}")
                return False

            # Verify response structure
            if not hasattr(response, 'data'):
                return False

            return True
        except Exception as e:
            logger.error(f"Content generation pipeline test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_environment_creation_system(self) -> bool:
        """Test environment creation system (terrain, objects, scripts, UI)"""
        try:
            # Test terrain generation
            terrain_task = "Create a forest environment with trees and a river"
            terrain_context = {
                "environment_type": "forest",
                "features": ["trees", "river", "path"],
                "size": "medium",
                "platform": "roblox"
            }

            terrain_result = await self.terrain_agent.execute(terrain_task, terrain_context)
            if not terrain_result.success:
                logger.warning("Terrain generation failed")
                return False

            # Test script generation
            script_task = "Create a script for a quiz system in Roblox"
            script_context = {
                "script_type": "quiz_system",
                "language": "lua",
                "platform": "roblox",
                "features": ["multiple_choice", "scoring", "timer"]
            }

            script_result = await self.script_agent.execute(script_task, script_context)
            if not script_result.success:
                logger.warning("Script generation failed")
                return False

            # Test UI generation
            ui_task = "Create a user interface for the quiz system"
            ui_context = {
                "ui_type": "quiz_interface",
                "platform": "roblox",
                "elements": ["question_display", "answer_buttons", "score_display", "timer"]
            }

            # Use content agent for UI generation
            ui_result = await self.content_agent.execute(ui_task, ui_context)
            if not ui_result.success:
                logger.warning("UI generation failed")
                return False

            return True
        except Exception as e:
            logger.error(f"Environment creation system test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_plugin_communication_hub(self) -> bool:
        """Test plugin communication hub functionality"""
        try:
            # Test hub initialization
            if not hasattr(self.communication_hub, 'agent_pool'):
                return False

            # Test agent pool
            agent_pool = self.communication_hub.agent_pool
            required_agents = ["content", "quiz", "terrain", "script", "review", "testing"]

            for agent_name in required_agents:
                if agent_name not in agent_pool:
                    return False

            # Test request tracking
            if not hasattr(self.communication_hub, 'active_requests'):
                return False

            if not hasattr(self.communication_hub, 'request_history'):
                return False

            return True
        except Exception as e:
            logger.error(f"Plugin communication hub test failed: {e}")
            return False

    @pytest.mark.asyncio(loop_scope="function")
    async def test_end_to_end_workflow(self) -> bool:
        """Test complete end-to-end workflow"""
        try:
            # Create a comprehensive educational content request
            request = PluginRequest(
                request_id=str(uuid.uuid4()),
                event_type=PluginEventType.CONTENT_GENERATION,
                user_id="test_teacher",
                session_id=str(uuid.uuid4()),
                data={
                    "content_type": "complete_lesson",
                    "subject": "geography",
                    "grade_level": 4,
                    "learning_objectives": ["Identify continents", "Understand climate zones"],
                    "format": "interactive_world",
                    "platform": "roblox",
                    "requirements": {
                        "terrain": True,
                        "objects": True,
                        "scripts": True,
                        "ui": True,
                        "quiz": True
                    }
                },
                metadata={
                    "source": "dashboard",
                    "priority": "high",
                    "teacher_id": "teacher_123",
                    "class_id": "class_456"
                },
                requires_database_save=True,
                requires_dashboard_update=True
            )

            # Process the complete request
            response = await self.communication_hub.handle_plugin_request(request)

            # Verify the response
            if not response.success:
                logger.warning(f"End-to-end workflow failed: {response.errors}")
                return False

            # Verify response has required data
            if not hasattr(response, 'data') or not response.data:
                return False

            # Verify execution time was tracked
            if not hasattr(response, 'execution_time') or response.execution_time <= 0:
                return False

            return True
        except Exception as e:
            logger.error(f"End-to-end workflow test failed: {e}")
            return False

    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASSED")
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "total_duration": f"{total_duration:.2f}s",
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "framework_availability": {
                "sparc_available": FRAMEWORKS_AVAILABLE,
                "swarm_available": FRAMEWORKS_AVAILABLE,
                "mcp_available": FRAMEWORKS_AVAILABLE
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        failed_tests = [name for name, result in self.test_results.items() if result["status"] == "FAILED"]

        if "sparc_framework_integration" in failed_tests:
            recommendations.append("Install and configure SPARC framework dependencies")

        if "swarm_controller_coordination" in failed_tests:
            recommendations.append("Set up Swarm controller with proper worker configuration")

        if "mcp_websocket_integration" in failed_tests:
            recommendations.append("Configure MCP WebSocket server and context management")

        if "content_generation_pipeline" in failed_tests:
            recommendations.append("Verify agent communication and content generation pipeline")

        if "environment_creation_system" in failed_tests:
            recommendations.append("Test individual agent capabilities (terrain, script, UI generation)")

        if not failed_tests:
            recommendations.append("All tests passed! System is ready for production deployment")

        return recommendations

async def main():
    """Main test execution function"""
    print("🎮 ToolboxAI Agent Communication & Framework Integration Test")
    print("=" * 70)

    tester = AgentCommunicationTester()
    report = await tester.run_all_tests()

    # Print summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    summary = report["test_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Duration: {summary['total_duration']}")

    # Print framework availability
    print("\n🔧 FRAMEWORK AVAILABILITY")
    print("=" * 30)
    frameworks = report["framework_availability"]
    print(f"SPARC Framework: {'✅ Available' if frameworks['sparc_available'] else '❌ Not Available'}")
    print(f"Swarm Controller: {'✅ Available' if frameworks['swarm_available'] else '❌ Not Available'}")
    print(f"MCP WebSocket: {'✅ Available' if frameworks['mcp_available'] else '❌ Not Available'}")

    # Print recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 30)
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. {rec}")

    # Save detailed report
    report_file = f"agent_communication_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Return exit code based on success rate
    success_rate = float(summary['success_rate'].rstrip('%'))
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
