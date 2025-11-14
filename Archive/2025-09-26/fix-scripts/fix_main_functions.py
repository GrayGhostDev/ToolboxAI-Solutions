#!/usr/bin/env python3
"""
Fix main function indentation issues in test files.
"""

from pathlib import Path


def fix_main_function(file_path: Path) -> bool:
    """Fix async def main() function that has incorrect indentation."""
    
    try:
        with open(file_path) as f:
            lines = f.readlines()
        
        fixed = False
        i = 0
        while i < len(lines):
            # Look for async def main():
            if lines[i].strip() == 'async def main():':
                # Check if next line is a docstring
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('"""'):
                    docstring_line = i + 1
                    # Find the end of the docstring
                    if '"""' in lines[docstring_line][3:]:
                        # Single line docstring
                        # Add pass after it
                        if i + 2 < len(lines) and not lines[i + 2].strip().startswith('pass'):
                            lines.insert(i + 2, '    pass\n')
                            fixed = True
                    else:
                        # Multi-line docstring - find the end
                        j = docstring_line + 1
                        while j < len(lines) and '"""' not in lines[j]:
                            j += 1
                        # Add pass after the closing """
                        if j + 1 < len(lines) and not lines[j + 1].strip().startswith('pass'):
                            lines.insert(j + 1, '    pass\n')
                            fixed = True
            i += 1
        
        if fixed:
            with open(file_path, 'w') as f:
                f.writelines(lines)
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main execution."""
    project_root = Path(__file__).parent.parent
    
    problem_files = [
        'tests/e2e/test_e2e_integration.py',
        'tests/integration/test_agent_communication_integration.py',
        'tests/integration/test_agent_integration_new.py',
        'tests/integration/test_auth_system.py',
        'tests/integration/test_comprehensive_verification.py',
        'tests/integration/test_content_generation_pipeline.py',
        'tests/integration/test_core_agent_communication.py',
        'tests/integration/test_fastapi_comprehensive.py',
        'tests/integration/test_fastapi_integration.py',
        'tests/integration/test_full_integration.py'
    ]
    
    fixed_count = 0
    for file_path in problem_files:
        full_path = project_root / file_path
        if full_path.exists():
            if fix_main_function(full_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()