#!/usr/bin/env python3
"""
ToolBoxAI Security Monitor - Phase 1.5 Security Agent
====================================================

Comprehensive security monitoring system maintaining 95% security score
during Phase 1.5 fixes implementation.

Features:
- Sub-Agent 1: Vulnerability Scanner (Real-time scanning)
- Sub-Agent 2: Compliance Checker (OWASP 2025 validation)
- Sub-Agent 3: Secret Rotator (Automated key rotation)
- Security Coordinator (Master orchestration)

Usage:
    python security_monitor.py --start-monitoring
    python security_monitor.py --run-scan
    python security_monitor.py --security-report
    python security_monitor.py --emergency-response

Security Target: Maintain 95%+ security score at all times
"""

import asyncio
import argparse
import logging
import sys
import signal
from pathlib import Path
from datetime import datetime
import json

# Import our security agents
try:
    from core.security_agents import (
        VulnerabilityScanner,
        ComplianceChecker, 
        SecretRotator,
        SecurityCoordinator
    )
except ImportError as e:
    print(f"Error importing security agents: {e}")
    print("Please ensure the security agents are properly installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('SecurityMonitor')

class SecurityMonitorCLI:
    """
    CLI interface for ToolBoxAI Security Monitor
    """
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.coordinator = None
        self.monitoring = False
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.monitoring = False
            if self.coordinator:
                asyncio.create_task(self.coordinator.stop_monitoring())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_monitoring(self, base_url: str = "http://localhost:8009"):
        """Start continuous security monitoring"""
        logger.info("🛡️  Starting ToolBoxAI Security Monitor - Phase 1.5")
        logger.info("📋 Target: Maintain 95%+ security score during fixes")
        
        self.coordinator = SecurityCoordinator(str(self.project_root), base_url)
        self.monitoring = True
        
        try:
            await self.coordinator.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            if self.coordinator:
                await self.coordinator.stop_monitoring()
    
    async def run_single_scan(self, base_url: str = "http://localhost:8009"):
        """Run a single comprehensive security scan"""
        logger.info("🔍 Running single comprehensive security scan...")
        
        coordinator = SecurityCoordinator(str(self.project_root), base_url)
        
        try:
            # Get comprehensive security status
            status = await coordinator.get_comprehensive_security_status()
            
            # Display results
            self.display_security_status(status)
            
            # Save report
            await coordinator.save_security_status(status)
            
            # Check if security target is met
            if status.overall_score >= 95.0:
                logger.info("✅ Security target achieved: 95%+ score maintained")
                return True
            else:
                logger.warning(f"⚠️  Security target not met: {status.overall_score:.1f}% < 95%")
                return False
                
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return False
    
    async def generate_security_report(self, base_url: str = "http://localhost:8009"):
        """Generate comprehensive security report"""
        logger.info("📊 Generating comprehensive security report...")
        
        coordinator = SecurityCoordinator(str(self.project_root), base_url)
        
        try:
            # Get detailed reports from all sub-agents
            vuln_scanner = VulnerabilityScanner(str(self.project_root))
            compliance_checker = ComplianceChecker(str(self.project_root), base_url)
            secret_rotator = SecretRotator(str(self.project_root))
            
            # Run comprehensive scans
            vuln_report = await vuln_scanner.run_comprehensive_scan()
            compliance_report = await compliance_checker.run_comprehensive_compliance_check()
            rotation_report = await secret_rotator.get_rotation_report()
            
            # Get overall status
            status = await coordinator.get_comprehensive_security_status()
            
            # Save comprehensive report
            await coordinator.save_comprehensive_report(
                status, vuln_report, compliance_report, rotation_report
            )
            
            # Display summary
            self.display_comprehensive_report(status, vuln_report, compliance_report, rotation_report)
            
            return status.overall_score >= 95.0
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return False
    
    async def emergency_response(self, reason: str, base_url: str = "http://localhost:8009"):
        """Execute emergency security response"""
        logger.critical(f"🚨 INITIATING EMERGENCY SECURITY RESPONSE: {reason}")
        
        coordinator = SecurityCoordinator(str(self.project_root), base_url)
        
        try:
            response = await coordinator.emergency_security_response(reason)
            
            # Display emergency response
            logger.critical("🚨 EMERGENCY RESPONSE SUMMARY:")
            logger.critical(f"   Reason: {response.get('reason', 'Unknown')}")
            logger.critical(f"   Actions Taken: {len(response.get('response_actions', []))}")
            
            for action in response.get('response_actions', []):
                logger.critical(f"   - {action}")
            
            if 'security_status' in response:
                status_data = response['security_status']
                logger.critical(f"   Security Score: {status_data.get('overall_score', 0):.1f}%")
                logger.critical(f"   Critical Issues: {status_data.get('critical_issues', 0)}")
            
            return response
            
        except Exception as e:
            logger.critical(f"Emergency response failed: {e}")
            return {'error': str(e)}
    
    async def validate_security_hooks(self, base_url: str = "http://localhost:8009"):
        """Validate all security hooks"""
        logger.info("🔒 Validating security hooks...")
        
        coordinator = SecurityCoordinator(str(self.project_root), base_url)
        
        hook_results = []
        hooks = ['pre_commit_security_check', 'post_fix_validation', 'deployment_security_gate']
        
        for hook_id in hooks:
            try:
                result = await coordinator.execute_security_hook(hook_id)
                hook_results.append((hook_id, result))
                
                if result:
                    logger.info(f"✅ {hook_id}: PASSED")
                else:
                    logger.error(f"❌ {hook_id}: FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {hook_id}: ERROR - {e}")
                hook_results.append((hook_id, False))
        
        all_passed = all(result for _, result in hook_results)
        
        if all_passed:
            logger.info("✅ All security hooks validated successfully")
        else:
            logger.error("❌ One or more security hooks failed validation")
        
        return all_passed
    
    def display_security_status(self, status):
        """Display security status in readable format"""
        print("\n" + "="*60)
        print("🛡️  TOOLBOXAI SECURITY STATUS - PHASE 1.5")
        print("="*60)
        print(f"Overall Security Score: {status.overall_score:.1f}% (Grade: {status.security_grade})")
        print(f"Target Achievement: {'✅ ACHIEVED' if status.overall_score >= 95.0 else '❌ NOT MET'} (Target: 95%)")
        print()
        
        print("📊 Component Scores:")
        print(f"   Vulnerability Scan: {status.vulnerability_score:.1f}%")
        print(f"   Compliance Check:   {status.compliance_score:.1f}%")
        print(f"   Secret Management:  {status.secret_rotation_score:.1f}%")
        print()
        
        print("🔍 Issue Summary:")
        print(f"   Critical Issues: {status.critical_issues}")
        print(f"   High Issues:     {status.high_issues}")
        print(f"   Medium Issues:   {status.medium_issues}")
        print(f"   Low Issues:      {status.low_issues}")
        print()
        
        if status.critical_issues > 0:
            print("🚨 CRITICAL ALERT: Critical vulnerabilities detected!")
        
        if status.overall_score < 95.0:
            print("⚠️  WARNING: Security score below 95% target")
        
        print("📋 Compliance Status:")
        for standard, compliant in status.compliance_status.items():
            status_emoji = "✅" if compliant else "❌"
            print(f"   {standard}: {status_emoji}")
        print()
        
        if status.recommendations:
            print("💡 Top Recommendations:")
            for i, rec in enumerate(status.recommendations[:5], 1):
                print(f"   {i}. {rec}")
            print()
        
        if status.next_actions:
            print("🎯 Next Actions:")
            for i, action in enumerate(status.next_actions[:3], 1):
                print(f"   {i}. {action}")
        
        print("="*60)
    
    def display_comprehensive_report(self, status, vuln_report, compliance_report, rotation_report):
        """Display comprehensive security report"""
        self.display_security_status(status)
        
        print("\n📋 DETAILED SECURITY REPORT")
        print("="*60)
        
        # Vulnerability details
        vulnerabilities = vuln_report.get('vulnerabilities', [])
        if vulnerabilities:
            print(f"🔍 Vulnerabilities Found: {len(vulnerabilities)}")
            for vuln in vulnerabilities[:5]:  # Show top 5
                print(f"   - {vuln['severity']}: {vuln['description']}")
        else:
            print("🔍 No vulnerabilities detected")
        
        print()
        
        # Compliance details
        compliance_summary = compliance_report.get('summary', {})
        print(f"📋 Compliance: {compliance_summary.get('passed_checks', 0)}/{compliance_summary.get('total_checks', 0)} checks passed")
        
        # Secret rotation details
        rotation_summary = rotation_report.get('health_summary', {})
        print(f"🔑 Secret Management: {rotation_summary.get('active_secrets', 0)} active secrets")
        
        print("="*60)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ToolBoxAI Security Monitor - Phase 1.5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python security_monitor.py --start-monitoring        # Start continuous monitoring
  python security_monitor.py --run-scan               # Run single security scan
  python security_monitor.py --security-report        # Generate comprehensive report
  python security_monitor.py --validate-hooks         # Validate security hooks
  python security_monitor.py --emergency-response "Security breach detected"
        """
    )
    
    parser.add_argument(
        '--start-monitoring',
        action='store_true',
        help='Start continuous security monitoring'
    )
    
    parser.add_argument(
        '--run-scan',
        action='store_true',
        help='Run single comprehensive security scan'
    )
    
    parser.add_argument(
        '--security-report',
        action='store_true',
        help='Generate comprehensive security report'
    )
    
    parser.add_argument(
        '--validate-hooks',
        action='store_true',
        help='Validate all security hooks'
    )
    
    parser.add_argument(
        '--emergency-response',
        type=str,
        help='Execute emergency security response with given reason'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default='http://localhost:8009',
        help='Base URL for backend API (default: http://localhost:8009)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create CLI instance
    cli = SecurityMonitorCLI()
    cli.setup_signal_handlers()
    
    # Determine action
    if args.start_monitoring:
        asyncio.run(cli.start_monitoring(args.base_url))
    elif args.run_scan:
        success = asyncio.run(cli.run_single_scan(args.base_url))
        sys.exit(0 if success else 1)
    elif args.security_report:
        success = asyncio.run(cli.generate_security_report(args.base_url))
        sys.exit(0 if success else 1)
    elif args.validate_hooks:
        success = asyncio.run(cli.validate_security_hooks(args.base_url))
        sys.exit(0 if success else 1)
    elif args.emergency_response:
        response = asyncio.run(cli.emergency_response(args.emergency_response, args.base_url))
        if 'error' in response:
            sys.exit(1)
    else:
        parser.print_help()
        print("\n🛡️  ToolBoxAI Security Monitor - Phase 1.5")
        print("📋 Maintains 95%+ security score during fixes")
        print("🔍 Use --help for available commands")

if __name__ == '__main__':
    main()
