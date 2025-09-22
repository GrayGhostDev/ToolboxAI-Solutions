#!/usr/bin/env python3
"""
Performance Optimization Monitor
Tracks bundle size reduction from 950KB to <500KB target
"""

import subprocess
import json
import os
import time
import datetime
import gzip
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import sqlite3
import requests
import psutil

@dataclass
class BundleMetrics:
    total_size_kb: float
    gzipped_size_kb: float
    js_size_kb: float
    css_size_kb: float
    assets_size_kb: float
    chunks_count: int
    largest_chunk_kb: float
    tree_shaking_savings: float = 0.0

@dataclass
class APIMetrics:
    avg_response_time_ms: float
    p95_response_time_ms: float
    error_rate: float
    requests_per_second: float
    active_connections: int

@dataclass
class SystemMetrics:
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_recv_mb: float
    network_io_sent_mb: float

@dataclass
class PerformanceMetrics:
    timestamp: datetime.datetime
    bundle_metrics: BundleMetrics
    api_metrics: APIMetrics
    system_metrics: SystemMetrics
    overall_score: float
    target_score: float = 95.0
    trend: str = "stable"

class PerformanceMonitor:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.db_path = self.project_root / "monitoring" / "performance_metrics.db"
        self.target_bundle_size = 500.0  # KB
        self.baseline_bundle_size = 950.0  # KB
        self.api_base_url = "http://127.0.0.1:8009"
        self.dashboard_url = "http://127.0.0.1:5179"
        self.init_database()
        self.history = []

    def init_database(self):
        """Initialize SQLite database for performance tracking"""
        self.db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_scans (
                    timestamp DATETIME PRIMARY KEY,
                    bundle_size_kb REAL,
                    gzipped_size_kb REAL,
                    api_response_time_ms REAL,
                    error_rate REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL,
                    overall_score REAL,
                    trend TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bundle_analysis (
                    timestamp DATETIME,
                    file_path TEXT,
                    size_kb REAL,
                    type TEXT,
                    optimization_potential REAL
                )
            """)

    def analyze_bundle_size(self) -> BundleMetrics:
        """Analyze current bundle size and composition"""
        dashboard_dist = self.project_root / "apps" / "dashboard" / "dist"

        if not dashboard_dist.exists():
            # Try to build first
            print("📦 Building dashboard to analyze bundle size...")
            try:
                subprocess.run(
                    ["npm", "run", "build"],
                    cwd=self.project_root / "apps" / "dashboard",
                    check=True,
                    capture_output=True,
                    timeout=300
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                print("⚠️ Build failed, using estimated metrics")
                return self.estimate_bundle_metrics()

        if dashboard_dist.exists():
            return self.calculate_actual_bundle_metrics(dashboard_dist)
        else:
            return self.estimate_bundle_metrics()

    def calculate_actual_bundle_metrics(self, dist_dir: Path) -> BundleMetrics:
        """Calculate actual bundle metrics from built files"""
        total_size = 0
        js_size = 0
        css_size = 0
        assets_size = 0
        chunks = []

        for file_path in dist_dir.rglob('*'):
            if file_path.is_file():
                size_bytes = file_path.stat().st_size
                size_kb = size_bytes / 1024

                total_size += size_kb

                if file_path.suffix == '.js':
                    js_size += size_kb
                    chunks.append(size_kb)
                elif file_path.suffix == '.css':
                    css_size += size_kb
                else:
                    assets_size += size_kb

        # Calculate gzipped size estimate
        gzipped_size = total_size * 0.3  # Typical gzip compression ratio

        # Find largest chunk
        largest_chunk = max(chunks) if chunks else 0

        # Estimate tree shaking savings (simplified)
        tree_shaking_savings = max(0, self.baseline_bundle_size - total_size)

        return BundleMetrics(
            total_size_kb=total_size,
            gzipped_size_kb=gzipped_size,
            js_size_kb=js_size,
            css_size_kb=css_size,
            assets_size_kb=assets_size,
            chunks_count=len(chunks),
            largest_chunk_kb=largest_chunk,
            tree_shaking_savings=tree_shaking_savings
        )

    def estimate_bundle_metrics(self) -> BundleMetrics:
        """Estimate bundle metrics when build is not available"""
        # Analyze source files to estimate bundle size
        src_dir = self.project_root / "apps" / "dashboard" / "src"
        node_modules = self.project_root / "node_modules"

        total_src_size = 0
        js_files = 0

        if src_dir.exists():
            for file_path in src_dir.rglob('*.{tsx,ts,jsx,js}'):
                if file_path.is_file():
                    total_src_size += file_path.stat().st_size / 1024
                    js_files += 1

        # Estimate bundle size based on source size and dependencies
        estimated_bundle = total_src_size * 1.5  # Account for transpilation

        # Add estimated dependency size
        if node_modules.exists():
            try:
                # Sample key dependencies to estimate size
                key_deps = ['react', 'react-dom', '@mui/material', 'axios']
                dep_size = 0
                for dep in key_deps:
                    dep_path = node_modules / dep
                    if dep_path.exists():
                        try:
                            result = subprocess.run(
                                ["du", "-sk", str(dep_path)],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            if result.returncode == 0:
                                dep_size += int(result.stdout.split()[0])
                        except:
                            dep_size += 100  # Default estimate

                # Estimate 10% of dependencies make it to bundle
                estimated_bundle += (dep_size * 0.1)

            except Exception:
                estimated_bundle += 300  # Default dependency estimate

        # Ensure reasonable bounds
        estimated_bundle = max(200, min(1500, estimated_bundle))

        return BundleMetrics(
            total_size_kb=estimated_bundle,
            gzipped_size_kb=estimated_bundle * 0.35,
            js_size_kb=estimated_bundle * 0.8,
            css_size_kb=estimated_bundle * 0.15,
            assets_size_kb=estimated_bundle * 0.05,
            chunks_count=js_files // 10,
            largest_chunk_kb=estimated_bundle * 0.4,
            tree_shaking_savings=max(0, self.baseline_bundle_size - estimated_bundle)
        )

    def measure_api_performance(self) -> APIMetrics:
        """Measure API performance metrics"""
        endpoints = [
            "/health",
            "/api/v1/auth/check",
            "/api/v1/classes",
            "/api/v1/lessons"
        ]

        response_times = []
        error_count = 0
        total_requests = len(endpoints)

        start_time = time.time()

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{self.api_base_url}{endpoint}",
                    timeout=5,
                    headers={"Authorization": "Bearer test-token"}
                )
                response_times.append(response.elapsed.total_seconds() * 1000)
                if response.status_code >= 400:
                    error_count += 1
            except Exception:
                error_count += 1
                response_times.append(5000)  # Timeout as 5s

        total_time = time.time() - start_time
        avg_response_time = sum(response_times) / len(response_times) if response_times else 1000
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 1000
        error_rate = error_count / total_requests if total_requests > 0 else 1.0
        rps = total_requests / total_time if total_time > 0 else 1.0

        # Estimate active connections (simplified)
        active_connections = self.count_active_connections()

        return APIMetrics(
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            error_rate=error_rate,
            requests_per_second=rps,
            active_connections=active_connections
        )

    def count_active_connections(self) -> int:
        """Count active network connections"""
        try:
            connections = psutil.net_connections()
            api_connections = [
                conn for conn in connections
                if conn.laddr and conn.laddr.port in [8009, 5179]
                and conn.status == 'ESTABLISHED'
            ]
            return len(api_connections)
        except Exception:
            return 0

    def measure_system_performance(self) -> SystemMetrics:
        """Measure system performance metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_mb = memory.used / (1024 * 1024)

            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0

            # Network I/O
            network_io = psutil.net_io_counters()
            network_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
            network_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0

            return SystemMetrics(
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_recv_mb=network_recv_mb,
                network_io_sent_mb=network_sent_mb
            )

        except Exception as e:
            print(f"Error measuring system metrics: {e}")
            return SystemMetrics(512.0, 25.0, 0.0, 0.0, 0.0, 0.0)

    def calculate_performance_score(self, bundle_metrics: BundleMetrics,
                                  api_metrics: APIMetrics,
                                  system_metrics: SystemMetrics) -> float:
        """Calculate overall performance score"""

        # Bundle size score (40% weight)
        bundle_score = max(0, min(100, (self.target_bundle_size / bundle_metrics.total_size_kb) * 100))

        # API performance score (30% weight)
        api_score = 100
        if api_metrics.avg_response_time_ms > 200:
            api_score = max(0, 100 - (api_metrics.avg_response_time_ms - 200) / 10)
        if api_metrics.error_rate > 0.01:
            api_score = max(0, api_score - (api_metrics.error_rate * 1000))

        # System performance score (30% weight)
        system_score = 100
        if system_metrics.cpu_usage_percent > 80:
            system_score = max(0, 100 - (system_metrics.cpu_usage_percent - 80))
        if system_metrics.memory_usage_mb > 2048:
            system_score = max(0, system_score - (system_metrics.memory_usage_mb - 2048) / 50)

        # Weighted overall score
        overall_score = (bundle_score * 0.4 + api_score * 0.3 + system_score * 0.3)

        return min(100, max(0, overall_score))

    def analyze_optimization_opportunities(self, bundle_metrics: BundleMetrics) -> List[Dict]:
        """Analyze optimization opportunities"""
        opportunities = []

        # Bundle size optimizations
        if bundle_metrics.total_size_kb > self.target_bundle_size:
            size_reduction_needed = bundle_metrics.total_size_kb - self.target_bundle_size

            opportunities.append({
                'category': 'bundle_size',
                'priority': 'high',
                'description': f'Bundle size {size_reduction_needed:.0f}KB over target',
                'potential_savings_kb': size_reduction_needed,
                'effort_hours': size_reduction_needed / 100  # Rough estimate
            })

        # Large chunk analysis
        if bundle_metrics.largest_chunk_kb > 200:
            opportunities.append({
                'category': 'code_splitting',
                'priority': 'medium',
                'description': f'Large chunk detected: {bundle_metrics.largest_chunk_kb:.0f}KB',
                'potential_savings_kb': bundle_metrics.largest_chunk_kb * 0.3,
                'effort_hours': 2
            })

        # Tree shaking opportunities
        if bundle_metrics.tree_shaking_savings < 100:
            opportunities.append({
                'category': 'tree_shaking',
                'priority': 'medium',
                'description': 'Limited tree shaking detected',
                'potential_savings_kb': 50,
                'effort_hours': 1
            })

        # CSS optimization
        if bundle_metrics.css_size_kb > bundle_metrics.total_size_kb * 0.2:
            opportunities.append({
                'category': 'css_optimization',
                'priority': 'low',
                'description': 'CSS size optimization possible',
                'potential_savings_kb': bundle_metrics.css_size_kb * 0.3,
                'effort_hours': 1
            })

        return sorted(opportunities, key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}[x['priority']],
            -x['potential_savings_kb']
        ))

    def run_performance_scan(self) -> PerformanceMetrics:
        """Run comprehensive performance scan"""
        print("📊 Analyzing bundle size...")
        bundle_metrics = self.analyze_bundle_size()

        print("🌐 Measuring API performance...")
        api_metrics = self.measure_api_performance()

        print("💻 Measuring system performance...")
        system_metrics = self.measure_system_performance()

        overall_score = self.calculate_performance_score(bundle_metrics, api_metrics, system_metrics)

        # Determine trend
        trend = "stable"
        if self.history:
            last_score = self.history[-1].overall_score
            if overall_score > last_score + 5:
                trend = "improving"
            elif overall_score < last_score - 5:
                trend = "declining"

        # Store metrics
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_scans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.datetime.now().isoformat(),
                bundle_metrics.total_size_kb,
                bundle_metrics.gzipped_size_kb,
                api_metrics.avg_response_time_ms,
                api_metrics.error_rate,
                system_metrics.memory_usage_mb,
                system_metrics.cpu_usage_percent,
                overall_score,
                trend
            ))

        metrics = PerformanceMetrics(
            timestamp=datetime.datetime.now(),
            bundle_metrics=bundle_metrics,
            api_metrics=api_metrics,
            system_metrics=system_metrics,
            overall_score=overall_score,
            trend=trend
        )

        self.history.append(metrics)
        return metrics

    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """Generate detailed performance monitoring report"""

        def progress_bar(current: float, target: float, width: int = 30, reverse: bool = False) -> str:
            if reverse:  # For values where lower is better (like bundle size)
                percentage = min(100, (target / current) * 100)
            else:
                percentage = min(100, (current / target) * 100)
            filled = int(width * percentage / 100)
            bar = '█' * filled + '▒' * (width - filled)
            return f"[{bar}] {percentage:.1f}%"

        # Calculate improvements
        size_reduction = self.baseline_bundle_size - metrics.bundle_metrics.total_size_kb
        size_reduction_pct = (size_reduction / self.baseline_bundle_size) * 100

        report = f"""
{'='*70}
⚡ PERFORMANCE OPTIMIZATION MONITORING
{'='*70}
Last Scan: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

📊 OVERALL PERFORMANCE SCORE
Current: {metrics.overall_score:.1f}% / {metrics.target_score}%
{progress_bar(metrics.overall_score, metrics.target_score)}
Trend: {metrics.trend.upper()}

📦 BUNDLE SIZE OPTIMIZATION
Target: <{self.target_bundle_size}KB | Current: {metrics.bundle_metrics.total_size_kb:.1f}KB
{progress_bar(metrics.bundle_metrics.total_size_kb, self.target_bundle_size, reverse=True)}

Size Breakdown:
  📄 JavaScript: {metrics.bundle_metrics.js_size_kb:.1f}KB ({metrics.bundle_metrics.js_size_kb/metrics.bundle_metrics.total_size_kb*100:.1f}%)
  🎨 CSS:        {metrics.bundle_metrics.css_size_kb:.1f}KB ({metrics.bundle_metrics.css_size_kb/metrics.bundle_metrics.total_size_kb*100:.1f}%)
  📁 Assets:     {metrics.bundle_metrics.assets_size_kb:.1f}KB ({metrics.bundle_metrics.assets_size_kb/metrics.bundle_metrics.total_size_kb*100:.1f}%)
  🗜️  Gzipped:    {metrics.bundle_metrics.gzipped_size_kb:.1f}KB (estimated)

Progress from baseline ({self.baseline_bundle_size}KB):
  Size reduction: {size_reduction:.1f}KB ({size_reduction_pct:.1f}%)
  Remaining: {max(0, metrics.bundle_metrics.total_size_kb - self.target_bundle_size):.1f}KB to target

🌐 API PERFORMANCE
Average Response: {metrics.api_metrics.avg_response_time_ms:.1f}ms
P95 Response: {metrics.api_metrics.p95_response_time_ms:.1f}ms
Error Rate: {metrics.api_metrics.error_rate*100:.2f}%
RPS: {metrics.api_metrics.requests_per_second:.1f}
Active Connections: {metrics.api_metrics.active_connections}

💻 SYSTEM PERFORMANCE
Memory Usage: {metrics.system_metrics.memory_usage_mb:.1f}MB
CPU Usage: {metrics.system_metrics.cpu_usage_percent:.1f}%
Disk I/O: {metrics.system_metrics.disk_io_read_mb:.1f}MB read, {metrics.system_metrics.disk_io_write_mb:.1f}MB write
Network I/O: {metrics.system_metrics.network_io_recv_mb:.1f}MB recv, {metrics.system_metrics.network_io_sent_mb:.1f}MB sent
"""

        # Add optimization opportunities
        opportunities = self.analyze_optimization_opportunities(metrics.bundle_metrics)
        if opportunities:
            report += "\n🔧 OPTIMIZATION OPPORTUNITIES\n"
            for i, opp in enumerate(opportunities[:5], 1):
                priority_emoji = "🔥" if opp['priority'] == 'high' else "⚡" if opp['priority'] == 'medium' else "💡"
                report += f"\n{priority_emoji} #{i} - {opp['priority'].upper()}\n"
                report += f"   {opp['description']}\n"
                report += f"   Potential savings: {opp['potential_savings_kb']:.0f}KB\n"
                report += f"   Estimated effort: {opp['effort_hours']:.1f} hours\n"

        # Performance recommendations
        report += "\n🎯 IMMEDIATE ACTIONS\n"

        if metrics.bundle_metrics.total_size_kb > self.target_bundle_size * 1.5:
            report += "  🔥 CRITICAL: Bundle size significantly over target - implement code splitting\n"
        elif metrics.bundle_metrics.total_size_kb > self.target_bundle_size:
            report += "  ⚡ HIGH: Optimize bundle size - focus on tree shaking and dependency analysis\n"

        if metrics.api_metrics.avg_response_time_ms > 500:
            report += "  ⚠️ API performance issues - investigate backend optimization\n"

        if metrics.system_metrics.memory_usage_mb > 2048:
            report += "  💾 High memory usage detected - check for memory leaks\n"

        if metrics.overall_score >= 90:
            report += "  ✅ Performance on track - maintain current optimizations\n"

        # Timeline estimation
        if metrics.bundle_metrics.total_size_kb > self.target_bundle_size:
            remaining_kb = metrics.bundle_metrics.total_size_kb - self.target_bundle_size
            total_effort = sum(opp['effort_hours'] for opp in opportunities)

            report += f"""
⏱️ EFFORT ESTIMATION
Remaining size to optimize: {remaining_kb:.0f}KB
Total estimated effort: {total_effort:.1f} hours
High priority tasks: {len([o for o in opportunities if o['priority'] == 'high'])}
Quick wins available: {len([o for o in opportunities if o['effort_hours'] <= 1])}
"""

        report += f"\n{'='*70}\n"

        return report

    def export_metrics(self, metrics: PerformanceMetrics, output_file: str = None):
        """Export metrics to JSON for integration"""
        if output_file is None:
            output_file = self.project_root / "monitoring" / "performance_metrics.json"

        output_file = Path(output_file)
        output_file.parent.mkdir(exist_ok=True)

        data = {
            'timestamp': metrics.timestamp.isoformat(),
            'overall_score': metrics.overall_score,
            'target_score': metrics.target_score,
            'trend': metrics.trend,
            'bundle_metrics': asdict(metrics.bundle_metrics),
            'api_metrics': asdict(metrics.api_metrics),
            'system_metrics': asdict(metrics.system_metrics),
            'optimization_opportunities': self.analyze_optimization_opportunities(metrics.bundle_metrics),
            'progress': {
                'baseline_size_kb': self.baseline_bundle_size,
                'target_size_kb': self.target_bundle_size,
                'current_size_kb': metrics.bundle_metrics.total_size_kb,
                'size_reduction_kb': self.baseline_bundle_size - metrics.bundle_metrics.total_size_kb,
                'size_reduction_percent': ((self.baseline_bundle_size - metrics.bundle_metrics.total_size_kb) / self.baseline_bundle_size) * 100,
                'remaining_kb': max(0, metrics.bundle_metrics.total_size_kb - self.target_bundle_size)
            }
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"📁 Performance metrics exported to: {output_file}")

def main():
    """Main entry point for performance monitor"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Optimization Monitor")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    parser.add_argument("--export", type=str, help="Export metrics to JSON file")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--interval", type=int, default=600, help="Watch interval in seconds (default: 10 min)")
    parser.add_argument("--build", action="store_true", help="Force build before analysis")

    args = parser.parse_args()

    monitor = PerformanceMonitor(args.project_root)

    if args.build:
        print("🔨 Building dashboard for analysis...")
        try:
            subprocess.run(
                ["npm", "run", "build"],
                cwd=monitor.project_root / "apps" / "dashboard",
                check=True
            )
        except subprocess.CalledProcessError:
            print("⚠️ Build failed, will use estimated metrics")

    if args.watch:
        print("📊 Starting continuous performance monitoring...")
        import time

        try:
            while True:
                metrics = monitor.run_performance_scan()
                report = monitor.generate_performance_report(metrics)

                # Clear screen and show report
                import os
                os.system('clear' if os.name == 'posix' else 'cls')
                print(report)

                if args.export:
                    monitor.export_metrics(metrics, args.export)

                if (metrics.bundle_metrics.total_size_kb <= monitor.target_bundle_size and
                    metrics.overall_score >= metrics.target_score):
                    print("🎉 TARGET ACHIEVED! Performance optimized!")
                    break

                print(f"⏳ Next scan in {args.interval} seconds...")
                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")

    else:
        # Single run
        metrics = monitor.run_performance_scan()
        report = monitor.generate_performance_report(metrics)
        print(report)

        if args.export:
            monitor.export_metrics(metrics, args.export)

if __name__ == "__main__":
    main()