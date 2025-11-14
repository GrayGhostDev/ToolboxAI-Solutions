#!/usr/bin/env python3
"""
Script to fix malformed TypeScript imports in dashboard components.
Fixes the pattern: import // @ts-ignore - comment from 'module/// @ts-ignore - comment';
"""
import re
import sys
from pathlib import Path


def fix_malformed_imports(file_path):
    """Fix malformed import statements in a TypeScript file."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()


        # Pattern to match malformed imports like:
        # import // @ts-ignore - Temporary fix for MUI imports from '@mui/material/// @ts-ignore - Temporary fix for MUI imports';
        malformed_pattern = r"import\s+//\s*@ts-ignore[^'\"]*from\s+['\"][^'\"]*///[^'\"]*['\"];"

        # Find all matches
        matches = re.findall(malformed_pattern, content, re.MULTILINE)

        if matches:
            print(f"Found {len(matches)} malformed imports in {file_path}")

            # Remove the malformed import lines entirely
            content = re.sub(malformed_pattern, '', content, flags=re.MULTILINE)

            # Clean up any double newlines that might result
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

            # Write back the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ Fixed {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all TypeScript files in dashboard."""
    dashboard_src = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard/src")

    if not dashboard_src.exists():
        print(f"Dashboard source directory not found: {dashboard_src}")
        return 1

    # Find all .tsx files
    tsx_files = list(dashboard_src.rglob("*.tsx"))

    print(f"Found {len(tsx_files)} TypeScript React files")

    fixed_count = 0
    for file_path in tsx_files:
        if fix_malformed_imports(file_path):
            fixed_count += 1

    print(f"\n🎉 Fixed {fixed_count} files with malformed imports")
    return 0

if __name__ == "__main__":
    sys.exit(main())