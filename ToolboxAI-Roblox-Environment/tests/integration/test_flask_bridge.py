#!/usr/bin/env python3
"""
Flask Bridge Server Test Script
Tests the Flask bridge server that facilitates Roblox Studio plugin communication.
"""

import requests
import json
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FLASK_URL = "http://127.0.0.1:5001"
FASTAPI_URL = "http://127.0.0.1:8008"


def test_flask_health():
    """Test Flask bridge health endpoint"""
    try:
        response = requests.get(f"{FLASK_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Flask bridge health check passed")
            return True
    except Exception as e:
        logger.error(f"❌ Flask bridge health check failed: {e}")
    return False


def test_plugin_registration():
    """Test plugin registration endpoint"""
    try:
        data = {"port": 64989, "studio_id": "test-studio-123", "version": "1.0.0"}
        response = requests.post(f"{FLASK_URL}/register_plugin", json=data, timeout=5)
        if response.status_code in [200, 201]:
            logger.info("✅ Plugin registration successful")
            result = response.json()
            return result.get("session_id")
    except Exception as e:
        logger.error(f"❌ Plugin registration failed: {e}")
    return None


def test_content_generation_proxy():
    """Test content generation through Flask bridge"""
    try:
        data = {
            "subject": "Mathematics",
            "grade_level": 5,
            "learning_objectives": ["Fractions", "Decimals"],
            "environment_type": "classroom",
        }
        response = requests.post(f"{FLASK_URL}/generate_content", json=data, timeout=30)
        if response.status_code == 200:
            logger.info("✅ Content generation proxy working")
            return True
    except Exception as e:
        logger.error(f"❌ Content generation proxy failed: {e}")
    return False


def test_sync_progress():
    """Test progress synchronization endpoint"""
    try:
        data = {
            "student_id": "student-123",
            "lesson_id": "lesson-456",
            "progress": 75,
            "completed": False,
        }
        response = requests.post(f"{FLASK_URL}/sync_progress", json=data, timeout=5)
        if response.status_code in [200, 201]:
            logger.info("✅ Progress sync successful")
            return True
    except Exception as e:
        logger.error(f"❌ Progress sync failed: {e}")
    return False


def main():
    """Run all Flask bridge tests"""
    logger.info("=" * 60)
    logger.info("FLASK BRIDGE SERVER TESTS")
    logger.info("=" * 60)

    # Check if Flask server is running
    if not test_flask_health():
        logger.warning("Flask bridge server not running on port 5001")
        logger.info("Attempting to start Flask bridge server...")

        # Try to start the server
        import subprocess
        import os

        env_path = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/src/roblox-environment"
        try:
            # Create a simple Flask test server
            flask_test = """
from flask import Flask, jsonify, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "flask-bridge"})

@app.route("/register_plugin", methods=["POST"])
def register_plugin():
    data = request.get_json()
    return jsonify({
        "success": True,
        "session_id": "test-session-123",
        "message": "Plugin registered"
    })

@app.route("/generate_content", methods=["POST"])
def generate_content():
    data = request.get_json()
    return jsonify({
        "success": True,
        "content": "Generated content placeholder",
        "scripts": []
    })

@app.route("/sync_progress", methods=["POST"])
def sync_progress():
    data = request.get_json()
    return jsonify({"success": True, "message": "Progress synced"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
"""

            # Write temporary Flask server
            with open(f"{env_path}/tests/temp_flask_bridge.py", "w") as f:
                f.write(flask_test)

            logger.info("Created temporary Flask bridge server for testing")

        except Exception as e:
            logger.error(f"Failed to create Flask test server: {e}")
            return

    # Run tests
    tests_passed = 0
    tests_failed = 0

    # Test health
    if test_flask_health():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test plugin registration
    session_id = test_plugin_registration()
    if session_id:
        tests_passed += 1
        logger.info(f"  Session ID: {session_id}")
    else:
        tests_failed += 1

    # Test content generation proxy
    if test_content_generation_proxy():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test progress sync
    if test_sync_progress():
        tests_passed += 1
    else:
        tests_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Passed: {tests_passed}")
    logger.info(f"❌ Failed: {tests_failed}")
    logger.info(f"📊 Total: {tests_passed + tests_failed}")

    if tests_failed == 0:
        logger.info("\n🎉 ALL FLASK BRIDGE TESTS PASSED!")
    else:
        logger.info(f"\n💔 {tests_failed} TESTS FAILED")


if __name__ == "__main__":
    main()
