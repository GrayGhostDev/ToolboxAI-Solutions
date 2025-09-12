#!/usr/bin/env python3
"""
Cleanup Monitoring and Metrics Collection
Based on CLEANUP_INTEGRATED.md monitoring protocols
"""

import os
import sys
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import subprocess

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class CleanupMetrics:
    """Collect and report cleanup metrics"""
    
    def __init__(self):
        self.project_path = PROJECT_ROOT
        self.logs_dir = self.project_path / 'logs' / 'cleanup'
        self.metrics = {
            'last_cleanup': None,
            'total_space_freed': 0,
            'cleanup_runs': 0,
            'average_duration': 0,
            'failure_rate': 0,
            'current_usage': {}
        }
    
    def format_size(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get current disk usage statistics"""
        result = subprocess.run(
            ['df', '-k', '/Volumes/G-DRIVE ArmorATD'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    total = int(parts[1]) * 1024  # Convert from KB to bytes
                    used = int(parts[2]) * 1024
                    available = int(parts[3]) * 1024
                    percent = float(parts[4].strip('%')) if '%' in parts[4] else 0
                    
                    return {
                        'total': total,
                        'used': used,
                        'available': available,
                        'percent': percent,
                        'total_formatted': self.format_size(total),
                        'used_formatted': self.format_size(used),
                        'available_formatted': self.format_size(available)
                    }
        
        return {}
    
    def get_project_size(self) -> int:
        """Calculate project directory size"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.project_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass
        return total_size
    
    def count_artifacts(self) -> Dict[str, int]:
        """Count cleanup-able artifacts"""
        counts = {
            'pycache': 0,
            'pyc_files': 0,
            'node_modules': 0,
            'dist_dirs': 0,
            'build_dirs': 0,
            'log_files': 0
        }
        
        # Count Python artifacts
        counts['pycache'] = len(list(self.project_path.glob('**/__pycache__')))
        counts['pyc_files'] = len(list(self.project_path.glob('**/*.pyc')))
        
        # Count Node.js artifacts
        counts['node_modules'] = len(list(self.project_path.glob('**/node_modules')))
        
        # Count build artifacts
        counts['dist_dirs'] = len(list(self.project_path.glob('**/dist')))
        counts['build_dirs'] = len(list(self.project_path.glob('**/build')))
        
        # Count log files
        counts['log_files'] = len(list(self.project_path.glob('**/*.log')))
        
        return counts
    
    def load_cleanup_history(self) -> List[Dict]:
        """Load historical cleanup data"""
        history = []
        
        if self.logs_dir.exists():
            for report_file in sorted(self.logs_dir.glob('cleanup_*.json')):
                try:
                    with open(report_file, 'r') as f:
                        data = json.load(f)
                        history.append(data)
                except:
                    pass
        
        return history
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate cleanup performance metrics"""
        # Load historical data
        history = self.load_cleanup_history()
        
        # Calculate metrics
        if history:
            self.metrics['cleanup_runs'] = len(history)
            self.metrics['total_space_freed'] = sum(r.get('space_freed', 0) for r in history)
            
            durations = [r.get('duration', 0) for r in history if 'duration' in r]
            if durations:
                self.metrics['average_duration'] = sum(durations) / len(durations)
            
            errors = [r for r in history if r.get('errors')]
            self.metrics['failure_rate'] = (len(errors) / len(history)) * 100 if history else 0
            
            if history:
                last_cleanup = history[-1]
                self.metrics['last_cleanup'] = last_cleanup.get('timestamp')
        
        # Get current usage
        self.metrics['current_usage'] = self.get_disk_usage()
        self.metrics['project_size'] = self.get_project_size()
        self.metrics['artifact_counts'] = self.count_artifacts()
        
        return self.metrics
    
    def generate_report(self) -> str:
        """Generate cleanup status report"""
        metrics = self.calculate_metrics()
        
        report = []
        report.append("=" * 60)
        report.append("📊 ToolBoxAI Cleanup Monitoring Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Disk usage
        report.append("💾 Disk Usage")
        report.append("-" * 40)
        if metrics['current_usage']:
            usage = metrics['current_usage']
            report.append(f"Total: {usage['total_formatted']}")
            report.append(f"Used: {usage['used_formatted']} ({usage['percent']:.1f}%)")
            report.append(f"Available: {usage['available_formatted']}")
            
            # Status indicator
            if usage['percent'] < 60:
                status = "✅ Healthy"
            elif usage['percent'] < 80:
                status = "⚠️ Monitor"
            else:
                status = "🚨 Critical"
            report.append(f"Status: {status}")
        report.append("")
        
        # Project size
        report.append("📁 Project Statistics")
        report.append("-" * 40)
        report.append(f"Project Size: {self.format_size(metrics['project_size'])}")
        report.append("")
        
        # Artifact counts
        report.append("🗑️ Cleanable Artifacts")
        report.append("-" * 40)
        counts = metrics['artifact_counts']
        report.append(f"Python __pycache__: {counts['pycache']}")
        report.append(f"Python .pyc files: {counts['pyc_files']}")
        report.append(f"Node modules: {counts['node_modules']}")
        report.append(f"Dist directories: {counts['dist_dirs']}")
        report.append(f"Build directories: {counts['build_dirs']}")
        report.append(f"Log files: {counts['log_files']}")
        report.append("")
        
        # Cleanup history
        report.append("📈 Cleanup History")
        report.append("-" * 40)
        report.append(f"Total runs: {metrics['cleanup_runs']}")
        report.append(f"Total space freed: {self.format_size(metrics['total_space_freed'])}")
        
        if metrics['average_duration'] > 0:
            report.append(f"Average duration: {metrics['average_duration']:.1f} seconds")
        
        if metrics['failure_rate'] > 0:
            report.append(f"Failure rate: {metrics['failure_rate']:.1f}%")
        
        if metrics['last_cleanup']:
            last_cleanup_time = datetime.fromisoformat(metrics['last_cleanup'])
            days_ago = (datetime.now() - last_cleanup_time).days
            report.append(f"Last cleanup: {last_cleanup_time.strftime('%Y-%m-%d %H:%M')} ({days_ago} days ago)")
        else:
            report.append("Last cleanup: Never")
        report.append("")
        
        # Recommendations
        report.append("💡 Recommendations")
        report.append("-" * 40)
        
        recommendations = []
        
        # Check if cleanup is needed
        if counts['pycache'] > 100 or counts['pyc_files'] > 500:
            recommendations.append("• Run Python cleanup (many cache files detected)")
        
        if counts['node_modules'] > 5:
            recommendations.append("• Clean node_modules directories")
        
        if metrics['current_usage'] and metrics['current_usage']['percent'] > 80:
            recommendations.append("• ⚠️ Run emergency cleanup (disk usage high)")
        
        if metrics['last_cleanup']:
            last_cleanup_time = datetime.fromisoformat(metrics['last_cleanup'])
            if (datetime.now() - last_cleanup_time).days > 7:
                recommendations.append("• Schedule regular cleanup (last run > 7 days ago)")
        else:
            recommendations.append("• Run initial cleanup")
        
        if not recommendations:
            recommendations.append("• System is clean and healthy")
        
        for rec in recommendations:
            report.append(rec)
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, report: str):
        """Save report to file"""
        reports_dir = self.project_path / 'logs' / 'cleanup' / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"monitor_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📝 Report saved to: {report_file.relative_to(self.project_path)}")


def main():
    """Main entry point"""
    monitor = CleanupMetrics()
    report = monitor.generate_report()
    
    # Print report
    print(report)
    
    # Save report
    monitor.save_report(report)
    
    # Check if immediate cleanup is needed
    metrics = monitor.calculate_metrics()
    if metrics['current_usage'] and metrics['current_usage']['percent'] > 90:
        print("\n🚨 CRITICAL: Disk usage above 90%!")
        print("Run emergency cleanup immediately:")
        print(f"  {PROJECT_ROOT}/scripts/terminal_sync/emergency_cleanup.sh")


if __name__ == "__main__":
    main()