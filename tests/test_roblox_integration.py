#!/usr/bin/env python3
"""
Quick test script to verify Roblox integration setup
"""

import os
import sys
import json
from pathlib import Path

# Load environment variables from .env.local
env_path = Path(".env.local")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
    print("✅ Loaded .env.local")
else:
    print("⚠️  .env.local not found")

print("\n" + "="*60)
print("ROBLOX INTEGRATION TEST")
print("="*60)

# Test 1: Check encryption service
print("\n1. Testing Encryption Service...")
try:
    from apps.backend.services.encryption import CredentialEncryption
    cipher = CredentialEncryption()
    test_data = "test_credential"
    encrypted, hash_val = cipher.encrypt_credential(test_data)
    decrypted = cipher.decrypt_credential(encrypted)
    assert decrypted == test_data
    print("   ✅ Encryption service working")
except Exception as e:
    print(f"   ❌ Encryption service failed: {e}")

# Test 2: Check credential manager
print("\n2. Testing Credential Manager...")
try:
    from apps.backend.services.credential_manager import get_credential_manager
    manager = get_credential_manager()

    # Check if credentials are available
    api_key = manager.get_roblox_api_key()
    client_secret = manager.get_roblox_client_secret()
    client_id = manager.get_roblox_client_id()

    if api_key:
        print(f"   ✅ API Key loaded (length: {len(api_key)})")
    else:
        print("   ⚠️  API Key not found (check ROBLOX_API_KEY_ENCRYPTED)")

    if client_secret:
        print(f"   ✅ Client Secret loaded (length: {len(client_secret)})")
    else:
        print("   ⚠️  Client Secret not found (check ROBLOX_CLIENT_SECRET_ENCRYPTED)")

    print(f"   ✅ Client ID: {client_id}")

except Exception as e:
    print(f"   ❌ Credential manager failed: {e}")

# Test 3: Check Roblox schemas
print("\n3. Testing Roblox Schemas...")
try:
    from apps.backend.schemas.roblox import (
        OAuth2InitiateRequest,
        ConversationStartRequest,
        RojoCheckResponse
    )

    # Test schema validation
    oauth_req = OAuth2InitiateRequest()
    print(f"   ✅ OAuth2 schemas loaded")

    conv_req = ConversationStartRequest(user_id="test_user")
    print(f"   ✅ Conversation schemas loaded")

    rojo_resp = RojoCheckResponse(installed=False)
    print(f"   ✅ Rojo schemas loaded")

except Exception as e:
    print(f"   ❌ Schema loading failed: {e}")

# Test 4: Check router endpoints
print("\n4. Testing Roblox Router...")
try:
    from apps.backend.api.routers.roblox import router

    endpoints = []
    for route in router.routes:
        if hasattr(route, 'path'):
            methods = list(route.methods) if hasattr(route, 'methods') else ['GET']
            endpoints.append(f"{methods[0]} {route.path}")

    print(f"   ✅ Router loaded with {len(endpoints)} endpoints:")
    for endpoint in endpoints[:10]:  # Show first 10
        print(f"      - {endpoint}")

    if len(endpoints) > 10:
        print(f"      ... and {len(endpoints) - 10} more")

except Exception as e:
    print(f"   ❌ Router loading failed: {e}")

# Test 5: Check environment configuration
print("\n5. Testing Environment Configuration...")
config_vars = [
    "ENCRYPTION_KEY",
    "ROBLOX_API_KEY_ENCRYPTED",
    "ROBLOX_CLIENT_SECRET_ENCRYPTED",
    "ROBLOX_CLIENT_ID",
    "ROBLOX_UNIVERSE_ID",
    "ROJO_SERVER_PORT",
    "ENABLE_ROBLOX_INTEGRATION"
]

missing = []
for var in config_vars:
    value = os.getenv(var)
    if value:
        if "ENCRYPTED" in var or "KEY" in var or "SECRET" in var:
            print(f"   ✅ {var}: ****** (set)")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        missing.append(var)
        print(f"   ❌ {var}: NOT SET")

if missing:
    print(f"\n   ⚠️  Missing environment variables: {', '.join(missing)}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if not missing and all([
    "Encryption service working" in locals(),
    "Router loaded" in locals()
]):
    print("✅ Roblox integration is properly configured!")
    print("\nNext steps:")
    print("1. Start the backend: uvicorn apps.backend.main:app --port 8009")
    print("2. Test OAuth2 flow: curl http://127.0.0.1:8009/api/v1/roblox/auth/initiate")
    print("3. Check health: curl http://127.0.0.1:8009/api/v1/roblox/health")
else:
    print("⚠️  Some configuration issues need to be resolved")
    print("\nPlease check the errors above and ensure:")
    print("1. .env.local is properly configured")
    print("2. All required packages are installed")
    print("3. Database connection is available")