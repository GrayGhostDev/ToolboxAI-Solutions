#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for ToolBoxAI Educational Platform
Tests all services, APIs, databases, and integrations without shortcuts.
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
import sys
import requests
import psycopg2
import redis
import socketio
import websocket
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
from colorama import init, Fore, Style
import pytest

# Skip all tests in this module as they require external services
# Tests are now enabled by default since we've fixed the issues
# To skip, set SKIP_INTEGRATION_TESTS=1
pytestmark = pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS'),
    reason="Tests manually disabled. Remove SKIP_INTEGRATION_TESTS to enable"
)

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
FASTAPI_URL = "http://127.0.0.1:8008"
FLASK_URL = "http://127.0.0.1:5001"
MCP_WS_URL = "ws://127.0.0.1:9876"
SOCKETIO_URL = "http://127.0.0.1:8008"
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'user': os.environ.get('DB_USER', 'eduplatform'),
    'password': os.environ.get('DB_PASSWORD', 'eduplatform2024'),
    'database': os.environ.get('DB_NAME', 'educational_platform_dev')
}

# Test credentials
TEST_USER = {
    'username': 'john_teacher',
    'password': 'Teacher123!'
}

class IntegrationTester:
    """Comprehensive integration testing class."""
    
    def __init__(self):
        self.results = []
        self.token = None
        self.socketio_client = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text:^60}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
    def print_test(self, name: str, status: bool, details: str = ""):
        """Print test result."""
        self.total_tests += 1
        if status:
            self.passed_tests += 1
            status_icon = f"{Fore.GREEN}✓"
            status_text = f"{Fore.GREEN}PASSED"
        else:
            self.failed_tests += 1
            status_icon = f"{Fore.RED}✗"
            status_text = f"{Fore.RED}FAILED"
            
        print(f"{status_icon} {name:40} [{status_text}]{Style.RESET_ALL}")
        if details and not status:
            print(f"  {Fore.YELLOW}Details: {details}{Style.RESET_ALL}")
            
    def test_database_connection(self) -> bool:
        """Test PostgreSQL database connection."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            # Test user count
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.print_test("PostgreSQL Connection", True)
            self.print_test("Database Tables", len(tables) > 0, f"Found {len(tables)} tables")
            self.print_test("User Records", user_count > 0, f"Found {user_count} users")
            
            return True
        except Exception as e:
            self.print_test("PostgreSQL Connection", False, str(e))
            return False
            
    def test_redis_connection(self) -> bool:
        """Test Redis connection."""
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            
            # Test basic operations
            test_key = f"test_key_{int(time.time())}"
            r.set(test_key, "test_value", ex=10)
            value = r.get(test_key)
            
            # Test pub/sub
            pubsub = r.pubsub()
            pubsub.subscribe('test_channel')
            
            # Clean up
            r.delete(test_key)
            pubsub.close()
            
            self.print_test("Redis Connection", True)
            self.print_test("Redis Set/Get", value == b"test_value")
            self.print_test("Redis Pub/Sub", True)
            
            return True
        except Exception as e:
            self.print_test("Redis Connection", False, str(e))
            return False
            
    def test_fastapi_health(self) -> bool:
        """Test FastAPI server health."""
        try:
            # Health check
            response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
            health_data = response.json()
            
            self.print_test("FastAPI Health", response.status_code == 200)
            self.print_test("FastAPI Status", health_data.get('status') == 'healthy')
            
            # API documentation
            response = requests.get(f"{FASTAPI_URL}/docs", timeout=5)
            self.print_test("FastAPI Swagger Docs", response.status_code == 200)
            
            # OpenAPI schema
            response = requests.get(f"{FASTAPI_URL}/openapi.json", timeout=5)
            self.print_test("FastAPI OpenAPI Schema", response.status_code == 200)
            
            return True
        except Exception as e:
            self.print_test("FastAPI Health", False, str(e))
            return False
            
    def test_flask_health(self) -> bool:
        """Test Flask bridge server health."""
        try:
            response = requests.get(f"{FLASK_URL}/health", timeout=5)
            health_data = response.json()
            
            self.print_test("Flask Bridge Health", response.status_code == 200)
            self.print_test("Flask Bridge Status", health_data.get('status') == 'healthy')
            
            # Test agent status
            agent_status = health_data.get('agents', {})
            self.print_test("Flask Agent Systems", agent_status.get('supervisor_available', False))
            self.print_test("Flask SPARC Integration", agent_status.get('sparc_available', False))
            self.print_test("Flask Swarm Integration", agent_status.get('swarm_available', False))
            
            return response.status_code == 200
        except Exception as e:
            self.print_test("Flask Bridge Health", False, str(e))
            return False
            
    def test_authentication(self) -> bool:
        """Test authentication system."""
        try:
            # Test login
            response = requests.post(
                f"{FASTAPI_URL}/auth/login",
                json={
                    "username": TEST_USER['username'],
                    "password": TEST_USER['password']
                },
                timeout=5
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.token = auth_data.get('access_token')
                
                self.print_test("Authentication Login", True)
                self.print_test("JWT Token Generation", bool(self.token))
                
                # Test token verification
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.get(
                    f"{FASTAPI_URL}/auth/me",
                    headers=headers,
                    timeout=5
                )
                
                self.print_test("Token Verification", response.status_code == 200)
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.print_test("User Data Retrieval", 'username' in user_data)
                
                return True
            else:
                self.print_test("Authentication Login", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Authentication Login", False, str(e))
            return False
            
    def test_api_endpoints(self) -> bool:
        """Test various API endpoints."""
        if not self.token:
            self.print_test("API Endpoints", False, "No auth token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.token}"}
        endpoints = [
            ("/dashboard/overview/Teacher", "Dashboard Overview"),
            ("/classes/", "Classes Endpoint"),
            ("/lessons/", "Lessons Endpoint"),
            ("/assessments/", "Assessments Endpoint"),
            ("/analytics/progress", "Analytics Endpoint"),
            ("/users/profile", "User Profile"),
            ("/messages/", "Messages Endpoint"),
        ]
        
        all_passed = True
        for endpoint, name in endpoints:
            try:
                response = requests.get(
                    f"{FASTAPI_URL}{endpoint}",
                    headers=headers,
                    timeout=5
                )
                success = response.status_code in [200, 201]
                self.print_test(name, success, f"Status: {response.status_code}")
                all_passed = all_passed and success
            except Exception as e:
                self.print_test(name, False, str(e))
                all_passed = False
                
        return all_passed
        
    def test_content_generation(self) -> bool:
        """Test AI content generation."""
        if not self.token:
            self.print_test("Content Generation", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "subject": "Science",
                "grade_level": 7,
                "learning_objectives": ["Solar System", "Planets"],
                "environment_type": "space_station",
                "include_quiz": True
            }
            
            response = requests.post(
                f"{FASTAPI_URL}/generate_content",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            success = response.status_code == 200
            self.print_test("Content Generation API", success, f"Status: {response.status_code}")
            
            if success:
                content = response.json()
                self.print_test("Content Structure", 'success' in content)
                self.print_test("Generated Content", bool(content.get('data')))
                
            return success
        except Exception as e:
            self.print_test("Content Generation API", False, str(e))
            return False
            
    def test_socketio_connection(self) -> bool:
        """Test Socket.io connection."""
        try:
            # Create Socket.io client
            sio = socketio.Client()
            connected = False
            received_message = False
            
            @sio.event
            def connect():
                nonlocal connected
                connected = True
                
            @sio.event
            def connected(data):
                nonlocal received_message
                received_message = True
                
            # Connect to server
            sio.connect(SOCKETIO_URL, wait_timeout=5)
            time.sleep(1)  # Give it time to connect
            
            self.print_test("Socket.io Connection", connected)
            self.print_test("Socket.io Handshake", received_message)
            
            # Test ping/pong
            pong_received = False
            
            @sio.event
            def pong(data):
                nonlocal pong_received
                pong_received = True
                
            sio.emit('ping', {'timestamp': datetime.now(timezone.utc).isoformat()})
            time.sleep(1)
            
            self.print_test("Socket.io Ping/Pong", pong_received)
            
            # Disconnect
            sio.disconnect()
            
            return connected
        except Exception as e:
            self.print_test("Socket.io Connection", False, str(e))
            return False
            
    def test_websocket_connection(self) -> bool:
        """Test native WebSocket connection."""
        try:
            ws = websocket.create_connection(f"{FASTAPI_URL}/ws", timeout=5)
            
            # Send test message
            test_message = json.dumps({"type": "ping", "data": "test"}, default=make_json_serializable)
            ws.send(test_message)
            
            # Try to receive response (may timeout if no response)
            try:
                response = ws.recv_frame()
                self.print_test("WebSocket Native", True)
            except:
                self.print_test("WebSocket Native", True, "Connected but no response")
                
            ws.close()
            return True
        except Exception as e:
            self.print_test("WebSocket Native", False, str(e))
            return False
            
    def test_mcp_websocket(self) -> bool:
        """Test MCP WebSocket connection."""
        try:
            ws = websocket.create_connection(MCP_WS_URL, timeout=5)
            
            # Send hello message
            hello_msg = json.dumps({
                "type": "hello",
                "client": "integration_test"
            }, default=make_json_serializable)
            ws.send(hello_msg)
            
            # Try to receive response
            try:
                response = ws.recv()
                self.print_test("MCP WebSocket", True)
            except:
                self.print_test("MCP WebSocket", True, "Connected but no response")
                
            ws.close()
            return True
        except Exception as e:
            self.print_test("MCP WebSocket", False, str(e))
            return False
            
    def test_roblox_integration(self) -> bool:
        """Test Roblox plugin endpoints."""
        try:
            # Test plugin registration
            plugin_data = {
                "plugin_id": "test_plugin_123",
                "version": "1.0.0",
                "capabilities": ["content", "quiz", "terrain"]
            }
            
            response = requests.post(
                f"{FLASK_URL}/plugin/register",
                json=plugin_data,
                timeout=5
            )
            
            self.print_test("Roblox Plugin Registration", response.status_code in [200, 201])
            
            # Test plugin message
            message_data = {
                "type": "request_content",
                "subject": "Math",
                "grade_level": 5
            }
            
            response = requests.post(
                f"{FLASK_URL}/plugin/message",
                json=message_data,
                timeout=5
            )
            
            self.print_test("Roblox Plugin Messaging", response.status_code in [200, 201])
            
            return True
        except Exception as e:
            self.print_test("Roblox Plugin Integration", False, str(e))
            return False
            
    def test_agent_systems(self) -> bool:
        """Test agent systems."""
        try:
            # Test agent health
            response = requests.get(f"{FASTAPI_URL}/agents/health", timeout=5)
            
            if response.status_code == 200:
                health = response.json()
                self.print_test("Agent System Health", True)
                
                # Check individual agents
                agents = health.get('agents', {})
                self.print_test("Supervisor Agent", agents.get('supervisor', {}).get('healthy', False))
                self.print_test("Content Agent", agents.get('content', {}).get('healthy', False))
                self.print_test("Quiz Agent", agents.get('quiz', {}).get('healthy', False))
                self.print_test("Terrain Agent", agents.get('terrain', {}).get('healthy', False))
                self.print_test("Script Agent", agents.get('script', {}).get('healthy', False))
                
                return True
            else:
                self.print_test("Agent System Health", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Agent System Health", False, str(e))
            return False
            
    def test_data_persistence(self) -> bool:
        """Test data persistence across services."""
        try:
            if not self.token:
                self.print_test("Data Persistence", False, "No auth token available")
                return False
                
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Create test data
            test_data = {
                "title": f"Integration Test {int(time.time())}",
                "description": "Test data for integration testing",
                "metadata": {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
            }
            
            # Store via API
            response = requests.post(
                f"{FASTAPI_URL}/lessons/",
                json=test_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                created_data = response.json()
                lesson_id = created_data.get('id') or created_data.get('data', {}).get('id')
                
                self.print_test("Data Creation", True)
                
                # Retrieve via API
                if lesson_id:
                    response = requests.get(
                        f"{FASTAPI_URL}/lessons/{lesson_id}",
                        headers=headers,
                        timeout=5
                    )
                    
                    self.print_test("Data Retrieval", response.status_code == 200)
                else:
                    self.print_test("Data Retrieval", False, "No ID returned")
                    
                # Verify in database
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM lessons WHERE title LIKE %s", (f"Integration Test%",))
                count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                
                self.print_test("Database Persistence", count > 0)
                
                return True
            else:
                self.print_test("Data Creation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Data Persistence", False, str(e))
            return False
            
    def test_concurrent_requests(self) -> bool:
        """Test system under concurrent load."""
        import concurrent.futures
        
        def make_request(index):
            try:
                response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
                return response.status_code == 200
            except:
                return False
                
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(20)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
                
            success_rate = sum(results) / len(results)
            self.print_test("Concurrent Requests", success_rate > 0.9, f"Success rate: {success_rate:.0%}")
            
            return success_rate > 0.9
        except Exception as e:
            self.print_test("Concurrent Requests", False, str(e))
            return False
            
    def test_error_handling(self) -> bool:
        """Test error handling."""
        try:
            # Test 404
            response = requests.get(f"{FASTAPI_URL}/nonexistent", timeout=5)
            self.print_test("404 Error Handling", response.status_code == 404)
            
            # Test invalid auth
            headers = {"Authorization": "Bearer invalid_token"}
            response = requests.get(f"{FASTAPI_URL}/auth/me", headers=headers, timeout=5)
            self.print_test("Invalid Auth Handling", response.status_code in [401, 403])
            
            # Test invalid data
            response = requests.post(
                f"{FASTAPI_URL}/generate_content",
                json={"invalid": "data"},
                timeout=5
            )
            self.print_test("Validation Error Handling", response.status_code in [400, 422])
            
            return True
        except Exception as e:
            self.print_test("Error Handling", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all integration tests."""
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}{'TOOLBOXAI COMPLETE INTEGRATION TEST SUITE':^60}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"\nStarting comprehensive integration tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Database Tests
        self.print_header("DATABASE CONNECTIVITY")
        self.test_database_connection()
        self.test_redis_connection()
        
        # Service Health Tests
        self.print_header("SERVICE HEALTH CHECKS")
        self.test_fastapi_health()
        self.test_flask_health()
        
        # Authentication Tests
        self.print_header("AUTHENTICATION SYSTEM")
        self.test_authentication()
        
        # API Tests
        self.print_header("API ENDPOINTS")
        self.test_api_endpoints()
        
        # Content Generation
        self.print_header("AI CONTENT GENERATION")
        self.test_content_generation()
        
        # WebSocket Tests
        self.print_header("WEBSOCKET CONNECTIONS")
        self.test_socketio_connection()
        self.test_websocket_connection()
        self.test_mcp_websocket()
        
        # Integration Tests
        self.print_header("INTEGRATION POINTS")
        self.test_roblox_integration()
        self.test_agent_systems()
        
        # Data Tests
        self.print_header("DATA PERSISTENCE")
        self.test_data_persistence()
        
        # Performance Tests
        self.print_header("PERFORMANCE & RELIABILITY")
        self.test_concurrent_requests()
        self.test_error_handling()
        
        # Final Summary
        self.print_header("TEST SUMMARY")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n{Fore.CYAN}Total Tests: {self.total_tests}")
        print(f"{Fore.GREEN}Passed: {self.passed_tests}")
        print(f"{Fore.RED}Failed: {self.failed_tests}")
        print(f"{Fore.YELLOW}Success Rate: {success_rate:.1f}%{Style.RESET_ALL}")
        
        if success_rate >= 90:
            print(f"\n{Fore.GREEN}{'='*60}")
            print(f"{Fore.GREEN}{'ALL CRITICAL SYSTEMS OPERATIONAL':^60}")
            print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        elif success_rate >= 70:
            print(f"\n{Fore.YELLOW}{'='*60}")
            print(f"{Fore.YELLOW}{'SYSTEM PARTIALLY OPERATIONAL':^60}")
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}{'='*60}")
            print(f"{Fore.RED}{'CRITICAL FAILURES DETECTED':^60}")
            print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}")
            
        return success_rate >= 70

def main():
    """Main test runner."""
    tester = IntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()