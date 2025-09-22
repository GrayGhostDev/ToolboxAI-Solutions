#!/usr/bin/env python3

"""
Comprehensive MUI _interopRequireDefault Fix Script
This script patches all MUI files that use the problematic require statement
and replaces it with an inline function definition for ESM/Vite compatibility
"""

import os
import glob
import re
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
MUI_DIR = os.path.join(BASE_DIR, "node_modules", "@mui")

# Pattern to match
OLD_PATTERN = 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");'

# Replacement text
NEW_PATTERN = '''// Patched: Define _interopRequireDefault inline to fix ESM/CommonJS issues
var _interopRequireDefault = function(obj) {
  return obj && obj.__esModule ? obj : { default: obj };
};'''

def patch_file(file_path):
    """Patch a single file if it contains the problematic require statement."""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file needs patching
        if OLD_PATTERN not in content:
            return 'already_patched'

        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{file_path}.backup-{timestamp}"
        shutil.copy2(file_path, backup_path)

        # Apply patch
        patched_content = content.replace(OLD_PATTERN, NEW_PATTERN)

        # Write patched content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(patched_content)

        return 'patched'

    except Exception as e:
        print(f"❌ Error patching {file_path}: {e}")
        return 'error'

def main():
    print("🔧 MUI _interopRequireDefault Comprehensive Patcher")
    print("=" * 50)
    print()

    if not os.path.exists(MUI_DIR):
        print(f"❌ MUI directory not found: {MUI_DIR}")
        return

    print("🔍 Finding JavaScript files in @mui packages...")

    # Find all JS files in @mui directory
    js_files = []
    for root, dirs, files in os.walk(MUI_DIR):
        for file in files:
            if file.endswith('.js'):
                js_files.append(os.path.join(root, file))

    print(f"📋 Found {len(js_files)} JavaScript files")

    # Count files that need patching
    files_to_patch = []
    for file_path in js_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if OLD_PATTERN in f.read():
                    files_to_patch.append(file_path)
        except:
            continue

    print(f"🎯 {len(files_to_patch)} files need patching")

    if len(files_to_patch) == 0:
        print("🎉 All files already patched!")
        return

    # Show breakdown by package
    print("\n📦 Breakdown by package:")
    package_counts = {}
    for file_path in files_to_patch:
        rel_path = os.path.relpath(file_path, MUI_DIR)
        package = rel_path.split('/')[0]
        package_counts[package] = package_counts.get(package, 0) + 1

    for package, count in sorted(package_counts.items()):
        print(f"   @mui/{package}: {count} files")

    print()
    response = input("🚀 Proceed with patching? (y/N): ")
    if response.lower() != 'y':
        print("❌ Aborted by user")
        return

    print("\n🔨 Patching files...")

    # Patch files
    stats = {'patched': 0, 'already_patched': 0, 'error': 0}
    for i, file_path in enumerate(files_to_patch, 1):
        result = patch_file(file_path)
        stats[result] += 1

        rel_path = os.path.relpath(file_path, MUI_DIR)
        if result == 'patched':
            print(f"✅ [{i:3d}/{len(files_to_patch)}] Patched: @mui/{rel_path}")
        elif result == 'already_patched':
            print(f"⏭️  [{i:3d}/{len(files_to_patch)}] Already patched: @mui/{rel_path}")
        else:
            print(f"❌ [{i:3d}/{len(files_to_patch)}] Failed: @mui/{rel_path}")

        # Progress indicator
        if i % 10 == 0:
            print(f"📊 Progress: {i}/{len(files_to_patch)} files processed")

    print("\n🎉 Patching completed!")
    print("\n📊 Statistics:")
    print(f"   Files patched: {stats['patched']}")
    print(f"   Already patched: {stats['already_patched']}")
    print(f"   Errors: {stats['error']}")

    # Verify patches
    print("\n🔍 Verifying patches...")
    failed_files = []
    for file_path in files_to_patch:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if OLD_PATTERN in f.read():
                    failed_files.append(file_path)
        except:
            continue

    if not failed_files:
        print("✅ All patches verified successfully!")
    else:
        print(f"❌ {len(failed_files)} files failed verification:")
        for file_path in failed_files[:5]:  # Show first 5
            rel_path = os.path.relpath(file_path, MUI_DIR)
            print(f"   @mui/{rel_path}")
        if len(failed_files) > 5:
            print(f"   ... and {len(failed_files) - 5} more")

    print("\n💡 Next steps:")
    print("   1. Test your dashboard: cd apps/dashboard && npm run dev")
    print("   2. Check browser console for any remaining errors")
    print("   3. Backup files are saved with timestamp suffix")
    print("\n🎯 Patch script completed!")

if __name__ == "__main__":
    main()