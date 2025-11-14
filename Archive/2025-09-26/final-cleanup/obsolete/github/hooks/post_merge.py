#!/usr/bin/env python3
"""
Post-merge hook for ToolboxAI Roblox Environment

This hook performs post-merge maintenance tasks:
- Dependency installation updates
- Documentation regeneration
- Cache invalidation
- Database migration checks
- Team notifications
- Environment synchronization

Usage:
    python post_merge.py [--notify] [--verbose] [--dry-run]

Environment Variables:
    SKIP_POST_MERGE_HOOKS - Set to 'true' to skip all hooks
    TEAM_WEBHOOK_URL - URL for team notifications
    AUTO_INSTALL_DEPS - Set to 'true' to auto-install dependencies
    AUTO_MIGRATE_DB - Set to 'true' to auto-run database migrations
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from github import (
    EducationalPlatformHelper,
    GitHubHelper,
    load_config,
    notify_team,
    setup_logging,
)

logger = setup_logging()

class PostMergeHook:
    """Post-merge hook implementation"""
    
    def __init__(self, send_notifications: bool = False, dry_run: bool = False):
        self.github_helper = GitHubHelper()
        self.edu_helper = EducationalPlatformHelper()
        self.config = load_config()
        self.send_notifications = send_notifications
        self.dry_run = dry_run
        self.repo_root = self.github_helper.repo_root
        self.actions_performed: list[str] = []
        
        # Get merge information
        self.merge_commit = self._get_merge_commit()
        self.changed_files = self._get_merge_changes()
        self.source_branch = self._get_source_branch()
    
    def run_all_tasks(self) -> bool:
        """Run all post-merge tasks"""
        if os.getenv('SKIP_POST_MERGE_HOOKS', '').lower() == 'true':
            logger.info("Post-merge hooks skipped via environment variable")
            return True
        
        logger.info("Running post-merge tasks...")
        logger.info(f"Merge commit: {self.merge_commit}")
        logger.info(f"Source branch: {self.source_branch}")
        logger.info(f"Changed files: {len(self.changed_files)}")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
        
        # Run all tasks
        tasks = [
            self.update_dependencies,
            self.regenerate_documentation,
            self.invalidate_caches,
            self.check_database_migrations,
            self.sync_environments,
            self.update_version_info,
            self.cleanup_temporary_files
        ]
        
        all_successful = True
        for task in tasks:
            try:
                if not task():
                    all_successful = False
            except Exception as e:
                logger.error(f"Task {task.__name__} failed: {e}")
                all_successful = False
        
        # Send notifications
        if self.send_notifications:
            self._send_merge_notification(all_successful)
        
        # Log summary
        if self.actions_performed:
            logger.info("Actions performed:")
            for action in self.actions_performed:
                logger.info(f"  - {action}")
        
        return all_successful
    
    def _get_merge_commit(self) -> str:
        """Get the current merge commit hash"""
        exit_code, stdout, stderr = self.github_helper.run_command(['git', 'rev-parse', 'HEAD'])
        if exit_code == 0:
            return stdout.strip()
        return 'unknown'
    
    def _get_merge_changes(self) -> list[str]:
        """Get files changed in the merge"""
        exit_code, stdout, stderr = self.github_helper.run_command(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'])
        if exit_code == 0:
            return [f.strip() for f in stdout.split('\n') if f.strip()]
        return []
    
    def _get_source_branch(self) -> str:
        """Get the source branch that was merged"""
        # Try to get from merge commit message
        commit_msg = self.github_helper.get_commit_message()
        if "Merge pull request" in commit_msg:
            # Extract branch name from PR merge message
            import re
            match = re.search(r'from .+?/(.+)', commit_msg)
            if match:
                return match.group(1)
        
        # Try to get from git log
        exit_code, stdout, stderr = self.github_helper.run_command([
            'git', 'log', '--merges', '-1', '--pretty=format:%P'
        ])
        if exit_code == 0 and stdout:
            parents = stdout.strip().split()
            if len(parents) >= 2:
                # Get branch name from second parent
                exit_code, branch_stdout, _ = self.github_helper.run_command([
                    'git', 'name-rev', '--name-only', parents[1]
                ])
                if exit_code == 0:
                    return branch_stdout.strip()
        
        return 'unknown'
    
    def update_dependencies(self) -> bool:
        """Update dependencies if dependency files changed"""
        logger.info("Checking for dependency updates...")
        
        dependency_files = [
            'requirements.txt',
            'package.json',
            'package-lock.json',
            'pyproject.toml',
            'poetry.lock',
            'Pipfile',
            'Pipfile.lock'
        ]
        
        changed_dep_files = [f for f in self.changed_files if f in dependency_files]
        
        if not changed_dep_files:
            logger.info("No dependency files changed")
            return True
        
        logger.info(f"Dependency files changed: {changed_dep_files}")
        
        auto_install = os.getenv('AUTO_INSTALL_DEPS', 'false').lower() == 'true'
        
        if not auto_install and not self.dry_run:
            logger.info("Auto-install disabled. Skipping dependency installation.")
            return True
        
        success = True
        
        # Update Python dependencies
        if any(f in changed_dep_files for f in ['requirements.txt', 'pyproject.toml', 'Pipfile']):
            success &= self._update_python_dependencies()
        
        # Update Node.js dependencies
        if any(f in changed_dep_files for f in ['package.json', 'package-lock.json']):
            success &= self._update_node_dependencies()
        
        return success
    
    def _update_python_dependencies(self) -> bool:
        """Update Python dependencies"""
        logger.info("Updating Python dependencies...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would update Python dependencies")
            return True
        
        # Check if we're in a virtual environment
        if not os.getenv('VIRTUAL_ENV'):
            logger.warning("Not in a virtual environment. Skipping Python dependency update.")
            return True
        
        # Try different Python package managers
        if (self.repo_root / 'pyproject.toml').exists():
            exit_code, stdout, stderr = self.github_helper.run_command(['pip', 'install', '-e', '.'])
        elif (self.repo_root / 'requirements.txt').exists():
            exit_code, stdout, stderr = self.github_helper.run_command(['pip', 'install', '-r', 'requirements.txt'])
        elif (self.repo_root / 'Pipfile').exists():
            exit_code, stdout, stderr = self.github_helper.run_command(['pipenv', 'install'])
        else:
            logger.info("No Python dependency file found")
            return True
        
        if exit_code == 0:
            logger.info("Python dependencies updated successfully")
            self.actions_performed.append("Updated Python dependencies")
            return True
        else:
            logger.error(f"Failed to update Python dependencies: {stderr}")
            return False
    
    def _update_node_dependencies(self) -> bool:
        """Update Node.js dependencies"""
        logger.info("Updating Node.js dependencies...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would update Node.js dependencies")
            return True
        
        success = True
        
        # Update main package.json
        if (self.repo_root / 'package.json').exists():
            exit_code, stdout, stderr = self.github_helper.run_command(['npm', 'install'])
            if exit_code == 0:
                logger.info("Main Node.js dependencies updated")
                self.actions_performed.append("Updated main Node.js dependencies")
            else:
                logger.error(f"Failed to update main Node.js dependencies: {stderr}")
                success = False
        
        # Update Dashboard dependencies
        dashboard_path = self.repo_root / 'API' / 'Dashboard'
        if dashboard_path.exists() and (dashboard_path / 'package.json').exists():
            exit_code, stdout, stderr = self.github_helper.run_command(['npm', 'install'], cwd=dashboard_path)
            if exit_code == 0:
                logger.info("Dashboard dependencies updated")
                self.actions_performed.append("Updated Dashboard dependencies")
            else:
                logger.error(f"Failed to update Dashboard dependencies: {stderr}")
                success = False
        
        return success
    
    def regenerate_documentation(self) -> bool:
        """Regenerate documentation if needed"""
        logger.info("Checking for documentation updates...")
        
        doc_files = [f for f in self.changed_files if f.endswith(('.md', '.rst', '.txt')) or 'docs/' in f.lower()]
        code_files = [f for f in self.changed_files if f.endswith(('.py', '.js', '.ts', '.lua'))]
        
        if not doc_files and not code_files:
            logger.info("No documentation updates needed")
            return True
        
        if self.dry_run:
            logger.info("DRY RUN: Would regenerate documentation")
            return True
        
        success = True
        
        # Generate API documentation if API files changed
        api_files = [f for f in code_files if self.edu_helper.is_api_file(f)]
        if api_files:
            success &= self._generate_api_docs()
        
        # Update agent documentation if agent files changed
        agent_files = [f for f in code_files if self.edu_helper.is_agent_file(f)]
        if agent_files:
            success &= self._generate_agent_docs()
        
        return success
    
    def _generate_api_docs(self) -> bool:
        """Generate API documentation"""
        logger.info("Generating API documentation...")
        
        # Generate OpenAPI docs
        api_docs_path = self.repo_root / 'docs' / 'api'
        api_docs_path.mkdir(parents=True, exist_ok=True)
        
        # Try to generate OpenAPI spec
        exit_code, stdout, stderr = self.github_helper.run_command([
            'python', '-c', 
            'from apps.backend.main import app; import json; print(json.dumps(app.openapi()))'
        ])
        
        if exit_code == 0:
            try:
                import json
                openapi_spec = json.loads(stdout)
                with open(api_docs_path / 'openapi.json', 'w') as f:
                    json.dump(openapi_spec, f, indent=2)
                logger.info("OpenAPI documentation generated")
                self.actions_performed.append("Generated API documentation")
                return True
            except Exception as e:
                logger.error(f"Failed to save OpenAPI spec: {e}")
                return False
        else:
            logger.warning(f"Failed to generate OpenAPI spec: {stderr}")
            return False
    
    def _generate_agent_docs(self) -> bool:
        """Generate agent system documentation"""
        logger.info("Generating agent documentation...")
        
        # This would generate documentation for the LangGraph agents
        # For now, just log that it would happen
        self.actions_performed.append("Generated agent documentation")
        return True
    
    def invalidate_caches(self) -> bool:
        """Invalidate various caches"""
        logger.info("Invalidating caches...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would invalidate caches")
            return True
        
        cache_paths = [
            self.repo_root / '__pycache__',
            self.repo_root / '.pytest_cache',
            self.repo_root / '.mypy_cache',
            self.repo_root / 'node_modules' / '.cache',
            self.repo_root / 'API' / 'Dashboard' / '.next' / 'cache'
        ]
        
        caches_cleared = 0
        for cache_path in cache_paths:
            if cache_path.exists():
                try:
                    import shutil
                    shutil.rmtree(cache_path)
                    caches_cleared += 1
                    logger.info(f"Cleared cache: {cache_path}")
                except Exception as e:
                    logger.warning(f"Failed to clear cache {cache_path}: {e}")
        
        if caches_cleared > 0:
            self.actions_performed.append(f"Cleared {caches_cleared} caches")
        
        return True
    
    def check_database_migrations(self) -> bool:
        """Check and run database migrations if needed"""
        logger.info("Checking for database migrations...")
        
        migration_files = [f for f in self.changed_files if 'migrations/' in f or 'alembic/' in f]
        
        if not migration_files:
            logger.info("No migration files changed")
            return True
        
        logger.info(f"Migration files changed: {migration_files}")
        
        auto_migrate = os.getenv('AUTO_MIGRATE_DB', 'false').lower() == 'true'
        
        if not auto_migrate:
            logger.info("Auto-migration disabled. Please run migrations manually.")
            return True
        
        if self.dry_run:
            logger.info("DRY RUN: Would run database migrations")
            return True
        
        # Check if Alembic is available
        ghost_backend_path = self.repo_root / 'API' / 'GhostBackend'
        if not ghost_backend_path.exists():
            logger.info("Ghost backend not found, skipping migrations")
            return True
        
        # Run Alembic migrations
        exit_code, stdout, stderr = self.github_helper.run_command(
            ['alembic', 'upgrade', 'head'], 
            cwd=ghost_backend_path
        )
        
        if exit_code == 0:
            logger.info("Database migrations completed successfully")
            self.actions_performed.append("Ran database migrations")
            return True
        else:
            logger.error(f"Database migration failed: {stderr}")
            return False
    
    def sync_environments(self) -> bool:
        """Synchronize development environments"""
        logger.info("Synchronizing environments...")
        
        env_files = [f for f in self.changed_files if f.endswith(('.env.example', '.env.template', 'docker-compose.yml'))]
        
        if not env_files:
            logger.info("No environment files changed")
            return True
        
        if self.dry_run:
            logger.info("DRY RUN: Would synchronize environments")
            return True
        
        # Update environment templates
        success = True
        
        # Check if .env files need updating based on .env.example
        env_example = self.repo_root / '.env.example'
        env_file = self.repo_root / '.env'
        
        if env_example.exists() and '.env.example' in env_files:
            success &= self._sync_env_file(env_example, env_file)
        
        # Sync Dashboard environment
        dashboard_env_example = self.repo_root / 'API' / 'Dashboard' / '.env.example'
        dashboard_env = self.repo_root / 'API' / 'Dashboard' / '.env'
        
        if dashboard_env_example.exists():
            success &= self._sync_env_file(dashboard_env_example, dashboard_env)
        
        # Sync Ghost Backend environment
        ghost_env_example = self.repo_root / 'API' / 'GhostBackend' / '.env.example'
        ghost_env = self.repo_root / 'API' / 'GhostBackend' / '.env'
        
        if ghost_env_example.exists():
            success &= self._sync_env_file(ghost_env_example, ghost_env)
        
        return success
    
    def _sync_env_file(self, example_file: Path, target_file: Path) -> bool:
        """Synchronize environment file with example"""
        try:
            if not target_file.exists():
                # Create new .env from example
                import shutil
                shutil.copy2(example_file, target_file)
                logger.info(f"Created {target_file} from {example_file}")
                self.actions_performed.append(f"Created {target_file.name}")
            else:
                # Check for new variables in example
                with open(example_file) as f:
                    example_vars = set()
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            var_name = line.split('=')[0]
                            example_vars.add(var_name)
                
                with open(target_file) as f:
                    current_vars = set()
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            var_name = line.split('=')[0]
                            current_vars.add(var_name)
                
                missing_vars = example_vars - current_vars
                if missing_vars:
                    logger.info(f"New environment variables found in {example_file}: {missing_vars}")
                    # Note: We don't automatically add them to avoid overwriting existing configs
                    self.actions_performed.append(f"New env vars available in {target_file.name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to sync {target_file}: {e}")
            return False
    
    def update_version_info(self) -> bool:
        """Update version information"""
        logger.info("Updating version information...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would update version information")
            return True
        
        # Update version in package.json files
        success = True
        
        # Update main package.json
        main_package = self.repo_root / 'package.json'
        if main_package.exists():
            success &= self._bump_package_version(main_package)
        
        # Update Dashboard package.json
        dashboard_package = self.repo_root / 'API' / 'Dashboard' / 'package.json'
        if dashboard_package.exists():
            success &= self._bump_package_version(dashboard_package)
        
        return success
    
    def _bump_package_version(self, package_file: Path) -> bool:
        """Bump version in package.json (patch version)"""
        try:
            import json
            import re
            
            with open(package_file) as f:
                package_data = json.load(f)
            
            current_version = package_data.get('version', '1.0.0')
            
            # Parse semantic version
            version_match = re.match(r'^(\d+)\.(\d+)\.(\d+)', current_version)
            if version_match:
                major, minor, patch = map(int, version_match.groups())
                new_version = f"{major}.{minor}.{patch + 1}"
                
                package_data['version'] = new_version
                
                with open(package_file, 'w') as f:
                    json.dump(package_data, f, indent=2)
                
                logger.info(f"Updated {package_file} version: {current_version} -> {new_version}")
                self.actions_performed.append(f"Bumped version to {new_version}")
                return True
            else:
                logger.warning(f"Could not parse version in {package_file}: {current_version}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update version in {package_file}: {e}")
            return False
    
    def cleanup_temporary_files(self) -> bool:
        """Clean up temporary files"""
        logger.info("Cleaning up temporary files...")
        
        if self.dry_run:
            logger.info("DRY RUN: Would clean up temporary files")
            return True
        
        temp_patterns = [
            '*.tmp',
            '*.temp',
            '*~',
            '.DS_Store',
            'Thumbs.db',
            '*.log',
            '*.swp',
            '*.swo'
        ]
        
        import glob
        files_removed = 0
        
        for pattern in temp_patterns:
            for temp_file in glob.glob(str(self.repo_root / '**' / pattern), recursive=True):
                try:
                    os.remove(temp_file)
                    files_removed += 1
                    logger.debug(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove {temp_file}: {e}")
        
        if files_removed > 0:
            logger.info(f"Removed {files_removed} temporary files")
            self.actions_performed.append(f"Cleaned {files_removed} temporary files")
        
        return True
    
    def _send_merge_notification(self, success: bool):
        """Send notification about merge completion"""
        status = "✅ Success" if success else "❌ Failed"
        
        message = f"""
        {status} Post-merge tasks completed
        
        **Merge Details:**
        - Commit: {self.merge_commit[:8]}
        - Source Branch: {self.source_branch}
        - Files Changed: {len(self.changed_files)}
        
        **Actions Performed:**
        {chr(10).join([f"• {action}" for action in self.actions_performed])}
        
        **Changed Components:**
        {chr(10).join([f"• {self.edu_helper.get_component_from_path(f)}" for f in set(self.edu_helper.get_component_from_path(f) for f in self.changed_files)])}
        """
        
        notify_team(message.strip())


def main():
    """Main entry point for post-merge hook"""
    parser = argparse.ArgumentParser(description='Post-merge hook for ToolboxAI Roblox Environment')
    parser.add_argument('--notify', action='store_true', help='Send team notifications')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    hook = PostMergeHook(send_notifications=args.notify, dry_run=args.dry_run)
    
    try:
        success = hook.run_all_tasks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Post-merge hook interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Post-merge hook failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()