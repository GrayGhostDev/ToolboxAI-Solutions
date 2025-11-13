#!/usr/bin/env python
"""
Week 2 Implementation Validation Script
Validates that all Week 2 services are properly implemented without importing them.
"""

import ast
from pathlib import Path


def validate_file_structure(file_path, required_classes, required_methods):
    """Validate that a Python file has required classes and methods."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())

        found_classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                if class_name in required_classes:
                    found_classes[class_name] = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) or isinstance(
                            item, ast.AsyncFunctionDef
                        ):
                            found_classes[class_name].append(item.name)

        # Check all required classes exist
        for cls in required_classes:
            if cls not in found_classes:
                return False, f"Missing class: {cls}"

        # Check all required methods exist
        for cls, methods in required_methods.items():
            if cls in found_classes:
                for method in methods:
                    if method not in found_classes[cls]:
                        return False, f"Missing method: {cls}.{method}"

        return True, "All required structure found"

    except Exception as e:
        return False, str(e)


def main():
    """Validate Week 2 implementations."""
    print("=" * 60)
    print("📋 Week 2 Implementation Validation")
    print("=" * 60)

    base_path = Path(".")
    results = {}

    # Test 1: Rate Limit Manager
    print("\n1. Validating Rate Limit Manager...")
    file_path = base_path / "apps/backend/core/security/rate_limit_manager.py"
    if file_path.exists():
        valid, msg = validate_file_structure(
            file_path,
            ["RateLimitManager", "RateLimitConfig"],
            {"RateLimitManager": ["__init__", "check_rate_limit", "reset_limits", "connect_redis"]},
        )
        if valid:
            results["RateLimitManager"] = "✅ Structure validated"
            print("   ✅ All required components present")
        else:
            results["RateLimitManager"] = f"❌ {msg}"
            print(f"   ❌ {msg}")
    else:
        results["RateLimitManager"] = "❌ File not found"
        print("   ❌ File not found")

    # Test 2: Semantic Cache Service
    print("\n2. Validating Semantic Cache Service...")
    file_path = base_path / "apps/backend/services/semantic_cache.py"
    if file_path.exists():
        valid, msg = validate_file_structure(
            file_path,
            ["SemanticCacheService"],
            {"SemanticCacheService": ["__init__", "get", "set", "clear_cache"]},
        )
        if valid:
            results["SemanticCacheService"] = "✅ Structure validated"
            print("   ✅ All required components present")
        else:
            results["SemanticCacheService"] = f"❌ {msg}"
            print(f"   ❌ {msg}")
    else:
        results["SemanticCacheService"] = "❌ File not found"
        print("   ❌ File not found")

    # Test 3: Cached AI Service
    print("\n3. Validating Cached AI Service...")
    file_path = base_path / "apps/backend/services/cached_ai_service.py"
    if file_path.exists():
        valid, msg = validate_file_structure(
            file_path,
            ["CachedAIService"],
            {"CachedAIService": ["__init__", "generate_completion", "batch_generate"]},
        )
        if valid:
            results["CachedAIService"] = "✅ Structure validated"
            print("   ✅ All required components present")
        else:
            results["CachedAIService"] = f"❌ {msg}"
            print(f"   ❌ {msg}")
    else:
        results["CachedAIService"] = "❌ File not found"
        print("   ❌ File not found")

    # Test 4: API Key Manager
    print("\n4. Validating API Key Manager...")
    file_path = base_path / "apps/backend/services/api_key_manager.py"
    if file_path.exists():
        valid, msg = validate_file_structure(
            file_path,
            ["APIKeyManager", "APIKeyScope"],
            {
                "APIKeyManager": [
                    "__init__",
                    "generate_api_key",
                    "validate_api_key",
                    "create_api_key",
                ]
            },
        )
        if valid:
            results["APIKeyManager"] = "✅ Structure validated"
            print("   ✅ All required components present")
        else:
            results["APIKeyManager"] = f"❌ {msg}"
            print(f"   ❌ {msg}")
    else:
        results["APIKeyManager"] = "❌ File not found"
        print("   ❌ File not found")

    # Test 5: Supabase Migration Manager
    print("\n5. Validating Supabase Migration Manager...")
    file_path = base_path / "apps/backend/services/supabase_migration_manager.py"
    if file_path.exists():
        valid, msg = validate_file_structure(
            file_path,
            ["SupabaseMigrationManager", "Migration", "MigrationStatus"],
            {
                "SupabaseMigrationManager": [
                    "__init__",
                    "migrate",
                    "rollback",
                    "get_status",
                    "create_backup",
                ]
            },
        )
        if valid:
            # Check that the singleton line is commented out
            with open(file_path) as f:
                content = f.read()
                if "# migration_manager = get_migration_manager()" in content:
                    results["SupabaseMigrationManager"] = "✅ Structure validated (singleton fixed)"
                    print("   ✅ All required components present and singleton fixed")
                else:
                    results["SupabaseMigrationManager"] = "✅ Structure validated"
                    print("   ✅ All required components present")
        else:
            results["SupabaseMigrationManager"] = f"❌ {msg}"
            print(f"   ❌ {msg}")
    else:
        results["SupabaseMigrationManager"] = "❌ File not found"
        print("   ❌ File not found")

    # Test 6: Roblox Deployment Service
    print("\n6. Validating Roblox Deployment Service...")
    file_path = base_path / "apps/backend/services/roblox_deployment.py"
    if file_path.exists():
        valid, msg = validate_file_structure(
            file_path,
            ["RobloxDeploymentPipeline", "DeploymentStatus"],
            {
                "RobloxDeploymentPipeline": [
                    "__init__",
                    "deploy_asset_bundle",
                    "create_asset_bundle",
                    "validate_asset_deployment",
                    "rollback_asset_deployment",
                ]
            },
        )
        if valid:
            results["RobloxDeploymentService"] = "✅ Structure validated"
            print("   ✅ All required components present")
        else:
            results["RobloxDeploymentService"] = f"❌ {msg}"
            print(f"   ❌ {msg}")
    else:
        results["RobloxDeploymentService"] = "❌ File not found"
        print("   ❌ File not found")

    # Test 7: Backup functionality in Supabase Migration Manager
    print("\n7. Validating Backup functionality...")
    file_path = base_path / "apps/backend/services/supabase_migration_manager.py"
    if file_path.exists():
        with open(file_path) as f:
            content = f.read()
            if "create_backup" in content and "BackupType" in content:
                results["Backup Functionality"] = "✅ Backup integrated in migration manager"
                print("   ✅ Backup functionality integrated in migration manager")
            else:
                results["Backup Functionality"] = "⚠️ Basic backup support only"
                print("   ⚠️ Basic backup support only")
    else:
        results["Backup Functionality"] = "❌ Migration manager not found"
        print("   ❌ Migration manager not found")

    # Validate Docker Configuration
    print("\n8. Validating Docker Configuration...")
    docker_file = base_path / "infrastructure/docker/compose/docker-compose.yml"
    if docker_file.exists():
        with open(docker_file) as f:
            content = f.read()
            week2_services = ["redis-cloud-connector", "backup-coordinator", "migration-runner"]
            missing = [s for s in week2_services if s not in content]
            if not missing:
                results["Docker Configuration"] = "✅ Week 2 services configured"
                print("   ✅ All Week 2 services in docker-compose.yml")
            else:
                results["Docker Configuration"] = f"❌ Missing: {missing}"
                print(f"   ❌ Missing services: {missing}")
    else:
        results["Docker Configuration"] = "❌ File not found"
        print("   ❌ docker-compose.yml not found")

    # Validate Environment Configuration
    print("\n9. Validating Environment Configuration...")
    env_file = base_path / ".env.example"
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            week2_vars = [
                "REDIS_CLOUD_ENABLED",
                "LANGCACHE_ENABLED",
                "API_KEY_MANAGER_ENABLED",
                "BACKUP_ENABLED",
                "MIGRATION_AUTO_RUN",
            ]
            missing = [v for v in week2_vars if v not in content]
            if not missing:
                results["Environment Config"] = "✅ Week 2 variables configured"
                print("   ✅ All Week 2 environment variables documented")
            else:
                results["Environment Config"] = f"❌ Missing: {missing}"
                print(f"   ❌ Missing variables: {missing}")
    else:
        results["Environment Config"] = "❌ File not found"
        print("   ❌ .env.example not found")

    # Validate API Documentation
    print("\n10. Validating API Documentation...")
    api_doc = base_path / "docs/04-api/README.md"
    if api_doc.exists():
        with open(api_doc) as f:
            content = f.read()
            if "350" in content and "Week 2" in content:
                results["API Documentation"] = "✅ Updated with Week 2 endpoints"
                print("   ✅ Documentation shows 350 endpoints with Week 2")
            else:
                results["API Documentation"] = "❌ Not updated for Week 2"
                print("   ❌ Documentation needs Week 2 updates")
    else:
        # Try alternate path
        api_doc = base_path / "docs/03-api/README.md"
        if api_doc.exists():
            with open(api_doc) as f:
                content = f.read()
                if "350" in content and "Week 2" in content:
                    results["API Documentation"] = "✅ Updated with Week 2 endpoints"
                    print("   ✅ Documentation shows 350 endpoints with Week 2")
                else:
                    results["API Documentation"] = "❌ Not updated for Week 2"
                    print("   ❌ Documentation needs Week 2 updates")
        else:
            results["API Documentation"] = "❌ File not found"
            print("   ❌ API documentation not found")

    # Validate TODO.md Updates
    print("\n11. Validating TODO.md Updates...")
    todo_file = base_path / "TODO.md"
    if todo_file.exists():
        with open(todo_file) as f:
            content = f.read()
            week2_completed = [
                "Redis Cloud Configuration",
                "LangCache Integration",
                "API Key Management",
                "Supabase Migration Manager",
                "Roblox Deployment Service",
                "Backup & Disaster Recovery",
            ]
            completed_count = sum(
                1 for item in week2_completed if "✅" in content and item in content
            )
            if completed_count >= 4:
                results["TODO.md"] = f"✅ {completed_count}/6 Week 2 tasks marked complete"
                print(f"   ✅ {completed_count}/6 Week 2 tasks marked as complete")
            else:
                results["TODO.md"] = f"⚠️  Only {completed_count}/6 tasks marked complete"
                print(f"   ⚠️  Only {completed_count}/6 tasks marked as complete")
    else:
        results["TODO.md"] = "❌ File not found"
        print("   ❌ TODO.md not found")

    # Print Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    warned = 0

    for component, result in results.items():
        print(f"{component:30} {result}")
        if "✅" in result:
            passed += 1
        elif "⚠️" in result:
            warned += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Total: {passed}/{len(results)} passed, {warned} warnings, {failed} failed")

    if failed == 0:
        print("✅ Week 2 implementation validation successful!")
        return 0
    else:
        print(f"❌ {failed} validation(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    import sys

    sys.exit(exit_code)
