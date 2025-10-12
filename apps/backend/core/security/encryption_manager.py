"""
Encryption Manager for ToolboxAI
Handles encryption key management, rotation, and data re-encryption
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, MultiFernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages encryption keys with rotation support.

    Features:
    - Multi-key encryption for key rotation
    - Automatic re-encryption during rotation
    - Key versioning and expiry
    - Secure key storage recommendations
    """

    def __init__(self, primary_key: Optional[str] = None, rotation_keys: Optional[List[str]] = None):
        """
        Initialize encryption manager.

        Args:
            primary_key: Current primary encryption key (base64)
            rotation_keys: List of previous keys for decryption during rotation
        """
        self.primary_key = primary_key or os.getenv("DATA_ENCRYPTION_KEY")
        self.rotation_keys = rotation_keys or self._load_rotation_keys()

        if not self.primary_key:
            raise ValueError("Primary encryption key must be provided or set in DATA_ENCRYPTION_KEY")

        # Create Fernet instances
        self.primary_fernet = Fernet(self.primary_key.encode() if isinstance(self.primary_key, str) else self.primary_key)

        # Create MultiFernet with rotation keys for backward compatibility
        if self.rotation_keys:
            rotation_fernets = [Fernet(key.encode() if isinstance(key, str) else key) for key in self.rotation_keys]
            self.multi_fernet = MultiFernet([self.primary_fernet] + rotation_fernets)
        else:
            self.multi_fernet = MultiFernet([self.primary_fernet])

    def _load_rotation_keys(self) -> List[str]:
        """Load rotation keys from environment variables."""
        keys = []
        for i in range(1, 6):  # Support up to 5 rotation keys
            key = os.getenv(f"DATA_ENCRYPTION_KEY_OLD_{i}")
            if key:
                keys.append(key)
        return keys

    def encrypt(self, data: str) -> str:
        """
        Encrypt data using the primary key.

        Args:
            data: Plaintext string to encrypt

        Returns:
            Base64-encoded encrypted data
        """
        if not data:
            return data

        try:
            encrypted = self.primary_fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data, trying rotation keys if primary key fails.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails with all keys
        """
        if not encrypted_data:
            return encrypted_data

        try:
            decrypted = self.multi_fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed - invalid token or wrong key")
            raise ValueError("Failed to decrypt data - invalid encryption key")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def rotate_encryption(self, encrypted_data: str) -> str:
        """
        Re-encrypt data with the current primary key.

        Use this during key rotation to update old encrypted data.

        Args:
            encrypted_data: Data encrypted with old key

        Returns:
            Data re-encrypted with current primary key
        """
        # Decrypt with any available key
        plaintext = self.decrypt(encrypted_data)

        # Re-encrypt with primary key
        return self.encrypt(plaintext)

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key
        """
        key = Fernet.generate_key()
        return key.decode()

    def needs_rotation(self, encrypted_data: str) -> bool:
        """
        Check if encrypted data was encrypted with an old key.

        Args:
            encrypted_data: Encrypted data to check

        Returns:
            True if data should be re-encrypted with current key
        """
        try:
            # Try to decrypt with primary key only
            self.primary_fernet.decrypt(encrypted_data.encode())
            return False
        except InvalidToken:
            # If primary key fails but multi_fernet succeeds, needs rotation
            try:
                self.multi_fernet.decrypt(encrypted_data.encode())
                return True
            except InvalidToken:
                return False

    async def rotate_user_data(self, db_session, user_model):
        """
        Rotate encryption for all user sensitive data.

        Args:
            db_session: Database session
            user_model: User model class
        """
        from sqlalchemy import select

        logger.info("Starting user data encryption rotation")

        # Get all users with encrypted data
        stmt = select(user_model).where(user_model.mfa_secret.isnot(None))
        result = await db_session.execute(stmt)
        users = result.scalars().all()

        rotated_count = 0

        for user in users:
            try:
                if user.mfa_secret and self.needs_rotation(user.mfa_secret):
                    # Re-encrypt with current key
                    user.mfa_secret = self.rotate_encryption(user.mfa_secret)
                    rotated_count += 1
            except Exception as e:
                logger.error(f"Failed to rotate encryption for user {user.id}: {e}")
                continue

        # Commit changes
        await db_session.commit()

        logger.info(f"Encryption rotation complete: {rotated_count} users updated")

        return {
            "total_users": len(users),
            "rotated_count": rotated_count,
            "completed_at": datetime.utcnow().isoformat()
        }


class EncryptionKeyRotationSchedule:
    """Manages encryption key rotation schedule and policies."""

    def __init__(self, rotation_interval_days: int = 90):
        """
        Initialize rotation schedule.

        Args:
            rotation_interval_days: Days between key rotations (default: 90)
        """
        self.rotation_interval = timedelta(days=rotation_interval_days)
        self.last_rotation = self._get_last_rotation_date()

    def _get_last_rotation_date(self) -> datetime:
        """Get last rotation date from environment or database."""
        last_rotation_str = os.getenv("LAST_KEY_ROTATION")
        if last_rotation_str:
            return datetime.fromisoformat(last_rotation_str)
        return datetime.utcnow()

    def is_rotation_due(self) -> bool:
        """Check if key rotation is due."""
        next_rotation = self.last_rotation + self.rotation_interval
        return datetime.utcnow() >= next_rotation

    def days_until_rotation(self) -> int:
        """Get number of days until next rotation."""
        next_rotation = self.last_rotation + self.rotation_interval
        delta = next_rotation - datetime.utcnow()
        return max(0, delta.days)


# Singleton instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


# Export
__all__ = [
    "EncryptionManager",
    "EncryptionKeyRotationSchedule",
    "get_encryption_manager",
]
