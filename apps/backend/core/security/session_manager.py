"""
Session Management Module for ToolboxAI

Implements secure session management with Redis backend,
session invalidation on password change, and session tracking.

Security features:
- Session invalidation on password change
- Multi-device session tracking
- Session timeout management
- Secure session token generation
- Session activity monitoring

References:
- OWASP Session Management: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- Redis Security: https://redis.io/docs/management/security/
"""

import hashlib
import json
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum

import redis
from redis.client import Pipeline

logger = logging.getLogger(__name__)


class SessionEvent(Enum):
    """Session lifecycle events for audit logging"""

    CREATED = "session_created"
    REFRESHED = "session_refreshed"
    INVALIDATED = "session_invalidated"
    EXPIRED = "session_expired"
    PASSWORD_CHANGED = "password_changed"
    LOGOUT = "logout"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class SessionInfo:
    """Session information structure"""

    session_id: str
    user_id: str
    username: str
    role: str
    created_at: float
    last_activity: float
    expires_at: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    is_active: bool = True
    refresh_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionInfo":
        """Create from dictionary retrieved from Redis"""
        return cls(**data)


class SessionManager:
    """
    Centralized session management with Redis backend.
    Handles session creation, validation, invalidation, and tracking.
    """

    # Configuration constants (following OWASP recommendations)
    SESSION_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"
    SESSION_VERSION_PREFIX = "session_version:"
    SESSION_EVENTS_PREFIX = "session_events:"
    SESSION_FINGERPRINT_PREFIX = "session_fp:"

    # OWASP-recommended timeouts (in seconds)
    DEFAULT_SESSION_TIMEOUT = 1800  # 30 minutes (OWASP: shorter for sensitive apps)
    DEFAULT_ABSOLUTE_TIMEOUT = 43200  # 12 hours absolute maximum
    DEFAULT_REFRESH_TIMEOUT = 86400  # 24 hours for refresh token
    DEFAULT_IDLE_TIMEOUT = 900  # 15 minutes idle timeout
    MAX_SESSIONS_PER_USER = 5  # Maximum concurrent sessions

    # Session ID configuration (OWASP: 128 bits of entropy minimum)
    SESSION_ID_LENGTH = 32  # 256 bits / 8 = 32 bytes
    SESSION_ID_CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        session_timeout: int = DEFAULT_SESSION_TIMEOUT,
        refresh_timeout: int = DEFAULT_REFRESH_TIMEOUT,
        max_sessions_per_user: int = MAX_SESSIONS_PER_USER,
    ):
        """
        Initialize session manager.

        Args:
            redis_client: Redis client instance
            session_timeout: Session timeout in seconds
            refresh_timeout: Refresh token timeout in seconds
            max_sessions_per_user: Maximum concurrent sessions per user
        """
        self.redis_client = redis_client
        self.session_timeout = session_timeout
        self.refresh_timeout = refresh_timeout
        self.max_sessions_per_user = max_sessions_per_user

        # In-memory fallback for development (NOT for production)
        self._memory_sessions: Dict[str, SessionInfo] = {}
        self._memory_user_sessions: Dict[str, Set[str]] = {}
        self._memory_session_versions: Dict[str, int] = {}
        self._memory_session_fingerprints: Dict[str, str] = {}

        # OWASP: Track absolute session creation time for maximum lifetime
        self._session_absolute_timeout: Dict[str, float] = {}

        if not self.redis_client:
            logger.warning("No Redis client provided. Using in-memory storage (NOT for production)")

    def generate_session_token(self) -> str:
        """
        Generate a cryptographically secure session token.
        OWASP: Use cryptographically secure random number generator
        with at least 128 bits of entropy (we use 256 bits).
        """
        # Use secrets module for cryptographically strong randomness
        # OWASP recommends at least 128 bits; we use 256 bits (32 bytes)
        return secrets.token_urlsafe(self.SESSION_ID_LENGTH)

    def generate_session_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """
        Generate session fingerprint for additional validation.
        OWASP: Bind session to client characteristics to prevent hijacking.
        """
        # Create fingerprint from stable client characteristics
        fingerprint_data = f"{ip_address}:{user_agent}".encode()
        return hashlib.sha256(fingerprint_data).hexdigest()

    def validate_session_fingerprint(
        self, session_id: str, ip_address: str, user_agent: str
    ) -> bool:
        """
        Validate session fingerprint to detect potential hijacking.
        OWASP: Additional layer of session validation.
        """
        expected_fingerprint = self.generate_session_fingerprint(ip_address, user_agent)

        if self.redis_client:
            key = f"{self.SESSION_FINGERPRINT_PREFIX}{session_id}"
            stored_fingerprint = self.redis_client.get(key)
            return stored_fingerprint == expected_fingerprint
        else:
            # Check in-memory storage
            return self._memory_session_fingerprints.get(session_id) == expected_fingerprint

    def create_session(
        self,
        user_id: str,
        username: str,
        role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> SessionInfo:
        """
        Create a new session for a user.

        Args:
            user_id: User identifier
            username: Username
            role: User role
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Device identifier

        Returns:
            SessionInfo object with session details
        """
        # Generate unique session ID and refresh token
        session_id = self.generate_session_token()
        refresh_token = self.generate_session_token()

        # Calculate expiration times
        now = time.time()
        expires_at = now + self.session_timeout

        # Create session info
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            username=username,
            role=role,
            created_at=now,
            last_activity=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            is_active=True,
            refresh_token=refresh_token,
        )

        # Store session
        if self.redis_client:
            self._store_session_redis(session)
        else:
            self._store_session_memory(session)

        # Log session creation event
        self._log_session_event(
            user_id=user_id,
            session_id=session_id,
            event=SessionEvent.CREATED,
            ip_address=ip_address,
        )

        # Enforce session limits
        self._enforce_session_limit(user_id)

        logger.info(f"Session created for user {username} (ID: {user_id})")
        return session

    def _store_session_redis(self, session: SessionInfo) -> None:
        """Store session in Redis with atomic operations"""
        pipe: Pipeline = self.redis_client.pipeline()

        # Store session data
        session_key = f"{self.SESSION_PREFIX}{session.session_id}"
        pipe.hset(session_key, mapping=session.to_dict())
        pipe.expire(session_key, self.session_timeout)

        # Add to user's session set
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{session.user_id}"
        pipe.sadd(user_sessions_key, session.session_id)
        pipe.expire(user_sessions_key, self.refresh_timeout)

        # Initialize session version (for invalidation tracking)
        version_key = f"{self.SESSION_VERSION_PREFIX}{session.user_id}"
        pipe.hsetnx(version_key, "version", 1)
        pipe.hsetnx(version_key, "last_password_change", time.time())

        pipe.execute()

    def _store_session_memory(self, session: SessionInfo) -> None:
        """Store session in memory (development only)"""
        self._memory_sessions[session.session_id] = session

        if session.user_id not in self._memory_user_sessions:
            self._memory_user_sessions[session.user_id] = set()
        self._memory_user_sessions[session.user_id].add(session.session_id)

        if session.user_id not in self._memory_session_versions:
            self._memory_session_versions[session.user_id] = 1

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Retrieve session information.

        Args:
            session_id: Session identifier

        Returns:
            SessionInfo if session exists and is valid, None otherwise
        """
        if self.redis_client:
            return self._get_session_redis(session_id)
        else:
            return self._get_session_memory(session_id)

    def _get_session_redis(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve session from Redis"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = self.redis_client.hgetall(session_key)

        if not session_data:
            return None

        # Convert Redis data types
        session_data = {
            k: (
                v
                if not k.endswith("_at") and k != "is_active"
                else (float(v) if k.endswith("_at") else v == "True")
            )
            for k, v in session_data.items()
        }

        session = SessionInfo.from_dict(session_data)

        # Check if session is expired
        if session.expires_at < time.time():
            self.invalidate_session(session_id)
            self._log_session_event(
                user_id=session.user_id, session_id=session_id, event=SessionEvent.EXPIRED
            )
            return None

        # Update last activity
        self.redis_client.hset(session_key, "last_activity", time.time())

        return session

    def _get_session_memory(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve session from memory"""
        session = self._memory_sessions.get(session_id)

        if not session:
            return None

        # Check if session is expired
        if session.expires_at < time.time():
            self.invalidate_session(session_id)
            return None

        # Update last activity
        session.last_activity = time.time()

        return session

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a specific session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was invalidated, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        if self.redis_client:
            self._invalidate_session_redis(session_id, session.user_id)
        else:
            self._invalidate_session_memory(session_id, session.user_id)

        self._log_session_event(
            user_id=session.user_id, session_id=session_id, event=SessionEvent.INVALIDATED
        )

        logger.info(f"Session {session_id} invalidated")
        return True

    def _invalidate_session_redis(self, session_id: str, user_id: str) -> None:
        """Invalidate session in Redis"""
        pipe: Pipeline = self.redis_client.pipeline()

        # Delete session data
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        pipe.delete(session_key)

        # Remove from user's session set
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        pipe.srem(user_sessions_key, session_id)

        pipe.execute()

    def _invalidate_session_memory(self, session_id: str, user_id: str) -> None:
        """Invalidate session in memory"""
        if session_id in self._memory_sessions:
            del self._memory_sessions[session_id]

        if user_id in self._memory_user_sessions:
            self._memory_user_sessions[user_id].discard(session_id)

    def invalidate_all_user_sessions(self, user_id: str, reason: str = "manual") -> int:
        """
        Invalidate all sessions for a user.
        Critical for password change security.

        Args:
            user_id: User identifier
            reason: Reason for invalidation

        Returns:
            Number of sessions invalidated
        """
        if self.redis_client:
            count = self._invalidate_all_user_sessions_redis(user_id)
        else:
            count = self._invalidate_all_user_sessions_memory(user_id)

        # Log the mass invalidation
        self._log_session_event(
            user_id=user_id,
            session_id="all",
            event=(
                SessionEvent.PASSWORD_CHANGED
                if reason == "password_change"
                else SessionEvent.LOGOUT
            ),
            details={"reason": reason, "sessions_invalidated": count},
        )

        logger.info(f"Invalidated {count} sessions for user {user_id} (reason: {reason})")
        return count

    def _invalidate_all_user_sessions_redis(self, user_id: str) -> int:
        """Invalidate all user sessions in Redis"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        session_ids = self.redis_client.smembers(user_sessions_key)

        if not session_ids:
            return 0

        pipe: Pipeline = self.redis_client.pipeline()

        # Delete all session data
        for session_id in session_ids:
            session_key = f"{self.SESSION_PREFIX}{session_id}"
            pipe.delete(session_key)

        # Clear user's session set
        pipe.delete(user_sessions_key)

        # Increment session version (invalidates all existing tokens)
        version_key = f"{self.SESSION_VERSION_PREFIX}{user_id}"
        pipe.hincrby(version_key, "version", 1)
        pipe.hset(version_key, "last_password_change", time.time())

        pipe.execute()

        return len(session_ids)

    def _invalidate_all_user_sessions_memory(self, user_id: str) -> int:
        """Invalidate all user sessions in memory"""
        if user_id not in self._memory_user_sessions:
            return 0

        session_ids = self._memory_user_sessions[user_id].copy()

        for session_id in session_ids:
            if session_id in self._memory_sessions:
                del self._memory_sessions[session_id]

        self._memory_user_sessions[user_id].clear()

        # Increment session version
        if user_id in self._memory_session_versions:
            self._memory_session_versions[user_id] += 1

        return len(session_ids)

    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of active SessionInfo objects
        """
        if self.redis_client:
            return self._get_user_sessions_redis(user_id)
        else:
            return self._get_user_sessions_memory(user_id)

    def _get_user_sessions_redis(self, user_id: str) -> List[SessionInfo]:
        """Get user sessions from Redis"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        session_ids = self.redis_client.smembers(user_sessions_key)

        sessions = []
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session and session.is_active:
                sessions.append(session)

        return sessions

    def _get_user_sessions_memory(self, user_id: str) -> List[SessionInfo]:
        """Get user sessions from memory"""
        if user_id not in self._memory_user_sessions:
            return []

        sessions = []
        for session_id in self._memory_user_sessions[user_id]:
            session = self.get_session(session_id)
            if session and session.is_active:
                sessions.append(session)

        return sessions

    def _enforce_session_limit(self, user_id: str) -> None:
        """
        Enforce maximum session limit per user.
        Removes oldest sessions if limit exceeded.
        """
        sessions = self.get_user_sessions(user_id)

        if len(sessions) <= self.max_sessions_per_user:
            return

        # Sort by creation time and remove oldest
        sessions.sort(key=lambda s: s.created_at)
        sessions_to_remove = sessions[: -self.max_sessions_per_user]

        for session in sessions_to_remove:
            self.invalidate_session(session.session_id)
            logger.info(f"Removed old session {session.session_id} due to session limit")

    def refresh_session(self, session_id: str, refresh_token: str) -> Optional[SessionInfo]:
        """
        Refresh a session using refresh token.

        Args:
            session_id: Session identifier
            refresh_token: Refresh token

        Returns:
            Updated SessionInfo if successful, None otherwise
        """
        session = self.get_session(session_id)

        if not session:
            return None

        # Verify refresh token
        if session.refresh_token != refresh_token:
            logger.warning(f"Invalid refresh token for session {session_id}")
            self._log_session_event(
                user_id=session.user_id,
                session_id=session_id,
                event=SessionEvent.SUSPICIOUS_ACTIVITY,
                details={"reason": "invalid_refresh_token"},
            )
            return None

        # Generate new tokens
        new_session_id = self.generate_session_token()
        new_refresh_token = self.generate_session_token()

        # Update session
        session.session_id = new_session_id
        session.refresh_token = new_refresh_token
        session.last_activity = time.time()
        session.expires_at = time.time() + self.session_timeout

        # Invalidate old session and create new one
        self.invalidate_session(session_id)

        if self.redis_client:
            self._store_session_redis(session)
        else:
            self._store_session_memory(session)

        self._log_session_event(
            user_id=session.user_id,
            session_id=new_session_id,
            event=SessionEvent.REFRESHED,
            details={"old_session_id": session_id},
        )

        return session

    def _log_session_event(
        self,
        user_id: str,
        session_id: str,
        event: SessionEvent,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log session events for audit trail.

        Args:
            user_id: User identifier
            session_id: Session identifier
            event: Session event type
            ip_address: Client IP address
            details: Additional event details
        """
        event_data = {
            "timestamp": time.time(),
            "user_id": user_id,
            "session_id": session_id,
            "event": event.value,
            "ip_address": ip_address,
            "details": details or {},
        }

        if self.redis_client:
            # Store in Redis with expiration
            event_key = f"{self.SESSION_EVENTS_PREFIX}{user_id}:{int(time.time())}"
            self.redis_client.setex(event_key, 86400 * 7, json.dumps(event_data))  # Keep for 7 days

        # Always log to application logger
        logger.info(f"Session event: {event.value} for user {user_id}", extra=event_data)

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        Should be called periodically by a background task.

        Returns:
            Number of sessions cleaned up
        """
        count = 0

        if self.redis_client:
            # Redis TTL handles expiration automatically
            # This is for additional cleanup if needed
            pass
        else:
            # Clean up memory sessions
            expired_sessions = []
            current_time = time.time()

            for session_id, session in self._memory_sessions.items():
                if session.expires_at < current_time:
                    expired_sessions.append((session_id, session.user_id))

            for session_id, user_id in expired_sessions:
                self._invalidate_session_memory(session_id, user_id)
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")

        return count


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(redis_client: Optional[redis.Redis] = None) -> SessionManager:
    """
    Get or create the global session manager instance.

    Args:
        redis_client: Optional Redis client to use

    Returns:
        SessionManager instance
    """
    global _session_manager

    if _session_manager is None:
        _session_manager = SessionManager(redis_client=redis_client)

    return _session_manager


def initialize_session_manager(
    redis_client: Optional[redis.Redis] = None,
    session_timeout: int = SessionManager.DEFAULT_SESSION_TIMEOUT,
    refresh_timeout: int = SessionManager.DEFAULT_REFRESH_TIMEOUT,
    max_sessions_per_user: int = SessionManager.MAX_SESSIONS_PER_USER,
) -> SessionManager:
    """
    Initialize the global session manager with custom settings.

    Args:
        redis_client: Redis client instance
        session_timeout: Session timeout in seconds
        refresh_timeout: Refresh token timeout in seconds
        max_sessions_per_user: Maximum concurrent sessions per user

    Returns:
        Initialized SessionManager instance
    """
    global _session_manager

    _session_manager = SessionManager(
        redis_client=redis_client,
        session_timeout=session_timeout,
        refresh_timeout=refresh_timeout,
        max_sessions_per_user=max_sessions_per_user,
    )

    return _session_manager
