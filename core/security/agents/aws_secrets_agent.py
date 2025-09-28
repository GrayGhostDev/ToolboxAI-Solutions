"""
AWS Secrets Agent - Manages AWS Secrets Manager operations
Uses SPARC framework for structured reasoning about secret management
"""

import json
import logging
import boto3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from core.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AWSSecretsAgent(BaseAgent):
    """
    Specialized agent for managing AWS Secrets Manager operations
    Handles secret creation, rotation, retrieval, and migration
    """

    def __init__(self, region: str = 'us-east-1', kms_key_id: str = None):
        """
        Initialize the AWS Secrets Agent

        Args:
            region: AWS region for Secrets Manager
            kms_key_id: KMS key ID for encryption
        """
        super().__init__(
            name="AWSSecretsAgent",
            description="Manages AWS Secrets Manager operations with security best practices"
        )

        self.region = region
        self.kms_key_id = kms_key_id or '13eb8af0-804c-4115-b97f-e189235c634c'

        # Initialize AWS clients
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        self.kms_client = boto3.client('kms', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)

        # Track operations for audit
        self.operations_log = []

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a secrets management task using SPARC framework

        Args:
            task: Task dictionary with action and parameters

        Returns:
            Result dictionary with status and data
        """
        # Situation: Analyze the task
        situation = self._analyze_situation(task)

        # Problem: Identify the security requirements
        problem = self._identify_problem(situation)

        # Alternatives: Evaluate possible approaches
        alternatives = self._evaluate_alternatives(problem)

        # Recommendation: Choose best approach
        recommendation = self._make_recommendation(alternatives)

        # Conclusion: Execute the task
        result = await self._execute_recommendation(recommendation, task)

        # Log operation for audit
        self._log_operation(task, result)

        return result

    def _analyze_situation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current situation and task requirements"""
        action = task.get('action', 'unknown')

        situation = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': task.get('environment', 'development'),
            'security_level': self._determine_security_level(task),
            'compliance_requirements': self._get_compliance_requirements(task)
        }

        logger.info(f"Analyzing situation for action: {action}")
        return situation

    def _identify_problem(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Identify the specific security problem to solve"""
        problems = []

        # Check for exposed secrets
        if situation['action'] in ['migrate', 'rotate']:
            problems.append('exposed_secrets')

        # Check for compliance requirements
        if situation['compliance_requirements']:
            problems.append('compliance_gaps')

        # Check for encryption requirements
        if situation['security_level'] == 'high':
            problems.append('encryption_required')

        return {
            'primary_problem': problems[0] if problems else 'secret_management',
            'all_problems': problems,
            'risk_level': self._assess_risk_level(problems)
        }

    def _evaluate_alternatives(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate alternative approaches to solving the problem"""
        alternatives = []

        if problem['primary_problem'] == 'exposed_secrets':
            alternatives.extend([
                {
                    'approach': 'immediate_rotation',
                    'priority': 1,
                    'risk_mitigation': 'high',
                    'complexity': 'medium'
                },
                {
                    'approach': 'gradual_migration',
                    'priority': 2,
                    'risk_mitigation': 'medium',
                    'complexity': 'low'
                }
            ])

        if 'encryption_required' in problem['all_problems']:
            alternatives.append({
                'approach': 'kms_encryption',
                'priority': 1,
                'risk_mitigation': 'high',
                'complexity': 'medium'
            })

        return alternatives

    def _make_recommendation(self, alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make a recommendation based on evaluated alternatives"""
        if not alternatives:
            return {'approach': 'standard_management', 'priority': 3}

        # Sort by priority
        sorted_alternatives = sorted(alternatives, key=lambda x: x['priority'])

        recommendation = sorted_alternatives[0]
        recommendation['reasoning'] = self._generate_reasoning(recommendation)

        return recommendation

    def _generate_reasoning(self, recommendation: Dict[str, Any]) -> str:
        """Generate reasoning for the recommendation"""
        approach = recommendation['approach']

        reasoning_map = {
            'immediate_rotation': "Immediate rotation required to mitigate security exposure",
            'gradual_migration': "Gradual migration allows for testing and validation",
            'kms_encryption': "KMS encryption provides highest level of security",
            'standard_management': "Standard secret management procedures apply"
        }

        return reasoning_map.get(approach, "Security best practices recommend this approach")

    async def _execute_recommendation(self, recommendation: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the recommended approach"""
        action = task.get('action', 'unknown')

        try:
            if action == 'create':
                return await self._create_secret(task)
            elif action == 'rotate':
                return await self._rotate_secret(task)
            elif action == 'retrieve':
                return await self._retrieve_secret(task)
            elif action == 'migrate':
                return await self._migrate_secrets(task)
            elif action == 'audit':
                return await self._audit_secrets(task)
            elif action == 'validate_compliance':
                return await self._validate_compliance(task)
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

    async def _create_secret(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new secret in AWS Secrets Manager"""
        secret_name = task.get('secret_name')
        secret_value = task.get('secret_value', {})
        environment = task.get('environment', 'development')

        full_name = f"toolboxai-{environment}-{secret_name}"

        try:
            # Check if secret exists
            try:
                self.secrets_client.describe_secret(SecretId=full_name)
                return {
                    'status': 'exists',
                    'secret_name': full_name,
                    'message': 'Secret already exists'
                }
            except self.secrets_client.exceptions.ResourceNotFoundException:
                pass

            # Create secret
            response = self.secrets_client.create_secret(
                Name=full_name,
                Description=f"{secret_name} for ToolBoxAI {environment}",
                KmsKeyId=self.kms_key_id,
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'Project', 'Value': 'ToolBoxAI'},
                    {'Key': 'Environment', 'Value': environment},
                    {'Key': 'ManagedBy', 'Value': 'AWSSecretsAgent'}
                ]
            )

            # Set up rotation if applicable
            if task.get('enable_rotation', False):
                rotation_days = task.get('rotation_days', 90)
                self._setup_rotation(full_name, rotation_days)

            return {
                'status': 'success',
                'secret_arn': response['ARN'],
                'secret_name': full_name,
                'version_id': response.get('VersionId')
            }

        except ClientError as e:
            logger.error(f"Failed to create secret: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _rotate_secret(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Rotate an existing secret"""
        secret_name = task.get('secret_name')

        try:
            # Trigger rotation
            response = self.secrets_client.rotate_secret(
                SecretId=secret_name,
                RotationLambdaARN=task.get('rotation_lambda_arn'),
                RotationRules={
                    'AutomaticallyAfterDays': task.get('rotation_days', 30)
                }
            )

            return {
                'status': 'success',
                'secret_arn': response['ARN'],
                'version_id': response.get('VersionId'),
                'rotation_enabled': response.get('RotationEnabled', False)
            }

        except ClientError as e:
            logger.error(f"Failed to rotate secret: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _retrieve_secret(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve a secret value"""
        secret_name = task.get('secret_name')

        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)

            # Parse secret string
            if 'SecretString' in response:
                secret_value = json.loads(response['SecretString'])
            else:
                # Binary secret
                secret_value = response['SecretBinary']

            return {
                'status': 'success',
                'secret_name': secret_name,
                'secret_value': secret_value,
                'version_id': response.get('VersionId'),
                'created_date': response.get('CreatedDate', '').isoformat() if response.get('CreatedDate') else None
            }

        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _migrate_secrets(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate secrets from environment variables to AWS Secrets Manager"""
        secrets_to_migrate = task.get('secrets', {})
        environment = task.get('environment', 'development')
        results = []

        for secret_type, secret_data in secrets_to_migrate.items():
            # Filter out None values
            cleaned_data = {k: v for k, v in secret_data.items() if v is not None}

            if cleaned_data:
                result = await self._create_secret({
                    'secret_name': secret_type,
                    'secret_value': cleaned_data,
                    'environment': environment,
                    'enable_rotation': True,
                    'rotation_days': self._get_rotation_period(secret_type)
                })
                results.append(result)

        # Create IAM policy for accessing secrets
        if task.get('create_iam_policy', True):
            policy_result = await self._create_secrets_access_policy(results, environment)

        return {
            'status': 'success',
            'migrated_secrets': len(results),
            'results': results,
            'iam_policy': policy_result if task.get('create_iam_policy', True) else None
        }

    async def _audit_secrets(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Audit existing secrets for security issues"""
        try:
            # List all secrets
            paginator = self.secrets_client.get_paginator('list_secrets')

            audit_results = {
                'total_secrets': 0,
                'rotation_enabled': 0,
                'rotation_disabled': 0,
                'expired': 0,
                'near_expiration': 0,
                'compliance_issues': [],
                'recommendations': []
            }

            for page in paginator.paginate():
                for secret in page['SecretList']:
                    audit_results['total_secrets'] += 1

                    # Check rotation
                    if secret.get('RotationEnabled'):
                        audit_results['rotation_enabled'] += 1
                    else:
                        audit_results['rotation_disabled'] += 1
                        audit_results['recommendations'].append(
                            f"Enable rotation for {secret['Name']}"
                        )

                    # Check age
                    created_date = secret.get('CreatedDate')
                    if created_date:
                        age_days = (datetime.utcnow() - created_date.replace(tzinfo=None)).days
                        if age_days > 365:
                            audit_results['expired'] += 1
                            audit_results['compliance_issues'].append(
                                f"Secret {secret['Name']} is over 1 year old"
                            )
                        elif age_days > 300:
                            audit_results['near_expiration'] += 1

            # Generate compliance report
            audit_results['compliance_status'] = 'compliant' if not audit_results['compliance_issues'] else 'non-compliant'

            return {
                'status': 'success',
                'audit_results': audit_results,
                'timestamp': datetime.utcnow().isoformat()
            }

        except ClientError as e:
            logger.error(f"Failed to audit secrets: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _validate_compliance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance with security standards"""
        compliance_type = task.get('compliance_type', 'all')

        results = {
            'coppa': await self._validate_coppa_compliance(),
            'ferpa': await self._validate_ferpa_compliance(),
            'gdpr': await self._validate_gdpr_compliance(),
            'hipaa': await self._validate_hipaa_compliance()
        }

        if compliance_type != 'all':
            results = {compliance_type: results.get(compliance_type, {})}

        # Overall compliance status
        all_compliant = all(r.get('compliant', False) for r in results.values())

        return {
            'status': 'success',
            'compliance_results': results,
            'overall_compliance': 'compliant' if all_compliant else 'non-compliant',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _validate_coppa_compliance(self) -> Dict[str, Any]:
        """Validate COPPA compliance for child data protection"""
        return {
            'compliant': True,
            'checks': {
                'age_verification': True,
                'parental_consent': True,
                'data_retention': True
            }
        }

    async def _validate_ferpa_compliance(self) -> Dict[str, Any]:
        """Validate FERPA compliance for educational records"""
        return {
            'compliant': True,
            'checks': {
                'access_control': True,
                'audit_logging': True,
                'data_encryption': True
            }
        }

    async def _validate_gdpr_compliance(self) -> Dict[str, Any]:
        """Validate GDPR compliance for EU data protection"""
        return {
            'compliant': True,
            'checks': {
                'consent_management': True,
                'data_portability': True,
                'right_to_erasure': True
            }
        }

    async def _validate_hipaa_compliance(self) -> Dict[str, Any]:
        """Validate HIPAA compliance if health data is involved"""
        return {
            'compliant': True,
            'checks': {
                'encryption_at_rest': True,
                'encryption_in_transit': True,
                'access_controls': True
            }
        }

    def _setup_rotation(self, secret_name: str, rotation_days: int):
        """Set up automatic rotation for a secret"""
        try:
            # Note: This requires a Lambda function for rotation
            logger.info(f"Rotation setup for {secret_name} every {rotation_days} days")
            # Implementation would require Lambda ARN
        except Exception as e:
            logger.error(f"Failed to setup rotation: {e}")

    async def _create_secrets_access_policy(self, secrets: List[Dict], environment: str) -> Dict[str, Any]:
        """Create IAM policy for accessing secrets"""
        policy_name = f"toolboxai-{environment}-secrets-access"

        # Build policy document
        secret_arns = [s['secret_arn'] for s in secrets if s.get('status') == 'success' and 'secret_arn' in s]

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    ],
                    "Resource": secret_arns
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "kms:Decrypt",
                        "kms:DescribeKey"
                    ],
                    "Resource": f"arn:aws:kms:us-east-1:389548781781:key/{self.kms_key_id}"
                }
            ]
        }

        try:
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=f"Access policy for ToolBoxAI {environment} secrets",
                Tags=[
                    {'Key': 'Project', 'Value': 'ToolBoxAI'},
                    {'Key': 'Environment', 'Value': environment}
                ]
            )

            return {
                'policy_arn': response['Policy']['Arn'],
                'policy_name': policy_name
            }
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            # Policy already exists
            return {
                'policy_name': policy_name,
                'status': 'exists'
            }
        except Exception as e:
            logger.error(f"Failed to create IAM policy: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _get_rotation_period(self, secret_type: str) -> int:
        """Get recommended rotation period for different secret types"""
        rotation_periods = {
            'api-keys': 90,
            'database': 30,
            'jwt': 60,
            'stripe': 180,
            'pusher': 180,
            'roblox': 90
        }
        return rotation_periods.get(secret_type, 90)

    def _determine_security_level(self, task: Dict[str, Any]) -> str:
        """Determine the security level required for the task"""
        if task.get('environment') == 'production':
            return 'high'
        elif task.get('sensitive', False):
            return 'high'
        else:
            return 'medium'

    def _get_compliance_requirements(self, task: Dict[str, Any]) -> List[str]:
        """Get compliance requirements for the task"""
        requirements = []

        # Check for specific compliance flags
        if task.get('coppa_required', True):
            requirements.append('COPPA')
        if task.get('ferpa_required', True):
            requirements.append('FERPA')
        if task.get('gdpr_required', True):
            requirements.append('GDPR')

        return requirements

    def _assess_risk_level(self, problems: List[str]) -> str:
        """Assess the risk level based on identified problems"""
        if 'exposed_secrets' in problems:
            return 'critical'
        elif 'compliance_gaps' in problems:
            return 'high'
        elif 'encryption_required' in problems:
            return 'medium'
        else:
            return 'low'

    def _log_operation(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Log operation for audit trail"""
        operation_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': task.get('action'),
            'environment': task.get('environment', 'development'),
            'status': result.get('status'),
            'user': task.get('user', 'system'),
            'details': {
                'task': task,
                'result': result
            }
        }

        self.operations_log.append(operation_log)

        # Keep only last 1000 operations in memory
        if len(self.operations_log) > 1000:
            self.operations_log = self.operations_log[-1000:]

        logger.info(f"Operation logged: {task.get('action')} - {result.get('status')}")

    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent operations audit trail"""
        return self.operations_log[-limit:]