#!/usr/bin/env python3
"""
Automated Qodana Issue Fixer
Fixes common code quality issues detected by Qodana inspection.

Handles:
- Unused imports (autoflake)
- Unused variables (autoflake)
- PEP8 naming (autopep8)
- Code formatting (black)
"""

import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

# SARIF file path
SARIF_FILE = "AmLZm_RvRvk_799331b8-be0c-4580-bcb4-6601912309d3_qodana.sarif.json"

# Directories to exclude from fixing
EXCLUDE_PATTERNS = [
    'Archive',
    'ghost-backend',
    'ToolboxAI-Roblox-Environment',
    'venv',
    'node_modules',
    '__pycache__',
    '.git'
]


def load_sarif_issues() -> Dict[str, List[dict]]:
    """Load and categorize issues from SARIF file."""
    print("📖 Loading Qodana SARIF report...")

    with open(SARIF_FILE, 'r') as f:
        sarif = json.load(f)

    results = sarif['runs'][0]['results']

    # Filter for active codebase only
    active_issues = []
    for result in results:
        location = result['locations'][0]['physicalLocation']['artifactLocation']['uri']
        if not any(pattern in location for pattern in EXCLUDE_PATTERNS):
            active_issues.append(result)

    # Categorize by file
    issues_by_file = defaultdict(list)
    for issue in active_issues:
        location = issue['locations'][0]['physicalLocation']['artifactLocation']['uri']
        issues_by_file[location].append(issue)

    print(f"✅ Found {len(active_issues)} issues in {len(issues_by_file)} files")
    return issues_by_file


def get_python_files_with_issues(issues_by_file: Dict[str, List[dict]]) -> Set[Path]:
    """Extract Python files that need fixing."""
    python_files = set()

    for file_path in issues_by_file.keys():
        if file_path.endswith('.py'):
            full_path = Path(file_path)
            if full_path.exists():
                python_files.add(full_path)

    return python_files


def check_dependencies():
    """Check if required tools are installed."""
    tools = {
        'autoflake': 'autoflake --version',
        'black': 'black --version',
        'isort': 'isort --version'
    }

    missing = []
    for tool, cmd in tools.items():
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)

    if missing:
        print(f"❌ Missing tools: {', '.join(missing)}")
        print(f"\n📦 Install with: pip install {' '.join(missing)}")
        return False

    return True


def fix_unused_imports_and_variables(python_files: Set[Path]):
    """Remove unused imports and variables using autoflake."""
    print(f"\n🔧 Fixing unused imports and variables in {len(python_files)} files...")

    for file_path in sorted(python_files):
        try:
            # autoflake: remove unused imports and variables
            subprocess.run([
                'autoflake',
                '--in-place',
                '--remove-unused-variables',
                '--remove-all-unused-imports',
                '--ignore-init-module-imports',
                str(file_path)
            ], check=True, capture_output=True)

            print(f"  ✓ {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {file_path}: {e.stderr.decode()[:100]}")


def fix_import_sorting(python_files: Set[Path]):
    """Sort imports using isort."""
    print(f"\n📚 Sorting imports in {len(python_files)} files...")

    for file_path in sorted(python_files):
        try:
            subprocess.run([
                'isort',
                '--profile', 'black',
                '--line-length', '100',
                str(file_path)
            ], check=True, capture_output=True)

            print(f"  ✓ {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {file_path}: {e.stderr.decode()[:100]}")


def fix_formatting(python_files: Set[Path]):
    """Format code using black."""
    print(f"\n🎨 Formatting code in {len(python_files)} files...")

    for file_path in sorted(python_files):
        try:
            subprocess.run([
                'black',
                '--line-length', '100',
                '--quiet',
                str(file_path)
            ], check=True, capture_output=True)

            print(f"  ✓ {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {file_path}: {e.stderr.decode()[:100]}")


def generate_report(issues_by_file: Dict[str, List[dict]]):
    """Generate summary report of issues."""
    print("\n" + "=" * 80)
    print("ISSUE SUMMARY")
    print("=" * 80)

    # Count by type
    by_type = defaultdict(int)
    for issues in issues_by_file.values():
        for issue in issues:
            by_type[issue['ruleId']] += 1

    print("\nTop Issues:")
    for rule_id, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {rule_id:50} {count:4} issues")

    print("\nTop Files:")
    for file_path, issues in sorted(issues_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  {len(issues):4} issues | {file_path}")


def main():
    """Main execution flow."""
    print("=" * 80)
    print("🔍 QODANA ISSUE FIXER")
    print("=" * 80)

    # Load issues
    issues_by_file = load_sarif_issues()

    # Get Python files
    python_files = get_python_files_with_issues(issues_by_file)

    if not python_files:
        print("✅ No Python files with issues found!")
        return 0

    # Check dependencies
    if not check_dependencies():
        return 1

    # Generate initial report
    generate_report(issues_by_file)

    # Ask for confirmation
    print(f"\n📝 Ready to fix {len(python_files)} Python files")
    response = input("Continue? (y/N): ").strip().lower()

    if response != 'y':
        print("❌ Cancelled by user")
        return 0

    # Run fixes
    fix_unused_imports_and_variables(python_files)
    fix_import_sorting(python_files)
    fix_formatting(python_files)

    print("\n" + "=" * 80)
    print("✅ FIXES COMPLETED")
    print("=" * 80)
    print("\n📋 Next steps:")
    print("  1. Review changes: git diff")
    print("  2. Run tests: pytest")
    print("  3. Run type check: basedpyright .")
    print("  4. Run Qodana again to verify fixes")
    print("\n💡 Manual fixes still needed:")
    print("  - Broad exception catching (PyBroadExceptionInspection)")
    print("  - Variable shadowing (PyShadowingNamesInspection)")
    print("  - Methods that could be static (PyMethodMayBeStaticInspection)")

    return 0


if __name__ == '__main__':
    sys.exit(main())
