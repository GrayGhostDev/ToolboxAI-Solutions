#!/usr/bin/env python3
"""
Debugger Alert Orchestrator - Intelligent alert management system
Part of the ToolBoxAI Educational Platform monitoring system
"""

import asyncio
import json
import redis.asyncio as aioredis
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path
import subprocess
import sys
import httpx

class AlertOrchestrator:
    def __init__(self):
        self.alert_rules = {
            "security": {
                "critical": self.handle_critical_security,
                "high": self.handle_high_security,
                "medium": self.handle_medium_security
            },
            "performance": {
                "critical": self.handle_critical_performance,
                "high": self.handle_high_performance
            },
            "availability": {
                "service_down": self.handle_service_down,
                "degraded": self.handle_degraded_service
            }
        }
        self.alert_history = []
        self.suppression_window = 300  # 5 minutes
        self.redis_client = None
        self.incident_count = 0
    
    async def initialize(self):
        """Initialize Redis connection and start listening"""
        try:
            self.redis_client = await aioredis.from_url(
                'redis://localhost:6379',
                decode_responses=True
            )
            print("✅ Connected to Redis")
            
            # Subscribe to alert channels
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(
                'terminal:alerts',
                'terminal:security:alerts',
                'terminal:performance:alerts'
            )
            
            print("📡 Listening for alerts...")
            
            # Process incoming alerts
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        alert_data = json.loads(message['data'])
                        await self.process_alert(alert_data)
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("Running in standalone mode...")
            
            # Run periodic checks without Redis
            await self.run_standalone_checks()
    
    async def run_standalone_checks(self):
        """Run checks when Redis is not available"""
        while True:
            # Check service health
            await self.check_all_services()
            
            # Check for alert files
            await self.check_alert_files()
            
            await asyncio.sleep(30)
    
    async def check_all_services(self):
        """Check health of all services"""
        services = [
            ("terminal1", "http://localhost:8008/health", "Backend"),
            ("terminal2", "http://localhost:5179", "Frontend"),
            ("terminal3", "http://localhost:5001/health", "Roblox Bridge")
        ]
        
        for service_id, url, name in services:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=5.0)
                    if response.status_code != 200:
                        await self.process_alert({
                            "category": "availability",
                            "severity": "service_down",
                            "service": service_id,
                            "service_name": name,
                            "message": f"{name} is not responding properly"
                        })
            except Exception as e:
                await self.process_alert({
                    "category": "availability",
                    "severity": "service_down",
                    "service": service_id,
                    "service_name": name,
                    "message": f"{name} is down: {str(e)}"
                })
    
    async def check_alert_files(self):
        """Check for alert files from other scripts"""
        alert_dir = Path("scripts/terminal_sync/alerts")
        if alert_dir.exists():
            for alert_file in alert_dir.glob("*.json"):
                try:
                    with open(alert_file, "r") as f:
                        alert_data = json.load(f)
                        await self.process_alert(alert_data)
                    # Remove processed alert file
                    alert_file.unlink()
                except Exception as e:
                    print(f"Error processing alert file {alert_file}: {e}")
    
    async def process_alert(self, alert: Dict):
        """Process incoming alert"""
        # Add timestamp if not present
        if "timestamp" not in alert:
            alert["timestamp"] = datetime.now().isoformat()
        
        # Check if alert should be suppressed
        if self.should_suppress(alert):
            return
        
        # Determine handler
        category = alert.get("category", "general")
        severity = alert.get("severity", "low").lower()
        
        handler = self.alert_rules.get(category, {}).get(severity)
        if handler:
            await handler(alert)
        else:
            await self.handle_generic_alert(alert)
        
        # Record alert
        self.alert_history.append({
            **alert,
            "processed_at": datetime.now().isoformat()
        })
        
        # Save alert history
        await self.save_alert_history()
    
    def should_suppress(self, alert: Dict) -> bool:
        """Check if alert should be suppressed"""
        # Check for duplicate alerts within suppression window
        cutoff = datetime.now() - timedelta(seconds=self.suppression_window)
        
        for past_alert in self.alert_history:
            if (past_alert.get("type") == alert.get("type") and
                past_alert.get("source") == alert.get("source") and
                datetime.fromisoformat(past_alert["processed_at"]) > cutoff):
                return True
        
        return False
    
    async def handle_critical_security(self, alert: Dict):
        """Handle critical security alerts"""
        print(f"🚨🚨🚨 CRITICAL SECURITY ALERT: {alert.get('message', 'Security breach detected')}")
        
        # Immediate actions
        actions = []
        
        if "hardcoded_credentials" in alert.get("type", ""):
            actions.append("Rotating all credentials")
            await self.rotate_credentials()
        
        if "auth_bypass" in alert.get("type", ""):
            actions.append("Enabling emergency auth lockdown")
            await self.enable_auth_lockdown()
        
        # Notify all terminals
        await self.broadcast_emergency({
            "alert": alert,
            "actions_taken": actions,
            "requires_immediate_attention": True
        })
        
        # Create incident
        await self.create_incident(alert, "CRITICAL")
    
    async def handle_high_security(self, alert: Dict):
        """Handle high security alerts"""
        print(f"⚠️ HIGH SECURITY ALERT: {alert.get('message', 'Security issue detected')}")
        
        # Create incident
        await self.create_incident(alert, "HIGH")
        
        # Notify relevant terminals
        await self.notify_terminals(alert, ["terminal1"])
    
    async def handle_medium_security(self, alert: Dict):
        """Handle medium security alerts"""
        print(f"ℹ️ MEDIUM SECURITY ALERT: {alert.get('message', 'Minor security issue')}")
        
        # Log for review
        await self.log_alert(alert)
    
    async def handle_critical_performance(self, alert: Dict):
        """Handle critical performance alerts"""
        print(f"🚨 CRITICAL PERFORMANCE: {alert.get('message', 'Performance crisis')}")
        
        # Attempt auto-recovery
        if "memory" in alert.get("type", "").lower():
            await self.free_memory()
        
        if "cpu" in alert.get("type", "").lower():
            await self.reduce_cpu_load()
        
        # Create incident
        await self.create_incident(alert, "CRITICAL")
    
    async def handle_high_performance(self, alert: Dict):
        """Handle high performance alerts"""
        print(f"⚠️ HIGH PERFORMANCE: {alert.get('message', 'Performance degraded')}")
        
        # Monitor for escalation
        await self.monitor_for_escalation(alert)
    
    async def handle_service_down(self, alert: Dict):
        """Handle service down alerts"""
        service = alert.get("service", "unknown")
        service_name = alert.get("service_name", service)
        print(f"🔴 SERVICE DOWN: {service_name}")
        
        # Attempt auto-recovery
        recovery_success = False
        
        if service == "terminal1":
            recovery_success = await self.restart_terminal1()
        elif service == "terminal2":
            recovery_success = await self.restart_terminal2()
        elif service == "terminal3":
            recovery_success = await self.restart_terminal3()
        
        if recovery_success:
            print(f"✅ {service_name} restarted successfully")
        else:
            # Escalate
            await self.escalate_incident(alert)
    
    async def handle_degraded_service(self, alert: Dict):
        """Handle degraded service alerts"""
        print(f"🟡 SERVICE DEGRADED: {alert.get('message', 'Service performance degraded')}")
        
        # Monitor for further degradation
        await self.monitor_for_escalation(alert)
    
    async def handle_generic_alert(self, alert: Dict):
        """Handle generic alerts"""
        severity = alert.get("severity", "INFO")
        message = alert.get("message", "Alert received")
        print(f"📢 [{severity}] {message}")
        
        # Log alert
        await self.log_alert(alert)
    
    async def restart_terminal1(self) -> bool:
        """Restart Terminal 1 services"""
        try:
            # Check if script exists
            script_path = Path("scripts/terminal1_start.sh")
            if script_path.exists():
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.returncode == 0
            else:
                print("  Terminal 1 restart script not found")
                return False
        except Exception as e:
            print(f"  Failed to restart Terminal 1: {e}")
            return False
    
    async def restart_terminal2(self) -> bool:
        """Restart Terminal 2 services"""
        try:
            # For frontend, we might need to restart the dev server
            print("  Terminal 2 (Frontend) requires manual restart")
            return False
        except Exception as e:
            print(f"  Failed to restart Terminal 2: {e}")
            return False
    
    async def restart_terminal3(self) -> bool:
        """Restart Terminal 3 services"""
        try:
            # Restart Flask bridge
            print("  Attempting to restart Flask bridge...")
            # This would normally restart the Flask server
            return False
        except Exception as e:
            print(f"  Failed to restart Terminal 3: {e}")
            return False
    
    async def rotate_credentials(self):
        """Rotate all credentials (placeholder)"""
        print("  🔐 Initiating credential rotation...")
        # This would trigger credential rotation process
    
    async def enable_auth_lockdown(self):
        """Enable emergency auth lockdown (placeholder)"""
        print("  🔒 Enabling auth lockdown...")
        # This would enable strict authentication
    
    async def free_memory(self):
        """Attempt to free memory"""
        import gc
        gc.collect()
        print("  💾 Freed memory via garbage collection")
    
    async def reduce_cpu_load(self):
        """Attempt to reduce CPU load"""
        print("  ⚡ Attempting to reduce CPU load...")
        # This would implement CPU reduction strategies
    
    async def broadcast_emergency(self, data: Dict):
        """Broadcast emergency to all terminals"""
        if self.redis_client:
            channels = [
                "terminal:emergency",
                "terminal:1:alerts",
                "terminal:2:alerts",
                "terminal:3:alerts"
            ]
            
            for channel in channels:
                try:
                    await self.redis_client.publish(channel, json.dumps(data))
                except:
                    pass
        
        # Also save to file
        emergency_file = Path("scripts/terminal_sync/alerts/emergency.json")
        emergency_file.parent.mkdir(parents=True, exist_ok=True)
        with open(emergency_file, "w") as f:
            json.dump(data, f, indent=2)
    
    async def notify_terminals(self, alert: Dict, terminals: List[str]):
        """Notify specific terminals"""
        if self.redis_client:
            for terminal in terminals:
                try:
                    await self.redis_client.publish(
                        f"terminal:{terminal}:alerts",
                        json.dumps(alert)
                    )
                except:
                    pass
    
    async def create_incident(self, alert: Dict, severity: str):
        """Create incident record"""
        self.incident_count += 1
        incident = {
            "id": f"INC-{datetime.now().strftime('%Y%m%d')}-{self.incident_count:04d}",
            "alert": alert,
            "severity": severity,
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "assigned_to": "on-call",
            "updates": []
        }
        
        # Create incidents directory
        incidents_dir = Path("incidents")
        incidents_dir.mkdir(exist_ok=True)
        
        # Save incident
        with open(incidents_dir / f"{incident['id']}.json", "w") as f:
            json.dump(incident, f, indent=2)
        
        print(f"  📝 Incident created: {incident['id']}")
        
        return incident
    
    async def escalate_incident(self, alert: Dict):
        """Escalate incident"""
        print(f"  📈 ESCALATING: {alert.get('message', 'Issue requires escalation')}")
        
        # Create high priority incident
        incident = await self.create_incident(alert, "ESCALATED")
        
        # Notify all terminals
        await self.broadcast_emergency({
            "type": "escalation",
            "incident": incident,
            "alert": alert
        })
    
    async def monitor_for_escalation(self, alert: Dict):
        """Monitor alert for potential escalation"""
        # Add to monitoring queue
        print(f"  👁️ Monitoring for escalation: {alert.get('type', 'unknown')}")
    
    async def log_alert(self, alert: Dict):
        """Log alert to file"""
        log_file = Path("scripts/terminal_sync/alerts/alert_log.jsonl")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(alert) + "\n")
    
    async def save_alert_history(self):
        """Save alert history to file"""
        history_file = Path("scripts/terminal_sync/alerts/history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Keep only last 100 alerts
        recent_alerts = self.alert_history[-100:]
        
        with open(history_file, "w") as f:
            json.dump(recent_alerts, f, indent=2)
    
    def get_alert_summary(self) -> Dict:
        """Get summary of recent alerts"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a["processed_at"]) > last_hour
        ]
        
        daily_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a["processed_at"]) > last_day
        ]
        
        return {
            "last_hour": len(recent_alerts),
            "last_24h": len(daily_alerts),
            "total": len(self.alert_history),
            "incidents": self.incident_count
        }

# Run the alert orchestrator
if __name__ == "__main__":
    print("🔔 Starting Alert Orchestrator...")
    print("=" * 50)
    orchestrator = AlertOrchestrator()
    
    try:
        asyncio.run(orchestrator.initialize())
    except KeyboardInterrupt:
        print("\n✅ Alert Orchestrator stopped")
        
        # Show summary
        summary = orchestrator.get_alert_summary()
        print("\n📊 Alert Summary:")
        print(f"  Last hour: {summary['last_hour']} alerts")
        print(f"  Last 24h: {summary['last_24h']} alerts")
        print(f"  Total processed: {summary['total']} alerts")
        print(f"  Incidents created: {summary['incidents']}")