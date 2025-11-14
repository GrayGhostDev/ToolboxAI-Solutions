#!/usr/bin/env python3
"""
Fix final indentation errors in test files.
These are all cases where a function definition has no body.
"""

import re
from pathlib import Path


def fix_empty_function_bodies(content: str) -> str:
    """Add 'pass' to functions that have no body."""
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this is a function definition
        if re.match(r'^(async\s+)?def\s+\w+\([^)]*\):', line.strip()):
            # Check if next line is a docstring or empty
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line is a docstring at wrong indentation level
                if next_line.strip().startswith('"""') and not next_line.startswith('    '):
                    # This is a function with only a docstring at wrong indentation
                    # Add proper indentation to docstring
                    i += 1
                    fixed_lines.append('    ' + next_line.strip())
                    # Check if docstring continues
                    if '"""' not in next_line[3:]:
                        # Multi-line docstring
                        i += 1
                        while i < len(lines) and '"""' not in lines[i]:
                            fixed_lines.append('    ' + lines[i].strip())
                            i += 1
                        if i < len(lines):
                            fixed_lines.append('    ' + lines[i].strip())
                    # Add pass after docstring
                    fixed_lines.append('    pass')
        
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_main_functions(content: str) -> str:
    """Fix main functions that may be missing pass statements."""
    
    # Pattern for main functions at end of file
    pattern = r'(if __name__ == "__main__":\s*\n)(async\s+)?def main\(\):\s*\n\s*"""[^"]*"""'
    
    def replacer(match):
        return match.group(0) + '\n    pass'
    
    content = re.sub(pattern, replacer, content)
    
    # Also fix standalone main functions
    pattern2 = r'^(async\s+)?def main\(\):\s*\n\s*"""[^"]*"""$'
    content = re.sub(pattern2, r'\g<0>\n    pass', content, flags=re.MULTILINE)
    
    return content

def fix_file(file_path: Path) -> bool:
    """Fix a single file."""
    try:
        content = file_path.read_text()
        original = content
        
        content = fix_empty_function_bodies(content)
        content = fix_main_functions(content)
        
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
    
    # Files with known indentation issues from the error log
    problem_files = [
        "tests/e2e/test_e2e_integration.py",
        "tests/integration/test_agent_communication_integration.py", 
        "tests/integration/test_agent_integration_new.py",
        "tests/integration/test_auth_system.py",
        "tests/integration/test_comprehensive_verification.py",
        "tests/integration/test_content_generation_pipeline.py",
        "tests/integration/test_core_agent_communication.py",
        "tests/integration/test_fastapi_comprehensive.py",
        "tests/integration/test_fastapi_integration.py",
        "tests/integration/test_full_integration.py",
        "tests/integration/test_mcp_integration.py",
        "tests/integration/test_socketio.py",
        "tests/integration/test_websocket_integration.py",
        "tests/test_roblox_plugin.py"
    ]
    
    fixed_count = 0
    
    for file_path in problem_files:
        full_path = project_root / file_path
        if full_path.exists():
            if fix_file(full_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1
        else:
            print(f"Not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()