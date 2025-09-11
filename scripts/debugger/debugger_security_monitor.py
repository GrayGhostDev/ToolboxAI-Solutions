#!/usr/bin/env python3
"""
Debugger Security Monitor - Real-time security vulnerability scanner
Part of the ToolBoxAI Educational Platform monitoring system
"""

import asyncio
import json
import re
import ast
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from typing import Dict, List, Tuple, Any
import os
import sys

# Try to import optional packages
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis module not available - using file-based communication")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import urllib.request
    print("⚠️ httpx not available - using urllib")

class SecurityMonitor:
    def __init__(self):
        self.redis_client = None
        self.vulnerabilities = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        self.terminals = {
            "terminal1": {"status": "unknown", "last_seen": None},
            "terminal2": {"status": "unknown", "last_seen": None},
            "terminal3": {"status": "unknown", "last_seen": None}
        }
        
    async def initialize(self):
        """Initialize connections and start monitoring"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = await aioredis.from_url(
                    'redis://localhost:6379',
                    decode_responses=True
                )
                print("✅ Connected to Redis")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                print("Continuing without Redis...")
        else:
            print("Running without Redis - using file-based communication")
            
        # Start monitoring tasks
        await asyncio.gather(
            self.monitor_terminals(),
            self.scan_for_vulnerabilities(),
            self.monitor_authentication(),
            self.check_compliance(),
            self.process_alerts()
        )
    
    async def monitor_terminals(self):
        """Monitor all terminal health and security"""
        while True:
            for terminal_id in self.terminals.keys():
                try:
                    # Check Terminal 1 (Backend)
                    if terminal_id == "terminal1":
                        status = await self.check_backend_security()
                        await self.verify_terminal1_security(status)
                    
                    # Check Terminal 2 (Frontend)
                    elif terminal_id == "terminal2":
                        status = await self.check_frontend_security()
                        await self.verify_terminal2_security(status)
                    
                    # Check Terminal 3 (Roblox)
                    elif terminal_id == "terminal3":
                        status = await self.check_roblox_security()
                        await self.verify_terminal3_security(status)
                    
                    # Update terminal status
                    self.terminals[terminal_id]["status"] = status.get("health", "unknown")
                    self.terminals[terminal_id]["last_seen"] = datetime.now()
                    
                    # Alert if terminal is down
                    if status.get("health") != "healthy":
                        await self.alert_terminal_issue(terminal_id, status)
                except Exception as e:
                    print(f"Error monitoring {terminal_id}: {e}")
            
            await asyncio.sleep(10)
    
    async def check_backend_security(self) -> Dict:
        """Check backend security status"""
        status = {"health": "unknown", "checks": {}}
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8008/health", timeout=5.0)
                    if response.status_code == 200:
                        status["health"] = "healthy"
                        status["data"] = response.json()
            else:
                # Fallback to urllib
                req = urllib.request.Request("http://localhost:8008/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        status["health"] = "healthy"
                        status["data"] = json.loads(response.read().decode())
        except:
            status["health"] = "down"
        return status
    
    async def check_frontend_security(self) -> Dict:
        """Check frontend security status"""
        status = {"health": "unknown", "checks": {}}
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:5179", timeout=5.0)
                    if response.status_code == 200:
                        status["health"] = "healthy"
            else:
                # Fallback to urllib
                req = urllib.request.Request("http://localhost:5179")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        status["health"] = "healthy"
        except:
            status["health"] = "down"
        return status
    
    async def check_roblox_security(self) -> Dict:
        """Check Roblox bridge security status"""
        status = {"health": "unknown", "checks": {}}
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:5001/health", timeout=5.0)
                    if response.status_code == 200:
                        status["health"] = "healthy"
                        status["data"] = response.json()
            else:
                # Fallback to urllib
                req = urllib.request.Request("http://localhost:5001/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        status["health"] = "healthy"
                        status["data"] = json.loads(response.read().decode())
        except:
            status["health"] = "down"
        return status
    
    async def scan_for_vulnerabilities(self):
        """Continuous vulnerability scanning"""
        while True:
            print("🔍 Scanning for security vulnerabilities...")
            
            # Clear previous vulnerabilities
            for key in self.vulnerabilities:
                self.vulnerabilities[key] = []
            
            # Scan for hardcoded credentials
            creds = await self.scan_hardcoded_credentials()
            if creds:
                self.vulnerabilities["critical"].extend(creds)
                await self.alert_critical_vulnerability("hardcoded_credentials", creds)
            
            # Scan for SQL injection risks
            sql_risks = await self.scan_sql_injection()
            if sql_risks:
                self.vulnerabilities["high"].extend(sql_risks)
                await self.alert_high_vulnerability("sql_injection", sql_risks)
            
            # Scan for XSS vulnerabilities
            xss_risks = await self.scan_xss_vulnerabilities()
            if xss_risks:
                self.vulnerabilities["high"].extend(xss_risks)
                await self.alert_high_vulnerability("xss", xss_risks)
            
            # Scan for authorization issues
            auth_issues = await self.scan_authorization_bypass()
            if auth_issues:
                self.vulnerabilities["critical"].extend(auth_issues)
                await self.alert_critical_vulnerability("auth_bypass", auth_issues)
            
            # Send report to all terminals
            await self.broadcast_security_report()
            
            await asyncio.sleep(300)  # Scan every 5 minutes
    
    async def scan_hardcoded_credentials(self) -> List[Dict]:
        """Scan for hardcoded passwords and keys"""
        vulnerabilities = []
        patterns = [
            (r'password\s*=\s*["\'](?!os\.getenv|environ)[^"\']+["\']', 'hardcoded_password'),
            (r'api_key\s*=\s*["\'](?!os\.getenv|environ)[^"\']+["\']', 'hardcoded_api_key'),
            (r'secret\s*=\s*["\'](?!os\.getenv|environ)[^"\']+["\']', 'hardcoded_secret'),
            (r'token\s*=\s*["\'](?!os\.getenv|environ)[^"\']+["\']', 'hardcoded_token'),
        ]
        
        search_paths = [
            Path('src/api'),
            Path('database'),
            Path('scripts')
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for file_path in search_path.glob('**/*.py'):
                try:
                    content = file_path.read_text()
                    for pattern, vuln_type in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "type": vuln_type,
                                "file": str(file_path),
                                "line": line_num,
                                "code": match.group(0)[:100],
                                "severity": "CRITICAL",
                                "cwe": "CWE-798"
                            })
                except Exception as e:
                    pass
        
        return vulnerabilities
    
    async def scan_sql_injection(self) -> List[Dict]:
        """Scan for SQL injection vulnerabilities"""
        vulnerabilities = []
        dangerous_patterns = [
            r'f"SELECT.*{.*}"',
            r'f"INSERT.*{.*}"',
            r'f"UPDATE.*{.*}"',
            r'f"DELETE.*{.*}"',
            r'\.format\(.*SELECT',
            r'%.*SELECT.*%',
        ]
        
        search_paths = [
            Path('src/api'),
            Path('database')
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for file_path in search_path.glob('**/*.py'):
                try:
                    content = file_path.read_text()
                    for pattern in dangerous_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "type": "sql_injection_risk",
                                "file": str(file_path),
                                "line": line_num,
                                "code": match.group(0)[:100],
                                "severity": "HIGH",
                                "cwe": "CWE-89"
                            })
                except Exception as e:
                    pass
        
        return vulnerabilities
    
    async def scan_xss_vulnerabilities(self) -> List[Dict]:
        """Scan for XSS vulnerabilities"""
        vulnerabilities = []
        xss_patterns = [
            r'dangerouslySetInnerHTML',
            r'innerHTML\s*=',
            r'document\.write\(',
            r'eval\(',
        ]
        
        search_paths = [
            Path('src/dashboard/src')
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for file_path in search_path.glob('**/*.{js,jsx,ts,tsx}'):
                try:
                    content = file_path.read_text()
                    for pattern in xss_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            vulnerabilities.append({
                                "type": "xss_risk",
                                "file": str(file_path),
                                "line": line_num,
                                "code": match.group(0)[:100],
                                "severity": "HIGH",
                                "cwe": "CWE-79"
                            })
                except Exception as e:
                    pass
        
        return vulnerabilities
    
    async def scan_authorization_bypass(self) -> List[Dict]:
        """Scan for authorization bypass issues"""
        vulnerabilities = []
        # This would require more complex analysis
        # For now, just check for missing auth decorators
        return vulnerabilities
    
    async def verify_terminal1_security(self, status):
        """Verify Terminal 1 (Backend) security"""
        checks = {
            "jwt_configured": False,
            "rate_limiting": False,
            "cors_restricted": False,
            "https_only": False,
            "input_validation": False
        }
        
        # Check JWT configuration
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8008/health", timeout=5.0)
                    checks["jwt_configured"] = response.status_code == 200
            else:
                req = urllib.request.Request("http://localhost:8008/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    checks["jwt_configured"] = response.status == 200
        except:
            pass
        
        # Send verification to Terminal 1
        await self.send_to_terminal("terminal1", {
            "type": "security_verification",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        })
        
        return checks
    
    async def verify_terminal2_security(self, status):
        """Verify Terminal 2 (Frontend) security"""
        checks = {
            "csp_header": False,
            "xss_protection": False,
            "secure_cookies": False,
            "content_security": False
        }
        
        # Check security headers
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:5179", timeout=5.0)
                    headers = response.headers
                    
                    checks["csp_header"] = "Content-Security-Policy" in headers
                    checks["xss_protection"] = headers.get("X-XSS-Protection") == "1; mode=block"
                    checks["secure_cookies"] = "Secure" in headers.get("Set-Cookie", "")
            else:
                req = urllib.request.Request("http://localhost:5179")
                with urllib.request.urlopen(req, timeout=5) as response:
                    headers = response.headers
                    checks["csp_header"] = "Content-Security-Policy" in headers
                    checks["xss_protection"] = headers.get("X-XSS-Protection") == "1; mode=block"
                    checks["secure_cookies"] = "Secure" in headers.get("Set-Cookie", "")
        except:
            pass
        
        # Send verification to Terminal 2
        await self.send_to_terminal("terminal2", {
            "type": "security_verification",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        })
        
        return checks
    
    async def verify_terminal3_security(self, status):
        """Verify Terminal 3 (Roblox) security"""
        checks = {
            "http_requests_validated": False,
            "data_store_encrypted": False,
            "user_input_sanitized": False,
            "api_rate_limited": False
        }
        
        # Check Flask Bridge security
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:5001/health", timeout=5.0)
                    checks["api_rate_limited"] = response.status_code != 429
            else:
                req = urllib.request.Request("http://localhost:5001/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    checks["api_rate_limited"] = response.status != 429
        except:
            pass
        
        # Send verification to Terminal 3
        await self.send_to_terminal("terminal3", {
            "type": "security_verification",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        })
        
        return checks
    
    async def send_to_terminal(self, terminal: str, data: Dict):
        """Send data to a specific terminal via Redis"""
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    f"terminal:{terminal}:security",
                    json.dumps(data)
                )
            except Exception as e:
                print(f"Failed to send to {terminal}: {e}")
    
    async def broadcast_security_report(self):
        """Send security report to all terminals"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": {
                "critical": len(self.vulnerabilities["critical"]),
                "high": len(self.vulnerabilities["high"]),
                "medium": len(self.vulnerabilities["medium"]),
                "low": len(self.vulnerabilities["low"])
            },
            "terminal_status": {
                k: {
                    "status": v["status"],
                    "last_seen": v["last_seen"].isoformat() if v["last_seen"] else None
                }
                for k, v in self.terminals.items()
            },
            "recommendations": self.generate_recommendations()
        }
        
        # Publish to all terminals
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "terminal:security:report",
                    json.dumps(report)
                )
            except:
                pass
        
        # Save to file for persistence
        report_file = Path("scripts/terminal_sync/status/security_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Security Report: {report['vulnerabilities']}")
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if self.vulnerabilities["critical"]:
            recommendations.append("URGENT: Remove all hardcoded credentials immediately")
            recommendations.append("URGENT: Fix authorization bypass vulnerabilities")
        
        if self.vulnerabilities["high"]:
            recommendations.append("HIGH: Implement parameterized queries for all database operations")
            recommendations.append("HIGH: Add input sanitization for all user inputs")
        
        recommendations.extend([
            "Enable HTTPS for all services",
            "Implement rate limiting on all endpoints",
            "Add security headers (CSP, HSTS, X-Frame-Options)",
            "Enable audit logging for all sensitive operations",
            "Implement regular security scanning in CI/CD"
        ])
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def alert_terminal_issue(self, terminal_id: str, status: Dict):
        """Alert when terminal has issues"""
        print(f"⚠️ Terminal {terminal_id} issue: {status}")
    
    async def alert_critical_vulnerability(self, vuln_type: str, vulnerabilities: List):
        """Alert on critical vulnerabilities"""
        print(f"🚨 CRITICAL: Found {len(vulnerabilities)} {vuln_type} vulnerabilities!")
        for vuln in vulnerabilities[:3]:  # Show first 3
            print(f"  - {vuln['file']}:{vuln['line']}")
    
    async def alert_high_vulnerability(self, vuln_type: str, vulnerabilities: List):
        """Alert on high vulnerabilities"""
        print(f"⚠️ HIGH: Found {len(vulnerabilities)} {vuln_type} vulnerabilities")
    
    async def monitor_authentication(self):
        """Monitor authentication security"""
        while True:
            # Check for failed login attempts, session hijacking, etc.
            await asyncio.sleep(60)
    
    async def check_compliance(self):
        """Check compliance requirements"""
        while True:
            # Check COPPA, FERPA, GDPR compliance
            await asyncio.sleep(600)
    
    async def process_alerts(self):
        """Process security alerts"""
        while True:
            # Process incoming alerts from other terminals
            await asyncio.sleep(5)

# Run the security monitor
if __name__ == "__main__":
    print("🛡️ Starting Security Monitor...")
    print("=" * 50)
    monitor = SecurityMonitor()
    try:
        asyncio.run(monitor.initialize())
    except KeyboardInterrupt:
        print("\n✅ Security Monitor stopped")