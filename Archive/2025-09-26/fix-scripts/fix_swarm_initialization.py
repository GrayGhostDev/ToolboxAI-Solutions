#!/usr/bin/env python3
"""
Fix SwarmController initialization issues across the codebase.

This script updates all incorrect SwarmController() calls to use the proper
factory function with required dependencies.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_files_with_swarm_init(root_dir: str = ".") -> List[Path]:
    """Find all Python files with SwarmController() initialization."""
    files_to_fix = []
    
    # Files known to have issues
    known_files = [
        "core/coordinators/main_coordinator.py",
        "core/coordinators/error_coordinator.py",
        "core/coordinators/workflow_coordinator.py",
        "core/coordinators/sync_coordinator.py",
    ]
    
    for file_path in known_files:
        full_path = Path(root_dir) / file_path
        if full_path.exists():
            files_to_fix.append(full_path)
    
    return files_to_fix


def fix_swarm_initialization(file_path: Path) -> bool:
    """Fix SwarmController initialization in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to find SwarmController() calls
        pattern = r'(\s+)(?:self\.)?swarm_controller\s*=\s*SwarmController\(\)'
        
        # Check if file needs fixing
        if not re.search(pattern, content):
            return False
        
        # Add import if not present
        if "from ..swarm.swarm_factory import" not in content:
            # Find the right place to add import
            import_section = re.search(r'(from \.\.swarm\.swarm_controller import SwarmController)', content)
            if import_section:
                content = content.replace(
                    import_section.group(1),
                    import_section.group(1) + "\n                from ..swarm.swarm_factory import create_test_swarm_controller"
                )
        
        # Replace SwarmController() with factory call
        replacement = r'\1self.swarm_controller = create_test_swarm_controller()'
        content = re.sub(pattern, replacement, content)
        
        # Also fix standalone controller = SwarmController()
        pattern2 = r'(\s+)controller\s*=\s*SwarmController\(\)'
        replacement2 = r'\1controller = create_test_swarm_controller()'
        content = re.sub(pattern2, replacement2, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix SwarmController initialization issues."""
    print("🔧 Fixing SwarmController initialization issues...")
    print("=" * 60)
    
    root_dir = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
    os.chdir(root_dir)
    
    # Find files to fix
    files_to_fix = find_files_with_swarm_init(".")
    print(f"Found {len(files_to_fix)} files to check\n")
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if fix_swarm_initialization(file_path):
            fixed_count += 1
            print(f"✅ Fixed: {file_path}")
        else:
            print(f"⏭️  Skipped: {file_path} (no changes needed)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   Files checked: {len(files_to_fix)}")
    print(f"   Files fixed: {fixed_count}")
    
    if fixed_count > 0:
        print("\n✨ SwarmController initialization issues fixed!")
        print("   Run tests to verify the fixes")
    else:
        print("\n✅ No SwarmController initialization issues found!")


if __name__ == "__main__":
    main()