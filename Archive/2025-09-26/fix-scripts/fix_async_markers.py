#!/usr/bin/env python3
"""
Automatically add missing @pytest.mark.asyncio decorators to async test functions.

This script scans all test files and adds the asyncio marker to async test functions
that are missing it, following pytest-asyncio 2025 best practices.
"""

import os
import re
from pathlib import Path


def find_test_files(root_dir: str = "tests") -> list[Path]:
    """Find all Python test files in the tests directory."""
    test_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(root) / file)
    
    return test_files


def needs_asyncio_marker(lines: list[str], line_idx: int) -> bool:
    """
    Check if an async test function needs the asyncio marker.
    
    Args:
        lines: All lines in the file
        line_idx: Index of the async def line
    
    Returns:
        True if the marker is missing, False otherwise
    """
    # Check previous lines for existing markers
    for i in range(max(0, line_idx - 5), line_idx):
        if "@pytest.mark.asyncio" in lines[i]:
            return False
        if "def " in lines[i] and i < line_idx - 1:
            # Hit another function definition, stop looking
            break
    
    return True


def add_asyncio_markers(file_path: Path) -> tuple[int, list[str]]:
    """
    Add missing asyncio markers to a test file.
    
    Args:
        file_path: Path to the test file
    
    Returns:
        Tuple of (number of markers added, list of function names fixed)
    """
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    
    markers_added = 0
    functions_fixed = []
    modified = False
    
    # Pattern to match async test functions
    async_test_pattern = re.compile(r'^(\s*)async\s+def\s+(test_\w+)\s*\(')
    
    i = 0
    while i < len(lines):
        match = async_test_pattern.match(lines[i])
        if match:
            indent = match.group(1)
            func_name = match.group(2)
            
            if needs_asyncio_marker(lines, i):
                # Add the marker with proper indentation
                marker_line = f"{indent}@pytest.mark.asyncio\n"
                lines.insert(i, marker_line)
                markers_added += 1
                functions_fixed.append(func_name)
                modified = True
                i += 1  # Skip the line we just added
        
        i += 1
    
    # Check if we need to add pytest import
    if modified:
        has_pytest_import = any("import pytest" in line for line in lines[:20])
        if not has_pytest_import:
            # Add pytest import after the module docstring
            import_added = False
            for i, line in enumerate(lines[:20]):
                if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith('#'):
                    lines.insert(i, "import pytest\n")
                    import_added = True
                    break
            
            if not import_added:
                lines.insert(0, "import pytest\n")
    
    # Write back if modified
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return markers_added, functions_fixed


def add_asyncio_loop_scope(file_path: Path) -> bool:
    """
    Update asyncio markers to include loop_scope parameter for better performance.
    
    Args:
        file_path: Path to the test file
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Update simple markers to include loop_scope
    content = re.sub(
        r'@pytest\.mark\.asyncio\s*\n',
        '@pytest.mark.asyncio(loop_scope="function")\n',
        content
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


def main():
    """Main function to fix async markers in all test files."""
    print("🔧 Fixing missing @pytest.mark.asyncio decorators...")
    print("=" * 60)
    
    # Find all test files
    test_files = find_test_files()
    print(f"Found {len(test_files)} test files to check\n")
    
    total_markers_added = 0
    total_files_modified = 0
    all_functions_fixed = []
    
    for test_file in test_files:
        markers_added, functions_fixed = add_asyncio_markers(test_file)
        
        if markers_added > 0:
            total_markers_added += markers_added
            total_files_modified += 1
            all_functions_fixed.extend(functions_fixed)
            
            try:
                rel_path = test_file.relative_to(Path.cwd())
            except ValueError:
                rel_path = test_file
            print(f"✅ {rel_path}")
            print(f"   Added {markers_added} markers to: {', '.join(functions_fixed)}")
    
    # Also update existing markers with loop_scope for optimization
    print("\n🔄 Updating markers with loop_scope for better performance...")
    scope_updates = 0
    
    for test_file in test_files:
        if add_asyncio_loop_scope(test_file):
            scope_updates += 1
            try:
                rel_path = test_file.relative_to(Path.cwd())
            except ValueError:
                rel_path = test_file
            print(f"   Updated: {rel_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   Files modified: {total_files_modified}")
    print(f"   Markers added: {total_markers_added}")
    print(f"   Scope updates: {scope_updates}")
    print(f"   Functions fixed: {len(all_functions_fixed)}")
    
    if total_markers_added > 0:
        print("\n✨ Successfully fixed async test markers!")
        print("   Run 'pytest' to verify the fixes")
    else:
        print("\n✅ All async test functions already have markers!")


if __name__ == "__main__":
    main()