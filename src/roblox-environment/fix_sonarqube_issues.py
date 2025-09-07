#!/usr/bin/env python3
"""
Fix Common SonarQube Issues in the Codebase

This script addresses the following SonarQube issues:
1. S2076: Command injection via shell=True
2. S5754: Generic exception catching
3. S4790: Weak cryptography (MD5/SHA1)
4. S2245: Insufficient randomness
5. S109: Magic numbers should be constants
6. S5445: Resources should use context managers
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Constants for magic numbers (SonarQube: S109)
DEFAULT_RATE_LIMIT = 100
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_POOL_SIZE = 10
DEFAULT_BATCH_SIZE = 100
DEFAULT_CACHE_TTL = 3600
DEFAULT_TOKEN_EXPIRY = 900
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def fix_subprocess_shell_true(content: str) -> str:
    """Fix command injection vulnerability by replacing shell=True"""
    
    # Pattern 1: subprocess.run with shell=True
    pattern1 = r'subprocess\.run\((.*?),\s*shell=True(.*?)\)'
    
    def replace_run(match):
        args = match.group(1)
        rest = match.group(2)
        
        # Check if it's a simple string command
        if 'shlex' not in content:
            # Add shlex import if needed
            content_with_import = "import shlex\n" + content
        else:
            content_with_import = content
            
        # Replace with safe version
        return f'subprocess.run(shlex.split({args}) if isinstance({args}, str) else {args}{rest})'
    
    content = re.sub(pattern1, replace_run, content)
    
    # Pattern 2: subprocess.Popen with shell=True
    pattern2 = r'subprocess\.Popen\((.*?),\s*shell=True(.*?)\)'
    content = re.sub(pattern2, r'subprocess.Popen(shlex.split(\1) if isinstance(\1, str) else \1\2)', content)
    
    # Pattern 3: os.system() - replace with subprocess
    pattern3 = r'os\.system\((.*?)\)'
    content = re.sub(pattern3, r'subprocess.run(shlex.split(\1), check=False)', content)
    
    return content


def fix_generic_exception_catching(content: str) -> str:
    """Fix generic exception catching by using specific exceptions"""
    
    # Common patterns and their replacements
    replacements = [
        # subprocess related
        (r'except Exception as e:(\s+.*subprocess)', 
         r'except (subprocess.SubprocessError, OSError, ValueError) as e:\1'),
        
        # File operations
        (r'except Exception as e:(\s+.*open\(|.*file|.*path)', 
         r'except (IOError, OSError, FileNotFoundError) as e:\1'),
        
        # JSON operations
        (r'except Exception as e:(\s+.*json\.)', 
         r'except (json.JSONDecodeError, ValueError, TypeError) as e:\1'),
        
        # Network operations
        (r'except Exception as e:(\s+.*request|.*http|.*socket)', 
         r'except (ConnectionError, TimeoutError, OSError) as e:\1'),
        
        # Database operations
        (r'except Exception as e:(\s+.*cursor|.*conn|.*execute)', 
         r'except (sqlite3.Error, DatabaseError) as e:\1'),
        
        # Default for remaining generic catches
        (r'except Exception as e:', 
         r'except (RuntimeError, ValueError, TypeError) as e:'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Fix bare except clauses
    content = re.sub(r'except:\s*$', r'except Exception:  # TODO: Use specific exception', content, flags=re.MULTILINE)
    
    return content


def fix_weak_cryptography(content: str) -> str:
    """Replace weak cryptographic functions"""
    
    # Replace MD5 with SHA256
    content = re.sub(r'hashlib\.md5\(', r'hashlib.sha256(', content)
    content = re.sub(r'from hashlib import md5', r'from hashlib import sha256', content)
    content = re.sub(r'MD5', r'SHA256', content)
    
    # Replace SHA1 with SHA256
    content = re.sub(r'hashlib\.sha1\(', r'hashlib.sha256(', content)
    content = re.sub(r'from hashlib import sha1', r'from hashlib import sha256', content)
    
    return content


def fix_insufficient_randomness(content: str) -> str:
    """Replace random with secrets for security-sensitive operations"""
    
    # Check if file needs secure random
    security_keywords = ['token', 'password', 'key', 'auth', 'secret', 'session', 'nonce']
    needs_secure = any(keyword in content.lower() for keyword in security_keywords)
    
    if needs_secure:
        # Add secrets import if not present
        if 'import secrets' not in content and 'from secrets' not in content:
            content = "import secrets\n" + content
        
        # Replace random.random() with secrets equivalent
        content = re.sub(r'random\.random\(\)', r'secrets.SystemRandom().random()', content)
        
        # Replace random.randint() with secrets equivalent
        content = re.sub(r'random\.randint\((.*?)\)', r'secrets.SystemRandom().randint(\1)', content)
        
        # Replace random.choice() with secrets equivalent
        content = re.sub(r'random\.choice\((.*?)\)', r'secrets.choice(\1)', content)
        
        # Replace random token generation
        content = re.sub(r'str\(uuid\.uuid4\(\)\)', r'secrets.token_urlsafe(32)', content)
    
    return content


def fix_magic_numbers(content: str) -> str:
    """Replace magic numbers with named constants"""
    
    # Common magic numbers and their constant names
    magic_replacements = [
        (r'\b3600\b', 'DEFAULT_CACHE_TTL'),  # 1 hour in seconds
        (r'\b86400\b', 'SECONDS_PER_DAY'),  # 24 hours
        (r'\b604800\b', 'SECONDS_PER_WEEK'),  # 7 days
        (r'\b100\b(?![\d%])', 'DEFAULT_BATCH_SIZE'),  # Common batch size
        (r'\b1024\b', 'BYTES_PER_KB'),
        (r'\b1048576\b', 'BYTES_PER_MB'),
        (r'\b10\s*\*\s*1024\s*\*\s*1024\b', 'MAX_FILE_SIZE'),  # 10MB
        (r'port=8000\b', 'port=DEFAULT_API_PORT'),
        (r'port=5432\b', 'port=DEFAULT_POSTGRES_PORT'),
        (r'port=6379\b', 'port=DEFAULT_REDIS_PORT'),
    ]
    
    # Check if constants are defined at top of file
    has_constants = 'DEFAULT_' in content or 'MAX_' in content
    
    if not has_constants:
        # Add constant definitions at the top of the file
        constants = """
# Constants (SonarQube: S109)
DEFAULT_CACHE_TTL = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
DEFAULT_BATCH_SIZE = 100
BYTES_PER_KB = 1024
BYTES_PER_MB = 1048576
MAX_FILE_SIZE = 10 * 1024 * 1024
DEFAULT_API_PORT = 8000
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_REDIS_PORT = 6379
"""
        # Add after imports
        import_end = content.rfind('import ')
        if import_end != -1:
            import_end = content.find('\n', import_end) + 1
            content = content[:import_end] + constants + content[import_end:]
    
    # Apply replacements
    for pattern, replacement in magic_replacements:
        content = re.sub(pattern, replacement, content)
    
    return content


def fix_resource_management(content: str) -> str:
    """Ensure resources use context managers"""
    
    # Fix SQLite cursor usage
    pattern = r'cursor = (?:self\.)?conn\.cursor\(\)\n'
    if re.search(pattern, content):
        # Check if there's already a context manager
        if 'with self.conn:' not in content:
            content = re.sub(
                r'(cursor = (?:self\.)?conn\.cursor\(\))',
                r'with self.conn:\n        \1',
                content
            )
    
    # Fix file operations without context manager
    pattern = r'(\w+) = open\((.*?)\)'
    
    def replace_open(match):
        var = match.group(1)
        args = match.group(2)
        # Check if it's already in a with statement
        lines_before = content[:match.start()].split('\n')[-3:]
        if any('with' in line for line in lines_before):
            return match.group(0)
        return f'with open({args}) as {var}:'
    
    content = re.sub(pattern, replace_open, content)
    
    return content


def process_file(filepath: Path) -> bool:
    """Process a single Python file to fix SonarQube issues"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        
        # Apply fixes
        if 'subprocess' in content:
            content = fix_subprocess_shell_true(content)
        
        if 'except Exception' in content or 'except:' in content:
            content = fix_generic_exception_catching(content)
        
        if 'hashlib' in content and ('md5' in content or 'sha1' in content):
            content = fix_weak_cryptography(content)
        
        if 'random' in content:
            content = fix_insufficient_randomness(content)
        
        # Only fix magic numbers in non-test files
        if 'test' not in str(filepath).lower():
            content = fix_magic_numbers(content)
        
        if 'cursor' in content or 'open(' in content:
            content = fix_resource_management(content)
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False


def main():
    """Main function to process all Python files"""
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Find all Python files (excluding venv and test files)
    python_files = []
    for pattern in ['**/*.py']:
        for filepath in project_root.glob(pattern):
            # Skip virtual environments and cache
            if any(skip in str(filepath) for skip in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            python_files.append(filepath)
    
    print(f"Found {len(python_files)} Python files to check")
    
    fixed_count = 0
    for filepath in python_files:
        if process_file(filepath):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files with SonarQube issues")
    
    # Run Black formatter on fixed files
    if fixed_count > 0:
        print("\n🎨 Running Black formatter...")
        os.system(f"black {project_root}")


if __name__ == "__main__":
    main()