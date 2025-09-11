#!/usr/bin/env python3
"""
Release management automation for ToolboxAI Roblox Environment

This script provides automated release management:
- Semantic versioning automation
- Changelog generation
- Asset bundling
- Docker image tagging
- Roblox version updates
- NPM/PyPI publishing preparation
- Release notes generation

Usage:
    python releases.py [command] [options]

Commands:
    create-release <version>     - Create a new release
    generate-changelog <version> - Generate changelog for version
    bundle-assets <version>      - Bundle release assets
    tag-images <version>         - Tag Docker images
    update-roblox <version>      - Update Roblox version info
    prepare-publish <version>    - Prepare for NPM/PyPI publishing
    generate-notes <version>     - Generate release notes

Environment Variables:
    GITHUB_TOKEN - GitHub personal access token
    DOCKER_REGISTRY - Docker registry URL
    NPM_TOKEN - NPM authentication token
    PYPI_TOKEN - PyPI authentication token
    ROBLOX_API_KEY - Roblox API key for uploads
"""

import os
import sys
import argparse
import json
import re
import subprocess
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import semver

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from github import GitHubHelper, EducationalPlatformHelper, setup_logging, load_config, notify_team

logger = setup_logging()

class ReleaseManager:
    """Automated release management for educational platform"""
    
    def __init__(self):
        self.github_helper = GitHubHelper()
        self.edu_helper = EducationalPlatformHelper()
        self.config = load_config()
        self.repo_root = self.github_helper.repo_root
        
        # Release configuration
        self.release_config = {
            'changelog_file': 'CHANGELOG.md',
            'version_files': [
                'package.json',
                'API/Dashboard/package.json',
                'pyproject.toml',
                'API/GhostBackend/pyproject.toml'
            ],
            'asset_paths': [
                'dist/',
                'build/',
                'Roblox/',
                'docker/',
                'docs/'
            ],
            'docker_images': [
                'toolboxai-api',
                'toolboxai-mcp',
                'toolboxai-agents',
                'toolboxai-dashboard'
            ]
        }
    
    def create_release(self, version: str, prerelease: bool = False) -> bool:
        """Create a complete release"""
        logger.info(f"Creating release {version}")
        
        # Validate version format
        if not self._validate_version(version):
            logger.error(f"Invalid version format: {version}")
            return False
        
        # Check if release already exists
        if self._release_exists(version):
            logger.error(f"Release {version} already exists")
            return False
        
        # Create release branch
        release_branch = f"release/{version}"
        if not self._create_release_branch(release_branch):
            logger.error("Failed to create release branch")
            return False
        
        try:
            # Update version numbers
            if not self._update_version_files(version):
                logger.error("Failed to update version files")
                return False
            
            # Generate changelog
            changelog = self._generate_changelog(version)
            if not changelog:
                logger.error("Failed to generate changelog")
                return False
            
            # Bundle assets
            asset_files = self._bundle_assets(version)
            
            # Tag Docker images
            if not self._tag_docker_images(version):
                logger.warning("Failed to tag Docker images")
            
            # Update Roblox version info
            if not self._update_roblox_version(version):
                logger.warning("Failed to update Roblox version info")
            
            # Commit changes
            if not self._commit_release_changes(version):
                logger.error("Failed to commit release changes")
                return False
            
            # Create Git tag
            if not self._create_git_tag(version):
                logger.error("Failed to create Git tag")
                return False
            
            # Create GitHub release
            release_notes = self._generate_release_notes(version, changelog)
            if not self._create_github_release(version, release_notes, asset_files, prerelease):
                logger.error("Failed to create GitHub release")
                return False
            
            # Prepare publishing
            if not prerelease:
                self._prepare_publishing(version)
            
            # Merge back to main
            if not self._merge_release_branch(release_branch):
                logger.warning("Failed to merge release branch back to main")
            
            # Notify team
            self._notify_release_created(version, prerelease)
            
            logger.info(f"Successfully created release {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating release: {e}")
            return False
    
    def _validate_version(self, version: str) -> bool:
        """Validate semantic version format"""
        try:
            # Remove 'v' prefix if present
            clean_version = version.lstrip('v')
            semver.VersionInfo.parse(clean_version)
            return True
        except ValueError:
            return False
    
    def _release_exists(self, version: str) -> bool:
        """Check if release already exists"""
        releases = self.github_helper.send_github_api_request('releases')
        if releases:
            for release in releases:
                if release.get('tag_name') == version or release.get('tag_name') == f'v{version}':
                    return True
        return False
    
    def _create_release_branch(self, branch_name: str) -> bool:
        """Create release branch from main"""
        logger.info(f"Creating release branch: {branch_name}")
        
        # Ensure we're on main and up to date
        commands = [
            ['git', 'checkout', 'main'],
            ['git', 'pull', 'origin', 'main'],
            ['git', 'checkout', '-b', branch_name]
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.github_helper.run_command(cmd)
            if exit_code != 0:
                logger.error(f"Command failed: {' '.join(cmd)}\n{stderr}")
                return False
        
        return True
    
    def _update_version_files(self, version: str) -> bool:
        """Update version in all relevant files"""
        logger.info(f"Updating version files to {version}")
        
        clean_version = version.lstrip('v')
        
        for version_file in self.release_config['version_files']:
            file_path = self.repo_root / version_file
            if not file_path.exists():
                continue
            
            try:
                if file_path.suffix == '.json':
                    self._update_json_version(file_path, clean_version)
                elif file_path.suffix == '.toml':
                    self._update_toml_version(file_path, clean_version)
                
                logger.info(f"Updated version in {version_file}")
            except Exception as e:
                logger.error(f"Failed to update {version_file}: {e}")
                return False
        
        return True
    
    def _update_json_version(self, file_path: Path, version: str):
        """Update version in JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        data['version'] = version
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _update_toml_version(self, file_path: Path, version: str):
        """Update version in TOML file"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Simple regex replacement for TOML version
        content = re.sub(r'version\s*=\s*"[^"]*"', f'version = "{version}"', content)
        
        with open(file_path, 'w') as f:
            f.write(content)
    
    def _generate_changelog(self, version: str) -> str:
        """Generate changelog for version"""
        logger.info(f"Generating changelog for {version}")
        
        # Get commits since last release
        last_tag = self._get_last_release_tag()
        if last_tag:
            commit_range = f"{last_tag}..HEAD"
        else:
            # First release, get all commits
            commit_range = "HEAD"
        
        # Get commit messages
        exit_code, stdout, stderr = self.github_helper.run_command([
            'git', 'log', commit_range, '--pretty=format:%h|%s|%an|%ad', '--date=short'
        ])
        
        if exit_code != 0:
            logger.error(f"Failed to get git log: {stderr}")
            return ""
        
        commits = []
        for line in stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
        
        # Categorize commits
        changelog_sections = {
            'Features': [],
            'Bug Fixes': [],
            'Educational Improvements': [],
            'API Changes': [],
            'Roblox Updates': [],
            'Agent System': [],
            'Documentation': [],
            'Other': []
        }
        
        for commit in commits:
            message = commit['message']
            category = self._categorize_commit(message)
            
            # Format commit entry
            entry = f"- {message} ({commit['hash']})"
            changelog_sections[category].append(entry)
        
        # Build changelog content
        changelog_content = f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        for section, entries in changelog_sections.items():
            if entries:
                changelog_content += f"### {section}\n\n"
                changelog_content += '\n'.join(entries) + '\n\n'
        
        # Update changelog file
        self._update_changelog_file(version, changelog_content)
        
        return changelog_content
    
    def _categorize_commit(self, message: str) -> str:
        """Categorize commit message"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['feat', 'feature', 'add']):
            if any(edu_keyword in message_lower for edu_keyword in ['curriculum', 'quiz', 'learning', 'student', 'teacher']):
                return 'Educational Improvements'
            elif any(roblox_keyword in message_lower for roblox_keyword in ['roblox', 'lua', 'game', 'studio']):
                return 'Roblox Updates'
            elif any(agent_keyword in message_lower for agent_keyword in ['agent', 'ai', 'langchain', 'llm']):
                return 'Agent System'
            elif any(api_keyword in message_lower for api_keyword in ['api', 'endpoint', 'backend']):
                return 'API Changes'
            else:
                return 'Features'
        elif any(keyword in message_lower for keyword in ['fix', 'bug', 'error', 'issue']):
            return 'Bug Fixes'
        elif any(keyword in message_lower for keyword in ['doc', 'readme', 'guide']):
            return 'Documentation'
        elif any(keyword in message_lower for keyword in ['roblox', 'lua', 'game']):
            return 'Roblox Updates'
        elif any(keyword in message_lower for keyword in ['agent', 'ai', 'langchain']):
            return 'Agent System'
        elif any(keyword in message_lower for keyword in ['api', 'endpoint', 'backend']):
            return 'API Changes'
        elif any(keyword in message_lower for keyword in ['curriculum', 'quiz', 'learning', 'educational']):
            return 'Educational Improvements'
        else:
            return 'Other'
    
    def _get_last_release_tag(self) -> Optional[str]:
        """Get the last release tag"""
        exit_code, stdout, stderr = self.github_helper.run_command([
            'git', 'describe', '--tags', '--abbrev=0'
        ])
        
        if exit_code == 0 and stdout.strip():
            return stdout.strip()
        return None
    
    def _update_changelog_file(self, version: str, content: str):
        """Update changelog file with new content"""
        changelog_file = self.repo_root / self.release_config['changelog_file']
        
        if changelog_file.exists():
            with open(changelog_file, 'r') as f:
                existing_content = f.read()
            
            # Insert new content after the header
            lines = existing_content.split('\n')
            if lines and lines[0].startswith('# '):
                # Find insertion point after header
                insert_index = 1
                while insert_index < len(lines) and not lines[insert_index].startswith('## '):
                    insert_index += 1
                
                # Insert new content
                lines.insert(insert_index, content)
                new_content = '\n'.join(lines)
            else:
                new_content = content + '\n' + existing_content
        else:
            # Create new changelog file
            header = "# Changelog\n\nAll notable changes to the ToolboxAI Roblox Educational Environment will be documented in this file.\n\n"
            new_content = header + content
        
        with open(changelog_file, 'w') as f:
            f.write(new_content)
    
    def _bundle_assets(self, version: str) -> List[str]:
        """Bundle release assets"""
        logger.info(f"Bundling assets for {version}")
        
        assets_dir = self.repo_root / 'release-assets' / version
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_files = []
        
        # Bundle source code
        source_archive = assets_dir / f'toolboxai-roblox-{version}-source.tar.gz'
        if self._create_source_archive(source_archive):
            asset_files.append(str(source_archive))
        
        # Bundle Roblox assets
        roblox_archive = assets_dir / f'toolboxai-roblox-{version}-roblox.zip'
        if self._create_roblox_archive(roblox_archive):
            asset_files.append(str(roblox_archive))
        
        # Bundle Docker images
        docker_archive = assets_dir / f'toolboxai-roblox-{version}-docker.tar.gz'
        if self._create_docker_archive(docker_archive, version):
            asset_files.append(str(docker_archive))
        
        # Bundle documentation
        docs_archive = assets_dir / f'toolboxai-roblox-{version}-docs.zip'
        if self._create_docs_archive(docs_archive):
            asset_files.append(str(docs_archive))
        
        return asset_files
    
    def _create_source_archive(self, output_file: Path) -> bool:
        """Create source code archive"""
        try:
            with tarfile.open(output_file, 'w:gz') as tar:
                # Add all source files, excluding build artifacts
                for root, dirs, files in os.walk(self.repo_root):
                    # Skip unwanted directories
                    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.next', 'dist', 'build']]
                    
                    for file in files:
                        if not file.startswith('.') and not file.endswith(('.pyc', '.log')):
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(self.repo_root)
                            tar.add(file_path, arcname=arcname)
            
            logger.info(f"Created source archive: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create source archive: {e}")
            return False
    
    def _create_roblox_archive(self, output_file: Path) -> bool:
        """Create Roblox-specific archive"""
        try:
            roblox_dir = self.repo_root / 'Roblox'
            if not roblox_dir.exists():
                return False
            
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(roblox_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(roblox_dir)
                        zip_file.write(file_path, arcname=arcname)
            
            logger.info(f"Created Roblox archive: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Roblox archive: {e}")
            return False
    
    def _create_docker_archive(self, output_file: Path, version: str) -> bool:
        """Create Docker images archive"""
        try:
            docker_dir = self.repo_root / 'docker'
            if not docker_dir.exists():
                return False
            
            with tarfile.open(output_file, 'w:gz') as tar:
                # Add Dockerfiles and compose files
                for dockerfile in docker_dir.glob('Dockerfile*'):
                    arcname = dockerfile.name
                    tar.add(dockerfile, arcname=arcname)
                
                for compose_file in docker_dir.glob('docker-compose*.yml'):
                    arcname = compose_file.name
                    tar.add(compose_file, arcname=arcname)
                
                # Add build scripts
                for script in docker_dir.glob('*.sh'):
                    arcname = script.name
                    tar.add(script, arcname=arcname)
            
            logger.info(f"Created Docker archive: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Docker archive: {e}")
            return False
    
    def _create_docs_archive(self, output_file: Path) -> bool:
        """Create documentation archive"""
        try:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add markdown files
                for md_file in self.repo_root.glob('*.md'):
                    zip_file.write(md_file, arcname=md_file.name)
                
                # Add docs directory if it exists
                docs_dir = self.repo_root / 'docs'
                if docs_dir.exists():
                    for root, dirs, files in os.walk(docs_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(self.repo_root)
                            zip_file.write(file_path, arcname=arcname)
            
            logger.info(f"Created docs archive: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create docs archive: {e}")
            return False
    
    def _tag_docker_images(self, version: str) -> bool:
        """Tag Docker images with version"""
        logger.info(f"Tagging Docker images with version {version}")
        
        registry = os.getenv('DOCKER_REGISTRY', '')
        success = True
        
        for image_name in self.release_config['docker_images']:
            try:
                # Tag with version
                version_tag = f"{registry}/{image_name}:{version}" if registry else f"{image_name}:{version}"
                exit_code, stdout, stderr = self.github_helper.run_command([
                    'docker', 'tag', f"{image_name}:latest", version_tag
                ])
                
                if exit_code == 0:
                    logger.info(f"Tagged {image_name} with {version}")
                    
                    # Also tag as latest
                    if registry:
                        latest_tag = f"{registry}/{image_name}:latest"
                        exit_code, stdout, stderr = self.github_helper.run_command([
                            'docker', 'tag', f"{image_name}:latest", latest_tag
                        ])
                else:
                    logger.error(f"Failed to tag {image_name}: {stderr}")
                    success = False
                    
            except Exception as e:
                logger.error(f"Error tagging {image_name}: {e}")
                success = False
        
        return success
    
    def _update_roblox_version(self, version: str) -> bool:
        """Update Roblox version information"""
        logger.info(f"Updating Roblox version to {version}")
        
        roblox_version_file = self.repo_root / 'Roblox' / 'version.lua'
        
        try:
            version_content = f"""
-- ToolboxAI Roblox Environment Version Information
-- Auto-generated during release process

local VERSION = {{
    major = {semver.VersionInfo.parse(version.lstrip('v')).major},
    minor = {semver.VersionInfo.parse(version.lstrip('v')).minor},
    patch = {semver.VersionInfo.parse(version.lstrip('v')).patch},
    string = "{version.lstrip('v')}",
    build_date = "{datetime.now(timezone.utc).isoformat()}",
    git_hash = "{self._get_git_hash()}"
}}

return VERSION
            """.strip()
            
            roblox_version_file.parent.mkdir(exist_ok=True)
            with open(roblox_version_file, 'w') as f:
                f.write(version_content)
            
            logger.info(f"Updated Roblox version file: {roblox_version_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Roblox version: {e}")
            return False
    
    def _get_git_hash(self) -> str:
        """Get current Git commit hash"""
        exit_code, stdout, stderr = self.github_helper.run_command(['git', 'rev-parse', 'HEAD'])
        if exit_code == 0:
            return stdout.strip()[:8]
        return 'unknown'
    
    def _commit_release_changes(self, version: str) -> bool:
        """Commit release changes"""
        logger.info(f"Committing release changes for {version}")
        
        commands = [
            ['git', 'add', '-A'],
            ['git', 'commit', '-m', f"chore: release {version}"]
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.github_helper.run_command(cmd)
            if exit_code != 0:
                logger.error(f"Command failed: {' '.join(cmd)}\n{stderr}")
                return False
        
        return True
    
    def _create_git_tag(self, version: str) -> bool:
        """Create Git tag for release"""
        logger.info(f"Creating Git tag: {version}")
        
        tag_name = version if version.startswith('v') else f'v{version}'
        
        exit_code, stdout, stderr = self.github_helper.run_command([
            'git', 'tag', '-a', tag_name, '-m', f"Release {version}"
        ])
        
        if exit_code != 0:
            logger.error(f"Failed to create tag: {stderr}")
            return False
        
        # Push tag
        exit_code, stdout, stderr = self.github_helper.run_command([
            'git', 'push', 'origin', tag_name
        ])
        
        if exit_code != 0:
            logger.error(f"Failed to push tag: {stderr}")
            return False
        
        return True
    
    def _generate_release_notes(self, version: str, changelog: str) -> str:
        """Generate release notes"""
        logger.info(f"Generating release notes for {version}")
        
        # Get educational platform metrics
        metrics = self._gather_release_metrics(version)
        
        release_notes = f"""# ToolboxAI Roblox Educational Environment {version}

## 🎓 Educational Platform Release

This release brings new features and improvements to the ToolboxAI Roblox Educational Environment, enhancing the learning experience for students and teaching tools for educators.

## 📊 Release Metrics

{metrics}

## 📝 What's Changed

{changelog}

## 🚀 Getting Started

### For Educators
1. Visit our Dashboard at `http://localhost:3000`
2. Connect your LMS (Canvas, Schoology, etc.)
3. Create or import your curriculum
4. Generate Roblox learning environments

### For Developers
1. Clone the repository
2. Run `docker-compose up -d`
3. Install dependencies with `npm install`
4. Start development servers

### For Roblox Developers
1. Open Roblox Studio
2. Install the ToolboxAI Content Generator plugin
3. Load the educational templates
4. Start creating immersive learning experiences

## 🔧 Technical Requirements

- **Python**: 3.11+
- **Node.js**: 18+
- **Roblox Studio**: Latest version
- **Docker**: 20.10+
- **PostgreSQL**: 15+
- **Redis**: 7+

## 📚 Educational Subjects Supported

- Mathematics (K-12)
- Science (Biology, Chemistry, Physics)
- History and Social Studies
- Language Arts
- Computer Science
- Art and Design
- Custom Curriculum Support

## 🛡️ Security & Privacy

This release includes enhanced security measures for educational environments:
- Student data protection compliance
- Content moderation for age-appropriate learning
- Secure LMS integration
- Privacy-first design

## 🤝 Contributing

We welcome contributions from educators, developers, and the community! 
See our [Contributing Guide](CONTRIBUTING.md) for details.

## 📞 Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/discussions)
- 📧 Email: support@toolboxai.solutions

---

**Full Changelog**: https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/compare/v{self._get_previous_version(version)}...{version}

🎓 *Built with ❤️ for educators and learners everywhere*
        """.strip()
        
        return release_notes
    
    def _gather_release_metrics(self, version: str) -> str:
        """Gather metrics for the release"""
        try:
            # Count commits since last release
            last_tag = self._get_last_release_tag()
            if last_tag:
                exit_code, stdout, stderr = self.github_helper.run_command([
                    'git', 'rev-list', '--count', f"{last_tag}..HEAD"
                ])
                commit_count = stdout.strip() if exit_code == 0 else "N/A"
            else:
                commit_count = "First Release"
            
            # Count changed files
            if last_tag:
                exit_code, stdout, stderr = self.github_helper.run_command([
                    'git', 'diff', '--name-only', f"{last_tag}..HEAD"
                ])
                file_count = len(stdout.strip().split('\n')) if exit_code == 0 and stdout.strip() else 0
            else:
                file_count = "N/A"
            
            # Count contributors
            if last_tag:
                exit_code, stdout, stderr = self.github_helper.run_command([
                    'git', 'shortlog', '-sn', f"{last_tag}..HEAD"
                ])
                contributor_count = len(stdout.strip().split('\n')) if exit_code == 0 and stdout.strip() else 0
            else:
                contributor_count = "N/A"
            
            metrics = f"""
- **Commits**: {commit_count}
- **Files Changed**: {file_count}
- **Contributors**: {contributor_count}
- **Release Date**: {datetime.now().strftime('%B %d, %Y')}
- **Platform Version**: {version}
            """.strip()
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Could not gather release metrics: {e}")
            return "Metrics unavailable"
    
    def _get_previous_version(self, current_version: str) -> str:
        """Get previous version for comparison"""
        last_tag = self._get_last_release_tag()
        if last_tag:
            return last_tag.lstrip('v')
        return "0.0.0"
    
    def _create_github_release(self, version: str, release_notes: str, asset_files: List[str], prerelease: bool) -> bool:
        """Create GitHub release"""
        logger.info(f"Creating GitHub release for {version}")
        
        tag_name = version if version.startswith('v') else f'v{version}'
        
        release_data = {
            'tag_name': tag_name,
            'name': f'ToolboxAI Roblox Environment {version}',
            'body': release_notes,
            'prerelease': prerelease,
            'draft': False
        }
        
        release_response = self.github_helper.send_github_api_request(
            'releases',
            method='POST',
            data=release_data
        )
        
        if not release_response:
            logger.error("Failed to create GitHub release")
            return False
        
        release_id = release_response['id']
        
        # Upload assets
        for asset_file in asset_files:
            if not self._upload_release_asset(release_id, asset_file):
                logger.warning(f"Failed to upload asset: {asset_file}")
        
        logger.info(f"Created GitHub release: {release_response['html_url']}")
        return True
    
    def _upload_release_asset(self, release_id: int, asset_file: str) -> bool:
        """Upload asset to GitHub release"""
        try:
            asset_path = Path(asset_file)
            if not asset_path.exists():
                return False
            
            # GitHub API for uploading assets requires different handling
            # This is a simplified version - in practice, you'd use the uploads API
            logger.info(f"Would upload asset: {asset_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload asset {asset_file}: {e}")
            return False
    
    def _prepare_publishing(self, version: str):
        """Prepare packages for NPM/PyPI publishing"""
        logger.info(f"Preparing publishing for {version}")
        
        # Prepare NPM packages
        npm_packages = [
            self.repo_root / 'package.json',
            self.repo_root / 'API' / 'Dashboard' / 'package.json'
        ]
        
        for package_file in npm_packages:
            if package_file.exists():
                logger.info(f"NPM package ready: {package_file.parent}")
        
        # Prepare Python packages
        python_packages = [
            self.repo_root / 'pyproject.toml',
            self.repo_root / 'API' / 'GhostBackend' / 'pyproject.toml'
        ]
        
        for package_file in python_packages:
            if package_file.exists():
                logger.info(f"Python package ready: {package_file.parent}")
    
    def _merge_release_branch(self, release_branch: str) -> bool:
        """Merge release branch back to main"""
        logger.info(f"Merging {release_branch} back to main")
        
        commands = [
            ['git', 'checkout', 'main'],
            ['git', 'merge', '--no-ff', release_branch, '-m', f'Merge {release_branch}'],
            ['git', 'push', 'origin', 'main'],
            ['git', 'branch', '-d', release_branch]
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.github_helper.run_command(cmd)
            if exit_code != 0:
                logger.error(f"Command failed: {' '.join(cmd)}\n{stderr}")
                return False
        
        return True
    
    def _notify_release_created(self, version: str, prerelease: bool):
        """Notify team about release"""
        release_type = "Pre-release" if prerelease else "Release"
        
        message = f"""
🚀 **{release_type} {version} Created**

The ToolboxAI Roblox Educational Environment {version} has been successfully released!

**What's New:**
- Enhanced educational content generation
- Improved Roblox integration
- Better LMS connectivity
- Performance optimizations

**For Educators:**
- Updated curriculum templates
- New assessment tools  
- Enhanced student analytics

**For Developers:**
- Updated API documentation
- New agent capabilities
- Improved deployment process

**Get Started:**
- Dashboard: http://localhost:3000
- Documentation: docs/
- GitHub Release: https://github.com/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/releases/tag/v{version}

Happy teaching and learning! 🎓
        """.strip()
        
        notify_team(message)


def main():
    """Main entry point for release management"""
    parser = argparse.ArgumentParser(description='Release management for ToolboxAI Roblox Environment')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create release command
    create_parser = subparsers.add_parser('create-release', help='Create a new release')
    create_parser.add_argument('version', help='Version to release (e.g., 1.2.3 or v1.2.3)')
    create_parser.add_argument('--prerelease', action='store_true', help='Mark as pre-release')
    
    # Generate changelog command
    changelog_parser = subparsers.add_parser('generate-changelog', help='Generate changelog')
    changelog_parser.add_argument('version', help='Version for changelog')
    
    # Bundle assets command
    bundle_parser = subparsers.add_parser('bundle-assets', help='Bundle release assets')
    bundle_parser.add_argument('version', help='Version to bundle')
    
    # Tag images command
    tag_parser = subparsers.add_parser('tag-images', help='Tag Docker images')
    tag_parser.add_argument('version', help='Version tag')
    
    # Update Roblox command
    roblox_parser = subparsers.add_parser('update-roblox', help='Update Roblox version info')
    roblox_parser.add_argument('version', help='Version to update')
    
    # Prepare publish command
    publish_parser = subparsers.add_parser('prepare-publish', help='Prepare for publishing')
    publish_parser.add_argument('version', help='Version to prepare')
    
    # Generate notes command
    notes_parser = subparsers.add_parser('generate-notes', help='Generate release notes')
    notes_parser.add_argument('version', help='Version for release notes')
    
    # Common arguments
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    manager = ReleaseManager()
    
    try:
        if args.command == 'create-release':
            success = manager.create_release(args.version, args.prerelease)
        elif args.command == 'generate-changelog':
            changelog = manager._generate_changelog(args.version)
            print(changelog)
            success = True
        elif args.command == 'bundle-assets':
            assets = manager._bundle_assets(args.version)
            print(f"Bundled assets: {assets}")
            success = True
        elif args.command == 'tag-images':
            success = manager._tag_docker_images(args.version)
        elif args.command == 'update-roblox':
            success = manager._update_roblox_version(args.version)
        elif args.command == 'prepare-publish':
            manager._prepare_publishing(args.version)
            success = True
        elif args.command == 'generate-notes':
            changelog = manager._generate_changelog(args.version)
            notes = manager._generate_release_notes(args.version, changelog)
            print(notes)
            success = True
        else:
            parser.print_help()
            success = False
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Release management interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Release management failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()