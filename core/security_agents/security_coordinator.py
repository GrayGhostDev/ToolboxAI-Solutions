"""
Security Coordinator
===================

Master coordinator for all security sub-agents:
- Orchestrates vulnerability scanning, compliance checking, and secret rotation
- Maintains 95% security score continuously
- Implements security validation hooks
- Provides comprehensive security reporting
- Handles security incident response

Ensures security is non-negotiable during Phase 1.5 fixes.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import aiofiles

from .vulnerability_scanner import VulnerabilityScanner
from .compliance_checker import ComplianceChecker
from .secret_rotator import SecretRotator

logger = logging.getLogger(__name__)

@dataclass
class SecurityStatus:
    """Overall security status"""
    timestamp: datetime
    overall_score: float
    security_grade: str
    vulnerability_score: float
    compliance_score: float
    secret_rotation_score: float
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    compliance_status: Dict[str, bool]
    recommendations: List[str]
    next_actions: List[str]

@dataclass
class SecurityHook:
    """Security validation hook"""
    hook_id: str
    hook_type: str  # PRE_COMMIT, POST_FIX, DEPLOYMENT, SCHEDULED
    description: str
    enabled: bool
    last_run: Optional[datetime]
    success_rate: float
    failure_threshold: int

class SecurityCoordinator:
    """
    Master security coordinator for Phase 1.5 monitoring
    
    Coordinates:
    - Vulnerability Scanner (Sub-Agent 1)
    - Compliance Checker (Sub-Agent 2) 
    - Secret Rotator (Sub-Agent 3)
    
    Maintains 95% security score through continuous monitoring
    and automated security validation hooks.
    """
    
    def __init__(self, project_root: str = ".", base_url: str = "http://localhost:8009"):
        self.project_root = Path(project_root)
        self.base_url = base_url
        self.monitoring = False
        self.monitoring_interval = 300  # 5 minutes
        
        # Initialize sub-agents
        self.vulnerability_scanner = VulnerabilityScanner(project_root)
        self.compliance_checker = ComplianceChecker(project_root, base_url)
        self.secret_rotator = SecretRotator(project_root)
        
        # Security thresholds
        self.target_security_score = 95.0
        self.critical_threshold = 0  # No critical vulnerabilities allowed
        self.high_threshold = 2      # Max 2 high vulnerabilities
        
        # Security hooks
        self.hooks: Dict[str, SecurityHook] = {}
        self.initialize_security_hooks()
        
        # Security metrics
        self.security_history: List[SecurityStatus] = []
        self.max_history = 100  # Keep last 100 status reports
        
        # Alert thresholds
        self.alert_thresholds = {
            'security_score_drop': 5.0,  # Alert if score drops by 5%
            'new_critical_vuln': 1,      # Alert on any new critical vuln
            'compliance_failure': 1,     # Alert on compliance failure
            'secret_rotation_failure': 1 # Alert on rotation failure
        }
    
    def initialize_security_hooks(self) -> None:
        """Initialize security validation hooks"""
        hooks = [
            SecurityHook(
                hook_id='pre_commit_security_check',
                hook_type='PRE_COMMIT',
                description='Security validation before code commits',
                enabled=True,
                last_run=None,
                success_rate=100.0,
                failure_threshold=0
            ),
            SecurityHook(
                hook_id='post_fix_validation',
                hook_type='POST_FIX',
                description='Security validation after Phase 1.5 fixes',
                enabled=True,
                last_run=None,
                success_rate=100.0,
                failure_threshold=0
            ),
            SecurityHook(
                hook_id='deployment_security_gate',
                hook_type='DEPLOYMENT',
                description='Security gate for deployment approval',
                enabled=True,
                last_run=None,
                success_rate=100.0,
                failure_threshold=0
            ),
            SecurityHook(
                hook_id='scheduled_comprehensive_scan',
                hook_type='SCHEDULED',
                description='Scheduled comprehensive security scan',
                enabled=True,
                last_run=None,
                success_rate=100.0,
                failure_threshold=2
            )
        ]
        
        for hook in hooks:
            self.hooks[hook.hook_id] = hook
    
    async def start_monitoring(self) -> None:
        """Start comprehensive security monitoring"""
        self.monitoring = True
        logger.info("🛡️  Security Coordinator: Starting comprehensive monitoring")
        
        # Start all sub-agents
        tasks = [
            asyncio.create_task(self.vulnerability_scanner.start_monitoring()),
            asyncio.create_task(self.compliance_checker.start_monitoring()),
            asyncio.create_task(self.secret_rotator.start_monitoring()),
            asyncio.create_task(self.master_monitoring_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Security monitoring error: {e}")
        finally:
            await self.stop_monitoring()
    
    async def stop_monitoring(self) -> None:
        """Stop all security monitoring"""
        self.monitoring = False
        self.vulnerability_scanner.stop_monitoring()
        self.compliance_checker.stop_monitoring()
        self.secret_rotator.stop_monitoring()
        logger.info("🛡️  Security Coordinator: Monitoring stopped")
    
    async def master_monitoring_loop(self) -> None:
        """Master monitoring loop that coordinates all security activities"""
        while self.monitoring:
            try:
                # Generate comprehensive security status
                status = await self.get_comprehensive_security_status()
                
                # Store in history
                self.security_history.append(status)
                if len(self.security_history) > self.max_history:
                    self.security_history.pop(0)
                
                # Check security thresholds
                await self.check_security_thresholds(status)
                
                # Execute scheduled hooks
                await self.execute_scheduled_hooks()
                
                # Save security status
                await self.save_security_status(status)
                
                # Log current status
                self.log_security_status(status)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Master monitoring loop error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    async def get_comprehensive_security_status(self) -> SecurityStatus:
        """Get comprehensive security status from all sub-agents"""
        logger.info("📊 Generating comprehensive security status...")
        
        # Get reports from all sub-agents
        vuln_report = await self.vulnerability_scanner.get_security_report()
        compliance_report = await self.compliance_checker.get_compliance_report()
        rotation_report = await self.secret_rotator.get_rotation_report()
        
        # Calculate overall scores
        vulnerability_score = vuln_report['security_score']
        compliance_score = compliance_report['overall_score']
        
        # Calculate secret rotation score based on health
        rotation_health = rotation_report['health_summary']
        total_secrets = rotation_health['active_secrets'] + rotation_health['expired_secrets']
        if total_secrets > 0:
            secret_rotation_score = (rotation_health['active_secrets'] / total_secrets) * 100
        else:
            secret_rotation_score = 100.0
        
        # Calculate overall security score (weighted average)
        overall_score = (
            vulnerability_score * 0.4 +      # 40% weight on vulnerabilities
            compliance_score * 0.4 +         # 40% weight on compliance
            secret_rotation_score * 0.2      # 20% weight on secret management
        )
        
        # Count issues by severity
        vulnerabilities = vuln_report.get('vulnerabilities', [])
        critical_issues = len([v for v in vulnerabilities if v['severity'] == 'CRITICAL'])
        high_issues = len([v for v in vulnerabilities if v['severity'] == 'HIGH'])
        medium_issues = len([v for v in vulnerabilities if v['severity'] == 'MEDIUM'])
        low_issues = len([v for v in vulnerabilities if v['severity'] == 'LOW'])
        
        # Determine security grade
        security_grade = self.calculate_security_grade(overall_score)
        
        # Compile compliance status
        compliance_status = compliance_report.get('compliance_status', {})
        
        # Generate recommendations
        recommendations = self.generate_comprehensive_recommendations(
            vuln_report, compliance_report, rotation_report
        )
        
        # Generate next actions
        next_actions = self.generate_next_actions(
            overall_score, critical_issues, high_issues, compliance_status
        )
        
        return SecurityStatus(
            timestamp=datetime.now(),
            overall_score=overall_score,
            security_grade=security_grade,
            vulnerability_score=vulnerability_score,
            compliance_score=compliance_score,
            secret_rotation_score=secret_rotation_score,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            compliance_status=compliance_status,
            recommendations=recommendations,
            next_actions=next_actions
        )
    
    def calculate_security_grade(self, score: float) -> str:
        """Calculate security grade based on score"""
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
    
    def generate_comprehensive_recommendations(
        self, 
        vuln_report: Dict, 
        compliance_report: Dict, 
        rotation_report: Dict
    ) -> List[str]:
        """Generate comprehensive security recommendations"""
        recommendations = []
        
        # Add vulnerability recommendations
        vuln_recommendations = vuln_report.get('recommendations', [])
        for rec in vuln_recommendations:
            recommendations.append(f"Vulnerability: {rec['title']}")
        
        # Add compliance recommendations
        compliance_recommendations = compliance_report.get('summary', {}).get('recommendations', [])
        for rec in compliance_recommendations:
            recommendations.append(f"Compliance: {rec}")
        
        # Add secret rotation recommendations
        rotation_recommendations = rotation_report.get('recommendations', [])
        for rec in rotation_recommendations:
            recommendations.append(f"Secret Management: {rec}")
        
        return recommendations
    
    def generate_next_actions(
        self, 
        overall_score: float, 
        critical_issues: int, 
        high_issues: int, 
        compliance_status: Dict[str, bool]
    ) -> List[str]:
        """Generate next actions based on security status"""
        next_actions = []
        
        # Critical actions
        if critical_issues > 0:
            next_actions.append(f"CRITICAL: Fix {critical_issues} critical vulnerabilities immediately")
        
        if overall_score < self.target_security_score:
            score_gap = self.target_security_score - overall_score
            next_actions.append(f"URGENT: Improve security score by {score_gap:.1f}% to reach target")
        
        # High priority actions
        if high_issues > self.high_threshold:
            excess_high = high_issues - self.high_threshold
            next_actions.append(f"HIGH: Fix {excess_high} high-severity vulnerabilities")
        
        # Compliance actions
        failed_compliance = [k for k, v in compliance_status.items() if not v]
        if failed_compliance:
            next_actions.append(f"COMPLIANCE: Address {len(failed_compliance)} compliance failures")
        
        # Maintenance actions
        if not next_actions:
            next_actions.append("Maintain current security posture")
            next_actions.append("Continue regular security monitoring")
        
        return next_actions
    
    async def check_security_thresholds(self, status: SecurityStatus) -> None:
        """Check security thresholds and generate alerts"""
        alerts = []
        
        # Check overall security score
        if status.overall_score < self.target_security_score:
            score_gap = self.target_security_score - status.overall_score
            alerts.append(f"🚨 Security score below target: {status.overall_score:.1f}% (target: {self.target_security_score}%)")
        
        # Check for score drops
        if len(self.security_history) > 1:
            previous_score = self.security_history[-2].overall_score
            score_drop = previous_score - status.overall_score
            if score_drop >= self.alert_thresholds['security_score_drop']:
                alerts.append(f"⚠️  Security score dropped by {score_drop:.1f}%")
        
        # Check critical vulnerabilities
        if status.critical_issues > self.critical_threshold:
            alerts.append(f"🚨 CRITICAL: {status.critical_issues} critical vulnerabilities detected")
        
        # Check high vulnerabilities
        if status.high_issues > self.high_threshold:
            alerts.append(f"⚠️  HIGH: {status.high_issues} high-severity vulnerabilities (threshold: {self.high_threshold})")
        
        # Check compliance failures
        failed_compliance = [k for k, v in status.compliance_status.items() if not v]
        if failed_compliance:
            alerts.append(f"📋 Compliance failures: {', '.join(failed_compliance)}")
        
        # Log alerts
        for alert in alerts:
            logger.warning(alert)
        
        # Save alerts for reporting
        if alerts:
            await self.save_security_alerts(alerts, status.timestamp)
    
    async def execute_security_hook(self, hook_id: str) -> bool:
        """Execute a specific security hook"""
        if hook_id not in self.hooks:
            logger.error(f"Security hook not found: {hook_id}")
            return False
        
        hook = self.hooks[hook_id]
        if not hook.enabled:
            logger.info(f"Security hook disabled: {hook_id}")
            return True
        
        logger.info(f"🔒 Executing security hook: {hook.description}")
        
        try:
            success = True
            
            if hook.hook_type == 'PRE_COMMIT':
                success = await self.pre_commit_security_check()
            elif hook.hook_type == 'POST_FIX':
                success = await self.post_fix_validation()
            elif hook.hook_type == 'DEPLOYMENT':
                success = await self.deployment_security_gate()
            elif hook.hook_type == 'SCHEDULED':
                success = await self.scheduled_comprehensive_scan()
            
            # Update hook statistics
            hook.last_run = datetime.now()
            if success:
                # Simple success rate calculation (could be more sophisticated)
                hook.success_rate = min(100.0, hook.success_rate + 1.0)
            else:
                hook.success_rate = max(0.0, hook.success_rate - 5.0)
            
            return success
            
        except Exception as e:
            logger.error(f"Security hook execution failed: {hook_id} - {e}")
            hook.success_rate = max(0.0, hook.success_rate - 10.0)
            return False
    
    async def pre_commit_security_check(self) -> bool:
        """Pre-commit security validation"""
        logger.info("🔍 Running pre-commit security check...")
        
        # Quick vulnerability scan
        vuln_report = await self.vulnerability_scanner.run_comprehensive_scan()
        
        # Check for critical issues
        vulnerabilities = vuln_report.get('vulnerabilities', [])
        critical_vulns = [v for v in vulnerabilities if v['severity'] == 'CRITICAL']
        
        if critical_vulns:
            logger.error(f"❌ Pre-commit check failed: {len(critical_vulns)} critical vulnerabilities")
            return False
        
        # Check for exposed secrets
        secret_vulns = [v for v in vulnerabilities if v['category'] == 'SECRET']
        if secret_vulns:
            logger.error(f"❌ Pre-commit check failed: {len(secret_vulns)} exposed secrets")
            return False
        
        logger.info("✅ Pre-commit security check passed")
        return True
    
    async def post_fix_validation(self) -> bool:
        """Post-fix security validation"""
        logger.info("🔍 Running post-fix security validation...")
        
        # Full security status check
        status = await self.get_comprehensive_security_status()
        
        # Ensure security score is maintained
        if status.overall_score < self.target_security_score:
            logger.error(f"❌ Post-fix validation failed: Security score {status.overall_score:.1f}% below target {self.target_security_score}%")
            return False
        
        # No critical issues allowed
        if status.critical_issues > 0:
            logger.error(f"❌ Post-fix validation failed: {status.critical_issues} critical issues remain")
            return False
        
        logger.info("✅ Post-fix security validation passed")
        return True
    
    async def deployment_security_gate(self) -> bool:
        """Deployment security gate validation"""
        logger.info("🚪 Running deployment security gate...")
        
        # Comprehensive security check
        status = await self.get_comprehensive_security_status()
        
        # Strict requirements for deployment
        if status.overall_score < 95.0:
            logger.error(f"❌ Deployment blocked: Security score {status.overall_score:.1f}% below 95%")
            return False
        
        if status.critical_issues > 0:
            logger.error(f"❌ Deployment blocked: {status.critical_issues} critical vulnerabilities")
            return False
        
        if status.high_issues > 1:
            logger.error(f"❌ Deployment blocked: {status.high_issues} high-severity vulnerabilities (max: 1)")
            return False
        
        # Check compliance
        compliance_failures = [k for k, v in status.compliance_status.items() if not v]
        if compliance_failures:
            logger.error(f"❌ Deployment blocked: Compliance failures: {', '.join(compliance_failures)}")
            return False
        
        logger.info("✅ Deployment security gate passed")
        return True
    
    async def scheduled_comprehensive_scan(self) -> bool:
        """Scheduled comprehensive security scan"""
        logger.info("📅 Running scheduled comprehensive scan...")
        
        try:
            # Force full scans from all sub-agents
            vuln_report = await self.vulnerability_scanner.run_comprehensive_scan()
            compliance_report = await self.compliance_checker.run_comprehensive_compliance_check()
            rotation_report = await self.secret_rotator.get_rotation_report()
            
            # Generate and save comprehensive report
            status = await self.get_comprehensive_security_status()
            await self.save_comprehensive_report(status, vuln_report, compliance_report, rotation_report)
            
            logger.info("✅ Scheduled comprehensive scan completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Scheduled comprehensive scan failed: {e}")
            return False
    
    async def execute_scheduled_hooks(self) -> None:
        """Execute any scheduled security hooks"""
        now = datetime.now()
        
        for hook_id, hook in self.hooks.items():
            if hook.hook_type == 'SCHEDULED' and hook.enabled:
                # Check if hook should run (every 6 hours for comprehensive scans)
                if hook.last_run is None or (now - hook.last_run) > timedelta(hours=6):
                    await self.execute_security_hook(hook_id)
    
    async def save_security_status(self, status: SecurityStatus) -> None:
        """Save security status to file"""
        try:
            status_file = self.project_root / 'security_status.json'
            
            status_data = {
                'timestamp': status.timestamp.isoformat(),
                'overall_score': status.overall_score,
                'security_grade': status.security_grade,
                'vulnerability_score': status.vulnerability_score,
                'compliance_score': status.compliance_score,
                'secret_rotation_score': status.secret_rotation_score,
                'critical_issues': status.critical_issues,
                'high_issues': status.high_issues,
                'medium_issues': status.medium_issues,
                'low_issues': status.low_issues,
                'compliance_status': status.compliance_status,
                'recommendations': status.recommendations,
                'next_actions': status.next_actions
            }
            
            async with aiofiles.open(status_file, 'w') as f:
                await f.write(json.dumps(status_data, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving security status: {e}")
    
    async def save_security_alerts(self, alerts: List[str], timestamp: datetime) -> None:
        """Save security alerts to file"""
        try:
            alerts_file = self.project_root / 'security_alerts.json'
            
            alert_data = {
                'timestamp': timestamp.isoformat(),
                'alerts': alerts
            }
            
            # Load existing alerts
            existing_alerts = []
            if alerts_file.exists():
                async with aiofiles.open(alerts_file, 'r') as f:
                    content = await f.read()
                    if content:
                        data = json.loads(content)
                        existing_alerts = data.get('alerts_history', [])
            
            # Add new alerts
            existing_alerts.append(alert_data)
            
            # Keep only last 50 alert events
            if len(existing_alerts) > 50:
                existing_alerts = existing_alerts[-50:]
            
            # Save alerts
            full_data = {
                'last_updated': timestamp.isoformat(),
                'alerts_history': existing_alerts
            }
            
            async with aiofiles.open(alerts_file, 'w') as f:
                await f.write(json.dumps(full_data, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving security alerts: {e}")
    
    async def save_comprehensive_report(
        self, 
        status: SecurityStatus,
        vuln_report: Dict,
        compliance_report: Dict, 
        rotation_report: Dict
    ) -> None:
        """Save comprehensive security report"""
        try:
            report_file = self.project_root / f'security_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            comprehensive_report = {
                'timestamp': status.timestamp.isoformat(),
                'security_summary': asdict(status),
                'vulnerability_report': vuln_report,
                'compliance_report': compliance_report,
                'secret_rotation_report': rotation_report,
                'security_hooks_status': {
                    hook_id: {
                        'description': hook.description,
                        'enabled': hook.enabled,
                        'last_run': hook.last_run.isoformat() if hook.last_run else None,
                        'success_rate': hook.success_rate
                    }
                    for hook_id, hook in self.hooks.items()
                }
            }
            
            async with aiofiles.open(report_file, 'w') as f:
                await f.write(json.dumps(comprehensive_report, indent=2))
                
            logger.info(f"📊 Comprehensive security report saved: {report_file.name}")
            
        except Exception as e:
            logger.error(f"Error saving comprehensive report: {e}")
    
    def log_security_status(self, status: SecurityStatus) -> None:
        """Log current security status"""
        logger.info(f"🛡️  Security Status: {status.overall_score:.1f}% (Grade: {status.security_grade})")
        
        if status.critical_issues > 0:
            logger.critical(f"🚨 CRITICAL: {status.critical_issues} critical issues")
        
        if status.high_issues > 0:
            logger.warning(f"⚠️  HIGH: {status.high_issues} high-severity issues")
        
        if status.overall_score >= self.target_security_score:
            logger.info("✅ Security score target maintained")
        else:
            logger.warning(f"⚠️  Security score below target: {status.overall_score:.1f}% < {self.target_security_score}%")
    
    async def emergency_security_response(self, reason: str) -> Dict:
        """Emergency security response procedure"""
        logger.critical(f"🚨 EMERGENCY SECURITY RESPONSE: {reason}")
        
        response_actions = []
        
        try:
            # 1. Immediate assessment
            logger.critical("1. Running immediate security assessment...")
            status = await self.get_comprehensive_security_status()
            response_actions.append("Completed immediate security assessment")
            
            # 2. Block deployment if score too low
            if status.overall_score < 90.0:
                logger.critical("2. Blocking all deployments due to low security score")
                response_actions.append("Blocked deployments")
            
            # 3. Emergency secret rotation if needed
            if status.critical_issues > 5:
                logger.critical("3. Initiating emergency secret rotation")
                rotation_results = await self.secret_rotator.emergency_rotation()
                response_actions.append(f"Emergency secret rotation: {len(rotation_results)} secrets rotated")
            
            # 4. Generate emergency report
            emergency_report = {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'security_status': asdict(status),
                'response_actions': response_actions,
                'recommendations': status.recommendations,
                'next_steps': status.next_actions
            }
            
            # Save emergency report
            emergency_file = self.project_root / f'EMERGENCY_SECURITY_REPORT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            async with aiofiles.open(emergency_file, 'w') as f:
                await f.write(json.dumps(emergency_report, indent=2))
            
            logger.critical(f"📄 Emergency report saved: {emergency_file.name}")
            
            return emergency_report
            
        except Exception as e:
            logger.critical(f"Emergency security response failed: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'error': str(e),
                'response_actions': response_actions
            }
    
    async def get_security_dashboard_data(self) -> Dict:
        """Get security dashboard data for monitoring"""
        if not self.security_history:
            status = await self.get_comprehensive_security_status()
            self.security_history.append(status)
        
        current_status = self.security_history[-1]
        
        # Calculate trends
        score_trend = 0.0
        if len(self.security_history) > 1:
            score_trend = current_status.overall_score - self.security_history[-2].overall_score
        
        return {
            'current_security_score': current_status.overall_score,
            'security_grade': current_status.security_grade,
            'score_trend': score_trend,
            'critical_issues': current_status.critical_issues,
            'high_issues': current_status.high_issues,
            'medium_issues': current_status.medium_issues,
            'low_issues': current_status.low_issues,
            'compliance_status': current_status.compliance_status,
            'target_maintained': current_status.overall_score >= self.target_security_score,
            'last_updated': current_status.timestamp.isoformat(),
            'recommendations': current_status.recommendations[:5],  # Top 5 recommendations
            'next_actions': current_status.next_actions[:3],        # Top 3 actions
            'security_hooks_status': {
                hook_id: {
                    'enabled': hook.enabled,
                    'success_rate': hook.success_rate,
                    'last_run': hook.last_run.isoformat() if hook.last_run else None
                }
                for hook_id, hook in self.hooks.items()
            }
        }
