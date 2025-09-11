#!/usr/bin/env python3
"""
Test script to verify that the rate limiting fix works correctly.

This script runs the problematic tests individually and together to ensure
that rate limiting state is properly isolated between tests.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_pytest_command(test_path: str, verbose: bool = True) -> tuple[int, str, str]:
    """Run a pytest command and return exit code, stdout, stderr"""
    cmd = ["python", "-m", "pytest", test_path, "-v" if verbose else "-q"]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Test timed out"
    except Exception as e:
        return -1, "", f"Error running test: {e}"


def test_individual_rate_limiting_tests():
    """Test each rate limiting test individually"""
    logger.info("Testing individual rate limiting tests...")
    
    # The specific test that was failing
    test_path = "tests/integration/test_api_integration.py::TestPluginWorkflow::test_rate_limiting"
    
    results = []
    
    for i in range(3):  # Run 3 times to check consistency
        logger.info(f"Running individual test attempt {i+1}/3...")
        
        exit_code, stdout, stderr = run_pytest_command(test_path)
        
        results.append({
            "attempt": i + 1,
            "exit_code": exit_code,
            "passed": exit_code == 0,
            "stdout": stdout,
            "stderr": stderr
        })
        
        logger.info(f"Attempt {i+1}: {'PASSED' if exit_code == 0 else 'FAILED'}")
        
        if exit_code != 0:
            logger.error(f"STDERR: {stderr}")
            logger.error(f"STDOUT: {stdout}")
    
    return results


def test_all_plugin_workflow_tests():
    """Test all plugin workflow tests together"""
    logger.info("Testing all plugin workflow tests together...")
    
    test_path = "tests/integration/test_api_integration.py::TestPluginWorkflow"
    
    exit_code, stdout, stderr = run_pytest_command(test_path)
    
    result = {
        "exit_code": exit_code,
        "passed": exit_code == 0,
        "stdout": stdout,
        "stderr": stderr
    }
    
    logger.info(f"All tests together: {'PASSED' if exit_code == 0 else 'FAILED'}")
    
    if exit_code != 0:
        logger.error(f"STDERR: {stderr}")
        logger.error(f"STDOUT: {stdout}")
    
    return result


def test_rate_limit_manager_directly():
    """Test the rate limit manager directly"""
    logger.info("Testing rate limit manager directly...")
    
    try:
        from server.rate_limit_manager import (
            RateLimitManager,
            RateLimitConfig,
            RateLimitMode,
            clear_all_rate_limits,
            set_testing_mode,
            RateLimitTestContext
        )
        
        # Test 1: Basic functionality
        logger.info("Test 1: Basic rate limit manager functionality")
        
        RateLimitManager.reset_instance()
        manager = RateLimitManager.get_instance()
        
        # Test bypass mode
        manager.set_mode(RateLimitMode.BYPASS)
        
        async def test_bypass():
            allowed, retry_after = await manager.check_rate_limit("test_id", max_requests=1)
            return allowed, retry_after
        
        allowed, retry_after = asyncio.run(test_bypass())
        assert allowed == True, "Bypass mode should always allow requests"
        logger.info("✓ Bypass mode works correctly")
        
        # Test 2: Production mode with limits
        logger.info("Test 2: Production mode rate limiting")
        
        manager.set_mode(RateLimitMode.PRODUCTION)
        config = RateLimitConfig(requests_per_minute=2, window_seconds=60)
        manager.config = config
        
        async def test_production():
            results = []
            for i in range(5):
                allowed, retry_after = await manager.check_rate_limit(
                    "test_prod", max_requests=2, window_seconds=60, source="test"
                )
                results.append(allowed)
            return results
        
        results = asyncio.run(test_production())
        
        # First 2 should be allowed, rest should be denied
        allowed_count = sum(results)
        assert allowed_count == 2, f"Expected 2 allowed requests, got {allowed_count}"
        logger.info("✓ Production mode rate limiting works correctly")
        
        # Test 3: State isolation
        logger.info("Test 3: State isolation")
        
        # Clear all state
        manager.clear_all_limits()
        
        # Verify state is clean
        status = manager.get_limit_status("test_prod")
        assert not status["limits"], "State should be clean after clearing"
        logger.info("✓ State isolation works correctly")
        
        # Test 4: Context manager
        logger.info("Test 4: Context manager functionality")
        
        with RateLimitTestContext(bypass=True, clear_on_exit=True) as ctx:
            # Should bypass rate limits
            async def test_context():
                allowed, _ = await ctx.check_rate_limit("ctx_test", max_requests=1)
                return allowed
            
            allowed = asyncio.run(test_context())
            assert allowed == True, "Context manager should bypass rate limits"
        
        # After context, state should be clean
        manager = RateLimitManager.get_instance()
        status = manager.get_limit_status("ctx_test")
        assert not status["limits"], "State should be clean after context exit"
        logger.info("✓ Context manager works correctly")
        
        # Final cleanup
        clear_all_rate_limits()
        RateLimitManager.reset_instance()
        
        logger.info("✅ All direct tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    logger.info("="*60)
    logger.info("Testing Rate Limiting Fix")
    logger.info("="*60)
    
    # Set environment for testing
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["TESTING_MODE"] = "true"
    os.environ["BYPASS_RATE_LIMIT_IN_TESTS"] = "true"
    
    all_passed = True
    
    # Test 1: Direct rate limit manager tests
    logger.info("\n1. Testing Rate Limit Manager Directly")
    logger.info("-" * 40)
    direct_passed = test_rate_limit_manager_directly()
    all_passed = all_passed and direct_passed
    
    # Test 2: Individual test runs
    logger.info("\n2. Testing Individual Rate Limiting Tests")
    logger.info("-" * 40)
    individual_results = test_individual_rate_limiting_tests()
    individual_passed = all(r["passed"] for r in individual_results)
    all_passed = all_passed and individual_passed
    
    # Test 3: All tests together
    logger.info("\n3. Testing All Plugin Workflow Tests Together")
    logger.info("-" * 40)
    combined_result = test_all_plugin_workflow_tests()
    combined_passed = combined_result["passed"]
    all_passed = all_passed and combined_passed
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Direct tests: {'✅ PASSED' if direct_passed else '❌ FAILED'}")
    logger.info(f"Individual tests: {'✅ PASSED' if individual_passed else '❌ FAILED'}")
    logger.info(f"Combined tests: {'✅ PASSED' if combined_passed else '❌ FAILED'}")
    logger.info("-" * 60)
    logger.info(f"OVERALL: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        logger.error("\nDetails of failures:")
        if not individual_passed:
            for result in individual_results:
                if not result["passed"]:
                    logger.error(f"Individual test attempt {result['attempt']} failed")
                    logger.error(f"Exit code: {result['exit_code']}")
                    logger.error(f"Error: {result['stderr']}")
        
        if not combined_passed:
            logger.error("Combined test failed:")
            logger.error(f"Exit code: {combined_result['exit_code']}")
            logger.error(f"Error: {combined_result['stderr']}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())