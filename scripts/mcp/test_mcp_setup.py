#!/usr/bin/env python3
"""
Test script to verify MCP setup
"""

import sys
import os
import asyncio
import websockets
import json
from pathlib import Path

# Add project paths (repo root is three levels up: scripts/mcp/ -> project root)
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "shared"))


def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")

    try:
        from core.mcp.server import MCPServer

        print("✅ MCP Server imported successfully")
    except ImportError as e:
        print(f"❌ MCP Server import failed: {e}")
        return False

    try:
        from core.agents.orchestrator import Orchestrator

        print("✅ Agent Orchestrator imported successfully")
    except ImportError as e:
        print(f"❌ Agent Orchestrator import failed: {e}")
        return False

    try:
        from core.sparc.state_manager import StateManager

        print("✅ SPARC Manager imported successfully")
    except ImportError as e:
        print(f"❌ SPARC Manager import failed: {e}")
        return False

    return True


    async def test_mcp_server():
    """Test MCP server functionality"""
    print("🔍 Testing MCP server...")

    try:
        from core.mcp.server import MCPServer

        server = MCPServer(port=9877, max_tokens=1000)  # Use different port for testing
        print("✅ MCP Server created successfully")
        return True
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Running MCP setup tests...")
    print("=" * 40)

    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return 1

    # Test MCP server
    if not asyncio.run(test_mcp_server()):
        print("❌ MCP server test failed")
        return 1

    print("=" * 40)
    print("✅ All tests passed! MCP setup is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
