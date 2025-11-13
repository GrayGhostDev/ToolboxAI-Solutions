#!/usr/bin/env python
"""
Simple test runner for Week 2 services tests.
This script runs tests with proper isolation to avoid import errors.
"""

import os
import subprocess
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def run_tests():
    """Run Week 2 tests with isolated environment."""

    print("=" * 60)
    print("🧪 Running Week 2 Services Tests")
    print("=" * 60)

    # Set minimal environment to avoid import issues
    test_env = os.environ.copy()
    test_env["TESTING"] = "true"
    test_env["PYTHONPATH"] = project_root

    # Run with Python directly to avoid pytest discovery issues
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/backend/services/test_week2_services.py",
        "-v",
        "--tb=short",
        "-k",
        "test_initialization or test_cache_hit or test_generate_api_key",
        "--no-header",
        "-q",
    ]

    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(cmd, env=test_env, capture_output=False, text=True)

    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()

    if exit_code == 0:
        print("\n✅ Tests passed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")

    sys.exit(exit_code)
