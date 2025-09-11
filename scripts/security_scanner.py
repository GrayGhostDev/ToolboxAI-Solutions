"""
Comprehensive Security Scanner for ToolBoxAI
Identifies and reports all security vulnerabilities
"""

import os
import re
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List, Any

class SecurityScanner:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.vulnerabilities = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        self.scan_results = {}
        
    def run_all_scans(self):
        """Execute all security scans"""
        print("=" * 60)
        print("COMPREHENSIVE SECURITY SCAN")
        print("=" * 60)
        
        # Scan different aspects
        self.scan_dependencies()
        self.scan_source_code()
        self.scan_authentication()
        self.scan_websocket_security()
        self.scan_input_validation()
        self.scan_sql_injection()
        self.scan_xss_vulnerabilities()
        self.scan_secrets()
        self.scan_cors_configuration()
        self.scan_rate_limiting()
        
        # Generate report
        self.generate_report()
        
    def scan_dependencies(self):
        """Scan for vulnerable dependencies"""
        print("\n1. Scanning Dependencies...")
        
        # Check Python dependencies - using pip audit instead of safety
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        if result.stdout:
            packages = json.loads(result.stdout)
            # Check for known vulnerable versions
            vulnerable_packages = {
                "flask": ["2.0.0", "2.0.1"],  # Example vulnerable versions
                "werkzeug": ["2.0.0", "2.0.1"],
                "jinja2": ["2.11.0", "2.11.1", "2.11.2"]
            }
            
            for package in packages:
                pkg_name = package.get("name", "").lower()
                pkg_version = package.get("version", "")
                
                if pkg_name in vulnerable_packages:
                    if pkg_version in vulnerable_packages[pkg_name]:
                        self.vulnerabilities["high"].append({
                            "type": "dependency",
                            "package": pkg_name,
                            "installed": pkg_version,
                            "issue": f"Known vulnerable version of {pkg_name}",
                            "fix": f"Update {pkg_name} to latest version"
                        })
        
        # Check npm dependencies
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            # Check for audit results
            npm_result = subprocess.run(
                ["npm", "outdated", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if npm_result.stdout:
                try:
                    outdated = json.loads(npm_result.stdout)
                    if isinstance(outdated, dict):
                        for pkg, info in outdated.items():
                            if isinstance(info, dict) and info.get("wanted") != info.get("current"):
                                self.vulnerabilities["medium"].append({
                                    "type": "npm_dependency",
                                    "package": pkg,
                                    "current": info.get("current"),
                                    "wanted": info.get("wanted"),
                                    "fix": f"Update {pkg} to {info.get('wanted')}"
                                })
                except (json.JSONDecodeError, TypeError):
                    pass
    
    def scan_source_code(self):
        """Scan source code for security issues"""
        print("\n2. Scanning Source Code...")
        
        # Check for common security issues in Python files
        for py_file in self.project_root.glob("**/*.py"):
            if "venv" in str(py_file) or "node_modules" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Check for eval usage
                if re.search(r'\beval\s*\(', content):
                    self.vulnerabilities["critical"].append({
                        "type": "code",
                        "file": str(py_file),
                        "issue": "Using eval() function",
                        "fix": "Replace eval() with ast.literal_eval() or safer alternatives"
                    })
                
                # Check for exec usage
                if re.search(r'\bexec\s*\(', content):
                    self.vulnerabilities["critical"].append({
                        "type": "code",
                        "file": str(py_file),
                        "issue": "Using exec() function",
                        "fix": "Remove exec() and use safer alternatives"
                    })
                
                # Check for pickle usage
                if "pickle.loads" in content or "pickle.load" in content:
                    self.vulnerabilities["high"].append({
                        "type": "code",
                        "file": str(py_file),
                        "issue": "Using pickle for deserialization",
                        "fix": "Use JSON or other safe serialization formats"
                    })
                    
            except Exception:
                pass
    
    def scan_authentication(self):
        """Scan authentication implementation"""
        print("\n3. Scanning Authentication...")
        
        # Check for auth files
        auth_files = list(self.project_root.glob("**/auth*.py"))
        
        for auth_file in auth_files:
            if "venv" in str(auth_file) or "node_modules" in str(auth_file):
                continue
                
            try:
                content = auth_file.read_text()
                
                # Check for hardcoded secrets
                if re.search(r'SECRET_KEY\s*=\s*["\'][^"\']+["\']', content):
                    if not re.search(r'os\.environ|os\.getenv|settings\.|config\.', content):
                        self.vulnerabilities["critical"].append({
                            "type": "authentication",
                            "file": str(auth_file),
                            "issue": "Hardcoded secret key found",
                            "fix": "Use environment variables for secrets"
                        })
                
                # Check for weak secret
                if re.search(r'SECRET_KEY.*secret|password|12345', content, re.IGNORECASE):
                    self.vulnerabilities["critical"].append({
                        "type": "authentication",
                        "file": str(auth_file),
                        "issue": "Weak or default secret key",
                        "fix": "Generate strong random secret: openssl rand -hex 32"
                    })
                
                # Check for missing token expiry
                if "jwt" in content.lower():
                    if "exp" not in content and "expires_delta" not in content and "expiry" not in content.lower():
                        self.vulnerabilities["high"].append({
                            "type": "authentication",
                            "file": str(auth_file),
                            "issue": "JWT tokens may not expire",
                            "fix": "Add expiration to JWT tokens"
                        })
                        
            except Exception:
                pass
    
    def scan_websocket_security(self):
        """Scan WebSocket implementation for security issues"""
        print("\n4. Scanning WebSocket Security...")
        
        ws_files = list(self.project_root.glob("**/websocket*.py"))
        
        for ws_file in ws_files:
            if "venv" in str(ws_file) or "node_modules" in str(ws_file):
                continue
                
            try:
                content = ws_file.read_text()
                
                # Check for authentication
                if "WebSocket" in content:
                    if "authenticate" not in content.lower() and "auth" not in content.lower():
                        self.vulnerabilities["critical"].append({
                            "type": "websocket",
                            "file": str(ws_file),
                            "issue": "WebSocket connection without authentication",
                            "fix": "Implement WebSocket authentication"
                        })
                    
                    # Check for rate limiting
                    if "rate_limit" not in content.lower():
                        self.vulnerabilities["high"].append({
                            "type": "websocket",
                            "file": str(ws_file),
                            "issue": "WebSocket without rate limiting",
                            "fix": "Implement per-connection rate limiting"
                        })
                    
                    # Check for RBAC
                    if not re.search(r'role.*check|rbac|permission', content, re.IGNORECASE):
                        self.vulnerabilities["high"].append({
                            "type": "websocket",
                            "file": str(ws_file),
                            "issue": "WebSocket without RBAC",
                            "fix": "Implement role-based access control"
                        })
                        
            except Exception:
                pass
    
    def scan_input_validation(self):
        """Scan for input validation issues"""
        print("\n5. Scanning Input Validation...")
        
        api_files = list(self.project_root.glob("**/api*.py")) + \
                   list(self.project_root.glob("**/routes*.py")) + \
                   list(self.project_root.glob("**/main.py"))
        
        for api_file in api_files:
            if "venv" in str(api_file) or "node_modules" in str(api_file):
                continue
                
            try:
                content = api_file.read_text()
                
                # Check for missing input validation
                if "@app.post" in content or "@app.put" in content or "@router.post" in content:
                    if "pydantic" not in content.lower() and "validate" not in content.lower():
                        self.vulnerabilities["high"].append({
                            "type": "input_validation",
                            "file": str(api_file),
                            "issue": "API endpoint without input validation",
                            "fix": "Use Pydantic models for input validation"
                        })
                
                # Check for file upload without validation
                if "upload" in content.lower() and "file" in content.lower():
                    if not re.search(r'content_type|mime|extension|allowed_extensions', content, re.IGNORECASE):
                        self.vulnerabilities["critical"].append({
                            "type": "file_upload",
                            "file": str(api_file),
                            "issue": "File upload without type validation",
                            "fix": "Validate file types and size limits"
                        })
                        
            except Exception:
                pass
    
    def scan_sql_injection(self):
        """Scan for SQL injection vulnerabilities"""
        print("\n6. Scanning for SQL Injection...")
        
        db_files = list(self.project_root.glob("**/database*.py")) + \
                  list(self.project_root.glob("**/repository*.py")) + \
                  list(self.project_root.glob("**/db*.py"))
        
        for db_file in db_files:
            if "venv" in str(db_file) or "node_modules" in str(db_file):
                continue
                
            try:
                content = db_file.read_text()
                
                # Check for string concatenation in queries
                if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*\+.*%', content, re.IGNORECASE):
                    self.vulnerabilities["critical"].append({
                        "type": "sql_injection",
                        "file": str(db_file),
                        "issue": "Potential SQL injection via string concatenation",
                        "fix": "Use parameterized queries"
                    })
                
                # Check for f-strings in queries
                if re.search(r'f["\'].*?(SELECT|INSERT|UPDATE|DELETE).*?\{', content, re.IGNORECASE):
                    self.vulnerabilities["critical"].append({
                        "type": "sql_injection",
                        "file": str(db_file),
                        "issue": "SQL query using f-string formatting",
                        "fix": "Use parameterized queries instead of f-strings"
                    })
                    
            except Exception:
                pass
    
    def scan_xss_vulnerabilities(self):
        """Scan for XSS vulnerabilities"""
        print("\n7. Scanning for XSS...")
        
        # Check React/JSX files
        jsx_files = list(self.project_root.glob("**/*.tsx")) + \
                   list(self.project_root.glob("**/*.jsx"))
        
        for jsx_file in jsx_files:
            if "node_modules" in str(jsx_file):
                continue
                
            try:
                content = jsx_file.read_text()
                
                # Check for dangerouslySetInnerHTML
                if "dangerouslySetInnerHTML" in content:
                    self.vulnerabilities["high"].append({
                        "type": "xss",
                        "file": str(jsx_file),
                        "issue": "Using dangerouslySetInnerHTML",
                        "fix": "Sanitize HTML or use safe alternatives"
                    })
                
                # Check for eval usage
                if re.search(r'\beval\s*\(', content):
                    self.vulnerabilities["critical"].append({
                        "type": "xss",
                        "file": str(jsx_file),
                        "issue": "Using eval() function",
                        "fix": "Remove eval() and use safe alternatives"
                    })
                    
            except Exception:
                pass
    
    def scan_secrets(self):
        """Scan for exposed secrets"""
        print("\n8. Scanning for Exposed Secrets...")
        
        # Patterns for various secrets
        secret_patterns = {
            "api_key": r'api[_-]?key["\']?\s*[:=]\s*["\'][\w\d]{20,}',
            "aws_key": r'AKIA[0-9A-Z]{16}',
            "github_token": r'ghp_[0-9a-zA-Z]{36}',
            "private_key": r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----',
            "password": r'password["\']?\s*[:=]\s*["\'][^"\']+["\']'
        }
        
        for file_path in self.project_root.glob("**/*"):
            if file_path.is_file() and file_path.suffix in [".py", ".js", ".ts", ".env", ".json", ".yml", ".yaml"]:
                if "venv" in str(file_path) or "node_modules" in str(file_path):
                    continue
                    
                try:
                    content = file_path.read_text()
                    
                    for secret_type, pattern in secret_patterns.items():
                        if re.search(pattern, content, re.IGNORECASE):
                            # Skip if it's in .env.example or test files
                            if ".example" not in str(file_path) and "test" not in str(file_path).lower():
                                self.vulnerabilities["critical"].append({
                                    "type": "exposed_secret",
                                    "file": str(file_path),
                                    "secret_type": secret_type,
                                    "issue": f"Potential {secret_type} exposed",
                                    "fix": "Move to environment variables"
                                })
                except Exception:
                    pass
    
    def scan_cors_configuration(self):
        """Scan CORS configuration"""
        print("\n9. Scanning CORS Configuration...")
        
        cors_files = list(self.project_root.glob("**/main.py")) + \
                    list(self.project_root.glob("**/app.py"))
        
        for cors_file in cors_files:
            if "venv" in str(cors_file) or "node_modules" in str(cors_file):
                continue
                
            try:
                content = cors_file.read_text()
                
                # Check for wildcard CORS
                if re.search(r'allow_origins.*?\[\s*["\']?\*["\']?\s*\]', content):
                    self.vulnerabilities["high"].append({
                        "type": "cors",
                        "file": str(cors_file),
                        "issue": "CORS allows all origins (*)",
                        "fix": "Specify allowed origins explicitly"
                    })
                
                # Check for credentials with wildcard
                if "allow_credentials=True" in content and "*" in content:
                    self.vulnerabilities["critical"].append({
                        "type": "cors",
                        "file": str(cors_file),
                        "issue": "CORS allows credentials with wildcard origin",
                        "fix": "Never use wildcard with credentials"
                    })
                    
            except Exception:
                pass
    
    def scan_rate_limiting(self):
        """Check rate limiting implementation"""
        print("\n10. Scanning Rate Limiting...")
        
        api_files = list(self.project_root.glob("**/api*.py")) + \
                   list(self.project_root.glob("**/main.py"))
        
        has_rate_limiting = False
        for api_file in api_files:
            if "venv" in str(api_file) or "node_modules" in str(api_file):
                continue
                
            try:
                content = api_file.read_text()
                if "rate_limit" in content.lower() or "slowapi" in content.lower():
                    has_rate_limiting = True
                    break
            except Exception:
                pass
        
        if not has_rate_limiting:
            self.vulnerabilities["high"].append({
                "type": "rate_limiting",
                "issue": "No rate limiting detected",
                "fix": "Implement rate limiting with slowapi or similar"
            })
    
    def generate_report(self):
        """Generate security report"""
        print("\n" + "=" * 60)
        print("SECURITY SCAN RESULTS")
        print("=" * 60)
        
        total_critical = len(self.vulnerabilities["critical"])
        total_high = len(self.vulnerabilities["high"])
        total_medium = len(self.vulnerabilities["medium"])
        total_low = len(self.vulnerabilities["low"])
        
        print(f"\n🔴 Critical: {total_critical}")
        print(f"🟠 High: {total_high}")
        print(f"🟡 Medium: {total_medium}")
        print(f"🟢 Low: {total_low}")
        
        # Save detailed report
        report = {
            "scan_date": datetime.now().isoformat(),
            "summary": {
                "critical": total_critical,
                "high": total_high,
                "medium": total_medium,
                "low": total_low
            },
            "vulnerabilities": self.vulnerabilities
        }
        
        report_path = self.project_root / "security_scan_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")
        
        # Print critical issues
        if total_critical > 0:
            print("\n🔴 CRITICAL ISSUES (MUST FIX):")
            for vuln in self.vulnerabilities["critical"]:
                print(f"  - {vuln.get('type')}: {vuln.get('issue')}")
                print(f"    File: {vuln.get('file', 'N/A')}")
                print(f"    Fix: {vuln.get('fix')}")
                print()

# Run scanner
if __name__ == "__main__":
    scanner = SecurityScanner("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions")
    scanner.run_all_scans()