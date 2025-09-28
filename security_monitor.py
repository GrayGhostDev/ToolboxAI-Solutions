#!/usr/bin/env python3
"""
ToolBoxAI Security Monitor
=========================

Monitors and validates security posture for the ToolBoxAI Solutions project.
Ensures security compliance before allowing commits.

Features:
- Secret detection in code
- Vulnerability scanning
- Security score calculation
- Pre-commit validation
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class SecurityIssue:
    """Represents a security issue found in the code."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # secret, vulnerability, configuration
    file_path: str
    line_number: int
    description: str
    remediation: str


class SecurityMonitor:
    """Main security monitoring and validation class."""

    # Patterns for detecting secrets
    SECRET_PATTERNS = [
        (r'(?i)api[_-]?key\s*=\s*["\'][\w\-]{20,}["\']', 'API Key'),
        (r'(?i)secret[_-]?key\s*=\s*["\'][\w\-]{20,}["\']', 'Secret Key'),
        (r'(?i)password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded Password'),
        (r'(?i)token\s*=\s*["\'][\w\-\.]{20,}["\']', 'Token'),
        (r'(?i)aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'][\w]{20}["\']', 'AWS Access Key'),
        (r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*=\s*["\'][\w\/\+]{40}["\']', 'AWS Secret Key'),
        (r'postgresql://[^@\s]+@[^\s]+', 'Database Connection String'),
        (r'mongodb://[^@\s]+@[^\s]+', 'MongoDB Connection String'),
        (r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', 'Private Key'),
    ]

    # Files and directories to exclude from scanning
    EXCLUDE_PATHS = [
        'venv/', '.venv/', 'env/',
        'node_modules/',
        '__pycache__/',
        '.git/',
        '*.pyc', '*.pyo',
        '.env.example', '.env.template',
        'test_', 'tests/',
        'Archive/',
        'Documentation/Archive/',
        '*.min.js', '*.min.css'
    ]

    # Acceptable files for certain patterns
    ALLOWED_PATTERNS = {
        '.env.example': ['password', 'key', 'token', 'secret'],
        '.env.template': ['password', 'key', 'token', 'secret'],
        'config.example': ['password', 'key', 'token', 'secret'],
    }

    def __init__(self, project_root: Path = None):
        """Initialize the security monitor."""
        self.project_root = project_root or Path.cwd()
        self.issues: List[SecurityIssue] = []
        self.stats = {
            'files_scanned': 0,
            'secrets_found': 0,
            'vulnerabilities_found': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0
        }

    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned."""
        file_str = str(file_path)

        # Check exclude patterns
        for pattern in self.EXCLUDE_PATHS:
            if pattern in file_str:
                return False

        # Only scan text files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read first 100 bytes to check if it's text
                f.read(100)
            return True
        except (UnicodeDecodeError, PermissionError):
            return False

    def scan_file_for_secrets(self, file_path: Path) -> List[SecurityIssue]:
        """Scan a single file for hardcoded secrets."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#') or line.strip().startswith('//'):
                    continue

                for pattern, secret_type in self.SECRET_PATTERNS:
                    if re.search(pattern, line):
                        # Check if this is an allowed pattern
                        file_name = file_path.name
                        if file_name in self.ALLOWED_PATTERNS:
                            continue

                        # Check if it's a placeholder
                        if any(placeholder in line.lower() for placeholder in
                               ['your-', 'xxx', 'example', 'placeholder', 'change-me']):
                            continue

                        issue = SecurityIssue(
                            severity='CRITICAL' if 'password' in secret_type.lower() else 'HIGH',
                            category='secret',
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            description=f'Potential {secret_type} detected',
                            remediation='Move to environment variables or secure secret management'
                        )
                        issues.append(issue)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        return issues

    def check_dependencies(self) -> List[SecurityIssue]:
        """Check for vulnerable dependencies."""
        issues = []

        # Check Python dependencies with pip-audit if available
        try:
            result = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    issue = SecurityIssue(
                        severity=self._map_severity(vuln.get('severity', 'UNKNOWN')),
                        category='vulnerability',
                        file_path='requirements.txt',
                        line_number=0,
                        description=f"{vuln['name']} {vuln['version']} - {vuln.get('description', 'Vulnerability detected')}",
                        remediation=f"Upgrade to {vuln.get('fix_versions', ['latest version'])[0]}"
                    )
                    issues.append(issue)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            # pip-audit not installed or failed - not critical
            pass

        return issues

    def _map_severity(self, severity: str) -> str:
        """Map external severity ratings to our scale."""
        severity = severity.upper()
        if severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            return severity
        elif severity in ['SEVERE', 'IMPORTANT']:
            return 'HIGH'
        elif severity in ['MODERATE']:
            return 'MEDIUM'
        else:
            return 'LOW'

    def run_scan(self) -> Tuple[List[SecurityIssue], Dict]:
        """Run a complete security scan."""
        print("🔍 Starting security scan...")

        # Scan all files for secrets
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and self.should_scan_file(file_path):
                self.stats['files_scanned'] += 1
                file_issues = self.scan_file_for_secrets(file_path)
                self.issues.extend(file_issues)
                self.stats['secrets_found'] += len(file_issues)

        # Check dependencies
        dep_issues = self.check_dependencies()
        self.issues.extend(dep_issues)
        self.stats['vulnerabilities_found'] += len(dep_issues)

        # Update severity counts
        for issue in self.issues:
            if issue.severity == 'CRITICAL':
                self.stats['critical_issues'] += 1
            elif issue.severity == 'HIGH':
                self.stats['high_issues'] += 1
            elif issue.severity == 'MEDIUM':
                self.stats['medium_issues'] += 1
            elif issue.severity == 'LOW':
                self.stats['low_issues'] += 1

        return self.issues, self.stats

    def calculate_security_score(self) -> float:
        """Calculate a security score from 0-100."""
        if self.stats['files_scanned'] == 0:
            return 100.0

        # Scoring weights
        weights = {
            'CRITICAL': 25,
            'HIGH': 10,
            'MEDIUM': 5,
            'LOW': 2
        }

        # Calculate deductions
        deductions = (
            self.stats['critical_issues'] * weights['CRITICAL'] +
            self.stats['high_issues'] * weights['HIGH'] +
            self.stats['medium_issues'] * weights['MEDIUM'] +
            self.stats['low_issues'] * weights['LOW']
        )

        # Calculate score (max deduction is 100)
        score = max(0, 100 - deductions)
        return score

    def validate_for_commit(self, threshold: float = 95.0) -> bool:
        """Validate if the code is secure enough for commit."""
        issues, stats = self.run_scan()
        score = self.calculate_security_score()

        print(f"\n📊 Security Scan Results:")
        print(f"   Files scanned: {stats['files_scanned']}")
        print(f"   Secrets found: {stats['secrets_found']}")
        print(f"   Vulnerabilities: {stats['vulnerabilities_found']}")
        print(f"   Critical issues: {stats['critical_issues']}")
        print(f"   High issues: {stats['high_issues']}")
        print(f"   Medium issues: {stats['medium_issues']}")
        print(f"   Low issues: {stats['low_issues']}")
        print(f"\n🎯 Security Score: {score:.1f}%")

        if stats['critical_issues'] > 0:
            print("\n❌ CRITICAL ISSUES FOUND:")
            for issue in issues:
                if issue.severity == 'CRITICAL':
                    print(f"   📁 {issue.file_path}:{issue.line_number}")
                    print(f"      {issue.description}")
                    print(f"      💡 {issue.remediation}")
            return False

        if score < threshold:
            print(f"\n⚠️  Security score {score:.1f}% is below threshold {threshold}%")
            if stats['high_issues'] > 0:
                print("\n⚠️  HIGH SEVERITY ISSUES:")
                for issue in issues[:5]:  # Show first 5 issues
                    if issue.severity == 'HIGH':
                        print(f"   📁 {issue.file_path}:{issue.line_number}")
                        print(f"      {issue.description}")
            return False

        return True


def main():
    """Main entry point for the security monitor."""
    parser = argparse.ArgumentParser(description='ToolBoxAI Security Monitor')
    parser.add_argument('--validate-hooks', action='store_true',
                        help='Validate security for pre-commit hooks')
    parser.add_argument('--run-scan', action='store_true',
                        help='Run a full security scan')
    parser.add_argument('--threshold', type=float, default=95.0,
                        help='Minimum security score threshold (default: 95.0)')
    parser.add_argument('--output-json', type=str,
                        help='Output results to JSON file')

    args = parser.parse_args()

    monitor = SecurityMonitor()

    if args.validate_hooks:
        # Pre-commit validation mode
        is_valid = monitor.validate_for_commit(args.threshold)
        if not is_valid:
            sys.exit(1)
        print("✅ Security validation passed")
        sys.exit(0)

    elif args.run_scan:
        # Full scan mode
        issues, stats = monitor.run_scan()
        score = monitor.calculate_security_score()

        print("\n" + "="*60)
        print("SECURITY SCAN COMPLETE")
        print("="*60)
        print(f"Security Score: {score:.1f}%")
        print(f"Total Issues: {len(issues)}")

        if args.output_json:
            # Save results to JSON
            results = {
                'score': score,
                'stats': stats,
                'issues': [
                    {
                        'severity': issue.severity,
                        'category': issue.category,
                        'file': issue.file_path,
                        'line': issue.line_number,
                        'description': issue.description,
                        'remediation': issue.remediation
                    }
                    for issue in issues
                ]
            }
            with open(args.output_json, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to {args.output_json}")

        # Exit with error if critical issues found
        if stats['critical_issues'] > 0:
            sys.exit(1)

    else:
        # Default: show help
        parser.print_help()


if __name__ == '__main__':
    main()