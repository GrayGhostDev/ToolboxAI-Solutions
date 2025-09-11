#!/usr/bin/env python3
"""
Intelligent Cleanup System for ToolBoxAI Educational Platform
Based on CLEANUP_INTEGRATED.md orchestrator design
"""

import os
import sys
import json
import glob
import shutil
import asyncio
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class PythonCleaner:
    """Clean Python build artifacts and caches"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.patterns = {
            'pycache': '**/__pycache__',
            'pyc_files': '**/*.pyc',
            'pyo_files': '**/*.pyo',
            'pytest_cache': '**/.pytest_cache',
            'coverage': '**/.coverage*',
            'htmlcov': '**/htmlcov',
            'dist': '**/dist',
            'build': '**/build',
            'egg_info': '**/*.egg-info',
            'wheels': '**/*.whl',
            'tox': '**/.tox',
            'mypy_cache': '**/.mypy_cache',
            'hypothesis': '**/.hypothesis',
            'ipynb_checkpoints': '**/.ipynb_checkpoints'
        }
    
    def get_dir_size(self, path: Path) -> int:
        """Calculate directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    async def clean_project(self, dry_run: bool = False) -> Dict[str, Any]:
        """Deep clean Python project"""
        stats = {
            'files_removed': 0,
            'dirs_removed': 0,
            'bytes_freed': 0,
            'patterns_cleaned': []
        }
        
        print("🐍 Cleaning Python artifacts...")
        
        for name, pattern in self.patterns.items():
            files = list(self.project_path.glob(pattern))
            
            if files:
                print(f"  Found {len(files)} {name} items")
                
            for file_path in files:
                try:
                    if file_path.is_dir():
                        size = self.get_dir_size(file_path)
                        if not dry_run:
                            shutil.rmtree(file_path, ignore_errors=True)
                        stats['dirs_removed'] += 1
                    else:
                        size = file_path.stat().st_size if file_path.exists() else 0
                        if not dry_run:
                            file_path.unlink(missing_ok=True)
                        stats['files_removed'] += 1
                    
                    stats['bytes_freed'] += size
                except Exception as e:
                    print(f"    Warning: Could not remove {file_path}: {e}")
            
            if files:
                stats['patterns_cleaned'].append(name)
        
        # Clean virtual environments if requested
        venvs = ['venv', '.venv', 'env', '.env', 'venv_clean', 'virtualenv']
        for venv in venvs:
            venv_path = self.project_path / venv
            if venv_path.exists() and self.should_clean_venv(venv_path):
                size = self.get_dir_size(venv_path)
                print(f"  Found virtual environment: {venv} ({self.format_size(size)})")
                if not dry_run:
                    shutil.rmtree(venv_path, ignore_errors=True)
                stats['bytes_freed'] += size
                stats['dirs_removed'] += 1
                stats['patterns_cleaned'].append(f'venv:{venv}')
        
        return stats
    
    def should_clean_venv(self, venv_path: Path) -> bool:
        """Check if virtual environment should be cleaned"""
        # Don't clean if recently used (within last 7 days)
        recent_threshold = datetime.now() - timedelta(days=7)
        
        try:
            for root, dirs, files in os.walk(venv_path):
                for file in files[:5]:  # Check first 5 files for performance
                    file_path = Path(root) / file
                    if file_path.stat().st_mtime > recent_threshold.timestamp():
                        return False
        except:
            pass
        
        return True
    
    def format_size(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"


class NodeCleaner:
    """Clean and optimize Node.js dependencies"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.patterns = [
            'node_modules/.cache',
            '.next',
            '.nuxt',
            'coverage',
            '.nyc_output',
            '.parcel-cache',
            '.turbo',
            '.yarn/cache',
            '.pnp.*'
        ]
    
    async def optimize_dependencies(self, dry_run: bool = False) -> Dict[str, Any]:
        """Optimize Node.js dependencies"""
        stats = {
            'modules_cleaned': 0,
            'cache_cleared': 0,
            'bytes_freed': 0
        }
        
        print("📦 Cleaning Node.js artifacts...")
        
        # Find all node_modules directories
        node_modules_dirs = list(self.project_path.glob('**/node_modules'))
        
        if node_modules_dirs:
            print(f"  Found {len(node_modules_dirs)} node_modules directories")
        
        for nm_dir in node_modules_dirs:
            # Skip if in important locations
            if 'backups' in str(nm_dir) or 'production' in str(nm_dir):
                continue
            
            try:
                size = self.get_dir_size(nm_dir)
                print(f"    {nm_dir.relative_to(self.project_path)}: {self.format_size(size)}")
                
                if not dry_run:
                    shutil.rmtree(nm_dir, ignore_errors=True)
                    stats['modules_cleaned'] += 1
                    stats['bytes_freed'] += size
            except Exception as e:
                print(f"    Warning: Could not remove {nm_dir}: {e}")
        
        # Clean other Node.js artifacts
        for pattern in self.patterns:
            for item in self.project_path.glob(f'**/{pattern}'):
                try:
                    if item.is_dir():
                        size = self.get_dir_size(item)
                        if not dry_run:
                            shutil.rmtree(item, ignore_errors=True)
                    else:
                        size = item.stat().st_size if item.exists() else 0
                        if not dry_run:
                            item.unlink(missing_ok=True)
                    
                    stats['cache_cleared'] += 1
                    stats['bytes_freed'] += size
                except:
                    pass
        
        return stats
    
    def get_dir_size(self, path: Path) -> int:
        """Calculate directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def format_size(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"


class LogCleaner:
    """Manage and clean log files"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.log_dirs = [
            'logs',
            'ToolboxAI-Roblox-Environment/logs',
            '.logs'
        ]
        self.archive_threshold = timedelta(days=7)
        self.delete_threshold = timedelta(days=30)
    
    async def manage_logs(self, dry_run: bool = False) -> Dict[str, Any]:
        """Archive and clean log files"""
        stats = {
            'files_archived': 0,
            'files_deleted': 0,
            'bytes_freed': 0
        }
        
        print("📝 Managing log files...")
        
        for log_dir_name in self.log_dirs:
            log_dir = self.project_path / log_dir_name
            if not log_dir.exists():
                continue
            
            for log_file in log_dir.glob('*.log*'):
                try:
                    file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
                    file_size = log_file.stat().st_size
                    
                    if file_age > self.delete_threshold:
                        print(f"  Deleting old log: {log_file.name}")
                        if not dry_run:
                            log_file.unlink()
                        stats['files_deleted'] += 1
                        stats['bytes_freed'] += file_size
                    elif file_age > self.archive_threshold and not log_file.suffix.endswith('.gz'):
                        print(f"  Archiving log: {log_file.name}")
                        if not dry_run:
                            await self.archive_log(log_file)
                        stats['files_archived'] += 1
                except Exception as e:
                    print(f"    Warning: Could not process {log_file}: {e}")
        
        return stats
    
    async def archive_log(self, log_file: Path):
        """Compress and archive log file"""
        import gzip
        
        archive_name = log_file.with_suffix(f'{log_file.suffix}.{datetime.now().strftime("%Y%m%d")}.gz')
        
        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_name, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        log_file.unlink()


class GitCleaner:
    """Clean Git repository"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    async def clean_repository(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean Git repository"""
        stats = {
            'branches_cleaned': 0,
            'size_before': 0,
            'size_after': 0,
            'optimized': False
        }
        
        print("🔀 Cleaning Git repository...")
        
        # Get initial size
        git_dir = self.project_path / '.git'
        if git_dir.exists():
            stats['size_before'] = self.get_dir_size(git_dir)
            print(f"  Git directory size: {self.format_size(stats['size_before'])}")
            
            if not dry_run:
                # Run garbage collection
                try:
                    result = subprocess.run(
                        ['git', 'gc', '--aggressive', '--prune=now'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        stats['optimized'] = True
                        print("  ✓ Git garbage collection completed")
                    else:
                        print(f"  ⚠ Git gc warning: {result.stderr}")
                except Exception as e:
                    print(f"  ⚠ Could not run git gc: {e}")
                
                # Get final size
                stats['size_after'] = self.get_dir_size(git_dir)
                print(f"  Git directory size after: {self.format_size(stats['size_after'])}")
                print(f"  Space freed: {self.format_size(stats['size_before'] - stats['size_after'])}")
        
        return stats
    
    def get_dir_size(self, path: Path) -> int:
        """Calculate directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def format_size(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"


class IntelligentCleaner:
    """Main cleanup orchestrator"""
    
    def __init__(self):
        self.project_path = PROJECT_ROOT
        self.cleaners = {
            'python': PythonCleaner(self.project_path),
            'node': NodeCleaner(self.project_path),
            'logs': LogCleaner(self.project_path),
            'git': GitCleaner(self.project_path)
        }
    
    async def run_cleanup_pipeline(self, aggressive: bool = False, dry_run: bool = False, 
                                  specific: List[str] = None) -> Dict[str, Any]:
        """Run complete cleanup pipeline"""
        start_time = datetime.now()
        total_stats = {
            'space_freed': 0,
            'files_removed': 0,
            'operations': [],
            'errors': []
        }
        
        print("\n" + "="*60)
        print("🧹 ToolBoxAI Intelligent Cleanup System")
        print("="*60)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be deleted")
        
        print(f"📍 Project: {self.project_path}")
        print(f"⏰ Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Determine which cleaners to run
        if specific:
            cleaners_to_run = {k: v for k, v in self.cleaners.items() if k in specific}
        else:
            cleaners_to_run = self.cleaners
        
        # Run cleaners in priority order
        priority_order = ['logs', 'python', 'node', 'git']
        
        for cleaner_name in priority_order:
            if cleaner_name not in cleaners_to_run:
                continue
                
            cleaner = cleaners_to_run[cleaner_name]
            
            try:
                # Run cleanup
                if cleaner_name == 'python':
                    stats = await cleaner.clean_project(dry_run=dry_run)
                elif cleaner_name == 'node':
                    stats = await cleaner.optimize_dependencies(dry_run=dry_run)
                elif cleaner_name == 'logs':
                    stats = await cleaner.manage_logs(dry_run=dry_run)
                elif cleaner_name == 'git':
                    stats = await cleaner.clean_repository(dry_run=dry_run)
                else:
                    continue
                
                # Aggregate stats
                if 'bytes_freed' in stats:
                    total_stats['space_freed'] += stats['bytes_freed']
                if 'files_removed' in stats:
                    total_stats['files_removed'] += stats.get('files_removed', 0)
                if 'dirs_removed' in stats:
                    total_stats['files_removed'] += stats.get('dirs_removed', 0)
                
                total_stats['operations'].append({
                    'cleaner': cleaner_name,
                    'stats': stats
                })
                
                print(f"  ✓ {cleaner_name.capitalize()} cleanup completed\n")
                
            except Exception as e:
                error_msg = f"Error in {cleaner_name}: {e}"
                print(f"  ✗ {error_msg}\n")
                total_stats['errors'].append(error_msg)
        
        # Generate report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📊 Cleanup Summary")
        print("="*60)
        print(f"⏱  Duration: {duration:.2f} seconds")
        print(f"💾 Space freed: {self.format_size(total_stats['space_freed'])}")
        print(f"📄 Items removed: {total_stats['files_removed']}")
        
        if total_stats['errors']:
            print(f"⚠  Errors: {len(total_stats['errors'])}")
            for error in total_stats['errors']:
                print(f"   - {error}")
        
        print("="*60 + "\n")
        
        # Save report
        if not dry_run:
            report = {
                'timestamp': start_time.isoformat(),
                'duration': duration,
                'space_freed': total_stats['space_freed'],
                'items_removed': total_stats['files_removed'],
                'operations': total_stats['operations'],
                'errors': total_stats['errors']
            }
            
            report_dir = self.project_path / 'logs' / 'cleanup'
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / f"cleanup_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📝 Report saved to: {report_file.relative_to(self.project_path)}")
        
        return total_stats
    
    def format_size(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Intelligent Cleanup System for ToolBoxAI Educational Platform'
    )
    
    parser.add_argument(
        '--aggressive',
        action='store_true',
        help='Perform aggressive cleanup (removes more files)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be cleaned without actually deleting'
    )
    
    parser.add_argument(
        '--type',
        nargs='+',
        choices=['python', 'node', 'logs', 'git', 'all'],
        default=['all'],
        help='Specific cleanup types to run'
    )
    
    args = parser.parse_args()
    
    # Determine which cleaners to run
    if 'all' in args.type:
        specific = None
    else:
        specific = args.type
    
    # Create and run cleaner
    cleaner = IntelligentCleaner()
    await cleaner.run_cleanup_pipeline(
        aggressive=args.aggressive,
        dry_run=args.dry_run,
        specific=specific
    )


if __name__ == "__main__":
    asyncio.run(main())