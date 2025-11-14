#!/usr/bin/env python3
"""
Pre-push hook for ToolboxAI Roblox Environment

This hook performs security and quality checks before pushing:
- Security scanning for vulnerabilities
- API key detection and prevention
- Large file prevention
- Branch protection enforcement
- Test coverage verification
- Breaking change detection

Usage:
    python pre_push.py [--force] [--skip-security] [--verbose]

Environment Variables:
    SKIP_PRE_PUSH_HOOKS - Set to 'true' to skip all hooks
    MIN_TEST_COVERAGE - Minimum test coverage percentage (default: 80)
    MAX_FILE_SIZE_MB - Maximum file size in MB (default: 100)
    SECURITY_SCAN_ENABLED - Set to 'false' to disable security scanning
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from github import EducationalPlatformHelper, GitHubHelper, load_config, setup_logging

logger = setup_logging()

class PrePushHook:
    """Pre-push hook implementation"""
    
    def __init__(self, force_push: bool = False, skip_security: bool = False):
        self.github_helper = GitHubHelper()
        self.edu_helper = EducationalPlatformHelper()
        self.config = load_config()
        self.force_push = force_push
        self.skip_security = skip_security
        self.repo_root = self.github_helper.repo_root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        
        # Get push information
        self.local_branch = self._get_local_branch()
        self.remote_branch = self._get_remote_branch()
        self.commits_to_push = self._get_commits_to_push()
    
    def run_all_checks(self) -> bool:
        """Run all pre-push checks"""
        if os.getenv('SKIP_PRE_PUSH_HOOKS', '').lower() == 'true':
            logger.info("Pre-push hooks skipped via environment variable")
            return True
        
        logger.info("Running pre-push checks...")
        logger.info(f"Local branch: {self.local_branch}")
        logger.info(f"Remote branch: {self.remote_branch}")
        logger.info(f"Commits to push: {len(self.commits_to_push)}")
        
        if not self.commits_to_push:
            logger.info("No commits to push")
            return True
        
        # Run all checks
        checks = [
            self.check_branch_protection,
            self.scan_for_security_issues,
            self.detect_api_keys,
            self.check_file_sizes,
            self.verify_test_coverage,
            self.detect_breaking_changes,
            self.validate_commit_messages,
            self.check_educational_standards
        ]
        
        all_passed = True
        for check in checks:
            if not check():
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
            
            if not self.force_push:
                logger.error("Push blocked due to errors. Use --force to override.")
                return False
        
        if all_passed:
            logger.info("All pre-push checks passed!")
        
        return all_passed or self.force_push
    
    def _get_local_branch(self) -> str:
        """Get current local branch"""
        return self.github_helper.get_git_branch()
    
    def _get_remote_branch(self) -> str:
        """Get remote branch being pushed to"""
        # Try to get from git push arguments (if available)
        # For now, assume same as local branch
        return self.local_branch
    
    def _get_commits_to_push(self) -> list[str]:
        """Get list of commits that will be pushed"""
        exit_code, stdout, stderr = self.github_helper.run_command([
            'git', 'log', f'origin/{self.remote_branch}..HEAD', '--pretty=format:%H'
        ])
        
        if exit_code == 0 and stdout:
            return stdout.strip().split('\n')
        return []
    
    def check_branch_protection(self) -> bool:
        """Check branch protection rules"""
        logger.info("Checking branch protection rules...")
        
        protected_branches = ['main', 'master', 'production', 'release']
        
        if self.remote_branch in protected_branches:
            # Check if this is a direct push to protected branch
            if len(self.commits_to_push) > 1:
                self.errors.append(f"Direct push to protected branch '{self.remote_branch}' with multiple commits")
                return False
            
            # Check if proper review process was followed
            if not self._check_commit_approval():
                self.warnings.append(f"Pushing to protected branch '{self.remote_branch}' without clear approval")
        
        return True
    
    def _check_commit_approval(self) -> bool:
        """Check if commits have been properly reviewed/approved"""
        # This would integrate with GitHub API to check PR status
        # For now, check commit messages for review indicators
        for commit in self.commits_to_push:
            commit_msg = self.github_helper.get_commit_message(commit)
            if any(indicator in commit_msg.lower() for indicator in ['reviewed-by:', 'approved-by:', 'co-authored-by:']):
                return True
        return False
    
    def scan_for_security_issues(self) -> bool:
        """Run security scanning on code changes"""
        if self.skip_security or not self.config.get('security_scan_enabled', True):
            logger.info("Security scanning disabled")
            return True
        
        logger.info("Running security scans...")
        
        # Get all changed files in commits to push
        changed_files = set()
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            changed_files.update(files)
        
        security_issues = []
        
        # Scan Python files with bandit if available
        python_files = [f for f in changed_files if self.github_helper.is_python_file(f)]
        if python_files:
            security_issues.extend(self._scan_python_security(python_files))
        
        # Scan for common security patterns
        for file_path in changed_files:
            if file_path.endswith(('.py', '.js', '.ts', '.lua', '.json', '.yaml')):
                security_issues.extend(self._scan_file_security_patterns(file_path))
        
        if security_issues:
            self.errors.extend([f"Security issue: {issue}" for issue in security_issues])
            return False
        
        return True
    
    def _scan_python_security(self, python_files: list[str]) -> list[str]:
        """Scan Python files with bandit security scanner"""
        try:
            cmd = ['bandit', '-f', 'json', '-q'] + python_files
            exit_code, stdout, stderr = self.github_helper.run_command(cmd)
            
            if exit_code == 0 and stdout:
                try:
                    results = json.loads(stdout)
                    issues = []
                    for result in results.get('results', []):
                        severity = result.get('issue_severity', 'UNKNOWN')
                        if severity in ['HIGH', 'MEDIUM']:
                            issues.append(f"{result['filename']}:{result['line_number']} - {result['issue_text']}")
                    return issues
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.warning(f"Bandit security scan failed: {e}")
        
        return []
    
    def _scan_file_security_patterns(self, file_path: str) -> list[str]:
        """Scan file for common security anti-patterns"""
        full_path = self.repo_root / file_path
        if not full_path.exists():
            return []
        
        issues = []
        
        try:
            with open(full_path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Security patterns to check
            security_patterns = {
                r'eval\s*\(': 'Use of ast.literal_eval() function is dangerous',
                r'exec\s*\(': 'Use of exec() function is dangerous',
                r'os\.system\s*\(': 'Use of os.system() can be dangerous',
                r'subprocess\.call\s*\([^)]*shell\s*=\s*True': 'Shell injection vulnerability',
                r'sql.*=.*\+.*%': 'Potential SQL injection vulnerability',
                r'password\s*=\s*["\'][^"\']*["\']': 'Hardcoded password detected',
                r'api_key\s*=\s*["\'][^"\']*["\']': 'Hardcoded API key detected',
                r'secret\s*=\s*["\'][^"\']*["\']': 'Hardcoded secret detected',
                r'token\s*=\s*["\'][^"\']*["\']': 'Hardcoded token detected',
                r'mysql://|postgresql://|mongodb://': 'Database connection string in code',
                r'http://(?!localhost|127\.0\.0\.1)': 'Unencrypted HTTP connection',
                r'disable.*ssl|verify.*false': 'SSL verification disabled',
                r'md5|sha1(?![\d])[^\w]': 'Weak cryptographic hash function'
            }
            
            for i, line in enumerate(lines, 1):
                for pattern, message in security_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip if it's in a comment
                        if not line.strip().startswith('#') and not line.strip().startswith('//'):
                            issues.append(f"{file_path}:{i} - {message}")
        
        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")
        
        return issues
    
    def detect_api_keys(self) -> bool:
        """Detect and prevent API keys from being pushed"""
        logger.info("Scanning for API keys...")
        
        # Get all changed files
        changed_files = set()
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            changed_files.update(files)
        
        api_key_patterns = [
            r'sk-[A-Za-z0-9]{48}',  # OpenAI API keys
            r'ghp_[A-Za-z0-9]{36}',  # GitHub personal access tokens
            r'gho_[A-Za-z0-9]{36}',  # GitHub OAuth tokens
            r'AIza[0-9A-Za-z-_]{35}',  # Google API keys
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key IDs
            r'ya29\.[0-9A-Za-z\-_]+',  # Google OAuth tokens
            r'[0-9a-fA-F]{40}',  # Generic 40-char hex (like GitHub tokens)
            r'[0-9a-fA-F]{64}',  # Generic 64-char hex
        ]
        
        api_keys_found = []
        
        for file_path in changed_files:
            full_path = self.repo_root / file_path
            if full_path.exists() and full_path.suffix in ['.py', '.js', '.ts', '.lua', '.json', '.yaml', '.yml', '.env']:
                keys = self._scan_file_for_keys(full_path, api_key_patterns)
                if keys:
                    api_keys_found.extend([f"{file_path}: {key}" for key in keys])
        
        if api_keys_found:
            self.errors.append("API keys detected in files:")
            self.errors.extend([f"  {key}" for key in api_keys_found])
            return False
        
        return True
    
    def _scan_file_for_keys(self, file_path: Path, patterns: list[str]) -> list[str]:
        """Scan file for API key patterns"""
        try:
            with open(file_path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            found_keys = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#') or line.strip().startswith('//'):
                    continue
                
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        # Mask the key for logging
                        key = match.group()
                        masked_key = key[:8] + '*' * (len(key) - 16) + key[-8:] if len(key) > 16 else '*' * len(key)
                        found_keys.append(f"Line {i}: {masked_key}")
            
            return found_keys
        
        except Exception as e:
            logger.warning(f"Error scanning {file_path} for keys: {e}")
            return []
    
    def check_file_sizes(self) -> bool:
        """Check for large files"""
        logger.info("Checking file sizes...")
        
        max_size_mb = self.config.get('max_file_size_mb', 100)
        
        # Get all files being pushed
        large_files = []
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            for file_path in files:
                full_path = self.repo_root / file_path
                if full_path.exists():
                    if not self.github_helper.check_file_size(full_path, max_size_mb):
                        size_mb = full_path.stat().st_size / (1024 * 1024)
                        large_files.append(f"{file_path} ({size_mb:.2f}MB)")
        
        if large_files:
            self.errors.append(f"Large files detected (>{max_size_mb}MB):")
            self.errors.extend([f"  {file}" for file in large_files])
            return False
        
        return True
    
    def verify_test_coverage(self) -> bool:
        """Verify test coverage meets minimum requirements"""
        logger.info("Verifying test coverage...")
        
        min_coverage = self.config.get('min_test_coverage', 80)
        
        # Get changed Python files
        changed_python_files = set()
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            for file_path in files:
                if self.github_helper.is_python_file(file_path) and not file_path.startswith('tests/'):
                    changed_python_files.add(file_path)
        
        if not changed_python_files:
            logger.info("No Python files changed, skipping coverage check")
            return True
        
        # Run coverage for changed files
        try:
            cmd = ['pytest', '--cov=server', '--cov=agents', '--cov=mcp', '--cov-report=json', 'tests/']
            exit_code, stdout, stderr = self.github_helper.run_command(cmd)
            
            if exit_code == 0:
                # Read coverage report
                coverage_file = self.repo_root / 'coverage.json'
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                    
                    total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                    
                    if total_coverage < min_coverage:
                        self.warnings.append(f"Test coverage is {total_coverage:.1f}%, minimum required: {min_coverage}%")
                    else:
                        logger.info(f"Test coverage: {total_coverage:.1f}%")
                    
                    # Check coverage for individual changed files
                    files_with_low_coverage = []
                    for file_path in changed_python_files:
                        file_coverage = coverage_data.get('files', {}).get(file_path, {})
                        file_percent = file_coverage.get('summary', {}).get('percent_covered', 0)
                        if file_percent < min_coverage:
                            files_with_low_coverage.append(f"{file_path}: {file_percent:.1f}%")
                    
                    if files_with_low_coverage:
                        self.warnings.append("Files with low test coverage:")
                        self.warnings.extend([f"  {file}" for file in files_with_low_coverage])
                    
                    return True
            
        except Exception as e:
            logger.warning(f"Coverage check failed: {e}")
        
        return True  # Don't fail on coverage issues, just warn
    
    def detect_breaking_changes(self) -> bool:
        """Detect potential breaking changes"""
        logger.info("Detecting breaking changes...")
        
        breaking_changes = []
        
        # Get commit messages and check for breaking change indicators
        for commit in self.commits_to_push:
            commit_msg = self.github_helper.get_commit_message(commit)
            
            # Check for conventional commit breaking change indicators
            if 'BREAKING CHANGE' in commit_msg or '!' in commit_msg.split(':')[0]:
                breaking_changes.append(f"Commit {commit[:8]}: {commit_msg}")
        
        # Check for API changes
        api_breaking_changes = self._detect_api_breaking_changes()
        breaking_changes.extend(api_breaking_changes)
        
        # Check for database schema changes
        schema_changes = self._detect_schema_changes()
        if schema_changes:
            self.warnings.extend([f"Database schema change: {change}" for change in schema_changes])
        
        if breaking_changes:
            self.warnings.append("Breaking changes detected:")
            self.warnings.extend([f"  {change}" for change in breaking_changes])
        
        return True  # Don't fail on breaking changes, just warn
    
    def _detect_api_breaking_changes(self) -> list[str]:
        """Detect breaking changes in API"""
        breaking_changes = []
        
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            api_files = [f for f in files if self.edu_helper.is_api_file(f)]
            
            for file_path in api_files:
                # Check git diff for removed endpoints or changed signatures
                exit_code, stdout, stderr = self.github_helper.run_command([
                    'git', 'show', f"{commit}:{file_path}"
                ])
                
                if exit_code == 0:
                    # Simple pattern matching for removed routes
                    if '- @app.' in stdout or '- def ' in stdout:
                        breaking_changes.append(f"Potential API endpoint removal in {file_path}")
        
        return breaking_changes
    
    def _detect_schema_changes(self) -> list[str]:
        """Detect database schema changes"""
        schema_changes = []
        
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            migration_files = [f for f in files if 'migration' in f.lower() or 'alembic' in f.lower()]
            
            for file_path in migration_files:
                if 'drop' in file_path.lower() or 'delete' in file_path.lower():
                    schema_changes.append(f"Potentially destructive migration: {file_path}")
        
        return schema_changes
    
    def validate_commit_messages(self) -> bool:
        """Validate commit message format"""
        logger.info("Validating commit messages...")
        
        invalid_messages = []
        
        # Conventional commit pattern
        conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+'
        
        for commit in self.commits_to_push:
            commit_msg = self.github_helper.get_commit_message(commit)
            
            if not re.match(conventional_pattern, commit_msg):
                invalid_messages.append(f"{commit[:8]}: {commit_msg[:50]}...")
        
        if invalid_messages:
            self.warnings.append("Non-conventional commit messages:")
            self.warnings.extend([f"  {msg}" for msg in invalid_messages])
        
        return True  # Don't fail on commit message format, just warn
    
    def check_educational_standards(self) -> bool:
        """Check educational platform specific standards"""
        logger.info("Checking educational platform standards...")
        
        # Get files being pushed
        changed_files = set()
        for commit in self.commits_to_push:
            files = self.github_helper.get_commit_files(commit)
            changed_files.update(files)
        
        educational_issues = []
        
        # Check Roblox files for educational best practices
        roblox_files = [f for f in changed_files if self.edu_helper.is_roblox_file(f)]
        for file_path in roblox_files:
            issues = self._check_roblox_educational_standards(file_path)
            educational_issues.extend(issues)
        
        # Check agent files for educational AI standards
        agent_files = [f for f in changed_files if self.edu_helper.is_agent_file(f)]
        for file_path in agent_files:
            issues = self._check_agent_educational_standards(file_path)
            educational_issues.extend(issues)
        
        if educational_issues:
            self.warnings.append("Educational platform standards issues:")
            self.warnings.extend([f"  {issue}" for issue in educational_issues])
        
        return True  # Don't fail on educational standards, just warn
    
    def _check_roblox_educational_standards(self, file_path: str) -> list[str]:
        """Check Roblox files for educational standards"""
        full_path = self.repo_root / file_path
        if not full_path.exists():
            return []
        
        issues = []
        
        try:
            with open(full_path) as f:
                content = f.read()
            
            # Check for inappropriate content for educational environment
            inappropriate_patterns = [
                r'kill|death|die|blood|violence',
                r'weapon|gun|sword|knife',
                r'money|cash|gambling|bet'
            ]
            
            for pattern in inappropriate_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if it's in a comment explaining why it's educational
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, re.IGNORECASE):
                            if not ('educational' in line.lower() or 'learning' in line.lower()):
                                issues.append(f"{file_path}:{i+1} - Potentially inappropriate content for educational environment")
            
            # Check for accessibility considerations
            if 'TextButton' in content or 'TextLabel' in content:
                if 'TextScaled' not in content:
                    issues.append(f"{file_path} - Consider adding TextScaled for accessibility")
            
        except Exception as e:
            logger.warning(f"Error checking educational standards in {file_path}: {e}")
        
        return issues
    
    def _check_agent_educational_standards(self, file_path: str) -> list[str]:
        """Check agent files for educational AI standards"""
        full_path = self.repo_root / file_path
        if not full_path.exists():
            return []
        
        issues = []
        
        try:
            with open(full_path) as f:
                content = f.read()
            
            # Check for educational AI best practices
            if 'openai' in content.lower() or 'llm' in content.lower():
                # Check for content filtering
                if 'content_filter' not in content and 'moderation' not in content:
                    issues.append(f"{file_path} - Consider adding content moderation for educational safety")
                
                # Check for age-appropriate responses
                if 'age_appropriate' not in content and 'grade_level' not in content:
                    issues.append(f"{file_path} - Consider adding age-appropriate content filtering")
            
            # Check for privacy considerations
            if 'student' in content.lower() and 'privacy' not in content.lower():
                issues.append(f"{file_path} - Consider student privacy implications")
        
        except Exception as e:
            logger.warning(f"Error checking educational AI standards in {file_path}: {e}")
        
        return issues


def main():
    """Main entry point for pre-push hook"""
    parser = argparse.ArgumentParser(description='Pre-push hook for ToolboxAI Roblox Environment')
    parser.add_argument('--force', action='store_true', help='Force push even if checks fail')
    parser.add_argument('--skip-security', action='store_true', help='Skip security scanning')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    hook = PrePushHook(force_push=args.force, skip_security=args.skip_security)
    
    try:
        success = hook.run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Pre-push hook interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pre-push hook failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()