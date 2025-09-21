#!/usr/bin/env python3
"""
Security Hardening Progress Monitor
Tracks security improvements from 85% to 95% target score
"""

import subprocess
import json
import re
import datetime
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import sqlite3

@dataclass
class SecurityIssue:
    id: str
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "dependency", "code", "config", "secret"
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fixed: bool = False
    fix_date: Optional[datetime.datetime] = None

@dataclass
class SecurityMetrics:
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    fixed_issues: int
    security_score: float
    target_score: float = 95.0
    last_scan: datetime.datetime = None
    trend: str = "stable"
    vulnerabilities_by_category: Dict[str, int] = None

class SecurityMonitor:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.db_path = self.project_root / "monitoring" / "security_metrics.db"
        self.baseline_score = 85.0
        self.target_score = 95.0
        self.init_database()
        self.history = []

    def init_database(self):
        """Initialize SQLite database for security tracking"""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_issues (
                    id TEXT PRIMARY KEY,
                    severity TEXT,
                    category TEXT,
                    description TEXT,
                    file_path TEXT,
                    line_number INTEGER,
                    fixed BOOLEAN DEFAULT FALSE,
                    discovered_date DATETIME,
                    fix_date DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_scans (
                    timestamp DATETIME PRIMARY KEY,
                    total_issues INTEGER,
                    critical_issues INTEGER,
                    high_issues INTEGER,
                    medium_issues INTEGER,
                    low_issues INTEGER,
                    security_score REAL,
                    scan_type TEXT
                )
            """)

    def run_dependency_security_scan(self) -> List[SecurityIssue]:
        """Scan for security vulnerabilities in dependencies"""
        issues = []

        # Safety check for Python dependencies
        try:
            result = subprocess.run(
                ["python", "-m", "safety", "check", "--json", "--ignore", "70612"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0 and result.stdout:
                try:
                    safety_data = json.loads(result.stdout)
                    for vuln in safety_data:
                        issue_id = hashlib.md5(f"safety_{vuln.get('id', '')}_{vuln.get('package_name', '')}".encode()).hexdigest()
                        issues.append(SecurityIssue(
                            id=issue_id,
                            severity=self.map_safety_severity(vuln.get('severity', 'medium')),
                            category="dependency",
                            description=f"Vulnerable package: {vuln.get('package_name', 'unknown')} - {vuln.get('advisory', 'No description')}",
                            file_path="requirements.txt"
                        ))
                except json.JSONDecodeError:
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Safety not available, check manually for known vulnerable packages
            issues.extend(self.check_known_vulnerabilities())

        # Check for npm vulnerabilities if Node.js project
        if (self.project_root / "package.json").exists():
            issues.extend(self.run_npm_audit())

        return issues

    def run_npm_audit(self) -> List[SecurityIssue]:
        """Run npm audit for Node.js dependencies"""
        issues = []
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    advisories = audit_data.get('advisories', {})

                    for vuln_id, vuln in advisories.items():
                        issue_id = hashlib.md5(f"npm_{vuln_id}".encode()).hexdigest()
                        issues.append(SecurityIssue(
                            id=issue_id,
                            severity=vuln.get('severity', 'medium'),
                            category="dependency",
                            description=f"NPM vulnerability: {vuln.get('module_name', 'unknown')} - {vuln.get('title', 'No description')}",
                            file_path="package.json"
                        ))
                except json.JSONDecodeError:
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return issues

    def check_known_vulnerabilities(self) -> List[SecurityIssue]:
        """Check for known vulnerable patterns in requirements"""
        issues = []
        requirements_file = self.project_root / "requirements.txt"

        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                content = f.read().lower()

                # Known vulnerable packages and versions
                vulnerable_patterns = {
                    'pillow<8.3.2': 'critical',
                    'jinja2<2.11.3': 'high',
                    'urllib3<1.26.5': 'medium',
                    'requests<2.25.1': 'medium',
                    'django<3.2.13': 'high',
                    'flask<2.0.0': 'medium'
                }

                for pattern, severity in vulnerable_patterns.items():
                    package_name = pattern.split('<')[0]
                    if package_name in content:
                        issue_id = hashlib.md5(f"known_{package_name}".encode()).hexdigest()
                        issues.append(SecurityIssue(
                            id=issue_id,
                            severity=severity,
                            category="dependency",
                            description=f"Potentially vulnerable package: {package_name}",
                            file_path="requirements.txt"
                        ))

        return issues

    def run_code_security_scan(self) -> List[SecurityIssue]:
        """Scan source code for security issues"""
        issues = []

        # Check for common security anti-patterns
        python_files = list(self.project_root.glob("**/*.py"))

        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    issues.extend(self.scan_file_for_issues(file_path, content))
            except Exception:
                continue

        return issues

    def scan_file_for_issues(self, file_path: Path, content: str) -> List[SecurityIssue]:
        """Scan individual file for security issues"""
        issues = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower().strip()

            # Check for hardcoded secrets
            if any(pattern in line_lower for pattern in [
                'password =', 'secret =', 'token =', 'api_key =', 'private_key ='
            ]) and not line_lower.startswith('#'):
                if not any(safe in line_lower for safe in ['none', 'null', 'false', 'true', 'input', 'environ']):
                    issue_id = hashlib.md5(f"secret_{file_path}_{line_num}".encode()).hexdigest()
                    issues.append(SecurityIssue(
                        id=issue_id,
                        severity="high",
                        category="secret",
                        description="Potential hardcoded secret",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num
                    ))

            # Check for SQL injection patterns
            if 'execute(' in line_lower and '%' in line and 'format' in line:
                issue_id = hashlib.md5(f"sql_{file_path}_{line_num}".encode()).hexdigest()
                issues.append(SecurityIssue(
                    id=issue_id,
                    severity="high",
                    category="code",
                    description="Potential SQL injection vulnerability",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num
                ))

            # Check for unsafe deserialization
            if any(unsafe in line_lower for unsafe in ['pickle.loads', 'eval(', 'exec(']):
                issue_id = hashlib.md5(f"unsafe_{file_path}_{line_num}".encode()).hexdigest()
                issues.append(SecurityIssue(
                    id=issue_id,
                    severity="medium",
                    category="code",
                    description="Potentially unsafe operation",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num
                ))

            # Check for debug mode in production
            if 'debug=true' in line_lower or 'debug = true' in line_lower:
                issue_id = hashlib.md5(f"debug_{file_path}_{line_num}".encode()).hexdigest()
                issues.append(SecurityIssue(
                    id=issue_id,
                    severity="medium",
                    category="config",
                    description="Debug mode enabled",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num
                ))

        return issues

    def run_configuration_security_scan(self) -> List[SecurityIssue]:
        """Scan configuration files for security issues"""
        issues = []

        # Check environment files
        env_files = ['.env', '.env.example', '.env.production', '.env.staging']
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                issues.extend(self.scan_env_file(env_path))

        # Check Docker files
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.production.yml']
        for docker_file in docker_files:
            docker_path = self.project_root / docker_file
            if docker_path.exists():
                issues.extend(self.scan_docker_file(docker_path))

        return issues

    def scan_env_file(self, file_path: Path) -> List[SecurityIssue]:
        """Scan environment file for security issues"""
        issues = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # Skip comments and empty lines
                if not line_stripped or line_stripped.startswith('#'):
                    continue

                # Check for weak passwords
                if 'PASSWORD=' in line.upper() and '=' in line:
                    password = line.split('=', 1)[1].strip('"\'')
                    if len(password) < 8 or password.lower() in ['password', '12345', 'admin']:
                        issue_id = hashlib.md5(f"weak_pass_{file_path}_{line_num}".encode()).hexdigest()
                        issues.append(SecurityIssue(
                            id=issue_id,
                            severity="medium",
                            category="config",
                            description="Weak password in environment file",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num
                        ))

                # Check for exposed secrets
                if any(secret in line.upper() for secret in ['SECRET=', 'TOKEN=', 'KEY=']):
                    if '=' in line:
                        value = line.split('=', 1)[1].strip('"\'')
                        if value and not value.startswith('${') and len(value) > 10:
                            issue_id = hashlib.md5(f"exposed_secret_{file_path}_{line_num}".encode()).hexdigest()
                            issues.append(SecurityIssue(
                                id=issue_id,
                                severity="high",
                                category="secret",
                                description="Potential exposed secret in environment file",
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_num
                            ))

        except Exception:
            pass

        return issues

    def scan_docker_file(self, file_path: Path) -> List[SecurityIssue]:
        """Scan Docker file for security issues"""
        issues = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip().upper()

                # Check for running as root
                if line_stripped.startswith('USER ROOT') or 'USER 0' in line_stripped:
                    issue_id = hashlib.md5(f"root_user_{file_path}_{line_num}".encode()).hexdigest()
                    issues.append(SecurityIssue(
                        id=issue_id,
                        severity="medium",
                        category="config",
                        description="Container running as root user",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num
                    ))

                # Check for latest tag usage
                if 'FROM' in line_stripped and ':LATEST' in line_stripped:
                    issue_id = hashlib.md5(f"latest_tag_{file_path}_{line_num}".encode()).hexdigest()
                    issues.append(SecurityIssue(
                        id=issue_id,
                        severity="low",
                        category="config",
                        description="Using 'latest' tag in Docker image",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num
                    ))

        except Exception:
            pass

        return issues

    def map_safety_severity(self, severity: str) -> str:
        """Map safety severity to standard levels"""
        severity_map = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        return severity_map.get(severity.lower(), 'medium')

    def calculate_security_score(self, issues: List[SecurityIssue]) -> float:
        """Calculate overall security score"""
        if not issues:
            return 100.0

        # Weight different severities
        weights = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 1
        }

        total_penalty = sum(weights.get(issue.severity, 5) for issue in issues if not issue.fixed)
        fixed_bonus = sum(weights.get(issue.severity, 5) * 0.5 for issue in issues if issue.fixed)

        # Start from baseline and adjust
        base_score = 100.0
        penalty_score = max(0, base_score - total_penalty)
        final_score = min(100.0, penalty_score + fixed_bonus)

        return final_score

    def update_issue_status(self, issues: List[SecurityIssue]):
        """Update database with current issues"""
        with sqlite3.connect(self.db_path) as conn:
            # Mark all existing issues as potentially fixed
            conn.execute("UPDATE security_issues SET fixed = TRUE, fix_date = ? WHERE fixed = FALSE",
                        (datetime.datetime.now().isoformat(),))

            # Insert/update current issues
            for issue in issues:
                conn.execute("""
                    INSERT OR REPLACE INTO security_issues
                    (id, severity, category, description, file_path, line_number, fixed, discovered_date)
                    VALUES (?, ?, ?, ?, ?, ?, FALSE, ?)
                """, (
                    issue.id, issue.severity, issue.category, issue.description,
                    issue.file_path, issue.line_number, datetime.datetime.now().isoformat()
                ))

            # Get count of fixed issues
            cursor = conn.execute("SELECT COUNT(*) FROM security_issues WHERE fixed = TRUE")
            fixed_count = cursor.fetchone()[0]

            return fixed_count

    def run_comprehensive_scan(self) -> SecurityMetrics:
        """Run comprehensive security scan"""
        all_issues = []

        print("🔍 Running dependency security scan...")
        all_issues.extend(self.run_dependency_security_scan())

        print("🔍 Running code security scan...")
        all_issues.extend(self.run_code_security_scan())

        print("🔍 Running configuration security scan...")
        all_issues.extend(self.run_configuration_security_scan())

        # Update database and get fix count
        fixed_count = self.update_issue_status(all_issues)

        # Calculate metrics
        severity_counts = {
            'critical': len([i for i in all_issues if i.severity == 'critical']),
            'high': len([i for i in all_issues if i.severity == 'high']),
            'medium': len([i for i in all_issues if i.severity == 'medium']),
            'low': len([i for i in all_issues if i.severity == 'low'])
        }

        category_counts = {}
        for issue in all_issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

        security_score = self.calculate_security_score(all_issues)

        # Determine trend
        trend = "stable"
        if self.history:
            last_score = self.history[-1].security_score
            if security_score > last_score + 2:
                trend = "improving"
            elif security_score < last_score - 2:
                trend = "declining"

        # Store scan results
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO security_scans VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.datetime.now().isoformat(),
                len(all_issues),
                severity_counts['critical'],
                severity_counts['high'],
                severity_counts['medium'],
                severity_counts['low'],
                security_score,
                "comprehensive"
            ))

        metrics = SecurityMetrics(
            total_issues=len(all_issues),
            critical_issues=severity_counts['critical'],
            high_issues=severity_counts['high'],
            medium_issues=severity_counts['medium'],
            low_issues=severity_counts['low'],
            fixed_issues=fixed_count,
            security_score=security_score,
            target_score=self.target_score,
            last_scan=datetime.datetime.now(),
            trend=trend,
            vulnerabilities_by_category=category_counts
        )

        self.history.append(metrics)
        return metrics

    def generate_security_report(self, metrics: SecurityMetrics) -> str:
        """Generate detailed security monitoring report"""

        def progress_bar(current: float, target: float, width: int = 30) -> str:
            percentage = min(100, (current / target) * 100)
            filled = int(width * percentage / 100)
            bar = '█' * filled + '▒' * (width - filled)
            return f"[{bar}] {percentage:.1f}%"

        # Calculate improvement from baseline
        improvement = metrics.security_score - self.baseline_score
        remaining_gap = self.target_score - metrics.security_score

        report = f"""
{'='*60}
🔒 SECURITY HARDENING MONITORING
{'='*60}
Last Scan: {metrics.last_scan.strftime('%Y-%m-%d %H:%M:%S')}

📊 SECURITY SCORE
Current: {metrics.security_score:.1f}% / {metrics.target_score}%
{progress_bar(metrics.security_score, metrics.target_score)}

Progress: +{improvement:.1f}% from baseline ({self.baseline_score}%)
Remaining: {remaining_gap:.1f}% to reach target

📈 VULNERABILITY BREAKDOWN
Total Issues: {metrics.total_issues}
  🔥 Critical: {metrics.critical_issues:3d}
  ⚠️  High:     {metrics.high_issues:3d}
  📝 Medium:   {metrics.medium_issues:3d}
  💡 Low:      {metrics.low_issues:3d}

✅ Fixed Issues: {metrics.fixed_issues}
📊 Trend: {metrics.trend.upper()}

🔍 ISSUES BY CATEGORY
"""

        if metrics.vulnerabilities_by_category:
            for category, count in sorted(metrics.vulnerabilities_by_category.items()):
                category_emoji = {
                    'dependency': '📦',
                    'code': '🐛',
                    'config': '⚙️',
                    'secret': '🔐'
                }.get(category, '📋')
                report += f"  {category_emoji} {category.title()}: {count}\n"

        # Priority recommendations
        report += "\n🎯 PRIORITY ACTIONS\n"

        if metrics.critical_issues > 0:
            report += f"  🔥 URGENT: Fix {metrics.critical_issues} critical vulnerabilities\n"

        if metrics.high_issues > 0:
            report += f"  ⚠️  HIGH: Address {metrics.high_issues} high-severity issues\n"

        # Score improvement suggestions
        if metrics.security_score < 90:
            report += "  📈 Focus on dependency updates and secret management\n"

        if metrics.security_score >= 90:
            report += "  🔧 Fine-tune configuration and code patterns\n"

        # Calculate effort estimate
        total_effort_hours = (
            metrics.critical_issues * 2 +
            metrics.high_issues * 1 +
            metrics.medium_issues * 0.5 +
            metrics.low_issues * 0.25
        )

        report += f"""
⏱️  ESTIMATED EFFORT
Total effort to reach 95%: {total_effort_hours:.1f} hours
Critical fixes: {metrics.critical_issues * 2:.0f} hours
High priority: {metrics.high_issues * 1:.0f} hours
Medium/Low: {(metrics.medium_issues * 0.5 + metrics.low_issues * 0.25):.1f} hours

🎯 TARGET TIMELINE
At current pace: {'✅ On track' if improvement > 0 else '⚠️ Needs acceleration'}
To reach 95%: {'✅ Achievable' if remaining_gap < 10 else '🔥 Requires focus'}
"""

        report += f"\n{'='*60}\n"

        return report

    def export_metrics(self, metrics: SecurityMetrics, output_file: str = None):
        """Export metrics to JSON for integration"""
        if output_file is None:
            output_file = self.project_root / "monitoring" / "security_metrics.json"

        output_file = Path(output_file)
        output_file.parent.mkdir(exist_ok=True)

        data = {
            'timestamp': metrics.last_scan.isoformat(),
            'security_score': metrics.security_score,
            'target_score': metrics.target_score,
            'baseline_score': self.baseline_score,
            'improvement': metrics.security_score - self.baseline_score,
            'remaining_gap': metrics.target_score - metrics.security_score,
            'total_issues': metrics.total_issues,
            'critical_issues': metrics.critical_issues,
            'high_issues': metrics.high_issues,
            'medium_issues': metrics.medium_issues,
            'low_issues': metrics.low_issues,
            'fixed_issues': metrics.fixed_issues,
            'trend': metrics.trend,
            'vulnerabilities_by_category': metrics.vulnerabilities_by_category or {}
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"📁 Security metrics exported to: {output_file}")

def main():
    """Main entry point for security monitor"""
    import argparse

    parser = argparse.ArgumentParser(description="Security Hardening Monitor")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    parser.add_argument("--export", type=str, help="Export metrics to JSON file")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--interval", type=int, default=900, help="Watch interval in seconds (default: 15 min)")

    args = parser.parse_args()

    monitor = SecurityMonitor(args.project_root)

    if args.watch:
        print("🔒 Starting continuous security monitoring...")
        import time

        try:
            while True:
                metrics = monitor.run_comprehensive_scan()
                report = monitor.generate_security_report(metrics)

                # Clear screen and show report
                import os
                os.system('clear' if os.name == 'posix' else 'cls')
                print(report)

                if args.export:
                    monitor.export_metrics(metrics, args.export)

                if metrics.security_score >= monitor.target_score:
                    print("🎉 TARGET ACHIEVED! Security score reached 95%")
                    break

                print(f"⏳ Next scan in {args.interval} seconds...")
                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")

    else:
        # Single run
        metrics = monitor.run_comprehensive_scan()
        report = monitor.generate_security_report(metrics)
        print(report)

        if args.export:
            monitor.export_metrics(metrics, args.export)

if __name__ == "__main__":
    main()