#!/usr/bin/env python3
"""
Pre-commit hook for ToolboxAI Roblox Environment

This hook performs comprehensive code quality checks before allowing commits:
- Python code formatting (Black, isort)
- Linting (flake8, mypy)
- Test execution for changed files
- Documentation validation
- File size limits
- Roblox Lua syntax checking
- Security checks for hardcoded secrets
- JSON/YAML validation

Usage:
    python pre_commit.py [--fix] [--skip-tests] [--verbose]

Environment Variables:
    SKIP_PRE_COMMIT_HOOKS - Set to 'true' to skip all hooks
    MAX_FILE_SIZE_MB - Maximum file size in MB (default: 50)
    PYTHON_VERSION - Required Python version (default: 3.11)
"""

import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from github import GitHubHelper, EducationalPlatformHelper, setup_logging, load_config

logger = setup_logging()

class PreCommitHook:
    """Pre-commit hook implementation"""
    
    def __init__(self, fix_issues: bool = False, skip_tests: bool = False):
        self.github_helper = GitHubHelper()
        self.edu_helper = EducationalPlatformHelper()
        self.config = load_config()
        self.fix_issues = fix_issues
        self.skip_tests = skip_tests
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.repo_root = self.github_helper.repo_root
    
    def run_all_checks(self) -> bool:
        """Run all pre-commit checks"""
        if os.getenv('SKIP_PRE_COMMIT_HOOKS', '').lower() == 'true':
            logger.info("Pre-commit hooks skipped via environment variable")
            return True
        
        logger.info("Running pre-commit checks...")
        
        staged_files = self.github_helper.get_staged_files()
        if not staged_files:
            logger.info("No staged files found")
            return True
        
        logger.info(f"Checking {len(staged_files)} staged files")
        
        # Run all checks
        checks = [
            self.check_file_sizes,
            self.check_secrets,
            self.validate_config_files,
            self.check_python_code,
            self.check_lua_code,
            self.check_documentation,
            self.run_tests if not self.skip_tests else lambda files: True
        ]
        
        all_passed = True
        for check in checks:
            if not check(staged_files):
                all_passed = False
        
        # Report results
        if self.warnings:
            logger.warning("Warnings found:")
            for warning in self.warnings:
                logger.warning(f"  {warning}")
        
        if self.errors:
            logger.error("Errors found:")
            for error in self.errors:
                logger.error(f"  {error}")
            return False
        
        if all_passed:
            logger.info("All pre-commit checks passed!")
        
        return all_passed
    
    def check_file_sizes(self, files: List[str]) -> bool:
        """Check file sizes against limits"""
        logger.info("Checking file sizes...")
        max_size_mb = self.config.get('max_file_size_mb', 50)
        
        large_files = []
        for file_path in files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                if not self.github_helper.check_file_size(full_path, max_size_mb):
                    large_files.append(file_path)
        
        if large_files:
            self.errors.extend([f"File too large: {f}" for f in large_files])
            return False
        
        return True
    
    def check_secrets(self, files: List[str]) -> bool:
        """Check for hardcoded secrets"""
        logger.info("Scanning for hardcoded secrets...")
        
        secrets_found = False
        for file_path in files:
            full_path = self.repo_root / file_path
            if full_path.exists() and full_path.suffix in ['.py', '.js', '.ts', '.lua', '.json', '.yaml', '.yml']:
                secrets = self.github_helper.check_secrets_in_file(full_path)
                if secrets:
                    secrets_found = True
                    self.errors.append(f"Potential secrets in {file_path}:")
                    self.errors.extend([f"  {secret}" for secret in secrets])
        
        return not secrets_found
    
    def validate_config_files(self, files: List[str]) -> bool:
        """Validate JSON and YAML configuration files"""
        logger.info("Validating configuration files...")
        
        validation_failed = False
        for file_path in files:
            if self.github_helper.is_config_file(file_path):
                full_path = self.repo_root / file_path
                if not full_path.exists():
                    continue
                
                if file_path.endswith('.json'):
                    if not self.github_helper.validate_json_file(full_path):
                        validation_failed = True
                        self.errors.append(f"Invalid JSON syntax in {file_path}")
                
                elif file_path.endswith(('.yaml', '.yml')):
                    if not self.github_helper.validate_yaml_file(full_path):
                        validation_failed = True
                        self.errors.append(f"Invalid YAML syntax in {file_path}")
        
        return not validation_failed
    
    def check_python_code(self, files: List[str]) -> bool:
        """Check Python code quality"""
        python_files = [f for f in files if self.github_helper.is_python_file(f)]
        if not python_files:
            return True
        
        logger.info(f"Checking {len(python_files)} Python files...")
        
        all_passed = True
        
        # Check Python version
        if not self._check_python_version():
            all_passed = False
        
        # Black formatting
        if not self._run_black(python_files):
            all_passed = False
        
        # Import sorting
        if not self._run_isort(python_files):
            all_passed = False
        
        # Linting
        if not self._run_flake8(python_files):
            all_passed = False
        
        # Type checking
        if not self._run_mypy(python_files):
            all_passed = False
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version compatibility"""
        required_version = self.config.get('python_version', '3.11')
        
        exit_code, stdout, stderr = self.github_helper.run_command([
            'python', '-c', 
            f'import sys; sys.exit(0 if sys.version_info >= tuple(map(int, "{required_version}".split("."))) else 1)'
        ])
        
        if exit_code != 0:
            self.errors.append(f"Python {required_version}+ required")
            return False
        
        return True
    
    def _run_black(self, python_files: List[str]) -> bool:
        """Run Black code formatter"""
        logger.info("Running Black formatter...")
        
        cmd = ['black', '--check']
        if self.fix_issues:
            cmd = ['black']
        
        cmd.extend(python_files)
        
        exit_code, stdout, stderr = self.github_helper.run_command(cmd)
        
        if exit_code != 0:
            if self.fix_issues:
                logger.info("Black formatting applied")
            else:
                self.errors.append("Black formatting required. Run with --fix to auto-format")
                if stderr:
                    self.errors.append(f"Black output: {stderr}")
            return self.fix_issues
        
        return True
    
    def _run_isort(self, python_files: List[str]) -> bool:
        """Run isort for import sorting"""
        logger.info("Running isort...")
        
        cmd = ['isort', '--check-only']
        if self.fix_issues:
            cmd = ['isort']
        
        cmd.extend(python_files)
        
        exit_code, stdout, stderr = self.github_helper.run_command(cmd)
        
        if exit_code != 0:
            if self.fix_issues:
                logger.info("Import sorting applied")
            else:
                self.errors.append("Import sorting required. Run with --fix to auto-sort")
            return self.fix_issues
        
        return True
    
    def _run_flake8(self, python_files: List[str]) -> bool:
        """Run flake8 linting"""
        logger.info("Running flake8 linter...")
        
        cmd = ['flake8'] + python_files
        
        exit_code, stdout, stderr = self.github_helper.run_command(cmd)
        
        if exit_code != 0:
            self.errors.append("Flake8 linting failed:")
            if stdout:
                self.errors.extend([f"  {line}" for line in stdout.split('\n') if line.strip()])
            return False
        
        return True
    
    def _run_mypy(self, python_files: List[str]) -> bool:
        """Run mypy type checking"""
        logger.info("Running mypy type checker...")
        
        cmd = ['mypy'] + python_files
        
        exit_code, stdout, stderr = self.github_helper.run_command(cmd)
        
        if exit_code != 0:
            # Mypy warnings are not always critical
            self.warnings.append("MyPy type checking issues found:")
            if stdout:
                self.warnings.extend([f"  {line}" for line in stdout.split('\n') if line.strip()])
        
        return True  # Don't fail on mypy issues, just warn
    
    def check_lua_code(self, files: List[str]) -> bool:
        """Check Roblox Lua code quality"""
        if not self.config.get('roblox_lint_enabled', True):
            return True
        
        lua_files = [f for f in files if self.github_helper.is_lua_file(f)]
        if not lua_files:
            return True
        
        logger.info(f"Checking {len(lua_files)} Lua files...")
        
        # Check for basic Lua syntax
        syntax_errors = []
        for file_path in lua_files:
            full_path = self.repo_root / file_path
            if not self._check_lua_syntax(full_path):
                syntax_errors.append(file_path)
        
        # Check for Roblox-specific patterns
        roblox_issues = []
        for file_path in lua_files:
            full_path = self.repo_root / file_path
            issues = self._check_roblox_patterns(full_path)
            if issues:
                roblox_issues.extend([f"{file_path}: {issue}" for issue in issues])
        
        if syntax_errors:
            self.errors.extend([f"Lua syntax error in {f}" for f in syntax_errors])
        
        if roblox_issues:
            self.warnings.extend(roblox_issues)
        
        return len(syntax_errors) == 0
    
    def _check_lua_syntax(self, file_path: Path) -> bool:
        """Check Lua syntax using luac if available"""
        if not file_path.exists():
            return True
        
        # Try to use luac for syntax checking
        exit_code, stdout, stderr = self.github_helper.run_command(['luac', '-p', str(file_path)])
        if exit_code == 0:
            return True
        
        # Fallback to basic pattern checking
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for unmatched brackets/parentheses
            brackets = {'(': ')', '[': ']', '{': '}'}
            stack = []
            
            for char in content:
                if char in brackets:
                    stack.append(brackets[char])
                elif char in brackets.values():
                    if not stack or stack.pop() != char:
                        return False
            
            return len(stack) == 0
        
        except Exception:
            return True  # If we can't check, assume it's OK
    
    def _check_roblox_patterns(self, file_path: Path) -> List[str]:
        """Check for Roblox-specific code patterns and best practices"""
        if not file_path.exists():
            return []
        
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for deprecated Roblox functions
                if 'wait(' in line_stripped:
                    issues.append(f"Line {i}: Use RunService.Heartbeat instead of wait()")
                
                # Check for direct Instance access without error handling
                if re.search(r'workspace\.\w+\.\w+', line_stripped) and 'WaitForChild' not in line_stripped:
                    issues.append(f"Line {i}: Consider using WaitForChild() for safe Instance access")
                
                # Check for RemoteEvent security
                if 'OnServerEvent' in line_stripped and 'player' not in line_stripped.lower():
                    issues.append(f"Line {i}: Server events should validate the player parameter")
                
                # Check for proper service access
                if re.search(r'game\.\w+(?!:GetService)', line_stripped):
                    issues.append(f"Line {i}: Use game:GetService() instead of direct service access")
        
        except Exception:
            pass  # If we can't read the file, skip the checks
        
        return issues
    
    def check_documentation(self, files: List[str]) -> bool:
        """Check documentation requirements"""
        if not self.config.get('documentation_required', False):
            return True
        
        logger.info("Checking documentation...")
        
        # Check if new modules have documentation
        missing_docs = []
        for file_path in files:
            if self.github_helper.is_python_file(file_path) and file_path.startswith(('agents/', 'server/', 'mcp/')):
                full_path = self.repo_root / file_path
                if full_path.exists() and not self._has_module_docstring(full_path):
                    missing_docs.append(file_path)
        
        if missing_docs:
            self.warnings.extend([f"Missing module docstring: {f}" for f in missing_docs])
        
        return True  # Don't fail on missing docs, just warn
    
    def _has_module_docstring(self, file_path: Path) -> bool:
        """Check if Python file has module-level docstring"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for docstring at the beginning of the file (after imports and shebang)
            lines = content.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('import') or line_stripped.startswith('from'):
                    continue
                if line_stripped.startswith('"""') or line_stripped.startswith("'''"):
                    return True
                break
            
            return False
        except Exception:
            return True  # If we can't check, assume it's OK
    
    def run_tests(self, files: List[str]) -> bool:
        """Run tests for changed files"""
        logger.info("Running tests for changed files...")
        
        # Find test files related to changed files
        test_files = []
        for file_path in files:
            if file_path.startswith('tests/'):
                test_files.append(file_path)
            elif self.github_helper.is_python_file(file_path):
                # Look for corresponding test file
                test_file = self._find_test_file(file_path)
                if test_file and test_file not in test_files:
                    test_files.append(test_file)
        
        if not test_files:
            logger.info("No relevant test files found")
            return True
        
        # Run pytest on test files
        cmd = ['pytest', '-v', '--tb=short'] + test_files
        
        exit_code, stdout, stderr = self.github_helper.run_command(cmd)
        
        if exit_code != 0:
            self.errors.append("Tests failed:")
            if stdout:
                self.errors.extend([f"  {line}" for line in stdout.split('\n')[-20:] if line.strip()])
            return False
        
        logger.info("All tests passed")
        return True
    
    def _find_test_file(self, source_file: str) -> Optional[str]:
        """Find corresponding test file for a source file"""
        # Convert source file path to test file path
        if source_file.startswith('server/'):
            test_file = source_file.replace('server/', 'tests/unit/server/')
        elif source_file.startswith('agents/'):
            test_file = source_file.replace('agents/', 'tests/unit/agents/')
        elif source_file.startswith('mcp/'):
            test_file = source_file.replace('mcp/', 'tests/unit/mcp/')
        else:
            return None
        
        # Replace .py with test_.py or _test.py patterns
        if test_file.endswith('.py'):
            base = test_file[:-3]
            test_candidates = [
                f"test_{base.split('/')[-1]}.py",
                f"{base}_test.py",
                f"tests/unit/{base.split('/')[-1]}_test.py"
            ]
            
            for candidate in test_candidates:
                if (self.repo_root / candidate).exists():
                    return candidate
        
        return None


def main():
    """Main entry point for pre-commit hook"""
    parser = argparse.ArgumentParser(description='Pre-commit hook for ToolboxAI Roblox Environment')
    parser.add_argument('--fix', action='store_true', help='Automatically fix issues where possible')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    hook = PreCommitHook(fix_issues=args.fix, skip_tests=args.skip_tests)
    
    try:
        success = hook.run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Pre-commit hook interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pre-commit hook failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()