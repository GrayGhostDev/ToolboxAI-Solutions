#!/usr/bin/env python3
"""
Fix imports from apps.backend.config to use config.environment
"""

import os
import re
import sys

# Get the project root
PROJECT_ROOT = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Files to update
FILES_TO_UPDATE = [
    "apps/backend/roblox_server.py",
    "core/database/connection.py",
    "core/mcp/server.py",
    "core/mcp/auth_middleware.py",
    "database/connection.py",
    "apps/backend/rate_limit_manager.py",
    "apps/backend/performance.py",
]

def update_file(filepath):
    """Update imports in a single file"""
    full_path = os.path.join(PROJECT_ROOT, filepath)
    
    if not os.path.exists(full_path):
        print(f"  ⚠️  File not found: {filepath}")
        return False
    
    with open(full_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace server.config imports with config.environment
    patterns = [
        (r'from server\.config import Settings', 'from toolboxai_settings import settings'),
        (r'from server\.config import settings', 'from toolboxai_settings import settings\nsettings = settings'),
        (r'import apps.backend\.config', 'from toolboxai_settings import settings'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Also replace any usage of Settings() with settings
    content = re.sub(r'Settings\(\)', 'settings', content)
    
    if content != original_content:
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated: {filepath}")
        return True
    else:
        print(f"  ⏭️  No changes: {filepath}")
        return False

def main():
    print("Fixing server.config imports...")
    print(f"Working directory: {PROJECT_ROOT}")
    print()
    
    updated_count = 0
    for filepath in FILES_TO_UPDATE:
        if update_file(filepath):
            updated_count += 1
    
    print()
    print(f"✨ Updated {updated_count} files")

if __name__ == "__main__":
    main()