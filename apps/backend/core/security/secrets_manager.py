"""
AWS Secrets Manager Integration for ToolBoxAI Solutions
Secure retrieval of secrets with caching and automatic rotation support
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from functools import lru_cache
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages secure retrieval of secrets from AWS Secrets Manager
    with caching and automatic fallback to environment variables
    """

    def __init__(self, region_name: str = None, use_cache: bool = True):
        """
        Initialize the Secrets Manager client

        Args:
            region_name: AWS region (defaults to AWS_REGION env var or us-east-1)
            use_cache: Whether to cache retrieved secrets
        """
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self.use_cache = use_cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes

        try:
            # Initialize boto3 client
            self.client = boto3.client(
                'secretsmanager',
                region_name=self.region_name
            )
            self.available = True
            logger.info("AWS Secrets Manager client initialized successfully")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS Secrets Manager not available, falling back to environment variables: {e}")
            self.client = None
            self.available = False

    def _is_cache_valid(self, secret_name: str) -> bool:
        """Check if cached secret is still valid"""
        if secret_name not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[secret_name]

    def get_secret(self, secret_name: str, fallback_env: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a secret from AWS Secrets Manager with fallback to environment variables

        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            fallback_env: Environment variable prefix for fallback

        Returns:
            Dictionary containing the secret values or None if not found
        """
        # Check cache first
        if self.use_cache and secret_name in self._cache and self._is_cache_valid(secret_name):
            logger.debug(f"Returning cached secret: {secret_name}")
            return self._cache[secret_name]

        # Try AWS Secrets Manager
        if self.available and self.client:
            try:
                response = self.client.get_secret_value(SecretId=secret_name)

                # Parse the secret string
                if 'SecretString' in response:
                    secret = json.loads(response['SecretString'])
                else:
                    # Binary secret (not expected for our use case)
                    logger.error(f"Binary secret not supported: {secret_name}")
                    return None

                # Cache the secret
                if self.use_cache:
                    self._cache[secret_name] = secret
                    self._cache_expiry[secret_name] = datetime.now() + self.cache_duration

                logger.info(f"Successfully retrieved secret: {secret_name}")
                return secret

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    logger.warning(f"Secret not found in AWS: {secret_name}")
                elif error_code == 'AccessDeniedException':
                    logger.error(f"Access denied to secret: {secret_name}")
                else:
                    logger.error(f"Error retrieving secret {secret_name}: {e}")

        # Fallback to environment variables
        if fallback_env:
            logger.info(f"Falling back to environment variables for {secret_name}")
            return self._get_from_env(fallback_env)

        return None

    def _get_from_env(self, prefix: str) -> Dict[str, Any]:
        """
        Get secret values from environment variables

        Args:
            prefix: Prefix for environment variables

        Returns:
            Dictionary of secret values from environment
        """
        env_mapping = {
            'api_keys': {
                'anthropic_api_key': f'{prefix}_ANTHROPIC_API_KEY',
                'openai_api_key': f'{prefix}_OPENAI_API_KEY',
                'langchain_api_key': f'{prefix}_LANGCHAIN_API_KEY',
                'langsmith_api_key': f'{prefix}_LANGSMITH_API_KEY'
            },
            'stripe': {
                'stripe_public_key': f'{prefix}_STRIPE_PUBLIC_KEY',
                'stripe_secret_key': f'{prefix}_STRIPE_SECRET_KEY',
                'stripe_webhook_secret': f'{prefix}_STRIPE_WEBHOOK_SECRET'
            },
            'database': {
                'host': f'{prefix}_DATABASE_HOST',
                'port': f'{prefix}_DATABASE_PORT',
                'database': f'{prefix}_DATABASE_NAME',
                'username': f'{prefix}_DATABASE_USERNAME',
                'password': f'{prefix}_DATABASE_PASSWORD'
            },
            'jwt': {
                'jwt_secret_key': f'{prefix}_JWT_SECRET_KEY',
                'jwt_algorithm': f'{prefix}_JWT_ALGORITHM',
                'jwt_expiration_minutes': f'{prefix}_JWT_EXPIRATION_MINUTES'
            },
            'pusher': {
                'app_id': f'{prefix}_PUSHER_APP_ID',
                'key': f'{prefix}_PUSHER_KEY',
                'secret': f'{prefix}_PUSHER_SECRET',
                'cluster': f'{prefix}_PUSHER_CLUSTER'
            },
            'roblox': {
                'api_key': f'{prefix}_ROBLOX_API_KEY',
                'client_id': f'{prefix}_ROBLOX_CLIENT_ID',
                'client_secret': f'{prefix}_ROBLOX_CLIENT_SECRET'
            }
        }

        # Determine which secret type based on prefix
        secret_type = None
        for key in env_mapping:
            if prefix.lower() in key:
                secret_type = key
                break

        if not secret_type:
            # Direct environment variable mapping
            result = {}
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    result[key.replace(prefix + '_', '').lower()] = value
            return result

        # Map environment variables to secret structure
        result = {}
        for key, env_var in env_mapping[secret_type].items():
            value = os.getenv(env_var.replace(f'{prefix}_', ''))
            if value:
                result[key] = value

        return result

    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys for external services"""
        secret_name = f"toolboxai-{os.getenv('ENV', 'development')}-api-keys"
        return self.get_secret(secret_name, fallback_env='') or {}

    def get_database_credentials(self) -> Dict[str, Any]:
        """Get database connection credentials"""
        secret_name = f"toolboxai-{os.getenv('ENV', 'development')}-database"
        return self.get_secret(secret_name, fallback_env='') or {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'educational_platform_dev'),
            'username': os.getenv('POSTGRES_USER', 'eduplatform'),
            'password': os.getenv('POSTGRES_PASSWORD', 'eduplatform2024')
        }

    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration"""
        secret_name = f"toolboxai-{os.getenv('ENV', 'development')}-jwt"
        return self.get_secret(secret_name, fallback_env='') or {
            'jwt_secret_key': os.getenv('JWT_SECRET_KEY'),
            'jwt_algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
            'jwt_expiration_minutes': int(os.getenv('JWT_EXPIRATION_MINUTES', '1440'))
        }

    def get_stripe_credentials(self) -> Dict[str, str]:
        """Get Stripe payment processing credentials"""
        secret_name = f"toolboxai-{os.getenv('ENV', 'development')}-stripe"
        return self.get_secret(secret_name, fallback_env='') or {
            'stripe_public_key': os.getenv('STRIPE_PUBLIC_KEY'),
            'stripe_secret_key': os.getenv('STRIPE_SECRET_KEY'),
            'stripe_webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET')
        }

    def get_pusher_credentials(self) -> Dict[str, Any]:
        """Get Pusher realtime messaging credentials"""
        secret_name = f"toolboxai-{os.getenv('ENV', 'development')}-pusher"
        return self.get_secret(secret_name, fallback_env='') or {
            'app_id': os.getenv('PUSHER_APP_ID'),
            'key': os.getenv('PUSHER_KEY'),
            'secret': os.getenv('PUSHER_SECRET'),
            'cluster': os.getenv('PUSHER_CLUSTER', 'us2')
        }

    def get_roblox_credentials(self) -> Dict[str, str]:
        """Get Roblox integration credentials"""
        secret_name = f"toolboxai-{os.getenv('ENV', 'development')}-roblox"
        return self.get_secret(secret_name, fallback_env='') or {
            'api_key': os.getenv('ROBLOX_API_KEY'),
            'client_id': os.getenv('ROBLOX_CLIENT_ID'),
            'client_secret': os.getenv('ROBLOX_CLIENT_SECRET')
        }

    def clear_cache(self, secret_name: Optional[str] = None):
        """
        Clear cached secrets

        Args:
            secret_name: Specific secret to clear, or None to clear all
        """
        if secret_name:
            self._cache.pop(secret_name, None)
            self._cache_expiry.pop(secret_name, None)
            logger.info(f"Cleared cache for secret: {secret_name}")
        else:
            self._cache.clear()
            self._cache_expiry.clear()
            logger.info("Cleared all cached secrets")

    def rotate_secret(self, secret_name: str) -> bool:
        """
        Trigger rotation for a secret

        Args:
            secret_name: Name of the secret to rotate

        Returns:
            True if rotation was initiated successfully
        """
        if not self.available or not self.client:
            logger.error("AWS Secrets Manager not available for rotation")
            return False

        try:
            self.client.rotate_secret(
                SecretId=secret_name,
                RotationLambdaARN=os.getenv('SECRET_ROTATION_LAMBDA_ARN')
            )

            # Clear cache for rotated secret
            self.clear_cache(secret_name)

            logger.info(f"Successfully initiated rotation for secret: {secret_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to rotate secret {secret_name}: {e}")
            return False


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create the global Secrets Manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


# Convenience functions
def get_api_key(service: str) -> Optional[str]:
    """
    Get a specific API key

    Args:
        service: Name of the service (anthropic, openai, etc.)

    Returns:
        API key or None if not found
    """
    manager = get_secrets_manager()
    api_keys = manager.get_api_keys()
    return api_keys.get(f'{service}_api_key')


def get_database_url() -> str:
    """Build database URL from credentials"""
    manager = get_secrets_manager()
    creds = manager.get_database_credentials()

    if not creds:
        # Fallback to environment variable
        return os.getenv('DATABASE_URL', '')

    return (
        f"postgresql://{creds['username']}:{creds['password']}"
        f"@{creds['host']}:{creds['port']}/{creds['database']}"
    )