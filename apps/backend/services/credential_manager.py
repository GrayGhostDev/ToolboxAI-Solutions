"""
Secure Credential Manager for Roblox API Integration
Manages encrypted credentials with audit logging and access control
"""

import asyncio
import logging
import os
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from typing import Any

from apps.backend.services.encryption import get_encryption_manager

logger = logging.getLogger(__name__)


class CredentialType(str, Enum):
    """Types of credentials managed by the system"""

    ROBLOX_API_KEY = "ROBLOX_API_KEY"
    ROBLOX_CLIENT_SECRET = "ROBLOX_CLIENT_SECRET"
    ROBLOX_CLIENT_ID = "ROBLOX_CLIENT_ID"
    ENCRYPTION_KEY = "ENCRYPTION_KEY"
    PUSHER_SECRET = "PUSHER_SECRET"


@dataclass
class CredentialAccess:
    """Record of credential access for audit logging"""

    credential_type: str
    accessed_at: datetime
    accessed_by: str | None
    ip_address: str | None
    user_agent: str | None
    success: bool
    error_message: str | None = None
    stack_trace: str | None = None


@dataclass
class CachedCredential:
    """Cached credential with TTL"""

    value: str
    cached_at: datetime
    ttl_seconds: int = 300  # 5 minutes default

    def is_expired(self) -> bool:
        """Check if cached credential has expired"""
        age = (datetime.now(timezone.utc) - self.cached_at).total_seconds()
        return age > self.ttl_seconds


class SecureCredentialManager:
    """
    Manages Roblox API credentials with enterprise-grade security
    Features: encryption, caching, audit logging, access control
    """

    def __init__(self, cache_ttl: int = 300, enable_audit: bool = True):
        """
        Initialize secure credential manager

        Args:
            cache_ttl: Cache time-to-live in seconds
            enable_audit: Enable audit logging
        """
        self.encryption_manager = get_encryption_manager()
        self.cipher = self.encryption_manager.get_current_cipher()
        self._credentials_cache: dict[str, CachedCredential] = {}
        self._cache_ttl = cache_ttl
        self._enable_audit = enable_audit
        self._access_log: list[CredentialAccess] = []
        self._access_lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None

    def _log_access(
        self,
        credential_type: str,
        success: bool = True,
        error_message: str | None = None,
        accessed_by: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Log credential access for audit trail

        Args:
            credential_type: Type of credential accessed
            success: Whether access was successful
            error_message: Error message if failed
            accessed_by: User/service accessing credential
            ip_address: IP address of accessor
            user_agent: User agent string
        """
        if not self._enable_audit:
            return

        access_record = CredentialAccess(
            credential_type=credential_type,
            accessed_at=datetime.now(timezone.utc),
            accessed_by=accessed_by or self._get_caller_info(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            stack_trace=traceback.format_exc() if error_message else None,
        )

        self._access_log.append(access_record)

        # Log to application logger
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"Credential access: {credential_type} by {access_record.accessed_by} - "
            f"{'SUCCESS' if success else 'FAILED'}",
        )

        # Persist to database (async if available)
        self._persist_audit_log(access_record)

    def _get_caller_info(self) -> str:
        """Get information about the calling function for audit"""
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller = frame.f_back.f_back
            return f"{caller.f_code.co_filename}:{caller.f_lineno}:{caller.f_code.co_name}"
        return "unknown"

    def _persist_audit_log(self, access_record: CredentialAccess) -> None:
        """
        Persist audit log to database (implement based on your DB)

        Args:
            access_record: Access record to persist
        """
        # TODO: Implement database persistence
        # This would typically write to credential_audit_log table
        pass

    def _get_from_cache(self, credential_type: str) -> str | None:
        """
        Get credential from cache if not expired

        Args:
            credential_type: Type of credential

        Returns:
            Cached credential value or None
        """
        if credential_type in self._credentials_cache:
            cached = self._credentials_cache[credential_type]
            if not cached.is_expired():
                logger.debug(f"Cache hit for {credential_type}")
                return cached.value
            else:
                logger.debug(f"Cache expired for {credential_type}")
                del self._credentials_cache[credential_type]
        return None

    def _cache_credential(self, credential_type: str, value: str) -> None:
        """
        Cache a credential with TTL

        Args:
            credential_type: Type of credential
            value: Credential value
        """
        self._credentials_cache[credential_type] = CachedCredential(
            value=value, cached_at=datetime.now(timezone.utc), ttl_seconds=self._cache_ttl
        )
        logger.debug(f"Cached {credential_type} for {self._cache_ttl} seconds")

    def _get_encrypted_from_env(self, env_var: str) -> str | None:
        """
        Get encrypted credential from environment variable

        Args:
            env_var: Environment variable name

        Returns:
            Encrypted credential or None
        """
        return os.getenv(env_var)

    @lru_cache(maxsize=1)
    def get_roblox_api_key(
        self, accessed_by: str | None = None, ip_address: str | None = None
    ) -> str | None:
        """
        Get decrypted Roblox API key with security checks

        Args:
            accessed_by: User/service accessing the key
            ip_address: IP address of accessor

        Returns:
            Decrypted API key or None if not found/failed
        """
        credential_type = CredentialType.ROBLOX_API_KEY.value

        try:
            # Check cache first
            cached_value = self._get_from_cache(credential_type)
            if cached_value:
                self._log_access(
                    credential_type, True, accessed_by=accessed_by, ip_address=ip_address
                )
                return cached_value

            # Get encrypted value from environment
            encrypted = self._get_encrypted_from_env("ROBLOX_API_KEY_ENCRYPTED")
            if not encrypted:
                # Try plain text as fallback (log security warning)
                plain = os.getenv("ROBLOX_API_KEY")
                if plain:
                    logger.warning("⚠️  Using unencrypted ROBLOX_API_KEY - encrypt in production!")
                    self._cache_credential(credential_type, plain)
                    self._log_access(
                        credential_type, True, accessed_by=accessed_by, ip_address=ip_address
                    )
                    return plain

                error_msg = "ROBLOX_API_KEY_ENCRYPTED not found in environment"
                self._log_access(credential_type, False, error_msg, accessed_by, ip_address)
                logger.error(error_msg)
                return None

            # Decrypt the credential
            decrypted = self.cipher.decrypt_credential(encrypted)

            # Cache the decrypted value
            self._cache_credential(credential_type, decrypted)

            # Log successful access
            self._log_access(credential_type, True, accessed_by=accessed_by, ip_address=ip_address)

            return decrypted

        except Exception as e:
            error_msg = f"Failed to get Roblox API key: {str(e)}"
            self._log_access(credential_type, False, error_msg, accessed_by, ip_address)
            logger.error(error_msg)
            return None

    @lru_cache(maxsize=1)
    def get_roblox_client_secret(
        self, accessed_by: str | None = None, ip_address: str | None = None
    ) -> str | None:
        """
        Get decrypted Roblox client secret with security checks

        Args:
            accessed_by: User/service accessing the secret
            ip_address: IP address of accessor

        Returns:
            Decrypted client secret or None if not found/failed
        """
        credential_type = CredentialType.ROBLOX_CLIENT_SECRET.value

        try:
            # Check cache first
            cached_value = self._get_from_cache(credential_type)
            if cached_value:
                self._log_access(
                    credential_type, True, accessed_by=accessed_by, ip_address=ip_address
                )
                return cached_value

            # Get encrypted value from environment
            encrypted = self._get_encrypted_from_env("ROBLOX_CLIENT_SECRET_ENCRYPTED")
            if not encrypted:
                # Try plain text as fallback (log security warning)
                plain = os.getenv("ROBLOX_CLIENT_SECRET")
                if plain:
                    logger.warning(
                        "⚠️  Using unencrypted ROBLOX_CLIENT_SECRET - encrypt in production!"
                    )
                    self._cache_credential(credential_type, plain)
                    self._log_access(
                        credential_type, True, accessed_by=accessed_by, ip_address=ip_address
                    )
                    return plain

                error_msg = "ROBLOX_CLIENT_SECRET_ENCRYPTED not found in environment"
                self._log_access(credential_type, False, error_msg, accessed_by, ip_address)
                logger.error(error_msg)
                return None

            # Decrypt the credential
            decrypted = self.cipher.decrypt_credential(encrypted)

            # Cache the decrypted value
            self._cache_credential(credential_type, decrypted)

            # Log successful access
            self._log_access(credential_type, True, accessed_by=accessed_by, ip_address=ip_address)

            return decrypted

        except Exception as e:
            error_msg = f"Failed to get Roblox client secret: {str(e)}"
            self._log_access(credential_type, False, error_msg, accessed_by, ip_address)
            logger.error(error_msg)
            return None

    def get_roblox_client_id(self) -> str:
        """
        Get Roblox client ID (public, not encrypted)

        Returns:
            Client ID
        """
        return os.getenv("ROBLOX_CLIENT_ID", "2214511122270781418")

    def get_roblox_universe_id(self) -> str:
        """
        Get Roblox universe ID (public, not encrypted)

        Returns:
            Universe ID
        """
        return os.getenv("ROBLOX_UNIVERSE_ID", "8505376973")

    def clear_cache(self) -> None:
        """Clear all cached credentials"""
        self._credentials_cache.clear()
        logger.info("Cleared credential cache")

    def rotate_credentials(self, credential_type: CredentialType, new_value: str) -> bool:
        """
        Rotate a credential (update with new value)

        Args:
            credential_type: Type of credential to rotate
            new_value: New credential value

        Returns:
            Success status
        """
        try:
            # Encrypt new value
            encrypted, _ = self.cipher.encrypt_credential(new_value)

            # Update environment variable (in memory only)
            os.environ[f"{credential_type.value}_ENCRYPTED"] = encrypted

            # Clear cache to force re-fetch
            if credential_type.value in self._credentials_cache:
                del self._credentials_cache[credential_type.value]

            # Clear LRU cache
            if credential_type == CredentialType.ROBLOX_API_KEY:
                self.get_roblox_api_key.cache_clear()
            elif credential_type == CredentialType.ROBLOX_CLIENT_SECRET:
                self.get_roblox_client_secret.cache_clear()

            logger.info(f"Rotated credential: {credential_type.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to rotate credential {credential_type.value}: {e}")
            return False

    def get_audit_log(
        self, credential_type: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get audit log entries

        Args:
            credential_type: Filter by credential type
            limit: Maximum entries to return

        Returns:
            List of audit log entries
        """
        logs = self._access_log
        if credential_type:
            logs = [l for l in logs if l.credential_type == credential_type]

        # Sort by timestamp descending
        logs.sort(key=lambda x: x.accessed_at, reverse=True)

        # Convert to dict and limit
        return [asdict(log) for log in logs[:limit]]

    def check_suspicious_activity(self) -> list[str]:
        """
        Check for suspicious credential access patterns

        Returns:
            List of warnings
        """
        warnings = []

        # Check for repeated failed attempts
        recent_failures = [
            log
            for log in self._access_log
            if not log.success
            and (datetime.now(timezone.utc) - log.accessed_at).total_seconds() < 300
        ]
        if len(recent_failures) > 5:
            warnings.append(
                f"Multiple failed credential access attempts: {len(recent_failures)} in last 5 minutes"
            )

        # Check for unusual access frequency
        recent_accesses = [
            log
            for log in self._access_log
            if (datetime.now(timezone.utc) - log.accessed_at).total_seconds() < 60
        ]
        if len(recent_accesses) > 10:
            warnings.append(
                f"High credential access frequency: {len(recent_accesses)} in last minute"
            )

        return warnings


# Singleton instance
_credential_manager = None


def get_credential_manager() -> SecureCredentialManager:
    """Get singleton credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SecureCredentialManager(
            cache_ttl=int(os.getenv("CREDENTIAL_CACHE_TTL", "300")),
            enable_audit=os.getenv("ENABLE_CREDENTIAL_AUDIT", "true").lower() == "true",
        )
    return _credential_manager
