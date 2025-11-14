#!/usr/bin/env python3
"""Find the exact location of the TypeError"""

import traceback

print("=" * 80)
print("FINDING TypeError LOCATION")
print("=" * 80)

# Test each module and capture full traceback
modules = [
    "apps.backend.core.config",
    "apps.backend.agents.agent",
    "apps.backend.api.routers",
]

for module_name in modules:
    print(f"\n{'=' * 80}")
    print(f"Testing: {module_name}")
    print("=" * 80)
    try:
        __import__(module_name)
        print(f"✓ {module_name} imported successfully")
    except TypeError as e:
        print(f"✗ TypeError in {module_name}:")
        print(f"  Error: {e}")
        print(f"\nFull Traceback:")
        traceback.print_exc()
        print("\n" + "=" * 80)
        break
    except Exception as e:
        print(f"✗ Other error in {module_name}: {type(e).__name__}: {e}")
