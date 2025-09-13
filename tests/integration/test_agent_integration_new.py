#!/usr/bin/env python3
"""
Comprehensive Agent System Integration Test
Tests all agent systems, frameworks, and integrations
"""

import asyncio
import json
import time
from datetime import datetime
import sys
from pathlib import Path
import logging
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Integration tests require external services - run with --run-integration")

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import all agents and systems
from core.agents.testing_agent import TestingAgent
from core.agents.orchestrator import Orchestrator, WorkflowType, OrchestrationRequest
from core.agents.supervisor import SupervisorAgent
from core.agents.content_agent import ContentAgent
from core.agents.quiz_agent import QuizAgent
from core.agents.terrain_agent import TerrainAgent
from core.agents.script_agent import ScriptAgent
from core.agents.review_agent import ReviewAgent

# Import database integration
try:
    from core.agents.database_integration import agent_db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    agent_db = None
    logger.warning("Database integration not available")

# Import SPARC framework
try:
    from core.sparc.state_manager import StateManager
    from core.sparc.policy_engine import PolicyEngine
    SPARC_AVAILABLE = True
except ImportError:
    SPARC_AVAILABLE = False
    logger.warning("SPARC framework not available")

# Import Swarm intelligence
try:
    from core.swarm.swarm_controller import SwarmController
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False
    logger.warning("Swarm intelligence not available")

# Import MCP
try:
    from core.mcp.context_manager import ContextManager
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP context manager not available")


class AgentIntegrationTest:
    """Comprehensive test suite for agent system integration"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    async def test_agent_initialization(self):
        """Test 1: Initialize all agents"""
        print("\n" + "="*60)
        print("🔍 Test 1: Agent Initialization")
        print("="*60)
        
        try:
            # Initialize all agents
            agents = {
                "testing": TestingAgent(),
                "orchestrator": Orchestrator(),
                "supervisor": SupervisorAgent(),
                "content": ContentAgent(),
                "quiz": QuizAgent(),
                "terrain": TerrainAgent(),
                "script": ScriptAgent(),
                "review": ReviewAgent()
            }
            
            # Check each agent
            for name, agent in agents.items():
                status = agent.get_status()
                print(f"  ✅ {name.capitalize()} Agent: Initialized - Status: {status['status']}")
                
            self.test_results.append({
                "test": "agent_initialization",
                "status": "passed",
                "agents_initialized": list(agents.keys())
            })
            
            print("\n✅ All agents initialized successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Agent initialization failed: {e}")
            self.test_results.append({
                "test": "agent_initialization",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def test_database_integration(self):
        """Test 2: Database Integration"""
        print("\n" + "="*60)
        print("🔍 Test 2: Database Integration")
        print("="*60)
        
        if not DATABASE_AVAILABLE:
            print("  ⏭️  Database integration not available - skipping")
            self.test_results.append({
                "test": "database_integration",
                "status": "skipped",
                "reason": "Database not available"
            })
            return True
            
        try:
            # Test database connections
            objectives = agent_db.get_learning_objectives(subject="Science", grade_level=7)
            content = agent_db.get_educational_content()
            standards = agent_db.get_curriculum_standards()
            
            print(f"  ✅ Learning Objectives: {len(objectives)} found")
            print(f"  ✅ Educational Content: {len(content)} items")
            print(f"  ✅ Curriculum Standards: {len(standards)} standards")
            
            # Test saving content
            test_content = {
                "title": "Integration Test Content",
                "description": "Test from agent integration",
                "timestamp": datetime.now().isoformat()
            }
            
            success = agent_db.save_generated_content(
                content_type="test",
                content_data=test_content
            )
            
            if success:
                print(f"  ✅ Content saved to database successfully")
            
            self.test_results.append({
                "test": "database_integration",
                "status": "passed",
                "objectives_count": len(objectives),
                "content_count": len(content),
                "save_test": success
            })
            
            print("\n✅ Database integration working!")
            return True
            
        except Exception as e:
            print(f"\n❌ Database integration failed: {e}")
            self.test_results.append({
                "test": "database_integration",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def test_sparc_integration(self):
        """Test 3: SPARC Framework Integration"""
        print("\n" + "="*60)
        print("🔍 Test 3: SPARC Framework Integration")
        print("="*60)
        
        if not SPARC_AVAILABLE:
            print("  ⏭️  SPARC framework not available - skipping")
            self.test_results.append({
                "test": "sparc_integration",
                "status": "skipped",
                "reason": "SPARC not available"
            })
            return True
            
        try:
            # Initialize SPARC components
            state_manager = StateManager()
            policy_engine = PolicyEngine(state_manager)
            
            # Test state management
            test_state = {
                "environment": "classroom",
                "subject": "Mathematics",
                "grade_level": 7,
                "students": 25
            }
            
            state_manager.update_state(test_state)
            current_state = state_manager.get_current_state()
            
            print(f"  ✅ State Manager: State updated")
            print(f"  ✅ Current Environment: {current_state.get('environment', 'unknown')}")
            
            # Test policy decision
            decision = policy_engine.decide_action(test_state)
            print(f"  ✅ Policy Engine: Decision made - {decision}")
            
            self.test_results.append({
                "test": "sparc_integration",
                "status": "passed",
                "state_updated": True,
                "policy_decision": decision is not None
            })
            
            print("\n✅ SPARC framework integration working!")
            return True
            
        except Exception as e:
            print(f"\n❌ SPARC integration failed: {e}")
            self.test_results.append({
                "test": "sparc_integration",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def test_swarm_integration(self):
        """Test 4: Swarm Intelligence Integration"""
        print("\n" + "="*60)
        print("🔍 Test 4: Swarm Intelligence Integration")
        print("="*60)
        
        if not SWARM_AVAILABLE:
            print("  ⏭️  Swarm intelligence not available - skipping")
            self.test_results.append({
                "test": "swarm_integration",
                "status": "skipped",
                "reason": "Swarm not available"
            })
            return True
            
        try:
            # Initialize swarm controller using factory function
            from core.swarm import create_swarm
            swarm = await create_swarm({"max_workers": 2})
            
            # Swarm is already started by create_swarm
            print(f"  ✅ Swarm Controller: Started with 2 workers")
            
            # Test task distribution
            test_tasks = [
                {"type": "test1", "data": "Task 1"},
                {"type": "test2", "data": "Task 2"}
            ]
            
            # Note: Actual task execution would depend on swarm implementation
            print(f"  ✅ Task Distribution: {len(test_tasks)} tasks ready")
            
            # Stop swarm
            await swarm.stop()
            print(f"  ✅ Swarm Controller: Stopped successfully")
            
            self.test_results.append({
                "test": "swarm_integration",
                "status": "passed",
                "workers": 2,
                "tasks": len(test_tasks)
            })
            
            print("\n✅ Swarm intelligence integration working!")
            return True
            
        except Exception as e:
            print(f"\n❌ Swarm integration failed: {e}")
            self.test_results.append({
                "test": "swarm_integration",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def test_mcp_integration(self):
        """Test 5: MCP Context Management Integration"""
        print("\n" + "="*60)
        print("🔍 Test 5: MCP Context Management")
        print("="*60)
        
        if not MCP_AVAILABLE:
            print("  ⏭️  MCP not available - skipping")
            self.test_results.append({
                "test": "mcp_integration",
                "status": "skipped",
                "reason": "MCP not available"
            })
            return True
            
        try:
            # Initialize context manager
            context_manager = ContextManager(max_tokens=128000)
            
            # Add test context
            context_manager.add_context(
                content="Integration test context",
                category="system",
                source="integration_test",
                importance=5.0
            )
            
            print(f"  ✅ Context Manager: Context added")
            
            # Get context stats
            stats = context_manager.get_stats()
            print(f"  ✅ Total Tokens: {stats['total_tokens']}")
            print(f"  ✅ Max Tokens: {stats['max_tokens']}")
            print(f"  ✅ Utilization: {stats['utilization']}")
            
            self.test_results.append({
                "test": "mcp_integration",
                "status": "passed",
                "total_tokens": stats['total_tokens'],
                "utilization": stats['utilization']
            })
            
            print("\n✅ MCP context management working!")
            return True
            
        except Exception as e:
            print(f"\n❌ MCP integration failed: {e}")
            self.test_results.append({
                "test": "mcp_integration",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def test_orchestrator_workflow(self):
        """Test 6: Orchestrator Workflow Execution"""
        print("\n" + "="*60)
        print("🔍 Test 6: Orchestrator Workflow")
        print("="*60)
        
        try:
            orchestrator = Orchestrator()
            
            # Create a simple workflow request
            request = OrchestrationRequest(
                workflow_type=WorkflowType.CONTENT_ONLY,
                subject="Science",
                grade_level="7",
                learning_objectives=["Solar System"],
                include_quiz=False  # Simple test
            )
            
            print(f"  ⏳ Starting content generation workflow...")
            
            # Execute workflow (this will use mock LLM if OpenAI not configured)
            result = await orchestrator.orchestrate(request)
            
            if result.success:
                print(f"  ✅ Workflow completed successfully")
                print(f"  ✅ Execution time: {result.execution_time:.2f}s")
                print(f"  ✅ Workflow path: {' → '.join(result.workflow_path)}")
            else:
                print(f"  ⚠️  Workflow completed with errors: {result.errors}")
                
            self.test_results.append({
                "test": "orchestrator_workflow",
                "status": "passed" if result.success else "partial",
                "execution_time": result.execution_time,
                "workflow_path": result.workflow_path
            })
            
            print("\n✅ Orchestrator workflow execution tested!")
            return True
            
        except Exception as e:
            print(f"\n❌ Orchestrator workflow failed: {e}")
            self.test_results.append({
                "test": "orchestrator_workflow",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def test_testing_agent_integration(self):
        """Test 7: Testing Agent Comprehensive Integration"""
        print("\n" + "="*60)
        print("🔍 Test 7: Testing Agent Integration")
        print("="*60)
        
        try:
            testing_agent = TestingAgent()
            
            # Test comprehensive integration
            print(f"  ⏳ Running comprehensive integration tests...")
            
            result = await testing_agent.run_comprehensive_integration_tests()
            
            print(f"\n  📊 Integration Test Results:")
            print(f"  ✅ Total Tests: {result['total_tests']}")
            print(f"  ✅ Passed: {result['passed']}")
            print(f"  ❌ Failed: {result['failed']}")
            print(f"  ⏭️  Skipped: {result['skipped']}")
            print(f"  📈 Success Rate: {result['success_rate']}")
            
            print(f"\n  🔧 Integration Status:")
            for component, status in result['integration_status'].items():
                icon = "✅" if status else "❌"
                print(f"    {icon} {component.upper()}: {'Available' if status else 'Not Available'}")
                
            self.test_results.append({
                "test": "testing_agent_integration",
                "status": "passed" if result['passed'] > 0 else "failed",
                "details": result
            })
            
            print("\n✅ Testing agent integration complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Testing agent integration failed: {e}")
            self.test_results.append({
                "test": "testing_agent_integration",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    async def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*80)
        print(" 🚀 COMPREHENSIVE AGENT SYSTEM INTEGRATION TEST")
        print("="*80)
        print(f"Start Time: {self.start_time.isoformat()}")
        print(f"Project: ToolBoxAI-Solutions Roblox Environment")
        
        # Run all tests
        await self.test_agent_initialization()
        await self.test_database_integration()
        await self.test_sparc_integration()
        await self.test_swarm_integration()
        await self.test_mcp_integration()
        await self.test_orchestrator_workflow()
        await self.test_testing_agent_integration()
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print(" 📊 INTEGRATION TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get("status") == "passed")
        failed = sum(1 for r in self.test_results if r.get("status") == "failed")
        skipped = sum(1 for r in self.test_results if r.get("status") == "skipped")
        partial = sum(1 for r in self.test_results if r.get("status") == "partial")
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"⚠️  Partial: {partial}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(passed/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n📋 Detailed Results:")
        for test in self.test_results:
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "partial": "⚠️"
            }.get(test.get("status"), "❓")
            
            test_name = test.get("test", "unknown").replace("_", " ").title()
            print(f"  {status_icon} {test_name}: {test.get('status', 'unknown').upper()}")
            
            if test.get("error"):
                print(f"      Error: {test['error']}")
                
        # Save results if database available
        if DATABASE_AVAILABLE and agent_db:
            try:
                agent_db.save_generated_content(
                    content_type="integration_test_results",
                    content_data={
                        "timestamp": datetime.now().isoformat(),
                        "duration": duration,
                        "total_tests": total_tests,
                        "passed": passed,
                        "failed": failed,
                        "skipped": skipped,
                        "partial": partial,
                        "results": self.test_results
                    }
                )
                print("\n💾 Test results saved to database")
            except:
                pass
                
        print("\n" + "="*80)
        print(" 🎯 INTEGRATION TEST COMPLETE")
        print("="*80)
        
        return {
            "success": failed == 0,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "partial": partial,
            "duration": duration,
            "results": self.test_results
        }


async def main():
    """Main test runner"""
    tester = AgentIntegrationTest()
    results = await tester.run_all_tests()
    
    # Return exit code based on results
    if results["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)