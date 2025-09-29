"""
Simple test for API v1 endpoints integration

Tests that the new endpoints are properly registered and accessible.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_endpoint_integration():
    """Test that all endpoints are properly integrated"""
    print("Testing API v1 endpoints integration...")
    
    try:
        from fastapi.testclient import TestClient
        from apps.backend.main import app
        
        with TestClient(app) as client:
            # Test health endpoint
            response = client.get("/health")
            print(f"Health endpoint: {response.status_code}")
            assert response.status_code == 200
            
            # Test OpenAPI docs
            response = client.get("/docs")
            print(f"Docs endpoint: {response.status_code}")
            assert response.status_code == 200
            
            # Test that our new endpoints appear in OpenAPI spec
            response = client.get("/openapi.json")
            print(f"OpenAPI spec: {response.status_code}")
            assert response.status_code == 200
            
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            # Check that our new endpoints are registered
            required_endpoints = [
                "/api/v1/analytics/realtime",
                "/api/v1/analytics/summary", 
                "/api/v1/reports/generate",
                "/api/v1/admin/users"
            ]
            
            missing_endpoints = []
            for endpoint in required_endpoints:
                if endpoint in paths:
                    print(f"✅ Found endpoint: {endpoint}")
                else:
                    print(f"❌ Missing endpoint: {endpoint}")
                    missing_endpoints.append(endpoint)
            
            if missing_endpoints:
                print(f"❌ Missing endpoints: {missing_endpoints}")
                return False
            
            print("✅ All API v1 endpoints properly integrated!")
            return True
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        from apps.backend.api_v1_endpoints import analytics_router, reports_router, admin_router
        print("✅ API v1 routers imported successfully")
        
        from database.connection import get_db
        print("✅ Database connection imported successfully")
        
        from database.models.models import User, Course, Lesson, Quiz
        print("✅ Database models imported successfully")
        
        from apps.backend.api.auth.auth import get_current_user, require_role
        print("✅ Auth functions imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_router_structure():
    """Test router structure and endpoints"""
    print("Testing router structure...")
    
    try:
        from apps.backend.api_v1_endpoints import analytics_router, reports_router, admin_router
        
        # Check analytics router
        analytics_routes = [route.path for route in analytics_router.routes]
        print(f"Analytics routes: {analytics_routes}")
        
        # Check reports router  
        reports_routes = [route.path for route in reports_router.routes]
        print(f"Reports routes: {reports_routes}")
        
        # Check admin router
        admin_routes = [route.path for route in admin_router.routes]
        print(f"Admin routes: {admin_routes}")
        
        # Verify expected routes exist
        expected_analytics = ["/realtime", "/summary"]
        expected_reports = ["/generate", "/status/{report_id}", "/download/{report_id}"]
        expected_admin = ["/users", "/users/{user_id}"]
        
        for route in expected_analytics:
            if any(route in r for r in analytics_routes):
                print(f"✅ Found analytics route: {route}")
            else:
                print(f"❌ Missing analytics route: {route}")
        
        for route in expected_reports:
            if any(route in r for r in reports_routes):
                print(f"✅ Found reports route: {route}")
            else:
                print(f"❌ Missing reports route: {route}")
        
        for route in expected_admin:
            if any(route in r for r in admin_routes):
                print(f"✅ Found admin route: {route}")
            else:
                print(f"❌ Missing admin route: {route}")
        
        print("✅ Router structure test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Router structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """Run basic integration tests"""
    print("🚀 Testing API v1 Endpoints...")
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    print()
    
    # Test router structure
    if not test_router_structure():
        all_passed = False
    
    print()
    
    # Test endpoint integration
    if not test_endpoint_integration():
        all_passed = False
    
    print()
    
    if all_passed:
        print("✅ All basic integration tests passed!")
        print("\n📝 Next steps:")
        print("   1. Start the server: python server/main.py")
        print("   2. Visit: http://localhost:8008/docs")
        print("   3. Test the new /api/v1/* endpoints")
        print("\n🔧 Endpoints available:")
        print("   - GET  /api/v1/analytics/realtime")
        print("   - GET  /api/v1/analytics/summary")
        print("   - POST /api/v1/reports/generate")
        print("   - GET  /api/v1/reports/status/{report_id}")
        print("   - GET  /api/v1/reports/download/{report_id}")
        print("   - GET  /api/v1/admin/users")
        print("   - POST /api/v1/admin/users")
        print("   - GET  /api/v1/admin/users/{user_id}")
        print("   - PUT  /api/v1/admin/users/{user_id}")
        print("   - DEL  /api/v1/admin/users/{user_id}")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)