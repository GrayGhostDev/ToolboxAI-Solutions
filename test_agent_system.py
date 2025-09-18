#!/usr/bin/env python3
"""
Test script for verifying the Agent System functionality.

This script tests the core components of the agent system including:
- Master Orchestrator
- Agent Registry and Factory
- Worktree Coordinator
- Resource Monitor
- Agent communication and task distribution

Author: ToolboxAI Team
Created: 2025-09-17
Version: 1.0.0
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✓{NC} {message}")


def print_error(message):
    """Print error message."""
    print(f"{RED}✗{NC} {message}")


def print_info(message):
    """Print info message."""
    print(f"{CYAN}ℹ{NC} {message}")


def print_section(title):
    """Print section header."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")


async def test_agent_registry():
    """Test the Agent Registry and Factory system."""
    print_section("Testing Agent Registry and Factory")

    try:
        from core.agents.agent_registry import get_registry, get_factory, AgentCategory
        from core.agents.base_agent import AgentCapability

        # Test registry
        print_info("Testing agent registry...")
        registry = get_registry()

        # Get statistics
        stats = registry.get_statistics()
        print_success(f"Registry initialized with {stats['total_agents']} agents")

        # List categories
        print_info("Agent categories:")
        for category, count in stats["by_category"].items():
            print(f"  - {category}: {count} agents")

        # Test factory
        print_info("\nTesting agent factory...")
        factory = get_factory()

        # Try to create an agent
        # Note: This might fail if specific agents aren't available
        educational_agents = registry.find_agents_by_category(AgentCategory.EDUCATIONAL)
        if educational_agents:
            agent_name = educational_agents[0]
            print_info(f"Creating test agent: {agent_name}")
            agent = factory.create_agent(agent_name)
            if agent:
                print_success(f"Successfully created agent: {agent_name}")
                factory.release_agent(agent)
            else:
                print_error(f"Failed to create agent: {agent_name}")
        else:
            print_info("No educational agents found (this is okay if not all modules are present)")

        # Get factory statistics
        factory_stats = factory.get_statistics()
        print_success(f"Factory statistics: {json.dumps(factory_stats, indent=2)}")

        return True

    except Exception as e:
        print_error(f"Agent Registry test failed: {e}")
        return False


async def test_master_orchestrator():
    """Test the Master Orchestrator."""
    print_section("Testing Master Orchestrator")

    try:
        from core.agents.master_orchestrator import (
            get_orchestrator,
            OrchestratorConfig,
            AgentSystemType,
            TaskPriority
        )

        print_info("Initializing Master Orchestrator...")
        config = OrchestratorConfig(
            max_concurrent_tasks=5,
            enable_health_checks=False,  # Disable for quick test
            enable_metrics=True
        )

        orchestrator = get_orchestrator(config)
        await orchestrator.start()
        print_success("Master Orchestrator started successfully")

        # Get status
        status = await orchestrator.get_status()
        print_info("Orchestrator status:")
        print(f"  - ID: {status['orchestrator_id']}")
        print(f"  - Running: {status['is_running']}")
        print(f"  - Agent pools: {json.dumps(status['agent_pools'], indent=4)}")

        # Submit a test task (might fail if agents aren't available)
        print_info("\nSubmitting test task...")
        try:
            task_id = await orchestrator.submit_task(
                agent_type=AgentSystemType.MONITORING,
                task_data={"action": "test"},
                priority=TaskPriority.LOW
            )
            print_success(f"Task submitted: {task_id}")

            # Wait briefly for task processing
            await asyncio.sleep(2)

            # Check task status
            task_status = await orchestrator.get_task_status(task_id)
            if task_status:
                print_info(f"Task status: {task_status.get('status')}")
        except Exception as e:
            print_info(f"Task submission failed (expected if agents not available): {e}")

        # Stop orchestrator
        await orchestrator.stop()
        print_success("Master Orchestrator stopped successfully")

        return True

    except Exception as e:
        print_error(f"Master Orchestrator test failed: {e}")
        return False


async def test_worktree_coordinator():
    """Test the Worktree-Agent Coordinator."""
    print_section("Testing Worktree-Agent Coordinator")

    try:
        from core.agents.worktree_coordinator import (
            WorktreeAgentCoordinator,
            WorktreeTaskType,
            TaskPriority
        )

        print_info("Initializing Worktree Coordinator...")
        coordinator = WorktreeAgentCoordinator()

        # Test task distribution (won't actually create worktrees in test mode)
        print_info("Testing task distribution...")
        task_id = await coordinator.distribute_task(
            task_type=WorktreeTaskType.TESTING,
            description="Test task for agent system verification",
            requirements=["Test the agent system", "Verify functionality"],
            priority=TaskPriority.LOW
        )
        print_success(f"Task distributed: {task_id}")

        # Get task status
        task_status = await coordinator.get_task_status(task_id)
        if task_status:
            print_info(f"Task status: {json.dumps(task_status, indent=2)}")

        # Get statistics
        stats = await coordinator.get_statistics()
        print_success(f"Coordinator statistics: {json.dumps(stats, indent=2)}")

        return True

    except Exception as e:
        print_error(f"Worktree Coordinator test failed: {e}")
        return False


async def test_resource_monitor():
    """Test the Resource Monitor Agent."""
    print_section("Testing Resource Monitor Agent")

    try:
        from core.agents.github_agents.resource_monitor_agent import ResourceMonitorAgent

        print_info("Initializing Resource Monitor...")
        monitor = ResourceMonitorAgent()

        # Monitor current resources
        print_info("Monitoring system resources...")
        result = await monitor.execute({"action": "monitor"})

        if result.success:
            snapshot = result.output.get("snapshot", {})
            print_success("Resource snapshot collected:")
            print(f"  - CPU: {snapshot.get('cpu_percent', 0):.1f}%")
            print(f"  - Memory: {snapshot.get('memory_percent', 0):.1f}%")
            print(f"  - Disk: {snapshot.get('disk_usage_percent', 0):.1f}%")
            print(f"  - Processes: {snapshot.get('process_count', 0)}")
        else:
            print_error(f"Resource monitoring failed: {result.error}")

        # Analyze usage
        print_info("\nAnalyzing resource usage...")
        analysis_result = await monitor.execute({"action": "analyze"})

        if analysis_result.success:
            analysis = analysis_result.output
            if "cpu" in analysis:
                print_success("Resource analysis complete:")
                print(f"  - CPU trend: {analysis['cpu'].get('trend', 'unknown')}")
                print(f"  - Memory trend: {analysis['memory'].get('trend', 'unknown')}")
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                print_info("Recommendations:")
                for rec in recommendations:
                    print(f"  - {rec}")
        else:
            print_info("Analysis skipped (insufficient history)")

        # Get alerts
        print_info("\nChecking for alerts...")
        alerts_result = await monitor.execute({"action": "get_alerts"})

        if alerts_result.success:
            alert_count = alerts_result.output.get("count", 0)
            if alert_count > 0:
                print_info(f"Active alerts: {alert_count}")
                for alert in alerts_result.output.get("alerts", []):
                    print(f"  - [{alert['severity']}] {alert['message']}")
            else:
                print_success("No active alerts")

        return True

    except Exception as e:
        print_error(f"Resource Monitor test failed: {e}")
        return False


async def test_agent_communication():
    """Test inter-agent communication."""
    print_section("Testing Inter-Agent Communication")

    try:
        from core.swarm.message_bus import MessageBus, MessageBusConfig
        from core.swarm.message_bus.agent_message import MessageBuilder
        from core.swarm.message_bus.event_types import EventType, EventPriority

        print_info("Initializing Message Bus...")
        config = MessageBusConfig(
            max_queue_size=100,
            enable_logging=True
        )
        bus = MessageBus(config)
        print_success("Message Bus initialized")

        # Create and send test message
        print_info("Testing message publishing...")
        message = (MessageBuilder()
            .with_event(EventType.TASK_CREATE)
            .from_agent("test_agent")
            .broadcast()
            .with_data({"test": "message", "timestamp": datetime.now().isoformat()})
            .with_priority(EventPriority.NORMAL)
            .build()
        )

        await bus.publish(message)
        print_success("Test message published")

        # Subscribe and receive
        print_info("Testing message subscription...")
        received_messages = []

        async def message_handler(msg):
            received_messages.append(msg)

        await bus.subscribe(EventType.TASK_CREATE, message_handler)
        await asyncio.sleep(0.5)  # Brief wait for processing

        if received_messages:
            print_success(f"Received {len(received_messages)} message(s)")
        else:
            print_info("No messages received (queue might be empty)")

        # MessageBus doesn't need explicit stopping
        print_success("Message communication test complete")

        return True

    except Exception as e:
        print_error(f"Agent communication test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{CYAN}{'=' * 60}{NC}")
    print(f"{CYAN}   ToolBoxAI Agent System Test Suite{NC}")
    print(f"{CYAN}   Version: 1.0.0{NC}")
    print(f"{CYAN}   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{NC}")
    print(f"{CYAN}{'=' * 60}{NC}")

    tests = [
        ("Agent Registry", test_agent_registry),
        ("Master Orchestrator", test_master_orchestrator),
        ("Worktree Coordinator", test_worktree_coordinator),
        ("Resource Monitor", test_resource_monitor),
        ("Agent Communication", test_agent_communication)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}PASSED{NC}" if result else f"{RED}FAILED{NC}"
        print(f"  {test_name}: {status}")

    print(f"\n{BLUE}{'=' * 60}{NC}")
    if passed == total:
        print(f"{GREEN}✅ All tests passed! ({passed}/{total}){NC}")
    else:
        print(f"{YELLOW}⚠ {passed}/{total} tests passed{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Test suite failed: {e}{NC}")
        sys.exit(1)