"""
Security Audit Agent - Performs comprehensive security audits
Scans for vulnerabilities, misconfigurations, and compliance issues
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from core.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SecurityAuditAgent(BaseAgent):
    """
    Specialized agent for performing security audits
    Identifies vulnerabilities, misconfigurations, and security best practice violations
    """

    def __init__(self):
        """Initialize the Security Audit Agent"""
        super().__init__(
            name="SecurityAuditAgent",
            description="Performs comprehensive security audits and vulnerability assessments"
        )

        # Security patterns to check
        self.sensitive_patterns = {
            'aws_access_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret_key': r'[0-9a-zA-Z/+=]{40}',
            'api_key': r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})',
            'private_key': r'-----BEGIN (RSA|EC|DSA) PRIVATE KEY-----',
            'jwt_token': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
            'github_token': r'ghp_[a-zA-Z0-9]{36}',
            'stripe_key': r'sk_live_[a-zA-Z0-9]{24}',
            'password': r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)'
        }

        # Security headers to check
        self.required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Content-Security-Policy',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]

        # Audit history
        self.audit_history = []

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Execute security audit using SPARC framework

        Args:
            task: Audit task with scope and parameters

        Returns:
            Audit results with findings and recommendations
        """
        # Situation: Define audit scope
        situation = self._analyze_situation(task)

        # Problem: Identify security concerns
        problem = self._identify_problem(situation)

        # Alternatives: Determine audit approaches
        alternatives = self._evaluate_alternatives(problem)

        # Recommendation: Select audit strategy
        recommendation = self._make_recommendation(alternatives)

        # Conclusion: Execute audit
        result = await self._execute_recommendation(recommendation, task)

        # Store audit result
        self._store_audit_result(result)

        return result

    def _analyze_situation(self, task: dict[str, Any]) -> dict[str, Any]:
        """Analyze audit scope and requirements"""
        audit_type = task.get('audit_type', 'comprehensive')
        target = task.get('target', 'full_application')

        situation = {
            'audit_type': audit_type,
            'target': target,
            'environment': task.get('environment', 'development'),
            'include_dependencies': task.get('include_dependencies', True),
            'scan_depth': task.get('scan_depth', 'deep'),
            'compliance_check': task.get('compliance_check', True),
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"Starting security audit: {audit_type} for {target}")
        return situation

    def _identify_problem(self, situation: dict[str, Any]) -> dict[str, Any]:
        """Identify potential security problems to check"""
        problems = []

        if situation['audit_type'] in ['comprehensive', 'secrets']:
            problems.append('exposed_secrets')

        if situation['audit_type'] in ['comprehensive', 'configuration']:
            problems.append('misconfigurations')

        if situation['audit_type'] in ['comprehensive', 'vulnerabilities']:
            problems.append('known_vulnerabilities')

        if situation['compliance_check']:
            problems.append('compliance_violations')

        return {
            'check_areas': problems,
            'priority': self._determine_priority(situation),
            'risk_level': 'high' if situation['environment'] == 'production' else 'medium'
        }

    def _evaluate_alternatives(self, problem: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate audit approaches"""
        alternatives = []

        if 'exposed_secrets' in problem['check_areas']:
            alternatives.append({
                'approach': 'secret_scanning',
                'priority': 1,
                'tools': ['regex_patterns', 'entropy_analysis']
            })

        if 'misconfigurations' in problem['check_areas']:
            alternatives.append({
                'approach': 'config_audit',
                'priority': 2,
                'tools': ['config_parser', 'security_headers']
            })

        if 'known_vulnerabilities' in problem['check_areas']:
            alternatives.append({
                'approach': 'dependency_scanning',
                'priority': 3,
                'tools': ['dependency_check', 'cve_database']
            })

        return alternatives

    def _make_recommendation(self, alternatives: list[dict[str, Any]]) -> dict[str, Any]:
        """Recommend audit strategy"""
        return {
            'strategy': 'multi-layered_audit',
            'approaches': alternatives,
            'execution_order': sorted(alternatives, key=lambda x: x['priority'])
        }

    async def _execute_recommendation(self, recommendation: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
        """Execute the security audit"""
        action = task.get('action', 'full_audit')

        try:
            if action == 'full_audit':
                return await self._perform_full_audit(task)
            elif action == 'scan_secrets':
                return await self._scan_for_secrets(task)
            elif action == 'check_configurations':
                return await self._check_configurations(task)
            elif action == 'scan_vulnerabilities':
                return await self._scan_vulnerabilities(task)
            elif action == 'check_headers':
                return await self._check_security_headers(task)
            elif action == 'audit_permissions':
                return await self._audit_permissions(task)
            elif action == 'generate_report':
                return await self._generate_audit_report(task)
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown audit action: {action}'
                }
        except Exception as e:
            logger.error(f"Audit error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _perform_full_audit(self, task: dict[str, Any]) -> dict[str, Any]:
        """Perform comprehensive security audit"""
        audit_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': task.get('environment', 'development'),
            'findings': {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'info': []
            },
            'summary': {},
            'recommendations': []
        }

        # 1. Scan for exposed secrets
        secrets_result = await self._scan_for_secrets(task)
        if secrets_result['status'] == 'success' and secrets_result.get('secrets_found'):
            for secret in secrets_result['secrets_found']:
                audit_results['findings']['critical'].append({
                    'type': 'exposed_secret',
                    'details': secret,
                    'severity': 'critical'
                })

        # 2. Check configurations
        config_result = await self._check_configurations(task)
        if config_result['status'] == 'success':
            for issue in config_result.get('issues', []):
                severity = issue.get('severity', 'medium')
                audit_results['findings'][severity].append({
                    'type': 'misconfiguration',
                    'details': issue
                })

        # 3. Scan for vulnerabilities
        vuln_result = await self._scan_vulnerabilities(task)
        if vuln_result['status'] == 'success':
            for vuln in vuln_result.get('vulnerabilities', []):
                severity = vuln.get('severity', 'medium').lower()
                audit_results['findings'][severity].append({
                    'type': 'vulnerability',
                    'details': vuln
                })

        # 4. Check security headers
        headers_result = await self._check_security_headers(task)
        if headers_result['status'] == 'success':
            for missing_header in headers_result.get('missing_headers', []):
                audit_results['findings']['medium'].append({
                    'type': 'missing_security_header',
                    'details': {'header': missing_header}
                })

        # 5. Audit permissions
        perm_result = await self._audit_permissions(task)
        if perm_result['status'] == 'success':
            for issue in perm_result.get('permission_issues', []):
                audit_results['findings']['high'].append({
                    'type': 'permission_issue',
                    'details': issue
                })

        # Generate summary
        audit_results['summary'] = {
            'total_findings': sum(len(findings) for findings in audit_results['findings'].values()),
            'critical_count': len(audit_results['findings']['critical']),
            'high_count': len(audit_results['findings']['high']),
            'medium_count': len(audit_results['findings']['medium']),
            'low_count': len(audit_results['findings']['low']),
            'info_count': len(audit_results['findings']['info'])
        }

        # Generate recommendations
        audit_results['recommendations'] = self._generate_recommendations(audit_results)

        # Calculate risk score
        audit_results['risk_score'] = self._calculate_risk_score(audit_results)

        return {
            'status': 'success',
            'audit_results': audit_results
        }

    async def _scan_for_secrets(self, task: dict[str, Any]) -> dict[str, Any]:
        """Scan for exposed secrets in code and configuration"""
        target_path = task.get('target_path', '.')
        exclude_paths = task.get('exclude_paths', ['.git', 'node_modules', '__pycache__', 'venv'])

        secrets_found = []
        files_scanned = 0

        # Get all files to scan
        path = Path(target_path)

        for file_path in path.rglob('*'):
            # Skip excluded paths
            if any(excluded in str(file_path) for excluded in exclude_paths):
                continue

            if file_path.is_file():
                files_scanned += 1

                try:
                    # Read file content
                    with open(file_path, encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Check each sensitive pattern
                    for pattern_name, pattern_regex in self.sensitive_patterns.items():
                        matches = re.finditer(pattern_regex, content, re.IGNORECASE | re.MULTILINE)

                        for match in matches:
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1

                            secrets_found.append({
                                'type': pattern_name,
                                'file': str(file_path.relative_to(path)),
                                'line': line_num,
                                'pattern_matched': pattern_name,
                                'severity': 'critical' if pattern_name in ['aws_secret_key', 'private_key'] else 'high'
                            })

                except Exception:
                    # Skip files that can't be read
                    continue

        # Also check for high entropy strings (potential secrets)
        entropy_secrets = self._find_high_entropy_strings(target_path, exclude_paths)
        secrets_found.extend(entropy_secrets)

        return {
            'status': 'success',
            'files_scanned': files_scanned,
            'secrets_found': secrets_found,
            'total_secrets': len(secrets_found)
        }

    def _find_high_entropy_strings(self, target_path: str, exclude_paths: list[str]) -> list[dict[str, Any]]:
        """Find strings with high entropy that might be secrets"""
        high_entropy_findings = []

        # Shannon entropy calculation
        def calculate_entropy(string: str) -> float:
            if not string:
                return 0

            entropy = 0
            for char in set(string):
                freq = string.count(char) / len(string)
                entropy -= freq * (freq if freq == 0 else freq * (1 / freq))

            return entropy

        # This would scan for high entropy strings
        # Implementation simplified for demonstration

        return high_entropy_findings

    async def _check_configurations(self, task: dict[str, Any]) -> dict[str, Any]:
        """Check for security misconfigurations"""
        issues = []

        # Check CORS configuration
        cors_check = self._check_cors_configuration(task)
        if cors_check:
            issues.extend(cors_check)

        # Check authentication configuration
        auth_check = self._check_authentication_config(task)
        if auth_check:
            issues.extend(auth_check)

        # Check database configuration
        db_check = self._check_database_config(task)
        if db_check:
            issues.extend(db_check)

        # Check TLS/SSL configuration
        tls_check = self._check_tls_config(task)
        if tls_check:
            issues.extend(tls_check)

        return {
            'status': 'success',
            'issues': issues,
            'total_issues': len(issues)
        }

    def _check_cors_configuration(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        """Check CORS configuration for security issues"""
        issues = []

        # Check for wildcard origins
        if task.get('cors_origins') == '*':
            issues.append({
                'issue': 'CORS wildcard origin',
                'severity': 'high',
                'description': 'CORS allows any origin (*), which is a security risk',
                'recommendation': 'Specify exact allowed origins'
            })

        return issues

    def _check_authentication_config(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        """Check authentication configuration"""
        issues = []

        # Check JWT expiration
        jwt_expiration = task.get('jwt_expiration_minutes', 1440)
        if jwt_expiration > 1440:  # More than 24 hours
            issues.append({
                'issue': 'Long JWT expiration',
                'severity': 'medium',
                'description': f'JWT tokens expire after {jwt_expiration} minutes',
                'recommendation': 'Reduce JWT expiration to 15-60 minutes'
            })

        # Check password policy
        if not task.get('password_policy'):
            issues.append({
                'issue': 'Missing password policy',
                'severity': 'medium',
                'description': 'No password complexity requirements defined',
                'recommendation': 'Implement strong password policy'
            })

        return issues

    def _check_database_config(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        """Check database configuration"""
        issues = []

        # Check for default credentials
        if task.get('db_password') in ['password', 'admin', 'root', '123456']:
            issues.append({
                'issue': 'Weak database password',
                'severity': 'critical',
                'description': 'Database using weak or default password',
                'recommendation': 'Use strong, unique database password'
            })

        # Check for encryption
        if not task.get('db_encryption_enabled', False):
            issues.append({
                'issue': 'Database encryption disabled',
                'severity': 'high',
                'description': 'Database not using encryption at rest',
                'recommendation': 'Enable database encryption'
            })

        return issues

    def _check_tls_config(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        """Check TLS/SSL configuration"""
        issues = []

        # Check TLS version
        tls_version = task.get('tls_version', '1.2')
        if tls_version < '1.2':
            issues.append({
                'issue': 'Outdated TLS version',
                'severity': 'high',
                'description': f'Using TLS {tls_version}',
                'recommendation': 'Use TLS 1.2 or higher'
            })

        return issues

    async def _scan_vulnerabilities(self, task: dict[str, Any]) -> dict[str, Any]:
        """Scan for known vulnerabilities in dependencies"""
        vulnerabilities = []

        # Check Python dependencies
        if task.get('scan_python', True):
            python_vulns = self._scan_python_dependencies()
            vulnerabilities.extend(python_vulns)

        # Check Node.js dependencies
        if task.get('scan_nodejs', True):
            nodejs_vulns = self._scan_nodejs_dependencies()
            vulnerabilities.extend(nodejs_vulns)

        # Check Docker images
        if task.get('scan_docker', True):
            docker_vulns = self._scan_docker_images()
            vulnerabilities.extend(docker_vulns)

        return {
            'status': 'success',
            'vulnerabilities': vulnerabilities,
            'total_vulnerabilities': len(vulnerabilities)
        }

    def _scan_python_dependencies(self) -> list[dict[str, Any]]:
        """Scan Python dependencies for vulnerabilities"""
        vulnerabilities = []

        # This would use tools like safety or pip-audit
        # Simplified implementation for demonstration

        try:
            # Check if requirements.txt exists
            if Path('requirements.txt').exists():
                # Would run: safety check --json
                # For now, return empty list
                pass
        except Exception as e:
            logger.error(f"Error scanning Python dependencies: {e}")

        return vulnerabilities

    def _scan_nodejs_dependencies(self) -> list[dict[str, Any]]:
        """Scan Node.js dependencies for vulnerabilities"""
        vulnerabilities = []

        # This would use npm audit or yarn audit
        # Simplified implementation

        try:
            if Path('package.json').exists():
                # Would run: npm audit --json
                pass
        except Exception as e:
            logger.error(f"Error scanning Node.js dependencies: {e}")

        return vulnerabilities

    def _scan_docker_images(self) -> list[dict[str, Any]]:
        """Scan Docker images for vulnerabilities"""
        vulnerabilities = []

        # This would use tools like Trivy or Clair
        # Simplified implementation

        return vulnerabilities

    async def _check_security_headers(self, task: dict[str, Any]) -> dict[str, Any]:
        """Check for required security headers"""
        missing_headers = []

        configured_headers = task.get('configured_headers', [])

        for required_header in self.required_headers:
            if required_header not in configured_headers:
                missing_headers.append(required_header)

        return {
            'status': 'success',
            'missing_headers': missing_headers,
            'configured_headers': configured_headers,
            'compliance': len(missing_headers) == 0
        }

    async def _audit_permissions(self, task: dict[str, Any]) -> dict[str, Any]:
        """Audit file and access permissions"""
        permission_issues = []

        # Check file permissions
        sensitive_files = task.get('sensitive_files', ['.env', 'config.json', 'secrets.yaml'])

        for file_path in sensitive_files:
            if Path(file_path).exists():
                # Check file permissions
                # Would check for overly permissive permissions
                pass

        # Check IAM permissions (for cloud deployments)
        if task.get('check_iam', False):
            # Would check IAM policies for least privilege
            pass

        return {
            'status': 'success',
            'permission_issues': permission_issues
        }

    async def _generate_audit_report(self, task: dict[str, Any]) -> dict[str, Any]:
        """Generate comprehensive audit report"""
        audit_result = await self._perform_full_audit(task)

        if audit_result['status'] != 'success':
            return audit_result

        audit_data = audit_result['audit_results']

        report = {
            'title': 'Security Audit Report',
            'generated_at': datetime.utcnow().isoformat(),
            'environment': audit_data['environment'],
            'executive_summary': self._generate_executive_summary(audit_data),
            'risk_score': audit_data['risk_score'],
            'findings': audit_data['findings'],
            'recommendations': audit_data['recommendations'],
            'remediation_timeline': self._generate_remediation_timeline(audit_data)
        }

        return {
            'status': 'success',
            'report': report
        }

    def _generate_recommendations(self, audit_results: dict[str, Any]) -> list[str]:
        """Generate security recommendations based on findings"""
        recommendations = []

        if audit_results['summary']['critical_count'] > 0:
            recommendations.append("IMMEDIATE: Address all critical security findings")

        if audit_results['summary']['high_count'] > 0:
            recommendations.append("HIGH PRIORITY: Fix high severity issues within 48 hours")

        # Specific recommendations based on finding types
        finding_types = set()
        for severity_findings in audit_results['findings'].values():
            for finding in severity_findings:
                finding_types.add(finding['type'])

        if 'exposed_secret' in finding_types:
            recommendations.append("Rotate all exposed credentials immediately")
            recommendations.append("Implement AWS Secrets Manager for credential storage")

        if 'misconfiguration' in finding_types:
            recommendations.append("Review and harden all security configurations")

        if 'vulnerability' in finding_types:
            recommendations.append("Update all vulnerable dependencies")

        if 'missing_security_header' in finding_types:
            recommendations.append("Implement all required security headers")

        if 'permission_issue' in finding_types:
            recommendations.append("Apply principle of least privilege to all permissions")

        return recommendations

    def _calculate_risk_score(self, audit_results: dict[str, Any]) -> int:
        """Calculate overall risk score (0-100)"""
        score = 0

        # Weight by severity
        score += audit_results['summary']['critical_count'] * 20
        score += audit_results['summary']['high_count'] * 10
        score += audit_results['summary']['medium_count'] * 5
        score += audit_results['summary']['low_count'] * 2
        score += audit_results['summary']['info_count'] * 1

        # Cap at 100
        return min(score, 100)

    def _generate_executive_summary(self, audit_data: dict[str, Any]) -> str:
        """Generate executive summary for audit report"""
        risk_score = audit_data['risk_score']

        if risk_score >= 80:
            return f"CRITICAL: The security audit identified {audit_data['summary']['total_findings']} findings with a risk score of {risk_score}/100. Immediate action required."
        elif risk_score >= 50:
            return f"HIGH RISK: The audit found {audit_data['summary']['total_findings']} security issues with a risk score of {risk_score}/100. Urgent remediation recommended."
        elif risk_score >= 20:
            return f"MEDIUM RISK: The audit identified {audit_data['summary']['total_findings']} findings with a risk score of {risk_score}/100. Schedule remediation soon."
        else:
            return f"LOW RISK: The audit found {audit_data['summary']['total_findings']} minor issues with a risk score of {risk_score}/100. Good security posture overall."

    def _generate_remediation_timeline(self, audit_data: dict[str, Any]) -> dict[str, str]:
        """Generate recommended remediation timeline"""
        return {
            'critical': 'Immediately',
            'high': 'Within 48 hours',
            'medium': 'Within 1 week',
            'low': 'Within 1 month',
            'info': 'Next maintenance window'
        }

    def _determine_priority(self, situation: dict[str, Any]) -> str:
        """Determine audit priority"""
        if situation['environment'] == 'production':
            return 'critical'
        elif situation['audit_type'] == 'comprehensive':
            return 'high'
        else:
            return 'medium'

    def _store_audit_result(self, result: dict[str, Any]):
        """Store audit result in history"""
        self.audit_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'result': result
        })

        # Keep only last 100 audits
        if len(self.audit_history) > 100:
            self.audit_history = self.audit_history[-100:]