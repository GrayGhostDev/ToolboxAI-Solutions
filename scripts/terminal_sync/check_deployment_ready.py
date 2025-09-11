#!/usr/bin/env python3
"""
Check if all terminals are ready for deployment.
Implements real coordination between services.
"""

import sys
import json
import time
import redis
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Tuple

class DeploymentReadinessChecker:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test Redis connection
            self.redis_client.ping()
            self.redis_available = True
        except (redis.ConnectionError, redis.TimeoutError):
            print("⚠️  Redis not available, using HTTP health checks only")
            self.redis_available = False
            self.redis_client = None
        
        self.services = {
            'fastapi': {
                'url': 'http://127.0.0.1:8008/health',
                'name': 'FastAPI Server',
                'required': True
            },
            'flask': {
                'url': 'http://127.0.0.1:5001/health',
                'name': 'Flask Bridge',
                'required': True
            },
            'dashboard': {
                'url': 'http://127.0.0.1:3000',
                'name': 'Dashboard Frontend',
                'required': False
            },
            'mcp': {
                'url': 'ws://127.0.0.1:9876',
                'name': 'MCP WebSocket',
                'required': False
            },
            'ghost': {
                'url': 'http://127.0.0.1:8000/health',
                'name': 'Ghost Backend',
                'required': False
            }
        }
        
        self.terminal_checks = {
            'terminal1': {'status': 'unknown', 'last_check': None},
            'terminal2': {'status': 'unknown', 'last_check': None},
            'terminal3': {'status': 'unknown', 'last_check': None},
            'debugger': {'status': 'unknown', 'last_check': None}
        }

    async def check_service(self, service_id: str, service_info: Dict) -> Tuple[str, bool, str]:
        """Check if a service is healthy."""
        try:
            if service_info['url'].startswith('ws://'):
                # WebSocket health check
                import websockets
                async with websockets.connect(service_info['url'], timeout=5) as ws:
                    return service_id, True, "Connected"
            else:
                # HTTP health check
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(service_info['url']) as response:
                        if response.status == 200:
                            return service_id, True, "Healthy"
                        else:
                            return service_id, False, f"HTTP {response.status}"
        except Exception as e:
            return service_id, False, str(e)

    async def check_all_services(self) -> Dict:
        """Check all services concurrently."""
        tasks = []
        for service_id, service_info in self.services.items():
            tasks.append(self.check_service(service_id, service_info))
        
        results = await asyncio.gather(*tasks)
        
        service_status = {}
        for service_id, healthy, message in results:
            service_status[service_id] = {
                'name': self.services[service_id]['name'],
                'healthy': healthy,
                'required': self.services[service_id]['required'],
                'message': message
            }
        
        return service_status

    def check_terminal_status(self) -> Dict:
        """Check terminal status via Redis."""
        if not self.redis_available:
            return self.terminal_checks
        
        for terminal in self.terminal_checks.keys():
            try:
                # Check if terminal has published recent status
                status_key = f"terminal:{terminal}:status"
                status = self.redis_client.get(status_key)
                
                if status:
                    status_data = json.loads(status)
                    self.terminal_checks[terminal] = {
                        'status': status_data.get('status', 'unknown'),
                        'last_check': status_data.get('timestamp', datetime.now().isoformat())
                    }
                else:
                    # Request status update
                    self.redis_client.publish(
                        f"terminal:{terminal}:status_request",
                        json.dumps({'timestamp': datetime.now().isoformat()})
                    )
            except Exception as e:
                print(f"Error checking {terminal}: {e}")
        
        return self.terminal_checks

    def check_database(self) -> bool:
        """Check database connectivity."""
        try:
            import psycopg2
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # Try to connect to database
            conn = psycopg2.connect(
                os.getenv('DATABASE_URL', 'postgresql://localhost/toolboxai')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Database check failed: {e}")
            return False

    async def run_readiness_check(self) -> bool:
        """Run comprehensive readiness check."""
        print("=" * 60)
        print("🚀 DEPLOYMENT READINESS CHECK")
        print("=" * 60)
        
        all_ready = True
        
        # Check services
        print("\n📡 Service Health Checks:")
        print("-" * 40)
        service_status = await self.check_all_services()
        
        for service_id, status in service_status.items():
            icon = "✅" if status['healthy'] else ("❌" if status['required'] else "⚠️ ")
            print(f"{icon} {status['name']}: {'Healthy' if status['healthy'] else status['message']}")
            
            if not status['healthy'] and status['required']:
                all_ready = False
        
        # Check database
        print("\n💾 Database Check:")
        print("-" * 40)
        db_ready = self.check_database()
        print(f"{'✅' if db_ready else '❌'} PostgreSQL: {'Connected' if db_ready else 'Not available'}")
        
        if not db_ready:
            all_ready = False
        
        # Check terminals (if Redis available)
        if self.redis_available:
            print("\n🖥️  Terminal Status:")
            print("-" * 40)
            terminal_status = self.check_terminal_status()
            
            for terminal, status in terminal_status.items():
                icon = "✅" if status['status'] == 'ready' else "⚠️ "
                print(f"{icon} {terminal}: {status['status']}")
        
        # Check Git status
        print("\n📦 Git Status:")
        print("-" * 40)
        import subprocess
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print("⚠️  Uncommitted changes detected")
                print("   Consider committing changes before deployment")
            else:
                print("✅ Working directory clean")
            
            # Check current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True
            )
            current_branch = branch_result.stdout.strip()
            print(f"📌 Current branch: {current_branch}")
            
        except Exception as e:
            print(f"⚠️  Git check failed: {e}")
        
        # Final verdict
        print("\n" + "=" * 60)
        if all_ready:
            print("✅ ALL SYSTEMS READY FOR DEPLOYMENT")
            
            # Notify via Redis if available
            if self.redis_available:
                self.redis_client.publish(
                    'terminal:all:deployment_ready',
                    json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'status': 'ready',
                        'services': service_status
                    })
                )
        else:
            print("❌ DEPLOYMENT BLOCKED - Required services not ready")
            print("\nTo fix:")
            print("1. Start required services with: scripts/start_mcp_servers.sh")
            print("2. Check service logs in: logs/")
            print("3. Verify database connection")
        
        print("=" * 60)
        
        return all_ready


async def main():
    """Main entry point."""
    checker = DeploymentReadinessChecker()
    ready = await checker.run_readiness_check()
    
    # Exit with appropriate code
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    asyncio.run(main())