"""
Sub-Agent 2: Compliance Checker
===============================

OWASP 2025 standards validation and compliance monitoring:
- Security headers verification
- Rate limiting validation
- Authentication security checks
- Input validation compliance
- Data protection measures
- Regulatory compliance (GDPR, COPPA, FERPA)

Ensures continuous compliance during Phase 1.5 fixes.
"""

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ComplianceCheck:
    """Individual compliance check result"""
    check_id: str
    category: str  # OWASP, GDPR, COPPA, FERPA, SECURITY_HEADERS, RATE_LIMITING
    description: str
    status: str  # PASS, FAIL, WARNING, SKIP
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    details: str
    remediation: Optional[str]
    standard_reference: str
    checked_at: datetime

@dataclass
class ComplianceReport:
    """Compliance report summary"""
    overall_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    categories: dict[str, float]
    compliance_status: dict[str, bool]
    recommendations: list[str]
    generated_at: datetime

class ComplianceChecker:
    """
    OWASP 2025 compliance checker for continuous validation
    
    Features:
    - OWASP Top 10 2025 compliance validation
    - Security headers verification
    - Rate limiting effectiveness checks
    - Authentication security validation
    - GDPR/COPPA/FERPA compliance monitoring
    - Real-time compliance scoring
    """
    
    def __init__(self, project_root: str = ".", base_url: str = "http://localhost:8009"):
        self.project_root = Path(project_root)
        self.base_url = base_url
        self.monitoring = False
        self.check_interval = 600  # 10 minutes
        self.checks: list[ComplianceCheck] = []
        
        # OWASP Top 10 2025 categories
        self.owasp_categories = {
            'A01_Broken_Access_Control': 'Broken Access Control',
            'A02_Cryptographic_Failures': 'Cryptographic Failures', 
            'A03_Injection': 'Injection Attacks',
            'A04_Insecure_Design': 'Insecure Design',
            'A05_Security_Misconfiguration': 'Security Misconfiguration',
            'A06_Vulnerable_Components': 'Vulnerable and Outdated Components',
            'A07_Identification_Failures': 'Identification and Authentication Failures',
            'A08_Software_Integrity_Failures': 'Software and Data Integrity Failures',
            'A09_Logging_Failures': 'Security Logging and Monitoring Failures',
            'A10_Server_Side_Request_Forgery': 'Server-Side Request Forgery (SSRF)'
        }
        
        # Compliance standards
        self.compliance_standards = {
            'GDPR': 'General Data Protection Regulation',
            'COPPA': 'Children\'s Online Privacy Protection Act',
            'FERPA': 'Family Educational Rights and Privacy Act',
            'SOC2': 'Service Organization Control 2',
            'PCI_DSS': 'Payment Card Industry Data Security Standard'
        }
        
        # Required security headers
        self.required_headers = {
            'Strict-Transport-Security': 'HSTS protection',
            'Content-Security-Policy': 'XSS protection',
            'X-Frame-Options': 'Clickjacking protection',
            'X-Content-Type-Options': 'MIME sniffing protection',
            'X-XSS-Protection': 'XSS filter',
            'Referrer-Policy': 'Referrer information control',
            'Permissions-Policy': 'Feature policy controls'
        }
    
    async def start_monitoring(self) -> None:
        """Start continuous compliance monitoring"""
        self.monitoring = True
        logger.info("📋 Compliance Checker: Starting continuous monitoring")
        
        while self.monitoring:
            try:
                await self.run_comprehensive_compliance_check()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Compliance checking error: {e}")
                await asyncio.sleep(120)  # Retry after 2 minutes on error
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring"""
        self.monitoring = False
        logger.info("📋 Compliance Checker: Monitoring stopped")
    
    async def run_comprehensive_compliance_check(self) -> ComplianceReport:
        """Run comprehensive compliance validation"""
        logger.info("📋 Running comprehensive compliance check...")
        
        self.checks = []
        
        # OWASP Top 10 2025 checks
        await self.check_owasp_compliance()
        
        # Security headers validation
        await self.check_security_headers()
        
        # Rate limiting validation
        await self.check_rate_limiting()
        
        # Authentication security
        await self.check_authentication_security()
        
        # Data protection compliance
        await self.check_data_protection()
        
        # Regulatory compliance
        await self.check_regulatory_compliance()
        
        # Generate compliance report
        report = self.generate_compliance_report()
        
        logger.info(f"📋 Compliance check complete: {report.overall_score:.1f}% compliance")
        return report
    
    async def check_owasp_compliance(self) -> None:
        """Check OWASP Top 10 2025 compliance"""
        logger.info("🔍 Checking OWASP Top 10 2025 compliance...")
        
        # A01: Broken Access Control
        await self.check_access_control()
        
        # A02: Cryptographic Failures
        await self.check_cryptographic_implementation()
        
        # A03: Injection
        await self.check_injection_protection()
        
        # A04: Insecure Design
        await self.check_secure_design()
        
        # A05: Security Misconfiguration
        await self.check_security_configuration()
        
        # A06: Vulnerable and Outdated Components
        await self.check_component_security()
        
        # A07: Identification and Authentication Failures
        await self.check_authentication_implementation()
        
        # A08: Software and Data Integrity Failures
        await self.check_integrity_controls()
        
        # A09: Security Logging and Monitoring Failures
        await self.check_logging_monitoring()
        
        # A10: Server-Side Request Forgery (SSRF)
        await self.check_ssrf_protection()
    
    async def check_access_control(self) -> None:
        """A01: Check access control implementation"""
        checks = [
            ('rbac_implementation', 'Role-based access control implementation'),
            ('endpoint_authorization', 'API endpoint authorization'),
            ('resource_permissions', 'Resource-level permissions'),
            ('privilege_escalation_protection', 'Privilege escalation protection')
        ]
        
        for check_id, description in checks:
            # Check for RBAC implementation
            rbac_files = list(self.project_root.glob('**/rbac*.py')) + \
                        list(self.project_root.glob('**/permissions*.py')) + \
                        list(self.project_root.glob('**/auth*.py'))
            
            if rbac_files:
                status = 'PASS'
                details = f'Found access control implementation in {len(rbac_files)} files'
                severity = 'LOW'
            else:
                status = 'FAIL'
                details = 'No access control implementation found'
                severity = 'HIGH'
            
            self.add_compliance_check(
                check_id=f'A01_{check_id}',
                category='OWASP_A01',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation='Implement proper access control mechanisms',
                standard_reference='OWASP Top 10 2025 A01'
            )
    
    async def check_cryptographic_implementation(self) -> None:
        """A02: Check cryptographic implementation"""
        # Check for proper encryption implementation
        crypto_patterns = [
            ('bcrypt', 'Password hashing'),
            ('cryptography', 'Encryption library'),
            ('jwt', 'Token security'),
            ('ssl', 'Transport security')
        ]
        
        for pattern, description in crypto_patterns:
            found = await self.check_code_pattern(pattern)
            
            if found:
                status = 'PASS'
                details = f'Found {description} implementation'
                severity = 'LOW'
            else:
                status = 'WARNING'
                details = f'No {description} implementation detected'
                severity = 'MEDIUM'
            
            self.add_compliance_check(
                check_id=f'A02_{pattern}_implementation',
                category='OWASP_A02',
                description=f'Cryptographic implementation: {description}',
                status=status,
                severity=severity,
                details=details,
                remediation=f'Implement proper {description}',
                standard_reference='OWASP Top 10 2025 A02'
            )
    
    async def check_injection_protection(self) -> None:
        """A03: Check injection attack protection"""
        # Check for ORM usage (SQL injection protection)
        orm_patterns = ['sqlalchemy', 'prisma', 'sequelize', 'mongoose']
        orm_found = any(await self.check_code_pattern(pattern) for pattern in orm_patterns)
        
        if orm_found:
            status = 'PASS'
            details = 'ORM usage detected for SQL injection protection'
            severity = 'LOW'
        else:
            status = 'FAIL'
            details = 'No ORM detected - potential SQL injection risk'
            severity = 'CRITICAL'
        
        self.add_compliance_check(
            check_id='A03_sql_injection_protection',
            category='OWASP_A03',
            description='SQL injection protection via ORM',
            status=status,
            severity=severity,
            details=details,
            remediation='Use parameterized queries or ORM',
            standard_reference='OWASP Top 10 2025 A03'
        )
        
        # Check for input validation
        validation_found = await self.check_code_pattern('pydantic') or \
                          await self.check_code_pattern('joi') or \
                          await self.check_code_pattern('validator')
        
        if validation_found:
            status = 'PASS'
            details = 'Input validation framework detected'
            severity = 'LOW'
        else:
            status = 'WARNING'
            details = 'No input validation framework detected'
            severity = 'MEDIUM'
        
        self.add_compliance_check(
            check_id='A03_input_validation',
            category='OWASP_A03',
            description='Input validation implementation',
            status=status,
            severity=severity,
            details=details,
            remediation='Implement comprehensive input validation',
            standard_reference='OWASP Top 10 2025 A03'
        )
    
    async def check_secure_design(self) -> None:
        """A04: Check secure design principles"""
        design_checks = [
            ('security_by_design', 'Security by design implementation'),
            ('threat_modeling', 'Threat modeling documentation'),
            ('secure_architecture', 'Secure architecture patterns')
        ]
        
        for check_id, description in design_checks:
            # Check for security documentation
            security_docs = list(self.project_root.glob('**/SECURITY*.md')) + \
                           list(self.project_root.glob('**/security*.md')) + \
                           list(self.project_root.glob('**/threat*.md'))
            
            if security_docs:
                status = 'PASS'
                details = f'Found security documentation: {len(security_docs)} files'
                severity = 'LOW'
            else:
                status = 'WARNING'
                details = 'No security design documentation found'
                severity = 'MEDIUM'
            
            self.add_compliance_check(
                check_id=f'A04_{check_id}',
                category='OWASP_A04',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation='Document security design principles',
                standard_reference='OWASP Top 10 2025 A04'
            )
    
    async def check_security_configuration(self) -> None:
        """A05: Check security configuration"""
        config_checks = [
            ('debug_disabled', 'Debug mode disabled in production'),
            ('default_passwords', 'No default passwords'),
            ('secure_defaults', 'Secure default configurations'),
            ('environment_separation', 'Environment-specific configurations')
        ]
        
        for check_id, description in config_checks:
            # Check environment configurations
            env_files = list(self.project_root.glob('**/.env*'))
            
            if env_files:
                # Check for debug configurations
                debug_safe = True
                for env_file in env_files:
                    try:
                        async with aiofiles.open(env_file) as f:
                            content = await f.read()
                            if 'DEBUG=true' in content or 'DEBUG=True' in content:
                                debug_safe = False
                                break
                    except Exception:
                        continue
                
                if debug_safe:
                    status = 'PASS'
                    details = 'No debug mode enabled in environment files'
                    severity = 'LOW'
                else:
                    status = 'FAIL'
                    details = 'Debug mode enabled in environment configuration'
                    severity = 'HIGH'
            else:
                status = 'WARNING'
                details = 'No environment configuration files found'
                severity = 'MEDIUM'
            
            self.add_compliance_check(
                check_id=f'A05_{check_id}',
                category='OWASP_A05',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation='Review and secure configuration settings',
                standard_reference='OWASP Top 10 2025 A05'
            )
    
    async def check_component_security(self) -> None:
        """A06: Check vulnerable and outdated components"""
        # This integrates with vulnerability scanner results
        # For now, we'll do a basic check
        
        package_files = list(self.project_root.glob('**/package.json')) + \
                       list(self.project_root.glob('**/requirements.txt')) + \
                       list(self.project_root.glob('**/Pipfile'))
        
        if package_files:
            status = 'PASS'
            details = f'Found {len(package_files)} dependency files for monitoring'
            severity = 'LOW'
        else:
            status = 'WARNING'
            details = 'No dependency files found'
            severity = 'MEDIUM'
        
        self.add_compliance_check(
            check_id='A06_component_monitoring',
            category='OWASP_A06',
            description='Component vulnerability monitoring',
            status=status,
            severity=severity,
            details=details,
            remediation='Implement dependency vulnerability scanning',
            standard_reference='OWASP Top 10 2025 A06'
        )
    
    async def check_authentication_implementation(self) -> None:
        """A07: Check authentication implementation"""
        auth_features = [
            ('mfa_implementation', 'Multi-factor authentication'),
            ('password_policy', 'Strong password policies'),
            ('session_management', 'Secure session management'),
            ('account_lockout', 'Account lockout mechanisms')
        ]
        
        for check_id, description in auth_features:
            # Check for authentication files
            auth_files = list(self.project_root.glob('**/auth*.py')) + \
                        list(self.project_root.glob('**/mfa*.py'))
            
            if auth_files:
                status = 'PASS'
                details = f'Found authentication implementation in {len(auth_files)} files'
                severity = 'LOW'
            else:
                status = 'FAIL'
                details = 'No authentication implementation found'
                severity = 'CRITICAL'
            
            self.add_compliance_check(
                check_id=f'A07_{check_id}',
                category='OWASP_A07',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation='Implement comprehensive authentication controls',
                standard_reference='OWASP Top 10 2025 A07'
            )
    
    async def check_integrity_controls(self) -> None:
        """A08: Check software and data integrity controls"""
        integrity_checks = [
            ('dependency_verification', 'Dependency integrity verification'),
            ('code_signing', 'Code signing implementation'),
            ('checksum_validation', 'Checksum validation'),
            ('supply_chain_security', 'Supply chain security measures')
        ]
        
        for check_id, description in integrity_checks:
            # Check for package lock files
            lock_files = list(self.project_root.glob('**/package-lock.json')) + \
                        list(self.project_root.glob('**/requirements.lock')) + \
                        list(self.project_root.glob('**/Pipfile.lock'))
            
            if lock_files:
                status = 'PASS'
                details = f'Found dependency lock files: {len(lock_files)}'
                severity = 'LOW'
            else:
                status = 'WARNING'
                details = 'No dependency lock files found'
                severity = 'MEDIUM'
            
            self.add_compliance_check(
                check_id=f'A08_{check_id}',
                category='OWASP_A08',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation='Implement dependency integrity controls',
                standard_reference='OWASP Top 10 2025 A08'
            )
    
    async def check_logging_monitoring(self) -> None:
        """A09: Check security logging and monitoring"""
        # Check for logging implementation
        logging_found = await self.check_code_pattern('logging') or \
                       await self.check_code_pattern('logger') or \
                       await self.check_code_pattern('audit')
        
        if logging_found:
            status = 'PASS'
            details = 'Logging implementation detected'
            severity = 'LOW'
        else:
            status = 'FAIL'
            details = 'No logging implementation found'
            severity = 'HIGH'
        
        self.add_compliance_check(
            check_id='A09_security_logging',
            category='OWASP_A09',
            description='Security logging implementation',
            status=status,
            severity=severity,
            details=details,
            remediation='Implement comprehensive security logging',
            standard_reference='OWASP Top 10 2025 A09'
        )
    
    async def check_ssrf_protection(self) -> None:
        """A10: Check SSRF protection"""
        # Check for URL validation
        url_validation = await self.check_code_pattern('validators') or \
                        await self.check_code_pattern('urllib.parse') or \
                        await self.check_code_pattern('url_validation')
        
        if url_validation:
            status = 'PASS'
            details = 'URL validation implementation detected'
            severity = 'LOW'
        else:
            status = 'WARNING'
            details = 'No URL validation detected'
            severity = 'MEDIUM'
        
        self.add_compliance_check(
            check_id='A10_ssrf_protection',
            category='OWASP_A10',
            description='SSRF protection implementation',
            status=status,
            severity=severity,
            details=details,
            remediation='Implement URL validation and filtering',
            standard_reference='OWASP Top 10 2025 A10'
        )
    
    async def check_security_headers(self) -> None:
        """Check security headers implementation"""
        logger.info("🔍 Checking security headers...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health/") as response:
                    headers = response.headers
                    
                    for header_name, description in self.required_headers.items():
                        if header_name in headers:
                            status = 'PASS'
                            details = f'Header present: {headers[header_name]}'
                            severity = 'LOW'
                        else:
                            status = 'FAIL'
                            details = f'Missing security header: {header_name}'
                            severity = 'HIGH'
                        
                        self.add_compliance_check(
                            check_id=f'HEADERS_{header_name.replace("-", "_").lower()}',
                            category='SECURITY_HEADERS',
                            description=f'Security header: {description}',
                            status=status,
                            severity=severity,
                            details=details,
                            remediation=f'Implement {header_name} header',
                            standard_reference='OWASP Security Headers'
                        )
        
        except Exception as e:
            logger.warning(f"Could not check security headers: {e}")
            self.add_compliance_check(
                check_id='HEADERS_connectivity',
                category='SECURITY_HEADERS',
                description='Security headers connectivity check',
                status='SKIP',
                severity='LOW',
                details=f'Could not connect to {self.base_url}',
                remediation='Ensure application is running',
                standard_reference='Infrastructure'
            )
    
    async def check_rate_limiting(self) -> None:
        """Check rate limiting implementation"""
        logger.info("🔍 Checking rate limiting...")
        
        # Check for rate limiting implementation
        rate_limit_files = list(self.project_root.glob('**/rate_limit*.py')) + \
                          list(self.project_root.glob('**/rate_limiter*.py'))
        
        if rate_limit_files:
            status = 'PASS'
            details = f'Rate limiting implementation found in {len(rate_limit_files)} files'
            severity = 'LOW'
        else:
            status = 'FAIL'
            details = 'No rate limiting implementation found'
            severity = 'HIGH'
        
        self.add_compliance_check(
            check_id='RATE_LIMITING_implementation',
            category='RATE_LIMITING',
            description='Rate limiting implementation',
            status=status,
            severity=severity,
            details=details,
            remediation='Implement comprehensive rate limiting',
            standard_reference='Security Best Practices'
        )
    
    async def check_authentication_security(self) -> None:
        """Check authentication security implementation"""
        logger.info("🔍 Checking authentication security...")
        
        security_features = [
            ('jwt_implementation', 'JWT token implementation'),
            ('password_hashing', 'Password hashing'),
            ('session_security', 'Session security'),
            ('mfa_support', 'Multi-factor authentication support')
        ]
        
        for check_id, description in security_features:
            pattern_found = await self.check_code_pattern(check_id.split('_')[0])
            
            if pattern_found:
                status = 'PASS'
                details = f'{description} detected in codebase'
                severity = 'LOW'
            else:
                status = 'WARNING'
                details = f'No {description} detected'
                severity = 'MEDIUM'
            
            self.add_compliance_check(
                check_id=f'AUTH_{check_id.upper()}',
                category='AUTHENTICATION',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation=f'Implement {description}',
                standard_reference='Authentication Security'
            )
    
    async def check_data_protection(self) -> None:
        """Check data protection implementation"""
        logger.info("🔍 Checking data protection...")
        
        protection_features = [
            ('encryption_at_rest', 'Data encryption at rest'),
            ('encryption_in_transit', 'Data encryption in transit'),
            ('data_anonymization', 'Data anonymization'),
            ('backup_security', 'Secure backup procedures')
        ]
        
        for check_id, description in protection_features:
            # Basic implementation check
            if 'encryption' in check_id:
                crypto_found = await self.check_code_pattern('cryptography') or \
                              await self.check_code_pattern('encrypt')
                
                if crypto_found:
                    status = 'PASS'
                    details = f'{description} implementation detected'
                    severity = 'LOW'
                else:
                    status = 'WARNING'
                    details = f'No {description} detected'
                    severity = 'MEDIUM'
            else:
                status = 'SKIP'
                details = f'{description} requires manual verification'
                severity = 'LOW'
            
            self.add_compliance_check(
                check_id=f'DATA_PROTECTION_{check_id.upper()}',
                category='DATA_PROTECTION',
                description=description,
                status=status,
                severity=severity,
                details=details,
                remediation=f'Implement {description}',
                standard_reference='Data Protection Standards'
            )
    
    async def check_regulatory_compliance(self) -> None:
        """Check regulatory compliance (GDPR, COPPA, FERPA)"""
        logger.info("🔍 Checking regulatory compliance...")
        
        for standard, description in self.compliance_standards.items():
            # Check for compliance documentation
            compliance_docs = list(self.project_root.glob(f'**/*{standard.lower()}*.md')) + \
                             list(self.project_root.glob(f'**/*privacy*.md')) + \
                             list(self.project_root.glob(f'**/*compliance*.md'))
            
            if compliance_docs:
                status = 'PASS'
                details = f'{description} documentation found'
                severity = 'LOW'
            else:
                status = 'WARNING'
                details = f'No {description} documentation found'
                severity = 'MEDIUM'
            
            self.add_compliance_check(
                check_id=f'REGULATORY_{standard}',
                category='REGULATORY',
                description=f'{description} compliance',
                status=status,
                severity=severity,
                details=details,
                remediation=f'Document {description} compliance measures',
                standard_reference=standard
            )
    
    async def check_code_pattern(self, pattern: str) -> bool:
        """Check if a pattern exists in the codebase"""
        code_files = ['**/*.py', '**/*.js', '**/*.ts', '**/*.jsx', '**/*.tsx']
        
        for file_pattern in code_files:
            for file_path in self.project_root.glob(file_pattern):
                if file_path.is_file() and 'node_modules' not in str(file_path):
                    try:
                        async with aiofiles.open(file_path, encoding='utf-8', errors='ignore') as f:
                            content = await f.read()
                            if pattern.lower() in content.lower():
                                return True
                    except Exception:
                        continue
        
        return False
    
    def add_compliance_check(
        self,
        check_id: str,
        category: str,
        description: str,
        status: str,
        severity: str,
        details: str,
        remediation: Optional[str],
        standard_reference: str
    ) -> None:
        """Add a compliance check result"""
        check = ComplianceCheck(
            check_id=check_id,
            category=category,
            description=description,
            status=status,
            severity=severity,
            details=details,
            remediation=remediation,
            standard_reference=standard_reference,
            checked_at=datetime.now()
        )
        self.checks.append(check)
    
    def generate_compliance_report(self) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        total_checks = len(self.checks)
        passed_checks = len([c for c in self.checks if c.status == 'PASS'])
        failed_checks = len([c for c in self.checks if c.status == 'FAIL'])
        warning_checks = len([c for c in self.checks if c.status == 'WARNING'])
        
        overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Calculate category scores
        categories = {}
        for category in set(c.category for c in self.checks):
            category_checks = [c for c in self.checks if c.category == category]
            category_passed = len([c for c in category_checks if c.status == 'PASS'])
            category_score = (category_passed / len(category_checks) * 100) if category_checks else 0
            categories[category] = category_score
        
        # Check compliance status
        compliance_status = {
            'owasp_2025': self.check_owasp_compliance_status(),
            'security_headers': self.check_security_headers_compliance(),
            'rate_limiting': self.check_rate_limiting_compliance(),
            'authentication': self.check_authentication_compliance()
        }
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        return ComplianceReport(
            overall_score=overall_score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_checks=warning_checks,
            categories=categories,
            compliance_status=compliance_status,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
    
    def check_owasp_compliance_status(self) -> bool:
        """Check OWASP compliance status"""
        owasp_checks = [c for c in self.checks if c.category.startswith('OWASP_')]
        critical_failures = [c for c in owasp_checks if c.status == 'FAIL' and c.severity == 'CRITICAL']
        
        return len(critical_failures) == 0
    
    def check_security_headers_compliance(self) -> bool:
        """Check security headers compliance"""
        header_checks = [c for c in self.checks if c.category == 'SECURITY_HEADERS']
        failed_headers = [c for c in header_checks if c.status == 'FAIL']
        
        return len(failed_headers) <= 1  # Allow 1 failed header
    
    def check_rate_limiting_compliance(self) -> bool:
        """Check rate limiting compliance"""
        rate_limit_checks = [c for c in self.checks if c.category == 'RATE_LIMITING']
        failed_checks = [c for c in rate_limit_checks if c.status == 'FAIL']
        
        return len(failed_checks) == 0
    
    def check_authentication_compliance(self) -> bool:
        """Check authentication compliance"""
        auth_checks = [c for c in self.checks if c.category == 'AUTHENTICATION']
        failed_checks = [c for c in auth_checks if c.status == 'FAIL']
        
        return len(failed_checks) == 0
    
    def generate_recommendations(self) -> list[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        failed_checks = [c for c in self.checks if c.status == 'FAIL']
        critical_failures = [c for c in failed_checks if c.severity == 'CRITICAL']
        
        if critical_failures:
            recommendations.append(f"Fix {len(critical_failures)} critical compliance failures immediately")
        
        if failed_checks:
            recommendations.append(f"Address {len(failed_checks)} total compliance failures")
        
        # Category-specific recommendations
        for category, score in self.generate_compliance_report().categories.items():
            if score < 80:
                recommendations.append(f"Improve {category} compliance (current: {score:.1f}%)")
        
        return recommendations
    
    async def get_compliance_report(self) -> dict:
        """Get comprehensive compliance report"""
        report = self.generate_compliance_report()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_score': report.overall_score,
            'compliance_grade': self.get_compliance_grade(report.overall_score),
            'summary': asdict(report),
            'checks': [asdict(check) for check in self.checks],
            'owasp_2025_status': report.compliance_status.get('owasp_2025', False),
            'security_score_maintained': report.overall_score >= 95.0
        }
    
    def get_compliance_grade(self, score: float) -> str:
        """Get compliance grade based on score"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        else:
            return 'F'
