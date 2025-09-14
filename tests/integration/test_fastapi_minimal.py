#!/usr/bin/env python3
"""
Minimal FastAPI Test Script - Isolate Server Startup Issues
This script creates a minimal FastAPI server to identify startup problems.
"""

import asyncio
import os
import sys
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

# Configure logging to see all debug information
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test imports one by one to identify issues
try:
    import uvicorn
    logger.info("✅ uvicorn imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import uvicorn: {e}")
    sys.exit(1)

try:
    from fastapi import FastAPI, WebSocket
    logger.info("✅ FastAPI imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import FastAPI: {e}")
    sys.exit(1)

try:
    import redis
    logger.info("✅ redis imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import redis: {e}")

try:
    import psycopg2
    logger.info("✅ psycopg2 imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ psycopg2 not available: {e}")

# Test Redis connection
def test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        logger.info("✅ Redis connection successful")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        return False

# Test Database connection
def test_database_connection() -> bool:
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="toolboxai",
            user="postgres"
        )
        conn.close()
        logger.info("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL connection failed: {e}")
        return False

# Create minimal FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan manager"""
    logger.info("🚀 Starting minimal FastAPI server...")
    
    # Test connections
    redis_ok = test_redis_connection()
    db_ok = test_database_connection()
    
    app.state.redis_available = redis_ok
    app.state.db_available = db_ok
    app.state.start_time = time.time()
    
    logger.info(f"Service Status: Redis={redis_ok}, Database={db_ok}")
    
    yield
    
    logger.info("👋 Shutting down minimal FastAPI server...")

# Create the app
app = FastAPI(
    title="Minimal FastAPI Test",
    description="Minimal server to test startup issues",
    version="1.0.0",
    lifespan=lifespan
)

# Add minimal endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "running",
        "message": "Minimal FastAPI server is running",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app.state.start_time
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "redis": app.state.redis_available,
        "database": app.state.db_available
    }

@app.get("/test-endpoint")
@pytest.mark.asyncio(loop_scope="function")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test endpoint working", "data": [1, 2, 3]}

@app.post("/generate_content")
async def generate_content(request: dict):
    """Generate content endpoint"""
    return {
        "success": True,
        "content": {
            "subject": request.get("subject", "Math"),
            "grade_level": request.get("grade_level", 5),
            "scripts": ["-- Generated Lua script"],
            "world_id": f"world-{int(time.time())}"
        },
        "message": "Content generated successfully"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint with optional authentication"""
    # Check for auth token in query params or headers
    token = websocket.query_params.get("token")
    
    # For development, allow both authenticated and anonymous connections
    if token:
        logger.info(f"WebSocket connection with token: {token[:10]}...")
    else:
        logger.info("WebSocket connection without authentication (dev mode)")
    
    await websocket.accept()
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "authenticated": bool(token)
        })
        
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "auth":
                # Handle authentication request
                auth_token = data.get("token")
                if auth_token:
                    await websocket.send_json({
                        "type": "auth_response",
                        "status": "authenticated",
                        "message": "Authentication successful"
                    })
                else:
                    await websocket.send_json({
                        "type": "auth_response",
                        "status": "unauthenticated",
                        "message": "No token provided"
                    })
            else:
                await websocket.send_json({"echo": data})
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Function to run the server
def run_server(host: str = "127.0.0.1", port: int = 8008):
    """Run the minimal FastAPI server"""
    logger.info(f"Starting server on {host}:{port}")
    
    try:
        # Try different configurations to see what works
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="debug",
            access_log=True,
            use_colors=True,
            reload=False  # Disable reload for testing
        )
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        
        # Try alternative configuration
        logger.info("Trying alternative configuration...")
        try:
            uvicorn.run(
                "test_fastapi_minimal:app",
                host=host,
                port=port,
                log_level="debug",
                reload=False
            )
        except Exception as e2:
            logger.error(f"❌ Alternative configuration also failed: {e2}")

# Async version for testing
async def run_server_async(host: str = "127.0.0.1", port: int = 8008):
    """Run the server asynchronously"""
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="debug",
        access_log=True
    )
    server = uvicorn.Server(config)
    await server.serve()

# Test script
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("MINIMAL FASTAPI SERVER TEST")
    logger.info("=" * 50)
    
    # Test basic functionality
    logger.info("\n1. Testing basic imports and connections...")
    
    # Check if port is available
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8008))
    if result == 0:
        logger.warning("⚠️ Port 8008 is already in use!")
        logger.info("Trying port 8009 instead...")
        port = 8009
    else:
        logger.info("✅ Port 8008 is available")
        port = 8008
    sock.close()
    
    # Run the server
    logger.info(f"\n2. Starting minimal server on port {port}...")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        run_server(port=port)
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        
        # Try async version
        logger.info("\nTrying async version...")
        try:
            asyncio.run(run_server_async(port=port))
        except Exception as e2:
            logger.error(f"❌ Async version also failed: {e2}")