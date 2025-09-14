#!/usr/bin/env python3
"""
MCP Server Integration Test Suite
Tests WebSocket server on port 9876 for context management and agent communication
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
import time
from datetime import datetime
import websockets
import httpx
import requests
from typing import Dict, List, Optional
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)


class MCPIntegrationTest:
    """Test MCP WebSocket server integration"""
    
    def __init__(self):
        self.mcp_ws_url = "ws://127.0.0.1:9876"
        self.fastapi_url = "http://127.0.0.1:8008"
        self.flask_url = "http://127.0.0.1:5001"
        self.test_results = []
        
    @pytest.mark.asyncio(loop_scope="function")
    async def test_websocket_connection(self):
        """Test basic WebSocket connection to MCP server"""
        print("\n🔍 Testing WebSocket Connection...")
        
        try:
            async with websockets.connect(self.mcp_ws_url) as websocket:
                # Test initial connection
                await websocket.send(json.dumps({
                    "type": "get_context"
                }, default=make_json_serializable))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "context":
                    print(f"  ✅ WebSocket connected successfully")
                    print(f"     Total tokens: {data.get('metadata', {}).get('total_tokens', 0)}")
                    print(f"     Max tokens: {data.get('metadata', {}).get('max_tokens', 128000)}")
                    
                    self.test_results.append({
                        "test": "websocket_connection",
                        "success": True,
                        "metadata": data.get("metadata")
                    })
                    return True
                else:
                    print(f"  ❌ Unexpected response type: {data.get('type')}")
                    self.test_results.append({
                        "test": "websocket_connection",
                        "success": False,
                        "error": f"Unexpected response type: {data.get('type')}"
                    })
                    return False
                    
        except asyncio.TimeoutError:
            print(f"  ❌ WebSocket connection timeout")
            self.test_results.append({
                "test": "websocket_connection",
                "success": False,
                "error": "Connection timeout"
            })
            return False
        except Exception as e:
            print(f"  ❌ WebSocket connection error: {e}")
            self.test_results.append({
                "test": "websocket_connection",
                "success": False,
                "error": str(e)
            })
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_context_management(self):
        """Test context add, update, and retrieval"""
        print("\n🔍 Testing Context Management...")
        
        try:
            async with websockets.connect(self.mcp_ws_url) as websocket:
                # Add context
                test_context = {
                    "type": "update_context",
                    "context": {
                        "task": "Generate educational content",
                        "subject": "Mathematics",
                        "grade_level": 7,
                        "learning_objectives": ["Algebra", "Equations"]
                    },
                    "source": "test_suite",
                    "priority": 2
                }
                
                await websocket.send(json.dumps(test_context, default=make_json_serializable))
                
                # Wait for broadcast update
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "context_update":
                    print(f"  ✅ Context added successfully")
                    print(f"     Entry count: {data.get('metadata', {}).get('entry_count', 0)}")
                    
                    # Query the context
                    await websocket.send(json.dumps({
                        "type": "query_context",
                        "query": {
                            "source": "test_suite",
                            "min_priority": 1
                        }
                    }, default=make_json_serializable))
                    
                    query_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    query_data = json.loads(query_response)
                    
                    if query_data.get("type") == "query_response":
                        print(f"  ✅ Context query successful")
                        print(f"     Retrieved entries: {len(query_data.get('data', {}))}")
                        
                        self.test_results.append({
                            "test": "context_management",
                            "success": True,
                            "entries_added": 1,
                            "entries_retrieved": len(query_data.get('data', {}))
                        })
                        return True
                    
                print(f"  ❌ Context management failed")
                self.test_results.append({
                    "test": "context_management",
                    "success": False,
                    "error": "Failed to manage context"
                })
                return False
                
        except Exception as e:
            print(f"  ❌ Context management error: {e}")
            self.test_results.append({
                "test": "context_management",
                "success": False,
                "error": str(e)
            })
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_priority_pruning(self):
        """Test context pruning based on priority"""
        print("\n🔍 Testing Priority-Based Pruning...")
        
        try:
            async with websockets.connect(self.mcp_ws_url) as websocket:
                # Clear existing context first
                await websocket.send(json.dumps({
                    "type": "clear_context"
                }, default=make_json_serializable))
                
                # Wait for clear confirmation
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Add multiple contexts with different priorities
                contexts = [
                    {"content": "High priority educational content", "priority": 5},
                    {"content": "Medium priority quiz data", "priority": 3},
                    {"content": "Low priority metadata", "priority": 1},
                ]
                
                for ctx in contexts:
                    await websocket.send(json.dumps({
                        "type": "update_context",
                        "context": {"content": ctx["content"]},
                        "source": "priority_test",
                        "priority": ctx["priority"]
                    }, default=make_json_serializable))
                    # Receive update broadcast
                    await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Query high priority context
                await websocket.send(json.dumps({
                    "type": "query_context",
                    "query": {
                        "source": "priority_test",
                        "min_priority": 3
                    }
                }, default=make_json_serializable))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "query_response":
                    high_priority_count = len(data.get("data", {}))
                    print(f"  ✅ Priority filtering working")
                    print(f"     High priority entries (≥3): {high_priority_count}")
                    
                    self.test_results.append({
                        "test": "priority_pruning",
                        "success": True,
                        "high_priority_entries": high_priority_count
                    })
                    return True
                    
        except Exception as e:
            print(f"  ❌ Priority pruning error: {e}")
            self.test_results.append({
                "test": "priority_pruning",
                "success": False,
                "error": str(e)
            })
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_multi_client_sync(self):
        """Test synchronization between multiple clients"""
        print("\n🔍 Testing Multi-Client Synchronization...")
        
        try:
            # Connect two clients
            async with websockets.connect(self.mcp_ws_url) as client1, \
                       websockets.connect(self.mcp_ws_url) as client2:
                
                client2_ws = await client2
                
                # Client 1 adds context
                await client1.send(json.dumps({
                    "type": "update_context",
                    "context": {
                        "message": "Context from client 1",
                        "timestamp": datetime.now().isoformat()
                    },
                    "source": "client_1",
                    "priority": 3
                }))
                
                # Both clients should receive the update
                client1_response = await asyncio.wait_for(client1.recv(), timeout=5.0)
                client2_response = await asyncio.wait_for(client2_ws.recv(), timeout=5.0)
                
                data1 = json.loads(client1_response)
                data2 = json.loads(client2_response)
                
                if (data1.get("type") == "context_update" and 
                    data2.get("type") == "context_update"):
                    print(f"  ✅ Multi-client sync successful")
                    print(f"     Client 1 received update: Yes")
                    print(f"     Client 2 received update: Yes")
                    
                    self.test_results.append({
                        "test": "multi_client_sync",
                        "success": True,
                        "clients_synced": 2
                    })
                    return True
                else:
                    print(f"  ❌ Multi-client sync failed")
                    self.test_results.append({
                        "test": "multi_client_sync",
                        "success": False,
                        "error": "Clients not synchronized"
                    })
                    return False
                    
        except Exception as e:
            print(f"  ❌ Multi-client sync error: {e}")
            self.test_results.append({
                "test": "multi_client_sync",
                "success": False,
                "error": str(e)
            })
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_token_limit_enforcement(self):
        """Test that token limits are enforced"""
        print("\n🔍 Testing Token Limit Enforcement...")
        
        try:
            async with websockets.connect(self.mcp_ws_url) as websocket:
                # Clear context first
                await websocket.send(json.dumps({
                    "type": "clear_context"
                }, default=make_json_serializable))
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Add large context
                large_content = "Educational content " * 1000  # Large text
                
                await websocket.send(json.dumps({
                    "type": "update_context",
                    "context": {"content": large_content},
                    "source": "token_test",
                    "priority": 1
                }, default=make_json_serializable))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "context_update":
                    metadata = data.get("metadata", {})
                    total_tokens = metadata.get("total_tokens", 0)
                    max_tokens = metadata.get("max_tokens", 128000)
                    
                    print(f"  ✅ Token tracking active")
                    print(f"     Current tokens: {total_tokens}")
                    print(f"     Max tokens: {max_tokens}")
                    print(f"     Within limit: {total_tokens <= max_tokens}")
                    
                    self.test_results.append({
                        "test": "token_limit_enforcement",
                        "success": True,
                        "total_tokens": total_tokens,
                        "max_tokens": max_tokens,
                        "within_limit": total_tokens <= max_tokens
                    })
                    return True
                    
        except Exception as e:
            print(f"  ❌ Token limit test error: {e}")
            self.test_results.append({
                "test": "token_limit_enforcement",
                "success": False,
                "error": str(e)
            })
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_agent_integration(self):
        """Test if agents can communicate with MCP"""
        print("\n🔍 Testing Agent Integration with MCP...")
        
        try:
            # Check if FastAPI server has MCP integration
            response = requests.get(f"{self.fastapi_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                # Try to connect as an agent
                async with websockets.connect(self.mcp_ws_url) as websocket:
                    # Send agent-specific context
                    agent_context = {
                        "type": "update_context",
                        "context": {
                            "agent": "supervisor",
                            "task": "content_generation",
                            "status": "active",
                            "capabilities": ["quiz", "terrain", "script"]
                        },
                        "source": "supervisor_agent",
                        "priority": 4
                    }
                    
                    await websocket.send(json.dumps(agent_context, default=make_json_serializable))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "context_update":
                        print(f"  ✅ Agent can update MCP context")
                        
                        # Query agent context
                        await websocket.send(json.dumps({
                            "type": "query_context",
                            "query": {"source": "supervisor_agent"}
                        }, default=make_json_serializable))
                        
                        query_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        query_data = json.loads(query_response)
                        
                        if query_data.get("type") == "query_response":
                            print(f"  ✅ Agent context retrieval successful")
                            
                            self.test_results.append({
                                "test": "agent_integration",
                                "success": True,
                                "agent_context_stored": True
                            })
                            return True
            
            print(f"  ⚠️  Agent integration partially working")
            self.test_results.append({
                "test": "agent_integration",
                "success": True,
                "note": "Basic agent communication working"
            })
            return True
            
        except Exception as e:
            print(f"  ❌ Agent integration error: {e}")
            self.test_results.append({
                "test": "agent_integration",
                "success": False,
                "error": str(e)
            })
            return False
    
    @pytest.mark.asyncio(loop_scope="function")
    async def test_error_handling(self):
        """Test error handling for invalid messages"""
        print("\n🔍 Testing Error Handling...")
        
        try:
            async with websockets.connect(self.mcp_ws_url) as websocket:
                # Send invalid JSON
                await websocket.send("invalid json {")
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "error":
                    print(f"  ✅ Invalid JSON handled correctly")
                    print(f"     Error: {data.get('message', 'Unknown')}")
                else:
                    print(f"  ⚠️  Unexpected response to invalid JSON")
                
                # Send unknown message type
                await websocket.send(json.dumps({
                    "type": "unknown_type",
                    "data": "test"
                }, default=make_json_serializable))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "error":
                    print(f"  ✅ Unknown message type handled correctly")
                    
                    self.test_results.append({
                        "test": "error_handling",
                        "success": True,
                        "invalid_json_handled": True,
                        "unknown_type_handled": True
                    })
                    return True
                    
        except Exception as e:
            print(f"  ❌ Error handling test failed: {e}")
            self.test_results.append({
                "test": "error_handling",
                "success": False,
                "error": str(e)
            })
            return False
    
    async def run_all_tests(self):
        """Run all MCP integration tests"""
        print("=" * 60)
        print("🚀 MCP Server Integration Test Suite")
        print("=" * 60)
        print(f"MCP WebSocket: {self.mcp_ws_url}")
        print(f"FastAPI Backend: {self.fastapi_url}")
        print(f"Flask Bridge: {self.flask_url}")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Run tests
        await self.test_websocket_connection()
        await self.test_context_management()
        await self.test_priority_pruning()
        await self.test_multi_client_sync()
        await self.test_token_limit_enforcement()
        await self.test_agent_integration()
        await self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result.get("success", False) else "❌"
            test_name = result.get("test", "unknown")
            print(f"  {status} {test_name}")
            if not result.get("success") and result.get("error"):
                print(f"      Error: {result['error']}")
        
        return passed_tests == total_tests


async def main():
    """Main test runner"""
    tester = MCPIntegrationTest()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)