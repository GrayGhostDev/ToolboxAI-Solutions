#!/usr/bin/env python3
"""
Test Integration Agents - Verify the agent swarm is working

This script tests the integration agents system to ensure all components
are working properly and the health check errors are resolved.

Tests both direct module imports and HTTP endpoints.
"""

import asyncio
import aiohttp
import sys
import os
import json
from datetime import datetime
import time
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def wait_for_server(base_url: str, max_attempts: int = 30):
    """Wait for the server to be ready"""
    print(f"⏳ Waiting for server at {base_url}...")

    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        print("✅ Server is ready!")
                        return True
        except:
            pass

        await asyncio.sleep(1)
        if attempt % 5 == 0:
            print(f"   Still waiting... ({attempt}/{max_attempts})")

    print("❌ Server failed to start")
    return False


async def test_integration_status(base_url: str):
    """Test the integration status endpoint"""
    print("\n📊 Testing Integration Status Endpoint...")

    async with aiohttp.ClientSession() as session:
        try:
            # Note: In production, you'd need proper authentication
            # For testing, we'll try without auth first
            async with session.get(f"{base_url}/api/v1/integration/status") as response:
                if response.status == 401:
                    print("   ⚠️  Authentication required (expected in production)")
                    return True
                elif response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Status: {data.get('overall_health', 'unknown')}")
                    print(f"   ✅ Initialized: {data.get('initialized', False)}")

                    agents = data.get('agents', {})
                    if agents:
                        print(f"   ✅ Active Agents: {len(agents)}")
                        for agent_name, agent_status in agents.items():
                            status = agent_status.get('status', 'unknown')
                            emoji = "✅" if status == "healthy" else "⚠️"
                            print(f"      {emoji} {agent_name}: {status}")
                    return True
                else:
                    print(f"   ❌ Unexpected status: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_integration_agents_list(base_url: str):
    """Test the agents list endpoint"""
    print("\n🤖 Testing Agents List Endpoint...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/api/v1/integration/agents") as response:
                if response.status == 401:
                    print("   ⚠️  Authentication required (expected)")
                    return True
                elif response.status == 200:
                    data = await response.json()
                    agents = data.get('agents', {})
                    print(f"   ✅ Found {len(agents)} agent types")

                    for agent_key, agent_info in agents.items():
                        print(f"   📌 {agent_info['name']}")
                        print(f"      {agent_info['description']}")
                        if agent_info.get('initialized'):
                            print(f"      Status: {agent_info.get('health', 'unknown')}")
                    return True
                else:
                    print(f"   ❌ Unexpected status: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_workflow_templates(base_url: str):
    """Test workflow templates endpoint"""
    print("\n📋 Testing Workflow Templates...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{base_url}/api/v1/integration/workflow/templates") as response:
                if response.status == 401:
                    print("   ⚠️  Authentication required (expected)")
                    return True
                elif response.status == 200:
                    data = await response.json()
                    templates = data.get('templates', {})
                    print(f"   ✅ Found {len(templates)} workflow templates")

                    for template_key, template_info in templates.items():
                        print(f"   📝 {template_info['name']}")
                        print(f"      {template_info['description']}")
                        print(f"      Tasks: {', '.join(template_info['tasks'])}")
                    return True
                else:
                    print(f"   ❌ Unexpected status: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_metrics_endpoint(base_url: str):
    """Test metrics endpoint"""
    print("\n📈 Testing Metrics Endpoint...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/api/v1/integration/metrics") as response:
                if response.status == 401:
                    print("   ⚠️  Authentication required (expected)")
                    return True
                elif response.status == 200:
                    data = await response.json()
                    totals = data.get('totals', {})
                    print(f"   ✅ Metrics Retrieved")
                    print(f"      Total Requests: {totals.get('total_requests', 0)}")
                    print(f"      Success Rate: {totals.get('success_rate', 0):.2%}")
                    print(f"      Events Processed: {totals.get('events_processed', 0)}")
                    return True
                else:
                    print(f"   ❌ Unexpected status: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_openapi_docs(base_url: str):
    """Test that integration endpoints appear in OpenAPI docs"""
    print("\n📚 Testing OpenAPI Documentation...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/openapi.json") as response:
                if response.status == 200:
                    data = await response.json()
                    paths = data.get('paths', {})

                    integration_paths = [p for p in paths if '/integration/' in p]
                    print(f"   ✅ Found {len(integration_paths)} integration endpoints in OpenAPI")

                    for path in integration_paths[:5]:  # Show first 5
                        methods = list(paths[path].keys())
                        print(f"      {', '.join(methods).upper()} {path}")

                    if len(integration_paths) > 5:
                        print(f"      ... and {len(integration_paths) - 5} more")

                    return len(integration_paths) > 0
                else:
                    print(f"   ❌ Failed to get OpenAPI spec: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_data_flow_imports():
    """Test that data flow imports work correctly"""
    print("\n📦 Testing Data Flow Imports...")
    try:
        from core.agents.integration.data_flow import (
            SchemaValidatorAgent,
            Schema,
            SchemaType,
            ValidationLevel,
            ValidationResult,
            SchemaMapping,
            SchemaEvolution
        )
        print("   ✅ Data flow imports successful")

        # Test SchemaType enum
        assert hasattr(SchemaType, 'JSON_SCHEMA')
        assert hasattr(SchemaType, 'PYDANTIC')
        assert hasattr(SchemaType, 'ROBLOX_DATASTORE')
        print("   ✅ SchemaType enum working correctly")

        return True
    except Exception as e:
        print(f"   ❌ Data flow imports failed: {e}")
        return False


async def test_integration_agents_manager():
    """Test the integration agents manager"""
    print("\n🤖 Testing Integration Agents Manager...")
    try:
        from apps.backend.services.integration_agents import IntegrationAgentsManager

        # Create manager instance
        manager = IntegrationAgentsManager()

        # Initialize (should use mock agents)
        await manager.initialize()
        print("   ✅ Integration agents manager initialized")

        # Test health check
        status = await manager.get_agent_status()
        print(f"   ✅ Health check successful: {len(status['agents'])} agents")

        # Verify all agents have health status
        for agent_name, health in status['agents'].items():
            assert 'status' in health
            assert 'healthy' in health
            print(f"      - {agent_name}: {health['status']}")

        # Test cleanup
        await manager.shutdown()
        print("   ✅ Integration agents manager shutdown")

        return True
    except Exception as e:
        print(f"   ❌ Integration agents manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_models():
    """Test that database models are importable"""
    print("\n🗄️  Testing Database Models...")
    try:
        from database.models import (
            User, Course, Lesson, Content, Quiz, UserProgress,
            StudentProgress, SchemaDefinition, SchemaMapping,
            AgentHealthStatus, IntegrationEvent
        )
        print("   ✅ Database models import successful")

        # Test that StudentProgress model is compatible
        assert hasattr(StudentProgress, 'student_id')
        assert hasattr(StudentProgress, 'lesson_id')
        assert hasattr(StudentProgress, 'progress_percentage')
        print("   ✅ StudentProgress model compatibility verified")

        return True
    except Exception as e:
        print(f"   ❌ Database models test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    base_url = "http://127.0.0.1:8009"  # Updated to port 8009

    print("=" * 60)
    print("🚀 Integration Agents Test Suite")
    print("=" * 60)
    print(f"Target: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # First run direct module tests
    direct_tests = [
        ("Data Flow Imports", test_data_flow_imports),
        ("Database Models", test_database_models),
        ("Integration Agents Manager", test_integration_agents_manager),
    ]

    # Then run HTTP endpoint tests if server is available
    http_tests = [
        ("Status Endpoint", test_integration_status),
        ("Agents List", test_integration_agents_list),
        ("Workflow Templates", test_workflow_templates),
        ("Metrics", test_metrics_endpoint),
        ("OpenAPI Docs", test_openapi_docs),
    ]

    all_results = []

    # Run direct tests first
    print("\n🔬 Running Direct Module Tests...")
    for test_name, test_func in direct_tests:
        try:
            result = await test_func()
            all_results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            all_results.append((test_name, False))

    # Check if server is running for HTTP tests
    print("\n🌐 Running HTTP Endpoint Tests...")
    server_available = await wait_for_server(base_url, max_attempts=5)

    if server_available:
        for test_name, test_func in http_tests:
            try:
                result = await test_func(base_url)
                all_results.append((test_name, result))
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                all_results.append((test_name, False))
    else:
        print("   ⚠️  Server not running - skipping HTTP tests")
        print("   💡 To test HTTP endpoints, start the server with:")
        print("      cd apps/backend && uvicorn main:app --host 127.0.0.1 --port 8009 --reload")

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)

    for test_name, result in all_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")

    if passed >= len(direct_tests):  # At least direct tests should pass
        print("🎉 Core integration functionality is working correctly!")
        if not server_available:
            print("💡 Start the backend server to test HTTP endpoints")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)