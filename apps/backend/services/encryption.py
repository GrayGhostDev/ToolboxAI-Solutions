"""
Secure Encryption Service for Credential Management
Provides AES-256 encryption via Fernet for storing sensitive API credentials
"""

import base64
import hashlib
import logging
import os
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """
    Secure credential encryption service using Fernet (AES-256)
    Implements key derivation, rotation, and secure storage patterns
    """

    def __init__(self, key: str | None = None):
        """
        Initialize encryption service with optional key

        Args:
            key: Base64 encoded encryption key (generates new if None)
        """
        self.key = self._get_or_create_key(key)
        self.cipher = Fernet(self.key)
        self._initialized_at = datetime.now(timezone.utc)

    def _get_or_create_key(self, provided_key: str | None = None) -> bytes:
        """
        Get encryption key from environment, parameter, or generate new

        Args:
            provided_key: Optional base64 encoded key

        Returns:
            bytes: Encryption key for Fernet
        """
        # Priority: provided_key > env var > generate new
        if provided_key:
            try:
                return base64.urlsafe_b64decode(provided_key)
            except Exception as e:
                logger.error(f"Invalid provided key format: {e}")
                raise ValueError("Invalid encryption key format")

        # Try environment variable
        env_key = os.getenv("ENCRYPTION_KEY")
        if env_key:
            try:
                # Validate key format
                Fernet(env_key.encode() if len(env_key) == 44 else env_key)
                return (
                    env_key.encode()
                    if isinstance(env_key, str) and len(env_key) == 44
                    else env_key.encode()
                )
            except Exception:
                # Key might need to be derived
                return self._derive_key_from_password(env_key)

        # Generate new key
        new_key = Fernet.generate_key()
        logger.warning(
            f"Generated new encryption key. Save this securely:\n"
            f"ENCRYPTION_KEY={new_key.decode()}"
        )
        return new_key

    def _derive_key_from_password(self, password: str, salt: bytes | None = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: Password to derive key from
            salt: Optional salt (generates if None)

        Returns:
            bytes: Derived encryption key
        """
        if salt is None:
            # Use deterministic salt based on password for consistency
            # In production, use random salt and store it
            salt = hashlib.sha256(f"toolboxai_salt_{password[:10]}".encode()).digest()[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_credential(self, credential: str) -> tuple[str, str]:
        """
        Encrypt a credential and return encrypted value with metadata

        Args:
            credential: Plain text credential to encrypt

        Returns:
            Tuple[str, str]: (encrypted_credential, credential_hash)
        """
        if not credential:
            raise ValueError("Cannot encrypt empty credential")

        # Encrypt the credential
        encrypted = self.cipher.encrypt(credential.encode())

        # Create hash for lookups without decryption
        credential_hash = hashlib.sha256(credential.encode()).hexdigest()

        # Return base64 encoded for storage
        return base64.urlsafe_b64encode(encrypted).decode(), credential_hash

    def decrypt_credential(self, encrypted: str) -> str:
        """
        Decrypt an encrypted credential

        Args:
            encrypted: Base64 encoded encrypted credential

        Returns:
            str: Decrypted plain text credential
        """
        if not encrypted:
            raise ValueError("Cannot decrypt empty value")

        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted)

            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_bytes)

            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {e}")
            raise ValueError("Failed to decrypt credential - invalid key or corrupted data")

    def rotate_key(self, new_key: str | None = None) -> "CredentialEncryption":
        """
        Create new encryption instance with rotated key

        Args:
            new_key: Optional new key (generates if None)

        Returns:
            CredentialEncryption: New instance with rotated key
        """
        return CredentialEncryption(new_key)

    def re_encrypt(self, encrypted: str, new_cipher: "CredentialEncryption") -> str:
        """
        Re-encrypt a credential with a new key (for key rotation)

        Args:
            encrypted: Currently encrypted credential
            new_cipher: New encryption instance with rotated key

        Returns:
            str: Re-encrypted credential with new key
        """
        # Decrypt with current key
        plain = self.decrypt_credential(encrypted)

        # Encrypt with new key
        new_encrypted, _ = new_cipher.encrypt_credential(plain)

        return new_encrypted

    def validate_key(self) -> bool:
        """
        Validate that the encryption key works correctly

        Returns:
            bool: True if key is valid
        """
        try:
            test_data = "test_validation_string"
            encrypted, _ = self.encrypt_credential(test_data)
            decrypted = self.decrypt_credential(encrypted)
            return decrypted == test_data
        except Exception:
            return False

    def get_key_info(self) -> dict:
        """
        Get information about the current encryption key (for monitoring)

        Returns:
            dict: Key metadata (no sensitive data)
        """
        return {
            "initialized_at": self._initialized_at.isoformat(),
            "key_valid": self.validate_key(),
            "key_fingerprint": hashlib.sha256(self.key).hexdigest()[:8],  # First 8 chars only
        }


class EncryptionKeyManager:
    """
    Manages encryption keys with rotation and versioning support
    """

    def __init__(self):
        self.current_version = 1
        self.keys = {}
        self._load_keys()

    def _load_keys(self):
        """Load encryption keys from environment or configuration"""
        # Current key
        current_key = os.getenv("ENCRYPTION_KEY")
        if current_key:
            self.keys[self.current_version] = CredentialEncryption(current_key)

        # Previous keys for backward compatibility during rotation
        for i in range(1, 4):  # Support up to 3 previous keys
            old_key = os.getenv(f"ENCRYPTION_KEY_V{i}")
            if old_key:
                self.keys[i] = CredentialEncryption(old_key)

    def get_current_cipher(self) -> CredentialEncryption:
        """Get the current encryption cipher"""
        if self.current_version not in self.keys:
            self.keys[self.current_version] = CredentialEncryption()
        return self.keys[self.current_version]

    def get_cipher_by_version(self, version: int) -> CredentialEncryption | None:
        """Get encryption cipher by version"""
        return self.keys.get(version)

    def rotate_keys(self, new_key: str | None = None) -> int:
        """
        Rotate encryption keys

        Args:
            new_key: Optional new key (generates if None)

        Returns:
            int: New version number
        """
        # Move current to old
        if self.current_version in self.keys:
            self.keys[self.current_version - 1] = self.keys[self.current_version]

        # Set new current
        self.current_version += 1
        self.keys[self.current_version] = CredentialEncryption(new_key)

        logger.info(f"Rotated encryption keys to version {self.current_version}")
        return self.current_version


# Singleton instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionKeyManager:
    """Get singleton encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionKeyManager()
    return _encryption_manager
