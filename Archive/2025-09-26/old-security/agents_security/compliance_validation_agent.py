"""
Compliance Validation Agent - Ensures COPPA, FERPA, and GDPR compliance
Validates data handling, privacy requirements, and regulatory compliance
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from core.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ComplianceType(Enum):
    """Compliance regulation types"""
    COPPA = "COPPA"  # Children's Online Privacy Protection Act
    FERPA = "FERPA"  # Family Educational Rights and Privacy Act
    GDPR = "GDPR"    # General Data Protection Regulation
    CCPA = "CCPA"    # California Consumer Privacy Act
    HIPAA = "HIPAA"  # Health Insurance Portability and Accountability Act


class ComplianceValidationAgent(BaseAgent):
    """
    Specialized agent for validating regulatory compliance
    Ensures educational platform meets all privacy and data protection requirements
    """

    def __init__(self):
        """Initialize the Compliance Validation Agent"""
        super().__init__(
            name="ComplianceValidationAgent",
            description="Validates regulatory compliance for educational data protection"
        )

        # Compliance requirements
        self.coppa_age_limit = 13
        self.gdpr_consent_age = 16
        self.data_retention_days = 365

        # Validation results cache
        self._validation_cache = {}
        self._cache_expiry = {}

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute compliance validation using SPARC framework

        Args:
            task: Task dictionary with validation requirements

        Returns:
            Validation results with compliance status
        """
        # Situation: Analyze compliance requirements
        situation = self._analyze_situation(task)

        # Problem: Identify compliance gaps
        problem = self._identify_problem(situation)

        # Alternatives: Evaluate remediation options
        alternatives = self._evaluate_alternatives(problem)

        # Recommendation: Propose compliance strategy
        recommendation = self._make_recommendation(alternatives)

        # Conclusion: Execute validation and remediation
        result = await self._execute_recommendation(recommendation, task)

        return result

    def _analyze_situation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compliance requirements for the task"""
        data_type = task.get('data_type', 'general')
        user_age = task.get('user_age')
        user_location = task.get('user_location', 'US')

        situation = {
            'data_type': data_type,
            'user_age': user_age,
            'user_location': user_location,
            'is_minor': user_age < 18 if user_age else None,
            'is_coppa_subject': user_age < self.coppa_age_limit if user_age else None,
            'is_eu_resident': self._is_eu_location(user_location),
            'required_compliance': self._determine_required_compliance(data_type, user_age, user_location),
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"Analyzing compliance situation: {situation['required_compliance']}")
        return situation

    def _identify_problem(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Identify compliance gaps and issues"""
        problems = []

        # COPPA issues
        if situation['is_coppa_subject']:
            problems.append({
                'type': 'coppa_minor',
                'severity': 'critical',
                'requirement': 'parental_consent'
            })

        # GDPR issues
        if situation['is_eu_resident']:
            problems.append({
                'type': 'gdpr_consent',
                'severity': 'high',
                'requirement': 'explicit_consent'
            })

        # FERPA issues for educational data
        if situation['data_type'] == 'educational_record':
            problems.append({
                'type': 'ferpa_protection',
                'severity': 'high',
                'requirement': 'access_control'
            })

        return {
            'problems': problems,
            'total_issues': len(problems),
            'max_severity': max([p['severity'] for p in problems], default='low') if problems else 'none'
        }

    def _evaluate_alternatives(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate compliance remediation alternatives"""
        alternatives = []

        for issue in problem['problems']:
            if issue['type'] == 'coppa_minor':
                alternatives.append({
                    'action': 'require_parental_consent',
                    'priority': 1,
                    'compliance': 'COPPA',
                    'implementation': 'consent_workflow'
                })

            elif issue['type'] == 'gdpr_consent':
                alternatives.append({
                    'action': 'explicit_consent_form',
                    'priority': 2,
                    'compliance': 'GDPR',
                    'implementation': 'consent_management'
                })

            elif issue['type'] == 'ferpa_protection':
                alternatives.append({
                    'action': 'implement_access_controls',
                    'priority': 2,
                    'compliance': 'FERPA',
                    'implementation': 'rbac_system'
                })

        return alternatives

    def _make_recommendation(self, alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make compliance recommendation"""
        if not alternatives:
            return {
                'action': 'maintain_current_compliance',
                'status': 'compliant'
            }

        # Sort by priority
        sorted_alternatives = sorted(alternatives, key=lambda x: x['priority'])

        recommendation = {
            'primary_action': sorted_alternatives[0],
            'all_actions': sorted_alternatives,
            'compliance_status': 'requires_action'
        }

        return recommendation

    async def _execute_recommendation(self, recommendation: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance validation and remediation"""
        action = task.get('action', 'validate')

        try:
            if action == 'validate':
                return await self._validate_compliance(task)
            elif action == 'validate_coppa':
                return await self._validate_coppa(task)
            elif action == 'validate_ferpa':
                return await self._validate_ferpa(task)
            elif action == 'validate_gdpr':
                return await self._validate_gdpr(task)
            elif action == 'check_consent':
                return await self._check_consent(task)
            elif action == 'audit':
                return await self._audit_compliance(task)
            elif action == 'generate_report':
                return await self._generate_compliance_report(task)
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
        except Exception as e:
            logger.error(f"Error executing {action}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _validate_compliance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate overall compliance status"""
        compliance_types = task.get('compliance_types', ['COPPA', 'FERPA', 'GDPR'])

        results = {}
        all_compliant = True

        for compliance_type in compliance_types:
            if compliance_type == 'COPPA':
                result = await self._validate_coppa(task)
            elif compliance_type == 'FERPA':
                result = await self._validate_ferpa(task)
            elif compliance_type == 'GDPR':
                result = await self._validate_gdpr(task)
            else:
                result = {'compliant': False, 'message': f'Unknown compliance type: {compliance_type}'}

            results[compliance_type] = result
            if not result.get('compliant', False):
                all_compliant = False

        return {
            'status': 'success',
            'overall_compliant': all_compliant,
            'compliance_results': results,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _validate_coppa(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate COPPA compliance for children under 13"""
        user_age = task.get('user_age')
        has_parental_consent = task.get('parental_consent', False)
        data_collection = task.get('data_collection', {})

        validation = {
            'compliant': True,
            'checks': {},
            'issues': [],
            'recommendations': []
        }

        # Age verification
        validation['checks']['age_verification'] = user_age is not None
        if not validation['checks']['age_verification']:
            validation['issues'].append('Age verification not implemented')
            validation['compliant'] = False

        # Under 13 checks
        if user_age and user_age < self.coppa_age_limit:
            # Parental consent required
            validation['checks']['parental_consent'] = has_parental_consent
            if not has_parental_consent:
                validation['issues'].append('Parental consent required for users under 13')
                validation['compliant'] = False
                validation['recommendations'].append('Implement parental consent workflow')

            # Data minimization
            sensitive_data = ['full_name', 'address', 'phone', 'social_security', 'geolocation']
            collected_sensitive = [d for d in sensitive_data if data_collection.get(d)]

            validation['checks']['data_minimization'] = len(collected_sensitive) == 0
            if collected_sensitive:
                validation['issues'].append(f'Sensitive data collected from minor: {collected_sensitive}')
                validation['compliant'] = False
                validation['recommendations'].append('Minimize data collection for minors')

            # Third-party sharing restrictions
            validation['checks']['no_third_party_sharing'] = not task.get('third_party_sharing', False)
            if task.get('third_party_sharing', False):
                validation['issues'].append('Third-party data sharing not permitted for COPPA subjects')
                validation['compliant'] = False

        # Data retention
        retention_days = task.get('retention_days', 365)
        validation['checks']['appropriate_retention'] = retention_days <= 365
        if retention_days > 365:
            validation['recommendations'].append(f'Reduce data retention from {retention_days} to 365 days')

        return validation

    async def _validate_ferpa(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate FERPA compliance for educational records"""
        data_type = task.get('data_type', 'general')
        access_controls = task.get('access_controls', {})
        audit_logging = task.get('audit_logging', False)

        validation = {
            'compliant': True,
            'checks': {},
            'issues': [],
            'recommendations': []
        }

        # Only applies to educational records
        if data_type != 'educational_record':
            validation['checks']['ferpa_applicable'] = False
            return validation

        validation['checks']['ferpa_applicable'] = True

        # Access control requirements
        validation['checks']['access_controls'] = bool(access_controls)
        if not access_controls:
            validation['issues'].append('Access controls not implemented for educational records')
            validation['compliant'] = False
            validation['recommendations'].append('Implement role-based access control')

        # Parent access rights (for minors)
        validation['checks']['parent_access'] = access_controls.get('parent_access', False)
        if not access_controls.get('parent_access', False):
            validation['issues'].append('Parent access rights not configured')
            validation['compliant'] = False

        # Audit logging requirement
        validation['checks']['audit_logging'] = audit_logging
        if not audit_logging:
            validation['issues'].append('Audit logging required for FERPA compliance')
            validation['compliant'] = False
            validation['recommendations'].append('Enable comprehensive audit logging')

        # Directory information opt-out
        validation['checks']['directory_opt_out'] = task.get('directory_opt_out', False)
        if not task.get('directory_opt_out', False):
            validation['recommendations'].append('Provide directory information opt-out option')

        # Data disclosure tracking
        validation['checks']['disclosure_tracking'] = task.get('disclosure_tracking', False)
        if not task.get('disclosure_tracking', False):
            validation['issues'].append('Educational record disclosure not tracked')
            validation['compliant'] = False

        return validation

    async def _validate_gdpr(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GDPR compliance for EU residents"""
        user_location = task.get('user_location', 'US')
        consent_obtained = task.get('consent_obtained', False)
        purpose_limitation = task.get('purpose_limitation', False)
        data_portability = task.get('data_portability', False)

        validation = {
            'compliant': True,
            'checks': {},
            'issues': [],
            'recommendations': []
        }

        # Check if GDPR applies
        is_eu = self._is_eu_location(user_location)
        validation['checks']['gdpr_applicable'] = is_eu

        if not is_eu:
            return validation

        # Lawful basis (consent)
        validation['checks']['lawful_basis'] = consent_obtained
        if not consent_obtained:
            validation['issues'].append('No lawful basis for data processing')
            validation['compliant'] = False
            validation['recommendations'].append('Obtain explicit consent for data processing')

        # Purpose limitation
        validation['checks']['purpose_limitation'] = purpose_limitation
        if not purpose_limitation:
            validation['issues'].append('Data used beyond stated purpose')
            validation['compliant'] = False

        # Data minimization
        validation['checks']['data_minimization'] = task.get('data_minimization', False)
        if not task.get('data_minimization', False):
            validation['recommendations'].append('Implement data minimization practices')

        # Right to erasure
        validation['checks']['right_to_erasure'] = task.get('erasure_capability', False)
        if not task.get('erasure_capability', False):
            validation['issues'].append('Right to erasure not implemented')
            validation['compliant'] = False
            validation['recommendations'].append('Implement data deletion capability')

        # Data portability
        validation['checks']['data_portability'] = data_portability
        if not data_portability:
            validation['issues'].append('Data portability not supported')
            validation['compliant'] = False
            validation['recommendations'].append('Implement data export functionality')

        # Privacy by design
        validation['checks']['privacy_by_design'] = task.get('privacy_by_design', False)
        if not task.get('privacy_by_design', False):
            validation['recommendations'].append('Implement privacy by design principles')

        # Data breach notification
        validation['checks']['breach_notification'] = task.get('breach_notification_process', False)
        if not task.get('breach_notification_process', False):
            validation['issues'].append('Data breach notification process not defined')
            validation['compliant'] = False

        return validation

    async def _check_consent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check consent status for a user"""
        user_id = task.get('user_id')
        user_age = task.get('user_age')
        user_location = task.get('user_location', 'US')

        consent_requirements = []

        # COPPA consent
        if user_age and user_age < self.coppa_age_limit:
            consent_requirements.append({
                'type': 'parental_consent',
                'regulation': 'COPPA',
                'required': True,
                'obtained': task.get('parental_consent', False)
            })

        # GDPR consent
        if self._is_eu_location(user_location):
            consent_requirements.append({
                'type': 'data_processing_consent',
                'regulation': 'GDPR',
                'required': True,
                'obtained': task.get('gdpr_consent', False)
            })

            if user_age and user_age < self.gdpr_consent_age:
                consent_requirements.append({
                    'type': 'parental_consent',
                    'regulation': 'GDPR',
                    'required': True,
                    'obtained': task.get('parental_consent', False)
                })

        # Check all consents
        all_obtained = all(c['obtained'] for c in consent_requirements if c['required'])

        return {
            'status': 'success',
            'user_id': user_id,
            'consent_valid': all_obtained,
            'consent_requirements': consent_requirements,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _audit_compliance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive compliance audit"""
        audit_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'compliance_scores': {},
            'total_issues': 0,
            'critical_issues': 0,
            'recommendations': []
        }

        # COPPA Audit
        coppa_result = await self._validate_coppa(task)
        audit_results['compliance_scores']['COPPA'] = {
            'compliant': coppa_result['compliant'],
            'issues': len(coppa_result.get('issues', [])),
            'score': 100 if coppa_result['compliant'] else 0
        }

        # FERPA Audit
        ferpa_result = await self._validate_ferpa(task)
        audit_results['compliance_scores']['FERPA'] = {
            'compliant': ferpa_result['compliant'],
            'issues': len(ferpa_result.get('issues', [])),
            'score': 100 if ferpa_result['compliant'] else 0
        }

        # GDPR Audit
        gdpr_result = await self._validate_gdpr(task)
        audit_results['compliance_scores']['GDPR'] = {
            'compliant': gdpr_result['compliant'],
            'issues': len(gdpr_result.get('issues', [])),
            'score': 100 if gdpr_result['compliant'] else 0
        }

        # Calculate totals
        for score in audit_results['compliance_scores'].values():
            audit_results['total_issues'] += score['issues']
            if score['issues'] > 0 and not score['compliant']:
                audit_results['critical_issues'] += 1

        # Overall compliance
        audit_results['overall_compliant'] = all(
            score['compliant'] for score in audit_results['compliance_scores'].values()
        )

        # Aggregate recommendations
        all_recommendations = set()
        for result in [coppa_result, ferpa_result, gdpr_result]:
            all_recommendations.update(result.get('recommendations', []))

        audit_results['recommendations'] = list(all_recommendations)

        return {
            'status': 'success',
            'audit_results': audit_results
        }

    async def _generate_compliance_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed compliance report"""
        # Perform audit
        audit_result = await self._audit_compliance(task)

        if audit_result['status'] != 'success':
            return audit_result

        audit_data = audit_result['audit_results']

        # Generate report
        report = {
            'title': 'ToolBoxAI Compliance Report',
            'generated_at': datetime.utcnow().isoformat(),
            'executive_summary': self._generate_executive_summary(audit_data),
            'compliance_status': audit_data['overall_compliant'],
            'detailed_findings': {
                'COPPA': self._generate_compliance_section('COPPA', audit_data['compliance_scores']['COPPA']),
                'FERPA': self._generate_compliance_section('FERPA', audit_data['compliance_scores']['FERPA']),
                'GDPR': self._generate_compliance_section('GDPR', audit_data['compliance_scores']['GDPR'])
            },
            'risk_assessment': self._assess_compliance_risk(audit_data),
            'recommendations': audit_data['recommendations'],
            'action_items': self._generate_action_items(audit_data)
        }

        return {
            'status': 'success',
            'report': report
        }

    def _generate_executive_summary(self, audit_data: Dict[str, Any]) -> str:
        """Generate executive summary for compliance report"""
        if audit_data['overall_compliant']:
            return "The platform is fully compliant with COPPA, FERPA, and GDPR regulations."
        else:
            return f"The platform has {audit_data['critical_issues']} critical compliance issues requiring immediate attention."

    def _generate_compliance_section(self, regulation: str, score: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report section for specific regulation"""
        return {
            'regulation': regulation,
            'status': 'Compliant' if score['compliant'] else 'Non-Compliant',
            'score': score['score'],
            'issues_count': score['issues'],
            'severity': 'Critical' if score['issues'] > 0 else 'None'
        }

    def _assess_compliance_risk(self, audit_data: Dict[str, Any]) -> str:
        """Assess overall compliance risk level"""
        if audit_data['critical_issues'] == 0:
            return 'Low Risk'
        elif audit_data['critical_issues'] <= 2:
            return 'Medium Risk'
        else:
            return 'High Risk'

    def _generate_action_items(self, audit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized action items"""
        action_items = []

        for recommendation in audit_data['recommendations']:
            priority = 'High' if 'consent' in recommendation.lower() else 'Medium'
            action_items.append({
                'action': recommendation,
                'priority': priority,
                'estimated_effort': '1-2 weeks'
            })

        return sorted(action_items, key=lambda x: x['priority'])

    def _is_eu_location(self, location: str) -> bool:
        """Check if location is in EU"""
        eu_countries = [
            'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
            'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
            'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
        ]
        return location.upper() in eu_countries

    def _determine_required_compliance(self, data_type: str, user_age: Optional[int], user_location: str) -> List[str]:
        """Determine which compliance regulations apply"""
        required = []

        # COPPA applies to US children under 13
        if user_age and user_age < self.coppa_age_limit:
            required.append('COPPA')

        # FERPA applies to educational records
        if data_type == 'educational_record':
            required.append('FERPA')

        # GDPR applies to EU residents
        if self._is_eu_location(user_location):
            required.append('GDPR')

        return required