#!/usr/bin/env python3
"""
Test script to verify Rojo integration setup
"""

import json
import os
import pytest
import subprocess
import sys
from pathlib import Path

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

def test_file_exists(file_path, description):
    """Test if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def test_json_valid(file_path, description):
    """Test if a JSON file is valid"""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        print(f"✅ {description}: Valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {description}: Invalid JSON - {e}")
        return False
    except FileNotFoundError:
        print(f"❌ {description}: File not found")
        return False

def test_command_exists(command):
    """Test if a command exists in PATH or Aftman bin"""
    # First try the command directly
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        print(f"✅ {command}: Available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # If not found, try in Aftman bin directory
    if command == "rojo":
        aftman_rojo = os.path.expanduser("~/.aftman/bin/rojo")
        try:
            subprocess.run([aftman_rojo, '--version'], capture_output=True, check=True)
            print(f"✅ {command}: Available (via Aftman)")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    print(f"❌ {command}: Not available")
    return False

def main():
    """Main test function"""
    print("🎮 Testing Rojo Integration Setup")
    print("=" * 50)

    # Get current directory
    current_dir = Path(__file__).parent
    os.chdir(current_dir)

    tests_passed = 0
    total_tests = 0

    # Test 1: Check if we're in the right directory
    total_tests += 1
    if test_file_exists("default.project.json", "Rojo project file"):
        tests_passed += 1

    # Test 2: Check Aftman configuration
    total_tests += 1
    if test_file_exists("aftman.toml", "Aftman configuration"):
        tests_passed += 1

    # Test 3: Validate Rojo project file
    total_tests += 1
    if test_json_valid("default.project.json", "Rojo project configuration"):
        tests_passed += 1

    # Test 4: Check VS Code configuration
    total_tests += 1
    if test_file_exists(".vscode/settings.json", "VS Code settings"):
        tests_passed += 1

    # Test 5: Check Cursor configuration
    total_tests += 1
    if test_file_exists(".cursor/settings.json", "Cursor settings"):
        tests_passed += 1

    # Test 6: Check extensions configuration
    total_tests += 1
    if test_file_exists(".vscode/extensions.json", "VS Code extensions"):
        tests_passed += 1

    # Test 7: Check setup script
    total_tests += 1
    if test_file_exists("setup_rojo_integration.sh", "Setup script"):
        tests_passed += 1

    # Test 8: Check if setup script is executable
    total_tests += 1
    if os.access("setup_rojo_integration.sh", os.X_OK):
        print("✅ Setup script: Executable")
        tests_passed += 1
    else:
        print("❌ Setup script: Not executable")

    # Test 9: Check Roblox directory structure
    total_tests += 1
    if test_file_exists("Roblox/Scripts/ServerScripts", "Server scripts directory"):
        tests_passed += 1

    # Test 10: Check if Aftman is available
    total_tests += 1
    if test_command_exists("aftman"):
        tests_passed += 1

    # Test 11: Check if Rojo is available (after Aftman install)
    total_tests += 1
    if test_command_exists("rojo"):
        tests_passed += 1

    # Test 12: Validate project structure
    total_tests += 1
    try:
        with open("default.project.json", 'r') as f:
            project_config = json.load(f)

        required_keys = ["name", "tree"]
        if all(key in project_config for key in required_keys):
            print("✅ Project structure: Valid")
            tests_passed += 1
        else:
            print("❌ Project structure: Missing required keys")
    except Exception as e:
        print(f"❌ Project structure: Error - {e}")

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Rojo integration is properly configured.")
        print("\n📋 Next steps:")
        print("1. Open this folder in VS Code or Cursor")
        print("2. Install recommended extensions")
        print("3. Run 'Rojo: Start Server' from Command Palette")
        print("4. Connect Roblox Studio to Rojo")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
        print("\n🔧 To fix issues:")
        print("1. Run ./setup_rojo_integration.sh")
        print("2. Install missing tools: aftman install")
        print("3. Check file permissions")
        return 1

if __name__ == "__main__":
    sys.exit(main())
