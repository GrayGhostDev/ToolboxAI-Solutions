#!/usr/bin/env python3
"""
Test script for JWT Rotation Manager
Validates key rotation, token creation, and verification
"""

import asyncio
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_jwt_rotation():
    """Test JWT rotation functionality"""
    from apps.backend.core.security.jwt_rotation import JWTRotationManager

    logger.info("=" * 50)
    logger.info("JWT Rotation Manager Test")
    logger.info("=" * 50)

    # Initialize manager with short intervals for testing
    manager = JWTRotationManager(
        key_rotation_interval=60,  # 1 minute for testing
        key_grace_period=30,  # 30 seconds grace
        access_token_expire=30,  # 30 seconds
        refresh_token_expire=120  # 2 minutes
    )

    await manager.initialize()

    # Test 1: Get initial key info
    logger.info("\n1. Initial Key State")
    info = await manager.get_key_info()
    logger.info(f"   Active Key: {info['active_key_id']}")
    logger.info(f"   Expires: {info['active_key_expires']}")
    logger.info(f"   Total Keys: {info['total_keys']}")

    # Test 2: Create token pair
    logger.info("\n2. Creating Token Pair")
    user_id = "test-user-123"
    access_token, refresh_token = await manager.create_token_pair(user_id, scope="admin")
    logger.info(f"   Access Token (first 50 chars): {access_token[:50]}...")
    logger.info(f"   Refresh Token (first 50 chars): {refresh_token[:50]}...")

    # Test 3: Verify access token
    logger.info("\n3. Verifying Access Token")
    access_payload = await manager.verify_token(access_token)
    if access_payload:
        logger.info(f"   ✓ Valid token for user: {access_payload.sub}")
        logger.info(f"   Token type: {access_payload.type}")
        logger.info(f"   Key ID: {access_payload.kid}")
        logger.info(f"   Expires: {access_payload.exp}")
    else:
        logger.error("   ✗ Token verification failed")

    # Test 4: Verify refresh token
    logger.info("\n4. Verifying Refresh Token")
    refresh_payload = await manager.verify_token(refresh_token)
    if refresh_payload:
        logger.info(f"   ✓ Valid refresh token")
        logger.info(f"   Token type: {refresh_payload.type}")
    else:
        logger.error("   ✗ Refresh token verification failed")

    # Test 5: Use refresh token to get new access token
    logger.info("\n5. Refreshing Access Token")
    new_tokens = await manager.refresh_access_token(refresh_token)
    if new_tokens:
        new_access, new_refresh = new_tokens
        logger.info(f"   ✓ New access token generated")
        logger.info(f"   New token (first 50 chars): {new_access[:50]}...")
    else:
        logger.error("   ✗ Token refresh failed")

    # Test 6: Rotate keys
    logger.info("\n6. Rotating Keys")
    old_key = await manager.get_active_key()
    old_kid = old_key.kid if old_key else None
    new_key = await manager.rotate_keys()
    logger.info(f"   Old Key: {old_kid}")
    logger.info(f"   New Key: {new_key.kid}")
    logger.info(f"   New Key Expires: {new_key.expires_at}")

    # Test 7: Verify old token still works (grace period)
    logger.info("\n7. Testing Grace Period")
    old_token_valid = await manager.verify_token(access_token)
    if old_token_valid:
        logger.info(f"   ✓ Old token still valid during grace period")
    else:
        logger.info(f"   ✗ Old token no longer valid")

    # Test 8: Create token with new key
    logger.info("\n8. Creating Token with New Key")
    new_access, new_refresh = await manager.create_token_pair(user_id, scope="user")
    new_payload = await manager.verify_token(new_access)
    if new_payload:
        logger.info(f"   ✓ New token created with key: {new_payload.kid}")
    else:
        logger.error("   ✗ Failed to create token with new key")

    # Test 9: Revoke token
    logger.info("\n9. Testing Token Revocation")
    revoked = await manager.revoke_token(new_access)
    if revoked:
        logger.info("   ✓ Token revoked successfully")

        # Try to verify revoked token
        revoked_check = await manager.verify_token(new_access)
        if not revoked_check:
            logger.info("   ✓ Revoked token correctly rejected")
        else:
            logger.error("   ✗ Revoked token still valid!")
    else:
        logger.error("   ✗ Failed to revoke token")

    # Test 10: Get final key info
    logger.info("\n10. Final Key State")
    final_info = await manager.get_key_info()
    logger.info(f"   Active Key: {final_info['active_key_id']}")
    logger.info(f"   Total Keys: {final_info['total_keys']}")
    logger.info(f"   Rotation Interval: {final_info['rotation_interval']}s")
    logger.info(f"   Grace Period: {final_info['grace_period']}s")

    # Cleanup
    await manager.close()

    logger.info("\n" + "=" * 50)
    logger.info("JWT Rotation Tests Complete!")
    logger.info("=" * 50)


async def main():
    """Main test runner"""
    try:
        await test_jwt_rotation()
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())