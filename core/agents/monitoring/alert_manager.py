"""
Alert Manager for GPT-4.1 Migration Monitoring

Manages alerts, notifications, and escalations for the migration process.
Integrates with multiple notification channels and provides intelligent alerting.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(Enum):
    """Alert categories"""
    COST = "cost"
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    DEADLINE = "deadline"
    BUDGET = "budget"
    QUALITY = "quality"
    SECURITY = "security"


class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SMS = "sms"
    DASHBOARD = "dashboard"
    LOG = "log"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    escalation_level: int = 0
    suppressed: bool = False


@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    category: AlertCategory
    severity: AlertSeverity
    condition: str  # Description of trigger condition
    threshold: float
    enabled: bool = True
    channels: List[NotificationChannel] = field(default_factory=list)
    escalation_time: int = 3600  # seconds before escalation
    suppression_time: int = 300  # seconds to suppress duplicate alerts
    custom_handler: Optional[Callable] = None


@dataclass
class NotificationConfig:
    """Notification channel configuration"""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    rate_limit: int = 60  # max notifications per hour
    priority_filter: List[AlertSeverity] = field(default_factory=list)


class AlertManager:
    """
    Comprehensive alert management system for GPT-4.1 migration monitoring.

    Features:
    - Multi-channel notification delivery
    - Alert escalation and acknowledgment
    - Rate limiting and suppression
    - Custom alert rules and handlers
    - Alert analytics and reporting
    """

    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}

        # Alert suppression tracking
        self.suppressed_alerts: Dict[str, datetime] = {}  # rule_id -> last_sent

        # Rate limiting tracking
        self.notification_counts: Dict[NotificationChannel, List[datetime]] = {}

        # Custom handlers
        self.custom_handlers: Dict[str, Callable] = {}

        # Initialize default alert rules
        self._initialize_default_rules()

        # Initialize default notification configs
        self._initialize_default_notifications()

        logger.info("AlertManager initialized")

    def _initialize_default_rules(self) -> None:
        """Initialize default alert rules for migration monitoring"""

        default_rules = [
            AlertRule(
                id="cost_budget_exceeded",
                name="Daily Budget Exceeded",
                category=AlertCategory.BUDGET,
                severity=AlertSeverity.CRITICAL,
                condition="Daily cost exceeds budget limit",
                threshold=100.0,  # $100
                channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
                escalation_time=1800  # 30 minutes
            ),
            AlertRule(
                id="error_rate_high",
                name="High Error Rate",
                category=AlertCategory.ERROR_RATE,
                severity=AlertSeverity.WARNING,
                condition="Error rate exceeds 5%",
                threshold=0.05,
                channels=[NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
                escalation_time=3600  # 1 hour
            ),
            AlertRule(
                id="error_rate_critical",
                name="Critical Error Rate",
                category=AlertCategory.ERROR_RATE,
                severity=AlertSeverity.CRITICAL,
                condition="Error rate exceeds 10%",
                threshold=0.10,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.DASHBOARD],
                escalation_time=900  # 15 minutes
            ),
            AlertRule(
                id="latency_high",
                name="High API Latency",
                category=AlertCategory.PERFORMANCE,
                severity=AlertSeverity.WARNING,
                condition="Average latency exceeds 5 seconds",
                threshold=5.0,
                channels=[NotificationChannel.DASHBOARD],
                escalation_time=3600
            ),
            AlertRule(
                id="latency_critical",
                name="Critical API Latency",
                category=AlertCategory.PERFORMANCE,
                severity=AlertSeverity.CRITICAL,
                condition="Average latency exceeds 10 seconds",
                threshold=10.0,
                channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
                escalation_time=1800
            ),
            AlertRule(
                id="deadline_approaching",
                name="Migration Deadline Approaching",
                category=AlertCategory.DEADLINE,
                severity=AlertSeverity.WARNING,
                condition="Less than 30 days to migration deadline",
                threshold=30.0,  # days
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_time=86400  # 24 hours
            ),
            AlertRule(
                id="deadline_critical",
                name="Migration Deadline Critical",
                category=AlertCategory.DEADLINE,
                severity=AlertSeverity.EMERGENCY,
                condition="Less than 7 days to migration deadline",
                threshold=7.0,  # days
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS],
                escalation_time=3600
            ),
            AlertRule(
                id="monthly_budget_approaching",
                name="Monthly Budget Limit Approaching",
                category=AlertCategory.BUDGET,
                severity=AlertSeverity.WARNING,
                condition="Monthly spending at 80% of budget",
                threshold=0.80,  # 80%
                channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
                escalation_time=86400
            ),
            AlertRule(
                id="quality_degradation",
                name="Output Quality Degradation",
                category=AlertCategory.QUALITY,
                severity=AlertSeverity.WARNING,
                condition="Output quality score below 80%",
                threshold=0.80,
                channels=[NotificationChannel.DASHBOARD],
                escalation_time=7200  # 2 hours
            )
        ]

        for rule in default_rules:
            self.alert_rules[rule.id] = rule

    def _initialize_default_notifications(self) -> None:
        """Initialize default notification channel configurations"""

        self.notification_configs = {
            NotificationChannel.EMAIL: NotificationConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                config={
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "recipients": ["admin@toolboxai.com"],
                    "sender": "alerts@toolboxai.com"
                },
                rate_limit=20,  # 20 emails per hour
                priority_filter=[AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
            ),
            NotificationChannel.SLACK: NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=False,  # Disabled by default until configured
                config={
                    "webhook_url": "",
                    "channel": "#gpt-migration-alerts",
                    "username": "GPT Migration Monitor"
                },
                rate_limit=100
            ),
            NotificationChannel.DASHBOARD: NotificationConfig(
                channel=NotificationChannel.DASHBOARD,
                enabled=True,
                config={},
                rate_limit=1000  # High limit for dashboard
            ),
            NotificationChannel.LOG: NotificationConfig(
                channel=NotificationChannel.LOG,
                enabled=True,
                config={"log_level": "WARNING"},
                rate_limit=1000
            ),
            NotificationChannel.WEBHOOK: NotificationConfig(
                channel=NotificationChannel.WEBHOOK,
                enabled=False,
                config={"url": "", "headers": {}},
                rate_limit=200
            )
        }

    async def trigger_alert(
        self,
        rule_id: str,
        message: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """Trigger an alert based on a rule"""

        if rule_id not in self.alert_rules:
            logger.error(f"Unknown alert rule: {rule_id}")
            return None

        rule = self.alert_rules[rule_id]

        if not rule.enabled:
            logger.debug(f"Alert rule {rule_id} is disabled")
            return None

        # Check if alert should be suppressed
        if self._should_suppress_alert(rule_id):
            logger.debug(f"Alert {rule_id} suppressed due to rate limiting")
            return None

        # Create alert
        alert_id = f"{rule_id}_{int(datetime.now().timestamp())}"
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(timezone.utc),
            severity=rule.severity,
            category=rule.category,
            title=rule.name,
            message=f"{message} (Value: {value}, Threshold: {rule.threshold})",
            source=f"AlertRule:{rule_id}",
            metadata=metadata or {}
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Update suppression tracking
        self.suppressed_alerts[rule_id] = datetime.now(timezone.utc)

        # Send notifications
        await self._send_notifications(alert, rule)

        # Set up escalation if needed
        if rule.escalation_time > 0:
            asyncio.create_task(self._schedule_escalation(alert, rule))

        logger.info(f"Alert triggered: {alert.title} ({alert.severity.value})")
        return alert

    def _should_suppress_alert(self, rule_id: str) -> bool:
        """Check if alert should be suppressed due to recent similar alert"""

        if rule_id not in self.alert_rules:
            return False

        rule = self.alert_rules[rule_id]

        if rule_id in self.suppressed_alerts:
            last_sent = self.suppressed_alerts[rule_id]
            time_since_last = (datetime.now(timezone.utc) - last_sent).total_seconds()

            if time_since_last < rule.suppression_time:
                return True

        return False

    async def _send_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Send notifications through configured channels"""

        for channel in rule.channels:
            if channel not in self.notification_configs:
                continue

            config = self.notification_configs[channel]

            if not config.enabled:
                continue

            # Check rate limiting
            if self._is_rate_limited(channel):
                logger.warning(f"Rate limit exceeded for {channel.value}")
                continue

            # Check priority filter
            if config.priority_filter and alert.severity not in config.priority_filter:
                continue

            try:
                await self._send_notification(alert, channel, config)
                self._update_rate_limit_counter(channel)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.value}: {e}")

    def _is_rate_limited(self, channel: NotificationChannel) -> bool:
        """Check if channel is rate limited"""

        if channel not in self.notification_configs:
            return True

        config = self.notification_configs[channel]
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        if channel not in self.notification_counts:
            self.notification_counts[channel] = []

        # Remove old entries
        self.notification_counts[channel] = [
            timestamp for timestamp in self.notification_counts[channel]
            if timestamp > hour_ago
        ]

        return len(self.notification_counts[channel]) >= config.rate_limit

    def _update_rate_limit_counter(self, channel: NotificationChannel) -> None:
        """Update rate limit counter for channel"""

        if channel not in self.notification_counts:
            self.notification_counts[channel] = []

        self.notification_counts[channel].append(datetime.now(timezone.utc))

    async def _send_notification(
        self,
        alert: Alert,
        channel: NotificationChannel,
        config: NotificationConfig
    ) -> None:
        """Send notification to specific channel"""

        if channel == NotificationChannel.EMAIL:
            await self._send_email_notification(alert, config)
        elif channel == NotificationChannel.SLACK:
            await self._send_slack_notification(alert, config)
        elif channel == NotificationChannel.DASHBOARD:
            await self._send_dashboard_notification(alert, config)
        elif channel == NotificationChannel.LOG:
            await self._send_log_notification(alert, config)
        elif channel == NotificationChannel.WEBHOOK:
            await self._send_webhook_notification(alert, config)
        else:
            logger.warning(f"Unsupported notification channel: {channel.value}")

    async def _send_email_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send email notification"""
        # Placeholder implementation
        logger.info(f"EMAIL: {alert.title} - {alert.message}")

    async def _send_slack_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send Slack notification"""
        # Placeholder implementation
        logger.info(f"SLACK: {alert.title} - {alert.message}")

    async def _send_dashboard_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send dashboard notification via Pusher"""
        try:
            # Try to send via Pusher for real-time dashboard updates
            from apps.backend.services.pusher import trigger_event as pusher_trigger_event

            await pusher_trigger_event(
                "gpt-migration-alerts",
                "alert",
                {
                    "type": "migration_alert",
                    "payload": {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "severity": alert.severity.value,
                        "category": alert.category.value,
                        "title": alert.title,
                        "message": alert.message,
                        "metadata": alert.metadata
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send dashboard notification via Pusher: {e}")

    async def _send_log_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send log notification"""
        log_level = config.config.get("log_level", "WARNING")

        if log_level == "INFO":
            logger.info(f"ALERT: {alert.title} - {alert.message}")
        elif log_level == "WARNING":
            logger.warning(f"ALERT: {alert.title} - {alert.message}")
        elif log_level == "ERROR":
            logger.error(f"ALERT: {alert.title} - {alert.message}")
        elif log_level == "CRITICAL":
            logger.critical(f"ALERT: {alert.title} - {alert.message}")

    async def _send_webhook_notification(self, alert: Alert, config: NotificationConfig) -> None:
        """Send webhook notification"""
        # Placeholder implementation
        logger.info(f"WEBHOOK: {alert.title} - {alert.message}")

    async def _schedule_escalation(self, alert: Alert, rule: AlertRule) -> None:
        """Schedule alert escalation"""

        await asyncio.sleep(rule.escalation_time)

        # Check if alert is still active and not acknowledged
        if alert.id in self.active_alerts and not alert.acknowledged:
            alert.escalation_level += 1

            escalated_alert = Alert(
                id=f"{alert.id}_escalated_{alert.escalation_level}",
                timestamp=datetime.now(timezone.utc),
                severity=AlertSeverity.CRITICAL if alert.severity != AlertSeverity.EMERGENCY else AlertSeverity.EMERGENCY,
                category=alert.category,
                title=f"ESCALATED: {alert.title}",
                message=f"Alert not acknowledged after {rule.escalation_time} seconds. Original: {alert.message}",
                source=alert.source,
                metadata=alert.metadata,
                escalation_level=alert.escalation_level
            )

            # Send escalated notifications (usually to higher priority channels)
            escalated_rule = AlertRule(
                id=f"{rule.id}_escalated",
                name=f"Escalated {rule.name}",
                category=rule.category,
                severity=escalated_alert.severity,
                condition=rule.condition,
                threshold=rule.threshold,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS]  # Escalate to high-priority channels
            )

            await self._send_notifications(escalated_alert, escalated_rule)

            logger.warning(f"Alert escalated: {alert.title}")

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""

        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by

        logger.info(f"Alert acknowledged: {alert.title} by {acknowledged_by}")
        return True

    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""

        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_by = resolved_by

        # Remove from active alerts
        del self.active_alerts[alert_id]

        logger.info(f"Alert resolved: {alert.title} by {resolved_by}")
        return True

    def get_active_alerts(
        self,
        severity_filter: Optional[List[AlertSeverity]] = None,
        category_filter: Optional[List[AlertCategory]] = None
    ) -> List[Alert]:
        """Get currently active alerts with optional filtering"""

        alerts = list(self.active_alerts.values())

        if severity_filter:
            alerts = [alert for alert in alerts if alert.severity in severity_filter]

        if category_filter:
            alerts = [alert for alert in alerts if alert.category in category_filter]

        # Sort by severity and timestamp
        severity_order = {
            AlertSeverity.EMERGENCY: 4,
            AlertSeverity.CRITICAL: 3,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 1
        }

        alerts.sort(key=lambda a: (severity_order[a.severity], a.timestamp), reverse=True)

        return alerts

    def get_alert_statistics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get alert statistics for the specified period"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)

        period_alerts = [
            alert for alert in self.alert_history
            if start_time <= alert.timestamp <= end_time
        ]

        # Count by severity
        severity_counts = {severity.value: 0 for severity in AlertSeverity}
        for alert in period_alerts:
            severity_counts[alert.severity.value] += 1

        # Count by category
        category_counts = {category.value: 0 for category in AlertCategory}
        for alert in period_alerts:
            category_counts[alert.category.value] += 1

        # Calculate resolution metrics
        total_alerts = len(period_alerts)
        resolved_alerts = len([alert for alert in period_alerts if alert.resolved])
        acknowledged_alerts = len([alert for alert in period_alerts if alert.acknowledged])

        resolution_rate = (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
        acknowledgment_rate = (acknowledged_alerts / total_alerts * 100) if total_alerts > 0 else 0

        return {
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "total_alerts": total_alerts,
            "active_alerts": len(self.active_alerts),
            "resolved_alerts": resolved_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "resolution_rate": resolution_rate,
            "acknowledgment_rate": acknowledgment_rate,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "most_frequent_category": max(category_counts, key=category_counts.get) if category_counts else None,
            "avg_alerts_per_day": total_alerts / days_back if days_back > 0 else 0
        }

    def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule"""

        if rule_id not in self.alert_rules:
            return False

        rule = self.alert_rules[rule_id]

        # Update allowed fields
        allowed_fields = ["enabled", "threshold", "channels", "escalation_time", "suppression_time"]

        for field, value in updates.items():
            if field in allowed_fields and hasattr(rule, field):
                setattr(rule, field, value)

        logger.info(f"Updated alert rule: {rule_id}")
        return True

    def add_custom_alert_rule(self, rule: AlertRule) -> bool:
        """Add a custom alert rule"""

        if rule.id in self.alert_rules:
            logger.warning(f"Alert rule {rule.id} already exists")
            return False

        self.alert_rules[rule.id] = rule
        logger.info(f"Added custom alert rule: {rule.id}")
        return True

    def configure_notification_channel(
        self,
        channel: NotificationChannel,
        config: NotificationConfig
    ) -> None:
        """Configure a notification channel"""

        self.notification_configs[channel] = config
        logger.info(f"Configured notification channel: {channel.value}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get alert data for dashboard display"""

        active_alerts = self.get_active_alerts()
        stats = self.get_alert_statistics(days_back=1)  # Last 24 hours

        return {
            "active_alerts": [
                {
                    "id": alert.id,
                    "timestamp": alert.timestamp.isoformat(),
                    "severity": alert.severity.value,
                    "category": alert.category.value,
                    "title": alert.title,
                    "message": alert.message,
                    "acknowledged": alert.acknowledged,
                    "escalation_level": alert.escalation_level
                }
                for alert in active_alerts[:10]  # Last 10 alerts
            ],
            "alert_counts": {
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "warning": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                "info": len([a for a in active_alerts if a.severity == AlertSeverity.INFO]),
                "emergency": len([a for a in active_alerts if a.severity == AlertSeverity.EMERGENCY])
            },
            "statistics": stats,
            "notification_status": {
                channel.value: config.enabled
                for channel, config in self.notification_configs.items()
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }