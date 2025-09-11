#!/usr/bin/env python3
# DEPRECATED: Use scripts/security_scanner.py
import sys
print("Use scripts/security_scanner.py", file=sys.stderr)
sys.exit(1)

import os
import re
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityScanner:
    def __init__(self, base_path="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"):
        self.base_path = Path(base_path)
        self.issues = []
        self.files_scanned = 0
        
        # Patterns to detect hardcoded credentials
        self.patterns = [
            (r'password\s*=\s*["\'](?!test|example|placeholder|password|changeme)[^"\']{4,}["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', 'Hardcoded API key'),
            (r'secret_key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', 'Hardcoded secret key'),
            (r'token\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', 'Hardcoded token'),
            (r'aws_access_key_id\s*=\s*["\'][A-Z0-9]{20}["\']', 'AWS Access Key'),
            (r'aws_secret_access_key\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']', 'AWS Secret Key'),
            (r'POSTGRES_PASSWORD\s*=\s*["\'][^"\']+["\']', 'Database password'),
            (r'JWT_SECRET_KEY\s*=\s*["\'][^"\']+["\']', 'JWT secret key'),
        ]
        
        # Directories to skip
        self.skip_dirs = {
            'venv', 'venv_clean', 'node_modules', '.git', '__pycache__',
            'dist', 'build', '.pytest_cache', 'test-results', 'backups'
        }
        
        # File extensions to scan
        self.scan_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.env', '.yaml', '.yml', '.json'}
    
    def scan_file(self, file_path):
        """Scan a single file for security issues"""
        try:
            # Skip binary files
            if file_path.suffix not in self.scan_extensions:
                return
            
            # Skip .env.example files
            if '.example' in file_path.name or 'template' in file_path.name.lower():
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            self.files_scanned += 1
            
            # Check for hardcoded credentials
            for pattern, issue_type in self.patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    self.issues.append({
                        'file': str(file_path.relative_to(self.base_path)),
                        'line': line_num,
                        'type': issue_type,
                        'match': match.group(0)[:50] + '...' if len(match.group(0)) > 50 else match.group(0)
                    })
            
            # Check for insecure configurations
            if file_path.suffix in ['.py']:
                # Check for DEBUG=True in production
                if re.search(r'DEBUG\s*=\s*True', content):
                    if 'production' in str(file_path).lower() or 'prod' in str(file_path).lower():
                        self.issues.append({
                            'file': str(file_path.relative_to(self.base_path)),
                            'line': 0,
                            'type': 'DEBUG enabled in production',
                            'match': 'DEBUG=True'
                        })
                
                # Check for disabled SSL verification
                if re.search(r'verify\s*=\s*False', content):
                    self.issues.append({
                        'file': str(file_path.relative_to(self.base_path)),
                        'line': 0,
                        'type': 'SSL verification disabled',
                        'match': 'verify=False'
                    })
                
                # Check for insecure random
                if re.search(r'random\.random\(\)', content):
                    self.issues.append({
                        'file': str(file_path.relative_to(self.base_path)),
                        'line': 0,
                        'type': 'Using insecure random for security',
                        'match': 'random.random()'
                    })
                    
        except Exception as e:
            logger.debug(f"Error scanning {file_path}: {e}")
    
    def scan_directory(self, directory=None):
        """Recursively scan directory for security issues"""
        if directory is None:
            directory = self.base_path
        
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in self.skip_dirs:
                    self.scan_directory(item)
            elif item.is_file():
                self.scan_file(item)
    
    def check_env_files(self):
        """Check for proper .env file configuration"""
        env_files = list(self.base_path.glob('**/.env'))
        env_example_files = list(self.base_path.glob('**/.env.example'))
        
        # Check if .env files are in .gitignore
        gitignore_path = self.base_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
                if '.env' not in gitignore_content:
                    self.issues.append({
                        'file': '.gitignore',
                        'line': 0,
                        'type': 'Missing .env in .gitignore',
                        'match': '.env files not ignored'
                    })
        
        # Check if .env files exist without .env.example
        for env_file in env_files:
            example_file = env_file.parent / '.env.example'
            if not example_file.exists():
                logger.warning(f"⚠️ Missing .env.example for {env_file}")
    
    def generate_report(self):
        """Generate security scan report"""
        logger.info("\n" + "=" * 60)
        logger.info("🔐 SECURITY SCAN REPORT")
        logger.info("=" * 60)
        logger.info(f"Files scanned: {self.files_scanned}")
        logger.info(f"Issues found: {len(self.issues)}")
        
        if not self.issues:
            logger.info("\n✅ No security issues found!")
            return
        
        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        # Print issues by type
        for issue_type, issues in issues_by_type.items():
            logger.warning(f"\n⚠️ {issue_type} ({len(issues)} instances):")
            for issue in issues[:5]:  # Show first 5 of each type
                logger.warning(f"  📍 {issue['file']}:{issue['line']}")
                logger.warning(f"     {issue['match']}")
            if len(issues) > 5:
                logger.warning(f"  ... and {len(issues) - 5} more")
        
        # Save detailed report
        report_path = self.base_path / 'security_scan_report.json'
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': os.popen('date').read().strip(),
                'files_scanned': self.files_scanned,
                'total_issues': len(self.issues),
                'issues': self.issues
            }, f, indent=2)
        
        logger.info(f"\n📄 Detailed report saved to: {report_path}")
    
    def suggest_fixes(self):
        """Suggest fixes for common issues"""
        logger.info("\n" + "=" * 60)
        logger.info("🔧 SUGGESTED FIXES")
        logger.info("=" * 60)
        
        suggestions = [
            "1. Move all credentials to environment variables (.env file)",
            "2. Use os.getenv() or config management for sensitive data",
            "3. Never commit .env files to version control",
            "4. Use secrets management service for production",
            "5. Enable SSL verification in production",
            "6. Use cryptographically secure random for security operations",
            "7. Disable DEBUG mode in production environments",
            "8. Regularly rotate API keys and passwords",
            "9. Use least privilege principle for database users",
            "10. Implement proper authentication and authorization"
        ]
        
        for suggestion in suggestions:
            logger.info(f"  ✅ {suggestion}")
    
    def run(self):
        """Run the complete security scan"""
        logger.info("🔍 Starting Security Scan...")
        logger.info(f"Scanning: {self.base_path}")
        
        # Scan for hardcoded credentials
        self.scan_directory()
        
        # Check environment file configuration
        self.check_env_files()
        
        # Generate report
        self.generate_report()
        
        # Suggest fixes
        if self.issues:
            self.suggest_fixes()
        
        logger.info("\n✅ Security scan complete!")
        
        # Return exit code based on issues found
        return 1 if self.issues else 0

if __name__ == "__main__":
    scanner = SecurityScanner()
    exit_code = scanner.run()
    exit(exit_code)