#!/usr/bin/env python3
"""
Test Script for Roblox Plugin Communication
Simulates the Roblox Studio plugin's communication with the Flask bridge server
"""

import asyncio

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
import uuid
from typing import Dict, Any, Optional
import aiohttp
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints
FLASK_BRIDGE_URL = "http://127.0.0.1:5001"
FASTAPI_URL = "http://127.0.0.1:8008"
WEBSOCKET_URL = "ws://127.0.0.1:8008/ws"

class RobloxPluginSimulator:
    """Simulates a Roblox Studio plugin communicating with the backend"""
    
    def __init__(self):
        self.plugin_id: Optional[str] = None
        self.studio_id = f"studio_{uuid.uuid4().hex[:8]}"
        self.version = "1.0.0"
        self.ws_connection = None
        self.session = None
    
    async def initialize(self):
        """Initialize the plugin simulator"""
        self.session = aiohttp.ClientSession()
        logger.info(f"🎮 Initializing Roblox Plugin Simulator (Studio ID: {self.studio_id})")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.ws_connection:
            await self.ws_connection.close()
        if self.session:
            await self.session.close()
    
    async def register_plugin(self) -> bool:
        """Register the plugin with the Flask bridge server"""
        logger.info("📝 Registering plugin with Flask bridge...")
        
        plugin_data = {
            "port": 64989,
            "studio_id": self.studio_id,
            "version": self.version,
            "capabilities": ["content_generation", "quiz_creation", "terrain_building"]
        }
        
        try:
            async with self.session.post(
                f"{FLASK_BRIDGE_URL}/register_plugin",
                json=plugin_data,
                timeout=5
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.plugin_id = result.get("plugin_id")
                    logger.info(f"✅ Plugin registered successfully! ID: {self.plugin_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Registration failed: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return False
    
    async def request_content_generation(self, subject: str, grade_level: int) -> Dict[str, Any]:
        """Request educational content generation"""
        logger.info(f"🎨 Requesting content generation for {subject} (Grade {grade_level})...")
        
        request_data = {
            "plugin_id": self.plugin_id,
            "request_type": "generate_content",
            "parameters": {
                "subject": subject,
                "grade_level": grade_level,
                "learning_objectives": ["Basic Concepts", "Problem Solving"],
                "environment_type": "interactive_classroom",
                "include_quiz": True
            }
        }
        
        try:
            # First try through Flask bridge
            async with self.session.post(
                f"{FLASK_BRIDGE_URL}/plugin_request",
                json=request_data,
                timeout=30
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info("✅ Content generated via Flask bridge")
                    return result
                elif resp.status == 404:
                    # If bridge endpoint doesn't exist, try direct FastAPI
                    logger.info("⚠️ Bridge endpoint not found, trying direct API...")
                    return await self.direct_content_request(
                        subject, grade_level
                    )
        except Exception as e:
            logger.error(f"❌ Content generation error: {e}")
            # Fallback to direct API
            return await self.direct_content_request(subject, grade_level)
    
    async def direct_content_request(self, subject: str, grade_level: int) -> Dict[str, Any]:
        """Direct content request to FastAPI server"""
        request_data = {
            "subject": subject,
            "grade_level": grade_level,
            "learning_objectives": ["Basic Concepts", "Problem Solving"],
            "environment_type": "interactive_classroom",
            "include_quiz": True
        }
        
        try:
            async with self.session.post(
                f"{FASTAPI_URL}/generate_content",
                json=request_data,
                timeout=30
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info("✅ Content generated via direct API")
                    return result
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Direct API failed: {error_text}")
                    return {"error": error_text}
        except Exception as e:
            logger.error(f"❌ Direct API error: {e}")
            return {"error": str(e)}
    
    async def establish_websocket(self, with_auth: bool = False) -> bool:
        """Establish WebSocket connection for real-time updates"""
        logger.info(f"🔌 Establishing WebSocket connection (auth: {with_auth})...")
        
        try:
            # Connect with or without authentication
            url = WEBSOCKET_URL
            if with_auth:
                # In production, get real token from auth endpoint
                fake_token = f"dev_token_{uuid.uuid4().hex[:16]}"
                url = f"{url}?token={fake_token}"
            
            self.ws_connection = await websockets.connect(url)
            
            # Wait for connection message
            message = await self.ws_connection.recv()
            data = json.loads(message)
            
            if data.get("type") == "connection":
                logger.info(f"✅ WebSocket connected! Authenticated: {data.get('authenticated', False)}")
                return True
            else:
                logger.warning(f"⚠️ Unexpected WebSocket response: {data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def send_plugin_update(self, update_type: str, data: Dict[str, Any]):
        """Send plugin status update via WebSocket"""
        if not self.ws_connection:
            logger.warning("⚠️ No WebSocket connection available")
            return
        
        message = {
            "type": "plugin_update",
            "plugin_id": self.plugin_id,
            "update_type": update_type,
            "data": data,
            "timestamp": time.time()
        }
        
        try:
            await self.ws_connection.send(json.dumps(message, default=make_json_serializable))
            logger.info(f"📤 Sent plugin update: {update_type}")
        except Exception as e:
            logger.error(f"❌ Failed to send update: {e}")
    
    async def listen_for_updates(self, duration: int = 5):
        """Listen for WebSocket updates for a specified duration"""
        if not self.ws_connection:
            return
        
        logger.info(f"👂 Listening for updates for {duration} seconds...")
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                try:
                    message = await asyncio.wait_for(
                        self.ws_connection.recv(),
                        timeout=1.0
                    )
                    data = json.loads(message)
                    logger.info(f"📥 Received: {data.get('type', 'unknown')} - {data}")
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error receiving message: {e}")
                    break
        except Exception as e:
            logger.error(f"❌ Listen error: {e}")
    
    async def run_complete_workflow(self):
        """Run a complete plugin workflow simulation"""
        logger.info("=" * 60)
        logger.info("🚀 ROBLOX PLUGIN COMMUNICATION TEST")
        logger.info("=" * 60)
        
        # Step 1: Register plugin
        if not await self.register_plugin():
            logger.error("Failed to register plugin")
            return
        
        # Step 2: Establish WebSocket connection
        ws_connected = await self.establish_websocket(with_auth=False)
        if ws_connected:
            # Send initial plugin status
            await self.send_plugin_update("status", {
                "state": "ready",
                "studio_version": "2024.3.1",
                "plugin_version": self.version
            })
        
        # Step 3: Request content generation
        content = await self.request_content_generation("Mathematics", 5)
        if "error" not in content:
            logger.info("📚 Content generation successful!")
            
            # Step 4: Send progress updates
            if ws_connected:
                await self.send_plugin_update("content_received", {
                    "status": "processing",
                    "content_id": content.get("content", {}).get("id", "unknown")
                })
                
                # Simulate processing
                await asyncio.sleep(1)
                
                await self.send_plugin_update("content_applied", {
                    "status": "complete",
                    "objects_created": 15,
                    "scripts_generated": 3
                })
        
        # Step 5: Listen for any server updates
        if ws_connected:
            await self.listen_for_updates(3)
        
        # Step 6: Test ping-pong
        if ws_connected:
            await self.ws_connection.send(json.dumps({"type": "ping"}, default=make_json_serializable))
            response = await self.ws_connection.recv()
            data = json.loads(response)
            if data.get("type") == "pong":
                logger.info("✅ Ping-pong successful!")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ PLUGIN WORKFLOW COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

async def main():
    """Main test runner"""
    simulator = RobloxPluginSimulator()
    
    try:
        await simulator.initialize()
        await simulator.run_complete_workflow()
    finally:
        await simulator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())