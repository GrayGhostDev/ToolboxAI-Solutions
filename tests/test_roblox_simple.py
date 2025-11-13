#!/usr/bin/env python3
"""
Minimal test to verify Roblox configuration
"""

from pathlib import Path

print("=" * 60)
print("ROBLOX CONFIGURATION CHECK")
print("=" * 60)

# Load and check .env.local
env_path = Path(".env.local")
if env_path.exists():
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, value = line.strip().split("=", 1)
                env_vars[key] = value

    print("\n✅ Found .env.local with encrypted credentials")

    # Check critical variables
    critical_vars = [
        "ENCRYPTION_KEY",
        "ROBLOX_API_KEY_ENCRYPTED",
        "ROBLOX_CLIENT_SECRET_ENCRYPTED",
        "ROBLOX_CLIENT_ID",
        "ROBLOX_UNIVERSE_ID",
        "ROJO_SERVER_PORT",
        "ENABLE_ROBLOX_INTEGRATION",
    ]

    print("\nConfiguration Status:")
    all_present = True
    for var in critical_vars:
        if var in env_vars:
            if "ENCRYPTED" in var or "KEY" in var or "SECRET" in var:
                print(f"  ✅ {var}: ****** (configured)")
            else:
                print(f"  ✅ {var}: {env_vars[var]}")
        else:
            print(f"  ❌ {var}: NOT CONFIGURED")
            all_present = False

    if all_present:
        print("\n✅ All required environment variables are configured!")
    else:
        print("\n⚠️  Some required variables are missing")

else:
    print("\n❌ .env.local not found!")
    print("Run: python scripts/generate_encrypted_roblox_config.py")

# Check if required files exist
print("\nFile Structure Check:")
files_to_check = [
    "apps/backend/services/encryption.py",
    "apps/backend/services/credential_manager.py",
    "apps/backend/schemas/roblox.py",
    "apps/backend/routers/roblox.py",
    "roblox/Config/default.project.json",
    "roblox/plugins/AIContentGenerator.lua",
]

all_files_exist = True
for file_path in files_to_check:
    if Path(file_path).exists():
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} - NOT FOUND")
        all_files_exist = False

if all_files_exist:
    print("\n✅ All required files are in place!")
else:
    print("\n⚠️  Some required files are missing")

# Test decryption (without heavy imports)
print("\nTesting Encryption/Decryption:")
try:
    from cryptography.fernet import Fernet

    if "ENCRYPTION_KEY" in env_vars and "ROBLOX_API_KEY_ENCRYPTED" in env_vars:
        cipher = Fernet(env_vars["ENCRYPTION_KEY"].encode())

        # Try to decrypt API key
        encrypted_api = env_vars["ROBLOX_API_KEY_ENCRYPTED"]
        decrypted = cipher.decrypt(encrypted_api.encode()).decode()
        print(f"  ✅ Successfully decrypted API key (length: {len(decrypted)})")

        # Try to decrypt client secret
        if "ROBLOX_CLIENT_SECRET_ENCRYPTED" in env_vars:
            encrypted_secret = env_vars["ROBLOX_CLIENT_SECRET_ENCRYPTED"]
            decrypted_secret = cipher.decrypt(encrypted_secret.encode()).decode()
            print(f"  ✅ Successfully decrypted client secret (length: {len(decrypted_secret)})")
    else:
        print("  ⚠️  Cannot test decryption - missing encryption key or encrypted credentials")

except Exception as e:
    print(f"  ❌ Decryption test failed: {e}")

# Summary
print("\n" + "=" * 60)
print("INTEGRATION STATUS SUMMARY")
print("=" * 60)

if all_present and all_files_exist:
    print("✅ Roblox Bridge integration is fully configured!")
    print("\n🚀 Ready to start the backend server:")
    print("   uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009")
    print("\n📝 API Documentation will be available at:")
    print("   http://127.0.0.1:8009/docs#/roblox")
    print("\n🔗 Test endpoints:")
    print("   - GET  http://127.0.0.1:8009/api/v1/roblox/health")
    print("   - POST http://127.0.0.1:8009/api/v1/roblox/auth/initiate")
    print("   - GET  http://127.0.0.1:8009/api/v1/roblox/rojo/check")
else:
    print("⚠️  Some configuration is missing. Please check the issues above.")

print("\n" + "=" * 60)
