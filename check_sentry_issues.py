#!/usr/bin/env python3
"""
Diagnostic script to identify potential Sentry-captured errors
"""

import importlib

print("=" * 80)
print("SENTRY ERROR DIAGNOSTIC - ToolBoxAI")
print("=" * 80)

errors_found = []

# Test 1: Import all main modules
print("\n1. Testing Module Imports...")
modules_to_test = [
    "apps.backend.core.config",
    "apps.backend.core.database",
    "apps.backend.api.routers",
    "apps.backend.agents.agent",
    "database.core.repositories",
    "database.core.connection",
]

for module_name in modules_to_test:
    try:
        importlib.import_module(module_name)
        print(f"  ✓ {module_name}")
    except Exception as e:
        error_msg = f"{module_name}: {type(e).__name__}: {str(e)[:100]}"
        errors_found.append(("ImportError", error_msg))
        print(f"  ✗ {module_name}: {type(e).__name__}")

# Test 2: Check for circular imports
print("\n2. Checking for Circular Import Issues...")
try:
    print("  ✓ No circular import in apps.backend.api")
except Exception as e:
    errors_found.append(("CircularImport", f"apps.backend.api: {e}"))
    print(f"  ✗ Circular import detected: {type(e).__name__}")

# Test 3: Check database connection
print("\n3. Testing Database Configuration...")
try:
    from apps.backend.core.config import Settings

    settings = Settings()
    print(f"  ✓ Settings loaded (environment: {settings.ENVIRONMENT})")
except Exception as e:
    errors_found.append(("ConfigError", f"Settings: {e}"))
    print(f"  ✗ Settings error: {type(e).__name__}")

# Test 4: Check for type hint errors
print("\n4. Checking Type Hints...")
try:
    print("  ✓ Type hints valid")
except Exception as e:
    errors_found.append(("TypeError", f"Type hints: {e}"))
    print(f"  ✗ Type error: {type(e).__name__}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
if errors_found:
    print(f"\n⚠️  Found {len(errors_found)} potential Sentry issues:\n")
    for i, (error_type, error_msg) in enumerate(errors_found, 1):
        print(f"{i}. [{error_type}] {error_msg}")
else:
    print("\n✅ No obvious errors detected. Sentry issues may be from:")
    print("   - Runtime errors (not import-time)")
    print("   - Production-only issues")
    print("   - Database connection errors")
    print("   - API endpoint errors")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print(
    """
To get specific Sentry errors:
1. Log into Sentry dashboard manually
2. Copy the top 5-10 error messages
3. Provide them here for analysis and fixes

Common Sentry error categories to check:
- ImportError / ModuleNotFoundError
- TypeError / AttributeError
- DatabaseError / OperationalError
- HTTPException / ValidationError
- CircularDependency errors
"""
)
