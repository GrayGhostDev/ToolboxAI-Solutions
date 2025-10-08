#!/usr/bin/env python3
"""
Test if courses routes are registered in the FastAPI app
"""
import sys
sys.path.insert(0, '/app')

try:
    from apps.backend.main import app

    print("=== COURSES ROUTES CHECK ===")
    courses_found = False

    for route in app.routes:
        if hasattr(route, 'path') and 'course' in route.path.lower():
            courses_found = True
            methods = ','.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
            print(f'{methods:15} {route.path}')

    if not courses_found:
        print("❌ NO COURSES ROUTES FOUND!")
        print(f"\nTotal routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
        print("\nSample routes:")
        for route in list(app.routes)[:10]:
            if hasattr(route, 'path'):
                print(f"  {route.path}")
    else:
        print("\n✅ Courses routes are registered!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

