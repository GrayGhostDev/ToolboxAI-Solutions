"""
HashiCorp Vault Manager for Secret Management
Implements secure secret storage, rotation, and dynamic credentials
Using hvac library with AppRole authentication
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hvac
from hvac.exceptions import InvalidPath, Forbidden, InvalidRequest
from functools import lru_cache
import asyncio
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Types of secrets managed by Vault"""
    DATABASE = "database"
    API_KEY = "api_key"
    ENCRYPTION_KEY = "encryption"
    JWT_KEY = "jwt"
    OAUTH = "oauth"
    CERTIFICATE = "certificate"
    SERVICE_ACCOUNT = "service_account"


@dataclass
class SecretMetadata:
    """Metadata for secret management"""
    name: str
    path: str
    type: SecretType
    version: int
    created_at: datetime
    rotated_at: Optional[datetime]
    rotation_period_days: int = 30
    description: str = ""
    tags: List[str] = None


class VaultManager:
    """
    Centralized secret management using HashiCorp Vault

    Features:
    - AppRole authentication
    - Dynamic database credentials
    - Automatic secret rotation
    - Encryption as a service
    - Audit logging
    - High availability support
    """

    def __init__(self):
        """Initialize Vault client with configuration"""
        self.vault_addr = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200')
        self.vault_token = os.getenv('VAULT_TOKEN')
        self.role_id = os.getenv('VAULT_ROLE_ID')
        self.secret_id = os.getenv('VAULT_SECRET_ID')
        # Namespace is Enterprise-only feature, default to empty for OSS
        self.namespace = os.getenv('VAULT_NAMESPACE', '')
        # TLS verification (disable only for development with self-signed certs)
        self.skip_verify = os.getenv('VAULT_SKIP_VERIFY', 'false').lower() in ('true', '1', 'yes')

        # Initialize client
        self.client = self._initialize_client()

        # Cache for frequently accessed secrets
        self._secret_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes

        # Rotation tracking
        self._rotation_schedule: Dict[str, datetime] = {}

    def _initialize_client(self) -> hvac.Client:
        """Initialize and authenticate Vault client"""
        # Set verify based on VAULT_SKIP_VERIFY (for dev environments only)
        verify = not self.skip_verify
        if self.skip_verify:
            logger.warning("TLS verification disabled - DO NOT use in production!")

        client = hvac.Client(
            url=self.vault_addr,
            namespace=self.namespace if self.namespace else None,
            verify=verify
        )

        # Authenticate using AppRole or token
        if self.role_id and self.secret_id:
            self._authenticate_approle(client)
        elif self.vault_token:
            client.token = self.vault_token
        else:
            raise ValueError("No Vault authentication method configured")

        if not client.is_authenticated():
            raise ConnectionError("Failed to authenticate with Vault")

        logger.info(f"Successfully connected to Vault at {self.vault_addr}")
        return client

    def _authenticate_approle(self, client: hvac.Client):
        """Authenticate using AppRole method"""
        try:
            response = client.auth.approle.login(
                role_id=self.role_id,
                secret_id=self.secret_id
            )
            client.token = response['auth']['client_token']
            logger.info("Successfully authenticated with AppRole")
        except Exception as e:
            logger.error(f"AppRole authentication failed: {e}")
            raise

    @contextmanager
    def _ensure_authenticated(self):
        """Ensure client is authenticated before operations"""
        if not self.client.is_authenticated():
            self.client = self._initialize_client()
        yield self.client

    def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """
        Retrieve secret from Vault

        Args:
            path: Vault path to secret
            key: Specific key within secret (optional)

        Returns:
            Secret value or entire secret dict
        """
        cache_key = f"{path}:{key}" if key else path

        # Check cache first
        if cache_key in self._secret_cache:
            cached = self._secret_cache[cache_key]
            if cached['expires'] > datetime.now():
                return cached['value']

        try:
            with self._ensure_authenticated() as client:
                response = client.secrets.kv.v2.read_secret_version(
                    mount_point='secret',
                    path=path
                )

                data = response['data']['data']

                # Cache the result
                self._secret_cache[cache_key] = {
                    'value': data.get(key) if key else data,
                    'expires': datetime.now() + timedelta(seconds=self._cache_ttl)
                }

                return data.get(key) if key else data

        except InvalidPath:
            logger.error(f"Secret not found at path: {path}")
            raise KeyError(f"Secret not found: {path}")
        except Exception as e:
            logger.error(f"Error retrieving secret: {e}")
            raise

    def set_secret(self, path: str, data: Dict[str, Any],
                   metadata: Optional[SecretMetadata] = None) -> bool:
        """
        Store secret in Vault

        Args:
            path: Vault path for secret
            data: Secret data to store
            metadata: Optional metadata for secret

        Returns:
            Success status
        """
        try:
            with self._ensure_authenticated() as client:
                # Add metadata to secret if provided
                if metadata:
                    data['_metadata'] = {
                        'type': metadata.type,
                        'created_at': metadata.created_at.isoformat(),
                        'rotation_period_days': metadata.rotation_period_days,
                        'description': metadata.description,
                        'tags': metadata.tags or []
                    }

                client.secrets.kv.v2.create_or_update_secret(
                    mount_point='secret',
                    path=path,
                    secret=data
                )

                # Invalidate cache
                self._invalidate_cache(path)

                # Schedule rotation if metadata provided
                if metadata and metadata.rotation_period_days > 0:
                    self._schedule_rotation(path, metadata.rotation_period_days)

                logger.info(f"Successfully stored secret at {path}")
                return True

        except Exception as e:
            logger.error(f"Error storing secret: {e}")
            raise

    def delete_secret(self, path: str, versions: Optional[List[int]] = None) -> bool:
        """
        Delete secret from Vault

        Args:
            path: Vault path to secret
            versions: Specific versions to delete (None = all)

        Returns:
            Success status
        """
        try:
            with self._ensure_authenticated() as client:
                if versions:
                    client.secrets.kv.v2.delete_secret_versions(
                        mount_point='secret',
                        path=path,
                        versions=versions
                    )
                else:
                    client.secrets.kv.v2.delete_metadata_and_all_versions(
                        mount_point='secret',
                        path=path
                    )

                self._invalidate_cache(path)
                logger.info(f"Successfully deleted secret at {path}")
                return True

        except Exception as e:
            logger.error(f"Error deleting secret: {e}")
            raise

    def rotate_secret(self, path: str, new_value: Any = None) -> bool:
        """
        Rotate a secret to a new value

        Args:
            path: Vault path to secret
            new_value: New secret value (auto-generated if None)

        Returns:
            Success status
        """
        try:
            # Get current secret
            current = self.get_secret(path)

            # Generate new value if not provided
            if new_value is None:
                new_value = self._generate_secret_value(path, current)

            # Store new version
            self.set_secret(path, new_value)

            # Update rotation timestamp
            self._rotation_schedule[path] = datetime.now()

            logger.info(f"Successfully rotated secret at {path}")
            return True

        except Exception as e:
            logger.error(f"Error rotating secret: {e}")
            raise

    def get_dynamic_database_credentials(self, database: str,
                                        ttl: str = "1h") -> Dict[str, str]:
        """
        Get dynamic database credentials from Vault

        Args:
            database: Database role name
            ttl: Time to live for credentials

        Returns:
            Dictionary with username and password
        """
        try:
            with self._ensure_authenticated() as client:
                response = client.secrets.database.generate_credentials(
                    name=database,
                    mount_point='database',
                    ttl=ttl
                )

                return {
                    'username': response['data']['username'],
                    'password': response['data']['password'],
                    'expires_at': datetime.now() + timedelta(hours=1)
                }

        except Exception as e:
            logger.error(f"Error getting dynamic DB credentials: {e}")
            raise

    def encrypt_data(self, plaintext: str, key_name: str = "default") -> str:
        """
        Encrypt data using Vault's Transit engine

        Args:
            plaintext: Data to encrypt
            key_name: Encryption key name

        Returns:
            Ciphertext
        """
        try:
            with self._ensure_authenticated() as client:
                response = client.secrets.transit.encrypt_data(
                    mount_point='transit',
                    name=key_name,
                    plaintext=plaintext
                )
                return response['data']['ciphertext']

        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt_data(self, ciphertext: str, key_name: str = "default") -> str:
        """
        Decrypt data using Vault's Transit engine

        Args:
            ciphertext: Data to decrypt
            key_name: Encryption key name

        Returns:
            Plaintext
        """
        try:
            with self._ensure_authenticated() as client:
                response = client.secrets.transit.decrypt_data(
                    mount_point='transit',
                    name=key_name,
                    ciphertext=ciphertext
                )
                return response['data']['plaintext']

        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

    def list_secrets(self, path: str = "") -> List[str]:
        """
        List secrets at a given path

        Args:
            path: Vault path to list

        Returns:
            List of secret names
        """
        try:
            with self._ensure_authenticated() as client:
                response = client.secrets.kv.v2.list_secrets(
                    mount_point='secret',
                    path=path
                )
                return response.get('data', {}).get('keys', [])

        except InvalidPath:
            return []
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            raise

    def get_secret_metadata(self, path: str) -> SecretMetadata:
        """
        Get metadata for a secret

        Args:
            path: Vault path to secret

        Returns:
            SecretMetadata object
        """
        try:
            with self._ensure_authenticated() as client:
                response = client.secrets.kv.v2.read_secret_metadata(
                    mount_point='secret',
                    path=path
                )

                data = response['data']
                custom_metadata = data.get('custom_metadata', {})

                return SecretMetadata(
                    name=path.split('/')[-1],
                    path=path,
                    type=SecretType(custom_metadata.get('type', 'api_key')),
                    version=data['current_version'],
                    created_at=datetime.fromisoformat(data['created_time']),
                    rotated_at=datetime.fromisoformat(data['updated_time']),
                    rotation_period_days=int(custom_metadata.get('rotation_period_days', 30)),
                    description=custom_metadata.get('description', ''),
                    tags=custom_metadata.get('tags', [])
                )

        except Exception as e:
            logger.error(f"Error getting secret metadata: {e}")
            raise

    def enable_audit_logging(self, path: str = "file",
                           options: Optional[Dict] = None) -> bool:
        """
        Enable audit logging for Vault operations

        Args:
            path: Audit device path
            options: Audit device options

        Returns:
            Success status
        """
        try:
            with self._ensure_authenticated() as client:
                client.sys.enable_audit_device(
                    device_type='file',
                    path=path,
                    options=options or {'file_path': '/var/log/vault/audit.log'}
                )
                logger.info(f"Audit logging enabled at {path}")
                return True

        except Exception as e:
            logger.error(f"Error enabling audit logging: {e}")
            return False

    def check_rotation_schedule(self) -> List[str]:
        """
        Check which secrets need rotation

        Returns:
            List of paths that need rotation
        """
        secrets_to_rotate = []

        for path in self.list_secrets():
            try:
                metadata = self.get_secret_metadata(path)

                if metadata.rotated_at:
                    days_since_rotation = (datetime.now() - metadata.rotated_at).days

                    if days_since_rotation >= metadata.rotation_period_days:
                        secrets_to_rotate.append(path)

            except Exception as e:
                logger.warning(f"Could not check rotation for {path}: {e}")

        return secrets_to_rotate

    def _schedule_rotation(self, path: str, days: int):
        """Schedule secret rotation"""
        rotation_time = datetime.now() + timedelta(days=days)
        self._rotation_schedule[path] = rotation_time
        logger.info(f"Scheduled rotation for {path} at {rotation_time}")

    def _invalidate_cache(self, path: str):
        """Invalidate cached secrets for a path"""
        keys_to_remove = [k for k in self._secret_cache if k.startswith(path)]
        for key in keys_to_remove:
            del self._secret_cache[key]

    def _generate_secret_value(self, path: str, current: Any) -> Any:
        """Generate new secret value based on type"""
        import secrets
        import string

        # Determine secret type and generate appropriate value
        if isinstance(current, str):
            # Generate random string of same length
            length = len(current) if current else 32
            chars = string.ascii_letters + string.digits + string.punctuation
            return ''.join(secrets.choice(chars) for _ in range(length))
        elif isinstance(current, dict):
            # Rotate each value in the dictionary
            return {k: self._generate_secret_value(f"{path}/{k}", v)
                   for k, v in current.items()}
        else:
            # Default to random hex string
            return secrets.token_hex(32)

    async def rotate_all_secrets(self) -> Dict[str, bool]:
        """
        Rotate all secrets that are due for rotation

        Returns:
            Dictionary of path: success status
        """
        results = {}
        secrets_to_rotate = self.check_rotation_schedule()

        for path in secrets_to_rotate:
            try:
                success = self.rotate_secret(path)
                results[path] = success
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to rotate {path}: {e}")
                results[path] = False

        return results


# Singleton instance
_vault_manager: Optional[VaultManager] = None


def get_vault_manager() -> VaultManager:
    """Get singleton Vault manager instance"""
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = VaultManager()
    return _vault_manager


# Convenience functions
def get_secret(path: str, key: Optional[str] = None) -> Any:
    """Get secret from Vault"""
    return get_vault_manager().get_secret(path, key)


def set_secret(path: str, data: Dict[str, Any]) -> bool:
    """Store secret in Vault"""
    return get_vault_manager().set_secret(path, data)


def rotate_secret(path: str) -> bool:
    """Rotate a secret"""
    return get_vault_manager().rotate_secret(path)