#!/usr/bin/env python3
"""
WebSocket Authentication Usage Examples

This file demonstrates how to use the new WebSocket authentication system
in the ToolBoxAI project for different types of clients and use cases.
"""

import asyncio
import json
import websockets
from datetime import datetime, timezone
from apps.backend.auth import JWTManager, User
from apps.backend.config import settings


class WebSocketAuthClient:
    """Example WebSocket client with authentication"""
    
    def __init__(self, username: str, role: str = "student"):
        self.username = username
        self.role = role
        self.user_id = f"{role}_{username}"
        self.token = None
        self.websocket = None
        self.authenticated = False
    
    def create_token(self) -> str:
        """Create JWT token for authentication"""
        token_data = {
            "sub": self.user_id,
            "username": self.username,
            "email": f"{self.username}@example.com",
            "role": self.role
        }
        self.token = JWTManager.create_access_token(token_data)
        return self.token
    
    async def connect_to_mcp_server(self, host: str = "localhost", port: int = 9876):
        """Connect to MCP server with authentication"""
        if not self.token:
            self.create_token()
        
        # Connect with token in query parameter
        uri = f"ws://{host}:{port}?token={self.token}"
        
        try:
            print(f"[{self.username}] Connecting to MCP server at {uri}")
            self.websocket = await websockets.connect(uri)
            print(f"[{self.username}] Connected successfully!")
            return True
        except Exception as e:
            print(f"[{self.username}] Connection failed: {e}")
            return False
    
    async def connect_to_fastapi_server(self, host: str = "localhost", port: int = 8008):
        """Connect to FastAPI WebSocket endpoint with authentication"""
        if not self.token:
            self.create_token()
        
        # Connect with token in query parameter
        uri = f"ws://{host}:{port}/ws?token={self.token}"
        
        try:
            print(f"[{self.username}] Connecting to FastAPI server at {uri}")
            self.websocket = await websockets.connect(uri)
            print(f"[{self.username}] Connected successfully!")
            return True
        except Exception as e:
            print(f"[{self.username}] Connection failed: {e}")
            return False
    
    async def send_message(self, message_type: str, data: dict = None):
        """Send authenticated message"""
        if not self.websocket:
            print(f"[{self.username}] Not connected!")
            return False
        
        message = {
            "type": message_type,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client": self.username
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"[{self.username}] Sent: {message_type}")
            return True
        except Exception as e:
            print(f"[{self.username}] Send failed: {e}")
            return False
    
    async def receive_messages(self):
        """Receive and process messages"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get("type", "unknown")
                
                if message_type == "auth_success":
                    self.authenticated = True
                    print(f"[{self.username}] ✅ Authentication successful!")
                    print(f"   User: {data.get('user', {}).get('username', 'unknown')}")
                    print(f"   Role: {data.get('user', {}).get('role', 'unknown')}")
                    
                elif message_type == "auth_error":
                    print(f"[{self.username}] ❌ Authentication failed: {data.get('message', 'Unknown error')}")
                    
                elif message_type == "token_refreshed":
                    print(f"[{self.username}] 🔄 Token refreshed successfully")
                    
                elif message_type == "context_update":
                    print(f"[{self.username}] 📝 Context updated: {data.get('metadata', {}).get('entry_count', 0)} entries")
                    
                elif message_type == "error":
                    print(f"[{self.username}] ⚠️ Error: {data.get('message', 'Unknown error')}")
                    
                else:
                    print(f"[{self.username}] 📨 Received: {message_type}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.username}] Connection closed")
        except Exception as e:
            print(f"[{self.username}] Receive error: {e}")
    
    async def refresh_token(self):
        """Refresh authentication token"""
        # Create new token
        new_token = self.create_token()
        
        # Send refresh request
        await self.send_message("refresh_token", {"token": new_token})
    
    async def disconnect(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()
            print(f"[{self.username}] Disconnected")


async def example_mcp_authentication():
    """Example: Authenticate with MCP server"""
    print("\n=== MCP Server Authentication Example ===")
    
    # Create a student client
    student = WebSocketAuthClient("alice", "student")
    
    # Connect and authenticate
    if await student.connect_to_mcp_server():
        # Start message handling
        receive_task = asyncio.create_task(student.receive_messages())
        
        # Wait a moment for authentication
        await asyncio.sleep(1)
        
        # Send some context updates
        await student.send_message("update_context", {
            "context": {"lesson": "Math", "topic": "Algebra"},
            "source": f"student_{student.username}",
            "priority": 1
        })
        
        # Wait and then disconnect
        await asyncio.sleep(2)
        receive_task.cancel()
        await student.disconnect()


async def example_fastapi_authentication():
    """Example: Authenticate with FastAPI WebSocket"""
    print("\n=== FastAPI Server Authentication Example ===")
    
    # Create a teacher client
    teacher = WebSocketAuthClient("john", "teacher")
    
    # Connect and authenticate
    if await teacher.connect_to_fastapi_server():
        # Start message handling
        receive_task = asyncio.create_task(teacher.receive_messages())
        
        # Wait a moment for authentication
        await asyncio.sleep(1)
        
        # Send various messages
        await teacher.send_message("ping")
        await teacher.send_message("subscribe", {"channels": ["teacher_updates", "content_updates"]})
        await teacher.send_message("content_request", {
            "subject": "Science", 
            "grade_level": 8,
            "request_id": "req_123"
        })
        
        # Wait and then disconnect
        await asyncio.sleep(3)
        receive_task.cancel()
        await teacher.disconnect()


async def example_token_refresh():
    """Example: Token refresh workflow"""
    print("\n=== Token Refresh Example ===")
    
    admin = WebSocketAuthClient("admin", "admin")
    
    if await admin.connect_to_mcp_server():
        receive_task = asyncio.create_task(admin.receive_messages())
        
        # Wait for initial authentication
        await asyncio.sleep(1)
        
        print(f"[{admin.username}] Refreshing token...")
        await admin.refresh_token()
        
        # Wait to see refresh response
        await asyncio.sleep(2)
        
        receive_task.cancel()
        await admin.disconnect()


async def example_multiple_clients():
    """Example: Multiple authenticated clients"""
    print("\n=== Multiple Clients Example ===")
    
    clients = [
        WebSocketAuthClient("student1", "student"),
        WebSocketAuthClient("student2", "student"), 
        WebSocketAuthClient("teacher1", "teacher"),
    ]
    
    # Connect all clients
    connections = []
    for client in clients:
        if await client.connect_to_mcp_server():
            connections.append(client)
    
    # Start message handling for all
    tasks = []
    for client in connections:
        task = asyncio.create_task(client.receive_messages())
        tasks.append(task)
    
    # Wait for authentication
    await asyncio.sleep(1)
    
    # Each client sends different types of messages
    await connections[0].send_message("update_context", {"lesson": "Math", "progress": 0.5})
    await connections[1].send_message("update_context", {"lesson": "Science", "progress": 0.3})
    await connections[2].send_message("query_context", {"source": "student1"})
    
    # Wait and cleanup
    await asyncio.sleep(3)
    
    for task in tasks:
        task.cancel()
    
    for client in connections:
        await client.disconnect()


async def example_authentication_errors():
    """Example: Authentication error scenarios"""
    print("\n=== Authentication Errors Example ===")
    
    # Test with invalid token
    print("Testing invalid token...")
    try:
        uri = "ws://localhost:9876?token=invalid.token.here"
        websocket = await websockets.connect(uri)
        await websocket.close()
    except Exception as e:
        print(f"❌ Invalid token correctly rejected: {e}")
    
    # Test with no token
    print("Testing no token...")
    try:
        uri = "ws://localhost:9876"
        websocket = await websockets.connect(uri)
        await websocket.close()
    except Exception as e:
        print(f"❌ No token correctly rejected: {e}")
    
    print("✅ Authentication errors handled correctly")


async def main():
    """Run all examples"""
    print("=== WebSocket Authentication Usage Examples ===")
    print("These examples demonstrate the new authentication system.")
    print("Note: Make sure the MCP server and/or FastAPI server are running first!")
    
    try:
        # Basic examples
        await example_mcp_authentication()
        await example_fastapi_authentication()
        await example_token_refresh()
        await example_multiple_clients()
        await example_authentication_errors()
        
        print("\n=== All Examples Completed ===")
        
    except KeyboardInterrupt:
        print("\n=== Examples Interrupted ===")
    except Exception as e:
        print(f"\n=== Example Error: {e} ===")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())