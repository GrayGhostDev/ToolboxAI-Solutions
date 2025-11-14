#!/usr/bin/env python3
"""
Automated Flake8 Issue Fixer
Fixes common flake8 issues across the backend codebase
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Root directory for backend code
BACKEND_DIR = Path(__file__).parent / "apps" / "backend"


def remove_trailing_whitespace(content: str) -> str:
    """Remove trailing whitespace from lines (W291)"""
    lines = content.split('\n')
    return '\n'.join(line.rstrip() for line in lines)


def remove_whitespace_blank_lines(content: str) -> str:
    """Remove whitespace from blank lines (W293)"""
    lines = content.split('\n')
    result = []
    for line in lines:
        if line.strip() == '':
            result.append('')
        else:
            result.append(line)
    return '\n'.join(result)


def fix_comparison_to_bool(content: str) -> str:
    """Fix comparisons to True/False (E712)"""
    # Fix == True
    content = re.sub(r'(\w+)\s*==\s*True\b', r'\1', content)
    # Fix == False
    content = re.sub(r'(\w+)\s*==\s*False\b', r'not \1', content)
    return content


def remove_unused_import(content: str, import_statement: str) -> str:
    """Remove a specific unused import"""
    # Handle different import formats
    patterns = [
        rf'^from\s+[\w.]+\s+import\s+{re.escape(import_statement)}\s*$',
        rf'^import\s+{re.escape(import_statement)}\s*$',
    ]
    
    lines = content.split('\n')
    result = []
    
    for line in lines:
        should_remove = False
        for pattern in patterns:
            if re.match(pattern, line.strip()):
                should_remove = True
                break
        
        if not should_remove:
            result.append(line)
    
    return '\n'.join(result)


def fix_bare_except(content: str) -> str:
    """Fix bare except clauses (E722)"""
    # Replace bare except with Exception
    content = re.sub(
        r'(\s+)except:\s*$',
        r'\1except Exception:',
        content,
        flags=re.MULTILINE
    )
    return content


def fix_ambiguous_variable_names(content: str) -> str:
    """Fix ambiguous variable names like 'l' (E741)"""
    # This is complex and context-dependent, so we'll flag it for manual review
    return content


def split_long_lines(content: str, max_length: int = 120) -> str:
    """Helper to identify long lines - manual fix needed for E501"""
    # This is too complex to automate safely
    return content


def process_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Process a single Python file and apply fixes"""
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        
        # Apply fixes
        content = remove_trailing_whitespace(content)
        if content != original_content:
            changes.append("Removed trailing whitespace")
        
        original_content = content
        content = remove_whitespace_blank_lines(content)
        if content != original_content:
            changes.append("Fixed blank lines with whitespace")
        
        original_content = content
        content = fix_comparison_to_bool(content)
        if content != original_content:
            changes.append("Fixed bool comparisons")
        
        original_content = content
        content = fix_bare_except(content)
        if content != original_content:
            changes.append("Fixed bare except clauses")
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        
        return False, []
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, []


def main():
    """Main execution function"""
    print("🔧 Starting Flake8 Auto-Fixer...")
    print(f"📁 Scanning: {BACKEND_DIR}")
    
    total_files = 0
    fixed_files = 0
    
    # Find all Python files
    for py_file in BACKEND_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        total_files += 1
        changed, changes = process_file(py_file)
        
        if changed:
            fixed_files += 1
            rel_path = py_file.relative_to(BACKEND_DIR)
            print(f"✅ Fixed: {rel_path}")
            for change in changes:
                print(f"   - {change}")
    
    print(f"\n📊 Summary:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Files fixed: {fixed_files}")
    print(f"\n⚠️  Manual fixes still needed for:")
    print("   - E501: Line too long (>120 chars)")
    print("   - E741: Ambiguous variable names (l, O, I)")
    print("   - F401: Unused imports (remove manually)")
    print("   - F821: Undefined names (fix logic)")
    print("   - E402: Module level imports not at top")
    print("\n💡 Run 'flake8 apps/backend/' to check remaining issues")


if __name__ == "__main__":
    main()
