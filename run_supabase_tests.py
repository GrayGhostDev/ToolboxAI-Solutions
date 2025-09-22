#!/usr/bin/env python3
"""
Minimal test runner for Supabase migration tests that avoids dependency conflicts.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Set up environment to avoid import conflicts
os.environ['TESTING_MODE'] = '1'
os.environ['SKIP_LANGCHAIN_IMPORTS'] = '1'
os.environ['PYTEST_CURRENT_TEST'] = 'supabase_migration_tests'

def run_tests():
    """Run Supabase migration tests with minimal dependencies."""
    project_root = Path(__file__).parent

    print("🧪 Supabase Migration Test Suite")
    print("=" * 60)
    print(f"📁 Project Root: {project_root}")
    print(f"🐍 Python: {sys.version}")
    print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test files to run
    test_files = [
        'tests/unit/core/agents/test_supabase_migration_agent.py',
        'tests/unit/core/agents/test_schema_analyzer_tool.py',
        'tests/unit/core/agents/test_rls_policy_generator_tool.py',
        'tests/unit/core/agents/test_data_migration_tool.py',
        'tests/integration/test_supabase_migration.py'
    ]

    # Check which test files exist
    existing_files = []
    missing_files = []

    for test_file in test_files:
        test_path = project_root / test_file
        if test_path.exists():
            existing_files.append(str(test_path))
        else:
            missing_files.append(test_file)

    if missing_files:
        print("⚠️  Missing test files:")
        for missing in missing_files:
            print(f"   ❌ {missing}")
        print()

    if not existing_files:
        print("❌ No test files found!")
        return 1

    print(f"✅ Found {len(existing_files)} test files:")
    for existing in existing_files:
        print(f"   📄 {Path(existing).name}")
    print()

    # Set up pytest command with minimal dependencies
    cmd = [
        sys.executable,
        "-m", "pytest",
        "--no-cov",  # Disable coverage initially to avoid conflicts
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-x",  # Stop on first failure
        "--import-mode=importlib",
        f"--rootdir={project_root}",
    ] + existing_files

    print("🚀 Running tests...")
    print(f"Command: {' '.join(cmd[:8])}... (+ {len(existing_files)} files)")
    print("-" * 60)

    start_time = time.time()
    result = subprocess.run(cmd, cwd=project_root)
    end_time = time.time()

    duration = end_time - start_time

    print("-" * 60)
    print(f"⏱️  Duration: {duration:.2f} seconds")

    if result.returncode == 0:
        print("🎉 All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {result.returncode}")

    return result.returncode

def run_with_coverage():
    """Run tests with coverage reporting."""
    project_root = Path(__file__).parent

    print("🧪 Supabase Migration Test Suite (With Coverage)")
    print("=" * 60)

    test_files = [
        'tests/unit/core/agents/test_supabase_migration_agent.py',
        'tests/unit/core/agents/test_schema_analyzer_tool.py',
        'tests/unit/core/agents/test_rls_policy_generator_tool.py',
        'tests/unit/core/agents/test_data_migration_tool.py',
    ]

    existing_files = [str(project_root / f) for f in test_files if (project_root / f).exists()]

    if not existing_files:
        print("❌ No test files found!")
        return 1

    cmd = [
        sys.executable,
        "-m", "pytest",
        "--cov=core.agents.supabase",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/supabase_migration",
        "--cov-fail-under=70",  # Lower threshold to start
        "-v",
        "--tb=short",
        "--disable-warnings",
        "--import-mode=importlib",
        f"--rootdir={project_root}",
    ] + existing_files

    print("🚀 Running tests with coverage...")
    print("-" * 60)

    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        print("🎉 Tests passed with coverage!")
        print(f"📊 Coverage report: {project_root}/htmlcov/supabase_migration/index.html")
    else:
        print(f"❌ Tests failed with exit code: {result.returncode}")

    return result.returncode

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        return run_with_coverage()
    else:
        return run_tests()

if __name__ == "__main__":
    sys.exit(main())