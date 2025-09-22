#!/usr/bin/env python3
"""
Master Control Script for Phase 1 Monitoring
Orchestrates all monitoring components with real-time dashboard
"""

import os
import sys
import time
import subprocess
import threading
import signal
from pathlib import Path
from typing import Dict, List
import json
import datetime

# Import monitoring components
from phase1_dashboard import Phase1Monitor
from test_monitor import TestMonitor
from security_monitor import SecurityMonitor
from performance_monitor import PerformanceMonitor
from alert_system import AlertSystem, console_notification_handler, file_notification_handler
from hourly_reporter import HourlyReporter

class Phase1MasterControl:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.running = False
        self.monitors = {}
        self.threads = []

        # Initialize all monitoring components
        self.init_monitors()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def init_monitors(self):
        """Initialize all monitoring components"""
        print("🚀 Initializing Phase 1 monitoring systems...")

        try:
            self.monitors['main'] = Phase1Monitor(str(self.project_root))
            print("✅ Main dashboard initialized")

            self.monitors['test'] = TestMonitor(str(self.project_root))
            print("✅ Test monitor initialized")

            self.monitors['security'] = SecurityMonitor(str(self.project_root))
            print("✅ Security monitor initialized")

            self.monitors['performance'] = PerformanceMonitor(str(self.project_root))
            print("✅ Performance monitor initialized")

            self.monitors['alerts'] = AlertSystem(str(self.project_root))
            self.monitors['alerts'].add_notification_handler(console_notification_handler)
            self.monitors['alerts'].add_notification_handler(file_notification_handler)
            print("✅ Alert system initialized")

            self.monitors['reporter'] = HourlyReporter(str(self.project_root))
            print("✅ Hourly reporter initialized")

        except Exception as e:
            print(f"❌ Error initializing monitors: {e}")
            sys.exit(1)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n📡 Received signal {signum}, shutting down monitors...")
        self.stop_monitoring()

    def start_monitoring(self):
        """Start all monitoring components"""
        print("\n🚀 Starting Phase 1 Critical Stabilization Monitoring")
        print("=" * 80)
        print("🎯 Target: 48-hour completion")
        print("📊 Monitoring: Tests, Security, Performance, Alerts")
        print("⏱️  Updates: Every 10 minutes")
        print("📈 Reports: Every hour")
        print("=" * 80)

        self.running = True

        # Start alert system first
        self.monitors['alerts'].start_monitoring(60)  # 1-minute alert checks

        # Start individual monitor threads
        monitors_config = [
            ('test', 300),        # 5 minutes
            ('security', 900),    # 15 minutes
            ('performance', 600), # 10 minutes
        ]

        for monitor_name, interval in monitors_config:
            thread = threading.Thread(
                target=self.run_monitor_loop,
                args=(monitor_name, interval),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            print(f"🔄 Started {monitor_name} monitor (interval: {interval}s)")

        # Start hourly reporter thread
        reporter_thread = threading.Thread(
            target=self.run_hourly_reports,
            daemon=True
        )
        reporter_thread.start()
        self.threads.append(reporter_thread)
        print("📊 Started hourly reporter")

        # Main dashboard loop
        print("\n📈 Starting main dashboard...")
        self.run_main_dashboard()

    def run_monitor_loop(self, monitor_name: str, interval: int):
        """Run individual monitor in a loop"""
        while self.running:
            try:
                if monitor_name == 'test':
                    metrics = self.monitors['test'].run_monitoring_cycle()
                    self.monitors['test'].export_metrics(metrics)

                elif monitor_name == 'security':
                    metrics = self.monitors['security'].run_comprehensive_scan()
                    self.monitors['security'].export_metrics(metrics)

                elif monitor_name == 'performance':
                    metrics = self.monitors['performance'].run_performance_scan()
                    self.monitors['performance'].export_metrics(metrics)

                # Check for alerts
                self.check_and_trigger_alerts()

            except Exception as e:
                print(f"❌ Error in {monitor_name} monitor: {e}")

            time.sleep(interval)

    def run_hourly_reports(self):
        """Run hourly progress reports"""
        last_report_hour = -1

        while self.running:
            current_hour = datetime.datetime.now().hour

            # Run report on the hour
            if current_hour != last_report_hour:
                try:
                    snapshot, trends, report = self.monitors['reporter'].run_hourly_report()
                    print("\n📊 HOURLY REPORT GENERATED")
                    print("=" * 50)
                    print(f"Completion: {snapshot.overall_completion:.1f}%")
                    print(f"Risk Level: {snapshot.risk_level}")
                    print(f"Active Blockers: {len(snapshot.blockers)}")
                    print("=" * 50)

                    last_report_hour = current_hour

                except Exception as e:
                    print(f"❌ Error generating hourly report: {e}")

            time.sleep(300)  # Check every 5 minutes

    def check_and_trigger_alerts(self):
        """Check metrics and trigger alerts if needed"""
        try:
            # Collect current metrics from all monitoring files
            metrics_data = {}

            # Load test metrics
            test_file = self.project_root / "monitoring" / "test_metrics.json"
            if test_file.exists():
                with open(test_file, 'r') as f:
                    test_data = json.load(f)
                    metrics_data['test_pass_rate'] = test_data.get('pass_rate', 0)
                    metrics_data['failing_tests'] = test_data.get('failed', 0)

            # Load security metrics
            security_file = self.project_root / "monitoring" / "security_metrics.json"
            if security_file.exists():
                with open(security_file, 'r') as f:
                    security_data = json.load(f)
                    metrics_data['security_score'] = security_data.get('security_score', 0)
                    metrics_data['critical_issues'] = security_data.get('critical_issues', 0)

            # Load performance metrics
            perf_file = self.project_root / "monitoring" / "performance_metrics.json"
            if perf_file.exists():
                with open(perf_file, 'r') as f:
                    perf_data = json.load(f)
                    bundle_metrics = perf_data.get('bundle_metrics', {})
                    api_metrics = perf_data.get('api_metrics', {})
                    system_metrics = perf_data.get('system_metrics', {})

                    metrics_data['bundle_size_kb'] = bundle_metrics.get('total_size_kb', 0)
                    metrics_data['api_latency_ms'] = api_metrics.get('avg_response_time_ms', 0)
                    metrics_data['error_rate'] = api_metrics.get('error_rate', 0)
                    metrics_data['memory_usage_mb'] = system_metrics.get('memory_usage_mb', 0)
                    metrics_data['cpu_utilization'] = system_metrics.get('cpu_usage_percent', 0)

            # Load progress data
            progress_file = self.project_root / "monitoring" / "hourly_progress.json"
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                    snapshot = progress_data.get('snapshot', {})
                    metrics_data['elapsed_hours'] = snapshot.get('elapsed_hours', 0)
                    metrics_data['progress_rate_per_hour'] = snapshot.get('progress_rate_per_hour', 0)

            # Evaluate alerts
            self.monitors['alerts'].evaluate_metrics(metrics_data)

        except Exception as e:
            print(f"❌ Error checking alerts: {e}")

    def run_main_dashboard(self):
        """Run main dashboard display loop"""
        try:
            while self.running:
                completed = self.monitors['main'].run_monitoring_cycle()

                if completed:
                    print("\n🎉 PHASE 1 COMPLETED SUCCESSFULLY!")
                    print("🏆 All targets achieved within 48 hours!")
                    self.stop_monitoring()
                    break

                # Show alert summary
                alert_summary = self.monitors['alerts'].get_alert_summary()
                if alert_summary['total_active'] > 0:
                    print(f"\n🚨 Active Alerts: {alert_summary['total_active']} "
                          f"(Critical: {alert_summary['by_severity']['critical']})")

                print(f"\n⏳ Next update in 10 minutes...")
                time.sleep(600)  # 10 minutes

        except Exception as e:
            print(f"❌ Main dashboard error: {e}")
            self.stop_monitoring()

    def stop_monitoring(self):
        """Stop all monitoring gracefully"""
        print("\n⏹️  Stopping Phase 1 monitoring...")

        self.running = False

        # Stop alert system
        if 'alerts' in self.monitors:
            self.monitors['alerts'].stop_monitoring()

        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)

        print("✅ All monitoring stopped")

    def get_status_summary(self) -> Dict:
        """Get current status summary for external tools"""
        try:
            # Load latest metrics
            test_file = self.project_root / "monitoring" / "test_metrics.json"
            security_file = self.project_root / "monitoring" / "security_metrics.json"
            perf_file = self.project_root / "monitoring" / "performance_metrics.json"
            progress_file = self.project_root / "monitoring" / "hourly_progress.json"

            summary = {
                'timestamp': datetime.datetime.now().isoformat(),
                'running': self.running,
                'test_pass_rate': 0,
                'security_score': 0,
                'bundle_size_kb': 0,
                'overall_completion': 0,
                'active_alerts': 0,
                'risk_level': 'UNKNOWN'
            }

            if test_file.exists():
                with open(test_file, 'r') as f:
                    data = json.load(f)
                    summary['test_pass_rate'] = data.get('pass_rate', 0)

            if security_file.exists():
                with open(security_file, 'r') as f:
                    data = json.load(f)
                    summary['security_score'] = data.get('security_score', 0)

            if perf_file.exists():
                with open(perf_file, 'r') as f:
                    data = json.load(f)
                    summary['bundle_size_kb'] = data.get('bundle_metrics', {}).get('total_size_kb', 0)

            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    snapshot = data.get('snapshot', {})
                    summary['overall_completion'] = snapshot.get('overall_completion', 0)
                    summary['risk_level'] = snapshot.get('risk_level', 'UNKNOWN')

            if 'alerts' in self.monitors:
                alert_summary = self.monitors['alerts'].get_alert_summary()
                summary['active_alerts'] = alert_summary['total_active']

            return summary

        except Exception as e:
            print(f"❌ Error getting status summary: {e}")
            return {'error': str(e)}

    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Installing monitoring dependencies...")

        dependencies = [
            'psutil',
            'requests',
            'schedule',
            'safety'
        ]

        for dep in dependencies:
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', dep
                ], check=True, capture_output=True)
                print(f"✅ Installed {dep}")
            except subprocess.CalledProcessError:
                print(f"⚠️ Failed to install {dep} - some features may be limited")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1 Master Control")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--test-run", action="store_true", help="Run monitoring once for testing")

    args = parser.parse_args()

    if args.install_deps:
        control = Phase1MasterControl(args.project_root)
        control.install_dependencies()
        return

    if args.status:
        control = Phase1MasterControl(args.project_root)
        status = control.get_status_summary()
        print(json.dumps(status, indent=2))
        return

    if args.test_run:
        control = Phase1MasterControl(args.project_root)
        print("🧪 Running test monitoring cycle...")

        # Run each monitor once
        test_metrics = control.monitors['test'].run_monitoring_cycle()
        security_metrics = control.monitors['security'].run_comprehensive_scan()
        perf_metrics = control.monitors['performance'].run_performance_scan()

        # Generate reports
        control.monitors['test'].export_metrics(test_metrics)
        control.monitors['security'].export_metrics(security_metrics)
        control.monitors['performance'].export_metrics(perf_metrics)

        snapshot, trends, report = control.monitors['reporter'].run_hourly_report()

        print("✅ Test run completed - check monitoring/ directory for outputs")
        return

    # Normal operation
    control = Phase1MasterControl(args.project_root)

    try:
        control.start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
    finally:
        control.stop_monitoring()

if __name__ == "__main__":
    main()