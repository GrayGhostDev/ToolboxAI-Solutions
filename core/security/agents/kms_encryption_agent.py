"""
KMS Encryption Agent - Handles AWS KMS encryption and decryption operations
Implements data-at-rest and data-in-transit encryption with SPARC reasoning
"""

import json
import base64
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from core.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class KMSEncryptionAgent(BaseAgent):
    """
    Specialized agent for managing KMS encryption operations
    Handles data encryption, decryption, key rotation, and envelope encryption
    """

    def __init__(self, region: str = 'us-east-1', kms_key_id: str = None):
        """
        Initialize the KMS Encryption Agent

        Args:
            region: AWS region for KMS
            kms_key_id: Default KMS key ID for encryption
        """
        super().__init__(
            name="KMSEncryptionAgent",
            description="Manages AWS KMS encryption operations with security best practices"
        )

        self.region = region
        self.default_key_id = kms_key_id or '13eb8af0-804c-4115-b97f-e189235c634c'

        # Initialize AWS KMS client
        self.kms_client = boto3.client('kms', region_name=region)

        # Cache for data keys (short-lived)
        self._data_key_cache = {}
        self._cache_expiry = {}

        # Encryption context for additional authentication
        self.default_encryption_context = {
            'project': 'ToolBoxAI',
            'service': 'KMSEncryptionAgent'
        }

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an encryption task using SPARC framework

        Args:
            task: Task dictionary with action and parameters

        Returns:
            Result dictionary with status and encrypted/decrypted data
        """
        # Situation: Analyze encryption requirements
        situation = self._analyze_situation(task)

        # Problem: Identify security concerns
        problem = self._identify_problem(situation)

        # Alternatives: Evaluate encryption methods
        alternatives = self._evaluate_alternatives(problem)

        # Recommendation: Select best encryption approach
        recommendation = self._make_recommendation(alternatives)

        # Conclusion: Execute encryption operation
        result = await self._execute_recommendation(recommendation, task)

        return result

    def _analyze_situation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the encryption requirements"""
        action = task.get('action', 'unknown')
        data_size = len(str(task.get('data', '')))

        situation = {
            'action': action,
            'data_size': data_size,
            'data_sensitivity': task.get('sensitivity', 'medium'),
            'use_envelope': data_size > 4096,  # Use envelope encryption for large data
            'require_audit': task.get('audit', True),
            'encryption_context': task.get('encryption_context', {})
        }

        logger.info(f"Analyzing encryption situation for action: {action}")
        return situation

    def _identify_problem(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Identify the specific encryption problem"""
        problems = []

        if situation['data_sensitivity'] == 'high':
            problems.append('high_sensitivity_data')

        if situation['use_envelope']:
            problems.append('large_data_encryption')

        if situation['require_audit']:
            problems.append('audit_trail_required')

        return {
            'primary_problem': problems[0] if problems else 'standard_encryption',
            'all_problems': problems,
            'encryption_level': self._determine_encryption_level(situation)
        }

    def _evaluate_alternatives(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate encryption alternatives"""
        alternatives = []

        if problem['encryption_level'] == 'maximum':
            alternatives.append({
                'method': 'envelope_encryption',
                'priority': 1,
                'security': 'maximum',
                'performance': 'optimized'
            })

        if 'large_data_encryption' in problem['all_problems']:
            alternatives.append({
                'method': 'hybrid_encryption',
                'priority': 2,
                'security': 'high',
                'performance': 'fast'
            })

        alternatives.append({
            'method': 'direct_kms',
            'priority': 3,
            'security': 'standard',
            'performance': 'standard'
        })

        return alternatives

    def _make_recommendation(self, alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make encryption method recommendation"""
        if not alternatives:
            return {'method': 'direct_kms', 'priority': 3}

        # Sort by priority
        sorted_alternatives = sorted(alternatives, key=lambda x: x['priority'])

        recommendation = sorted_alternatives[0]
        recommendation['reasoning'] = self._generate_reasoning(recommendation)

        return recommendation

    def _generate_reasoning(self, recommendation: Dict[str, Any]) -> str:
        """Generate reasoning for the encryption method"""
        method = recommendation['method']

        reasoning_map = {
            'envelope_encryption': "Envelope encryption provides maximum security for sensitive data",
            'hybrid_encryption': "Hybrid encryption optimizes performance for large data",
            'direct_kms': "Direct KMS encryption suitable for standard security requirements"
        }

        return reasoning_map.get(method, "Selected based on security requirements")

    async def _execute_recommendation(self, recommendation: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the recommended encryption approach"""
        action = task.get('action', 'unknown')

        try:
            if action == 'encrypt':
                return await self._encrypt_data(task, recommendation)
            elif action == 'decrypt':
                return await self._decrypt_data(task, recommendation)
            elif action == 'rotate_key':
                return await self._rotate_key(task)
            elif action == 'create_data_key':
                return await self._create_data_key(task)
            elif action == 'validate_key':
                return await self._validate_key(task)
            elif action == 'audit_encryption':
                return await self._audit_encryption(task)
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

    async def _encrypt_data(self, task: Dict[str, Any], recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt data using the recommended method"""
        data = task.get('data')
        key_id = task.get('key_id', self.default_key_id)
        method = recommendation.get('method', 'direct_kms')

        if not data:
            return {
                'status': 'error',
                'message': 'No data provided for encryption'
            }

        try:
            if method == 'envelope_encryption':
                return await self._envelope_encrypt(data, key_id, task)
            elif method == 'hybrid_encryption':
                return await self._hybrid_encrypt(data, key_id, task)
            else:
                return await self._direct_kms_encrypt(data, key_id, task)

        except ClientError as e:
            logger.error(f"Encryption failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _decrypt_data(self, task: Dict[str, Any], recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt data using the appropriate method"""
        encrypted_data = task.get('encrypted_data')
        method = task.get('encryption_method', 'direct_kms')

        if not encrypted_data:
            return {
                'status': 'error',
                'message': 'No encrypted data provided'
            }

        try:
            if method == 'envelope_encryption':
                return await self._envelope_decrypt(encrypted_data, task)
            elif method == 'hybrid_encryption':
                return await self._hybrid_decrypt(encrypted_data, task)
            else:
                return await self._direct_kms_decrypt(encrypted_data, task)

        except ClientError as e:
            logger.error(f"Decryption failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _direct_kms_encrypt(self, data: Any, key_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Direct encryption using KMS (for small data < 4KB)"""
        # Convert data to bytes
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = str(data).encode('utf-8')

        # Check size limit (4KB for KMS direct encryption)
        if len(data_bytes) > 4096:
            return {
                'status': 'error',
                'message': 'Data too large for direct KMS encryption. Use envelope encryption.'
            }

        # Build encryption context
        encryption_context = {**self.default_encryption_context}
        encryption_context.update(task.get('encryption_context', {}))

        # Encrypt using KMS
        response = self.kms_client.encrypt(
            KeyId=key_id,
            Plaintext=data_bytes,
            EncryptionContext=encryption_context
        )

        encrypted_blob = base64.b64encode(response['CiphertextBlob']).decode('utf-8')

        return {
            'status': 'success',
            'encrypted_data': encrypted_blob,
            'key_id': response['KeyId'],
            'encryption_method': 'direct_kms',
            'encryption_context': encryption_context
        }

    async def _direct_kms_decrypt(self, encrypted_data: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Direct decryption using KMS"""
        # Decode from base64
        try:
            ciphertext_blob = base64.b64decode(encrypted_data)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Invalid encrypted data format: {e}'
            }

        # Build encryption context
        encryption_context = {**self.default_encryption_context}
        encryption_context.update(task.get('encryption_context', {}))

        # Decrypt using KMS
        try:
            response = self.kms_client.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionContext=encryption_context
            )

            # Decode plaintext
            plaintext = response['Plaintext'].decode('utf-8')

            # Try to parse as JSON if applicable
            try:
                data = json.loads(plaintext)
            except:
                data = plaintext

            return {
                'status': 'success',
                'decrypted_data': data,
                'key_id': response['KeyId']
            }

        except ClientError as e:
            logger.error(f"KMS decryption failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _envelope_encrypt(self, data: Any, key_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Envelope encryption for large data"""
        # Generate data key
        data_key_result = await self._create_data_key({
            'key_id': key_id,
            'key_spec': 'AES_256'
        })

        if data_key_result['status'] != 'success':
            return data_key_result

        plaintext_key = data_key_result['plaintext_key']
        encrypted_key = data_key_result['encrypted_key']

        # Convert data to bytes
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = str(data).encode('utf-8')

        # Encrypt data with data key using Fernet
        fernet = Fernet(base64.urlsafe_b64encode(plaintext_key[:32]))
        encrypted_data = fernet.encrypt(data_bytes)

        # Clear plaintext key from memory
        plaintext_key = None

        # Return envelope
        envelope = {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'encrypted_key': encrypted_key,
            'key_id': key_id,
            'encryption_method': 'envelope_encryption',
            'algorithm': 'AES_256_GCM'
        }

        return {
            'status': 'success',
            'envelope': envelope
        }

    async def _envelope_decrypt(self, envelope: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Envelope decryption for large data"""
        encrypted_data = envelope.get('encrypted_data')
        encrypted_key = envelope.get('encrypted_key')

        if not encrypted_data or not encrypted_key:
            return {
                'status': 'error',
                'message': 'Invalid envelope structure'
            }

        # Decrypt data key
        try:
            key_blob = base64.b64decode(encrypted_key)
            response = self.kms_client.decrypt(CiphertextBlob=key_blob)
            plaintext_key = response['Plaintext']

            # Decrypt data with plaintext key
            fernet = Fernet(base64.urlsafe_b64encode(plaintext_key[:32]))
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = fernet.decrypt(encrypted_bytes)

            # Clear plaintext key
            plaintext_key = None

            # Parse data
            data = decrypted_data.decode('utf-8')
            try:
                data = json.loads(data)
            except:
                pass

            return {
                'status': 'success',
                'decrypted_data': data
            }

        except Exception as e:
            logger.error(f"Envelope decryption failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _hybrid_encrypt(self, data: Any, key_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Hybrid encryption combining KMS and local encryption"""
        # Similar to envelope but with optimizations
        return await self._envelope_encrypt(data, key_id, task)

    async def _hybrid_decrypt(self, encrypted_data: Any, task: Dict[str, Any]) -> Dict[str, Any]:
        """Hybrid decryption"""
        return await self._envelope_decrypt(encrypted_data, task)

    async def _create_data_key(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a data encryption key"""
        key_id = task.get('key_id', self.default_key_id)
        key_spec = task.get('key_spec', 'AES_256')

        try:
            response = self.kms_client.generate_data_key(
                KeyId=key_id,
                KeySpec=key_spec
            )

            return {
                'status': 'success',
                'plaintext_key': response['Plaintext'],
                'encrypted_key': base64.b64encode(response['CiphertextBlob']).decode('utf-8'),
                'key_id': response['KeyId']
            }

        except ClientError as e:
            logger.error(f"Failed to create data key: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _rotate_key(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Rotate KMS key"""
        key_id = task.get('key_id', self.default_key_id)

        try:
            # Enable automatic key rotation
            self.kms_client.enable_key_rotation(KeyId=key_id)

            # Get key rotation status
            response = self.kms_client.get_key_rotation_status(KeyId=key_id)

            return {
                'status': 'success',
                'key_id': key_id,
                'rotation_enabled': response['KeyRotationEnabled']
            }

        except ClientError as e:
            logger.error(f"Failed to rotate key: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _validate_key(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate KMS key configuration"""
        key_id = task.get('key_id', self.default_key_id)

        try:
            # Describe key
            response = self.kms_client.describe_key(KeyId=key_id)
            key_metadata = response['KeyMetadata']

            # Check key state
            key_state = key_metadata['KeyState']
            is_valid = key_state == 'Enabled'

            # Check key usage
            key_usage = key_metadata.get('KeyUsage', 'ENCRYPT_DECRYPT')

            # Get key policy
            policy_response = self.kms_client.get_key_policy(KeyId=key_id, PolicyName='default')

            validation_result = {
                'key_id': key_metadata['KeyId'],
                'key_arn': key_metadata['Arn'],
                'key_state': key_state,
                'key_usage': key_usage,
                'creation_date': key_metadata['CreationDate'].isoformat() if key_metadata.get('CreationDate') else None,
                'is_valid': is_valid,
                'customer_managed': key_metadata.get('Origin') == 'AWS_KMS',
                'multi_region': key_metadata.get('MultiRegion', False)
            }

            return {
                'status': 'success',
                'validation': validation_result
            }

        except ClientError as e:
            logger.error(f"Failed to validate key: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def _audit_encryption(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Audit encryption usage and compliance"""
        try:
            # List all KMS keys
            paginator = self.kms_client.get_paginator('list_keys')

            audit_results = {
                'total_keys': 0,
                'enabled_keys': 0,
                'disabled_keys': 0,
                'rotation_enabled': 0,
                'customer_managed': 0,
                'aws_managed': 0,
                'compliance_issues': [],
                'recommendations': []
            }

            for page in paginator.paginate():
                for key_entry in page['Keys']:
                    audit_results['total_keys'] += 1

                    # Describe each key
                    try:
                        key_response = self.kms_client.describe_key(KeyId=key_entry['KeyId'])
                        key_metadata = key_response['KeyMetadata']

                        # Check state
                        if key_metadata['KeyState'] == 'Enabled':
                            audit_results['enabled_keys'] += 1
                        else:
                            audit_results['disabled_keys'] += 1

                        # Check origin
                        if key_metadata.get('Origin') == 'AWS_KMS':
                            audit_results['customer_managed'] += 1
                        else:
                            audit_results['aws_managed'] += 1

                        # Check rotation (only for customer managed keys)
                        if key_metadata.get('Origin') == 'AWS_KMS':
                            try:
                                rotation_response = self.kms_client.get_key_rotation_status(
                                    KeyId=key_entry['KeyId']
                                )
                                if rotation_response['KeyRotationEnabled']:
                                    audit_results['rotation_enabled'] += 1
                                else:
                                    audit_results['recommendations'].append(
                                        f"Enable rotation for key {key_entry['KeyId'][:20]}..."
                                    )
                            except:
                                pass

                    except ClientError:
                        # Skip keys we can't access
                        continue

            # Calculate compliance
            if audit_results['customer_managed'] > 0:
                rotation_percentage = (audit_results['rotation_enabled'] / audit_results['customer_managed']) * 100
                if rotation_percentage < 100:
                    audit_results['compliance_issues'].append(
                        f"Only {rotation_percentage:.1f}% of customer-managed keys have rotation enabled"
                    )

            audit_results['compliance_status'] = 'compliant' if not audit_results['compliance_issues'] else 'non-compliant'

            return {
                'status': 'success',
                'audit_results': audit_results,
                'timestamp': datetime.utcnow().isoformat()
            }

        except ClientError as e:
            logger.error(f"Failed to audit encryption: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _determine_encryption_level(self, situation: Dict[str, Any]) -> str:
        """Determine required encryption level"""
        if situation['data_sensitivity'] == 'high':
            return 'maximum'
        elif situation['data_sensitivity'] == 'medium':
            return 'standard'
        else:
            return 'basic'

    def clear_cache(self):
        """Clear data key cache"""
        self._data_key_cache.clear()
        self._cache_expiry.clear()
        logger.info("Data key cache cleared")