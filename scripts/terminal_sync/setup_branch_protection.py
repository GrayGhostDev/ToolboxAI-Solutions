#!/usr/bin/env python3
"""
Configure GitHub branch protection rules for the repository.
Ensures code quality and review requirements are enforced.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional

try:
    from github import Github
    from github.GithubException import GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("❌ PyGithub not installed. Install with: pip install PyGithub")
    sys.exit(1)


class BranchProtectionManager:
    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """Initialize the branch protection manager."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        
        if not self.token:
            print("❌ GitHub token not found. Set GITHUB_TOKEN environment variable.")
            sys.exit(1)
        
        self.github = Github(self.token)
        
        # Default repository
        self.repo_name = repo_name or 'ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment'
        
        try:
            self.repo = self.github.get_repo(self.repo_name)
            print(f"✅ Connected to repository: {self.repo_name}")
        except GithubException as e:
            print(f"❌ Failed to access repository: {e}")
            sys.exit(1)

    def get_protection_rules(self, branch_name: str) -> Dict:
        """Get protection rules configuration for a branch."""
        if branch_name == 'main':
            return {
                'required_status_checks': {
                    'strict': True,  # Require branches to be up to date
                    'contexts': [
                        'continuous-integration/github-actions',
                        'test / test (backend)',
                        'test / test (frontend)',
                        'test / test (roblox)',
                        'test / test (integration)',
                        'security-scan'
                    ]
                },
                'enforce_admins': False,  # Allow admins to bypass in emergencies
                'required_pull_request_reviews': {
                    'required_approving_review_count': 2,
                    'dismiss_stale_reviews': True,
                    'require_code_owner_reviews': True,
                    'dismissal_restrictions': {}
                },
                'restrictions': None,  # No user/team restrictions
                'allow_force_pushes': False,
                'allow_deletions': False,
                'required_conversation_resolution': True,
                'lock_branch': False,
                'allow_fork_syncing': False
            }
        elif branch_name == 'develop':
            return {
                'required_status_checks': {
                    'strict': False,  # More lenient for develop
                    'contexts': [
                        'test / test (backend)',
                        'test / test (frontend)',
                        'security-scan'
                    ]
                },
                'enforce_admins': False,
                'required_pull_request_reviews': {
                    'required_approving_review_count': 1,
                    'dismiss_stale_reviews': True,
                    'require_code_owner_reviews': False,
                    'dismissal_restrictions': {}
                },
                'restrictions': None,
                'allow_force_pushes': False,
                'allow_deletions': False,
                'required_conversation_resolution': False,
                'lock_branch': False,
                'allow_fork_syncing': False
            }
        else:
            # Default rules for other branches
            return {
                'required_status_checks': {
                    'strict': False,
                    'contexts': []
                },
                'enforce_admins': False,
                'required_pull_request_reviews': None,
                'restrictions': None,
                'allow_force_pushes': True,
                'allow_deletions': True,
                'required_conversation_resolution': False,
                'lock_branch': False,
                'allow_fork_syncing': False
            }

    def setup_branch_protection(self, branch_name: str, custom_rules: Optional[Dict] = None):
        """Set up branch protection for a specific branch."""
        print(f"\n🔒 Configuring protection for branch: {branch_name}")
        
        try:
            # Get the branch
            branch = self.repo.get_branch(branch_name)
            
            # Get protection rules
            rules = custom_rules or self.get_protection_rules(branch_name)
            
            # Apply protection rules
            if rules.get('required_pull_request_reviews'):
                pr_reviews = rules['required_pull_request_reviews']
                
                branch.edit_protection(
                    required_status_checks=rules.get('required_status_checks'),
                    enforce_admins=rules.get('enforce_admins', False),
                    required_approving_review_count=pr_reviews.get('required_approving_review_count', 1),
                    dismiss_stale_reviews=pr_reviews.get('dismiss_stale_reviews', False),
                    require_code_owner_reviews=pr_reviews.get('require_code_owner_reviews', False),
                    restrictions=rules.get('restrictions'),
                    allow_force_pushes=rules.get('allow_force_pushes', False),
                    allow_deletions=rules.get('allow_deletions', False),
                    required_conversation_resolution=rules.get('required_conversation_resolution', False),
                    lock_branch=rules.get('lock_branch', False),
                    allow_fork_syncing=rules.get('allow_fork_syncing', False)
                )
            else:
                # No PR reviews required
                branch.edit_protection(
                    required_status_checks=rules.get('required_status_checks'),
                    enforce_admins=rules.get('enforce_admins', False),
                    restrictions=rules.get('restrictions'),
                    allow_force_pushes=rules.get('allow_force_pushes', True),
                    allow_deletions=rules.get('allow_deletions', True)
                )
            
            print(f"✅ Branch protection configured for: {branch_name}")
            self.display_protection_summary(branch_name, rules)
            
        except GithubException as e:
            if e.status == 404:
                print(f"❌ Branch '{branch_name}' not found")
                
                # Offer to create the branch
                response = input(f"Create branch '{branch_name}'? (y/N): ")
                if response.lower() == 'y':
                    self.create_branch(branch_name)
                    # Retry protection setup
                    self.setup_branch_protection(branch_name, custom_rules)
            else:
                print(f"❌ Failed to configure protection: {e}")

    def create_branch(self, branch_name: str, base_branch: str = 'main'):
        """Create a new branch."""
        try:
            # Get the base branch
            base = self.repo.get_branch(base_branch)
            
            # Create new branch from base
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base.commit.sha
            )
            
            print(f"✅ Created branch: {branch_name} from {base_branch}")
            
        except GithubException as e:
            print(f"❌ Failed to create branch: {e}")

    def display_protection_summary(self, branch_name: str, rules: Dict):
        """Display a summary of protection rules."""
        print(f"\n📋 Protection Summary for '{branch_name}':")
        print("-" * 40)
        
        # Status checks
        if rules.get('required_status_checks'):
            checks = rules['required_status_checks']
            print(f"✓ Status Checks: {len(checks.get('contexts', []))} required")
            if checks.get('strict'):
                print("  - Branches must be up to date")
            for context in checks.get('contexts', []):
                print(f"  - {context}")
        else:
            print("✗ Status Checks: None")
        
        # PR reviews
        if rules.get('required_pull_request_reviews'):
            reviews = rules['required_pull_request_reviews']
            print(f"✓ PR Reviews: {reviews.get('required_approving_review_count', 0)} required")
            if reviews.get('dismiss_stale_reviews'):
                print("  - Dismiss stale reviews")
            if reviews.get('require_code_owner_reviews'):
                print("  - Require code owner reviews")
        else:
            print("✗ PR Reviews: Not required")
        
        # Other settings
        print(f"✓ Enforce for admins: {'Yes' if rules.get('enforce_admins') else 'No'}")
        print(f"✓ Allow force pushes: {'Yes' if rules.get('allow_force_pushes') else 'No'}")
        print(f"✓ Allow deletions: {'Yes' if rules.get('allow_deletions') else 'No'}")
        
        if rules.get('required_conversation_resolution'):
            print("✓ Require conversation resolution")
        
        print("-" * 40)

    def remove_protection(self, branch_name: str):
        """Remove protection from a branch."""
        print(f"\n🔓 Removing protection from branch: {branch_name}")
        
        try:
            branch = self.repo.get_branch(branch_name)
            branch.remove_protection()
            print(f"✅ Protection removed from: {branch_name}")
            
        except GithubException as e:
            print(f"❌ Failed to remove protection: {e}")

    def list_protected_branches(self):
        """List all protected branches."""
        print("\n🔒 Protected Branches:")
        print("-" * 40)
        
        try:
            branches = self.repo.get_branches()
            protected_count = 0
            
            for branch in branches:
                if branch.protected:
                    protected_count += 1
                    print(f"✓ {branch.name}")
                    
                    # Get protection details
                    try:
                        protection = branch.get_protection()
                        if protection:
                            # Show basic info
                            if hasattr(protection, 'required_status_checks'):
                                checks = protection.required_status_checks
                                if checks and hasattr(checks, 'contexts'):
                                    print(f"  - {len(checks.contexts)} status checks")
                            
                            if hasattr(protection, 'required_pull_request_reviews'):
                                reviews = protection.required_pull_request_reviews
                                if reviews:
                                    count = getattr(reviews, 'required_approving_review_count', 0)
                                    print(f"  - {count} review(s) required")
                    except:
                        pass
            
            if protected_count == 0:
                print("No protected branches found")
            else:
                print(f"\nTotal: {protected_count} protected branch(es)")
            
        except GithubException as e:
            print(f"❌ Failed to list branches: {e}")

    def setup_codeowners(self):
        """Create or update CODEOWNERS file."""
        print("\n📝 Setting up CODEOWNERS file...")
        
        codeowners_content = """# CODEOWNERS file for ToolBoxAI Educational Platform
# These owners will be requested for review when someone opens a pull request

# Default owners for everything
* @ToolBoxAI-Solutions/maintainers

# Backend (Python/FastAPI)
/ToolboxAI-Roblox-Environment/server/ @ToolBoxAI-Solutions/backend
/ToolboxAI-Roblox-Environment/agents/ @ToolBoxAI-Solutions/ai-team
/ToolboxAI-Roblox-Environment/sparc/ @ToolBoxAI-Solutions/ai-team
/ToolboxAI-Roblox-Environment/mcp/ @ToolBoxAI-Solutions/backend

# Frontend (React/TypeScript)
/src/dashboard/ @ToolBoxAI-Solutions/frontend
/API/Dashboard/ @ToolBoxAI-Solutions/frontend

# Database
/database/ @ToolBoxAI-Solutions/database
*.sql @ToolBoxAI-Solutions/database

# Roblox
/ToolboxAI-Roblox-Environment/Roblox/ @ToolBoxAI-Solutions/roblox
*.lua @ToolBoxAI-Solutions/roblox

# CI/CD and DevOps
/.github/ @ToolBoxAI-Solutions/devops
/scripts/ @ToolBoxAI-Solutions/devops
/config/ @ToolBoxAI-Solutions/devops

# Documentation
/Documentation/ @ToolBoxAI-Solutions/docs
*.md @ToolBoxAI-Solutions/docs

# Security-sensitive files
.env* @ToolBoxAI-Solutions/security
**/secrets.* @ToolBoxAI-Solutions/security
**/credentials.* @ToolBoxAI-Solutions/security
"""
        
        try:
            # Check if CODEOWNERS exists
            try:
                contents = self.repo.get_contents(".github/CODEOWNERS")
                # Update existing file
                self.repo.update_file(
                    ".github/CODEOWNERS",
                    "Update CODEOWNERS file",
                    codeowners_content,
                    contents.sha
                )
                print("✅ Updated CODEOWNERS file")
            except:
                # Create new file
                self.repo.create_file(
                    ".github/CODEOWNERS",
                    "Add CODEOWNERS file",
                    codeowners_content
                )
                print("✅ Created CODEOWNERS file")
            
            print("\n📋 CODEOWNERS configuration:")
            print("  - Default owners: @ToolBoxAI-Solutions/maintainers")
            print("  - Backend: @ToolBoxAI-Solutions/backend")
            print("  - Frontend: @ToolBoxAI-Solutions/frontend")
            print("  - AI/ML: @ToolBoxAI-Solutions/ai-team")
            print("  - Roblox: @ToolBoxAI-Solutions/roblox")
            print("  - DevOps: @ToolBoxAI-Solutions/devops")
            
        except GithubException as e:
            print(f"⚠️  Could not create CODEOWNERS: {e}")
            print("You can manually create .github/CODEOWNERS with the above content")

    def setup_all_branches(self):
        """Set up protection for all standard branches."""
        branches = ['main', 'develop']
        
        print("=" * 60)
        print("🔒 BRANCH PROTECTION SETUP")
        print("=" * 60)
        
        for branch in branches:
            self.setup_branch_protection(branch)
        
        # Set up CODEOWNERS
        self.setup_codeowners()
        
        # List all protected branches
        self.list_protected_branches()
        
        print("\n" + "=" * 60)
        print("✅ Branch protection setup complete!")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Setup GitHub branch protection')
    parser.add_argument('--branch', help='Specific branch to protect')
    parser.add_argument('--remove', action='store_true',
                       help='Remove protection instead of adding')
    parser.add_argument('--list', action='store_true',
                       help='List protected branches')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--repo', help='Repository name (owner/repo)')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = BranchProtectionManager(token=args.token, repo_name=args.repo)
    
    # Execute requested action
    if args.list:
        manager.list_protected_branches()
    elif args.remove and args.branch:
        manager.remove_protection(args.branch)
    elif args.branch:
        manager.setup_branch_protection(args.branch)
    else:
        # Default: setup all standard branches
        manager.setup_all_branches()


if __name__ == "__main__":
    main()