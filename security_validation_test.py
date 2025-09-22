#!/usr/bin/env python3
"""
ToolBoxAI Security Validation Test
=================================

Comprehensive test of the security monitoring system for Phase 1.5 fixes.
Validates that 95% security score is maintained and all sub-agents work correctly.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('SecurityValidationTest')

async def test_vulnerability_scanning():
    """Test vulnerability scanning functionality"""
    logger.info("🔍 Testing Vulnerability Scanner...")
    
    try:
        from core.security_agents.vulnerability_scanner import VulnerabilityScanner
        
        scanner = VulnerabilityScanner(".")
        
        # Run dependency scan
        dep_results = await scanner.scan_dependencies()
        logger.info(f"Dependencies scanned: {len(dep_results.get('vulnerabilities', []))} vulnerabilities found")
        
        # Run secret scan
        secret_results = await scanner.scan_secrets()
        logger.info(f"Secret scan: {len(secret_results.get('vulnerabilities', []))} exposed secrets found")
        
        # Get security report
        report = await scanner.get_security_report()
        security_score = report['security_score']
        
        logger.info(f"Vulnerability Scanner Score: {security_score:.1f}%")
        
        if security_score >= 95.0:
            logger.info("✅ Vulnerability Scanner: PASSED")
            return True
        else:
            logger.warning(f"⚠️  Vulnerability Scanner: Score below 95% ({security_score:.1f}%)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Vulnerability Scanner: FAILED - {e}")
        return False

async def test_compliance_checking():
    """Test compliance checking functionality"""
    logger.info("📋 Testing Compliance Checker...")
    
    try:
        from core.security_agents.compliance_checker import ComplianceChecker
        
        checker = ComplianceChecker(".", "http://localhost:8009")
        
        # Run OWASP compliance check
        await checker.check_owasp_compliance()
        
        # Run security headers check
        await checker.check_security_headers()
        
        # Get compliance report
        report = await checker.get_compliance_report()
        compliance_score = report['overall_score']
        
        logger.info(f"Compliance Checker Score: {compliance_score:.1f}%")
        
        if compliance_score >= 95.0:
            logger.info("✅ Compliance Checker: PASSED")
            return True
        else:
            logger.warning(f"⚠️  Compliance Checker: Score below 95% ({compliance_score:.1f}%)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Compliance Checker: FAILED - {e}")
        return False

async def test_secret_rotation():
    """Test secret rotation functionality"""
    logger.info("🔑 Testing Secret Rotator...")
    
    try:
        from core.security_agents.secret_rotator import SecretRotator
        
        rotator = SecretRotator(".")
        
        # Register a test secret
        await rotator.register_secret(
            "test_jwt_secret",
            "JWT",
            "development",
            auto_rotate=False  # Don't auto-rotate in test
        )
        
        # Get rotation report
        report = await rotator.get_rotation_report()
        
        logger.info(f"Secret Rotator: {report['total_secrets']} secrets managed")
        
        # Calculate score based on health
        health = report['health_summary']
        total_secrets = health['active_secrets'] + health['expired_secrets']
        if total_secrets > 0:
            secret_score = (health['active_secrets'] / total_secrets) * 100
        else:
            secret_score = 100.0
        
        logger.info(f"Secret Rotator Score: {secret_score:.1f}%")
        
        if secret_score >= 95.0:
            logger.info("✅ Secret Rotator: PASSED")
            return True
        else:
            logger.warning(f"⚠️  Secret Rotator: Score below 95% ({secret_score:.1f}%)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Secret Rotator: FAILED - {e}")
        return False

async def test_security_coordinator():
    """Test security coordinator functionality"""
    logger.info("🛡️  Testing Security Coordinator...")
    
    try:
        from core.security_agents.security_coordinator import SecurityCoordinator
        
        coordinator = SecurityCoordinator(".", "http://localhost:8009")
        
        # Get comprehensive security status
        status = await coordinator.get_comprehensive_security_status()
        
        logger.info(f"Overall Security Score: {status.overall_score:.1f}%")
        logger.info(f"Security Grade: {status.security_grade}")
        logger.info(f"Critical Issues: {status.critical_issues}")
        logger.info(f"High Issues: {status.high_issues}")
        
        # Test security hooks
        hooks_passed = 0
        total_hooks = 0
        
        for hook_id in ['pre_commit_security_check', 'post_fix_validation']:
            total_hooks += 1
            try:
                result = await coordinator.execute_security_hook(hook_id)
                if result:
                    hooks_passed += 1
                    logger.info(f"✅ Security Hook {hook_id}: PASSED")
                else:
                    logger.warning(f"⚠️  Security Hook {hook_id}: FAILED")
            except Exception as e:
                logger.error(f"❌ Security Hook {hook_id}: ERROR - {e}")
        
        logger.info(f"Security Hooks: {hooks_passed}/{total_hooks} passed")
        
        # Overall assessment
        if status.overall_score >= 95.0 and status.critical_issues == 0:
            logger.info("✅ Security Coordinator: PASSED")
            return True, status
        else:
            logger.warning(f"⚠️  Security Coordinator: Requirements not met")
            return False, status
            
    except Exception as e:
        logger.error(f"❌ Security Coordinator: FAILED - {e}")
        return False, None

async def validate_environment_security():
    """Validate environment security configuration"""
    logger.info("🔧 Validating Environment Security...")
    
    try:
        env_file = Path('.env')
        if not env_file.exists():
            logger.error("❌ Environment file not found")
            return False
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        # Check for required security configurations
        required_configs = [
            'RATE_LIMIT_PER_MINUTE',
            'MAX_LOGIN_ATTEMPTS', 
            'LOCKOUT_DURATION',
            'BCRYPT_ROUNDS',
            'CORS_ALLOWED_ORIGINS'
        ]
        
        missing_configs = []
        for config in required_configs:
            if config not in env_content:
                missing_configs.append(config)
        
        if missing_configs:
            logger.warning(f"⚠️  Missing security configs: {', '.join(missing_configs)}")
            return False
        else:
            logger.info("✅ Environment Security: All required configs present")
            return True
            
    except Exception as e:
        logger.error(f"❌ Environment Security: FAILED - {e}")
        return False

async def run_comprehensive_security_validation():
    """Run comprehensive security validation"""
    logger.info("🚀 Starting Comprehensive Security Validation")
    logger.info("🎯 Target: Maintain 95%+ security score")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Environment Security
    results['environment'] = await validate_environment_security()
    
    # Test 2: Vulnerability Scanner
    results['vulnerability_scanner'] = await test_vulnerability_scanning()
    
    # Test 3: Compliance Checker
    results['compliance_checker'] = await test_compliance_checking()
    
    # Test 4: Secret Rotator
    results['secret_rotator'] = await test_secret_rotation()
    
    # Test 5: Security Coordinator
    coordinator_result, security_status = await test_security_coordinator()
    results['security_coordinator'] = coordinator_result
    
    # Summary
    print("\n" + "=" * 60)
    logger.info("📊 SECURITY VALIDATION SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
    
    for test_name, result in results.items():
        status_emoji = "✅" if result else "❌"
        logger.info(f"{status_emoji} {test_name.replace('_', ' ').title()}: {'PASSED' if result else 'FAILED'}")
    
    if security_status:
        print("\n🛡️  SECURITY STATUS:")
        print(f"   Overall Score: {security_status.overall_score:.1f}%")
        print(f"   Security Grade: {security_status.security_grade}")
        print(f"   Critical Issues: {security_status.critical_issues}")
        print(f"   High Issues: {security_status.high_issues}")
        
        if security_status.overall_score >= 95.0:
            print("   🎯 TARGET ACHIEVED: 95%+ security score maintained")
        else:
            print(f"   ⚠️  TARGET NOT MET: Score below 95% ({security_status.overall_score:.1f}%)")
    
    # Overall result
    all_passed = all(results.values())
    target_score_met = security_status and security_status.overall_score >= 95.0
    
    print("\n" + "=" * 60)
    if all_passed and target_score_met:
        logger.info("🎉 OVERALL RESULT: SUCCESS")
        logger.info("✅ All security tests passed")
        logger.info("✅ 95% security score target maintained")
        logger.info("🛡️  System ready for Phase 1.5 fixes")
        return_code = 0
    else:
        logger.error("🚨 OVERALL RESULT: FAILURE")
        if not all_passed:
            logger.error("❌ Some security tests failed")
        if not target_score_met:
            logger.error("❌ Security score below 95% target")
        logger.error("🔧 Fix security issues before proceeding with fixes")
        return_code = 1
    
    print("=" * 60)
    return return_code

async def main():
    """Main test execution"""
    try:
        return_code = await run_comprehensive_security_validation()
        sys.exit(return_code)
    except KeyboardInterrupt:
        logger.info("Security validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Security validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
