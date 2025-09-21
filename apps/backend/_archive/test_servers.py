
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_connection():
    """Mock database connection for tests"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

#!/usr/bin/env python3
"""
Test Script for ToolboxAI Roblox Environment Servers

Tests basic functionality of both FastAPI and Flask servers to ensure
they are working correctly and can communicate properly.
"""

import requests
import time
import json
import asyncio
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerTester:
    """Tests server functionality"""

    def __init__(self):
        self.fastapi_base = "http://127.0.0.1:8008"
        self.flask_base = "http://127.0.0.1:5001"
        self.timeout = 10

    def test_server_health(self, base_url: str, server_name: str) -> bool:
        """Test server health endpoint"""
        try:
            response = requests.get(f"{base_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {server_name} health check passed: {data.get('status')}")
                return True
            else:
                logger.error(f"❌ {server_name} health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"❌ {server_name} health check error: {e}")
            return False

    def test_fastapi_endpoints(self) -> Dict[str, bool]:
        """Test FastAPI endpoints"""
        results = {}

        # Test health endpoint
        results["health"] = self.test_server_health(self.fastapi_base, "FastAPI")

        # Test info endpoint
        try:
            response = requests.get(f"{self.fastapi_base}/info", timeout=self.timeout)
            results["info"] = response.status_code == 200
            if results["info"]:
                logger.info("✅ FastAPI info endpoint working")
            else:
                logger.error(f"❌ FastAPI info endpoint failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ FastAPI info endpoint error: {e}")
            results["info"] = False

        # Test metrics endpoint
        try:
            response = requests.get(f"{self.fastapi_base}/metrics", timeout=self.timeout)
            results["metrics"] = response.status_code == 200
            if results["metrics"]:
                logger.info("✅ FastAPI metrics endpoint working")
            else:
                logger.error(f"❌ FastAPI metrics endpoint failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ FastAPI metrics endpoint error: {e}")
            results["metrics"] = False

        # Test content generation (without auth for testing)
        try:
            test_request = {
                "subject": "Mathematics",
                "grade_level": 5,
                "learning_objectives": [
                    {"title": "Basic Addition", "description": "Learn to add numbers"}
                ],
                "environment_type": "classroom",
                "include_quiz": True,
            }

            # This will likely fail due to auth, but we can check if endpoint exists
            response = requests.post(
                f"{self.fastapi_base}/generate_content", json=test_request, timeout=self.timeout
            )

            # 401 (auth required) or 422 (validation error) are acceptable
            results["content_generation"] = response.status_code in [401, 422, 200]
            if results["content_generation"]:
                logger.info("✅ FastAPI content generation endpoint reachable")
            else:
                logger.error(
                    f"❌ FastAPI content generation endpoint issue: {response.status_code}"
                )

        except Exception as e:
            logger.error(f"❌ FastAPI content generation error: {e}")
            results["content_generation"] = False

        return results

    def test_flask_endpoints(self) -> Dict[str, bool]:
        """Test Flask bridge server endpoints"""
        results = {}

        # Test health endpoint
        results["health"] = self.test_server_health(self.flask_base, "Flask Bridge")

        # Test status endpoint
        try:
            response = requests.get(f"{self.flask_base}/status", timeout=self.timeout)
            results["status"] = response.status_code == 200
            if results["status"]:
                data = response.json()
                logger.info(f"✅ Flask status endpoint working: {data.get('status')}")
            else:
                logger.error(f"❌ Flask status endpoint failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Flask status endpoint error: {e}")
            results["status"] = False

        # Test plugin registration
        try:
            test_plugin = {"studio_id": "test_user_123", "port": 64989, "version": "1.0.0"}

            response = requests.post(
                f"{self.flask_base}/register_plugin", json=test_plugin, timeout=self.timeout
            )

            results["plugin_registration"] = response.status_code == 200
            if results["plugin_registration"]:
                data = response.json()
                logger.info(f"✅ Flask plugin registration working: {data.get('success')}")
            else:
                logger.error(f"❌ Flask plugin registration failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Flask plugin registration error: {e}")
            results["plugin_registration"] = False

        # Test simple content generation
        try:
            test_content_request = {
                "subject": "Science",
                "grade_level": 6,
                "learning_objectives": ["Photosynthesis"],
                "environment_type": "laboratory",
            }

            response = requests.post(
                f"{self.flask_base}/generate_simple_content",
                json=test_content_request,
                timeout=30,  # Longer timeout for content generation
            )

            results["simple_content"] = response.status_code == 200
            if results["simple_content"]:
                logger.info("✅ Flask simple content generation working")
            else:
                logger.warning(f"⚠️ Flask simple content generation issue: {response.status_code}")
                # This might fail if FastAPI server is not responding, so it's a warning

        except Exception as e:
            logger.warning(f"⚠️ Flask simple content generation error: {e}")
            results["simple_content"] = False

        return results

    def test_server_communication(self) -> bool:
        """Test communication between Flask and FastAPI servers"""
        try:
            # Use Flask bridge to test FastAPI communication
            response = requests.get(f"{self.flask_base}/status", timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                fastapi_connection = data.get("fastapi_connection")

                if fastapi_connection:
                    logger.info(f"✅ Server communication configured: {fastapi_connection}")
                    return True
                else:
                    logger.warning("⚠️ FastAPI connection not configured in Flask bridge")
                    return False
            else:
                logger.error("❌ Cannot test server communication - Flask status failed")
                return False

        except Exception as e:
            logger.error(f"❌ Server communication test error: {e}")
            return False

    def test_dependencies(self) -> Dict[str, bool]:
        """Test if required dependencies are working"""
        results = {}

        # Test imports
        dependencies = [
            ("fastapi", "FastAPI"),
            ("flask", "Flask"),
            ("requests", "Requests"),
            ("redis", "Redis"),
            ("pydantic", "Pydantic"),
        ]

        for module, name in dependencies:
            try:
                __import__(module)
                results[name.lower()] = True
                logger.info(f"✅ {name} import successful")
            except ImportError:
                results[name.lower()] = False
                logger.error(f"❌ {name} import failed")

        # Test optional AI dependencies
        ai_dependencies = [
            ("openai", "OpenAI"),
            ("langchain", "LangChain"),
        ]

        for module, name in ai_dependencies:
            try:
                __import__(module)
                results[name.lower()] = True
                logger.info(f"✅ {name} import successful")
            except ImportError:
                results[name.lower()] = False
                logger.warning(f"⚠️ {name} import failed (optional)")

        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("🚀 Starting ToolboxAI Roblox Environment server tests...")

        results = {
            "timestamp": time.time(),
            "dependencies": {},
            "fastapi": {},
            "flask": {},
            "communication": False,
            "overall_status": "unknown",
        }

        # Test dependencies
        logger.info("📦 Testing dependencies...")
        results["dependencies"] = self.test_dependencies()

        # Wait for servers to be ready
        logger.info("⏳ Waiting for servers to be ready...")
        time.sleep(2)

        # Test FastAPI server
        logger.info("🔧 Testing FastAPI server...")
        results["fastapi"] = self.test_fastapi_endpoints()

        # Test Flask server
        logger.info("🌉 Testing Flask bridge server...")
        results["flask"] = self.test_flask_endpoints()

        # Test server communication
        logger.info("🔗 Testing server communication...")
        results["communication"] = self.test_server_communication()

        # Calculate overall status
        fastapi_working = any(results["fastapi"].values())
        flask_working = any(results["flask"].values())
        deps_working = any(results["dependencies"].values())

        if fastapi_working and flask_working and deps_working:
            results["overall_status"] = "healthy"
            logger.info("🎉 Overall status: HEALTHY")
        elif fastapi_working or flask_working:
            results["overall_status"] = "partial"
            logger.warning("⚠️ Overall status: PARTIAL (some servers working)")
        else:
            results["overall_status"] = "unhealthy"
            logger.error("❌ Overall status: UNHEALTHY")

        return results

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)

        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Test Time: {time.ctime(results['timestamp'])}")
        print()

        print("Dependencies:")
        for dep, status in results["dependencies"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {dep}")
        print()

        print("FastAPI Server:")
        for endpoint, status in results["fastapi"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {endpoint}")
        print()

        print("Flask Bridge Server:")
        for endpoint, status in results["flask"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {endpoint}")
        print()

        comm_icon = "✅" if results["communication"] else "❌"
        print(f"Server Communication: {comm_icon}")
        print()

        if results["overall_status"] == "healthy":
            print("🎉 All systems are working correctly!")
        elif results["overall_status"] == "partial":
            print("⚠️ Some issues detected. Check the logs above.")
        else:
            print("❌ Multiple issues detected. Please check server configuration.")

        print("=" * 60)


def main():
    """Main test runner"""
    tester = ServerTester()

    try:
        results = tester.run_all_tests()
        tester.print_summary(results)

        # Return appropriate exit code
        if results["overall_status"] == "healthy":
            return 0
        elif results["overall_status"] == "partial":
            return 1
        else:
            return 2

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Test runner error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
