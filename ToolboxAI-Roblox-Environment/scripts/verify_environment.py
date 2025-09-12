#!/usr/bin/env python3
"""
Environment Configuration Verification Script

Verifies that mock data is only used in development/testing
and that production always uses real data.
"""

import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.environment import (
    get_environment_config,
    Environment,
    is_production,
    is_development,
    is_testing,
    should_use_mock_llm,
    should_use_real_data
)


def verify_environment_configuration():
    """Verify environment configuration is correctly set up"""
    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION VERIFICATION")
    print("=" * 60)
    
    # Get current configuration
    config = get_environment_config()
    
    print(f"\n📍 Current Environment: {config.environment.value}")
    print(f"   Environment Variable: {os.getenv('ENVIRONMENT', 'not set')}")
    print(f"   NODE_ENV: {os.getenv('NODE_ENV', 'not set')}")
    print(f"   TESTING: {os.getenv('TESTING', 'not set')}")
    
    print("\n🔍 Environment Detection:")
    print(f"   Is Production: {is_production()}")
    print(f"   Is Development: {is_development()}")
    print(f"   Is Testing: {is_testing()}")
    
    print("\n🎭 Mock Configuration:")
    print(f"   Use Mock LLM: {config.use_mock_llm}")
    print(f"   Use Mock Database: {config.use_mock_database}")
    print(f"   Use Mock Services: {config.use_mock_services}")
    print(f"   Use Real Data: {config.use_real_data}")
    
    print("\n🔐 Security Settings:")
    print(f"   Require Auth: {config.require_auth}")
    print(f"   Bypass Rate Limit: {config.bypass_rate_limit}")
    print(f"   Debug Mode: {config.debug_mode}")
    print(f"   Log Level: {config.log_level}")
    
    print("\n📊 Database Configuration:")
    print(f"   Database URL: {config.get_database_url()[:50]}...")
    
    print("\n🌐 Service URLs:")
    for service in ["fastapi", "flask", "mcp", "roblox"]:
        print(f"   {service}: {config.get_service_url(service)}")
    
    # Run safety checks
    print("\n" + "=" * 60)
    print("SAFETY CHECKS")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Test 1: Production never uses mocks
    print("\n✓ Test 1: Production Safety Check")
    original_env = os.environ.copy()
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["USE_MOCK_LLM"] = "true"  # Try to force mock
        os.environ["USE_MOCK_DATABASE"] = "true"
        os.environ["USE_MOCK_SERVICES"] = "true"
        
        # Recreate config
        from config.environment import EnvironmentConfig
        prod_config = EnvironmentConfig()
        
        if prod_config.use_mock_llm:
            print("   ❌ FAILED: Production allowed mock LLM!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Production blocks mock LLM")
            
        if prod_config.use_mock_database:
            print("   ❌ FAILED: Production allowed mock database!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Production blocks mock database")
            
        if prod_config.use_mock_services:
            print("   ❌ FAILED: Production allowed mock services!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Production blocks mock services")
            
        if not prod_config.require_auth:
            print("   ❌ FAILED: Production doesn't require auth!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Production requires authentication")
            
        if prod_config.bypass_rate_limit:
            print("   ❌ FAILED: Production bypasses rate limit!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Production enforces rate limiting")
            
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
    
    # Test 2: Development can use mocks
    print("\n✓ Test 2: Development Mode Check")
    try:
        os.environ["ENVIRONMENT"] = "development"
        os.environ["USE_MOCK_LLM"] = "true"
        
        dev_config = EnvironmentConfig()
        
        if not dev_config.use_mock_llm:
            print("   ❌ FAILED: Development can't use mock LLM when requested!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Development can use mock LLM")
            
    finally:
        os.environ.clear()
        os.environ.update(original_env)
    
    # Test 3: Testing defaults to mocks
    print("\n✓ Test 3: Testing Mode Check")
    try:
        os.environ["ENVIRONMENT"] = "testing"
        # Don't set USE_MOCK_* to test defaults
        
        test_config = EnvironmentConfig()
        
        if not test_config.use_mock_llm:
            print("   ❌ FAILED: Testing doesn't default to mock LLM!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Testing defaults to mock LLM")
            
        if not test_config.use_mock_database:
            print("   ❌ FAILED: Testing doesn't default to mock database!")
            all_checks_passed = False
        else:
            print("   ✅ PASSED: Testing defaults to mock database")
            
    finally:
        os.environ.clear()
        os.environ.update(original_env)
    
    # Test 4: Validate production configuration
    print("\n✓ Test 4: Production Validation")
    try:
        os.environ["ENVIRONMENT"] = "production"
        prod_config = EnvironmentConfig()
        
        if prod_config.validate_for_production():
            print("   ✅ PASSED: Production configuration is valid")
        else:
            print("   ❌ FAILED: Production configuration is invalid!")
            all_checks_passed = False
            
    finally:
        os.environ.clear()
        os.environ.update(original_env)
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - Environment configuration is correct!")
        print("   - Production will ALWAYS use real data")
        print("   - Development/Testing can use mocks when configured")
        print("   - Security settings are properly enforced")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please review configuration!")
        return 1


def check_current_settings():
    """Check current environment settings"""
    print("\n" + "=" * 60)
    print("CURRENT ENVIRONMENT SETTINGS")
    print("=" * 60)
    
    # Check agent mock LLM usage
    print("\n📦 Agent Configuration:")
    try:
        from agents.base_agent import USE_MOCK_LLM
        print(f"   Agents using mock LLM: {USE_MOCK_LLM}")
    except ImportError:
        print("   Could not import agent configuration")
    
    # Check if OpenAI key is present
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"   OpenAI API Key: Set ({len(api_key)} chars)")
    else:
        print("   OpenAI API Key: Not set")
    
    # Check rate limiting
    print("\n⚡ Rate Limiting:")
    try:
        from server.rate_limit_manager import get_rate_limit_manager
        manager = get_rate_limit_manager()
        print(f"   Mode: {manager.config.mode.value}")
        print(f"   Bypass: {manager.should_bypass()}")
    except ImportError:
        print("   Rate limit manager not available")
    
    print("\n🔍 Environment Variables:")
    env_vars = [
        "ENVIRONMENT", "NODE_ENV", "TESTING",
        "USE_MOCK_LLM", "USE_MOCK_DATABASE", "USE_MOCK_SERVICES",
        "BYPASS_RATE_LIMIT_IN_TESTS", "REQUIRE_AUTH"
    ]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   {var}: {value}")


if __name__ == "__main__":
    # Run verification
    exit_code = verify_environment_configuration()
    
    # Show current settings
    check_current_settings()
    
    sys.exit(exit_code)