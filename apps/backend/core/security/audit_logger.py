"""
Security Audit Logging System

Comprehensive audit logging for security events, user actions, and system activities.
Supports multiple output targets (file, database, SIEM) and provides tamper detection.
"""

import json
import hashlib
import hmac
import logging
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
from queue import Queue, Empty
import gzip
import shutil

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
import redis

from toolboxai_settings import settings

logger = logging.getLogger(__name__)


def _serialize_audit_event(event: "AuditEvent") -> Dict[str, Any]:
    """Convert AuditEvent to JSON-serializable dict"""
    event_dict = asdict(event)
    # Convert enums to their values
    if isinstance(event_dict.get("category"), Enum):
        event_dict["category"] = event.category.value
    if isinstance(event_dict.get("severity"), Enum):
        event_dict["severity"] = event.severity.value
    return event_dict

Base = declarative_base()


class AuditSeverity(Enum):
    """Audit event severity levels"""
    CRITICAL = "critical"  # Security breaches, data loss
    HIGH = "high"         # Failed authentications, authorization violations
    MEDIUM = "medium"     # Configuration changes, suspicious activity
    LOW = "low"          # Normal operations, successful logins
    INFO = "info"        # Informational events


class AuditCategory(Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION = "configuration"
    SECURITY_EVENT = "security_event"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    API_ACCESS = "api_access"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Structured audit event"""
    timestamp: str
    event_id: str
    category: AuditCategory
    severity: AuditSeverity
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    action: str
    resource: Optional[str]
    result: str  # success, failure, error
    details: Dict[str, Any]
    session_id: Optional[str]
    request_id: Optional[str]
    correlation_id: Optional[str]
    environment: str
    service_name: str
    host: str
    integrity_hash: Optional[str] = None


class AuditLogEntry(Base):
    """Database model for audit logs"""
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    category = Column(String(50), index=True)
    severity = Column(String(20), index=True)
    user_id = Column(String(50), index=True, nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), index=True, nullable=True)
    action = Column(String(200), index=True)
    resource = Column(String(500), nullable=True)
    result = Column(String(20))
    details = Column(JSON)
    session_id = Column(String(64), index=True, nullable=True)
    request_id = Column(String(64), index=True, nullable=True)
    correlation_id = Column(String(64), index=True, nullable=True)
    integrity_hash = Column(String(128))
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))


class SecurityAuditLogger:
    """
    Enterprise-grade security audit logging system
    """

    def __init__(
        self,
        service_name: str = "toolboxai",
        environment: str = None,
        db_session: Optional[Session] = None,
        redis_client: Optional[redis.Redis] = None,
        log_file_path: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_db_logging: bool = True,
        enable_siem_export: bool = False,
        integrity_key: Optional[str] = None,
        async_mode: bool = True,
        buffer_size: int = 1000
    ):
        """
        Initialize the audit logger

        Args:
            service_name: Name of the service for identification
            environment: Environment (production, staging, development)
            db_session: Database session for persistence
            redis_client: Redis client for real-time alerts
            log_file_path: Path for audit log files
            enable_file_logging: Enable file-based logging
            enable_db_logging: Enable database logging
            enable_siem_export: Enable SIEM integration
            integrity_key: Secret key for integrity hashing
            async_mode: Enable asynchronous logging
            buffer_size: Size of the async buffer
        """
        self.service_name = service_name
        self.environment = environment or settings.ENVIRONMENT
        self.db = db_session
        self.redis = redis_client
        self.enable_file_logging = enable_file_logging
        self.enable_db_logging = enable_db_logging
        self.enable_siem_export = enable_siem_export
        self.async_mode = async_mode
        self.host = os.uname().nodename

        # Set up integrity key for tamper detection
        self.integrity_key = integrity_key or settings.JWT_SECRET_KEY

        # Set up file logging
        if enable_file_logging:
            self.log_file_path = log_file_path or f"/var/log/{service_name}/audit.log"
            self._setup_file_logging()

        # Set up async processing
        if async_mode:
            self.event_queue = Queue(maxsize=buffer_size)
            self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.processing_thread.start()

        # Statistics
        self.stats = {
            "total_events": 0,
            "events_by_category": {},
            "events_by_severity": {},
            "failed_events": 0
        }

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        logger.info(f"Security Audit Logger initialized for {service_name} in {self.environment}")

    def _setup_file_logging(self):
        """Set up secure file-based logging"""
        try:
            log_dir = Path(self.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

            # Set restrictive permissions on log file
            if Path(self.log_file_path).exists():
                os.chmod(self.log_file_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to set up file logging: {e}")
            self.enable_file_logging = False

    async def log_event(
        self,
        category: AuditCategory,
        severity: AuditSeverity,
        action: str,
        result: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Log a security audit event

        Args:
            category: Event category
            severity: Event severity
            action: Action performed
            result: Result of the action
            details: Additional event details
            user_id: User identifier
            username: Username
            ip_address: Client IP address
            user_agent: Client user agent
            resource: Affected resource
            session_id: Session identifier
            request_id: Request identifier
            correlation_id: Correlation ID for tracing

        Returns:
            Event ID of the logged event
        """
        # Generate event ID
        event_id = self._generate_event_id()

        # Create audit event
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_id=event_id,
            category=category,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource=resource,
            result=result,
            details=details,
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id,
            environment=self.environment,
            service_name=self.service_name,
            host=self.host
        )

        # Calculate integrity hash
        event.integrity_hash = self._calculate_integrity_hash(event)

        # Process event
        if self.async_mode:
            await self._queue_event(event)
        else:
            await self._process_event(event)

        # Check for alerts
        await self._check_alerts(event)

        # Update statistics
        self._update_statistics(event)

        return event_id

    async def _queue_event(self, event: AuditEvent):
        """Queue event for async processing"""
        try:
            self.event_queue.put_nowait(_serialize_audit_event(event))
        except:
            # If queue is full, process synchronously
            await self._process_event(event)

    async def _process_event(self, event: AuditEvent):
        """Process a single audit event"""
        tasks = []

        # File logging
        if self.enable_file_logging:
            tasks.append(self._write_to_file(event))

        # Database logging
        if self.enable_db_logging and self.db:
            tasks.append(self._write_to_database(event))

        # SIEM export
        if self.enable_siem_export:
            tasks.append(self._export_to_siem(event))

        # Redis for real-time monitoring
        if self.redis:
            tasks.append(self._publish_to_redis(event))

        # Execute all tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error processing audit event: {result}")
                    self.stats["failed_events"] += 1

    def _process_queue(self):
        """Background thread for processing queued events"""
        while True:
            try:
                event_data = self.event_queue.get(timeout=1)
                event = self._reconstruct_event(event_data)
                asyncio.run(self._process_event(event))
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in audit queue processor: {e}")

    async def _write_to_file(self, event: AuditEvent):
        """Write event to audit log file"""
        try:
            log_line = json.dumps(_serialize_audit_event(event)) + "\n"

            # Atomic write with rotation
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)

            # Check for rotation
            await self._rotate_log_if_needed()

        except Exception as e:
            logger.error(f"Failed to write audit log to file: {e}")
            raise

    async def _write_to_database(self, event: AuditEvent):
        """Write event to database"""
        try:
            db_entry = AuditLogEntry(
                event_id=event.event_id,
                timestamp=datetime.fromisoformat(event.timestamp),
                category=event.category.value,
                severity=event.severity.value,
                user_id=event.user_id,
                username=event.username,
                ip_address=event.ip_address,
                action=event.action,
                resource=event.resource,
                result=event.result,
                details=event.details,
                session_id=event.session_id,
                request_id=event.request_id,
                correlation_id=event.correlation_id,
                integrity_hash=event.integrity_hash
            )

            self.db.add(db_entry)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to write audit log to database: {e}")
            self.db.rollback()
            raise

    async def _export_to_siem(self, event: AuditEvent):
        """Export event to SIEM system"""
        # Implement SIEM integration (e.g., Splunk, ELK, Datadog)
        # This is a placeholder for actual SIEM integration
        siem_format = {
            "time": event.timestamp,
            "source": self.service_name,
            "sourcetype": "security_audit",
            "host": event.host,
            "event": _serialize_audit_event(event)
        }

        # Send to SIEM endpoint
        # await siem_client.send(siem_format)

    async def _publish_to_redis(self, event: AuditEvent):
        """Publish event to Redis for real-time monitoring"""
        try:
            channel = f"audit:{event.category.value}:{event.severity.value}"
            message = json.dumps(_serialize_audit_event(event))
            self.redis.publish(channel, message)

            # Store in Redis for recent events
            key = f"audit:recent:{event.category.value}"
            self.redis.lpush(key, message)
            self.redis.ltrim(key, 0, 100)  # Keep last 100 events
            self.redis.expire(key, 86400)  # Expire after 24 hours

        except Exception as e:
            logger.error(f"Failed to publish audit event to Redis: {e}")

    async def _check_alerts(self, event: AuditEvent):
        """Check if event should trigger alerts"""
        # Critical severity always triggers alerts
        if event.severity == AuditSeverity.CRITICAL:
            await self._trigger_alert(event, "Critical security event detected")

        # Multiple failed authentication attempts
        if event.category == AuditCategory.AUTHENTICATION and event.result == "failure":
            count = await self._count_recent_failures(event.user_id or event.ip_address)
            if count >= 5:
                await self._trigger_alert(event, f"Multiple failed authentication attempts: {count}")

        # Unauthorized data access
        if event.category == AuditCategory.DATA_ACCESS and event.result == "unauthorized":
            await self._trigger_alert(event, "Unauthorized data access attempt")

    async def _trigger_alert(self, event: AuditEvent, message: str):
        """Trigger security alert"""
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "event": _serialize_audit_event(event)
        }

        # Execute alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        # Log alert
        logger.critical(f"SECURITY ALERT: {message} - Event ID: {event.event_id}")

    async def _count_recent_failures(self, identifier: str) -> int:
        """Count recent failure events for an identifier"""
        if not self.redis or not identifier:
            return 0

        key = f"audit:failures:{identifier}"
        count = self.redis.get(key)
        return int(count) if count else 0

    def _calculate_integrity_hash(self, event: AuditEvent) -> str:
        """Calculate integrity hash for tamper detection"""
        # Create a deterministic string representation
        data = f"{event.timestamp}|{event.event_id}|{event.category.value}|{event.severity.value}|"
        data += f"{event.action}|{event.result}|{json.dumps(event.details, sort_keys=True)}"

        # Calculate HMAC
        h = hmac.new(
            self.integrity_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        )
        return h.hexdigest()

    def verify_integrity(self, event: AuditEvent) -> bool:
        """Verify event integrity"""
        expected_hash = self._calculate_integrity_hash(event)
        return event.integrity_hash == expected_hash

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return str(uuid.uuid4())

    def _reconstruct_event(self, event_data: Dict[str, Any]) -> AuditEvent:
        """Reconstruct AuditEvent from dictionary"""
        event_data['category'] = AuditCategory(event_data['category'])
        event_data['severity'] = AuditSeverity(event_data['severity'])
        return AuditEvent(**event_data)

    def _update_statistics(self, event: AuditEvent):
        """Update audit statistics"""
        self.stats["total_events"] += 1

        category = event.category.value
        self.stats["events_by_category"][category] = self.stats["events_by_category"].get(category, 0) + 1

        severity = event.severity.value
        self.stats["events_by_severity"][severity] = self.stats["events_by_severity"].get(severity, 0) + 1

    async def _rotate_log_if_needed(self):
        """Rotate log file if it exceeds size limit"""
        try:
            if not Path(self.log_file_path).exists():
                return

            file_size = Path(self.log_file_path).stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                rotated_path = f"{self.log_file_path}.{timestamp}"

                # Move and compress
                shutil.move(self.log_file_path, rotated_path)

                with open(rotated_path, 'rb') as f_in:
                    with gzip.open(f"{rotated_path}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                os.remove(rotated_path)

                logger.info(f"Rotated audit log to {rotated_path}.gz")

        except Exception as e:
            logger.error(f"Failed to rotate audit log: {e}")

    def add_alert_callback(self, callback: Callable):
        """Add alert callback for security events"""
        self.alert_callbacks.append(callback)

    async def query_events(
        self,
        start_time: datetime,
        end_time: datetime,
        category: Optional[AuditCategory] = None,
        severity: Optional[AuditSeverity] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit events from database"""
        if not self.db:
            return []

        query = self.db.query(AuditLogEntry)
        query = query.filter(AuditLogEntry.timestamp >= start_time)
        query = query.filter(AuditLogEntry.timestamp <= end_time)

        if category:
            query = query.filter(AuditLogEntry.category == category.value)
        if severity:
            query = query.filter(AuditLogEntry.severity == severity.value)
        if user_id:
            query = query.filter(AuditLogEntry.user_id == user_id)

        query = query.order_by(AuditLogEntry.timestamp.desc())
        query = query.limit(limit)

        results = []
        for entry in query.all():
            event_data = {
                "timestamp": entry.timestamp.isoformat(),
                "event_id": entry.event_id,
                "category": AuditCategory(entry.category),
                "severity": AuditSeverity(entry.severity),
                "user_id": entry.user_id,
                "username": entry.username,
                "ip_address": entry.ip_address,
                "user_agent": None,
                "action": entry.action,
                "resource": entry.resource,
                "result": entry.result,
                "details": entry.details,
                "session_id": entry.session_id,
                "request_id": entry.request_id,
                "correlation_id": entry.correlation_id,
                "environment": self.environment,
                "service_name": self.service_name,
                "host": self.host,
                "integrity_hash": entry.integrity_hash
            }
            results.append(AuditEvent(**event_data))

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        return self.stats.copy()

    async def archive_old_events(self, days_to_keep: int = 90):
        """Archive old audit events"""
        if not self.db:
            return

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        try:
            # Mark old events as archived
            self.db.query(AuditLogEntry).filter(
                AuditLogEntry.timestamp < cutoff_date,
                AuditLogEntry.archived == False
            ).update({"archived": True})

            self.db.commit()
            logger.info(f"Archived audit events older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Failed to archive audit events: {e}")
            self.db.rollback()


# Singleton instance for easy access
_audit_logger = None

def get_audit_logger() -> SecurityAuditLogger:
    """Get singleton audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SecurityAuditLogger()
    return _audit_logger


# Convenience functions
async def audit_log(
    category: AuditCategory,
    severity: AuditSeverity,
    action: str,
    **kwargs
) -> str:
    """Convenience function for logging audit events"""
    logger = get_audit_logger()
    return await logger.log_event(category, severity, action, **kwargs)


# Export public interface
__all__ = [
    "SecurityAuditLogger",
    "AuditEvent",
    "AuditSeverity",
    "AuditCategory",
    "AuditLogEntry",
    "get_audit_logger",
    "audit_log"
]