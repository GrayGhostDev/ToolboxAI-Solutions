#!/usr/bin/env python3
"""
Test that all key imports work after restructuring
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_import(module_name, item_name=None):
    """Test importing a module and optionally a specific item"""
    try:
        if item_name:
            exec(f"from {module_name} import {item_name}")
            print(f"✅ {module_name}.{item_name}")
        else:
            exec(f"import {module_name}")
            print(f"✅ {module_name}")
        return True
    except Exception as e:
        print(f"❌ {module_name}{f'.{item_name}' if item_name else ''}: {str(e)[:100]}")
        return False

def main():
    print("Testing core imports after restructuring...")
    print("=" * 60)
    
    # Test configuration
    print("\n1. Configuration imports:")
    test_import("config.environment", "get_environment_config")
    test_import("config.environment", "EnvironmentConfig")
    
    # Test core packages
    print("\n2. Core package imports:")
    test_import("core")
    test_import("core.database")
    test_import("core.agents")
    test_import("core.mcp")
    test_import("core.sparc")
    test_import("core.swarm")
    
    # Test specific modules
    print("\n3. Specific module imports:")
    test_import("core.database.models", "EducationalContent")
    test_import("core.database.models", "Content")
    test_import("core.database.connection_manager", "OptimizedConnectionManager")
    test_import("core.agents.base_agent", "BaseAgent")
    test_import("core.agents.content_agent", "ContentAgent")
    test_import("core.agents.orchestrator", "AgentOrchestrator")
    test_import("core.mcp.context_manager", "MCPContextManager")
    test_import("core.sparc.state_manager", "StateManager")
    test_import("core.swarm.swarm_controller", "SwarmController")
    
    # Test database connections
    print("\n4. Database connection imports:")
    test_import("database.connection", "DatabaseManager")
    test_import("database.connection", "get_async_session")
    
    # Test apps
    print("\n5. App imports:")
    test_import("apps.backend.config")
    test_import("apps.backend.main", "app")
    
    print("\n" + "=" * 60)
    print("Import testing complete!")

if __name__ == "__main__":
    main()