#!/usr/bin/env python3
"""
Fix syntax errors introduced by the previous fix script.
"""

import re
from pathlib import Path


def fix_duplicate_default_parameter(content: str) -> str:
    """Fix duplicate 'default' parameter in json.dumps calls."""
    
    # Fix patterns like: json.dumps(..., default=str, default=make_json_serializable)
    content = re.sub(
        r'json\.dumps\(([^)]+),\s*default=[^,)]+,\s*default=make_json_serializable\)',
        r'json.dumps(\1, default=make_json_serializable)',
        content
    )
    
    # Fix patterns like: datetime.now(, default=make_json_serializable)
    content = re.sub(
        r'datetime\.now\(,\s*default=make_json_serializable\)',
        r'datetime.now()',
        content
    )
    
    # Fix patterns like: time.time(, default=make_json_serializable)
    content = re.sub(
        r'time\.time\(,\s*default=make_json_serializable\)',
        r'time.time()',
        content
    )
    
    # Fix patterns like: uuid.uuid4(, default=make_json_serializable)
    content = re.sub(
        r'uuid\.uuid4\(,\s*default=make_json_serializable\)',
        r'uuid.uuid4()',
        content
    )
    
    return content

def fix_indentation_errors(content: str) -> str:
    """Fix indentation errors in async def statements."""
    
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check if this is an async def with incorrect indentation
        if line.strip().startswith('async def ') and i > 0:
            # Check the previous non-empty line
            prev_line_idx = i - 1
            while prev_line_idx >= 0 and not lines[prev_line_idx].strip():
                prev_line_idx -= 1
            
            if prev_line_idx >= 0:
                prev_line = lines[prev_line_idx]
                # If previous line is indented but this isn't properly aligned
                if prev_line.startswith('    ') and not line.startswith('    '):
                    # Add proper indentation
                    line = '    ' + line.lstrip()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file(file_path: Path) -> bool:
    """Fix a single file."""
    try:
        content = file_path.read_text()
        original = content
        
        content = fix_duplicate_default_parameter(content)
        content = fix_indentation_errors(content)
        
        if content != original:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main execution."""
    project_root = Path(__file__).parent.parent
    
    # Files with known issues
    problem_files = [
        "tests/integration/test_advanced_supervisor.py",
        "tests/integration/test_mcp_integration.py",
        "tests/performance/test_load.py",
        "tests/test_error_handling.py",
        "tests/unit/core/test_server.py"
    ]
    
    fixed_count = 0
    
    for file_path in problem_files:
        full_path = project_root / file_path
        if full_path.exists():
            if fix_file(full_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1
    
    # Also scan for any other files with these patterns
    for test_file in project_root.rglob("test_*.py"):
        if str(test_file.relative_to(project_root)) not in problem_files:
            if fix_file(test_file):
                print(f"Fixed: {test_file.relative_to(project_root)}")
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()