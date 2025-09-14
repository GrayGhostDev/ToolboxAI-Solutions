#!/usr/bin/env python3
"""
Core Agent Communication Test

This test validates the basic agent communication without complex dependencies.
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
sys.path.append('/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoreAgentCommunicationTester:
    """Test suite for core agent communication"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now(timezone.utc)
        
        # Initialize agents directly
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agents with error handling"""
        try:
            from core.agents.base_agent import BaseAgent, TaskResult
            from core.agents.supervisor import SupervisorAgent
            from core.agents.content_agent import ContentAgent
            from core.agents.quiz_agent import QuizAgent
            from core.agents.terrain_agent import TerrainAgent
            from core.agents.script_agent import ScriptAgent
            from core.agents.review_agent import ReviewAgent
            
            self.agents = {
                "supervisor": SupervisorAgent(),
                "content": ContentAgent(),
                "quiz": QuizAgent(),
                "terrain": TerrainAgent(),
                "script": ScriptAgent(),
                "review": ReviewAgent()
            }
            
            logger.info("✅ All agents initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            self.agents = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all core communication tests"""
        logger.info("🚀 Starting Core Agent Communication Tests")
        
        tests = [
            ("agent_initialization", self.test_agent_initialization),
            ("agent_execution", self.test_agent_execution),
            ("agent_collaboration", self.test_agent_collaboration),
            ("task_result_structure", self.test_task_result_structure),
            ("error_handling", self.test_error_handling),
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
            if not self.agents:
                return False
            
            # Test each agent has required attributes
            for agent_name, agent in self.agents.items():
                if not hasattr(agent, 'name') or not agent.name:
                    logger.error(f"Agent {agent_name} missing name")
                    return False
                
                if not hasattr(agent, 'execute'):
                    logger.error(f"Agent {agent_name} missing execute method")
                    return False
                
                if not callable(getattr(agent, 'execute')):
                    logger.error(f"Agent {agent_name} execute is not callable")
                    return False
            
            logger.info(f"✅ All {len(self.agents)} agents initialized correctly")
            return True
        except Exception as e:
            logger.error(f"Agent initialization test failed: {e}")
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_execution(self) -> bool:
        """Test individual agent execution"""
        try:
            if not self.agents:
                return False
            
            # Test content agent execution
            content_agent = self.agents.get("content")
            if not content_agent:
                return False
            
            task = "Create a simple educational content about basic math"
            context = {
                "subject": "mathematics",
                "grade_level": 3,
                "learning_objectives": ["Count to 10", "Basic addition"]
            }
            
            result = await content_agent.execute(task, context)
            
            if not result:
                logger.error("Content agent execution returned None")
                return False
            
            # Check if result has expected structure
            if not hasattr(result, 'success'):
                logger.error("Result missing success attribute")
                return False
            
            if not hasattr(result, 'output'):
                logger.error("Result missing output attribute")
                return False
            
            logger.info(f"✅ Content agent execution successful: {result.success}")
            return True
        except Exception as e:
            logger.error(f"Agent execution test failed: {e}")
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_collaboration(self) -> bool:
        """Test agent-to-agent collaboration"""
        try:
            if not self.agents:
                return False
            
            content_agent = self.agents.get("content")
            quiz_agent = self.agents.get("quiz")
            
            if not content_agent or not quiz_agent:
                return False
            
            # Test collaboration
            task = "Create educational content and quiz about animals"
            context = {
                "subject": "science",
                "grade_level": 2,
                "learning_objectives": ["Identify common animals", "Understand animal habitats"]
            }
            
            result = await content_agent.collaborate(quiz_agent, task, context)
            
            if not result:
                logger.error("Collaboration returned None")
                return False
            
            if not hasattr(result, 'success'):
                logger.error("Collaboration result missing success attribute")
                return False
            
            if not hasattr(result, 'metadata'):
                logger.error("Collaboration result missing metadata attribute")
                return False
            
            # Check collaboration metadata
            if not result.metadata.get("collaboration"):
                logger.error("Collaboration metadata missing collaboration flag")
                return False
            
            logger.info(f"✅ Agent collaboration successful: {result.success}")
            return True
        except Exception as e:
            logger.error(f"Agent collaboration test failed: {e}")
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_task_result_structure(self) -> bool:
        """Test TaskResult structure and methods"""
        try:
            from core.agents.base_agent import TaskResult
            
            # Create a test result
            result = TaskResult(
                success=True,
                output="Test output",
                metadata={"test": True, "timestamp": datetime.now().isoformat()}
            )
            
            # Test required attributes
            if not hasattr(result, 'success'):
                return False
            
            if not hasattr(result, 'output'):
                return False
            
            if not hasattr(result, 'metadata'):
                return False
            
            # Test to_dict method if it exists
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
                if not isinstance(result_dict, dict):
                    return False
            
            logger.info("✅ TaskResult structure is correct")
            return True
        except Exception as e:
            logger.error(f"TaskResult structure test failed: {e}")
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_error_handling(self) -> bool:
        """Test error handling in agents"""
        try:
            if not self.agents:
                return False
            
            content_agent = self.agents.get("content")
            if not content_agent:
                return False
            
            # Test with invalid input
            try:
                result = await content_agent.execute(None, None)
                # Should handle gracefully, not crash
                if result is None:
                    return False
                
                # Result should indicate failure
                if result.success:
                    logger.warning("Agent should have failed with invalid input")
                    return False
                
                logger.info("✅ Error handling works correctly")
                return True
            except Exception as e:
                # If it raises an exception, that's also acceptable error handling
                logger.info(f"✅ Error handling works (exception caught): {e}")
                return True
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate test report"""
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
            "agent_status": {
                "agents_initialized": len(self.agents),
                "agent_names": list(self.agents.keys()) if self.agents else []
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [name for name, result in self.test_results.items() if result["status"] == "FAILED"]
        
        if "agent_initialization" in failed_tests:
            recommendations.append("Fix agent initialization - check imports and dependencies")
        
        if "agent_execution" in failed_tests:
            recommendations.append("Fix agent execution - check agent implementation")
        
        if "agent_collaboration" in failed_tests:
            recommendations.append("Fix agent collaboration - check collaboration methods")
        
        if "task_result_structure" in failed_tests:
            recommendations.append("Fix TaskResult structure - check base_agent implementation")
        
        if "error_handling" in failed_tests:
            recommendations.append("Improve error handling in agents")
        
        if not failed_tests:
            recommendations.append("All core tests passed! Ready for advanced testing")
        
        return recommendations

async def main():
    """Main test execution function"""
    print("🎮 ToolboxAI Core Agent Communication Test")
    print("=" * 50)
    
    tester = CoreAgentCommunicationTester()
    report = await tester.run_all_tests()
    
    # Print summary
    print("\n📊 TEST SUMMARY")
    print("=" * 20)
    summary = report["test_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Duration: {summary['total_duration']}")
    
    # Print agent status
    print("\n🤖 AGENT STATUS")
    print("=" * 20)
    agent_status = report["agent_status"]
    print(f"Agents Initialized: {agent_status['agents_initialized']}")
    print(f"Agent Names: {', '.join(agent_status['agent_names'])}")
    
    # Print recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 20)
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. {rec}")
    
    # Save detailed report
    report_file = f"core_agent_communication_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on success rate
    success_rate = float(summary['success_rate'].rstrip('%'))
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

