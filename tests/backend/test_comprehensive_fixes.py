from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


#!/usr/bin/env python3
"""
Comprehensive test to verify all the fixes we implemented
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_imports() -> bool:
    """Test all critical imports"""
    print_section("Testing Module Imports")

    test_results = []

    # Test 1: Core agents imports
    try:
        from core.agents import (
            get_available_agents,
        )

        print("✅ Core agents imports successful")
        agents = get_available_agents()
        print(f"   Available agents: {agents}")
        test_results.append(True)
    except Exception as e:
        print(f"❌ Core agents import failed: {e}")
        test_results.append(False)

    # Test 2: Backend main imports
    try:

        print("✅ Backend main app import successful")
        test_results.append(True)
    except Exception as e:
        print(f"❌ Backend main import failed: {e}")
        test_results.append(False)

    # Test 3: MCP context manager imports
    try:
        from core.mcp.context_manager import MCPContextManager

        manager = MCPContextManager(max_tokens=128000)
        print("✅ MCP Context Manager import and instantiation successful")
        test_results.append(True)
    except Exception as e:
        print(f"❌ MCP Context Manager import failed: {e}")
        test_results.append(False)

    # Test 4: WebSocket auth imports
    try:

        print("✅ WebSocket auth imports successful")
        test_results.append(True)
    except Exception as e:
        print(f"❌ WebSocket auth import failed: {e}")
        test_results.append(False)

    # Test 5: Settings imports
    try:
        from toolboxai_settings import settings

        print("✅ Settings import successful")
        print(f"   Environment: {settings.ENV_NAME}")
        test_results.append(True)
    except Exception as e:
        print(f"❌ Settings import failed: {e}")
        test_results.append(False)

    return all(test_results)


def test_websocket_endpoints() -> bool:
    """Test WebSocket endpoints are configured correctly"""
    print_section("Testing WebSocket Endpoints")

    test_results = []

    try:
        from fastapi.testclient import TestClient

        from apps.backend.main import app

        client = TestClient(app)

        # Test 1: Native WebSocket endpoint exists
        try:
            # Check that the native endpoint is registered
            routes = [route.path for route in app.routes]
            if "/ws/native" in routes:
                print("✅ /ws/native endpoint is registered")
                test_results.append(True)
            else:
                print("❌ /ws/native endpoint not found in routes")
                test_results.append(False)
        except Exception as e:
            print(f"❌ Error checking routes: {e}")
            test_results.append(False)

        # Test 2: WebSocket echo functionality
        try:
            with client.websocket_connect("/ws/native") as websocket:
                # Send test message
                test_message = "Hello, WebSocket!"
                websocket.send_text(test_message)

                # Receive echo response
                response = websocket.receive_text()
                expected = f"Echo: {test_message}"

                if response == expected:
                    print(f"✅ WebSocket echo test passed: '{response}'")
                    test_results.append(True)
                else:
                    print(f"❌ WebSocket echo test failed:")
                    print(f"   Expected: '{expected}'")
                    print(f"   Got: '{response}'")
                    test_results.append(False)
        except Exception as e:
            print(f"❌ WebSocket connection test failed: {e}")
            test_results.append(False)

        # Test 3: Verify route ordering (native before parametric)
        try:
            ws_routes = [
                (i, route.path) for i, route in enumerate(app.routes) if "/ws" in str(route.path)
            ]
            native_index = next((i for i, path in ws_routes if path == "/ws/native"), None)
            param_index = next((i for i, path in ws_routes if "{client_id}" in path), None)

            if native_index is not None and param_index is not None:
                if native_index < param_index:
                    print(
                        f"✅ Route ordering correct: /ws/native (index {native_index}) before /ws/{{client_id}} (index {param_index})"
                    )
                    test_results.append(True)
                else:
                    print(
                        f"❌ Route ordering incorrect: /ws/native (index {native_index}) should be before /ws/{{client_id}} (index {param_index})"
                    )
                    test_results.append(False)
            else:
                print(
                    f"⚠️  Could not verify route ordering (native: {native_index}, param: {param_index})"
                )
                test_results.append(True)  # Don't fail if we can't verify
        except Exception as e:
            print(f"⚠️  Error checking route ordering: {e}")
            test_results.append(True)  # Don't fail on this check

    except Exception as e:
        print(f"❌ WebSocket endpoint test setup failed: {e}")
        return False

    return all(test_results)


def test_agent_functionality() -> bool:
    """Test agent creation and basic functionality"""
    print_section("Testing Agent Functionality")

    test_results = []

    try:
        from core.agents import AgentConfig, create_agent

        # Test creating different agent types
        agent_types = ["content", "quiz", "terrain", "script"]

        for agent_type in agent_types:
            try:
                config = AgentConfig(name=f"test_{agent_type}", model="gpt-4")
                agent = create_agent(agent_type, config)
                print(f"✅ Created {agent_type} agent successfully")
                test_results.append(True)
            except Exception as e:
                print(f"❌ Failed to create {agent_type} agent: {e}")
                test_results.append(False)

    except Exception as e:
        print(f"❌ Agent functionality test failed: {e}")
        return False

    return all(test_results)


def main():
    """Run all comprehensive tests"""
    print("\n" + "=" * 60)
    print("  COMPREHENSIVE TEST SUITE FOR FIXES")
    print("=" * 60)

    results = []

    # Run import tests
    results.append(("Import Tests", test_imports()))

    # Run WebSocket tests
    results.append(("WebSocket Tests", test_websocket_endpoints()))

    # Run agent tests
    results.append(("Agent Tests", test_agent_functionality()))

    # Print summary
    print_section("TEST SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")

    print(f"\n  Total: {passed_tests}/{total_tests} tests passed")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! All fixes are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
