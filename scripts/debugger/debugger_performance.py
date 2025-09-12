#!/usr/bin/env python3
"""
Debugger Performance Aggregator - Multi-terminal performance monitoring
Part of the ToolBoxAI Educational Platform monitoring system
"""

import psutil
import asyncio
import httpx
import statistics
from datetime import datetime, timedelta
from typing import Dict, List
import json
import redis
from pathlib import Path
import sys
import os

class PerformanceAggregator:
    def __init__(self):
        self.metrics = {
            "terminal1": [],
            "terminal2": [],
            "terminal3": [],
            "system": []
        }
        self.alerts = []
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "response_time_ms": 500,
            "error_rate": 0.05,
            "websocket_latency_ms": 100
        }
        self.redis_client = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("Continuing without Redis...")
    
    async def collect_all_metrics(self):
        """Collect metrics from all terminals"""
        await self.initialize()
        
        while True:
            timestamp = datetime.now()
            
            # Collect Terminal 1 metrics
            terminal1_metrics = await self.collect_terminal1_metrics()
            self.metrics["terminal1"].append({
                "timestamp": timestamp,
                **terminal1_metrics
            })
            
            # Collect Terminal 2 metrics
            terminal2_metrics = await self.collect_terminal2_metrics()
            self.metrics["terminal2"].append({
                "timestamp": timestamp,
                **terminal2_metrics
            })
            
            # Collect Terminal 3 metrics
            terminal3_metrics = await self.collect_terminal3_metrics()
            self.metrics["terminal3"].append({
                "timestamp": timestamp,
                **terminal3_metrics
            })
            
            # Collect system metrics
            system_metrics = self.collect_system_metrics()
            self.metrics["system"].append({
                "timestamp": timestamp,
                **system_metrics
            })
            
            # Analyze and alert
            await self.analyze_metrics()
            
            # Save current metrics
            await self.save_metrics()
            
            # Clean old metrics (keep last hour)
            self.clean_old_metrics()
            
            # Display current status
            self.display_status()
            
            await asyncio.sleep(10)
    
    async def collect_terminal1_metrics(self) -> Dict:
        """Collect backend performance metrics"""
        metrics = {
            "api_response_time": 0,
            "database_query_time": 0,
            "active_connections": 0,
            "request_rate": 0,
            "error_rate": 0,
            "websocket_connections": 0,
            "status": "down"
        }
        
        try:
            # Test API response time
            start = datetime.now()
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8008/health", timeout=5.0)
                metrics["api_response_time"] = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    metrics["status"] = "healthy"
                    data = response.json()
                    metrics["websocket_connections"] = data.get("websocket_connections", 0)
            
            # Get database metrics (if endpoint exists)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8008/metrics/database", timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        metrics["database_query_time"] = data.get("avg_query_time", 0)
                        metrics["active_connections"] = data.get("active_connections", 0)
            except:
                pass
                
        except Exception as e:
            metrics["status"] = "down"
            metrics["error"] = str(e)
        
        return metrics
    
    async def collect_terminal2_metrics(self) -> Dict:
        """Collect frontend performance metrics"""
        metrics = {
            "page_load_time": 0,
            "first_contentful_paint": 0,
            "websocket_latency": 0,
            "javascript_errors": 0,
            "component_render_time": 0,
            "status": "down"
        }
        
        try:
            # Check if frontend is running
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:5179", timeout=5.0)
                if response.status_code == 200:
                    metrics["status"] = "healthy"
                    
            # Get performance metrics from dashboard (if endpoint exists)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:5179/api/metrics", timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        metrics.update(data)
            except:
                # Dashboard might not have metrics endpoint yet
                pass
                
        except Exception as e:
            metrics["status"] = "down"
            metrics["error"] = str(e)
        
        return metrics
    
    async def collect_terminal3_metrics(self) -> Dict:
        """Collect Roblox performance metrics"""
        metrics = {
            "fps": 60,  # Default to 60 FPS
            "memory_usage_mb": 0,
            "player_count": 0,
            "content_load_time": 0,
            "script_errors": 0,
            "status": "down"
        }
        
        try:
            # Check Flask Bridge health
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:5001/health", timeout=5.0)
                if response.status_code == 200:
                    metrics["status"] = "healthy"
                    data = response.json()
                    metrics["uptime"] = data.get("uptime", 0)
            
            # Get metrics from Flask Bridge (if endpoint exists)
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:5001/metrics/roblox", timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        metrics.update(data)
            except:
                # Flask Bridge might not have metrics endpoint yet
                pass
                
        except Exception as e:
            metrics["status"] = "down"
            metrics["error"] = str(e)
        
        return metrics
    
    def collect_system_metrics(self) -> Dict:
        """Collect system-wide metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_bytes_sent": psutil.net_io_counters().bytes_sent,
                "network_bytes_recv": psutil.net_io_counters().bytes_recv,
                "process_count": len(psutil.pids()),
                "status": "healthy"
            }
        except Exception as e:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_usage": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_metrics(self):
        """Analyze metrics and generate alerts"""
        # Check system resources
        latest_system = self.metrics["system"][-1] if self.metrics["system"] else {}
        
        if latest_system.get("cpu_percent", 0) > self.thresholds["cpu_percent"]:
            await self.alert("HIGH_CPU", f"CPU usage: {latest_system['cpu_percent']:.1f}%")
        
        if latest_system.get("memory_percent", 0) > self.thresholds["memory_percent"]:
            await self.alert("HIGH_MEMORY", f"Memory usage: {latest_system['memory_percent']:.1f}%")
        
        # Check Terminal 1 performance
        if self.metrics["terminal1"]:
            latest_t1 = self.metrics["terminal1"][-1]
            if latest_t1["api_response_time"] > self.thresholds["response_time_ms"]:
                await self.alert("SLOW_API", f"API response time: {latest_t1['api_response_time']:.0f}ms")
        
        # Check Terminal 2 performance
        if self.metrics["terminal2"]:
            latest_t2 = self.metrics["terminal2"][-1]
            if latest_t2["websocket_latency"] > self.thresholds["websocket_latency_ms"]:
                await self.alert("HIGH_LATENCY", f"WebSocket latency: {latest_t2['websocket_latency']:.0f}ms")
        
        # Check Terminal 3 performance
        if self.metrics["terminal3"]:
            latest_t3 = self.metrics["terminal3"][-1]
            if latest_t3["fps"] < 30:
                await self.alert("LOW_FPS", f"Roblox FPS: {latest_t3['fps']}")
    
    async def alert(self, alert_type: str, message: str):
        """Send alert to all terminals"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "severity": self.get_severity(alert_type)
        }
        
        self.alerts.append(alert)
        
        # Broadcast alert
        print(f"🚨 ALERT [{alert['severity']}]: {message}")
        
        # Send to all terminals via Redis
        if self.redis_client:
            try:
                self.redis_client.publish("terminal:alerts", json.dumps(alert))
            except:
                pass
        
        # Take action based on alert type
        if alert_type == "HIGH_CPU":
            await self.optimize_cpu_usage()
        elif alert_type == "HIGH_MEMORY":
            await self.optimize_memory_usage()
    
    def get_severity(self, alert_type: str) -> str:
        """Determine alert severity"""
        critical = ["HIGH_MEMORY", "SECURITY_BREACH", "SERVICE_DOWN"]
        high = ["HIGH_CPU", "SLOW_API", "HIGH_LATENCY"]
        
        if alert_type in critical:
            return "CRITICAL"
        elif alert_type in high:
            return "HIGH"
        else:
            return "MEDIUM"
    
    async def optimize_cpu_usage(self):
        """Attempt to reduce CPU usage"""
        # Find high CPU processes
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] > 50:
                    print(f"  High CPU process: {proc.info['name']} ({proc.info['cpu_percent']:.1f}%)")
            except:
                pass
    
    async def optimize_memory_usage(self):
        """Attempt to free memory"""
        # Trigger garbage collection
        import gc
        gc.collect()
        print("  Triggered garbage collection")
    
    def clean_old_metrics(self):
        """Remove metrics older than 1 hour"""
        cutoff = datetime.now() - timedelta(hours=1)
        
        for terminal in self.metrics:
            self.metrics[terminal] = [
                m for m in self.metrics[terminal]
                if m["timestamp"] > cutoff
            ]
    
    async def save_metrics(self):
        """Save current metrics to file"""
        metrics_file = Path("scripts/terminal_sync/metrics/performance.json")
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare metrics for JSON serialization
        save_data = {}
        for terminal, metrics_list in self.metrics.items():
            if metrics_list:
                latest = metrics_list[-1].copy()
                latest["timestamp"] = latest["timestamp"].isoformat()
                save_data[terminal] = latest
        
        with open(metrics_file, "w") as f:
            json.dump(save_data, f, indent=2)
    
    def display_status(self):
        """Display current performance status"""
        print("\r", end="")  # Clear line
        
        # System metrics
        if self.metrics["system"]:
            sys_metrics = self.metrics["system"][-1]
            print(f"📊 CPU: {sys_metrics['cpu_percent']:.1f}% | "
                  f"Memory: {sys_metrics['memory_percent']:.1f}% | ", end="")
        
        # Terminal status
        for terminal in ["terminal1", "terminal2", "terminal3"]:
            if self.metrics[terminal]:
                status = self.metrics[terminal][-1].get("status", "unknown")
                if status == "healthy":
                    print(f"✅ {terminal[-1]} ", end="")
                else:
                    print(f"❌ {terminal[-1]} ", end="")
        
        # Alert count
        recent_alerts = [a for a in self.alerts 
                        if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(minutes=5)]
        if recent_alerts:
            print(f"| ⚠️ {len(recent_alerts)} alerts", end="")
        
        sys.stdout.flush()
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "alerts": self.alerts[-10:],  # Last 10 alerts
            "recommendations": []
        }
        
        # Calculate averages for each terminal
        for terminal, metrics_list in self.metrics.items():
            if metrics_list:
                # Get numeric fields
                numeric_fields = [
                    k for k in metrics_list[0].keys()
                    if isinstance(metrics_list[0][k], (int, float))
                ]
                
                report["summary"][terminal] = {}
                for field in numeric_fields:
                    values = [m[field] for m in metrics_list if field in m]
                    if values:
                        report["summary"][terminal][field] = {
                            "avg": statistics.mean(values),
                            "min": min(values),
                            "max": max(values),
                            "p95": statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values)
                        }
        
        # Generate recommendations
        if report["summary"].get("system", {}).get("cpu_percent", {}).get("avg", 0) > 70:
            report["recommendations"].append("Consider scaling horizontally")
        
        if report["summary"].get("terminal1", {}).get("api_response_time", {}).get("p95", 0) > 1000:
            report["recommendations"].append("Optimize slow API endpoints")
        
        return report

# Run performance monitoring
if __name__ == "__main__":
    print("📊 Starting Performance Monitor...")
    print("=" * 50)
    aggregator = PerformanceAggregator()
    try:
        asyncio.run(aggregator.collect_all_metrics())
    except KeyboardInterrupt:
        print("\n✅ Performance Monitor stopped")
        
        # Generate final report
        report = aggregator.generate_performance_report()
        print("\n📈 Final Performance Report:")
        print(f"  Alerts: {len(report['alerts'])}")
        if report['recommendations']:
            print("  Recommendations:")
            for rec in report['recommendations']:
                print(f"    - {rec}")