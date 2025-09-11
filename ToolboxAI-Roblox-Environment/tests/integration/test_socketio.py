#!/usr/bin/env python3
"""Test Socket.IO connection to the server with authentication"""

import asyncio
import socketio
import sys
import os

# Create a Socket.IO client
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("🔌 Connected to server!")

@sio.event
async def connected(data):
    print(f"📨 Received connected event: {data}")

@sio.event
async def disconnect():
    print("🔌 Disconnected from server!")

@sio.event
async def connect_error(data):
    print(f"❌ Connection error: {data}")

@sio.event  
async def auth_failed(data):
    print(f"🔐 Auth failed: {data}")

@sio.event
async def auth_success(data):
    print(f"✅ Auth success: {data}")

@sio.event
async def error(data):
    print(f"❌ Socket error: {data}")

@sio.event
async def pong(data):
    print(f"🏓 Received pong: {data}")

async def test_with_token(token):
    """Test connection with authentication token"""
    try:
        print(f"🔄 Attempting to connect with token: {token[:20]}...")
        await sio.connect('http://localhost:8008', 
                          socketio_path='/socket.io/',
                          transports=['websocket', 'polling'],
                          auth={'token': token},
                          headers={'Authorization': f'Bearer {token}'})
        print("✅ Connection established, waiting for events...")
        await asyncio.sleep(3)
        
        # Test ping
        await sio.emit('ping')
        print("📤 Sent ping")
        await asyncio.sleep(1)
        
        await sio.disconnect()
        print("🔌 Disconnected gracefully")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_without_token():
    """Test connection without authentication token"""
    try:
        print("🔄 Attempting to connect without token...")
        await sio.connect('http://localhost:8008', 
                          socketio_path='/socket.io/',
                          transports=['websocket', 'polling'])
        print("✅ Connection established (no auth)")
        await asyncio.sleep(2)
        await sio.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    # Test token (you should replace this with a real JWT token)
    test_token = sys.argv[1] if len(sys.argv) > 1 else None
    
    if test_token:
        print("🧪 Testing with provided token...")
        await test_with_token(test_token)
    else:
        print("🧪 Testing without authentication...")
        await test_without_token()
        
        print("\n" + "="*50)
        print("💡 To test with authentication, run:")
        print("python test_socketio.py YOUR_JWT_TOKEN")
        print("💡 Get a token by logging in at the dashboard")

if __name__ == '__main__':
    asyncio.run(main())