#!/usr/bin/env python3
"""
GitHub Integration Module for ToolboxAI Roblox Environment

This module provides helper functions and utilities for GitHub hooks and integrations
in the ToolboxAI educational platform development workflow.
"""

import os
import sys
import subprocess
import logging
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubHelper:
    """Helper class for GitHub operations"""
    
    def __init__(self):
        self.repo_root = self._find_repo_root()
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPOSITORY_OWNER', 'ToolBoxAI-Solutions')
        self.repo_name = os.getenv('GITHUB_REPOSITORY_NAME', 'ToolboxAI-Roblox-Environment')
    
    def _find_repo_root(self) -> Path:
        """Find the root directory of the Git repository"""
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            if (current_dir / '.git').exists():
                return current_dir
            current_dir = current_dir.parent
        return Path.cwd()
    
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def get_changed_files(self, commit_range: Optional[str] = None) -> List[str]:
        """Get list of changed files"""
        if commit_range:
            cmd = ['git', 'diff', '--name-only', commit_range]
        else:
            cmd = ['git', 'diff', '--cached', '--name-only']
        
        exit_code, stdout, stderr = self.run_command(cmd)
        if exit_code == 0:
            return [f.strip() for f in stdout.split('\n') if f.strip()]
        return []
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files"""
        return self.get_changed_files()
    
    def is_python_file(self, file_path: str) -> bool:
        """Check if file is a Python file"""
        return file_path.endswith('.py')
    
    def is_lua_file(self, file_path: str) -> bool:
        """Check if file is a Lua file"""
        return file_path.endswith('.lua')
    
    def is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file"""
        config_extensions = ['.json', '.yaml', '.yml', '.toml', '.ini']
        return any(file_path.endswith(ext) for ext in config_extensions)
    
    def validate_json_file(self, file_path: Path) -> bool:
        """Validate JSON file syntax"""
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            return True
        except json.JSONDecodeError as e:
            logger.error(f"JSON validation failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return False
    
    def validate_yaml_file(self, file_path: Path) -> bool:
        """Validate YAML file syntax"""
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            logger.error(f"YAML validation failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return False
    
    def check_file_size(self, file_path: Path, max_size_mb: int = 50) -> bool:
        """Check if file size is within limits"""
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                logger.error(f"File {file_path} exceeds size limit: {size_mb:.2f}MB > {max_size_mb}MB")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking file size for {file_path}: {e}")
            return False
    
    def check_secrets_in_file(self, file_path: Path) -> List[str]:
        """Check for potential secrets in file content"""
        secret_patterns = [
            'api_key',
            'secret_key',
            'password',
            'token',
            'private_key',
            'access_key',
            'secret_access_key',
            'database_url',
            'connection_string'
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            found_secrets = []
            for pattern in secret_patterns:
                if pattern in content and '=' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if pattern in line and '=' in line and not line.strip().startswith('#'):
                            found_secrets.append(f"Line {i}: Possible {pattern}")
            
            return found_secrets
        except Exception as e:
            logger.error(f"Error checking secrets in {file_path}: {e}")
            return []
    
    def get_git_branch(self) -> str:
        """Get current Git branch"""
        exit_code, stdout, stderr = self.run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        if exit_code == 0:
            return stdout.strip()
        return 'unknown'
    
    def get_commit_message(self, commit_hash: str = 'HEAD') -> str:
        """Get commit message for a specific commit"""
        exit_code, stdout, stderr = self.run_command(['git', 'log', '-1', '--pretty=format:%s', commit_hash])
        if exit_code == 0:
            return stdout.strip()
        return ''
    
    def get_commit_files(self, commit_hash: str = 'HEAD') -> List[str]:
        """Get files changed in a specific commit"""
        exit_code, stdout, stderr = self.run_command(['git', 'show', '--name-only', '--pretty=format:', commit_hash])
        if exit_code == 0:
            return [f.strip() for f in stdout.split('\n') if f.strip()]
        return []
    
    def send_github_api_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict]:
        """Send request to GitHub API"""
        if not self.github_token:
            logger.warning("GitHub token not available")
            return None
        
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/{endpoint}"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            return None

class EducationalPlatformHelper:
    """Helper for educational platform specific operations"""
    
    @staticmethod
    def is_roblox_file(file_path: str) -> bool:
        """Check if file is related to Roblox development"""
        roblox_paths = ['Roblox/', 'roblox/', '.lua', 'rbxl', 'rbxm']
        return any(pattern in file_path for pattern in roblox_paths)
    
    @staticmethod
    def is_api_file(file_path: str) -> bool:
        """Check if file is part of the API layer"""
        api_paths = ['API/', 'api/', 'server/', 'backend/']
        return any(pattern in file_path for pattern in api_paths)
    
    @staticmethod
    def is_agent_file(file_path: str) -> bool:
        """Check if file is part of the AI agent system"""
        agent_paths = ['agents/', 'mcp/', 'sparc/', 'swarm/', 'coordinators/']
        return any(pattern in file_path for pattern in agent_paths)
    
    @staticmethod
    def get_component_from_path(file_path: str) -> str:
        """Determine component type from file path"""
        if EducationalPlatformHelper.is_roblox_file(file_path):
            return 'roblox'
        elif EducationalPlatformHelper.is_api_file(file_path):
            return 'api'
        elif EducationalPlatformHelper.is_agent_file(file_path):
            return 'agents'
        elif 'github/' in file_path:
            return 'github'
        elif 'tests/' in file_path:
            return 'tests'
        elif 'docker/' in file_path:
            return 'docker'
        else:
            return 'core'
    
    @staticmethod
    def get_educational_labels(content: str) -> List[str]:
        """Extract educational-related labels from content"""
        educational_keywords = {
            'curriculum': 'curriculum',
            'quiz': 'assessment',
            'assessment': 'assessment',
            'learning': 'learning',
            'student': 'student',
            'teacher': 'teacher',
            'grade': 'grading',
            'lms': 'lms-integration',
            'schoology': 'lms-integration',
            'canvas': 'lms-integration',
            'gamification': 'gamification',
            'achievement': 'gamification',
            'progress': 'progress-tracking',
            'analytics': 'analytics'
        }
        
        content_lower = content.lower()
        labels = []
        
        for keyword, label in educational_keywords.items():
            if keyword in content_lower and label not in labels:
                labels.append(label)
        
        return labels

# Utility functions
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('github_integration')
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from file"""
    if config_path is None:
        config_path = Path(__file__).parent / 'config.json'
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    # Default configuration
    return {
        'max_file_size_mb': 50,
        'python_version': '3.11',
        'node_version': '18',
        'test_timeout': 300,
        'security_scan_enabled': True,
        'documentation_required': False,
        'roblox_lint_enabled': True
    }

def notify_team(message: str, webhook_url: Optional[str] = None):
    """Send notification to team via webhook"""
    if not webhook_url:
        webhook_url = os.getenv('TEAM_WEBHOOK_URL')
    
    if not webhook_url:
        logger.info(f"Team notification: {message}")
        return
    
    try:
        response = requests.post(webhook_url, json={'text': message})
        response.raise_for_status()
        logger.info("Team notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send team notification: {e}")

# Export main classes and functions
__all__ = [
    'GitHubHelper',
    'EducationalPlatformHelper',
    'setup_logging',
    'load_config',
    'notify_team'
]