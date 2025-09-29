"""
PII Encryption Manager
Implements field-level encryption for personally identifiable information
Using AES-256-GCM with key management via Vault
"""

import base64
import json
import logging
from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import os

logger = logging.getLogger(__name__)


class PIIField(str, Enum):
    """Types of PII fields that require encryption"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    FULL_NAME = "full_name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    MEDICAL_RECORD = "medical_record"
    IP_ADDRESS = "ip_address"
    BIOMETRIC = "biometric"
    CUSTOM = "custom"


@dataclass
class EncryptedField:
    """Container for encrypted field data"""
    ciphertext: str  # Base64 encoded encrypted data
    nonce: str  # Base64 encoded nonce/IV
    tag: str  # Base64 encoded authentication tag
    field_type: PIIField
    key_version: int
    encrypted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    algorithm: str = "AES-256-GCM"


class PIIEncryptionManager:
    """
    Manages encryption/decryption of PII data

    Features:
    - AES-256-GCM encryption for authenticated encryption
    - Field-level encryption for granular control
    - Key rotation support via Vault
    - Format-preserving encryption for certain fields
    - Audit logging for compliance
    - Search capability on encrypted data using blind indexing
    """

    def __init__(self, vault_enabled: bool = True):
        """
        Initialize PII Encryption Manager

        Args:
            vault_enabled: Whether to use Vault for key management
        """
        self.vault_enabled = vault_enabled
        self.algorithm = "AES-256-GCM"
        self.key_size = 32  # 256 bits
        self.nonce_size = 12  # 96 bits for GCM
        self.tag_size = 16  # 128 bits

        # Initialize encryption keys
        self._init_keys()

        # Field-specific configurations
        self.field_configs = {
            PIIField.EMAIL: {"searchable": True, "format_preserving": False},
            PIIField.PHONE: {"searchable": True, "format_preserving": True},
            PIIField.SSN: {"searchable": False, "format_preserving": True},
            PIIField.CREDIT_CARD: {"searchable": False, "format_preserving": True},
            PIIField.FULL_NAME: {"searchable": True, "format_preserving": False},
            PIIField.DATE_OF_BIRTH: {"searchable": False, "format_preserving": False},
        }

    def _init_keys(self):
        """Initialize or retrieve encryption keys"""
        if self.vault_enabled:
            try:
                from apps.backend.services.vault_manager import get_vault_manager
                self.vault = get_vault_manager()

                # Get or create data encryption key
                dek_data = self.vault.get_secret("apps/backend/encryption/data_key")
                if dek_data:
                    self.data_key = base64.b64decode(dek_data["key"])
                    self.key_version = dek_data.get("version", 1)
                else:
                    self._generate_new_key()
            except Exception as e:
                logger.warning(f"Vault unavailable, using local key: {e}")
                self._use_local_key()
        else:
            self._use_local_key()

    def _generate_new_key(self):
        """Generate new data encryption key"""
        # Generate random 256-bit key
        self.data_key = os.urandom(self.key_size)
        self.key_version = 1

        if self.vault_enabled and hasattr(self, 'vault'):
            try:
                # Store in Vault
                self.vault.set_secret("apps/backend/encryption/data_key", {
                    "key": base64.b64encode(self.data_key).decode('utf-8'),
                    "version": self.key_version,
                    "algorithm": self.algorithm,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                logger.info("Generated and stored new data encryption key")
            except Exception as e:
                logger.error(f"Failed to store key in Vault: {e}")

    def _use_local_key(self):
        """Use local key when Vault is unavailable"""
        # Derive key from environment variable or use default (not for production!)
        key_seed = os.getenv("PII_ENCRYPTION_KEY", "CHANGE_THIS_IN_PRODUCTION")

        # Use PBKDF2 to derive a proper key from seed
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=b"toolboxai_pii_salt",  # Should be random in production
            iterations=100000,
            backend=default_backend()
        )
        self.data_key = kdf.derive(key_seed.encode())
        self.key_version = 0  # Local key version

    def encrypt_field(
        self,
        value: Any,
        field_type: PIIField,
        additional_data: Optional[bytes] = None
    ) -> EncryptedField:
        """
        Encrypt a PII field

        Args:
            value: Value to encrypt
            field_type: Type of PII field
            additional_data: Additional authenticated data (AAD)

        Returns:
            EncryptedField object containing encrypted data
        """
        if value is None:
            return None

        try:
            # Convert value to bytes
            if isinstance(value, str):
                plaintext = value.encode('utf-8')
            elif isinstance(value, (int, float)):
                plaintext = str(value).encode('utf-8')
            elif isinstance(value, dict):
                plaintext = json.dumps(value).encode('utf-8')
            else:
                plaintext = bytes(value)

            # Check if format-preserving encryption is needed
            if self.field_configs.get(field_type, {}).get("format_preserving"):
                return self._format_preserving_encrypt(value, field_type)

            # Generate nonce
            nonce = os.urandom(self.nonce_size)

            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.data_key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Add additional authenticated data if provided
            if additional_data:
                encryptor.authenticate_additional_data(additional_data)

            # Encrypt
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()

            # Create encrypted field
            encrypted = EncryptedField(
                ciphertext=base64.b64encode(ciphertext).decode('utf-8'),
                nonce=base64.b64encode(nonce).decode('utf-8'),
                tag=base64.b64encode(encryptor.tag).decode('utf-8'),
                field_type=field_type,
                key_version=self.key_version
            )

            # Create searchable index if needed
            if self.field_configs.get(field_type, {}).get("searchable"):
                self._create_blind_index(value, field_type)

            # Audit log
            self._audit_encryption(field_type, "encrypt")

            return encrypted

        except Exception as e:
            logger.error(f"Encryption failed for {field_type}: {e}")
            raise

    def decrypt_field(
        self,
        encrypted: EncryptedField,
        additional_data: Optional[bytes] = None
    ) -> Any:
        """
        Decrypt a PII field

        Args:
            encrypted: EncryptedField object
            additional_data: Additional authenticated data (AAD)

        Returns:
            Decrypted value
        """
        if encrypted is None:
            return None

        try:
            # Check if format-preserving encryption was used
            if self.field_configs.get(encrypted.field_type, {}).get("format_preserving"):
                return self._format_preserving_decrypt(encrypted)

            # Decode from base64
            ciphertext = base64.b64decode(encrypted.ciphertext)
            nonce = base64.b64decode(encrypted.nonce)
            tag = base64.b64decode(encrypted.tag)

            # Get the appropriate key version
            key = self._get_key_for_version(encrypted.key_version)

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Add additional authenticated data if provided
            if additional_data:
                decryptor.authenticate_additional_data(additional_data)

            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Audit log
            self._audit_encryption(encrypted.field_type, "decrypt")

            # Convert back to original type
            try:
                return plaintext.decode('utf-8')
            except:
                return plaintext

        except Exception as e:
            logger.error(f"Decryption failed for {encrypted.field_type}: {e}")
            raise

    def encrypt_document(
        self,
        document: Dict[str, Any],
        field_mappings: Dict[str, PIIField]
    ) -> Dict[str, Any]:
        """
        Encrypt multiple fields in a document

        Args:
            document: Document containing PII fields
            field_mappings: Mapping of field names to PII types

        Returns:
            Document with encrypted fields
        """
        encrypted_doc = document.copy()

        for field_name, field_type in field_mappings.items():
            if field_name in document and document[field_name] is not None:
                encrypted_field = self.encrypt_field(
                    document[field_name],
                    field_type
                )
                # Store as dict for serialization
                encrypted_doc[field_name] = self._serialize_encrypted_field(encrypted_field)

        return encrypted_doc

    def decrypt_document(
        self,
        encrypted_doc: Dict[str, Any],
        field_mappings: Dict[str, PIIField]
    ) -> Dict[str, Any]:
        """
        Decrypt multiple fields in a document

        Args:
            encrypted_doc: Document with encrypted fields
            field_mappings: Mapping of field names to PII types

        Returns:
            Document with decrypted fields
        """
        decrypted_doc = encrypted_doc.copy()

        for field_name, field_type in field_mappings.items():
            if field_name in encrypted_doc and encrypted_doc[field_name] is not None:
                encrypted_field = self._deserialize_encrypted_field(
                    encrypted_doc[field_name]
                )
                decrypted_doc[field_name] = self.decrypt_field(encrypted_field)

        return decrypted_doc

    def _format_preserving_encrypt(self, value: str, field_type: PIIField) -> EncryptedField:
        """
        Format-preserving encryption for fields like SSN, phone numbers

        Args:
            value: Value to encrypt
            field_type: Type of field

        Returns:
            EncryptedField with format preserved
        """
        # This is a simplified implementation
        # In production, use FF3-1 algorithm or similar

        if field_type == PIIField.PHONE:
            # Keep format like (XXX) XXX-XXXX
            # Encrypt only the digits
            digits = ''.join(c for c in value if c.isdigit())
            encrypted_digits = self._simple_format_preserve(digits)

            # Reconstruct with original format
            result = value
            digit_index = 0
            for i, char in enumerate(value):
                if char.isdigit() and digit_index < len(encrypted_digits):
                    result = result[:i] + encrypted_digits[digit_index] + result[i+1:]
                    digit_index += 1

            return EncryptedField(
                ciphertext=result,
                nonce="",  # Not used in FPE
                tag="",  # Not used in FPE
                field_type=field_type,
                key_version=self.key_version
            )

        elif field_type == PIIField.SSN:
            # Keep format like XXX-XX-XXXX
            # Only encrypt, maintain dashes
            parts = value.split('-')
            encrypted_parts = [self._simple_format_preserve(part) for part in parts]
            result = '-'.join(encrypted_parts)

            return EncryptedField(
                ciphertext=result,
                nonce="",
                tag="",
                field_type=field_type,
                key_version=self.key_version
            )

        # Default: regular encryption
        return self.encrypt_field(value, field_type)

    def _simple_format_preserve(self, digits: str) -> str:
        """Simple format-preserving transformation for digits"""
        # This is a simplified version - use proper FPE in production
        import hashlib

        # Create deterministic mapping
        h = hashlib.sha256(self.data_key + digits.encode()).digest()

        result = ""
        for i, char in enumerate(digits):
            if char.isdigit():
                # Map to another digit deterministically
                mapped = str((int(char) + h[i % len(h)]) % 10)
                result += mapped
            else:
                result += char

        return result

    def _format_preserving_decrypt(self, encrypted: EncryptedField) -> str:
        """Decrypt format-preserved encryption"""
        # In this simplified version, we'd need to store mapping
        # In production, use proper FF3-1 decryption
        return encrypted.ciphertext  # Placeholder

    def _create_blind_index(self, value: Any, field_type: PIIField):
        """
        Create blind index for searching encrypted data

        Args:
            value: Original value
            field_type: Type of field
        """
        import hashlib

        # Create HMAC-based blind index
        index_key = hashlib.sha256(
            self.data_key + b"_index_" + field_type.value.encode()
        ).digest()

        # Create index
        h = hashlib.sha256()
        h.update(index_key)
        h.update(str(value).encode('utf-8'))
        blind_index = h.hexdigest()

        # Store index (in production, store in database)
        # This allows searching without decryption
        logger.debug(f"Created blind index for {field_type}: {blind_index[:8]}...")

    def search_encrypted(
        self,
        search_value: Any,
        field_type: PIIField
    ) -> str:
        """
        Generate blind index for searching encrypted data

        Args:
            search_value: Value to search for
            field_type: Type of field

        Returns:
            Blind index hash for searching
        """
        import hashlib

        if not self.field_configs.get(field_type, {}).get("searchable"):
            raise ValueError(f"Field type {field_type} is not searchable")

        # Generate same blind index
        index_key = hashlib.sha256(
            self.data_key + b"_index_" + field_type.value.encode()
        ).digest()

        h = hashlib.sha256()
        h.update(index_key)
        h.update(str(search_value).encode('utf-8'))

        return h.hexdigest()

    def rotate_encryption_key(self) -> bool:
        """
        Rotate the data encryption key

        Returns:
            Success status
        """
        try:
            # Generate new key
            old_key = self.data_key
            old_version = self.key_version

            self._generate_new_key()
            self.key_version += 1

            # Store old key for decryption of existing data
            if self.vault_enabled and hasattr(self, 'vault'):
                self.vault.set_secret(f"apps/backend/encryption/data_key_v{old_version}", {
                    "key": base64.b64encode(old_key).decode('utf-8'),
                    "version": old_version,
                    "retired_at": datetime.now(timezone.utc).isoformat()
                })

            logger.info(f"Encryption key rotated to version {self.key_version}")
            return True

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False

    def _get_key_for_version(self, version: int) -> bytes:
        """
        Get encryption key for specific version

        Args:
            version: Key version

        Returns:
            Encryption key
        """
        if version == self.key_version:
            return self.data_key

        # Retrieve old key from Vault
        if self.vault_enabled and hasattr(self, 'vault'):
            try:
                old_key_data = self.vault.get_secret(f"apps/backend/encryption/data_key_v{version}")
                if old_key_data:
                    return base64.b64decode(old_key_data["key"])
            except Exception as e:
                logger.error(f"Failed to retrieve key version {version}: {e}")

        raise ValueError(f"Encryption key version {version} not found")

    def _serialize_encrypted_field(self, field: EncryptedField) -> Dict:
        """Serialize EncryptedField for storage"""
        return {
            "ciphertext": field.ciphertext,
            "nonce": field.nonce,
            "tag": field.tag,
            "field_type": field.field_type.value,
            "key_version": field.key_version,
            "encrypted_at": field.encrypted_at.isoformat(),
            "algorithm": field.algorithm
        }

    def _deserialize_encrypted_field(self, data: Dict) -> EncryptedField:
        """Deserialize EncryptedField from storage"""
        return EncryptedField(
            ciphertext=data["ciphertext"],
            nonce=data["nonce"],
            tag=data["tag"],
            field_type=PIIField(data["field_type"]),
            key_version=data["key_version"],
            encrypted_at=datetime.fromisoformat(data["encrypted_at"]),
            algorithm=data.get("algorithm", "AES-256-GCM")
        )

    def _audit_encryption(self, field_type: PIIField, operation: str):
        """
        Audit encryption/decryption operations

        Args:
            field_type: Type of field
            operation: Operation performed
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "field_type": field_type.value,
            "key_version": self.key_version
        }

        logger.debug(f"PII encryption audit: {json.dumps(audit_entry)}")

        # In production, store in audit database


# Singleton instance
_pii_manager: Optional[PIIEncryptionManager] = None


def get_pii_manager() -> PIIEncryptionManager:
    """Get singleton PII encryption manager"""
    global _pii_manager
    if _pii_manager is None:
        vault_enabled = os.getenv("VAULT_ENABLED", "false").lower() in ("true", "1", "yes")
        _pii_manager = PIIEncryptionManager(vault_enabled=vault_enabled)
    return _pii_manager


# Convenience functions
def encrypt_pii(value: Any, field_type: str) -> Dict:
    """Encrypt PII value"""
    manager = get_pii_manager()
    encrypted = manager.encrypt_field(value, PIIField(field_type))
    return manager._serialize_encrypted_field(encrypted)


def decrypt_pii(encrypted_data: Dict) -> Any:
    """Decrypt PII value"""
    manager = get_pii_manager()
    encrypted = manager._deserialize_encrypted_field(encrypted_data)
    return manager.decrypt_field(encrypted)