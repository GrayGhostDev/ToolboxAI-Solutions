#!/usr/bin/env python3
"""
Simple test script to isolate and test just the rate limiting functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Setup environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["TESTING_MODE"] = "true"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.rate_limit_manager import (
    RateLimitManager,
    RateLimitConfig,
    RateLimitMode,
    clear_all_rate_limits
)

async def test_rate_limiting():
    """Test rate limiting in isolation"""
    
    print("Testing Rate Limiting in Isolation")
    print("=" * 50)
    
    # Reset everything
    RateLimitManager.reset_instance()
    clear_all_rate_limits()
    
    # Test 1: Production mode with very low limits
    print("\n1. Testing Production Mode Rate Limiting")
    
    config = RateLimitConfig(
        requests_per_minute=2,  # Only 2 requests allowed
        window_seconds=30,      # In 30 second window
        mode=RateLimitMode.PRODUCTION
    )
    
    manager = RateLimitManager.get_instance(config=config)
    manager.set_mode(RateLimitMode.PRODUCTION)
    
    # Check that bypass is disabled
    should_bypass = manager.should_bypass()
    print(f"Should bypass: {should_bypass}")
    assert should_bypass == False, "Production mode should never bypass"
    
    # Test rate limiting
    identifier = "test_user_123"
    results = []
    
    for i in range(5):
        allowed, retry_after = await manager.check_rate_limit(
            identifier=identifier,
            max_requests=2,
            window_seconds=30,
            source="test"
        )
        results.append(allowed)
        print(f"Request {i+1}: {'ALLOWED' if allowed else 'DENIED'}")
    
    allowed_count = sum(results)
    denied_count = len(results) - allowed_count
    
    print(f"Total allowed: {allowed_count}, denied: {denied_count}")
    
    # Should have exactly 2 allowed, 3 denied
    assert allowed_count == 2, f"Expected 2 allowed requests, got {allowed_count}"
    assert denied_count == 3, f"Expected 3 denied requests, got {denied_count}"
    
    print("✓ Production mode rate limiting works correctly")
    
    # Test 2: State isolation
    print("\n2. Testing State Isolation")
    
    manager.clear_all_limits()
    
    # Try again with fresh state
    allowed, retry_after = await manager.check_rate_limit(
        identifier=identifier,
        max_requests=2,
        window_seconds=30,
        source="test"
    )
    
    assert allowed == True, "First request after clearing should be allowed"
    print("✓ State isolation works correctly")
    
    # Test 3: Different identifiers
    print("\n3. Testing Different Identifiers")
    
    manager.clear_all_limits()
    
    # Test that different identifiers have separate limits
    for user_id in ["user1", "user2", "user3"]:
        for request_num in range(2):  # 2 requests each user
            allowed, _ = await manager.check_rate_limit(
                identifier=user_id,
                max_requests=2,
                window_seconds=30,
                source="test"
            )
            assert allowed == True, f"Request {request_num+1} for {user_id} should be allowed"
    
    # Third request for user1 should be denied
    allowed, _ = await manager.check_rate_limit(
        identifier="user1",
        max_requests=2,
        window_seconds=30,
        source="test"
    )
    assert allowed == False, "Third request for user1 should be denied"
    
    print("✓ Different identifiers work correctly")
    
    # Final cleanup
    manager.clear_all_limits()
    RateLimitManager.reset_instance()
    
    print("\n✅ All isolated rate limiting tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_rate_limiting())
        if success:
            print("\n🎉 SUCCESS: Rate limiting is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ FAILURE: Rate limiting tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)