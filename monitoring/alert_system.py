#!/usr/bin/env python3
"""
Real-time Alert System for Phase 1 Monitoring
Detects blockers, regressions, and critical issues requiring immediate attention
"""

import json
import time
import datetime
import smtplib
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import queue
import subprocess
import requests
import logging

@dataclass
class Alert:
    id: str
    timestamp: datetime.datetime
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "test", "security", "performance", "system"
    title: str
    description: str
    metric_value: float
    threshold: float
    trend: str  # "increasing", "decreasing", "stable"
    action_required: str
    auto_resolve: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime.datetime] = None

@dataclass
class AlertRule:
    name: str
    category: str
    severity: str
    condition: str  # "greater_than", "less_than", "equals", "contains"
    threshold: float
    metric_path: str  # JSON path to metric
    duration_minutes: int = 5  # How long condition must persist
    cooldown_minutes: int = 30  # Minimum time between same alerts
    auto_resolve: bool = False
    enabled: bool = True

class AlertSystem:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.db_path = self.project_root / "monitoring" / "alerts.db"
        self.config_path = self.project_root / "monitoring" / "alert_config.json"
        self.alert_queue = queue.Queue()
        self.active_alerts = {}
        self.alert_history = []
        self.notification_handlers = []
        self.running = False

        self.init_database()
        self.load_alert_rules()
        self.setup_logging()

    def init_database(self):
        """Initialize SQLite database for alert tracking"""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    severity TEXT,
                    category TEXT,
                    title TEXT,
                    description TEXT,
                    metric_value REAL,
                    threshold REAL,
                    trend TEXT,
                    action_required TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_time DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    name TEXT PRIMARY KEY,
                    category TEXT,
                    severity TEXT,
                    condition_type TEXT,
                    threshold REAL,
                    metric_path TEXT,
                    duration_minutes INTEGER,
                    cooldown_minutes INTEGER,
                    auto_resolve BOOLEAN,
                    enabled BOOLEAN
                )
            """)

    def setup_logging(self):
        """Setup logging for alert system"""
        log_file = self.project_root / "monitoring" / "alerts.log"
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_alert_rules(self):
        """Load alert rules from configuration"""
        default_rules = [
            # Test Infrastructure Alerts
            AlertRule(
                name="test_pass_rate_critical",
                category="test",
                severity="critical",
                condition="less_than",
                threshold=70.0,
                metric_path="test_pass_rate",
                duration_minutes=5,
                cooldown_minutes=15
            ),
            AlertRule(
                name="test_pass_rate_declining",
                category="test",
                severity="high",
                condition="less_than",
                threshold=80.0,
                metric_path="test_pass_rate",
                duration_minutes=10,
                cooldown_minutes=30
            ),
            AlertRule(
                name="test_failures_spike",
                category="test",
                severity="high",
                condition="greater_than",
                threshold=50,
                metric_path="failing_tests",
                duration_minutes=3,
                cooldown_minutes=20
            ),

            # Security Alerts
            AlertRule(
                name="critical_security_issues",
                category="security",
                severity="critical",
                condition="greater_than",
                threshold=0,
                metric_path="critical_issues",
                duration_minutes=1,
                cooldown_minutes=60
            ),
            AlertRule(
                name="security_score_declining",
                category="security",
                severity="medium",
                condition="less_than",
                threshold=85.0,
                metric_path="security_score",
                duration_minutes=15,
                cooldown_minutes=60
            ),

            # Performance Alerts
            AlertRule(
                name="bundle_size_critical",
                category="performance",
                severity="high",
                condition="greater_than",
                threshold=1000.0,
                metric_path="bundle_size_kb",
                duration_minutes=5,
                cooldown_minutes=30
            ),
            AlertRule(
                name="api_latency_high",
                category="performance",
                severity="medium",
                condition="greater_than",
                threshold=500.0,
                metric_path="api_latency_ms",
                duration_minutes=10,
                cooldown_minutes=20
            ),
            AlertRule(
                name="error_rate_spike",
                category="performance",
                severity="high",
                condition="greater_than",
                threshold=0.05,
                metric_path="error_rate",
                duration_minutes=5,
                cooldown_minutes=15
            ),

            # System Alerts
            AlertRule(
                name="memory_usage_critical",
                category="system",
                severity="critical",
                condition="greater_than",
                threshold=4096.0,
                metric_path="memory_usage_mb",
                duration_minutes=5,
                cooldown_minutes=20
            ),
            AlertRule(
                name="cpu_usage_high",
                category="system",
                severity="medium",
                condition="greater_than",
                threshold=90.0,
                metric_path="cpu_utilization",
                duration_minutes=10,
                cooldown_minutes=30
            ),

            # Progress Alerts
            AlertRule(
                name="progress_stalled",
                category="progress",
                severity="high",
                condition="less_than",
                threshold=2.0,
                metric_path="progress_rate_per_hour",
                duration_minutes=60,
                cooldown_minutes=120
            ),
            AlertRule(
                name="deadline_risk",
                category="progress",
                severity="critical",
                condition="greater_than",
                threshold=40.0,
                metric_path="elapsed_hours",
                duration_minutes=5,
                cooldown_minutes=180
            )
        ]

        # Load from config file if exists, otherwise use defaults
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    self.alert_rules = [AlertRule(**rule) for rule in config_data.get('rules', [])]
            except Exception as e:
                self.logger.warning(f"Failed to load alert config: {e}, using defaults")
                self.alert_rules = default_rules
        else:
            self.alert_rules = default_rules
            self.save_alert_rules()

    def save_alert_rules(self):
        """Save alert rules to configuration file"""
        config_data = {
            'rules': [asdict(rule) for rule in self.alert_rules],
            'last_updated': datetime.datetime.now().isoformat()
        }

        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Add a notification handler function"""
        self.notification_handlers.append(handler)

    def evaluate_metrics(self, metrics_data: Dict):
        """Evaluate metrics against alert rules"""
        current_time = datetime.datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            try:
                metric_value = self.extract_metric_value(metrics_data, rule.metric_path)
                if metric_value is None:
                    continue

                alert_triggered = self.check_alert_condition(rule, metric_value)

                if alert_triggered:
                    alert_id = f"{rule.name}_{int(current_time.timestamp())}"

                    # Check cooldown period
                    if self.is_in_cooldown(rule.name, current_time, rule.cooldown_minutes):
                        continue

                    # Create alert
                    alert = Alert(
                        id=alert_id,
                        timestamp=current_time,
                        severity=rule.severity,
                        category=rule.category,
                        title=self.generate_alert_title(rule, metric_value),
                        description=self.generate_alert_description(rule, metric_value),
                        metric_value=metric_value,
                        threshold=rule.threshold,
                        trend=self.calculate_trend(rule.metric_path, metric_value),
                        action_required=self.generate_action_required(rule, metric_value),
                        auto_resolve=rule.auto_resolve
                    )

                    self.trigger_alert(alert)

                elif rule.auto_resolve:
                    # Check if we should auto-resolve existing alerts
                    self.auto_resolve_alerts(rule.name)

            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.name}: {e}")

    def extract_metric_value(self, data: Dict, path: str) -> Optional[float]:
        """Extract metric value from nested dictionary using path"""
        try:
            value = data
            for key in path.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None

            return float(value) if value is not None else None
        except (ValueError, TypeError, KeyError):
            return None

    def check_alert_condition(self, rule: AlertRule, value: float) -> bool:
        """Check if alert condition is met"""
        if rule.condition == "greater_than":
            return value > rule.threshold
        elif rule.condition == "less_than":
            return value < rule.threshold
        elif rule.condition == "equals":
            return abs(value - rule.threshold) < 0.001
        elif rule.condition == "not_equals":
            return abs(value - rule.threshold) >= 0.001
        else:
            return False

    def is_in_cooldown(self, rule_name: str, current_time: datetime.datetime, cooldown_minutes: int) -> bool:
        """Check if alert is in cooldown period"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT MAX(timestamp) FROM alerts
                    WHERE title LIKE ? AND timestamp > ?
                """, (
                    f"%{rule_name}%",
                    (current_time - datetime.timedelta(minutes=cooldown_minutes)).isoformat()
                ))

                result = cursor.fetchone()
                return result[0] is not None
        except Exception:
            return False

    def calculate_trend(self, metric_path: str, current_value: float) -> str:
        """Calculate trend for metric based on recent history"""
        try:
            # Get recent values from database or history
            # For now, return stable as default
            return "stable"
        except Exception:
            return "unknown"

    def generate_alert_title(self, rule: AlertRule, value: float) -> str:
        """Generate human-readable alert title"""
        titles = {
            "test_pass_rate_critical": f"CRITICAL: Test pass rate dropped to {value:.1f}%",
            "test_pass_rate_declining": f"Test pass rate declining: {value:.1f}%",
            "test_failures_spike": f"Test failures spiked to {value:.0f}",
            "critical_security_issues": f"CRITICAL: {value:.0f} critical security issues detected",
            "security_score_declining": f"Security score declined to {value:.1f}%",
            "bundle_size_critical": f"Bundle size critical: {value:.0f}KB",
            "api_latency_high": f"API latency high: {value:.0f}ms",
            "error_rate_spike": f"Error rate spike: {value:.2%}",
            "memory_usage_critical": f"CRITICAL: Memory usage at {value:.0f}MB",
            "cpu_usage_high": f"High CPU usage: {value:.1f}%",
            "progress_stalled": f"Progress stalled: {value:.1f}% per hour",
            "deadline_risk": f"DEADLINE RISK: {value:.1f} hours elapsed"
        }

        return titles.get(rule.name, f"Alert: {rule.name} = {value}")

    def generate_alert_description(self, rule: AlertRule, value: float) -> str:
        """Generate detailed alert description"""
        descriptions = {
            "test_pass_rate_critical": f"Test pass rate has dropped to {value:.1f}%, well below the critical threshold of {rule.threshold}%. This indicates major test infrastructure issues that are blocking development progress.",
            "critical_security_issues": f"Security scan detected {value:.0f} critical vulnerabilities that require immediate attention. These issues pose significant security risks.",
            "bundle_size_critical": f"Application bundle size has grown to {value:.0f}KB, significantly exceeding the target of 500KB. This will impact load times and user experience.",
            "deadline_risk": f"Phase 1 has been running for {value:.1f} hours of the 48-hour target. Current progress may not meet the deadline.",
            "memory_usage_critical": f"System memory usage has reached {value:.0f}MB, indicating potential memory leaks or resource exhaustion."
        }

        return descriptions.get(rule.name, f"Metric {rule.metric_path} value {value} exceeded threshold {rule.threshold}")

    def generate_action_required(self, rule: AlertRule, value: float) -> str:
        """Generate recommended actions for alert"""
        actions = {
            "test_pass_rate_critical": "1. Run detailed test analysis to identify failing tests\n2. Fix import/dependency errors\n3. Verify test environment configuration",
            "critical_security_issues": "1. Review security scan results\n2. Update vulnerable dependencies\n3. Fix code security issues",
            "bundle_size_critical": "1. Analyze bundle composition\n2. Implement code splitting\n3. Remove unused dependencies",
            "deadline_risk": "1. Escalate to project leads\n2. Assess progress blockers\n3. Consider scope adjustment",
            "memory_usage_critical": "1. Check for memory leaks\n2. Restart affected services\n3. Monitor resource usage"
        }

        return actions.get(rule.name, "Review metric and take appropriate action")

    def trigger_alert(self, alert: Alert):
        """Trigger an alert and notify handlers"""
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.timestamp.isoformat(),
                alert.severity,
                alert.category,
                alert.title,
                alert.description,
                alert.metric_value,
                alert.threshold,
                alert.trend,
                alert.action_required,
                alert.resolved,
                alert.resolution_time.isoformat() if alert.resolution_time else None
            ))

        # Log alert
        self.logger.warning(f"ALERT [{alert.severity.upper()}] {alert.title}")

        # Notify handlers
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Notification handler failed: {e}")

        # Add to queue for immediate processing
        self.alert_queue.put(alert)

    def auto_resolve_alerts(self, rule_name: str):
        """Auto-resolve alerts for a rule when condition is no longer met"""
        current_time = datetime.datetime.now()

        # Find active alerts for this rule
        alerts_to_resolve = [
            alert for alert in self.active_alerts.values()
            if rule_name in alert.title and not alert.resolved and alert.auto_resolve
        ]

        for alert in alerts_to_resolve:
            alert.resolved = True
            alert.resolution_time = current_time

            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts SET resolved = TRUE, resolution_time = ? WHERE id = ?
                """, (current_time.isoformat(), alert.id))

            self.logger.info(f"Auto-resolved alert: {alert.title}")

    def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """Manually resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.datetime.now()

            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts SET resolved = TRUE, resolution_time = ? WHERE id = ?
                """, (alert.resolution_time.isoformat(), alert_id))

            self.logger.info(f"Manually resolved alert: {alert.title} - {resolution_note}")

    def get_active_alerts(self, severity: str = None, category: str = None) -> List[Alert]:
        """Get currently active alerts"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        if category:
            alerts = [alert for alert in alerts if alert.category == category]

        return sorted(alerts, key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x.severity],
            x.timestamp
        ), reverse=True)

    def get_alert_summary(self) -> Dict:
        """Get summary of current alert status"""
        active_alerts = self.get_active_alerts()

        summary = {
            'total_active': len(active_alerts),
            'by_severity': {
                'critical': len([a for a in active_alerts if a.severity == 'critical']),
                'high': len([a for a in active_alerts if a.severity == 'high']),
                'medium': len([a for a in active_alerts if a.severity == 'medium']),
                'low': len([a for a in active_alerts if a.severity == 'low'])
            },
            'by_category': {
                'test': len([a for a in active_alerts if a.category == 'test']),
                'security': len([a for a in active_alerts if a.category == 'security']),
                'performance': len([a for a in active_alerts if a.category == 'performance']),
                'system': len([a for a in active_alerts if a.category == 'system']),
                'progress': len([a for a in active_alerts if a.category == 'progress'])
            },
            'recent_alerts': [asdict(alert) for alert in active_alerts[:5]]
        }

        return summary

    def generate_alert_report(self) -> str:
        """Generate comprehensive alert status report"""
        active_alerts = self.get_active_alerts()
        summary = self.get_alert_summary()

        report = f"""
{'='*60}
🚨 ALERT SYSTEM STATUS
{'='*60}
Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Active Alerts: {summary['total_active']}

📊 ALERTS BY SEVERITY
🔥 Critical: {summary['by_severity']['critical']}
⚠️  High:     {summary['by_severity']['high']}
📝 Medium:   {summary['by_severity']['medium']}
💡 Low:      {summary['by_severity']['low']}

🔍 ALERTS BY CATEGORY
🧪 Test:        {summary['by_category']['test']}
🔒 Security:    {summary['by_category']['security']}
⚡ Performance: {summary['by_category']['performance']}
💻 System:      {summary['by_category']['system']}
📈 Progress:    {summary['by_category']['progress']}

🔥 ACTIVE ALERTS
"""

        if active_alerts:
            for i, alert in enumerate(active_alerts[:10], 1):
                severity_emoji = {
                    'critical': '🔥',
                    'high': '⚠️',
                    'medium': '📝',
                    'low': '💡'
                }[alert.severity]

                elapsed = datetime.datetime.now() - alert.timestamp
                elapsed_str = f"{elapsed.total_seconds()/3600:.1f}h ago"

                report += f"\n{severity_emoji} #{i} [{alert.severity.upper()}] {alert.title}\n"
                report += f"   Category: {alert.category} | {elapsed_str}\n"
                report += f"   Value: {alert.metric_value:.2f} (threshold: {alert.threshold:.2f})\n"

                # Show action required for critical alerts
                if alert.severity == 'critical':
                    report += f"   Action: {alert.action_required.split(chr(10))[0]}...\n"

        else:
            report += "\n✅ No active alerts\n"

        # Alert system health
        rules_enabled = len([r for r in self.alert_rules if r.enabled])
        report += f"""
🔧 ALERT SYSTEM HEALTH
Enabled Rules: {rules_enabled}/{len(self.alert_rules)}
Notification Handlers: {len(self.notification_handlers)}
System Status: {'🟢 Active' if self.running else '🔴 Stopped'}

📋 RECENT ACTIVITY
Total Alerts (24h): {len([a for a in self.alert_history if (datetime.datetime.now() - a.timestamp).total_seconds() < 86400])}
Auto-Resolved (24h): {len([a for a in self.alert_history if a.auto_resolve and a.resolved and (datetime.datetime.now() - a.timestamp).total_seconds() < 86400])}
"""

        report += f"\n{'='*60}\n"

        return report

    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous alert monitoring"""
        self.running = True
        self.logger.info("Alert system started")

        def monitor_loop():
            while self.running:
                try:
                    # Process queued alerts
                    while not self.alert_queue.empty():
                        alert = self.alert_queue.get_nowait()
                        self.process_alert(alert)

                    time.sleep(interval_seconds)

                except Exception as e:
                    self.logger.error(f"Monitor loop error: {e}")
                    time.sleep(interval_seconds)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.running = False
        self.logger.info("Alert system stopped")

    def process_alert(self, alert: Alert):
        """Process individual alert for immediate actions"""
        if alert.severity == 'critical':
            # For critical alerts, attempt automatic remediation
            self.attempt_auto_remediation(alert)

    def attempt_auto_remediation(self, alert: Alert):
        """Attempt automatic remediation for critical alerts"""
        remediation_actions = {
            "memory_usage_critical": self.restart_services,
            "test_pass_rate_critical": self.trigger_test_fix_attempt,
            "critical_security_issues": self.trigger_security_scan
        }

        for pattern, action in remediation_actions.items():
            if pattern in alert.title.lower():
                try:
                    self.logger.info(f"Attempting auto-remediation for: {alert.title}")
                    action()
                except Exception as e:
                    self.logger.error(f"Auto-remediation failed: {e}")

    def restart_services(self):
        """Restart critical services"""
        self.logger.info("Restarting services for memory issue")
        # Implementation would restart specific services

    def trigger_test_fix_attempt(self):
        """Trigger automated test fixing"""
        self.logger.info("Triggering test fix attempt")
        # Implementation would run test fixing scripts

    def trigger_security_scan(self):
        """Trigger security scan update"""
        self.logger.info("Triggering security scan update")
        # Implementation would run security updates

# Notification handlers
def console_notification_handler(alert: Alert):
    """Console notification handler"""
    severity_colors = {
        'critical': '\033[91m',  # Red
        'high': '\033[93m',      # Yellow
        'medium': '\033[94m',    # Blue
        'low': '\033[92m'        # Green
    }
    reset_color = '\033[0m'

    color = severity_colors.get(alert.severity, '')
    print(f"\n{color}🚨 ALERT [{alert.severity.upper()}]{reset_color}")
    print(f"📋 {alert.title}")
    print(f"🕐 {alert.timestamp.strftime('%H:%M:%S')}")
    print(f"📊 Value: {alert.metric_value:.2f} (threshold: {alert.threshold:.2f})")
    if alert.severity in ['critical', 'high']:
        print(f"⚡ Action: {alert.action_required.split(chr(10))[0]}")
    print("-" * 50)

def file_notification_handler(alert: Alert):
    """File notification handler"""
    alert_file = Path("monitoring/alert_notifications.log")
    alert_file.parent.mkdir(exist_ok=True)

    with open(alert_file, 'a') as f:
        f.write(f"{alert.timestamp.isoformat()} - [{alert.severity.upper()}] {alert.title}\n")
        f.write(f"  Category: {alert.category}\n")
        f.write(f"  Value: {alert.metric_value:.2f} (threshold: {alert.threshold:.2f})\n")
        f.write(f"  Action: {alert.action_required.split(chr(10))[0]}\n\n")

def main():
    """Main entry point for alert system"""
    import argparse

    parser = argparse.ArgumentParser(description="Real-time Alert System")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    parser.add_argument("--test-alert", action="store_true", help="Trigger test alert")
    parser.add_argument("--list-active", action="store_true", help="List active alerts")
    parser.add_argument("--resolve", type=str, help="Resolve alert by ID")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring mode")
    parser.add_argument("--interval", type=int, default=60, help="Monitor interval in seconds")

    args = parser.parse_args()

    alert_system = AlertSystem(args.project_root)

    # Add notification handlers
    alert_system.add_notification_handler(console_notification_handler)
    alert_system.add_notification_handler(file_notification_handler)

    if args.test_alert:
        # Trigger test alert
        test_alert = Alert(
            id="test_alert_123",
            timestamp=datetime.datetime.now(),
            severity="high",
            category="test",
            title="Test Alert",
            description="This is a test alert to verify the system is working",
            metric_value=50.0,
            threshold=70.0,
            trend="declining",
            action_required="No action required - this is a test"
        )
        alert_system.trigger_alert(test_alert)

    elif args.list_active:
        active_alerts = alert_system.get_active_alerts()
        if active_alerts:
            for alert in active_alerts:
                print(f"[{alert.severity.upper()}] {alert.title} - {alert.timestamp}")
        else:
            print("No active alerts")

    elif args.resolve:
        alert_system.resolve_alert(args.resolve, "Manually resolved")
        print(f"Alert {args.resolve} resolved")

    elif args.monitor:
        print("🚨 Starting alert system monitoring...")
        alert_system.start_monitoring(args.interval)

        try:
            while True:
                report = alert_system.generate_alert_report()
                print(report)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n⏹️ Alert monitoring stopped")
            alert_system.stop_monitoring()

    else:
        # Show status
        report = alert_system.generate_alert_report()
        print(report)

if __name__ == "__main__":
    main()