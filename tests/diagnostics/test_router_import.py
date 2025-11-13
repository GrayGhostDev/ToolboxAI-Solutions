#!/usr/bin/env python3
"""Test router imports to diagnose startup issues"""
import sys

sys.path.insert(0, ".")

print("=" * 60)
print("ROUTER IMPORT TEST")
print("=" * 60)

# Test 1: Import routers module
print("\n1. Testing routers.py import...")
try:
    from apps.backend.api.routers import register_routers

    print("   ✓ routers.py imported successfully")
except Exception as e:
    print(f"   ✗ ERROR importing routers.py: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 2: Import individual endpoint modules
endpoints_to_test = [
    ("auth", "apps.backend.api.v1.endpoints.auth"),
    ("users", "apps.backend.api.v1.endpoints.users"),
    ("lessons", "apps.backend.api.v1.endpoints.lessons"),
    ("assessments", "apps.backend.api.v1.endpoints.assessments"),
]

print("\n2. Testing individual endpoint imports...")
for name, module_path in endpoints_to_test:
    try:
        module = __import__(module_path, fromlist=["router"])
        router = getattr(module, "router")
        print(f"   ✓ {name:<15} → {type(router).__name__}")
    except Exception as e:
        print(f"   ✗ {name:<15} → ERROR: {str(e)[:60]}")

# Test 3: Try creating a FastAPI app and registering
print("\n3. Testing FastAPI registration...")
try:
    from fastapi import FastAPI

    app = FastAPI()
    register_routers(app)
    print("   ✓ Routers registered with FastAPI app")
    print(f"   ✓ Total routes: {len(app.routes)}")
except Exception as e:
    print(f"   ✗ ERROR during registration: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
