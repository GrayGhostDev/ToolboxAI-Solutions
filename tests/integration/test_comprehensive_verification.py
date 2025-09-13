#!/usr/bin/env python3
"""
Comprehensive Verification Test Script for ToolboxAI Platform

This script tests:
1. Database connectivity with correct credentials
2. Authentication system functionality
3. API endpoints and content generation
4. WebSocket authentication and messaging
5. End-to-end workflow validation

Usage:
    python test_comprehensive_verification.py [--verbose] [--fix-issues]
"""

import asyncio
import aiohttp
import asyncpg
import json
import logging
import os
import sys
import time
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import uuid
import argparse
import pytest

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skip(reason="Integration tests require external services - run with --run-integration")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveVerificationTest:
    """Comprehensive test suite for ToolboxAI platform"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8008", 
                 ws_url: str = "ws://127.0.0.1:8008",
                 verbose: bool = False):
        self.base_url = base_url
        self.ws_url = ws_url
        self.verbose = verbose
        self.results = []
        self.auth_token = None
        self.test_user = None
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'eduplatform'),
            'password': os.getenv('DB_PASSWORD', 'eduplatform2024'),
            'database': os.getenv('DB_NAME', 'educational_platform_dev')
        }
        
    def log_test_result(self, test_name: str, status: str, details: str = "", 
                       duration: float = 0):
        """Log test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if self.verbose and details:
            print(f"   Details: {details}")
            
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity with correct credentials"""
        start_time = time.time()
        
        try:
            # Test connection
            conn = await asyncpg.connect(**self.db_config)
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                self.log_test_result(
                    "Database Connectivity", 
                    "FAIL", 
                    "Basic query failed",
                    time.time() - start_time
                )
                return False
                
            # Test tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            table_names = [row['table_name'] for row in tables]
            required_tables = ['dashboard_users', 'classes', 'assignments', 'submissions']
            missing_tables = [t for t in required_tables if t not in table_names]
            
            await conn.close()
            
            if missing_tables:
                self.log_test_result(
                    "Database Connectivity", 
                    "WARN", 
                    f"Missing tables: {missing_tables}",
                    time.time() - start_time
                )
                return True  # Connection works, but schema incomplete
            else:
                self.log_test_result(
                    "Database Connectivity", 
                    "PASS", 
                    f"Connected successfully, {len(table_names)} tables found",
                    time.time() - start_time
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Database Connectivity", 
                "FAIL", 
                f"Connection failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_api_health_check(self) -> bool:
        """Test API health endpoint"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test_result(
                            "API Health Check", 
                            "PASS", 
                            f"API responding: {data.get('status')}",
                            time.time() - start_time
                        )
                        return True
                    else:
                        self.log_test_result(
                            "API Health Check", 
                            "FAIL", 
                            f"HTTP {response.status}",
                            time.time() - start_time
                        )
                        return False
                        
        except Exception as e:
            self.log_test_result(
                "API Health Check", 
                "FAIL", 
                f"Request failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_authentication_system(self) -> bool:
        """Test authentication endpoints"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test registration (if available)
                register_data = {
                    "username": f"test_user_{int(time.time())}",
                    "email": f"test_{int(time.time())}@example.com",
                    "password": "Test123!@#",
                    "role": "student"
                }
                
                # Try registration endpoint
                try:
                    async with session.post(
                        f"{self.base_url}/auth/register", 
                        json=register_data
                    ) as response:
                        if response.status in [200, 201]:
                            reg_data = await response.json()
                            self.test_user = register_data
                            self.auth_token = reg_data.get('access_token')
                        elif response.status == 404:
                            # Registration endpoint doesn't exist, try login with demo user
                            pass
                        else:
                            details = await response.text()
                            logger.warning(f"Registration failed: {details}")
                except Exception as e:
                    logger.warning(f"Registration test failed: {e}")
                
                # Test login
                login_data = {
                    "username": os.getenv("DEMO_USERNAME", "demo_student"),
                    "password": os.getenv("DEMO_PASSWORD", "demo123")
                }
                
                # If we have a test user, use that instead
                if self.test_user:
                    login_data = {
                        "username": self.test_user["username"],
                        "password": self.test_user["password"]
                    }
                
                async with session.post(
                    f"{self.base_url}/auth/login", 
                    json=login_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.auth_token = data.get('access_token')
                        if self.auth_token:
                            self.log_test_result(
                                "Authentication System", 
                                "PASS", 
                                "Login successful, token received",
                                time.time() - start_time
                            )
                            return True
                        else:
                            self.log_test_result(
                                "Authentication System", 
                                "FAIL", 
                                "Login successful but no token received",
                                time.time() - start_time
                            )
                            return False
                    else:
                        details = await response.text()
                        self.log_test_result(
                            "Authentication System", 
                            "FAIL", 
                            f"Login failed: HTTP {response.status} - {details}",
                            time.time() - start_time
                        )
                        return False
                        
        except Exception as e:
            self.log_test_result(
                "Authentication System", 
                "FAIL", 
                f"Authentication test failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_protected_endpoints(self) -> bool:
        """Test protected API endpoints"""
        start_time = time.time()
        
        if not self.auth_token:
            self.log_test_result(
                "Protected Endpoints", 
                "SKIP", 
                "No auth token available",
                time.time() - start_time
            )
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with aiohttp.ClientSession() as session:
                # Test dashboard data endpoint
                async with session.get(
                    f"{self.base_url}/api/dashboard/data", 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test_result(
                            "Protected Endpoints", 
                            "PASS", 
                            f"Dashboard data retrieved: {len(data)} items",
                            time.time() - start_time
                        )
                        return True
                    else:
                        details = await response.text()
                        self.log_test_result(
                            "Protected Endpoints", 
                            "FAIL", 
                            f"Dashboard access failed: HTTP {response.status} - {details}",
                            time.time() - start_time
                        )
                        return False
                        
        except Exception as e:
            self.log_test_result(
                "Protected Endpoints", 
                "FAIL", 
                f"Protected endpoint test failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_content_generation(self) -> bool:
        """Test content generation endpoints"""
        start_time = time.time()
        
        if not self.auth_token:
            self.log_test_result(
                "Content Generation", 
                "SKIP", 
                "No auth token available",
                time.time() - start_time
            )
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            content_request = {
                "subject": "Mathematics",
                "grade_level": 7,
                "learning_objectives": ["Basic Algebra", "Variables"],
                "environment_type": "classroom",
                "include_quiz": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/generate_content", 
                    json=content_request,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                            self.log_test_result(
                                "Content Generation", 
                                "PASS", 
                                f"Content generated successfully: {data.get('message', '')}",
                                time.time() - start_time
                            )
                            return True
                        else:
                            self.log_test_result(
                                "Content Generation", 
                                "FAIL", 
                                f"Content generation failed: {data.get('message', '')}",
                                time.time() - start_time
                            )
                            return False
                    else:
                        details = await response.text()
                        self.log_test_result(
                            "Content Generation", 
                            "FAIL", 
                            f"Content generation request failed: HTTP {response.status} - {details}",
                            time.time() - start_time
                        )
                        return False
                        
        except Exception as e:
            self.log_test_result(
                "Content Generation", 
                "FAIL", 
                f"Content generation test failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_websocket_authentication(self) -> bool:
        """Test WebSocket authentication and messaging"""
        start_time = time.time()
        
        if not self.auth_token:
            self.log_test_result(
                "WebSocket Authentication", 
                "SKIP", 
                "No auth token available",
                time.time() - start_time
            )
            return False
            
        try:
            # Connect to WebSocket with authentication
            ws_url = f"{self.ws_url}/ws?token={self.auth_token}"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for welcome message
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                welcome_data = json.loads(welcome_msg)
                
                if welcome_data.get('type') == 'connected':
                    # Send a ping message
                    ping_msg = {
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(ping_msg))
                    
                    # Wait for pong response
                    response_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response_msg)
                    
                    if response_data.get('type') == 'pong':
                        self.log_test_result(
                            "WebSocket Authentication", 
                            "PASS", 
                            "WebSocket connection and messaging successful",
                            time.time() - start_time
                        )
                        return True
                    else:
                        self.log_test_result(
                            "WebSocket Authentication", 
                            "FAIL", 
                            f"Unexpected response: {response_data}",
                            time.time() - start_time
                        )
                        return False
                else:
                    self.log_test_result(
                        "WebSocket Authentication", 
                        "FAIL", 
                        f"No welcome message received: {welcome_data}",
                        time.time() - start_time
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "WebSocket Authentication", 
                "FAIL", 
                f"WebSocket test failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_database_performance(self) -> bool:
        """Test database query performance"""
        start_time = time.time()
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Test query performance
            query_start = time.time()
            result = await conn.fetch("""
                SELECT COUNT(*) as total_users
                FROM dashboard_users
                WHERE is_active = true
            """)
            query_time = (time.time() - query_start) * 1000  # Convert to ms
            
            await conn.close()
            
            if query_time < 50:  # 50ms threshold
                self.log_test_result(
                    "Database Performance", 
                    "PASS", 
                    f"Query executed in {query_time:.2f}ms (target: <50ms)",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Database Performance", 
                    "WARN", 
                    f"Query took {query_time:.2f}ms (target: <50ms)",
                    time.time() - start_time
                )
                return True  # Still pass, but with warning
                
        except Exception as e:
            self.log_test_result(
                "Database Performance", 
                "FAIL", 
                f"Performance test failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def test_websocket_endpoints(self) -> bool:
        """Test WebSocket status endpoints"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test WebSocket status endpoint
                async with session.get(f"{self.base_url}/ws/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        active_connections = data.get('active_connections', 0)
                        self.log_test_result(
                            "WebSocket Status Endpoints", 
                            "PASS", 
                            f"WebSocket status available: {active_connections} active connections",
                            time.time() - start_time
                        )
                        return True
                    else:
                        self.log_test_result(
                            "WebSocket Status Endpoints", 
                            "FAIL", 
                            f"WebSocket status failed: HTTP {response.status}",
                            time.time() - start_time
                        )
                        return False
                        
        except Exception as e:
            self.log_test_result(
                "WebSocket Status Endpoints", 
                "FAIL", 
                f"WebSocket status test failed: {str(e)}",
                time.time() - start_time
            )
            return False
            
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all verification tests"""
        print("🚀 Starting Comprehensive ToolboxAI Platform Verification")
        print("=" * 80)
        
        total_start_time = time.time()
        
        # Run all tests in sequence
        tests = [
            self.test_database_connectivity,
            self.test_api_health_check,
            self.test_authentication_system,
            self.test_protected_endpoints,
            self.test_content_generation,
            self.test_websocket_authentication,
            self.test_database_performance,
            self.test_websocket_endpoints
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    # Check if it was skipped
                    last_result = self.results[-1] if self.results else {}
                    if last_result.get('status') == 'SKIP':
                        skipped += 1
                    else:
                        failed += 1
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
                failed += 1
                
        total_duration = time.time() - total_start_time
        
        # Generate summary
        summary = {
            'total_tests': len(tests),
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'success_rate': (passed / len(tests)) * 100,
            'total_duration': total_duration,
            'timestamp': datetime.now().isoformat(),
            'detailed_results': self.results
        }
        
        print("\n" + "=" * 80)
        print("📊 VERIFICATION RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} {'❌' if summary['failed'] > 0 else '✅'}")
        print(f"Skipped: {summary['skipped']} ⚠️")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        if summary['success_rate'] >= 80:
            print("\n🎉 PLATFORM VERIFICATION SUCCESSFUL!")
            print("✅ The ToolboxAI platform is working correctly with the database fixes.")
        else:
            print(f"\n⚠️ PLATFORM VERIFICATION INCOMPLETE!")
            print(f"❌ {summary['failed']} critical issues found. Review failed tests above.")
            
        return summary
        
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"verification_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed results saved to: {filename}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Comprehensive ToolboxAI Platform Verification")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--fix-issues", action="store_true", help="Attempt to fix issues (not implemented)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8008", help="Base API URL")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8008", help="WebSocket URL")
    
    args = parser.parse_args()
    
    # Create test instance
    verifier = ComprehensiveVerificationTest(
        base_url=args.base_url,
        ws_url=args.ws_url,
        verbose=args.verbose
    )
    
    # Run all tests
    results = await verifier.run_all_tests()
    
    # Save results
    verifier.save_results(results)
    
    # Return appropriate exit code
    if results['success_rate'] >= 80:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)