"""
BCrypt handler with 2025 best practices

Direct bcrypt implementation that avoids passlib compatibility issues
while following OWASP recommendations.
"""

import bcrypt
import hashlib
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BcryptHandler:
    """
    Modern bcrypt implementation for 2025

    Handles:
    - Password length > 72 bytes via SHA-256 pre-hashing
    - Null byte issues via base64 encoding
    - Timing attack protection
    - Salt generation
    """

    def __init__(self, rounds: int = 12, pepper: Optional[str] = None):
        """
        Initialize BCrypt handler

        Args:
            rounds: BCrypt cost factor (12 is recommended for 2025)
            pepper: Optional pepper for additional security
        """
        self.rounds = rounds
        self.pepper = pepper or ""

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with SHA-256 pre-hashing

        This follows OWASP 2025 recommendations to handle passwords
        of any length by pre-hashing with SHA-256.

        Args:
            password: Plain text password

        Returns:
            BCrypt hash string
        """
        # Add pepper if configured
        peppered = password + self.pepper

        # Pre-hash with SHA-256 to handle any length
        # This reduces the password to 32 bytes (256 bits)
        sha256_hash = hashlib.sha256(peppered.encode("utf-8")).digest()

        # Base64 encode to avoid null byte issues
        # SHA-256 produces 32 bytes, base64 encodes to 44 chars
        password_b64 = base64.b64encode(sha256_hash)

        # Generate salt and hash with bcrypt
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_b64, salt)

        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash

        Args:
            password: Plain text password to verify
            hashed: BCrypt hash to check against

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Add pepper if configured
            peppered = password + self.pepper

            # Apply same pre-hashing as in hash_password
            sha256_hash = hashlib.sha256(peppered.encode("utf-8")).digest()
            password_b64 = base64.b64encode(sha256_hash)

            # Verify with bcrypt (handles timing attacks)
            return bcrypt.checkpw(password_b64, hashed.encode("utf-8"))

        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False


# Global instance for convenience
default_handler = BcryptHandler()
