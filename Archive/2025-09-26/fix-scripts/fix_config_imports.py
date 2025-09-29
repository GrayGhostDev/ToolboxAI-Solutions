#!/usr/bin/env python3
"""Fix config.environment imports to use toolboxai_settings."""

import os
import re
from pathlib import Path

def fix_config_imports(file_path):
    """Fix config imports in a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace config.environment imports with toolboxai_settings
    replacements = [
        (r'from config\.environment import get_environment_config', 'from toolboxai_settings import settings'),
        (r'from config\.environment import EnvironmentConfig', 'from toolboxai_settings import settings'),
        (r'import config\.environment', 'import toolboxai_settings'),
        (r'config\.environment\.get_environment_config\(\)', 'toolboxai_settings.settings'),
        (r'config\.environment\.EnvironmentConfig', 'toolboxai_settings.settings'),
        (r'get_environment_config\(\)', 'settings'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix all config imports."""
    root_dir = Path('/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions')
    
    # Files that need fixing
    files_to_fix = [
        'scripts/maintenance/fix_server_config_imports.py',
        'scripts/maintenance/verify_environment.py',
        'tests/integration/conftest.py',
        'apps/backend/services/roblox.py',
        'core/mcp/auth_middleware.py',
        'core/agents/database_integration.py',
        'core/database/connection.py',
        'database/connection.py',
        'core/agents/quiz_agent.py',
        'apps/backend/core/config.py',
        'core/mcp/server.py',
        'apps/backend/core/performance.py',
        'apps/backend/core/security/rate_limiter.py',
        'core/agents/content_agent.py',
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        full_path = root_dir / file_path
        if full_path.exists():
            if fix_config_imports(full_path):
                print(f"✅ Fixed: {file_path}")
                fixed_count += 1
            else:
                print(f"⏭️  No changes needed: {file_path}")
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\n📊 Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
