#!/usr/bin/env python3
"""
Real-time documentation monitoring and auto-updater
Watches for code changes and automatically regenerates relevant documentation
"""

import asyncio
import json
import redis
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import subprocess
import hashlib
import time

class DocumentationMonitor:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Watch patterns for different file types
        self.watch_patterns = {
            'api': {
                'paths': ['server/', 'ToolboxAI-Roblox-Environment/server/'],
                'extensions': ['.py'],
                'doc_generator': 'generate_api_docs.py',
                'doc_type': 'API'
            },
            'components': {
                'paths': ['src/dashboard/src/components/'],
                'extensions': ['.tsx', '.jsx', '.ts', '.js'],
                'doc_generator': 'scan_components.py',
                'doc_type': 'Component'
            },
            'database': {
                'paths': ['database/schemas/'],
                'extensions': ['.sql'],
                'doc_generator': 'document_schemas.py',
                'doc_type': 'Database'
            },
            'roblox': {
                'paths': ['Roblox/Scripts/', 'ToolboxAI-Roblox-Environment/Roblox/Scripts/'],
                'extensions': ['.lua'],
                'doc_generator': None,  # Will implement Lua doc generator
                'doc_type': 'Roblox'
            }
        }
        
        # File hash cache to detect real changes
        self.file_hashes = {}
        self.load_hash_cache()
        
        # Documentation status
        self.doc_status = {
            'last_update': {},
            'pending_updates': set(),
            'update_in_progress': False
        }
        
    def load_hash_cache(self):
        """Load cached file hashes"""
        cache_file = self.project_root / '.claude-code' / 'doc_hashes.json'
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.file_hashes = json.load(f)
    
    def save_hash_cache(self):
        """Save file hashes to cache"""
        cache_dir = self.project_root / '.claude-code'
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / 'doc_hashes.json'
        with open(cache_file, 'w') as f:
            json.dump(self.file_hashes, f, indent=2)
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute hash of a file"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    async def monitor_files(self, auto_update: bool = True, notify_terminals: bool = True):
        """Main monitoring loop"""
        print("🔍 Starting documentation monitoring...")
        print(f"  Auto-update: {'✅' if auto_update else '❌'}")
        print(f"  Terminal notifications: {'✅' if notify_terminals else '❌'}")
        
        while True:
            try:
                # Check for changes
                changes = await self.detect_changes()
                
                if changes and auto_update:
                    await self.process_changes(changes, notify_terminals)
                
                # Sleep before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                print("\n⏹️  Stopping documentation monitor...")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def detect_changes(self) -> Dict[str, List[Path]]:
        """Detect changed files that need documentation updates"""
        changes = {}
        
        for doc_type, config in self.watch_patterns.items():
            changed_files = []
            
            for base_path in config['paths']:
                path = self.project_root / base_path
                if not path.exists():
                    continue
                
                # Find all matching files
                for ext in config['extensions']:
                    for file_path in path.rglob(f"*{ext}"):
                        # Skip test files
                        if 'test' in file_path.name.lower() or '__pycache__' in str(file_path):
                            continue
                        
                        # Check if file has changed
                        file_str = str(file_path)
                        current_hash = self.compute_file_hash(file_path)
                        
                        if file_str not in self.file_hashes or self.file_hashes[file_str] != current_hash:
                            changed_files.append(file_path)
                            self.file_hashes[file_str] = current_hash
            
            if changed_files:
                changes[doc_type] = changed_files
        
        return changes
    
    async def process_changes(self, changes: Dict[str, List[Path]], notify_terminals: bool):
        """Process detected changes and update documentation"""
        if self.doc_status['update_in_progress']:
            print("⏳ Documentation update already in progress...")
            return
        
        self.doc_status['update_in_progress'] = True
        
        try:
            for doc_type, changed_files in changes.items():
                print(f"\n📝 Detected {len(changed_files)} changed {doc_type} files")
                
                # Add to pending updates
                for file_path in changed_files:
                    self.doc_status['pending_updates'].add((doc_type, str(file_path)))
                
                # Run appropriate documentation generator
                config = self.watch_patterns[doc_type]
                if config['doc_generator']:
                    await self.regenerate_documentation(doc_type, config, changed_files)
                
                # Notify terminals if enabled
                if notify_terminals:
                    await self.notify_terminals(doc_type, changed_files)
                
                # Update status
                self.doc_status['last_update'][doc_type] = datetime.now().isoformat()
            
            # Save hash cache
            self.save_hash_cache()
            
        finally:
            self.doc_status['update_in_progress'] = False
    
    async def regenerate_documentation(self, doc_type: str, config: Dict, changed_files: List[Path]):
        """Regenerate documentation for a specific type"""
        print(f"🔄 Regenerating {doc_type} documentation...")
        
        script_path = self.project_root / 'scripts' / 'terminal_sync' / config['doc_generator']
        
        if not script_path.exists():
            print(f"⚠️  Documentation generator not found: {script_path}")
            return
        
        try:
            # Run the documentation generator
            result = subprocess.run(
                ['python', str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                print(f"✅ Successfully regenerated {doc_type} documentation")
                
                # Clear pending updates for this type
                self.doc_status['pending_updates'] = {
                    (t, f) for t, f in self.doc_status['pending_updates']
                    if t != doc_type
                }
            else:
                print(f"❌ Failed to regenerate {doc_type} documentation:")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error regenerating {doc_type} documentation: {e}")
    
    async def notify_terminals(self, doc_type: str, changed_files: List[Path]):
        """Notify other terminals about documentation updates"""
        try:
            # Prepare notification message
            message = {
                'timestamp': datetime.now().isoformat(),
                'terminal': 'documentation',
                'type': 'doc_update',
                'doc_type': doc_type,
                'files_changed': len(changed_files),
                'files': [str(f.relative_to(self.project_root)) for f in changed_files[:10]]  # First 10 files
            }
            
            # Publish to Redis channels
            channels = [
                'terminal:all:documentation',
                f'terminal:documentation:{doc_type.lower()}'
            ]
            
            for channel in channels:
                self.redis_client.publish(channel, json.dumps(message))
            
            print(f"📢 Notified terminals about {doc_type} documentation update")
            
        except Exception as e:
            print(f"⚠️  Failed to notify terminals: {e}")
    
    def get_documentation_status(self) -> Dict:
        """Get current documentation status"""
        status = {
            'monitoring': True,
            'last_updates': self.doc_status['last_update'],
            'pending_updates': list(self.doc_status['pending_updates']),
            'update_in_progress': self.doc_status['update_in_progress'],
            'file_cache_size': len(self.file_hashes),
            'watch_patterns': list(self.watch_patterns.keys())
        }
        return status
    
    async def force_regenerate_all(self):
        """Force regeneration of all documentation"""
        print("🔄 Force regenerating all documentation...")
        
        for doc_type, config in self.watch_patterns.items():
            if config['doc_generator']:
                await self.regenerate_documentation(doc_type, config, [])
        
        print("✅ All documentation regenerated")
    
    async def check_documentation_health(self) -> Dict:
        """Check health of documentation"""
        health = {
            'status': 'healthy',
            'issues': [],
            'statistics': {}
        }
        
        # Check if documentation files exist
        doc_paths = [
            self.project_root / 'Documentation' / '03-api' / 'openapi-spec.yaml',
            self.project_root / 'Documentation' / '05-features' / 'dashboard' / 'components' / 'README.md',
            self.project_root / 'Documentation' / '02-architecture' / 'data-models' / 'README.md'
        ]
        
        for doc_path in doc_paths:
            if not doc_path.exists():
                health['issues'].append(f"Missing: {doc_path.relative_to(self.project_root)}")
                health['status'] = 'degraded'
            else:
                # Check if documentation is stale (older than 7 days)
                mtime = datetime.fromtimestamp(doc_path.stat().st_mtime)
                age_days = (datetime.now() - mtime).days
                if age_days > 7:
                    health['issues'].append(f"Stale ({age_days} days old): {doc_path.name}")
                    if health['status'] == 'healthy':
                        health['status'] = 'warning'
        
        # Gather statistics
        health['statistics'] = {
            'total_watched_files': len(self.file_hashes),
            'pending_updates': len(self.doc_status['pending_updates']),
            'last_updates': self.doc_status['last_update']
        }
        
        return health


async def main():
    """Main execution with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Documentation monitoring and auto-updater')
    parser.add_argument('--watch', action='store_true', help='Start watching for changes')
    parser.add_argument('--auto-update', action='store_true', help='Automatically update documentation on changes')
    parser.add_argument('--notify-terminals', action='store_true', help='Notify other terminals of updates')
    parser.add_argument('--status', action='store_true', help='Show documentation status')
    parser.add_argument('--health', action='store_true', help='Check documentation health')
    parser.add_argument('--force-regenerate', action='store_true', help='Force regenerate all documentation')
    
    args = parser.parse_args()
    
    monitor = DocumentationMonitor()
    
    if args.status:
        status = monitor.get_documentation_status()
        print("\n📊 Documentation Status:")
        print(json.dumps(status, indent=2))
        
    elif args.health:
        health = await monitor.check_documentation_health()
        print("\n🏥 Documentation Health:")
        print(f"Status: {health['status']}")
        if health['issues']:
            print("\nIssues:")
            for issue in health['issues']:
                print(f"  - {issue}")
        print("\nStatistics:")
        print(json.dumps(health['statistics'], indent=2))
        
    elif args.force_regenerate:
        await monitor.force_regenerate_all()
        
    elif args.watch:
        await monitor.monitor_files(
            auto_update=args.auto_update,
            notify_terminals=args.notify_terminals
        )
    else:
        print("Use --help to see available options")


if __name__ == "__main__":
    asyncio.run(main())