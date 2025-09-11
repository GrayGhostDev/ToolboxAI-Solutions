#!/usr/bin/env python3
"""
Cross-Terminal Documentation Synchronization Coordinator
Manages documentation synchronization across all terminal agents
"""

import asyncio
import json
import redis.asyncio as aioredis
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import subprocess

class TerminalType(Enum):
    TERMINAL1 = "terminal1"  # Backend/API
    TERMINAL2 = "terminal2"  # Frontend/UI
    TERMINAL3 = "terminal3"  # Roblox/Lua
    DEBUGGER = "debugger"    # Monitoring/Testing
    DOCUMENTATION = "documentation"  # Documentation generation
    CLEANUP = "cleanup"      # Maintenance
    GITHUB = "github"        # CI/CD
    CLOUD = "cloud"          # Deployment

class DocumentationSyncCoordinator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.redis_client = None
        self.pubsub = None
        
        # Terminal-specific channels
        self.channels = {
            # Inbound channels (listening)
            'terminal:documentation:requests': 'Documentation generation requests',
            'terminal:documentation:updates': 'Documentation update notifications',
            'terminal:documentation:sync': 'Sync requests from other terminals',
            
            # Outbound channels (publishing)
            'terminal:all:documentation': 'Documentation status broadcasts',
            'terminal:debugger:docs': 'Documentation health metrics',
            'terminal:terminal1:api_docs': 'API documentation updates',
            'terminal:terminal2:ui_docs': 'UI component documentation',
            'terminal:terminal3:lua_docs': 'Lua script documentation'
        }
        
        # Documentation generators mapping
        self.doc_generators = {
            'api': 'generate_api_docs.py',
            'components': 'scan_components.py',
            'database': 'document_schemas.py',
            'coverage': None,  # Special handling for test coverage
            'lua': None  # Will be implemented
        }
        
        # Sync status tracking
        self.sync_status = {
            'active_syncs': {},
            'pending_requests': [],
            'last_sync': {},
            'sync_history': []
        }
    
    async def initialize(self):
        """Initialize Redis connection and subscriptions"""
        try:
            self.redis_client = await aioredis.create_redis_pool(
                'redis://localhost:6379',
                encoding='utf-8'
            )
            
            # Create pubsub instance
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to documentation channels
            for channel in self.channels.keys():
                if channel.startswith('terminal:documentation:'):
                    await self.pubsub.subscribe(channel)
            
            print("✅ Documentation sync coordinator initialized")
            print(f"📡 Listening on {len(self.channels)} channels")
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            raise
    
    async def start(self):
        """Start the synchronization coordinator"""
        await self.initialize()
        
        print("\n🚀 Documentation Sync Coordinator Started")
        print("=" * 60)
        
        # Start message handler
        asyncio.create_task(self.handle_messages())
        
        # Start periodic health check
        asyncio.create_task(self.periodic_health_check())
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping documentation sync coordinator...")
            await self.cleanup()
    
    async def handle_messages(self):
        """Handle incoming messages from terminals"""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                await self.process_message(message['channel'], message['data'])
    
    async def process_message(self, channel: str, data: str):
        """Process incoming terminal message"""
        try:
            message = json.loads(data)
            msg_type = message.get('type')
            terminal = message.get('terminal')
            
            print(f"\n📨 Received from {terminal}: {msg_type}")
            
            if msg_type == 'api_change':
                await self.handle_api_change(message)
            elif msg_type == 'ui_component_added':
                await self.handle_ui_component_change(message)
            elif msg_type == 'roblox_script_updated':
                await self.handle_roblox_update(message)
            elif msg_type == 'security_vulnerability':
                await self.handle_security_issue(message)
            elif msg_type == 'test_coverage_update':
                await self.handle_test_coverage(message)
            elif msg_type == 'sync_request':
                await self.handle_sync_request(message)
            elif msg_type == 'health_check':
                await self.handle_health_check(message)
            
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON received: {data}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def handle_api_change(self, message: Dict):
        """Handle API change notification from Terminal 1"""
        endpoint = message.get('endpoint')
        change_type = message.get('change_type', 'modified')
        
        print(f"🔄 API change detected: {change_type} {endpoint}")
        
        # Regenerate API documentation
        await self.regenerate_documentation('api')
        
        # Notify Terminal 2 about API changes
        await self.notify_terminal(
            TerminalType.TERMINAL2,
            'api_update',
            {
                'endpoint': endpoint,
                'change_type': change_type,
                'documentation_updated': True
            }
        )
        
        # Update sync status
        self.sync_status['last_sync']['api'] = datetime.now().isoformat()
    
    async def handle_ui_component_change(self, message: Dict):
        """Handle UI component change from Terminal 2"""
        component = message.get('component')
        action = message.get('action', 'modified')
        
        print(f"🎨 UI component {action}: {component}")
        
        # Regenerate component documentation
        await self.regenerate_documentation('components')
        
        # Notify Terminal 1 if API integration needed
        if message.get('requires_api'):
            await self.notify_terminal(
                TerminalType.TERMINAL1,
                'component_needs_api',
                {
                    'component': component,
                    'requirements': message.get('api_requirements', {})
                }
            )
        
        self.sync_status['last_sync']['components'] = datetime.now().isoformat()
    
    async def handle_roblox_update(self, message: Dict):
        """Handle Roblox script update from Terminal 3"""
        script = message.get('script')
        script_type = message.get('script_type')
        
        print(f"🎮 Roblox script updated: {script}")
        
        # Generate Lua documentation (if generator available)
        if self.doc_generators.get('lua'):
            await self.regenerate_documentation('lua')
        
        # Notify relevant terminals
        await self.broadcast_update('roblox_update', {
            'script': script,
            'type': script_type,
            'documentation_status': 'pending'
        })
        
        self.sync_status['last_sync']['roblox'] = datetime.now().isoformat()
    
    async def handle_security_issue(self, message: Dict):
        """Handle security vulnerability from Debugger"""
        vulnerability = message.get('vulnerability')
        severity = message.get('severity')
        affected_components = message.get('affected_components', [])
        
        print(f"🔒 Security issue ({severity}): {vulnerability}")
        
        # Create security advisory documentation
        await self.create_security_advisory(vulnerability, severity, affected_components)
        
        # Notify all terminals
        await self.broadcast_urgent('security_advisory', {
            'vulnerability': vulnerability,
            'severity': severity,
            'affected': affected_components,
            'advisory_created': True
        })
    
    async def handle_test_coverage(self, message: Dict):
        """Handle test coverage update"""
        coverage_data = message.get('coverage')
        test_type = message.get('test_type')
        
        print(f"📊 Test coverage update: {test_type}")
        
        # Generate coverage documentation
        await self.generate_coverage_docs(coverage_data)
        
        # Notify terminals
        await self.broadcast_update('coverage_update', {
            'test_type': test_type,
            'coverage': coverage_data
        })
    
    async def handle_sync_request(self, message: Dict):
        """Handle explicit sync request from a terminal"""
        requesting_terminal = message.get('terminal')
        sync_type = message.get('sync_type', 'full')
        
        print(f"🔄 Sync request from {requesting_terminal}: {sync_type}")
        
        if sync_type == 'full':
            await self.perform_full_sync()
        else:
            await self.regenerate_documentation(sync_type)
    
    async def handle_health_check(self, message: Dict):
        """Handle health check request"""
        terminal = message.get('terminal')
        
        health_status = await self.check_documentation_health()
        
        # Send health status back
        await self.notify_terminal(
            terminal,
            'health_response',
            health_status
        )
    
    async def regenerate_documentation(self, doc_type: str):
        """Regenerate specific documentation type"""
        generator = self.doc_generators.get(doc_type)
        
        if not generator:
            print(f"⚠️  No generator available for {doc_type}")
            return False
        
        script_path = self.project_root / 'scripts' / 'terminal_sync' / generator
        
        print(f"🔄 Regenerating {doc_type} documentation...")
        
        try:
            result = await asyncio.create_subprocess_exec(
                'python', str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                print(f"✅ {doc_type} documentation regenerated")
                return True
            else:
                print(f"❌ Failed to regenerate {doc_type}: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error regenerating {doc_type}: {e}")
            return False
    
    async def perform_full_sync(self):
        """Perform full documentation synchronization"""
        print("\n🔄 Performing full documentation sync...")
        
        # Track sync status
        sync_id = datetime.now().isoformat()
        self.sync_status['active_syncs'][sync_id] = {
            'start': datetime.now().isoformat(),
            'status': 'in_progress',
            'components': []
        }
        
        # Regenerate all documentation types
        for doc_type in self.doc_generators.keys():
            if self.doc_generators[doc_type]:
                success = await self.regenerate_documentation(doc_type)
                self.sync_status['active_syncs'][sync_id]['components'].append({
                    'type': doc_type,
                    'success': success
                })
        
        # Update sync status
        self.sync_status['active_syncs'][sync_id]['status'] = 'completed'
        self.sync_status['active_syncs'][sync_id]['end'] = datetime.now().isoformat()
        
        # Notify all terminals
        await self.broadcast_update('sync_completed', {
            'sync_id': sync_id,
            'components': self.sync_status['active_syncs'][sync_id]['components']
        })
        
        print("✅ Full documentation sync completed")
    
    async def create_security_advisory(self, vulnerability: str, severity: str, affected: List[str]):
        """Create security advisory documentation"""
        advisory_dir = self.project_root / 'Documentation' / '10-security' / 'advisories'
        advisory_dir.mkdir(parents=True, exist_ok=True)
        
        advisory_id = f"TBAI-{datetime.now().strftime('%Y%m%d')}-{hash(vulnerability) % 1000:03d}"
        advisory_file = advisory_dir / f"{advisory_id}.md"
        
        content = f"""# Security Advisory: {advisory_id}

## Vulnerability: {vulnerability}

**Severity**: {severity}
**Date**: {datetime.now().isoformat()}

## Affected Components
{chr(10).join(f'- {comp}' for comp in affected)}

## Description
{vulnerability}

## Remediation
Under investigation. Updates will be provided as available.

## Timeline
- **Discovered**: {datetime.now().isoformat()}
- **Reported**: {datetime.now().isoformat()}
- **Fixed**: Pending

---
*This advisory was automatically generated by the Documentation Sync Coordinator*
"""
        
        with open(advisory_file, 'w') as f:
            f.write(content)
        
        print(f"📝 Security advisory created: {advisory_id}")
    
    async def generate_coverage_docs(self, coverage_data: Dict):
        """Generate test coverage documentation"""
        coverage_dir = self.project_root / 'Documentation' / '04-implementation' / 'coverage'
        coverage_dir.mkdir(parents=True, exist_ok=True)
        
        summary_file = coverage_dir / 'coverage_summary.md'
        
        with open(summary_file, 'w') as f:
            f.write(f"# Test Coverage Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"## Summary\n")
            f.write(f"- Total Coverage: {coverage_data.get('total', 0)}%\n")
            f.write(f"- Lines Covered: {coverage_data.get('covered', 0)}\n")
            f.write(f"- Lines Total: {coverage_data.get('total_lines', 0)}\n")
        
        print("📊 Coverage documentation updated")
    
    async def notify_terminal(self, terminal: TerminalType, msg_type: str, data: Dict):
        """Send notification to specific terminal"""
        channel = f'terminal:{terminal.value}:{msg_type}'
        message = {
            'timestamp': datetime.now().isoformat(),
            'from': 'documentation',
            'type': msg_type,
            'data': data
        }
        
        await self.redis_client.publish(channel, json.dumps(message))
        print(f"📤 Notified {terminal.value}: {msg_type}")
    
    async def broadcast_update(self, msg_type: str, data: Dict):
        """Broadcast update to all terminals"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'from': 'documentation',
            'type': msg_type,
            'data': data
        }
        
        await self.redis_client.publish('terminal:all:documentation', json.dumps(message))
        print(f"📢 Broadcast: {msg_type}")
    
    async def broadcast_urgent(self, msg_type: str, data: Dict):
        """Broadcast urgent message to all terminals"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'from': 'documentation',
            'type': msg_type,
            'priority': 'urgent',
            'data': data
        }
        
        # Publish to multiple channels for redundancy
        channels = [
            'terminal:all:documentation',
            'terminal:all:urgent',
            'terminal:debugger:alerts'
        ]
        
        for channel in channels:
            await self.redis_client.publish(channel, json.dumps(message))
        
        print(f"🚨 Urgent broadcast: {msg_type}")
    
    async def check_documentation_health(self) -> Dict:
        """Check health of documentation system"""
        health = {
            'status': 'healthy',
            'issues': [],
            'sync_status': self.sync_status,
            'last_checks': {}
        }
        
        # Check if documentation files exist
        checks = {
            'api': self.project_root / 'Documentation' / '03-api' / 'openapi-spec.yaml',
            'components': self.project_root / 'Documentation' / '05-features' / 'dashboard' / 'components' / 'README.md',
            'database': self.project_root / 'Documentation' / '02-architecture' / 'data-models' / 'README.md'
        }
        
        for doc_type, path in checks.items():
            if path.exists():
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                age_hours = (datetime.now() - mtime).total_seconds() / 3600
                health['last_checks'][doc_type] = {
                    'exists': True,
                    'last_modified': mtime.isoformat(),
                    'age_hours': round(age_hours, 2)
                }
                
                if age_hours > 168:  # Older than 1 week
                    health['issues'].append(f"{doc_type} documentation is stale")
                    health['status'] = 'warning'
            else:
                health['last_checks'][doc_type] = {'exists': False}
                health['issues'].append(f"{doc_type} documentation missing")
                health['status'] = 'degraded'
        
        return health
    
    async def periodic_health_check(self):
        """Perform periodic health checks"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            health = await self.check_documentation_health()
            
            # Send health metrics to debugger
            await self.notify_terminal(
                TerminalType.DEBUGGER,
                'docs_health',
                health
            )
            
            # Log issues
            if health['issues']:
                print(f"⚠️  Documentation health issues: {', '.join(health['issues'])}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis_client:
            self.redis_client.close()
            await self.redis_client.wait_closed()
        print("✅ Cleanup completed")


async def main():
    """Main execution"""
    coordinator = DocumentationSyncCoordinator()
    await coordinator.start()


if __name__ == "__main__":
    print("🚀 Starting Documentation Sync Coordinator...")
    print("=" * 60)
    print("This coordinator manages documentation synchronization")
    print("across all terminal agents in the ToolBoxAI platform")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Documentation sync coordinator stopped")