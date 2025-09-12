"""
Error Coordinator - Centralized error handling and recovery system

Provides comprehensive error management, automatic recovery strategies,
alerting, and error pattern analysis for the ToolboxAI Roblox Environment.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import json
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import operator
import ast

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class RecoveryStatus(Enum):
    """Recovery attempt status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"


@dataclass
class ErrorRecord:
    """Comprehensive error record"""

    error_id: str
    error_type: str
    severity: ErrorSeverity
    message: str
    stack_trace: str
    component: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    recovery_attempts: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @property
    def age_minutes(self) -> float:
        """Get error age in minutes"""
        return (datetime.now() - self.timestamp).total_seconds() / 60


@dataclass
class RecoveryStrategy:
    """Error recovery strategy definition"""

    strategy_id: str
    name: str
    description: str
    applicable_errors: List[str]  # Error types this strategy can handle
    severity_threshold: ErrorSeverity
    auto_retry: bool
    max_attempts: int
    delay_seconds: int
    escalation_threshold: int  # Minutes before escalation
    recovery_function: Optional[Callable] = None


@dataclass
class AlertRule:
    """Alert rule definition"""

    rule_id: str
    name: str
    condition: str  # Python expression for alert condition
    severity_threshold: ErrorSeverity
    time_window_minutes: int
    max_occurrences: int
    notification_channels: List[str]  # email, slack, webhook
    enabled: bool = True


class ErrorCoordinator:
    """
    Centralized error handling and recovery coordinator.

    Handles:
    - Error collection and categorization
    - Automatic recovery strategies
    - Error pattern analysis
    - Alert and notification system
    - Error metrics and reporting
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Configuration
        self.max_error_history = self.config.get("max_error_history", 10000)
        self.enable_auto_recovery = self.config.get("enable_auto_recovery", True)
        self.enable_notifications = self.config.get("enable_notifications", True)
        self.notification_cooldown = self.config.get(
            "notification_cooldown", 300
        )  # 5 minutes

        # Email configuration
        self.smtp_server = self.config.get("smtp_server", "localhost")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.smtp_username = self.config.get("smtp_username")
        self.smtp_password = self.config.get("smtp_password")
        self.alert_email = self.config.get("alert_email")

        # Core state
        self.is_initialized = False
        self.error_history: deque = deque(maxlen=self.max_error_history)
        self.error_counts = defaultdict(int)
        self.error_patterns = defaultdict(list)

        # Recovery system
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self.active_recoveries: Dict[str, RecoveryStatus] = {}
        self.recovery_success_rates = defaultdict(float)

        # Alert system
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_history = deque(maxlen=1000)
        self.last_notification_times = defaultdict(datetime)

        # Component error tracking
        self.component_error_stats = defaultdict(
            lambda: {
                "total_errors": 0,
                "recent_errors": 0,
                "error_rate": 0.0,
                "last_error_time": None,
                "mean_time_between_errors": 0.0,
            }
        )

        # Background tasks
        self.pattern_analyzer_task = None
        self.alert_processor_task = None
        self.cleanup_task = None

        # FastAPI app
        self.app = FastAPI(title="Error Coordinator API", version="1.0.0")
        self._setup_routes()

        # Setup default recovery strategies and alerts
        self._setup_default_recovery_strategies()
        self._setup_default_alert_rules()

    async def initialize(self):
        """Initialize the error coordinator"""
        try:
            logger.info("Initializing Error Coordinator...")

            # Start background tasks
            self.pattern_analyzer_task = asyncio.create_task(self._pattern_analyzer())
            self.alert_processor_task = asyncio.create_task(self._alert_processor())
            self.cleanup_task = asyncio.create_task(self._cleanup_old_errors())

            self.is_initialized = True
            logger.info("Error Coordinator initialized successfully")

        except Exception as e:
            logger.error(f"Error Coordinator initialization failed: {e}")
            raise

    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies for common error types"""

        # Connection retry strategy
        self.recovery_strategies["connection_retry"] = RecoveryStrategy(
            strategy_id="connection_retry",
            name="Connection Retry",
            description="Retry failed connections with exponential backoff",
            applicable_errors=["connection_error", "timeout_error", "network_error"],
            severity_threshold=ErrorSeverity.WARNING,
            auto_retry=True,
            max_attempts=3,
            delay_seconds=5,
            escalation_threshold=10,
            recovery_function=self._recover_connection,
        )

        # Service restart strategy
        self.recovery_strategies["service_restart"] = RecoveryStrategy(
            strategy_id="service_restart",
            name="Service Restart",
            description="Restart failed services",
            applicable_errors=["service_crash", "initialization_error"],
            severity_threshold=ErrorSeverity.ERROR,
            auto_retry=True,
            max_attempts=2,
            delay_seconds=10,
            escalation_threshold=5,
            recovery_function=self._recover_service_restart,
        )

        # Resource cleanup strategy
        self.recovery_strategies["resource_cleanup"] = RecoveryStrategy(
            strategy_id="resource_cleanup",
            name="Resource Cleanup",
            description="Clean up leaked resources and retry",
            applicable_errors=["memory_error", "resource_exhaustion"],
            severity_threshold=ErrorSeverity.ERROR,
            auto_retry=True,
            max_attempts=1,
            delay_seconds=30,
            escalation_threshold=2,
            recovery_function=self._recover_resource_cleanup,
        )

        # API quota recovery
        self.recovery_strategies["api_quota_wait"] = RecoveryStrategy(
            strategy_id="api_quota_wait",
            name="API Quota Wait",
            description="Wait for API quota to reset",
            applicable_errors=["quota_exceeded", "rate_limit"],
            severity_threshold=ErrorSeverity.WARNING,
            auto_retry=True,
            max_attempts=5,
            delay_seconds=60,
            escalation_threshold=15,
            recovery_function=self._recover_api_quota,
        )

        # Data corruption recovery
        self.recovery_strategies["data_rollback"] = RecoveryStrategy(
            strategy_id="data_rollback",
            name="Data Rollback",
            description="Rollback to last known good state",
            applicable_errors=["data_corruption", "state_conflict"],
            severity_threshold=ErrorSeverity.ERROR,
            auto_retry=False,
            max_attempts=1,
            delay_seconds=0,
            escalation_threshold=1,
            recovery_function=self._recover_data_rollback,
        )

        logger.info(f"Loaded {len(self.recovery_strategies)} recovery strategies")

    def _setup_default_alert_rules(self):
        """Setup default alert rules for common scenarios"""

        # High error rate alert
        self.alert_rules["high_error_rate"] = AlertRule(
            rule_id="high_error_rate",
            name="High Error Rate",
            condition="error_rate > 0.1",  # 10% error rate
            severity_threshold=ErrorSeverity.WARNING,
            time_window_minutes=5,
            max_occurrences=10,
            notification_channels=["email", "log"],
        )

        # Critical error alert
        self.alert_rules["critical_errors"] = AlertRule(
            rule_id="critical_errors",
            name="Critical Errors",
            condition="severity >= 4",  # Critical or Fatal
            severity_threshold=ErrorSeverity.CRITICAL,
            time_window_minutes=1,
            max_occurrences=1,
            notification_channels=["email", "slack", "webhook"],
        )

        # Component failure alert
        self.alert_rules["component_failure"] = AlertRule(
            rule_id="component_failure",
            name="Component Failure",
            condition="component_errors > 5",
            severity_threshold=ErrorSeverity.ERROR,
            time_window_minutes=10,
            max_occurrences=5,
            notification_channels=["email"],
        )

        # Recovery failure alert
        self.alert_rules["recovery_failure"] = AlertRule(
            rule_id="recovery_failure",
            name="Recovery Failure",
            condition="recovery_attempts >= max_attempts",
            severity_threshold=ErrorSeverity.ERROR,
            time_window_minutes=30,
            max_occurrences=3,
            notification_channels=["email", "slack"],
        )

        logger.info(f"Loaded {len(self.alert_rules)} alert rules")

    async def handle_error(
        self,
        error_type: str,
        error: Union[Exception, str],
        context: Dict[str, Any],
        component: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        tags: List[str] = None,
    ) -> str:
        """
        Handle an error with comprehensive processing and recovery

        Args:
            error_type: Type/category of error
            error: Exception object or error message
            context: Additional context about the error
            component: Component where error occurred
            severity: Error severity level
            tags: Optional tags for categorization

        Returns:
            Error ID for tracking
        """
        error_id = str(uuid.uuid4())

        # Extract error information
        if isinstance(error, Exception):
            message = str(error)
            stack_trace = traceback.format_exc()
        else:
            message = str(error)
            stack_trace = ""

        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            message=message,
            stack_trace=stack_trace,
            component=component,
            context=context,
            tags=tags or [],
        )

        # Store error
        self.error_history.append(error_record)
        self.error_counts[error_type] += 1

        # Update component error stats
        await self._update_component_error_stats(component, error_record)

        # Log error
        log_level = {
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.FATAL: logging.CRITICAL,
        }[severity]

        logger.log(log_level, f"Error {error_id} in {component}: {message}")

        # Attempt automatic recovery
        if self.enable_auto_recovery and severity != ErrorSeverity.FATAL:
            asyncio.create_task(self._attempt_recovery(error_record))

        # Check alert rules
        await self._check_alert_rules(error_record)

        # Update error patterns
        self.error_patterns[error_type].append(
            {
                "timestamp": error_record.timestamp,
                "component": component,
                "context": context,
            }
        )

        return error_id

    async def _update_component_error_stats(
        self, component: str, error_record: ErrorRecord
    ):
        """Update error statistics for a component"""
        stats = self.component_error_stats[component]

        stats["total_errors"] += 1
        stats["last_error_time"] = error_record.timestamp

        # Calculate recent error count (last hour)
        recent_threshold = datetime.now() - timedelta(hours=1)
        recent_errors = [
            err
            for err in self.error_history
            if err.component == component and err.timestamp > recent_threshold
        ]
        stats["recent_errors"] = len(recent_errors)

        # Calculate error rate (errors per hour)
        if stats["total_errors"] > 1:
            time_span_hours = (
                error_record.timestamp - self.error_history[0].timestamp
            ).total_seconds() / 3600
            stats["error_rate"] = stats["total_errors"] / max(time_span_hours, 1)

        # Calculate mean time between errors
        component_errors = [
            err for err in self.error_history if err.component == component
        ]
        if len(component_errors) > 1:
            time_diffs = []
            for i in range(1, len(component_errors)):
                diff = (
                    component_errors[i].timestamp - component_errors[i - 1].timestamp
                ).total_seconds()
                time_diffs.append(diff)
            stats["mean_time_between_errors"] = sum(time_diffs) / len(time_diffs)

    async def _attempt_recovery(self, error_record: ErrorRecord):
        """Attempt automatic recovery for an error"""
        recovery_id = f"{error_record.error_id}_recovery"

        try:
            # Find applicable recovery strategies
            applicable_strategies = [
                strategy
                for strategy in self.recovery_strategies.values()
                if (
                    error_record.error_type in strategy.applicable_errors
                    and error_record.severity.value >= strategy.severity_threshold.value
                )
            ]

            if not applicable_strategies:
                logger.info(
                    f"No recovery strategies found for error {error_record.error_id}"
                )
                return

            # Try strategies in order of priority
            for strategy in applicable_strategies:
                if not strategy.auto_retry:
                    continue

                self.active_recoveries[recovery_id] = RecoveryStatus.IN_PROGRESS

                logger.info(
                    f"Attempting recovery using {strategy.name} for error {error_record.error_id}"
                )

                # Execute recovery with retry logic
                success = await self._execute_recovery_strategy(strategy, error_record)

                if success:
                    self.active_recoveries[recovery_id] = RecoveryStatus.SUCCESS
                    error_record.resolved = True
                    error_record.resolution_time = datetime.now()

                    # Update success rate
                    self.recovery_success_rates[strategy.strategy_id] = (
                        self.recovery_success_rates[strategy.strategy_id] * 0.9 + 0.1
                    )

                    logger.info(
                        f"Recovery successful for error {error_record.error_id}"
                    )

                    # Publish recovery event
                    await self._publish_recovery_event(error_record, strategy, True)

                    break
                else:
                    # Record failed attempt
                    error_record.recovery_attempts.append(
                        {
                            "strategy": strategy.strategy_id,
                            "timestamp": datetime.now().isoformat(),
                            "success": False,
                        }
                    )

                    # Update success rate
                    self.recovery_success_rates[strategy.strategy_id] = (
                        self.recovery_success_rates[strategy.strategy_id] * 0.9
                    )

            # Mark as requiring manual intervention if all strategies failed
            if not error_record.resolved:
                self.active_recoveries[recovery_id] = RecoveryStatus.MANUAL_REQUIRED

                # Check for escalation
                if error_record.age_minutes > min(
                    s.escalation_threshold for s in applicable_strategies
                ):
                    await self._escalate_error(error_record)

        except Exception as e:
            logger.error(
                f"Recovery attempt failed for error {error_record.error_id}: {e}"
            )
            self.active_recoveries[recovery_id] = RecoveryStatus.FAILED

    async def _execute_recovery_strategy(
        self, strategy: RecoveryStrategy, error_record: ErrorRecord
    ) -> bool:
        """Execute a specific recovery strategy"""

        for attempt in range(strategy.max_attempts):
            try:
                if strategy.recovery_function:
                    # Execute custom recovery function
                    success = await strategy.recovery_function(error_record, attempt)
                    if success:
                        return True
                else:
                    # Use built-in recovery logic
                    success = await self._default_recovery(
                        strategy, error_record, attempt
                    )
                    if success:
                        return True

                # Wait before retry
                if attempt < strategy.max_attempts - 1:
                    delay = strategy.delay_seconds * (2**attempt)  # Exponential backoff
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Recovery attempt {attempt + 1} failed: {e}")

        return False

    async def _default_recovery(
        self, strategy: RecoveryStrategy, error_record: ErrorRecord, attempt: int
    ) -> bool:
        """Default recovery logic for common error types"""

        if strategy.strategy_id == "connection_retry":
            return await self._recover_connection(error_record, attempt)
        elif strategy.strategy_id == "service_restart":
            return await self._recover_service_restart(error_record, attempt)
        elif strategy.strategy_id == "resource_cleanup":
            return await self._recover_resource_cleanup(error_record, attempt)
        elif strategy.strategy_id == "api_quota_wait":
            return await self._recover_api_quota(error_record, attempt)
        elif strategy.strategy_id == "data_rollback":
            return await self._recover_data_rollback(error_record, attempt)

        return False

    async def _recover_connection(
        self, error_record: ErrorRecord, attempt: int
    ) -> bool:
        """Recover connection-related errors"""
        try:
            component = error_record.component

            # Try to reconnect component
            if component == "mcp_client":
                from ..mcp.client import MCPClient

                client = MCPClient()
                await client.reconnect()
                return True

            elif component == "database":
                # Reinitialize database connection
                from core.database.connection_manager import get_session
                
                # Test database connection
                try:
                    with get_session("education") as session:
                        # Simple connectivity test
                        session.execute("SELECT 1")
                    return True
                except Exception:
                    return False

            return False

        except Exception as e:
            logger.error(f"Connection recovery failed: {e}")
            return False

    async def _recover_service_restart(
        self, error_record: ErrorRecord, attempt: int
    ) -> bool:
        """Recover by restarting services"""
        try:
            component = error_record.component

            # Restart specific services
            if component == "agent_system":
                from ..agents.orchestrator import AgentOrchestrator

                orchestrator = AgentOrchestrator()
                await orchestrator.restart()
                return True

            elif component == "swarm_controller":
                from ..swarm.swarm_controller import SwarmController

                controller = SwarmController()
                await controller.restart()
                return True

            return False

        except Exception as e:
            logger.error(f"Service restart recovery failed: {e}")
            return False

    async def _recover_resource_cleanup(
        self, error_record: ErrorRecord, attempt: int
    ) -> bool:
        """Recover by cleaning up resources"""
        try:
            # Force garbage collection
            import gc

            gc.collect()

            # Clean up resource allocations if resource coordinator is available
            from . import get_coordinator_system

            try:
                system = get_coordinator_system()
                resource_coordinator = system.get_resource_coordinator()

                # Release any expired allocations
                await resource_coordinator._cleanup_expired_allocations()
                return True

            except Exception:
                pass

            return False

        except Exception as e:
            logger.error(f"Resource cleanup recovery failed: {e}")
            return False

    async def _recover_api_quota(self, error_record: ErrorRecord, attempt: int) -> bool:
        """Recover from API quota exhaustion"""
        try:
            # Wait for quota reset (already handled by delay_seconds in strategy)
            # Just return True to indicate we should retry after waiting
            return True

        except Exception as e:
            logger.error(f"API quota recovery failed: {e}")
            return False

    async def _recover_data_rollback(
        self, error_record: ErrorRecord, attempt: int
    ) -> bool:
        """Recover by rolling back to previous state"""
        try:
            component = error_record.component

            # Use sync coordinator to rollback if available
            from . import get_coordinator_system

            try:
                system = get_coordinator_system()
                sync_coordinator = system.get_sync_coordinator()

                # Rollback to previous version
                current_state = await sync_coordinator.get_component_state(component)
                if current_state and current_state.version > 1:
                    success = await sync_coordinator.rollback_component_state(
                        component, current_state.version - 1
                    )
                    return success

            except Exception:
                pass

            return False

        except Exception as e:
            logger.error(f"Data rollback recovery failed: {e}")
            return False

    async def _check_alert_rules(self, error_record: ErrorRecord):
        """Check if error triggers any alert rules"""

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            # Check severity threshold
            if error_record.severity.value < rule.severity_threshold.value:
                continue

            # Check time window
            time_threshold = datetime.now() - timedelta(
                minutes=rule.time_window_minutes
            )
            recent_errors = [
                err for err in self.error_history if err.timestamp > time_threshold
            ]

            # Evaluate condition
            context = {
                "error_rate": len(recent_errors) / rule.time_window_minutes,
                "severity": error_record.severity.value,
                "component_errors": len(
                    [e for e in recent_errors if e.component == error_record.component]
                ),
                "total_errors": len(recent_errors),
                "recovery_attempts": len(error_record.recovery_attempts),
            }

            try:
                if self._evaluate_condition_safely(rule.condition, context):
                    await self._trigger_alert(rule, error_record, context)
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                logger.error(f"Alert rule evaluation failed for {rule.rule_id}: {e}")

    def _evaluate_condition_safely(
        self, condition: str, context: Dict[str, Any]
    ) -> bool:
        """Safely evaluate a condition without using ast.literal_eval()"""
        # Define allowed operators for safe evaluation
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: operator.and_,
            ast.Or: operator.or_,
            ast.Not: operator.not_,
        }

        def safe_eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                if node.id in context:
                    return context[node.id]
                raise ValueError(f"Unknown variable: {node.id}")
            elif isinstance(node, ast.BinOp):
                op = allowed_operators.get(type(node.op))
                if op:
                    return op(safe_eval(node.left), safe_eval(node.right))
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            elif isinstance(node, ast.Compare):
                left = safe_eval(node.left)
                for op, comparator in zip(node.ops, node.comparators):
                    op_func = allowed_operators.get(type(op))
                    if not op_func:
                        raise ValueError(f"Unsupported comparison: {type(op).__name__}")
                    right = safe_eval(comparator)
                    if not op_func(left, right):
                        return False
                    left = right
                return True
            elif isinstance(node, ast.BoolOp):
                op = allowed_operators.get(type(node.op))
                if op:
                    values = [safe_eval(value) for value in node.values]
                    if isinstance(node.op, ast.And):
                        return all(values)
                    elif isinstance(node.op, ast.Or):
                        return any(values)
                raise ValueError(
                    f"Unsupported boolean operator: {type(node.op).__name__}"
                )
            elif isinstance(node, ast.UnaryOp):
                op = allowed_operators.get(type(node.op))
                if op:
                    return op(safe_eval(node.operand))
                raise ValueError(
                    f"Unsupported unary operator: {type(node.op).__name__}"
                )
            else:
                raise ValueError(f"Unsupported expression type: {type(node).__name__}")

        try:
            tree = ast.parse(condition, mode="eval")
            return bool(safe_eval(tree.body))
        except (SyntaxError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid condition expression: {e}")

    async def _trigger_alert(
        self, rule: AlertRule, error_record: ErrorRecord, context: Dict[str, Any]
    ):
        """Trigger an alert based on rule"""

        # Check notification cooldown
        last_notification = self.last_notification_times.get(rule.rule_id)
        if last_notification and datetime.now() - last_notification < timedelta(
            seconds=self.notification_cooldown
        ):
            return

        # Create alert message
        alert_message = f"""
        Alert: {rule.name}
        
        Error ID: {error_record.error_id}
        Component: {error_record.component}
        Error Type: {error_record.error_type}
        Severity: {error_record.severity.value}
        Message: {error_record.message}
        
        Context: {json.dumps(context, indent=2)}
        
        Time: {error_record.timestamp.isoformat()}
        """

        # Send notifications
        for channel in rule.notification_channels:
            try:
                if channel == "email" and self.enable_notifications:
                    await self._send_email_alert(rule.name, alert_message)
                elif channel == "log":
                    logger.critical(f"ALERT: {rule.name} - {alert_message}")
                elif channel == "slack":
                    await self._send_slack_alert(rule.name, alert_message)
                elif channel == "webhook":
                    await self._send_webhook_alert(
                        rule.name, alert_message, error_record
                    )

            except Exception as e:
                logger.error(f"Failed to send {channel} alert: {e}")

        # Record notification
        self.notification_history.append(
            {
                "rule_id": rule.rule_id,
                "error_id": error_record.error_id,
                "timestamp": datetime.now().isoformat(),
                "channels": rule.notification_channels,
            }
        )

        self.last_notification_times[rule.rule_id] = datetime.now()

    async def _send_email_alert(self, subject: str, message: str):
        """Send email alert"""
        if not self.alert_email or not self.smtp_username:
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_username
            msg["To"] = self.alert_email
            msg["Subject"] = f"ToolboxAI Alert: {subject}"

            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email alert sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_slack_alert(self, title: str, message: str):
        """Send Slack alert (placeholder)"""
        # Implementation would depend on Slack webhook configuration
        logger.info(f"Slack alert (not implemented): {title}")

    async def _send_webhook_alert(
        self, title: str, message: str, error_record: ErrorRecord
    ):
        """Send webhook alert"""
        # Implementation would depend on webhook configuration
        logger.info(f"Webhook alert (not implemented): {title}")

    async def _escalate_error(self, error_record: ErrorRecord):
        """Escalate unresolved error"""
        logger.critical(f"Escalating unresolved error {error_record.error_id}")

        # Create escalation alert
        escalation_message = f"""
        ESCALATION: Unresolved error requiring manual intervention
        
        Error ID: {error_record.error_id}
        Component: {error_record.component}
        Error Type: {error_record.error_type}
        Age: {error_record.age_minutes:.1f} minutes
        Recovery Attempts: {len(error_record.recovery_attempts)}
        
        Message: {error_record.message}
        Context: {json.dumps(error_record.context, indent=2)}
        """

        if self.enable_notifications and self.alert_email:
            await self._send_email_alert("ESCALATION REQUIRED", escalation_message)

    async def _publish_recovery_event(
        self, error_record: ErrorRecord, strategy: RecoveryStrategy, success: bool
    ):
        """Publish recovery event for system-wide notification"""
        from . import get_coordinator_system

        try:
            system = get_coordinator_system()
            sync_coordinator = system.get_sync_coordinator()

            await sync_coordinator.publish_event(
                event_type="error_recovery",
                source="error_coordinator",
                data={
                    "error_id": error_record.error_id,
                    "strategy": strategy.strategy_id,
                    "success": success,
                    "component": error_record.component,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish recovery event: {e}")

    async def _pattern_analyzer(self):
        """Background task to analyze error patterns"""
        while self.is_initialized:
            try:
                await asyncio.sleep(3600)  # Analyze every hour

                # Analyze error patterns
                patterns = await self._analyze_error_patterns()

                # Generate insights
                insights = await self._generate_error_insights(patterns)

                if insights:
                    logger.info(f"Error pattern insights: {insights}")

            except Exception as e:
                logger.error(f"Pattern analyzer error: {e}")

    async def _analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns for insights"""
        analysis = {}

        # Time-based pattern analysis
        hourly_errors = defaultdict(int)
        for error in self.error_history:
            hour = error.timestamp.hour
            hourly_errors[hour] += 1

        analysis["hourly_distribution"] = dict(hourly_errors)

        # Component error analysis
        component_errors = defaultdict(int)
        for error in self.error_history:
            component_errors[error.component] += 1

        analysis["component_distribution"] = dict(component_errors)

        # Error type frequency
        error_type_freq = defaultdict(int)
        for error in self.error_history:
            error_type_freq[error.error_type] += 1

        analysis["error_type_frequency"] = dict(error_type_freq)

        # Recent trend analysis
        recent_threshold = datetime.now() - timedelta(hours=24)
        recent_errors = [
            err for err in self.error_history if err.timestamp > recent_threshold
        ]

        analysis["recent_trend"] = {
            "total_recent_errors": len(recent_errors),
            "error_rate_per_hour": len(recent_errors) / 24,
            "most_common_recent": max(
                (err.error_type for err in recent_errors),
                key=lambda x: sum(1 for e in recent_errors if e.error_type == x),
                default=None,
            ),
        }

        return analysis

    async def _generate_error_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from error patterns"""
        insights = []

        # High error rate insight
        if patterns["recent_trend"]["error_rate_per_hour"] > 5:
            insights.append("High error rate detected - consider system health review")

        # Component-specific insights
        component_dist = patterns["component_distribution"]
        if component_dist:
            most_errors_component = max(component_dist, key=component_dist.get)
            if component_dist[most_errors_component] > len(self.error_history) * 0.3:
                insights.append(
                    f"Component {most_errors_component} has disproportionate error rate"
                )

        # Time-based insights
        hourly_dist = patterns["hourly_distribution"]
        if hourly_dist:
            peak_hour = max(hourly_dist, key=hourly_dist.get)
            if hourly_dist[peak_hour] > sum(hourly_dist.values()) * 0.2:
                insights.append(f"Error spike detected at hour {peak_hour}")

        return insights

    async def _alert_processor(self):
        """Background task to process alerts and notifications"""
        while self.is_initialized:
            try:
                await asyncio.sleep(60)  # Process every minute

                # Check for alert conditions
                for rule in self.alert_rules.values():
                    if rule.enabled:
                        await self._evaluate_alert_rule(rule)

            except Exception as e:
                logger.error(f"Alert processor error: {e}")

    async def _evaluate_alert_rule(self, rule: AlertRule):
        """Evaluate a specific alert rule"""
        try:
            time_threshold = datetime.now() - timedelta(
                minutes=rule.time_window_minutes
            )
            recent_errors = [
                err
                for err in self.error_history
                if err.timestamp > time_threshold
                and err.severity.value >= rule.severity_threshold.value
            ]

            if len(recent_errors) >= rule.max_occurrences:
                # Rule triggered
                context = {
                    "rule_id": rule.rule_id,
                    "triggered_errors": len(recent_errors),
                    "time_window": rule.time_window_minutes,
                    "threshold": rule.max_occurrences,
                }

                # Create synthetic error for alert
                alert_error = ErrorRecord(
                    error_id=str(uuid.uuid4()),
                    error_type="alert_triggered",
                    severity=rule.severity_threshold,
                    message=f"Alert rule {rule.name} triggered",
                    stack_trace="",
                    component="error_coordinator",
                    context=context,
                    tags=["alert", rule.rule_id],
                )

                await self._trigger_alert(rule, alert_error, context)

        except Exception as e:
            logger.error(f"Alert rule evaluation failed for {rule.rule_id}: {e}")

    async def _cleanup_old_errors(self):
        """Background task to cleanup old error data"""
        while self.is_initialized:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour

                # Clean up old notifications
                cutoff_time = datetime.now() - timedelta(days=7)

                old_notifications = [
                    notif
                    for notif in self.notification_history
                    if datetime.fromisoformat(notif["timestamp"]) < cutoff_time
                ]

                for notification in old_notifications:
                    self.notification_history.remove(notification)

                # Clean up resolved recovery attempts
                resolved_recoveries = [
                    recovery_id
                    for recovery_id, status in self.active_recoveries.items()
                    if status in [RecoveryStatus.SUCCESS, RecoveryStatus.FAILED]
                ]

                for recovery_id in resolved_recoveries:
                    del self.active_recoveries[recovery_id]

                if old_notifications or resolved_recoveries:
                    logger.info(
                        f"Cleaned up {len(old_notifications)} old notifications and {len(resolved_recoveries)} old recoveries"
                    )

            except Exception as e:
                logger.error(f"Cleanup task error: {e}")

    async def get_error_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error summary for specified time window"""
        time_threshold = datetime.now() - timedelta(hours=time_window_hours)
        recent_errors = [
            err for err in self.error_history if err.timestamp > time_threshold
        ]

        # Severity breakdown
        severity_counts = defaultdict(int)
        for error in recent_errors:
            severity_counts[error.severity.value] += 1

        # Component breakdown
        component_counts = defaultdict(int)
        for error in recent_errors:
            component_counts[error.component] += 1

        # Error type breakdown
        type_counts = defaultdict(int)
        for error in recent_errors:
            type_counts[error.error_type] += 1

        # Resolution stats
        resolved_errors = len([err for err in recent_errors if err.resolved])
        resolution_rate = (
            (resolved_errors / len(recent_errors) * 100) if recent_errors else 0
        )

        return {
            "time_window_hours": time_window_hours,
            "total_errors": len(recent_errors),
            "resolution_rate": resolution_rate,
            "severity_breakdown": dict(severity_counts),
            "component_breakdown": dict(component_counts),
            "error_type_breakdown": dict(type_counts),
            "recovery_stats": {
                "active_recoveries": len(self.active_recoveries),
                "success_rates": dict(self.recovery_success_rates),
            },
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get error coordinator metrics"""
        error_summary = await self.get_error_summary()

        return {
            "error_summary": error_summary,
            "system_stats": {
                "total_errors_tracked": len(self.error_history),
                "error_types_seen": len(self.error_counts),
                "components_with_errors": len(self.component_error_stats),
                "recovery_strategies": len(self.recovery_strategies),
                "alert_rules": len(self.alert_rules),
            },
            "component_error_stats": dict(self.component_error_stats),
            "recent_patterns": await self._analyze_error_patterns(),
        }

    async def get_health(self) -> Dict[str, Any]:
        """Get error coordinator health status"""
        try:
            # Check recent error rate
            recent_errors = await self.get_error_summary(1)  # Last hour
            error_rate = recent_errors["total_errors"]

            # Determine health status
            if error_rate == 0:
                status = "healthy"
            elif error_rate < 5:
                status = "healthy"
            elif error_rate < 20:
                status = "degraded"
            else:
                status = "unhealthy"

            # Check background tasks
            background_tasks_healthy = all(
                [
                    self.pattern_analyzer_task
                    and not self.pattern_analyzer_task.done(),
                    self.alert_processor_task and not self.alert_processor_task.done(),
                    self.cleanup_task and not self.cleanup_task.done(),
                ]
            )

            if not background_tasks_healthy:
                status = "degraded"

            return {
                "status": status,
                "recent_error_rate": error_rate,
                "resolution_rate": recent_errors["resolution_rate"],
                "active_recoveries": len(self.active_recoveries),
                "background_tasks_healthy": background_tasks_healthy,
                "notification_system_enabled": self.enable_notifications,
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    def _setup_routes(self):
        """Setup FastAPI routes for error management"""

        @self.app.post("/errors")
        async def handle_error_endpoint(request: dict):
            """Handle error via REST API"""
            error_id = await self.handle_error(
                error_type=request["error_type"],
                error=request["error"],
                context=request["context"],
                component=request.get("component", "unknown"),
                severity=ErrorSeverity(request.get("severity", "error")),
                tags=request.get("tags", []),
            )
            return {"error_id": error_id}

        @self.app.get("/errors/{error_id}")
        async def get_error_endpoint(error_id: str):
            """Get specific error details"""
            for error in self.error_history:
                if error.error_id == error_id:
                    return asdict(error)
            raise HTTPException(status_code=404, detail="Error not found")

        @self.app.get("/errors")
        async def list_errors_endpoint(
            component: Optional[str] = None,
            error_type: Optional[str] = None,
            severity: Optional[str] = None,
            limit: int = 100,
        ):
            """List errors with optional filtering"""
            filtered_errors = list(self.error_history)

            if component:
                filtered_errors = [
                    e for e in filtered_errors if e.component == component
                ]
            if error_type:
                filtered_errors = [
                    e for e in filtered_errors if e.error_type == error_type
                ]
            if severity:
                filtered_errors = [
                    e for e in filtered_errors if e.severity.value == severity
                ]

            # Return most recent errors first
            return [asdict(error) for error in filtered_errors[-limit:]][::-1]

        @self.app.get("/summary")
        async def error_summary_endpoint(hours: int = 24):
            """Get error summary"""
            return await self.get_error_summary(hours)

        @self.app.post("/recovery/{error_id}")
        async def manual_recovery_endpoint(error_id: str, request: dict):
            """Trigger manual recovery for an error"""
            for error in self.error_history:
                if error.error_id == error_id:
                    strategy_id = request["strategy_id"]
                    if strategy_id in self.recovery_strategies:
                        strategy = self.recovery_strategies[strategy_id]
                        success = await self._execute_recovery_strategy(strategy, error)
                        return {"success": success}
                    else:
                        raise HTTPException(
                            status_code=400, detail="Unknown recovery strategy"
                        )

            raise HTTPException(status_code=404, detail="Error not found")

        @self.app.get("/strategies")
        async def list_strategies_endpoint():
            """List available recovery strategies"""
            return {
                strategy_id: {
                    "name": strategy.name,
                    "description": strategy.description,
                    "applicable_errors": strategy.applicable_errors,
                    "success_rate": self.recovery_success_rates.get(strategy_id, 0),
                }
                for strategy_id, strategy in self.recovery_strategies.items()
            }

        @self.app.get("/alerts")
        async def list_alerts_endpoint():
            """List alert rules and recent notifications"""
            return {
                "rules": {
                    rule_id: {
                        "name": rule.name,
                        "condition": rule.condition,
                        "enabled": rule.enabled,
                        "severity_threshold": rule.severity_threshold.value,
                    }
                    for rule_id, rule in self.alert_rules.items()
                },
                "recent_notifications": list(self.notification_history)[-20:],
            }

        @self.app.get("/metrics")
        async def metrics_endpoint():
            """Get error metrics"""
            return await self.get_metrics()

        @self.app.get("/health")
        async def health_endpoint():
            """Health check"""
            return await self.get_health()

    async def shutdown(self):
        """Gracefully shutdown error coordinator"""
        try:
            logger.info("Shutting down Error Coordinator...")

            # Cancel background tasks
            if self.pattern_analyzer_task:
                self.pattern_analyzer_task.cancel()
            if self.alert_processor_task:
                self.alert_processor_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()

            self.is_initialized = False
            logger.info("Error Coordinator shutdown complete")

        except Exception as e:
            logger.error(f"Error during Error Coordinator shutdown: {e}")


# Custom exception classes
class RecoveryError(Exception):
    """Exception raised when error recovery fails"""

    pass


class AlertError(Exception):
    """Exception raised when alert processing fails"""

    pass


# Convenience functions
async def create_error_coordinator(**kwargs) -> ErrorCoordinator:
    """Create and initialize an error coordinator instance"""
    coordinator = ErrorCoordinator(**kwargs)
    await coordinator.initialize()
    return coordinator
