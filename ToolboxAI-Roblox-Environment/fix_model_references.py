#!/usr/bin/env python3
"""
Fix all model references from gpt-4 to gpt-3.5-turbo
"""

import os
import re
from pathlib import Path

def fix_model_references(directory):
    """Update all gpt-4 references to gpt-3.5-turbo in Python files"""
    
    count = 0
    files_updated = []
    
    # Walk through all Python files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace model references
                    original_content = content
                    
                    # Replace model="gpt-4"
                    content = re.sub(r'model\s*=\s*"gpt-4"', 'model="gpt-3.5-turbo"', content)
                    
                    # Replace model='gpt-4'
                    content = re.sub(r"model\s*=\s*'gpt-4'", "model='gpt-3.5-turbo'", content)
                    
                    # Replace DEFAULT_MODEL = "gpt-4"
                    content = re.sub(r'DEFAULT_MODEL\s*=\s*"gpt-4"', 'DEFAULT_MODEL = "gpt-3.5-turbo"', content)
                    
                    # Only write if changes were made
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        count += 1
                        files_updated.append(str(file_path.relative_to(directory)))
                        print(f"Updated: {file_path.relative_to(directory)}")
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return count, files_updated

if __name__ == "__main__":
    # Fix models in agents directory
    agents_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/agents")
    
    print("Fixing model references in agents directory...")
    count, files = fix_model_references(agents_dir)
    
    print(f"\n✅ Updated {count} files:")
    for file in files:
        print(f"  - {file}")
    
    # Also fix in server directory if needed
    server_dir = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/server")
    
    print("\nFixing model references in server directory...")
    count2, files2 = fix_model_references(server_dir)
    
    if count2 > 0:
        print(f"\n✅ Updated {count2} files in server:")
        for file in files2:
            print(f"  - {file}")
    
    print(f"\n🎉 Total files updated: {count + count2}")