#!/usr/bin/env python3
"""
Verify CI/CD Integration
Comprehensive verification of all CI/CD components and terminal integration.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class CICDVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []

    def check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if a file exists."""
        full_path = self.project_root / file_path
        exists = full_path.exists()
        
        if exists:
            self.checks_passed += 1
            self.results.append(f"✅ {description}: Found")
        else:
            self.checks_failed += 1
            self.results.append(f"❌ {description}: Missing at {file_path}")
        
        return exists

    def check_executable(self, file_path: str, description: str) -> bool:
        """Check if a file is executable."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            self.checks_failed += 1
            self.results.append(f"❌ {description}: File not found")
            return False
        
        is_exec = os.access(full_path, os.X_OK)
        
        if is_exec:
            self.checks_passed += 1
            self.results.append(f"✅ {description}: Executable")
        else:
            self.checks_failed += 1
            self.results.append(f"⚠️  {description}: Not executable")
        
        return is_exec

    def check_python_syntax(self, file_path: str, description: str) -> bool:
        """Check Python file syntax."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return False
        
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', str(full_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.checks_passed += 1
                self.results.append(f"✅ {description}: Valid Python syntax")
                return True
            else:
                self.checks_failed += 1
                self.results.append(f"❌ {description}: Syntax error")
                return False
        except Exception as e:
            self.checks_failed += 1
            self.results.append(f"❌ {description}: Check failed - {e}")
            return False

    def check_yaml_syntax(self, file_path: str, description: str) -> bool:
        """Check YAML file syntax."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return False
        
        try:
            import yaml
            with open(full_path, 'r') as f:
                yaml.safe_load(f)
            
            self.checks_passed += 1
            self.results.append(f"✅ {description}: Valid YAML syntax")
            return True
        except Exception as e:
            self.checks_failed += 1
            self.results.append(f"❌ {description}: Invalid YAML - {e}")
            return False

    def check_github_token(self) -> bool:
        """Check if GitHub token is configured."""
        token = os.getenv('GITHUB_TOKEN')
        
        if token:
            self.checks_passed += 1
            self.results.append(f"✅ GitHub Token: Configured")
            return True
        else:
            self.checks_failed += 1
            self.results.append(f"⚠️  GitHub Token: Not configured (set GITHUB_TOKEN env var)")
            return False

    def run_verification(self):
        """Run comprehensive CI/CD verification."""
        print("=" * 60)
        print("🔍 CI/CD INTEGRATION VERIFICATION")
        print("=" * 60)
        print()
        
        # GitHub Actions Workflows
        print("📋 GitHub Actions Workflows:")
        print("-" * 40)
        self.check_file_exists('.github/workflows/integrated_pipeline.yml', 'Integrated Pipeline')
        self.check_yaml_syntax('.github/workflows/integrated_pipeline.yml', 'Pipeline YAML')
        self.check_file_exists('.github/workflows/deploy.yml', 'Deploy Workflow')
        self.check_file_exists('.github/workflows/roblox-sync.yml', 'Roblox Sync Workflow')
        print()
        
        # Terminal Sync Scripts
        print("🔧 Terminal Synchronization Scripts:")
        print("-" * 40)
        self.check_file_exists('scripts/terminal_sync/check_deployment_ready.py', 'Deployment Ready Check')
        self.check_executable('scripts/terminal_sync/check_deployment_ready.py', 'Deployment Ready Check')
        self.check_python_syntax('scripts/terminal_sync/check_deployment_ready.py', 'Deployment Ready Check')
        
        self.check_file_exists('scripts/terminal_sync/wait_for_terminal.py', 'Terminal Waiter')
        self.check_executable('scripts/terminal_sync/wait_for_terminal.py', 'Terminal Waiter')
        self.check_python_syntax('scripts/terminal_sync/wait_for_terminal.py', 'Terminal Waiter')
        
        self.check_file_exists('scripts/terminal_sync/deploy_pipeline.sh', 'Deploy Pipeline')
        self.check_executable('scripts/terminal_sync/deploy_pipeline.sh', 'Deploy Pipeline')
        print()
        
        # Release Management
        print("🚀 Release Management:")
        print("-" * 40)
        self.check_file_exists('scripts/terminal_sync/auto_release.py', 'Auto Release Manager')
        self.check_executable('scripts/terminal_sync/auto_release.py', 'Auto Release Manager')
        self.check_python_syntax('scripts/terminal_sync/auto_release.py', 'Auto Release Manager')
        print()
        
        # Branch Protection
        print("🔒 Branch Protection:")
        print("-" * 40)
        self.check_file_exists('scripts/terminal_sync/setup_branch_protection.py', 'Branch Protection Setup')
        self.check_executable('scripts/terminal_sync/setup_branch_protection.py', 'Branch Protection Setup')
        self.check_python_syntax('scripts/terminal_sync/setup_branch_protection.py', 'Branch Protection Setup')
        print()
        
        # Metrics Collection
        print("📊 Metrics Collection:")
        print("-" * 40)
        self.check_file_exists('scripts/terminal_sync/cicd_metrics.py', 'CI/CD Metrics')
        self.check_executable('scripts/terminal_sync/cicd_metrics.py', 'CI/CD Metrics')
        self.check_python_syntax('scripts/terminal_sync/cicd_metrics.py', 'CI/CD Metrics')
        print()
        
        # Environment Configuration
        print("🔐 Environment Configuration:")
        print("-" * 40)
        self.check_github_token()
        print()
        
        # Summary
        print("=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"📈 Success Rate: {(self.checks_passed/(self.checks_passed + self.checks_failed)*100):.1f}%")
        print()
        
        if self.checks_failed > 0:
            print("⚠️  Issues Found:")
            for result in self.results:
                if result.startswith('❌') or result.startswith('⚠️'):
                    print(f"  {result}")
            print()
            print("To fix issues:")
            print("1. Ensure all files are created")
            print("2. Make scripts executable: chmod +x scripts/terminal_sync/*.py scripts/terminal_sync/*.sh")
            print("3. Set GitHub token: export GITHUB_TOKEN=your_token")
            print("4. Install dependencies: pip install PyGithub redis semantic-version matplotlib")
        else:
            print("✅ All CI/CD components are properly configured!")
            print()
            print("Next steps:")
            print("1. Set up GitHub token: export GITHUB_TOKEN=your_token")
            print("2. Configure branch protection: python scripts/terminal_sync/setup_branch_protection.py")
            print("3. Test deployment: scripts/terminal_sync/deploy_pipeline.sh staging")
            print("4. Generate metrics report: python scripts/terminal_sync/cicd_metrics.py --report")
        
        print("=" * 60)
        
        return self.checks_failed == 0


def main():
    """Main entry point."""
    verifier = CICDVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()