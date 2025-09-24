#!/usr/bin/env python3
"""
Hourly Progress Reporter for Phase 1 Monitoring
Generates comprehensive hourly progress reports with trend analysis and projections
"""

import json
import time
import datetime
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess
import threading
import schedule

@dataclass
class HourlySnapshot:
    timestamp: datetime.datetime
    elapsed_hours: float
    test_pass_rate: float
    security_score: float
    bundle_size_kb: float
    overall_completion: float
    active_alerts: int
    critical_alerts: int
    blockers: List[str]
    progress_rate_per_hour: float
    estimated_completion_hours: Optional[float]
    risk_level: str

@dataclass
class ProgressTrend:
    metric_name: str
    current_value: float
    hourly_change: float
    daily_change: float
    trend_direction: str  # "improving", "stable", "declining"
    velocity: float  # rate of change per hour
    projected_24h: float

class HourlyReporter:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.db_path = self.project_root / "monitoring" / "hourly_reports.db"
        self.reports_dir = self.project_root / "monitoring" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.init_database()
        self.targets = {
            "test_pass_rate": 95.0,
            "security_score": 95.0,
            "bundle_size_kb": 500.0,
            "overall_completion": 100.0
        }

    def init_database(self):
        """Initialize database for hourly reports"""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_snapshots (
                    timestamp DATETIME PRIMARY KEY,
                    elapsed_hours REAL,
                    test_pass_rate REAL,
                    security_score REAL,
                    bundle_size_kb REAL,
                    overall_completion REAL,
                    active_alerts INTEGER,
                    critical_alerts INTEGER,
                    blockers TEXT,
                    progress_rate_per_hour REAL,
                    estimated_completion_hours REAL,
                    risk_level TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS progress_trends (
                    timestamp DATETIME,
                    metric_name TEXT,
                    current_value REAL,
                    hourly_change REAL,
                    daily_change REAL,
                    trend_direction TEXT,
                    velocity REAL,
                    projected_24h REAL
                )
            """)

    def collect_current_metrics(self) -> Dict:
        """Collect current metrics from all monitoring systems"""
        metrics = {}

        # Load test metrics
        test_metrics_file = self.project_root / "monitoring" / "test_metrics.json"
        if test_metrics_file.exists():
            try:
                with open(test_metrics_file, 'r') as f:
                    test_data = json.load(f)
                    metrics['test_pass_rate'] = test_data.get('pass_rate', 0)
                    metrics['failing_tests'] = test_data.get('failed', 0)
            except Exception:
                metrics['test_pass_rate'] = 67.7  # Default current state

        # Load security metrics
        security_metrics_file = self.project_root / "monitoring" / "security_metrics.json"
        if security_metrics_file.exists():
            try:
                with open(security_metrics_file, 'r') as f:
                    security_data = json.load(f)
                    metrics['security_score'] = security_data.get('security_score', 85.0)
                    metrics['critical_issues'] = security_data.get('critical_issues', 0)
            except Exception:
                metrics['security_score'] = 85.0

        # Load performance metrics
        performance_metrics_file = self.project_root / "monitoring" / "performance_metrics.json"
        if performance_metrics_file.exists():
            try:
                with open(performance_metrics_file, 'r') as f:
                    perf_data = json.load(f)
                    metrics['bundle_size_kb'] = perf_data.get('bundle_metrics', {}).get('total_size_kb', 950.0)
                    metrics['api_latency_ms'] = perf_data.get('api_metrics', {}).get('avg_response_time_ms', 200.0)
            except Exception:
                metrics['bundle_size_kb'] = 950.0
                metrics['api_latency_ms'] = 200.0

        # Load alert metrics
        alert_db = self.project_root / "monitoring" / "alerts.db"
        if alert_db.exists():
            try:
                with sqlite3.connect(alert_db) as conn:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM alerts WHERE resolved = FALSE"
                    )
                    metrics['active_alerts'] = cursor.fetchone()[0]

                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM alerts WHERE resolved = FALSE AND severity = 'critical'"
                    )
                    metrics['critical_alerts'] = cursor.fetchone()[0]
            except Exception:
                metrics['active_alerts'] = 0
                metrics['critical_alerts'] = 0
        else:
            metrics['active_alerts'] = 0
            metrics['critical_alerts'] = 0

        return metrics

    def calculate_overall_completion(self, metrics: Dict) -> float:
        """Calculate overall completion percentage"""
        test_progress = min(100, (metrics.get('test_pass_rate', 0) / self.targets['test_pass_rate']) * 100)
        security_progress = min(100, (metrics.get('security_score', 0) / self.targets['security_score']) * 100)
        performance_progress = min(100, (self.targets['bundle_size_kb'] / metrics.get('bundle_size_kb', 1000)) * 100)

        overall = (test_progress + security_progress + performance_progress) / 3
        return min(100, max(0, overall))

    def identify_current_blockers(self, metrics: Dict) -> List[str]:
        """Identify current blockers based on metrics"""
        blockers = []

        if metrics.get('test_pass_rate', 0) < 50:
            blockers.append("Critical test failures blocking development")

        if metrics.get('critical_issues', 0) > 0:
            blockers.append(f"{metrics['critical_issues']} critical security vulnerabilities")

        if metrics.get('bundle_size_kb', 0) > 800:
            blockers.append("Bundle size significantly exceeds target")

        if metrics.get('critical_alerts', 0) > 0:
            blockers.append(f"{metrics['critical_alerts']} critical system alerts")

        if metrics.get('api_latency_ms', 0) > 1000:
            blockers.append("Severe API performance degradation")

        return blockers

    def calculate_progress_rate(self, current_completion: float, elapsed_hours: float) -> float:
        """Calculate progress rate per hour"""
        if elapsed_hours <= 0:
            return 0.0
        return current_completion / elapsed_hours

    def estimate_completion_time(self, current_completion: float, progress_rate: float) -> Optional[float]:
        """Estimate total hours to completion"""
        if progress_rate <= 0 or current_completion >= 100:
            return None

        remaining_work = 100 - current_completion
        estimated_hours = remaining_work / progress_rate

        return estimated_hours

    def assess_risk_level(self, elapsed_hours: float, completion: float,
                         critical_alerts: int, blockers: List[str]) -> str:
        """Assess current risk level"""
        if critical_alerts > 0 or len(blockers) >= 3:
            return "CRITICAL"

        if elapsed_hours > 42 and completion < 80:
            return "HIGH"

        if elapsed_hours > 36 and completion < 70:
            return "MEDIUM"

        if elapsed_hours > 30 and completion < 50:
            return "MEDIUM"

        return "LOW"

    def calculate_trends(self, current_metrics: Dict) -> List[ProgressTrend]:
        """Calculate trends for key metrics"""
        trends = []

        # Get historical data for trend calculation
        historical_data = self.get_historical_snapshots(hours=24)

        for metric_name in ['test_pass_rate', 'security_score', 'bundle_size_kb', 'overall_completion']:
            current_value = current_metrics.get(metric_name, 0)

            if len(historical_data) >= 2:
                # Calculate hourly change
                one_hour_ago = self.find_closest_snapshot(historical_data, 1)
                hourly_change = current_value - one_hour_ago.get(metric_name, current_value) if one_hour_ago else 0

                # Calculate daily change
                twenty_four_hours_ago = self.find_closest_snapshot(historical_data, 24)
                daily_change = current_value - twenty_four_hours_ago.get(metric_name, current_value) if twenty_four_hours_ago else 0

                # Determine trend direction
                if abs(hourly_change) < 0.5:
                    trend_direction = "stable"
                elif hourly_change > 0:
                    trend_direction = "improving" if metric_name != 'bundle_size_kb' else "declining"
                else:
                    trend_direction = "declining" if metric_name != 'bundle_size_kb' else "improving"

                # Calculate velocity (rate of change per hour)
                velocity = hourly_change

                # Project 24 hours ahead
                projected_24h = current_value + (velocity * 24)

            else:
                hourly_change = 0
                daily_change = 0
                trend_direction = "stable"
                velocity = 0
                projected_24h = current_value

            trends.append(ProgressTrend(
                metric_name=metric_name,
                current_value=current_value,
                hourly_change=hourly_change,
                daily_change=daily_change,
                trend_direction=trend_direction,
                velocity=velocity,
                projected_24h=projected_24h
            ))

        return trends

    def get_historical_snapshots(self, hours: int = 24) -> List[Dict]:
        """Get historical snapshots from database"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM hourly_snapshots
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time.isoformat(),))

                columns = [desc[0] for desc in cursor.description]
                snapshots = []

                for row in cursor.fetchall():
                    snapshot = dict(zip(columns, row))
                    snapshots.append(snapshot)

                return snapshots

        except Exception:
            return []

    def find_closest_snapshot(self, snapshots: List[Dict], hours_ago: int) -> Optional[Dict]:
        """Find snapshot closest to N hours ago"""
        target_time = datetime.datetime.now() - datetime.timedelta(hours=hours_ago)

        closest_snapshot = None
        min_diff = float('inf')

        for snapshot in snapshots:
            try:
                snapshot_time = datetime.datetime.fromisoformat(snapshot['timestamp'])
                diff = abs((snapshot_time - target_time).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest_snapshot = snapshot
            except Exception:
                continue

        return closest_snapshot

    def create_hourly_snapshot(self) -> HourlySnapshot:
        """Create a snapshot of current state"""
        current_metrics = self.collect_current_metrics()

        # Calculate derived metrics
        elapsed_hours = self.calculate_elapsed_hours()
        overall_completion = self.calculate_overall_completion(current_metrics)
        blockers = self.identify_current_blockers(current_metrics)
        progress_rate = self.calculate_progress_rate(overall_completion, elapsed_hours)
        estimated_completion = self.estimate_completion_time(overall_completion, progress_rate)
        risk_level = self.assess_risk_level(
            elapsed_hours,
            overall_completion,
            current_metrics.get('critical_alerts', 0),
            blockers
        )

        snapshot = HourlySnapshot(
            timestamp=datetime.datetime.now(),
            elapsed_hours=elapsed_hours,
            test_pass_rate=current_metrics.get('test_pass_rate', 0),
            security_score=current_metrics.get('security_score', 0),
            bundle_size_kb=current_metrics.get('bundle_size_kb', 0),
            overall_completion=overall_completion,
            active_alerts=current_metrics.get('active_alerts', 0),
            critical_alerts=current_metrics.get('critical_alerts', 0),
            blockers=blockers,
            progress_rate_per_hour=progress_rate,
            estimated_completion_hours=estimated_completion,
            risk_level=risk_level
        )

        # Store in database
        self.store_snapshot(snapshot)

        return snapshot

    def calculate_elapsed_hours(self) -> float:
        """Calculate elapsed hours since Phase 1 start"""
        # Try to get start time from first snapshot, otherwise estimate
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT MIN(timestamp) FROM hourly_snapshots"
                )
                first_snapshot = cursor.fetchone()[0]

                if first_snapshot:
                    start_time = datetime.datetime.fromisoformat(first_snapshot)
                else:
                    # Assume started 12 hours ago if no history
                    start_time = datetime.datetime.now() - datetime.timedelta(hours=12)

        except Exception:
            # Default to 12 hours if no database
            start_time = datetime.datetime.now() - datetime.timedelta(hours=12)

        elapsed = datetime.datetime.now() - start_time
        return elapsed.total_seconds() / 3600

    def store_snapshot(self, snapshot: HourlySnapshot):
        """Store snapshot in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO hourly_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp.isoformat(),
                snapshot.elapsed_hours,
                snapshot.test_pass_rate,
                snapshot.security_score,
                snapshot.bundle_size_kb,
                snapshot.overall_completion,
                snapshot.active_alerts,
                snapshot.critical_alerts,
                json.dumps(snapshot.blockers),
                snapshot.progress_rate_per_hour,
                snapshot.estimated_completion_hours,
                snapshot.risk_level
            ))

    def store_trends(self, trends: List[ProgressTrend]):
        """Store trend data in database"""
        timestamp = datetime.datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            for trend in trends:
                conn.execute("""
                    INSERT INTO progress_trends VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    trend.metric_name,
                    trend.current_value,
                    trend.hourly_change,
                    trend.daily_change,
                    trend.trend_direction,
                    trend.velocity,
                    trend.projected_24h
                ))

    def generate_hourly_report(self, snapshot: HourlySnapshot, trends: List[ProgressTrend]) -> str:
        """Generate comprehensive hourly report"""

        def progress_bar(current: float, target: float, width: int = 25) -> str:
            percentage = min(100, (current / target) * 100)
            filled = int(width * percentage / 100)
            bar = '█' * filled + '▒' * (width - filled)
            return f"[{bar}] {percentage:.1f}%"

        def trend_arrow(direction: str) -> str:
            arrows = {"improving": "📈", "declining": "📉", "stable": "➡️"}
            return arrows.get(direction, "❓")

        def risk_emoji(level: str) -> str:
            emojis = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
            return emojis.get(level, "⚪")

        # Calculate time remaining
        target_hours = 48.0
        time_remaining = max(0, target_hours - snapshot.elapsed_hours)

        report = f"""
{'='*80}
📊 PHASE 1 HOURLY PROGRESS REPORT
{'='*80}
Report Time: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Elapsed: {snapshot.elapsed_hours:.1f}h / {target_hours}h
Remaining: {time_remaining:.1f}h
Risk Level: {risk_emoji(snapshot.risk_level)} {snapshot.risk_level}

🎯 OVERALL PROGRESS
Completion: {snapshot.overall_completion:.1f}%
{progress_bar(snapshot.overall_completion, 100)}
Progress Rate: {snapshot.progress_rate_per_hour:.1f}% per hour
"""

        if snapshot.estimated_completion_hours:
            eta = datetime.datetime.now() + datetime.timedelta(hours=snapshot.estimated_completion_hours)
            on_time = "✅" if snapshot.estimated_completion_hours <= time_remaining else "⚠️"
            report += f"Estimated Completion: {eta.strftime('%Y-%m-%d %H:%M')} {on_time}\n"
        else:
            report += "Estimated Completion: Unable to calculate\n"

        # Individual metrics with trends
        report += f"""
📋 DETAILED METRICS

🧪 Test Infrastructure
Current: {snapshot.test_pass_rate:.1f}% / 95%
{progress_bar(snapshot.test_pass_rate, 95)}
"""

        test_trend = next((t for t in trends if t.metric_name == 'test_pass_rate'), None)
        if test_trend:
            report += f"Trend: {trend_arrow(test_trend.trend_direction)} {test_trend.hourly_change:+.1f}%/h\n"
            if test_trend.projected_24h > 95:
                report += f"Projection: ✅ Will reach 95% in ~{(95 - snapshot.test_pass_rate) / test_trend.velocity:.1f}h\n"
            elif test_trend.velocity > 0:
                report += f"Projection: 📈 {test_trend.projected_24h:.1f}% in 24h\n"
            else:
                report += f"Projection: 📉 No improvement trend\n"

        report += f"""
🔒 Security Hardening
Current: {snapshot.security_score:.1f}% / 95%
{progress_bar(snapshot.security_score, 95)}
"""

        security_trend = next((t for t in trends if t.metric_name == 'security_score'), None)
        if security_trend:
            report += f"Trend: {trend_arrow(security_trend.trend_direction)} {security_trend.hourly_change:+.1f}%/h\n"

        report += f"""
⚡ Performance Optimization
Bundle Size: {snapshot.bundle_size_kb:.0f}KB / 500KB
{progress_bar(500, snapshot.bundle_size_kb) if snapshot.bundle_size_kb > 500 else progress_bar(snapshot.bundle_size_kb, 500)}
"""

        bundle_trend = next((t for t in trends if t.metric_name == 'bundle_size_kb'), None)
        if bundle_trend:
            report += f"Trend: {trend_arrow(bundle_trend.trend_direction)} {bundle_trend.hourly_change:+.0f}KB/h\n"

        # Alerts and blockers
        report += f"""
🚨 ALERTS & BLOCKERS
Active Alerts: {snapshot.active_alerts}
Critical Alerts: {snapshot.critical_alerts}
"""

        if snapshot.blockers:
            report += "Current Blockers:\n"
            for i, blocker in enumerate(snapshot.blockers, 1):
                report += f"  {i}. {blocker}\n"
        else:
            report += "✅ No active blockers\n"

        # Trend analysis
        report += f"""
📈 TREND ANALYSIS (24-hour view)
"""

        for trend in trends:
            if trend.trend_direction != "stable":
                report += f"{trend.metric_name}: {trend_arrow(trend.trend_direction)} "
                report += f"{trend.hourly_change:+.1f}/h (24h: {trend.daily_change:+.1f})\n"

        # Recommendations
        report += f"""
🎯 IMMEDIATE PRIORITIES
"""

        priorities = []

        if snapshot.critical_alerts > 0:
            priorities.append(f"🔥 CRITICAL: Address {snapshot.critical_alerts} critical alerts")

        if snapshot.test_pass_rate < 80:
            priorities.append("⚡ HIGH: Focus on test infrastructure fixes")

        if snapshot.security_score < 90:
            priorities.append("🔒 MEDIUM: Continue security hardening efforts")

        if snapshot.bundle_size_kb > 700:
            priorities.append("📦 MEDIUM: Implement bundle optimization")

        if snapshot.elapsed_hours > 36 and snapshot.overall_completion < 75:
            priorities.append("⏰ URGENT: Escalate timeline risk")

        if not priorities:
            priorities.append("✅ MAINTAIN: Continue steady progress")

        for priority in priorities:
            report += f"  • {priority}\n"

        # Risk assessment
        report += f"""
⚠️ RISK ASSESSMENT
Timeline Risk: {'🔴 HIGH' if time_remaining < 12 and snapshot.overall_completion < 80 else '🟡 MEDIUM' if time_remaining < 24 and snapshot.overall_completion < 90 else '🟢 LOW'}
Quality Risk: {'🔴 HIGH' if snapshot.critical_alerts > 0 else '🟡 MEDIUM' if len(snapshot.blockers) > 2 else '🟢 LOW'}
Resource Risk: {'🔴 HIGH' if snapshot.progress_rate_per_hour < 1.5 else '🟡 MEDIUM' if snapshot.progress_rate_per_hour < 2.5 else '🟢 LOW'}

📊 VELOCITY METRICS
Current Velocity: {snapshot.progress_rate_per_hour:.1f}% completion per hour
Required Velocity: {(100 - snapshot.overall_completion) / time_remaining:.1f}% per hour to meet deadline
Performance Gap: {((100 - snapshot.overall_completion) / time_remaining) - snapshot.progress_rate_per_hour:+.1f}% per hour
"""

        report += f"\n{'='*80}\n"

        return report

    def save_report_to_file(self, report: str, snapshot: HourlySnapshot):
        """Save report to timestamped file"""
        filename = f"hourly_report_{snapshot.timestamp.strftime('%Y%m%d_%H%M')}.txt"
        filepath = self.reports_dir / filename

        with open(filepath, 'w') as f:
            f.write(report)

        # Also save as latest
        latest_path = self.reports_dir / "latest_hourly_report.txt"
        with open(latest_path, 'w') as f:
            f.write(report)

        return filepath

    def export_data(self, snapshot: HourlySnapshot, trends: List[ProgressTrend]):
        """Export data for integration with main dashboard"""
        data = {
            'snapshot': asdict(snapshot),
            'trends': [asdict(trend) for trend in trends],
            'targets': self.targets,
            'timeline': {
                'target_hours': 48.0,
                'elapsed_hours': snapshot.elapsed_hours,
                'remaining_hours': max(0, 48.0 - snapshot.elapsed_hours),
                'on_track': snapshot.estimated_completion_hours <= (48.0 - snapshot.elapsed_hours) if snapshot.estimated_completion_hours else False
            }
        }

        export_file = self.project_root / "monitoring" / "hourly_progress.json"
        with open(export_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def run_hourly_report(self) -> Tuple[HourlySnapshot, List[ProgressTrend], str]:
        """Generate complete hourly report"""
        print("📊 Generating hourly progress report...")

        # Create snapshot
        snapshot = self.create_hourly_snapshot()

        # Calculate trends
        trends = self.calculate_trends({
            'test_pass_rate': snapshot.test_pass_rate,
            'security_score': snapshot.security_score,
            'bundle_size_kb': snapshot.bundle_size_kb,
            'overall_completion': snapshot.overall_completion
        })

        # Store trends
        self.store_trends(trends)

        # Generate report
        report = self.generate_hourly_report(snapshot, trends)

        # Save to file
        filepath = self.save_report_to_file(report, snapshot)
        print(f"📁 Report saved to: {filepath}")

        # Export data
        self.export_data(snapshot, trends)

        return snapshot, trends, report

    def start_scheduled_reporting(self):
        """Start scheduled hourly reporting"""
        print("⏰ Starting scheduled hourly reporting...")

        # Schedule hourly reports
        schedule.every().hour.at(":00").do(self.run_hourly_report)

        # Also run immediately
        self.run_hourly_report()

        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point for hourly reporter"""
    import argparse

    parser = argparse.ArgumentParser(description="Hourly Progress Reporter")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    parser.add_argument("--run-once", action="store_true", help="Run report once and exit")
    parser.add_argument("--scheduled", action="store_true", help="Start scheduled reporting")
    parser.add_argument("--export-only", action="store_true", help="Export data without generating report")

    args = parser.parse_args()

    reporter = HourlyReporter(args.project_root)

    if args.run_once:
        snapshot, trends, report = reporter.run_hourly_report()
        print(report)

    elif args.export_only:
        snapshot = reporter.create_hourly_snapshot()
        trends = reporter.calculate_trends({
            'test_pass_rate': snapshot.test_pass_rate,
            'security_score': snapshot.security_score,
            'bundle_size_kb': snapshot.bundle_size_kb,
            'overall_completion': snapshot.overall_completion
        })
        reporter.export_data(snapshot, trends)
        print("📁 Data exported to hourly_progress.json")

    elif args.scheduled:
        try:
            reporter.start_scheduled_reporting()
        except KeyboardInterrupt:
            print("\n⏹️ Scheduled reporting stopped")

    else:
        # Default: run once
        snapshot, trends, report = reporter.run_hourly_report()
        print(report)

if __name__ == "__main__":
    main()