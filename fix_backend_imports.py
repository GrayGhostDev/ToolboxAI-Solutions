#!/usr/bin/env python3
"""
Fix all backend import paths to use absolute imports from apps.backend
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single Python file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match imports that need fixing
    patterns = [
        (r'^from (api\.)', r'from apps.backend.\1'),
        (r'^from (core\.)', r'from apps.backend.\1'),
        (r'^from (models\.)', r'from apps.backend.\1'),
        (r'^from (services\.)', r'from apps.backend.\1'),
        (r'^from (agents\.)', r'from apps.backend.\1'),
        (r'^from (utils\.)', r'from apps.backend.\1'),
        (r'^from (roblox\.)', r'from apps.backend.\1'),
        # Also fix indented imports in functions
        (r'^(\s+)from (api\.)', r'\1from apps.backend.\2'),
        (r'^(\s+)from (core\.)', r'\1from apps.backend.\2'),
        (r'^(\s+)from (models\.)', r'\1from apps.backend.\2'),
        (r'^(\s+)from (services\.)', r'\1from apps.backend.\2'),
        (r'^(\s+)from (agents\.)', r'\1from apps.backend.\2'),
        (r'^(\s+)from (utils\.)', r'\1from apps.backend.\2'),
        (r'^(\s+)from (roblox\.)', r'\1from apps.backend.\2'),
        # Fix imports without dots
        (r'^(\s+)from (api|core|models|services|agents|utils|roblox|auth) import', r'\1from apps.backend.\2 import'),
        (r'^from (api|core|models|services|agents|utils|roblox|auth) import', r'from apps.backend.\1 import'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Don't double-fix already correct imports
    content = re.sub(r'from apps\.backend\.apps\.backend\.', 'from apps.backend.', content)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    backend_dir = Path('apps/backend')

    if not backend_dir.exists():
        print("Error: apps/backend directory not found")
        return

    fixed_files = []

    for py_file in backend_dir.rglob('*.py'):
        if fix_imports_in_file(py_file):
            fixed_files.append(py_file)

    if fixed_files:
        print(f"Fixed imports in {len(fixed_files)} files:")
        for f in fixed_files:
            print(f"  - {f}")
    else:
        print("No files needed fixing")

if __name__ == '__main__':
    main()