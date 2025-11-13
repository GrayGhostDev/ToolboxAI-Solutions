#!/usr/bin/env python3
"""
Comprehensive Python Code Quality Fixer
Fixes all Python files in active codebase directories
"""

import subprocess
from pathlib import Path
from typing import List, Set

# Directories to process
INCLUDE_DIRS = [
    'apps/backend',
    'database',
    'scripts',
    'tests',
    'github'
]

# Directories to exclude
EXCLUDE_PATTERNS = [
    'venv',
    'node_modules',
    '__pycache__',
    '.git',
    'Archive',
    'dist',
    'build',
    '.pytest_cache'
]


def find_python_files() -> List[Path]:
    """Find all Python files in included directories."""
    python_files = []
    
    for dir_name in INCLUDE_DIRS:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            continue
        
        for py_file in dir_path.rglob('*.py'):
            # Skip excluded patterns
            if any(pattern in str(py_file) for pattern in EXCLUDE_PATTERNS):
                continue
            python_files.append(py_file)
    
    return python_files


def fix_file(file_path: Path) -> dict:
    """Fix a single Python file."""
    results = {
        'file': str(file_path),
        'autoflake': False,
        'isort': False,
        'black': False,
        'errors': []
    }
    
    # 1. Remove unused imports and variables
    try:
        subprocess.run([
            'autoflake',
            '--in-place',
            '--remove-unused-variables',
            '--remove-all-unused-imports',
            '--ignore-init-module-imports',
            '--remove-duplicate-keys',
            str(file_path)
        ], check=True, capture_output=True, timeout=30)
        results['autoflake'] = True
    except Exception as e:
        results['errors'].append(f"autoflake: {str(e)[:50]}")
    
    # 2. Sort imports
    try:
        subprocess.run([
            'isort',
            '--profile', 'black',
            '--line-length', '100',
            '--skip-gitignore',
            str(file_path)
        ], check=True, capture_output=True, timeout=30)
        results['isort'] = True
    except Exception as e:
        results['errors'].append(f"isort: {str(e)[:50]}")
    
    # 3. Format code
    try:
        subprocess.run([
            'black',
            '--line-length', '100',
            '--quiet',
            str(file_path)
        ], check=True, capture_output=True, timeout=30)
        results['black'] = True
    except Exception as e:
        results['errors'].append(f"black: {str(e)[:50]}")
    
    return results


def main():
    print("=" * 80)
    print("🔍 COMPREHENSIVE PYTHON CODE FIXER")
    print("=" * 80)
    
    # Find files
    print(f"\n📁 Scanning directories: {', '.join(INCLUDE_DIRS)}")
    python_files = find_python_files()
    print(f"✅ Found {len(python_files)} Python files\n")
    
    if not python_files:
        print("❌ No Python files found to fix")
        return 0
    
    # Process files
    fixed = 0
    errors = 0
    
    for i, file_path in enumerate(sorted(python_files), 1):
        result = fix_file(file_path)
        
        if result['errors']:
            print(f"[{i:3}/{len(python_files)}] ✗ {file_path}")
            for error in result['errors']:
                print(f"           {error}")
            errors += 1
        else:
            print(f"[{i:3}/{len(python_files)}] ✓ {file_path}")
            fixed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Fixed: {fixed} files")
    print(f"❌ Errors: {errors} files")
    print(f"📁 Total: {len(python_files)} files")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
