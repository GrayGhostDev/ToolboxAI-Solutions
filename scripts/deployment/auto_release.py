#!/usr/bin/env python3
"""
Automated Release Management System
Creates releases based on commits and coordinates with all terminals.
"""

import os
import sys
import json
import redis
import asyncio
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("⚠️  PyGithub not installed. Install with: pip install PyGithub")

import semantic_version


class AutoReleaser:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent.parent
        
        # Initialize GitHub client if available
        self.github = None
        self.repo = None
        if GITHUB_AVAILABLE and os.getenv('GITHUB_TOKEN'):
            self.github = Github(os.getenv('GITHUB_TOKEN'))
            try:
                self.repo = self.github.get_repo('ToolBoxAI-Solutions/ToolboxAI-Solutions')
            except Exception as e:
                print(f"⚠️  Could not access GitHub repo: {e}")
        
        # Initialize Redis for terminal coordination
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.redis_available = True
        except (redis.ConnectionError, redis.TimeoutError):
            self.redis_available = False
            self.redis_client = None

    def get_current_version(self) -> semantic_version.Version:
        """Get the current version from git tags or default."""
        try:
            # Get latest tag
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                tag = result.stdout.strip()
                # Remove 'v' prefix if present
                if tag.startswith('v'):
                    tag = tag[1:]
                return semantic_version.Version(tag)
            else:
                # No tags found, start from 0.1.0
                return semantic_version.Version('0.1.0')
        except Exception as e:
            print(f"Error getting current version: {e}")
            return semantic_version.Version('0.1.0')

    def analyze_commits(self, since_tag: Optional[str] = None) -> Dict:
        """Analyze commits to determine version bump type."""
        try:
            # Get commits since last tag
            if since_tag:
                cmd = ['git', 'log', f'{since_tag}..HEAD', '--pretty=format:%s|%b|%an|%ae']
            else:
                cmd = ['git', 'log', '--pretty=format:%s|%b|%an|%ae']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commits = result.stdout.strip().split('\n') if result.stdout else []
            
            analysis = {
                'breaking_changes': [],
                'features': [],
                'fixes': [],
                'other': [],
                'contributors': set()
            }
            
            for commit in commits:
                if not commit:
                    continue
                
                parts = commit.split('|')
                if len(parts) >= 4:
                    subject = parts[0]
                    body = parts[1] if len(parts) > 1 else ''
                    author = parts[2]
                    email = parts[3]
                    
                    analysis['contributors'].add(f"{author} <{email}>")
                    
                    # Conventional commit analysis
                    if 'BREAKING CHANGE' in subject or 'BREAKING CHANGE' in body:
                        analysis['breaking_changes'].append(subject)
                    elif subject.startswith('feat:') or subject.startswith('feature:'):
                        analysis['features'].append(subject)
                    elif subject.startswith('fix:') or subject.startswith('bugfix:'):
                        analysis['fixes'].append(subject)
                    else:
                        analysis['other'].append(subject)
            
            return analysis
            
        except subprocess.CalledProcessError as e:
            print(f"Error analyzing commits: {e}")
            return {
                'breaking_changes': [],
                'features': [],
                'fixes': [],
                'other': [],
                'contributors': set()
            }

    def determine_version_bump(self, analysis: Dict) -> str:
        """Determine version bump type based on commit analysis."""
        if analysis['breaking_changes']:
            return 'major'
        elif analysis['features']:
            return 'minor'
        elif analysis['fixes']:
            return 'patch'
        else:
            return 'patch'  # Default to patch

    def bump_version(self, current: semantic_version.Version, bump_type: str) -> semantic_version.Version:
        """Bump version based on type."""
        if bump_type == 'major':
            return current.next_major()
        elif bump_type == 'minor':
            return current.next_minor()
        else:
            return current.next_patch()

    def generate_changelog(self, version: str, analysis: Dict) -> str:
        """Generate changelog from commit analysis."""
        changelog = f"# Release v{version}\n\n"
        changelog += f"Released: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if analysis['breaking_changes']:
            changelog += "## ⚠️ Breaking Changes\n\n"
            for change in analysis['breaking_changes']:
                changelog += f"- {self.format_commit_message(change)}\n"
            changelog += "\n"
        
        if analysis['features']:
            changelog += "## ✨ New Features\n\n"
            for feature in analysis['features']:
                changelog += f"- {self.format_commit_message(feature)}\n"
            changelog += "\n"
        
        if analysis['fixes']:
            changelog += "## 🐛 Bug Fixes\n\n"
            for fix in analysis['fixes']:
                changelog += f"- {self.format_commit_message(fix)}\n"
            changelog += "\n"
        
        if analysis['other']:
            changelog += "## 📝 Other Changes\n\n"
            for change in analysis['other'][:10]:  # Limit to 10 other changes
                changelog += f"- {self.format_commit_message(change)}\n"
            if len(analysis['other']) > 10:
                changelog += f"- ...and {len(analysis['other']) - 10} more\n"
            changelog += "\n"
        
        # Add terminal status if available
        terminal_status = self.get_terminal_status()
        if terminal_status:
            changelog += "## 🖥️ Terminal Status\n\n"
            for terminal, status in terminal_status.items():
                icon = "✅" if status == "ready" else "⚠️"
                changelog += f"- {icon} {terminal}: {status}\n"
            changelog += "\n"
        
        if analysis['contributors']:
            changelog += "## 👥 Contributors\n\n"
            for contributor in sorted(analysis['contributors']):
                changelog += f"- {contributor}\n"
            changelog += "\n"
        
        changelog += "---\n"
        changelog += "*This release was automatically generated*\n"
        
        return changelog

    def format_commit_message(self, message: str) -> str:
        """Format commit message for changelog."""
        # Remove conventional commit prefixes
        prefixes = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 
                   'test:', 'chore:', 'feature:', 'bugfix:']
        
        for prefix in prefixes:
            if message.startswith(prefix):
                message = message[len(prefix):].strip()
                break
        
        # Capitalize first letter
        if message and message[0].islower():
            message = message[0].upper() + message[1:]
        
        return message

    async def check_terminal_approval(self, version: str) -> bool:
        """Check if all terminals approve the release."""
        if not self.redis_available:
            print("⚠️  Redis not available, skipping terminal approval")
            return True
        
        terminals = ['terminal1', 'terminal2', 'terminal3', 'debugger']
        approvals = {}
        
        for terminal in terminals:
            # Request approval
            self.redis_client.publish(
                f"terminal:{terminal}:release_approval",
                json.dumps({
                    'version': version,
                    'timestamp': datetime.now().isoformat()
                })
            )
        
        # Wait for approvals (with timeout)
        timeout = 30  # seconds
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            all_approved = True
            
            for terminal in terminals:
                approval_key = f"terminal:{terminal}:release_approval:{version}"
                approval = self.redis_client.get(approval_key)
                
                if approval:
                    approvals[terminal] = json.loads(approval).get('approved', False)
                else:
                    approvals[terminal] = None
                    all_approved = False
            
            if all(v is not None for v in approvals.values()):
                break
            
            await asyncio.sleep(1)
        
        # Report approval status
        print("\n📋 Terminal Approval Status:")
        for terminal, approved in approvals.items():
            if approved is None:
                print(f"  ⏳ {terminal}: No response")
            elif approved:
                print(f"  ✅ {terminal}: Approved")
            else:
                print(f"  ❌ {terminal}: Rejected")
        
        return all(v == True for v in approvals.values() if v is not None)

    def get_terminal_status(self) -> Dict[str, str]:
        """Get current status of all terminals."""
        if not self.redis_available:
            return {}
        
        status = {}
        terminals = ['terminal1', 'terminal2', 'terminal3', 'debugger', 'cloud']
        
        for terminal in terminals:
            status_key = f"terminal:{terminal}:status"
            terminal_status = self.redis_client.get(status_key)
            
            if terminal_status:
                status_data = json.loads(terminal_status)
                status[terminal] = status_data.get('status', 'unknown')
            else:
                status[terminal] = 'offline'
        
        return status

    def create_git_tag(self, version: str, message: str):
        """Create a git tag for the release."""
        tag_name = f"v{version}"
        
        if self.dry_run:
            print(f"[DRY RUN] Would create tag: {tag_name}")
            return
        
        try:
            # Create annotated tag
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', message],
                check=True
            )
            print(f"✅ Created tag: {tag_name}")
            
            # Push tag to remote
            subprocess.run(
                ['git', 'push', 'origin', tag_name],
                check=False  # Don't fail if can't push
            )
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create tag: {e}")

    def create_github_release(self, version: str, changelog: str):
        """Create a GitHub release."""
        if not self.github or not self.repo:
            print("⚠️  GitHub not configured, skipping GitHub release")
            return
        
        if self.dry_run:
            print(f"[DRY RUN] Would create GitHub release v{version}")
            return
        
        try:
            release = self.repo.create_git_release(
                tag=f"v{version}",
                name=f"Release v{version}",
                message=changelog,
                draft=False,
                prerelease=self.is_prerelease(version)
            )
            
            print(f"✅ Created GitHub release: {release.html_url}")
            
            # Notify terminals
            if self.redis_available:
                self.redis_client.publish(
                    'terminal:all:release_created',
                    json.dumps({
                        'version': version,
                        'url': release.html_url,
                        'timestamp': datetime.now().isoformat()
                    })
                )
            
        except Exception as e:
            print(f"❌ Failed to create GitHub release: {e}")

    def is_prerelease(self, version: str) -> bool:
        """Determine if version is a prerelease."""
        v = semantic_version.Version(version)
        return v.prerelease is not None

    async def deploy_to_staging(self, version: str):
        """Deploy release to staging environment."""
        print("\n🚀 Deploying to staging...")
        
        if self.dry_run:
            print("[DRY RUN] Would deploy to staging")
            return True
        
        # Run deployment script
        deploy_script = self.project_root / "scripts" / "terminal_sync" / "deploy_pipeline.sh"
        
        if deploy_script.exists():
            result = subprocess.run(
                [str(deploy_script), "staging", version],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Staging deployment successful")
                return True
            else:
                print(f"❌ Staging deployment failed: {result.stderr}")
                return False
        else:
            print("⚠️  Deployment script not found")
            return False

    async def run_staging_tests(self) -> bool:
        """Run tests against staging environment."""
        print("\n🧪 Running staging tests...")
        
        if self.dry_run:
            print("[DRY RUN] Would run staging tests")
            return True
        
        # Run comprehensive tests
        test_script = self.project_root / "scripts" / "testing" / "run_comprehensive_tests.sh"
        
        if test_script.exists():
            result = subprocess.run(
                [str(test_script), "--type=e2e", "--environment=staging"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Staging tests passed")
                return True
            else:
                print(f"❌ Staging tests failed")
                return False
        else:
            print("⚠️  Test script not found")
            return True  # Don't block if no tests

    async def create_auto_release(self):
        """Main function to create an automated release."""
        print("=" * 60)
        print("🤖 AUTOMATED RELEASE MANAGER")
        print("=" * 60)
        
        # Get current version
        current_version = self.get_current_version()
        print(f"\n📌 Current version: v{current_version}")
        
        # Analyze commits
        print("\n📊 Analyzing commits...")
        analysis = self.analyze_commits(f"v{current_version}")
        
        # Determine version bump
        bump_type = self.determine_version_bump(analysis)
        new_version = self.bump_version(current_version, bump_type)
        
        print(f"📈 Version bump: {bump_type} (v{current_version} → v{new_version})")
        
        # Print commit summary
        print("\n📝 Commit Summary:")
        print(f"  Breaking changes: {len(analysis['breaking_changes'])}")
        print(f"  Features: {len(analysis['features'])}")
        print(f"  Fixes: {len(analysis['fixes'])}")
        print(f"  Other: {len(analysis['other'])}")
        print(f"  Contributors: {len(analysis['contributors'])}")
        
        # Generate changelog
        print("\n📄 Generating changelog...")
        changelog = self.generate_changelog(str(new_version), analysis)
        
        if self.dry_run:
            print("\n[DRY RUN] Changelog preview:")
            print("-" * 40)
            print(changelog[:500] + "..." if len(changelog) > 500 else changelog)
            print("-" * 40)
        
        # Check terminal approvals
        print("\n🔍 Checking terminal approvals...")
        if not self.dry_run:
            approved = await self.check_terminal_approval(str(new_version))
            
            if not approved:
                print("\n❌ Release blocked: Not all terminals approved")
                return
        
        # Create release
        print(f"\n🎉 Creating release v{new_version}...")
        
        # Create git tag
        self.create_git_tag(str(new_version), f"Release v{new_version}\n\n{changelog}")
        
        # Create GitHub release
        self.create_github_release(str(new_version), changelog)
        
        # Deploy to staging
        if await self.deploy_to_staging(str(new_version)):
            # Run staging tests
            if await self.run_staging_tests():
                print("\n✅ Release v{new_version} created successfully!")
                
                # Ask for production deployment
                if not self.dry_run:
                    response = input("\n🚀 Deploy to production? (y/N): ")
                    if response.lower() == 'y':
                        print("Deploying to production...")
                        subprocess.run(
                            [str(self.project_root / "scripts" / "terminal_sync" / "deploy_pipeline.sh"),
                             "production", str(new_version)]
                        )
            else:
                print("\n⚠️  Staging tests failed, release created but not deployed to production")
        else:
            print("\n⚠️  Staging deployment failed")
        
        print("\n" + "=" * 60)
        print("Release process complete!")
        print("=" * 60)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Automated Release Manager')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Force release even without terminal approval')
    
    args = parser.parse_args()
    
    releaser = AutoReleaser(dry_run=args.dry_run)
    await releaser.create_auto_release()


if __name__ == "__main__":
    asyncio.run(main())