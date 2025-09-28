"""
Comprehensive Security Audit System

Features:
- Real-time security event logging
- Threat detection and alerting
- Compliance audit trails
- Security metrics and reporting
- Integration with external SIEM systems
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import aiofiles
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Security event types for categorization"""

    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKOUT = "account_lockout"

    # Authorization Events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ROLE_CHANGE = "role_change"

    # Attack Detection
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DDOS_DETECTED = "ddos_detected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    CSRF_ATTEMPT = "csrf_attempt"

    # Data Protection
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    DATA_EXPORT = "data_export"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    ENCRYPTION_EVENT = "encryption_event"

    # System Security
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    SECURITY_SCAN = "security_scan"

    # Compliance
    AUDIT_LOG_ACCESS = "audit_log_access"
    COMPLIANCE_VIOLATION = "compliance_violation"
    DATA_RETENTION_EVENT = "data_retention_event"
    PRIVACY_EVENT = "privacy_event"


class SecurityLevel(Enum):
    """Security event severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure"""

    event_id: str
    event_type: SecurityEventType
    severity: SecurityLevel
    timestamp: datetime
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = None
    threat_indicators: List[str] = None
    compliance_tags: List[str] = None
    geo_location: Optional[Dict[str, str]] = None
    response_status: Optional[int] = None
    response_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class SecurityAuditSystem:
    """
    Comprehensive security audit and monitoring system

    Features:
    - Real-time event logging
    - Threat pattern detection
    - Compliance reporting
    - Alert generation
    - SIEM integration
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        log_directory: str = "/var/log/toolboxai/security",
        enable_file_logging: bool = True,
        enable_siem_integration: bool = False,
        retention_days: int = 90,
    ):
        self.redis = redis_client
        self.log_directory = Path(log_directory)
        self.enable_file_logging = enable_file_logging
        self.enable_siem_integration = enable_siem_integration
        self.retention_days = retention_days

        # Ensure log directory exists
        if self.enable_file_logging:
            self.log_directory.mkdir(parents=True, exist_ok=True)

        # Event pattern tracking
        self.threat_patterns = {}
        self.compliance_rules = {}

        # Initialize threat detection rules
        self._initialize_threat_detection()
        self._initialize_compliance_rules()

    async def log_event(self, event: SecurityEvent) -> str:
        """Log a security event with multiple outputs"""

        try:
            # Generate unique event ID if not provided
            if not event.event_id:
                event.event_id = self._generate_event_id(event)

            # Enrich event with additional context
            await self._enrich_event(event)

            # Store in Redis for real-time access
            await self._store_in_redis(event)

            # Write to log files
            if self.enable_file_logging:
                await self._write_to_file(event)

            # Check for threat patterns
            await self._check_threat_patterns(event)

            # Check compliance requirements
            await self._check_compliance(event)

            # Send to SIEM if enabled
            if self.enable_siem_integration:
                await self._send_to_siem(event)

            # Log to application logger
            self._log_to_application(event)

            return event.event_id

        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
            raise

    async def _enrich_event(self, event: SecurityEvent):
        """Enrich event with additional context"""

        # Add geo-location if IP available
        if event.source_ip and not event.geo_location:
            event.geo_location = await self._get_geo_location(event.source_ip)

        # Add threat indicators
        if not event.threat_indicators:
            event.threat_indicators = await self._detect_threat_indicators(event)

        # Add compliance tags
        if not event.compliance_tags:
            event.compliance_tags = self._get_compliance_tags(event)

    async def _store_in_redis(self, event: SecurityEvent):
        """Store event in Redis for real-time access"""

        # Store event data
        await self.redis.setex(
            f"security_event:{event.event_id}",
            86400 * self.retention_days,  # TTL in seconds
            event.to_json(),
        )

        # Add to time-series indexes
        timestamp_key = f"security_events:{event.timestamp.strftime('%Y%m%d')}"
        await self.redis.zadd(timestamp_key, {event.event_id: event.timestamp.timestamp()})
        await self.redis.expire(timestamp_key, 86400 * self.retention_days)

        # Add to type-based indexes
        type_key = f"security_events:type:{event.event_type.value}"
        await self.redis.lpush(type_key, event.event_id)
        await self.redis.ltrim(type_key, 0, 1000)  # Keep last 1000 events
        await self.redis.expire(type_key, 86400 * self.retention_days)

        # Add to severity indexes
        if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            critical_key = f"security_events:critical:{event.timestamp.strftime('%Y%m%d')}"
            await self.redis.lpush(critical_key, event.event_id)
            await self.redis.expire(critical_key, 86400 * 30)  # Keep critical events for 30 days

    async def _write_to_file(self, event: SecurityEvent):
        """Write event to daily log files"""

        log_file = self.log_directory / f"security_{event.timestamp.strftime('%Y%m%d')}.jsonl"

        async with aiofiles.open(log_file, "a") as f:
            await f.write(event.to_json() + "\n")

    async def _check_threat_patterns(self, event: SecurityEvent):
        """Check for known threat patterns and generate alerts"""

        patterns_detected = []

        # Check for brute force patterns
        if event.event_type in [SecurityEventType.LOGIN_FAILURE, SecurityEventType.MFA_FAILURE]:
            pattern = await self._check_brute_force_pattern(event)
            if pattern:
                patterns_detected.append(pattern)

        # Check for account enumeration
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            pattern = await self._check_account_enumeration(event)
            if pattern:
                patterns_detected.append(pattern)

        # Check for privilege escalation
        if event.event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            pattern = await self._check_privilege_escalation_pattern(event)
            if pattern:
                patterns_detected.append(pattern)

        # Generate alerts for detected patterns
        for pattern in patterns_detected:
            await self._generate_alert(event, pattern)

    async def _check_brute_force_pattern(self, event: SecurityEvent) -> Optional[str]:
        """Check for brute force attack patterns"""

        if not event.source_ip:
            return None

        # Count failed attempts from this IP in last hour
        key = f"brute_force:{event.source_ip}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1 hour TTL

        # Alert if more than 10 failures per hour
        if count > 10:
            return f"brute_force_detected:ip={event.source_ip},count={count}"

        return None

    async def _check_account_enumeration(self, event: SecurityEvent) -> Optional[str]:
        """Check for account enumeration patterns"""

        if not event.source_ip:
            return None

        # Track unique usernames attempted from this IP
        key = f"enum_users:{event.source_ip}"
        user_key = event.user_email or event.user_id or "unknown"

        await self.redis.sadd(key, user_key)
        await self.redis.expire(key, 3600)  # 1 hour TTL

        unique_users = await self.redis.scard(key)

        # Alert if attempting many different usernames
        if unique_users > 20:
            return f"account_enumeration:ip={event.source_ip},users_attempted={unique_users}"

        return None

    async def _check_privilege_escalation_pattern(self, event: SecurityEvent) -> Optional[str]:
        """Check for privilege escalation patterns"""

        if not event.user_id:
            return None

        # Track role changes for this user
        key = f"role_changes:{event.user_id}"
        await self.redis.incr(key)
        await self.redis.expire(key, 86400)  # 24 hours TTL

        changes = await self.redis.get(key)

        # Alert if multiple role changes in 24 hours
        if int(changes or 0) > 3:
            return f"suspicious_privilege_changes:user={event.user_id},changes={changes}"

        return None

    async def _generate_alert(self, event: SecurityEvent, pattern: str):
        """Generate security alert"""

        alert = {
            "alert_id": self._generate_alert_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high",
            "pattern": pattern,
            "related_event": event.event_id,
            "source_ip": event.source_ip,
            "user_id": event.user_id,
            "description": f"Security pattern detected: {pattern}",
            "recommended_action": self._get_recommended_action(pattern),
        }

        # Store alert
        await self.redis.setex(
            f"security_alert:{alert['alert_id']}",
            86400 * 7,  # Keep alerts for 7 days
            json.dumps(alert),
        )

        # Add to alerts queue for notification
        await self.redis.lpush("security_alerts_queue", json.dumps(alert))

        # Log critical alert
        logger.critical(f"SECURITY_ALERT: {alert['description']} - {pattern}")

    def _get_recommended_action(self, pattern: str) -> str:
        """Get recommended action for detected pattern"""

        if "brute_force" in pattern:
            return "Consider IP blocking and account lockout policies"
        elif "enumeration" in pattern:
            return "Implement CAPTCHA and rate limiting"
        elif "privilege" in pattern:
            return "Review user permissions and audit trail"
        else:
            return "Investigate and monitor for additional suspicious activity"

    async def get_security_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get security metrics for dashboard"""

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        metrics = {
            "timeframe": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days,
            },
            "event_counts": {},
            "threat_indicators": {},
            "top_source_ips": [],
            "failed_logins": 0,
            "successful_logins": 0,
            "critical_events": 0,
            "compliance_violations": 0,
        }

        # Count events by type
        for event_type in SecurityEventType:
            type_key = f"security_events:type:{event_type.value}"
            count = await self.redis.llen(type_key)
            metrics["event_counts"][event_type.value] = count

        # Get critical events count
        for i in range(days):
            date = (end_time - timedelta(days=i)).strftime("%Y%m%d")
            critical_key = f"security_events:critical:{date}"
            count = await self.redis.llen(critical_key)
            metrics["critical_events"] += count

        # Calculate specific metrics
        metrics["failed_logins"] = metrics["event_counts"].get("login_failure", 0)
        metrics["successful_logins"] = metrics["event_counts"].get("login_success", 0)

        # Get active alerts
        alerts_count = await self.redis.llen("security_alerts_queue")
        metrics["active_alerts"] = alerts_count

        return metrics

    def _generate_event_id(self, event: SecurityEvent) -> str:
        """Generate unique event ID"""
        content = f"{event.event_type.value}{event.timestamp.isoformat()}{event.source_ip or ''}{event.user_id or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid

        return f"alert_{uuid.uuid4().hex[:12]}"

    async def _get_geo_location(self, ip: str) -> Dict[str, str]:
        """Get geo-location for IP address (placeholder)"""
        # In production, integrate with GeoIP service
        return {"country": "unknown", "city": "unknown", "region": "unknown"}

    async def _detect_threat_indicators(self, event: SecurityEvent) -> List[str]:
        """Detect threat indicators in event"""
        indicators = []

        # Check user agent for known attack tools
        if event.user_agent:
            suspicious_agents = ["sqlmap", "nikto", "burp", "nmap", "masscan", "dirbuster"]
            for agent in suspicious_agents:
                if agent in event.user_agent.lower():
                    indicators.append(f"suspicious_user_agent:{agent}")

        # Check endpoint for suspicious patterns
        if event.endpoint:
            if any(
                pattern in event.endpoint.lower()
                for pattern in ["../", "union", "select", "<script"]
            ):
                indicators.append("suspicious_endpoint_pattern")

        return indicators

    def _get_compliance_tags(self, event: SecurityEvent) -> List[str]:
        """Get compliance tags for event"""
        tags = []

        # GDPR compliance
        if event.event_type in [
            SecurityEventType.SENSITIVE_DATA_ACCESS,
            SecurityEventType.DATA_EXPORT,
        ]:
            tags.append("gdpr_relevant")

        # SOX compliance
        if event.event_type in [
            SecurityEventType.DATA_MODIFICATION,
            SecurityEventType.CONFIGURATION_CHANGE,
        ]:
            tags.append("sox_relevant")

        # PCI DSS compliance
        if "payment" in str(event.details).lower():
            tags.append("pci_dss_relevant")

        return tags

    def _initialize_threat_detection(self):
        """Initialize threat detection rules"""
        # This would load rules from configuration
        pass

    def _initialize_compliance_rules(self):
        """Initialize compliance rules"""
        # This would load compliance requirements
        pass

    async def _check_compliance(self, event: SecurityEvent):
        """Check compliance requirements"""
        # Implement compliance checking logic
        pass

    async def _send_to_siem(self, event: SecurityEvent):
        """Send event to external SIEM system"""
        # Implement SIEM integration
        pass

    def _log_to_application(self, event: SecurityEvent):
        """Log to application logger"""
        level = (
            logging.WARNING
            if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            else logging.INFO
        )
        logger.log(level, f"SECURITY_EVENT: {event.event_type.value} - {event.to_json()}")


# Global audit system instance
_audit_system: Optional[SecurityAuditSystem] = None


def get_audit_system(redis_client: redis.Redis = None) -> SecurityAuditSystem:
    """Get audit system instance"""
    global _audit_system

    if _audit_system is None:
        if redis_client is None:
            raise RuntimeError("Redis client required for audit system")
        _audit_system = SecurityAuditSystem(redis_client)

    return _audit_system


# Convenience functions for common events
async def log_login_attempt(
    user_id: str,
    success: bool,
    ip_address: str,
    user_agent: str = None,
    details: Dict[str, Any] = None,
):
    """Log login attempt"""
    audit_system = get_audit_system()

    event = SecurityEvent(
        event_id=None,
        event_type=SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILURE,
        severity=SecurityLevel.LOW if success else SecurityLevel.MEDIUM,
        timestamp=datetime.utcnow(),
        source_ip=ip_address,
        user_id=user_id,
        user_agent=user_agent,
        details=details or {},
    )

    return await audit_system.log_event(event)


async def log_access_attempt(
    user_id: str,
    endpoint: str,
    method: str,
    granted: bool,
    ip_address: str,
    status_code: int = None,
    details: Dict[str, Any] = None,
):
    """Log access attempt"""
    audit_system = get_audit_system()

    event = SecurityEvent(
        event_id=None,
        event_type=SecurityEventType.ACCESS_GRANTED if granted else SecurityEventType.ACCESS_DENIED,
        severity=SecurityLevel.LOW if granted else SecurityLevel.MEDIUM,
        timestamp=datetime.utcnow(),
        source_ip=ip_address,
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        response_status=status_code,
        details=details or {},
    )

    return await audit_system.log_event(event)


async def log_security_violation(
    violation_type: SecurityEventType,
    severity: SecurityLevel,
    ip_address: str,
    user_id: str = None,
    endpoint: str = None,
    details: Dict[str, Any] = None,
):
    """Log security violation"""
    audit_system = get_audit_system()

    event = SecurityEvent(
        event_id=None,
        event_type=violation_type,
        severity=severity,
        timestamp=datetime.utcnow(),
        source_ip=ip_address,
        user_id=user_id,
        endpoint=endpoint,
        details=details or {},
    )

    return await audit_system.log_event(event)
