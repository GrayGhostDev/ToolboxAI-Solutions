#!/usr/bin/env python3
"""
CI/CD Metrics Collection System
Collects and reports DORA metrics and other CI/CD performance indicators.
"""

import os
import sys
import json
import redis
import sqlite3
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("⚠️  PyGithub not installed. Install with: pip install PyGithub")

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class CICDMetrics:
    """Collect and analyze CI/CD metrics."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.metrics_db = self.project_root / "logs" / "metrics.db"
        self.metrics_db.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Initialize GitHub client if available
        self.github = None
        self.repo = None
        if GITHUB_AVAILABLE and os.getenv('GITHUB_TOKEN'):
            self.github = Github(os.getenv('GITHUB_TOKEN'))
            try:
                self.repo = self.github.get_repo('ToolBoxAI-Solutions/ToolboxAI-Solutions')
            except Exception as e:
                print(f"⚠️  Could not access GitHub repo: {e}")
        
        # Initialize Redis for real-time metrics
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.redis_available = True
        except (redis.ConnectionError, redis.TimeoutError):
            self.redis_available = False
            self.redis_client = None
        
        # DORA metrics
        self.dora_metrics = {
            'deployment_frequency': 0,
            'lead_time_for_changes': 0,
            'mean_time_to_recovery': 0,
            'change_failure_rate': 0
        }
        
        # Additional metrics
        self.additional_metrics = {
            'build_success_rate': 0,
            'test_coverage': 0,
            'code_review_time': 0,
            'pipeline_duration': 0,
            'active_contributors': 0
        }

    def init_database(self):
        """Initialize SQLite database for metrics storage."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                environment TEXT,
                version TEXT,
                status TEXT,
                duration_seconds INTEGER,
                triggered_by TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                build_id TEXT,
                branch TEXT,
                status TEXT,
                duration_seconds INTEGER,
                test_results TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                severity TEXT,
                resolution_time_minutes INTEGER,
                root_cause TEXT,
                affected_service TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT,
                metric_value REAL,
                period TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def calculate_deployment_frequency(self, days: int = 30) -> float:
        """Calculate deployment frequency (deployments per day)."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        # Get deployments in the last N days
        since = datetime.now() - timedelta(days=days)
        cursor.execute("""
            SELECT COUNT(*) FROM deployments 
            WHERE timestamp > ? AND status = 'success' AND environment = 'production'
        """, (since.isoformat(),))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        # Calculate frequency
        frequency = count / days if days > 0 else 0
        return round(frequency, 2)

    def calculate_lead_time(self, days: int = 30) -> float:
        """Calculate lead time for changes (hours from commit to deploy)."""
        if not self.repo:
            return 0.0
        
        lead_times = []
        
        try:
            # Get recent deployments
            conn = sqlite3.connect(self.metrics_db)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(days=days)
            cursor.execute("""
                SELECT version, timestamp FROM deployments 
                WHERE timestamp > ? AND status = 'success' AND environment = 'production'
                ORDER BY timestamp DESC LIMIT 20
            """, (since.isoformat(),))
            
            deployments = cursor.fetchall()
            conn.close()
            
            for version, deploy_time in deployments:
                # Get commit time for this version
                try:
                    commit = self.repo.get_commit(version[:7] if len(version) > 7 else version)
                    commit_time = commit.commit.author.date
                    deploy_dt = datetime.fromisoformat(deploy_time)
                    
                    # Calculate lead time in hours
                    lead_time = (deploy_dt - commit_time).total_seconds() / 3600
                    lead_times.append(lead_time)
                except:
                    continue
            
            # Return average lead time
            if lead_times:
                return round(sum(lead_times) / len(lead_times), 2)
        except Exception as e:
            print(f"Error calculating lead time: {e}")
        
        return 0.0

    def calculate_mttr(self, days: int = 90) -> float:
        """Calculate Mean Time To Recovery (MTTR) in minutes."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        # Get incidents in the last N days
        since = datetime.now() - timedelta(days=days)
        cursor.execute("""
            SELECT resolution_time_minutes FROM incidents 
            WHERE timestamp > ? AND resolution_time_minutes IS NOT NULL
        """, (since.isoformat(),))
        
        recovery_times = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if recovery_times:
            return round(sum(recovery_times) / len(recovery_times), 2)
        return 0.0

    def calculate_change_failure_rate(self, days: int = 30) -> float:
        """Calculate change failure rate (percentage of deployments causing incidents)."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        # Get total deployments
        cursor.execute("""
            SELECT COUNT(*) FROM deployments 
            WHERE timestamp > ? AND environment = 'production'
        """, (since.isoformat(),))
        total_deployments = cursor.fetchone()[0]
        
        # Get failed deployments
        cursor.execute("""
            SELECT COUNT(*) FROM deployments 
            WHERE timestamp > ? AND status = 'failed' AND environment = 'production'
        """, (since.isoformat(),))
        failed_deployments = cursor.fetchone()[0]
        
        conn.close()
        
        if total_deployments > 0:
            rate = (failed_deployments / total_deployments) * 100
            return round(rate, 2)
        return 0.0

    def calculate_build_success_rate(self, days: int = 7) -> float:
        """Calculate build success rate."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        # Get build statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM builds 
            WHERE timestamp > ?
        """, (since.isoformat(),))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            rate = (result[1] / result[0]) * 100
            return round(rate, 2)
        return 0.0

    def get_github_metrics(self) -> Dict:
        """Collect metrics from GitHub API."""
        metrics = {
            'open_prs': 0,
            'open_issues': 0,
            'stars': 0,
            'forks': 0,
            'contributors': 0,
            'workflow_runs': []
        }
        
        if not self.repo:
            return metrics
        
        try:
            # Basic repository metrics
            metrics['open_prs'] = self.repo.get_pulls(state='open').totalCount
            metrics['open_issues'] = self.repo.get_issues(state='open').totalCount
            metrics['stars'] = self.repo.stargazers_count
            metrics['forks'] = self.repo.forks_count
            metrics['contributors'] = self.repo.get_contributors().totalCount
            
            # Get recent workflow runs
            if hasattr(self.repo, 'get_workflow_runs'):
                runs = self.repo.get_workflow_runs()
                for run in runs[:20]:  # Last 20 runs
                    metrics['workflow_runs'].append({
                        'id': run.id,
                        'name': run.name,
                        'status': run.status,
                        'conclusion': run.conclusion,
                        'created_at': run.created_at.isoformat(),
                        'duration': (run.updated_at - run.created_at).total_seconds() if run.updated_at else 0
                    })
        except Exception as e:
            print(f"Error collecting GitHub metrics: {e}")
        
        return metrics

    def record_deployment(self, environment: str, version: str, status: str, 
                         duration: int, triggered_by: str = 'unknown'):
        """Record a deployment event."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO deployments (environment, version, status, duration_seconds, triggered_by)
            VALUES (?, ?, ?, ?, ?)
        """, (environment, version, status, duration, triggered_by))
        
        conn.commit()
        conn.close()
        
        # Publish to Redis if available
        if self.redis_available:
            self.redis_client.publish(
                'terminal:debugger:deployment_recorded',
                json.dumps({
                    'environment': environment,
                    'version': version,
                    'status': status,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
            )

    def record_build(self, build_id: str, branch: str, status: str, 
                    duration: int, test_results: Optional[Dict] = None):
        """Record a build event."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO builds (build_id, branch, status, duration_seconds, test_results)
            VALUES (?, ?, ?, ?, ?)
        """, (build_id, branch, status, duration, json.dumps(test_results) if test_results else None))
        
        conn.commit()
        conn.close()

    def record_incident(self, severity: str, resolution_time: int, 
                       root_cause: str, affected_service: str):
        """Record an incident."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO incidents (severity, resolution_time_minutes, root_cause, affected_service)
            VALUES (?, ?, ?, ?)
        """, (severity, resolution_time, root_cause, affected_service))
        
        conn.commit()
        conn.close()

    async def collect_all_metrics(self) -> Dict:
        """Collect all metrics."""
        print("📊 Collecting CI/CD metrics...")
        
        # Calculate DORA metrics
        self.dora_metrics['deployment_frequency'] = self.calculate_deployment_frequency()
        self.dora_metrics['lead_time_for_changes'] = self.calculate_lead_time()
        self.dora_metrics['mean_time_to_recovery'] = self.calculate_mttr()
        self.dora_metrics['change_failure_rate'] = self.calculate_change_failure_rate()
        
        # Calculate additional metrics
        self.additional_metrics['build_success_rate'] = self.calculate_build_success_rate()
        
        # Get GitHub metrics
        github_metrics = self.get_github_metrics()
        
        # Store snapshot.json
        self.store_metrics_snapshot()
        
        # Combine all metrics
        all_metrics = {
            'dora': self.dora_metrics,
            'additional': self.additional_metrics,
            'github': github_metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to Debugger terminal if Redis available
        if self.redis_available:
            self.redis_client.publish(
                'terminal:debugger:ci_metrics',
                json.dumps(all_metrics)
            )
        
        return all_metrics

    def store_metrics_snapshot(self):
        """Store current metrics snapshot.json in database."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        # Store DORA metrics
        for name, value in self.dora_metrics.items():
            cursor.execute("""
                INSERT INTO metrics_snapshot (metric_name, metric_value, period)
                VALUES (?, ?, ?)
            """, (f"dora_{name}", value, 'daily'))
        
        # Store additional metrics
        for name, value in self.additional_metrics.items():
            cursor.execute("""
                INSERT INTO metrics_snapshot (metric_name, metric_value, period)
                VALUES (?, ?, ?)
            """, (f"additional_{name}", value, 'daily'))
        
        conn.commit()
        conn.close()

    def generate_metrics_report(self, output_file: Optional[str] = None):
        """Generate a comprehensive metrics report."""
        metrics = asyncio.run(self.collect_all_metrics())
        
        report = []
        report.append("=" * 60)
        report.append("📊 CI/CD METRICS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # DORA Metrics
        report.append("🎯 DORA Metrics")
        report.append("-" * 40)
        report.append(f"Deployment Frequency: {metrics['dora']['deployment_frequency']} deploys/day")
        report.append(f"Lead Time for Changes: {metrics['dora']['lead_time_for_changes']} hours")
        report.append(f"Mean Time To Recovery: {metrics['dora']['mean_time_to_recovery']} minutes")
        report.append(f"Change Failure Rate: {metrics['dora']['change_failure_rate']}%")
        report.append("")
        
        # Performance Classification
        report.append("🏆 Performance Level")
        report.append("-" * 40)
        perf_level = self.classify_performance(metrics['dora'])
        report.append(f"Overall: {perf_level}")
        report.append("")
        
        # Additional Metrics
        report.append("📈 Additional Metrics")
        report.append("-" * 40)
        report.append(f"Build Success Rate: {metrics['additional']['build_success_rate']}%")
        report.append("")
        
        # GitHub Metrics
        if metrics['github']:
            report.append("🐙 GitHub Metrics")
            report.append("-" * 40)
            report.append(f"Open PRs: {metrics['github']['open_prs']}")
            report.append(f"Open Issues: {metrics['github']['open_issues']}")
            report.append(f"Stars: {metrics['github']['stars']}")
            report.append(f"Contributors: {metrics['github']['contributors']}")
            report.append("")
        
        # Recent Workflow Runs
        if metrics['github'].get('workflow_runs'):
            report.append("🔄 Recent Workflow Runs")
            report.append("-" * 40)
            
            success_count = sum(1 for run in metrics['github']['workflow_runs'] 
                              if run['conclusion'] == 'success')
            total_count = len(metrics['github']['workflow_runs'])
            
            report.append(f"Success Rate: {(success_count/total_count*100):.1f}% ({success_count}/{total_count})")
            report.append("")
        
        # Recommendations
        report.append("💡 Recommendations")
        report.append("-" * 40)
        recommendations = self.generate_recommendations(metrics)
        for rec in recommendations:
            report.append(f"• {rec}")
        
        report.append("")
        report.append("=" * 60)
        
        # Output report
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to: {output_file}")
        else:
            print(report_text)
        
        return report_text

    def classify_performance(self, dora_metrics: Dict) -> str:
        """Classify performance level based on DORA metrics."""
        score = 0
        
        # Deployment frequency (higher is better)
        if dora_metrics['deployment_frequency'] >= 1.0:  # Daily or more
            score += 3
        elif dora_metrics['deployment_frequency'] >= 0.25:  # Weekly
            score += 2
        elif dora_metrics['deployment_frequency'] >= 0.03:  # Monthly
            score += 1
        
        # Lead time (lower is better)
        if dora_metrics['lead_time_for_changes'] <= 24:  # Less than a day
            score += 3
        elif dora_metrics['lead_time_for_changes'] <= 168:  # Less than a week
            score += 2
        elif dora_metrics['lead_time_for_changes'] <= 720:  # Less than a month
            score += 1
        
        # MTTR (lower is better)
        if dora_metrics['mean_time_to_recovery'] <= 60:  # Less than an hour
            score += 3
        elif dora_metrics['mean_time_to_recovery'] <= 1440:  # Less than a day
            score += 2
        elif dora_metrics['mean_time_to_recovery'] <= 10080:  # Less than a week
            score += 1
        
        # Change failure rate (lower is better)
        if dora_metrics['change_failure_rate'] <= 5:
            score += 3
        elif dora_metrics['change_failure_rate'] <= 15:
            score += 2
        elif dora_metrics['change_failure_rate'] <= 30:
            score += 1
        
        # Classify based on total score
        if score >= 10:
            return "🚀 Elite Performer"
        elif score >= 7:
            return "⭐ High Performer"
        elif score >= 4:
            return "📊 Medium Performer"
        else:
            return "📈 Low Performer (Improvement Needed)"

    def generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        dora = metrics['dora']
        
        # Deployment frequency
        if dora['deployment_frequency'] < 0.25:
            recommendations.append("Increase deployment frequency - aim for at least weekly deployments")
        
        # Lead time
        if dora['lead_time_for_changes'] > 168:
            recommendations.append("Reduce lead time - optimize CI/CD pipeline and review process")
        
        # MTTR
        if dora['mean_time_to_recovery'] > 60:
            recommendations.append("Improve incident response - implement better monitoring and rollback procedures")
        
        # Change failure rate
        if dora['change_failure_rate'] > 15:
            recommendations.append("Reduce failure rate - improve testing and code review practices")
        
        # Build success rate
        if metrics['additional']['build_success_rate'] < 90:
            recommendations.append("Improve build stability - fix flaky tests and environment issues")
        
        # GitHub metrics
        if metrics['github'].get('open_prs', 0) > 10:
            recommendations.append("Review pending PRs - reduce review cycle time")
        
        if not recommendations:
            recommendations.append("Great job! Continue monitoring and maintaining current performance levels")
        
        return recommendations

    def generate_trend_charts(self, days: int = 30):
        """Generate trend charts for metrics."""
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        # Get historical data
        since = datetime.now() - timedelta(days=days)
        cursor.execute("""
            SELECT timestamp, metric_name, metric_value 
            FROM metrics_snapshot 
            WHERE timestamp > ? 
            ORDER BY timestamp
        """, (since.isoformat(),))
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            print("No historical data available for charts")
            return
        
        # Organize data by metric
        metrics_data = defaultdict(lambda: {'timestamps': [], 'values': []})
        
        for timestamp, metric_name, value in data:
            dt = datetime.fromisoformat(timestamp)
            metrics_data[metric_name]['timestamps'].append(dt)
            metrics_data[metric_name]['values'].append(value)
        
        # Create charts
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('CI/CD Metrics Trends', fontsize=16)
        
        # Chart 1: Deployment Frequency
        ax = axes[0, 0]
        if 'dora_deployment_frequency' in metrics_data:
            data = metrics_data['dora_deployment_frequency']
            ax.plot(data['timestamps'], data['values'], marker='o')
            ax.set_title('Deployment Frequency')
            ax.set_ylabel('Deploys/Day')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Chart 2: Lead Time
        ax = axes[0, 1]
        if 'dora_lead_time_for_changes' in metrics_data:
            data = metrics_data['dora_lead_time_for_changes']
            ax.plot(data['timestamps'], data['values'], marker='o', color='orange')
            ax.set_title('Lead Time for Changes')
            ax.set_ylabel('Hours')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Chart 3: MTTR
        ax = axes[1, 0]
        if 'dora_mean_time_to_recovery' in metrics_data:
            data = metrics_data['dora_mean_time_to_recovery']
            ax.plot(data['timestamps'], data['values'], marker='o', color='red')
            ax.set_title('Mean Time To Recovery')
            ax.set_ylabel('Minutes')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Chart 4: Build Success Rate
        ax = axes[1, 1]
        if 'additional_build_success_rate' in metrics_data:
            data = metrics_data['additional_build_success_rate']
            ax.plot(data['timestamps'], data['values'], marker='o', color='green')
            ax.set_title('Build Success Rate')
            ax.set_ylabel('Percentage')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Adjust layout and save
        plt.tight_layout()
        
        output_file = self.project_root / "logs" / "metrics_trends.png"
        plt.savefig(output_file, dpi=100)
        print(f"📊 Trend charts saved to: {output_file}")
        
        plt.close()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='CI/CD Metrics Collection')
    parser.add_argument('--report', action='store_true',
                       help='Generate metrics report')
    parser.add_argument('--charts', action='store_true',
                       help='Generate trend charts')
    parser.add_argument('--record-deployment', nargs=4,
                       metavar=('ENV', 'VERSION', 'STATUS', 'DURATION'),
                       help='Record a deployment')
    parser.add_argument('--record-build', nargs=4,
                       metavar=('ID', 'BRANCH', 'STATUS', 'DURATION'),
                       help='Record a build')
    parser.add_argument('--output', help='Output file for report')
    
    args = parser.parse_args()
    
    metrics = CICDMetrics()
    
    if args.record_deployment:
        env, version, status, duration = args.record_deployment
        metrics.record_deployment(env, version, status, int(duration))
        print(f"✅ Recorded deployment: {env} v{version} ({status})")
    
    elif args.record_build:
        build_id, branch, status, duration = args.record_build
        metrics.record_build(build_id, branch, status, int(duration))
        print(f"✅ Recorded build: {build_id} on {branch} ({status})")
    
    elif args.charts:
        metrics.generate_trend_charts()
    
    elif args.report:
        metrics.generate_metrics_report(args.output)
    
    else:
        # Default: collect and display current metrics
        all_metrics = await metrics.collect_all_metrics()
        print(json.dumps(all_metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main())