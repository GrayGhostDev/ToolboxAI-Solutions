#!/usr/bin/env python3
"""
Fix dynamic imports in integration modules by making __all__ exports dynamic.
This prevents AttributeError when importing * from modules with optional dependencies.
"""

import re
from pathlib import Path
import argparse


def fix_init_file(file_path: Path) -> bool:
    """
    Fix a single __init__.py file to use dynamic exports.
    Returns True if the file was modified.
    """
    try:
        content = file_path.read_text()

        # Skip if already fixed (contains _available_exports)
        if '_available_exports' in content:
            print(f"  Already fixed: {file_path}")
            return False

        # Skip if no __all__ found
        if '__all__' not in content:
            print(f"  No __all__ found: {file_path}")
            return False

        # Find the __all__ definition
        all_pattern = r'__all__\s*=\s*\[(.*?)\]'
        all_match = re.search(all_pattern, content, re.DOTALL)

        if not all_match:
            print(f"  Could not parse __all__: {file_path}")
            return False

        all_content = all_match.group(1)

        # Extract static imports (those before try/except blocks)
        lines = content.split('\n')
        static_exports = []
        in_try_block = False

        # Find imports before first try block
        for line in lines:
            line = line.strip()
            if line.startswith('try:'):
                break
            if line.startswith('from .') and 'import (' in line:
                # Start of multi-line import
                import_start = lines.index(line) if line in lines else -1
                if import_start != -1:
                    # Find the closing parenthesis
                    for i in range(import_start, len(lines)):
                        if ')' in lines[i]:
                            # Extract imported names
                            import_block = '\n'.join(lines[import_start:i+1])
                            # Extract names between parentheses
                            import_match = re.search(r'import \((.*?)\)', import_block, re.DOTALL)
                            if import_match:
                                names = [name.strip().strip(',') for name in import_match.group(1).split('\n') if name.strip() and not name.strip().startswith('#')]
                                static_exports.extend([name for name in names if name and not name.startswith('"')])
                            break

        # Create new content with dynamic exports
        new_content = content

        # Find where to insert the _available_exports initialization
        first_try_pos = content.find('try:')
        if first_try_pos == -1:
            first_try_pos = content.find('__all__')

        if first_try_pos != -1:
            # Insert before first try block or __all__
            lines = content[:first_try_pos].split('\n')

            # Add dynamic exports initialization
            exports_init = f'\n# Track available exports dynamically\n_available_exports = {static_exports!r}\n\n'

            # Insert before the first try block
            before_try = '\n'.join(lines[:-1]) if lines[-1].strip() == '' else '\n'.join(lines)
            after_try = content[first_try_pos:]

            # Replace __all__ = [...] with __all__ = _available_exports
            after_try = re.sub(
                r'__all__\s*=\s*\[.*?\]',
                '__all__ = _available_exports',
                after_try,
                flags=re.DOTALL
            )

            # Update try blocks to append to _available_exports
            # Pattern: from .module import (Class1, Class2, ...)
            try_block_pattern = r'try:\s*\n\s*from\s+\.\w+\s+import\s+\((.*?)\)\s*\nexcept\s+ImportError:\s*\n\s*pass'

            def replace_try_block(match):
                imports = match.group(1)
                import_names = [name.strip().strip(',') for name in imports.split('\n') if name.strip() and not name.strip().startswith('#')]
                import_names = [name for name in import_names if name and '"' not in name]

                if import_names:
                    append_line = f'    _available_exports.extend({import_names!r})'
                    return match.group(0).replace('pass', append_line)
                return match.group(0)

            after_try = re.sub(try_block_pattern, replace_try_block, after_try, flags=re.DOTALL)

            # Handle single-line imports
            single_import_pattern = r'try:\s*\n\s*from\s+\.(\w+)\s+import\s+(\w+)\s*\n\s*except\s+ImportError:\s*\n\s*pass'

            def replace_single_import(match):
                class_name = match.group(2)
                append_line = f'    _available_exports.append("{class_name}")'
                return match.group(0).replace('pass', append_line)

            after_try = re.sub(single_import_pattern, replace_single_import, after_try, flags=re.DOTALL)

            new_content = before_try + exports_init + after_try

        # Write the fixed content
        if new_content != content:
            file_path.write_text(new_content)
            print(f"  Fixed: {file_path}")
            return True
        else:
            print(f"  No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"  Error fixing {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Fix dynamic imports in integration modules')
    parser.add_argument('--path', default='core/agents/integration',
                       help='Path to search for __init__.py files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without making changes')

    args = parser.parse_args()

    # Find all __init__.py files in integration modules
    base_path = Path(args.path)
    if not base_path.exists():
        print(f"Path does not exist: {base_path}")
        return 1

    init_files = list(base_path.rglob('__init__.py'))

    print(f"Found {len(init_files)} __init__.py files")

    fixed_count = 0
    for init_file in init_files:
        print(f"Checking: {init_file}")
        if not args.dry_run:
            if fix_init_file(init_file):
                fixed_count += 1
        else:
            # For dry run, just check if file needs fixing
            content = init_file.read_text()
            if '__all__' in content and '_available_exports' not in content:
                print(f"  Would fix: {init_file}")
                fixed_count += 1
            else:
                print(f"  No changes needed: {init_file}")

    print(f"\n{'Would fix' if args.dry_run else 'Fixed'} {fixed_count} files")
    return 0


if __name__ == '__main__':
    exit(main())