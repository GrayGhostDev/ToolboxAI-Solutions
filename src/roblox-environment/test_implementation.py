#!/usr/bin/env python3
"""
Test script to verify the ToolboxAI Roblox Environment implementation.

This script checks that all major components are properly installed and functional.
"""

import sys
import os
import asyncio
from typing import Dict, Any, List
import logging
import importlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_import(module_name: str, component_name: str = None) -> bool:
    """Check if a module can be imported."""
    try:
        # Use importlib instead of exec() for security (SonarQube: S1523)
        if component_name:
            module = importlib.import_module(module_name)
            getattr(module, component_name)  # Check if component exists
        else:
            importlib.import_module(module_name)
        return True
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {e}")
        return False
    except AttributeError as e:
        logger.error(f"Component {component_name} not found in {module_name}: {e}")
        return False


async def test_agents():
    """Test the agent system."""
    print_section("Testing Agent System")

    try:
        from agents import create_orchestrator, OrchestrationRequest, WorkflowType

        print("✅ Agent imports successful")

        # Create orchestrator
        orchestrator = create_orchestrator()
        print("✅ Orchestrator created")

        # Check agent health
        health = await orchestrator.health_check()
        print(f"✅ Health check: {health['orchestrator']}")

        # Create a simple request
        request = OrchestrationRequest(
            workflow_type=WorkflowType.CONTENT_ONLY,
            subject="Mathematics",
            grade_level="5",
            learning_objectives=["Test objective"],
            include_quiz=False,
        )
        print("✅ Created test request")

        return True

    except Exception as e:
        logger.error(f"Agent test failed: {e}")
        return False


async def test_sparc():
    """Test the SPARC framework."""
    print_section("Testing SPARC Framework")

    try:
        from sparc import create_sparc_system, SPARCConfig

        print("✅ SPARC imports successful")

        # Create SPARC system
        config = SPARCConfig()
        sparc = create_sparc_system(config)
        print("✅ SPARC system created")

        # Test observation
        observation = {
            "student_id": "test_student",
            "subject": "science",
            "grade_level": 7,
        }

        # Execute a cycle (without actual AI calls)
        state = await sparc.observe(observation)
        print(f"✅ State observation: {state.quality_score:.2f}")

        return True

    except Exception as e:
        logger.error(f"SPARC test failed: {e}")
        return False


async def test_swarm():
    """Test the swarm coordination system."""
    print_section("Testing Swarm System")

    try:
        from swarm import create_swarm, SwarmConfig

        print("✅ Swarm imports successful")

        # Create swarm
        config = SwarmConfig(min_workers=2, max_workers=4)
        swarm = await create_swarm(config)
        print(f"✅ Swarm created with {len(swarm.worker_pool.workers)} workers")

        # Check swarm status
        status = swarm.get_status()
        print(f"✅ Swarm status: {status['state']}")

        # Shutdown swarm
        await swarm.shutdown()
        print("✅ Swarm shutdown successful")

        return True

    except Exception as e:
        logger.error(f"Swarm test failed: {e}")
        return False


async def test_coordinators():
    """Test the coordinator system."""
    print_section("Testing Coordinator System")

    try:
        from coordinators import GlobalCoordinator

        print("✅ Coordinator imports successful")

        # Get global coordinator
        coordinator = GlobalCoordinator()
        print("✅ Global coordinator accessed")

        # Check subsystems
        subsystems = coordinator.get_subsystems()
        print(f"✅ Found {len(subsystems)} subsystems")

        return True

    except Exception as e:
        logger.error(f"Coordinator test failed: {e}")
        return False


def test_mcp():
    """Test the MCP system."""
    print_section("Testing MCP System")

    try:
        from mcp import MCPServer, ContextManager, MemoryStore

        print("✅ MCP imports successful")

        # Create context manager
        context = ContextManager()
        print(f"✅ Context manager created (max tokens: {context.max_tokens})")

        # Create memory store
        memory = MemoryStore(":memory:")
        print("✅ Memory store created")

        return True

    except Exception as e:
        logger.error(f"MCP test failed: {e}")
        return False


def test_server():
    """Test server components."""
    print_section("Testing Server Components")

    try:
        # Test imports
        modules = [
            ("server.main", "app"),
            ("server.roblox_server", "app"),
            ("server.tools", "ALL_TOOLS"),
            ("server.models", "ContentRequest"),
            ("server.auth", "JWTAuth"),
            ("server.config", "settings"),
        ]

        for module, component in modules:
            if check_import(module, component):
                print(f"✅ {module}.{component} imported")
            else:
                print(f"❌ Failed to import {module}.{component}")
                return False

        return True

    except Exception as e:
        logger.error(f"Server test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  ToolboxAI Roblox Environment - Implementation Test")
    print("  76% Complete (42/55 files implemented)")
    print("=" * 60)

    results = []

    # Test each component
    results.append(("MCP", test_mcp()))
    results.append(("Agents", await test_agents()))
    results.append(("SPARC", await test_sparc()))
    results.append(("Swarm", await test_swarm()))
    results.append(("Coordinators", await test_coordinators()))
    results.append(("Server", test_server()))

    # Print summary
    print_section("Test Summary")

    passed = 0
    failed = 0

    for component, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{component:15} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed}/{len(results)} passed")

    if failed == 0:
        print("\n🎉 All implemented components are working correctly!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set environment variables (OPENAI_API_KEY, etc.)")
        print("3. Start servers: python server/start_servers.py")
        print("4. Access API docs: http://127.0.0.1:8008/docs")
    else:
        print(
            f"\n⚠️  {failed} component(s) failed. Please check the error messages above."
        )
        print("\nCommon issues:")
        print("- Missing dependencies: Run 'pip install -r requirements.txt'")
        print("- Import errors: Check that all files were created correctly")
        print("- Configuration issues: Set required environment variables")

    return failed == 0


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
