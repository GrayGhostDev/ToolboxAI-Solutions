# TERMINAL 4: SECURITY & TESTING SPECIALIST
**Priority: CRITICAL | Status: 4 Critical, 13 High Vulnerabilities | Target: 0 Critical, 0 High in 24 hours**

## YOUR MISSION
You are the Security & Testing Specialist responsible for identifying and patching ALL security vulnerabilities, implementing the new WebSocket RBAC and rate limiting features from CLAUDE.md, and ensuring comprehensive test coverage. The system CANNOT go to production with critical vulnerabilities.

## CURRENT SECURITY STATUS
```
🔴 4 Critical Vulnerabilities (MUST FIX)
🟠 13 High Vulnerabilities (MUST FIX)
⚠️ WebSocket RBAC not fully implemented
⚠️ Rate limiting incomplete
⚠️ JWT token expiry not enforced properly
❌ Input validation missing in several endpoints
```

## DEPENDENCIES
- **Terminal 1**: FastAPI must be running for API testing
- **Terminal 2**: Dashboard must be accessible for frontend security testing
- **Terminal 3**: Roblox integration ready for security audit

## PHASE 1: CRITICAL VULNERABILITY SCANNING (First 2 hours)

### Task 1.1: Run Comprehensive Security Scan
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Install security scanning tools
pip install safety bandit sqlparse pyjwt cryptography paramiko

# Create security scanner script
cat > security_scanner.py << 'EOF'
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
import jwt
import hashlib

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
        
        # Check Python dependencies
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            vulnerabilities = json.loads(result.stdout)
            for vuln in vulnerabilities:
                self.vulnerabilities["critical"].append({
                    "type": "dependency",
                    "package": vuln.get("package"),
                    "installed": vuln.get("installed_version"),
                    "affected": vuln.get("affected_versions"),
                    "description": vuln.get("description"),
                    "fix": f"Update to {vuln.get('latest_version')}"
                })
        
        # Check npm dependencies
        if Path("package.json").exists():
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout:
                audit = json.loads(result.stdout)
                if "vulnerabilities" in audit:
                    for severity in ["critical", "high", "moderate", "low"]:
                        count = audit["vulnerabilities"].get(severity, 0)
                        if count > 0:
                            level = "critical" if severity == "critical" else \
                                   "high" if severity == "high" else \
                                   "medium" if severity == "moderate" else "low"
                            
                            self.vulnerabilities[level].append({
                                "type": "npm_dependency",
                                "severity": severity,
                                "count": count,
                                "fix": "Run: npm audit fix --force"
                            })
    
    def scan_source_code(self):
        """Scan source code for security issues"""
        print("\n2. Scanning Source Code...")
        
        # Run bandit for Python security issues
        result = subprocess.run(
            ["bandit", "-r", ".", "-f", "json", "-ll"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        if result.stdout:
            bandit_results = json.loads(result.stdout)
            for issue in bandit_results.get("results", []):
                severity = issue.get("issue_severity", "").lower()
                level = "critical" if severity == "high" else \
                       "high" if severity == "medium" else "medium"
                
                self.vulnerabilities[level].append({
                    "type": "code",
                    "file": issue.get("filename"),
                    "line": issue.get("line_number"),
                    "issue": issue.get("issue_text"),
                    "fix": issue.get("more_info")
                })
    
    def scan_authentication(self):
        """Scan authentication implementation"""
        print("\n3. Scanning Authentication...")
        
        # Check for weak JWT configuration
        auth_files = list(self.project_root.glob("**/auth*.py"))
        
        for auth_file in auth_files:
            content = auth_file.read_text()
            
            # Check for hardcoded secrets
            if re.search(r'SECRET_KEY\s*=\s*["\'][\w\d]+["\']', content):
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
            if "exp" not in content and "expires_delta" not in content:
                self.vulnerabilities["high"].append({
                    "type": "authentication",
                    "file": str(auth_file),
                    "issue": "JWT tokens may not expire",
                    "fix": "Add expiration to JWT tokens"
                })
    
    def scan_websocket_security(self):
        """Scan WebSocket implementation for security issues"""
        print("\n4. Scanning WebSocket Security...")
        
        ws_files = list(self.project_root.glob("**/websocket*.py"))
        
        for ws_file in ws_files:
            content = ws_file.read_text()
            
            # Check for authentication
            if "WebSocket" in content and "authenticate" not in content.lower():
                self.vulnerabilities["critical"].append({
                    "type": "websocket",
                    "file": str(ws_file),
                    "issue": "WebSocket connection without authentication",
                    "fix": "Implement WebSocket authentication"
                })
            
            # Check for rate limiting
            if "WebSocket" in content and "rate_limit" not in content.lower():
                self.vulnerabilities["high"].append({
                    "type": "websocket",
                    "file": str(ws_file),
                    "issue": "WebSocket without rate limiting",
                    "fix": "Implement per-connection rate limiting"
                })
            
            # Check for RBAC
            if "WebSocket" in content and not re.search(r'role.*check|rbac|permission', content, re.IGNORECASE):
                self.vulnerabilities["high"].append({
                    "type": "websocket",
                    "file": str(ws_file),
                    "issue": "WebSocket without RBAC",
                    "fix": "Implement role-based access control"
                })
    
    def scan_input_validation(self):
        """Scan for input validation issues"""
        print("\n5. Scanning Input Validation...")
        
        api_files = list(self.project_root.glob("**/api*.py")) + \
                   list(self.project_root.glob("**/routes*.py")) + \
                   list(self.project_root.glob("**/main.py"))
        
        for api_file in api_files:
            content = api_file.read_text()
            
            # Check for missing input validation
            if "@app.post" in content or "@app.put" in content:
                if "pydantic" not in content.lower() and "validate" not in content.lower():
                    self.vulnerabilities["high"].append({
                        "type": "input_validation",
                        "file": str(api_file),
                        "issue": "API endpoint without input validation",
                        "fix": "Use Pydantic models for input validation"
                    })
            
            # Check for file upload without validation
            if "upload" in content.lower() and "file" in content.lower():
                if not re.search(r'content_type|mime|extension', content, re.IGNORECASE):
                    self.vulnerabilities["critical"].append({
                        "type": "file_upload",
                        "file": str(api_file),
                        "issue": "File upload without type validation",
                        "fix": "Validate file types and size limits"
                    })
    
    def scan_sql_injection(self):
        """Scan for SQL injection vulnerabilities"""
        print("\n6. Scanning for SQL Injection...")
        
        db_files = list(self.project_root.glob("**/database*.py")) + \
                  list(self.project_root.glob("**/repository*.py"))
        
        for db_file in db_files:
            content = db_file.read_text()
            
            # Check for string concatenation in queries
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*\+.*%(.*?)\%', content, re.IGNORECASE):
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
    
    def scan_xss_vulnerabilities(self):
        """Scan for XSS vulnerabilities"""
        print("\n7. Scanning for XSS...")
        
        # Check React/JSX files
        jsx_files = list(self.project_root.glob("**/*.tsx")) + \
                   list(self.project_root.glob("**/*.jsx"))
        
        for jsx_file in jsx_files:
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
    
    def scan_secrets(self):
        """Scan for exposed secrets"""
        print("\n8. Scanning for Exposed Secrets...")
        
        # Patterns for various secrets
        secret_patterns = {
            "api_key": r'api[_-]?key["\']?\s*[:=]\s*["\'][\w\d]{20,}',
            "aws_key": r'AKIA[0-9A-Z]{16}',
            "github_token": r'ghp_[0-9a-zA-Z]{36}',
            "private_key": r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----',
            "password": r'password["\']?\s*[:=]\s*["\']\w+["\']'
        }
        
        for file_path in self.project_root.glob("**/*"):
            if file_path.is_file() and file_path.suffix in [".py", ".js", ".ts", ".env", ".json"]:
                try:
                    content = file_path.read_text()
                    
                    for secret_type, pattern in secret_patterns.items():
                        if re.search(pattern, content, re.IGNORECASE):
                            # Skip if it's in .env.example
                            if ".example" not in str(file_path):
                                self.vulnerabilities["critical"].append({
                                    "type": "exposed_secret",
                                    "file": str(file_path),
                                    "secret_type": secret_type,
                                    "issue": f"Potential {secret_type} exposed",
                                    "fix": "Move to environment variables"
                                })
                except:
                    pass
    
    def scan_cors_configuration(self):
        """Scan CORS configuration"""
        print("\n9. Scanning CORS Configuration...")
        
        cors_files = list(self.project_root.glob("**/main.py")) + \
                    list(self.project_root.glob("**/app.py"))
        
        for cors_file in cors_files:
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
    
    def scan_rate_limiting(self):
        """Check rate limiting implementation"""
        print("\n10. Scanning Rate Limiting...")
        
        api_files = list(self.project_root.glob("**/api*.py")) + \
                   list(self.project_root.glob("**/main.py"))
        
        has_rate_limiting = False
        for api_file in api_files:
            content = api_file.read_text()
            if "rate_limit" in content.lower() or "slowapi" in content.lower():
                has_rate_limiting = True
                break
        
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
        
        with open("security_scan_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: security_scan_report.json")
        
        # Print critical issues
        if total_critical > 0:
            print("\n🔴 CRITICAL ISSUES (MUST FIX):")
            for vuln in self.vulnerabilities["critical"]:
                print(f"  - {vuln.get('type')}: {vuln.get('issue')}")
                print(f"    File: {vuln.get('file', 'N/A')}")
                print(f"    Fix: {vuln.get('fix')}")
                print()

# Run scanner
scanner = SecurityScanner()
scanner.run_all_scans()
EOF

python security_scanner.py
```

## PHASE 2: PATCH CRITICAL VULNERABILITIES (Next 3 hours)

### Task 2.1: Fix Authentication & JWT Issues
```bash
# Fix JWT implementation with proper expiry and validation
cat > ToolboxAI-Roblox-Environment/server/auth_secure.py << 'EOF'
"""
Secure Authentication Implementation
Fixes all JWT and authentication vulnerabilities
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import redis
from functools import wraps
import time

# Security configuration from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    # Generate secure key if not provided
    SECRET_KEY = secrets.token_hex(32)
    print(f"WARNING: Generated new secret key. Set JWT_SECRET_KEY in .env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes

# Redis for token blacklist and rate limiting
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    """Token payload with validation"""
    sub: str  # User ID
    role: str
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['admin', 'teacher', 'student', 'parent']
        if v not in allowed_roles:
            raise ValueError(f"Invalid role: {v}")
        return v

class SecureAuth:
    """Secure authentication handler"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain number")
        
        # Hash with bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with security features"""
        to_encode = data.copy()
        
        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Add security claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),  # Unique token ID
            "type": "access"
        })
        
        # Encode token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Store in Redis with expiry
        redis_client.setex(
            f"refresh_token:{user_id}",
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            encoded_jwt
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True}
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError("Invalid token type")
            
            # Check if token is blacklisted
            if redis_client.get(f"blacklist:{payload.get('jti')}"):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    @staticmethod
    def revoke_token(token: str):
        """Revoke a token by adding to blacklist"""
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp:
                # Calculate TTL until token expiry
                ttl = exp - datetime.now(timezone.utc).timestamp()
                if ttl > 0:
                    redis_client.setex(
                        f"blacklist:{jti}",
                        int(ttl),
                        "revoked"
                    )
                    
        except Exception:
            pass  # Token already invalid
    
    @staticmethod
    def check_login_attempts(username: str) -> bool:
        """Check if user is locked out due to failed attempts"""
        attempts_key = f"login_attempts:{username}"
        lockout_key = f"lockout:{username}"
        
        # Check if locked out
        if redis_client.get(lockout_key):
            return False
        
        # Get attempt count
        attempts = redis_client.get(attempts_key)
        if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
            # Lock out user
            redis_client.setex(lockout_key, LOCKOUT_DURATION, "locked")
            redis_client.delete(attempts_key)
            return False
        
        return True
    
    @staticmethod
    def record_failed_login(username: str):
        """Record failed login attempt"""
        attempts_key = f"login_attempts:{username}"
        
        # Increment attempts
        attempts = redis_client.incr(attempts_key)
        
        # Set expiry if first attempt
        if attempts == 1:
            redis_client.expire(attempts_key, 900)  # 15 minutes
    
    @staticmethod
    def clear_login_attempts(username: str):
        """Clear login attempts on successful login"""
        redis_client.delete(f"login_attempts:{username}")
        redis_client.delete(f"lockout:{username}")

# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    
    # Verify token
    payload = SecureAuth.verify_token(token)
    
    # Return user data
    return {
        "id": payload.get("sub"),
        "role": payload.get("role"),
        "token_id": payload.get("jti")
    }

# Role-based access control decorator
def require_role(allowed_roles: list):
    """Decorator for role-based access control"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.get("role") not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{current_user.get('role')}' not authorized"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Rate limiting
class RateLimiter:
    """Rate limiter using Redis"""
    
    @staticmethod
    def check_rate_limit(
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """Check if rate limit exceeded"""
        current = redis_client.incr(key)
        
        if current == 1:
            redis_client.expire(key, window_seconds)
        
        return current <= max_requests
    
    @staticmethod
    def rate_limit_decorator(max_requests: int = 100, window: int = 60):
        """Decorator for rate limiting"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get user ID or IP for rate limiting
                request = kwargs.get("request")
                if request:
                    key = f"rate_limit:{request.client.host}"
                    
                    if not RateLimiter.check_rate_limit(key, max_requests, window):
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit exceeded"
                        )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator

# Export secure authentication
auth = SecureAuth()
rate_limiter = RateLimiter()
EOF
```

### Task 2.2: Implement WebSocket RBAC and Rate Limiting
```bash
# Implement secure WebSocket with RBAC based on CLAUDE.md updates
cat > ToolboxAI-Roblox-Environment/server/websocket_secure.py << 'EOF'
"""
Secure WebSocket Implementation with RBAC and Rate Limiting
Based on security requirements from CLAUDE.md
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import jwt
from collections import defaultdict
import time

from server.auth_secure import SecureAuth, SECRET_KEY, ALGORITHM
from server.config import settings

class RBACManager:
    """Role-Based Access Control for WebSocket messages"""
    
    # Message type to required role mapping (from CLAUDE.md)
    RBAC_RULES = {
        # Student actions
        "ping": ["student", "teacher", "admin"],
        "subscribe": ["student", "teacher", "admin"],
        "quiz_response": ["student", "teacher", "admin"],
        "progress_update": ["student", "teacher", "admin"],
        
        # Teacher actions
        "broadcast": ["teacher", "admin"],
        "content_request": ["teacher", "admin"],
        "roblox_event": ["teacher", "admin"],
        "create_quiz": ["teacher", "admin"],
        "grade_submission": ["teacher", "admin"],
        
        # Admin actions
        "system_broadcast": ["admin"],
        "user_management": ["admin"],
        "config_update": ["admin"],
        "rbac_update": ["admin"]
    }
    
    @classmethod
    def check_permission(cls, message_type: str, user_role: str) -> bool:
        """Check if user role has permission for message type"""
        allowed_roles = cls.RBAC_RULES.get(message_type, [])
        return user_role in allowed_roles
    
    @classmethod
    def get_rbac_rules(cls) -> Dict[str, list]:
        """Get current RBAC rules"""
        return cls.RBAC_RULES.copy()
    
    @classmethod
    def update_rbac_rules(cls, updates: Dict[str, list]) -> bool:
        """Update RBAC rules (admin only)"""
        try:
            for message_type, roles in updates.items():
                if isinstance(roles, list):
                    cls.RBAC_RULES[message_type] = roles
            return True
        except Exception:
            return False

class WebSocketRateLimiter:
    """Per-connection rate limiting for WebSocket"""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "message_count": 0,
            "window_start": time.time(),
            "blocked_until": 0
        })
    
    def check_rate_limit(
        self,
        connection_id: str,
        max_messages: int = None,
        window_seconds: int = 60
    ) -> bool:
        """Check if connection exceeded rate limit"""
        
        # Use settings or defaults
        max_messages = max_messages or settings.WS_RATE_LIMIT_PER_MINUTE
        
        conn_data = self.connections[connection_id]
        current_time = time.time()
        
        # Check if blocked
        if current_time < conn_data["blocked_until"]:
            return False
        
        # Reset window if expired
        if current_time - conn_data["window_start"] >= window_seconds:
            conn_data["message_count"] = 0
            conn_data["window_start"] = current_time
        
        # Increment and check
        conn_data["message_count"] += 1
        
        if conn_data["message_count"] > max_messages:
            # Block for remaining window time
            conn_data["blocked_until"] = conn_data["window_start"] + window_seconds
            return False
        
        return True
    
    def cleanup_connection(self, connection_id: str):
        """Remove connection from tracking"""
        if connection_id in self.connections:
            del self.connections[connection_id]

class SecureWebSocketManager:
    """Secure WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.rate_limiter = WebSocketRateLimiter()
        self.rbac = RBACManager()
        self.metrics = {
            "total_connections": 0,
            "messages_processed": 0,
            "auth_failures": 0,
            "rate_limit_hits": 0,
            "rbac_denials": 0,
            "token_expired": 0
        }
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        token: str
    ) -> Optional[Dict[str, Any]]:
        """Establish secure WebSocket connection"""
        
        try:
            # Verify JWT token
            payload = SecureAuth.verify_token(token)
            
            # Extract user info
            user_info = {
                "id": payload.get("sub"),
                "role": payload.get("role"),
                "token_exp": payload.get("exp"),
                "connected_at": datetime.utcnow().isoformat()
            }
            
            # Accept WebSocket connection
            await websocket.accept()
            
            # Store connection info
            self.active_connections[client_id] = {
                "websocket": websocket,
                "user": user_info,
                "last_activity": time.time()
            }
            
            self.metrics["total_connections"] += 1
            
            # Send authentication success
            await self.send_personal_message(
                client_id,
                {
                    "type": "auth_success",
                    "user": user_info,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return user_info
            
        except Exception as e:
            self.metrics["auth_failures"] += 1
            await websocket.close(code=1008, reason="Authentication failed")
            return None
    
    def disconnect(self, client_id: str):
        """Disconnect WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.rate_limiter.cleanup_connection(client_id)
    
    async def send_personal_message(
        self,
        client_id: str,
        message: Dict[str, Any]
    ):
        """Send message to specific client"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            websocket = connection["websocket"]
            
            try:
                await websocket.send_json(message)
            except Exception:
                # Connection lost, clean up
                self.disconnect(client_id)
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
        role_filter: Optional[str] = None
    ):
        """Broadcast message to multiple clients"""
        exclude = exclude or set()
        
        disconnected = []
        for client_id, connection in self.active_connections.items():
            if client_id in exclude:
                continue
            
            # Apply role filter if specified
            if role_filter and connection["user"]["role"] != role_filter:
                continue
            
            try:
                await connection["websocket"].send_json(message)
            except Exception:
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def handle_message(
        self,
        client_id: str,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process incoming WebSocket message with security checks"""
        
        if client_id not in self.active_connections:
            return None
        
        connection = self.active_connections[client_id]
        user = connection["user"]
        
        # Check token expiry
        if user["token_exp"] < time.time():
            self.metrics["token_expired"] += 1
            await self.send_personal_message(
                client_id,
                {
                    "type": "error",
                    "error": "token_expired",
                    "message": "Authentication token has expired"
                }
            )
            await connection["websocket"].close(code=1008, reason="Token expired")
            self.disconnect(client_id)
            return None
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(client_id):
            self.metrics["rate_limit_hits"] += 1
            await self.send_personal_message(
                client_id,
                {
                    "type": "error",
                    "error": "rate_limit",
                    "message": "Rate limit exceeded. Please slow down."
                }
            )
            return None
        
        # Check RBAC permissions
        message_type = message.get("type", "unknown")
        if not self.rbac.check_permission(message_type, user["role"]):
            self.metrics["rbac_denials"] += 1
            await self.send_personal_message(
                client_id,
                {
                    "type": "error",
                    "error": "permission_denied",
                    "message": f"Role '{user['role']}' cannot perform '{message_type}'"
                }
            )
            return None
        
        # Update last activity
        connection["last_activity"] = time.time()
        self.metrics["messages_processed"] += 1
        
        # Process message based on type
        return await self.process_message(client_id, message, user)
    
    async def process_message(
        self,
        client_id: str,
        message: Dict[str, Any],
        user: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process validated message"""
        
        message_type = message.get("type")
        
        if message_type == "ping":
            return {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        
        elif message_type == "broadcast":
            # Teacher/Admin broadcast
            await self.broadcast(
                {
                    "type": "broadcast",
                    "from": user["id"],
                    "role": user["role"],
                    "message": message.get("content"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude={client_id}
            )
            return {"type": "broadcast_sent", "status": "success"}
        
        elif message_type == "subscribe":
            # Subscribe to channel
            channel = message.get("channel")
            # Implementation for channel subscription
            return {"type": "subscribed", "channel": channel}
        
        elif message_type == "content_request":
            # Teacher requesting content generation
            # Forward to content generation service
            return {
                "type": "content_request_received",
                "request_id": message.get("request_id"),
                "status": "processing"
            }
        
        # Add more message handlers as needed
        
        return None
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        
        role_distribution = defaultdict(int)
        for conn in self.active_connections.values():
            role_distribution[conn["user"]["role"]] += 1
        
        return {
            "active_connections": len(self.active_connections),
            "role_distribution": dict(role_distribution),
            "metrics": self.metrics,
            "rbac_rules": self.rbac.get_rbac_rules()
        }
    
    async def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """Clean up inactive connections"""
        current_time = time.time()
        disconnected = []
        
        for client_id, connection in self.active_connections.items():
            if current_time - connection["last_activity"] > timeout_seconds:
                disconnected.append(client_id)
        
        for client_id in disconnected:
            connection = self.active_connections[client_id]
            await connection["websocket"].close(
                code=1000,
                reason="Connection timeout due to inactivity"
            )
            self.disconnect(client_id)

# Global WebSocket manager instance
ws_manager = SecureWebSocketManager()

# Background task for cleanup
async def websocket_cleanup_task():
    """Periodic cleanup of inactive connections"""
    while True:
        await asyncio.sleep(60)  # Run every minute
        await ws_manager.cleanup_inactive_connections()
EOF
```

## PHASE 3: IMPLEMENT COMPREHENSIVE TESTING (Next 2 hours)

### Task 3.1: Create Security Test Suite
```bash
cat > ToolboxAI-Roblox-Environment/tests/test_security.py << 'EOF'
"""
Comprehensive Security Test Suite
Tests all security implementations
"""

import pytest
import jwt
import json
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import redis

from server.main import app
from server.auth_secure import SecureAuth, RateLimiter
from server.websocket_secure import SecureWebSocketManager, RBACManager

class TestAuthentication:
    """Test authentication security"""
    
    def test_password_hashing(self):
        """Test secure password hashing"""
        password = "SecurePass123!"
        
        # Hash password
        hashed = SecureAuth.hash_password(password)
        
        # Verify hash is different from original
        assert hashed != password
        
        # Verify password
        assert SecureAuth.verify_password(password, hashed)
        
        # Wrong password should fail
        assert not SecureAuth.verify_password("WrongPass", hashed)
    
    def test_weak_password_rejection(self):
        """Test weak passwords are rejected"""
        weak_passwords = [
            "short",  # Too short
            "alllowercase",  # No uppercase
            "ALLUPPERCASE",  # No lowercase
            "NoNumbers!",  # No digits
            "12345678"  # No letters
        ]
        
        for weak_pass in weak_passwords:
            with pytest.raises(ValueError):
                SecureAuth.hash_password(weak_pass)
    
    def test_jwt_token_creation(self):
        """Test JWT token creation with security features"""
        user_data = {
            "sub": "user123",
            "role": "teacher"
        }
        
        token = SecureAuth.create_access_token(user_data)
        
        # Decode token
        payload = jwt.decode(
            token,
            SecureAuth.SECRET_KEY,
            algorithms=[SecureAuth.ALGORITHM]
        )
        
        # Verify claims
        assert payload["sub"] == "user123"
        assert payload["role"] == "teacher"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload  # Unique token ID
        assert payload["type"] == "access"
    
    def test_token_expiration(self):
        """Test token expiration"""
        user_data = {"sub": "user123", "role": "student"}
        
        # Create token with 1 second expiry
        token = SecureAuth.create_access_token(
            user_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        payload = SecureAuth.verify_token(token)
        assert payload["sub"] == "user123"
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Token should be expired
        with pytest.raises(Exception):
            SecureAuth.verify_token(token)
    
    def test_token_revocation(self):
        """Test token revocation"""
        user_data = {"sub": "user123", "role": "admin"}
        token = SecureAuth.create_access_token(user_data)
        
        # Token should be valid
        payload = SecureAuth.verify_token(token)
        assert payload is not None
        
        # Revoke token
        SecureAuth.revoke_token(token)
        
        # Token should be invalid
        with pytest.raises(Exception):
            SecureAuth.verify_token(token)
    
    def test_login_attempt_limiting(self):
        """Test login attempt limiting"""
        username = "test_user"
        
        # Should allow initial attempts
        assert SecureAuth.check_login_attempts(username)
        
        # Record failed attempts
        for _ in range(5):
            SecureAuth.record_failed_login(username)
        
        # Should be locked out
        assert not SecureAuth.check_login_attempts(username)
        
        # Clear attempts
        SecureAuth.clear_login_attempts(username)
        
        # Should be allowed again
        assert SecureAuth.check_login_attempts(username)

class TestWebSocketSecurity:
    """Test WebSocket security features"""
    
    @pytest.fixture
    def ws_manager(self):
        return SecureWebSocketManager()
    
    async def test_websocket_authentication(self, ws_manager):
        """Test WebSocket requires authentication"""
        mock_websocket = Mock()
        
        # Invalid token should fail
        result = await ws_manager.connect(
            mock_websocket,
            "client1",
            "invalid_token"
        )
        
        assert result is None
        assert ws_manager.metrics["auth_failures"] > 0
    
    async def test_websocket_rbac(self, ws_manager):
        """Test WebSocket RBAC enforcement"""
        # Test student cannot broadcast
        assert not RBACManager.check_permission("broadcast", "student")
        
        # Test teacher can broadcast
        assert RBACManager.check_permission("broadcast", "teacher")
        
        # Test admin can do everything
        assert RBACManager.check_permission("broadcast", "admin")
        assert RBACManager.check_permission("system_broadcast", "admin")
        
        # Test student can do basic actions
        assert RBACManager.check_permission("ping", "student")
        assert RBACManager.check_permission("quiz_response", "student")
    
    async def test_websocket_rate_limiting(self, ws_manager):
        """Test WebSocket rate limiting"""
        client_id = "test_client"
        
        # Should allow initial messages
        for i in range(60):
            assert ws_manager.rate_limiter.check_rate_limit(
                client_id,
                max_messages=60,
                window_seconds=60
            )
        
        # Should block after limit
        assert not ws_manager.rate_limiter.check_rate_limit(
            client_id,
            max_messages=60,
            window_seconds=60
        )
    
    async def test_token_expiry_check(self, ws_manager):
        """Test WebSocket checks token expiry"""
        client_id = "test_client"
        expired_user = {
            "id": "user123",
            "role": "student",
            "token_exp": time.time() - 1  # Expired
        }
        
        ws_manager.active_connections[client_id] = {
            "websocket": Mock(),
            "user": expired_user,
            "last_activity": time.time()
        }
        
        # Should reject message due to expired token
        result = await ws_manager.handle_message(
            client_id,
            {"type": "ping"}
        )
        
        assert result is None
        assert ws_manager.metrics["token_expired"] > 0

class TestInputValidation:
    """Test input validation"""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        client = TestClient(app)
        
        # Attempt SQL injection
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post(
            "/api/search",
            json={"query": malicious_input}
        )
        
        # Should sanitize or reject
        assert "DROP TABLE" not in str(response.content)
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        client = TestClient(app)
        
        # Attempt XSS
        xss_payload = "<script>alert('XSS')</script>"
        
        response = client.post(
            "/api/content",
            json={"content": xss_payload}
        )
        
        # Should escape or reject
        if response.status_code == 200:
            assert "<script>" not in response.text
            assert "&lt;script&gt;" in response.text or "script" not in response.text
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        client = TestClient(app)
        
        # Attempt to upload executable
        files = {
            "file": ("malicious.exe", b"binary content", "application/x-executable")
        }
        
        response = client.post("/api/upload", files=files)
        
        # Should reject executable
        assert response.status_code in [400, 415]  # Bad request or unsupported media type

class TestRateLimiting:
    """Test rate limiting"""
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        client = TestClient(app)
        
        # Make many requests
        responses = []
        for _ in range(105):
            response = client.get("/api/health")
            responses.append(response.status_code)
        
        # Should hit rate limit
        assert 429 in responses  # Too Many Requests
    
    def test_rate_limit_per_user(self):
        """Test rate limiting is per user"""
        limiter = RateLimiter()
        
        # User 1 requests
        for _ in range(100):
            assert limiter.check_rate_limit("user1", 100, 60)
        
        # User 1 should be blocked
        assert not limiter.check_rate_limit("user1", 100, 60)
        
        # User 2 should still be allowed
        assert limiter.check_rate_limit("user2", 100, 60)

class TestCORSSecurity:
    """Test CORS configuration"""
    
    def test_cors_configuration(self):
        """Test CORS is properly configured"""
        client = TestClient(app)
        
        # Test with allowed origin
        response = client.options(
            "/api/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        
        # Test with disallowed origin
        response = client.options(
            "/api/health",
            headers={"Origin": "http://evil.com"}
        )
        
        assert response.headers.get("Access-Control-Allow-Origin") != "http://evil.com"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Run security tests
cd ToolboxAI-Roblox-Environment
pytest tests/test_security.py -v
```

## PHASE 4: SECURITY HARDENING (Final 1 hour)

### Task 4.1: Create Security Middleware and Monitoring
```bash
cat > ToolboxAI-Roblox-Environment/server/security_middleware.py << 'EOF'
"""
Security Middleware and Monitoring
Comprehensive security enforcement layer
"""

import time
import hashlib
import hmac
from typing import Optional, Callable
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize all requests"""
    
    BLOCKED_PATTERNS = [
        # SQL Injection
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)",
        # XSS
        r"(<script|javascript:|onerror=|onload=|<iframe|<object)",
        # Path Traversal
        r"(\.\./|\.\.\\|%2e%2e)",
        # Command Injection
        r"(;|\||&&|`|\$\()",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
        
        # Validate path
        if any(pattern in request.url.path for pattern in ["../", "..\\", "%2e%2e"]):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid path"}
            )
        
        # Check for malicious patterns in query params
        for param_value in request.query_params.values():
            for pattern in self.BLOCKED_PATTERNS:
                if re.search(pattern, param_value, re.IGNORECASE):
                    logger.warning(f"Blocked malicious request: {pattern} in {param_value}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request"}
                    )
        
        response = await call_next(request)
        return response

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Log all security-relevant events"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get user info from token if available
        user_id = None
        user_role = None
        
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                # Decode token (without verification for logging)
                import jwt
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
                user_role = payload.get("role")
            except:
                pass
        
        # Log request
        audit_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "user_id": user_id,
            "user_role": user_role,
            "user_agent": request.headers.get("User-Agent")
        }
        
        try:
            response = await call_next(request)
            
            # Log response
            audit_log["status_code"] = response.status_code
            audit_log["response_time"] = time.time() - start_time
            
            # Log security events
            if response.status_code == 401:
                audit_log["event"] = "authentication_failure"
            elif response.status_code == 403:
                audit_log["event"] = "authorization_failure"
            elif response.status_code == 429:
                audit_log["event"] = "rate_limit_exceeded"
            
            # Write to audit log
            logger.info(f"AUDIT: {json.dumps(audit_log)}")
            
            return response
            
        except Exception as e:
            audit_log["error"] = str(e)
            audit_log["event"] = "request_error"
            logger.error(f"AUDIT: {json.dumps(audit_log)}")
            raise

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing operations"""
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token"""
        message = f"{session_id}:{time.time()}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{message}:{signature}"
    
    def verify_csrf_token(self, token: str, session_id: str) -> bool:
        """Verify CSRF token"""
        try:
            message, signature = token.rsplit(":", 1)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Verify session
            token_session = message.split(":")[0]
            if token_session != session_id:
                return False
            
            # Check token age (1 hour)
            token_time = float(message.split(":")[1])
            if time.time() - token_time > 3600:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Skip for API endpoints (they use JWT)
        if request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Verify CSRF token for form submissions
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=403,
                content={"error": "CSRF token missing"}
            )
        
        # Get session ID (from cookie or header)
        session_id = request.cookies.get("session_id", "")
        
        if not self.verify_csrf_token(csrf_token, session_id):
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid CSRF token"}
            )
        
        return await call_next(request)

class SecurityMonitor:
    """Monitor security metrics"""
    
    def __init__(self):
        self.metrics = {
            "auth_attempts": 0,
            "auth_failures": 0,
            "rate_limit_hits": 0,
            "malicious_requests": 0,
            "api_errors": 0
        }
        self.alerts = []
    
    def record_auth_attempt(self, success: bool):
        """Record authentication attempt"""
        self.metrics["auth_attempts"] += 1
        if not success:
            self.metrics["auth_failures"] += 1
            
            # Alert on multiple failures
            if self.metrics["auth_failures"] % 10 == 0:
                self.alert(
                    "HIGH",
                    f"Multiple auth failures: {self.metrics['auth_failures']}"
                )
    
    def record_rate_limit(self):
        """Record rate limit hit"""
        self.metrics["rate_limit_hits"] += 1
        
        # Alert on excessive rate limiting
        if self.metrics["rate_limit_hits"] % 100 == 0:
            self.alert(
                "MEDIUM",
                f"High rate limit hits: {self.metrics['rate_limit_hits']}"
            )
    
    def record_malicious_request(self, details: str):
        """Record malicious request"""
        self.metrics["malicious_requests"] += 1
        self.alert("CRITICAL", f"Malicious request detected: {details}")
    
    def alert(self, severity: str, message: str):
        """Send security alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "message": message
        }
        
        self.alerts.append(alert)
        logger.warning(f"SECURITY ALERT: {severity} - {message}")
        
        # Send to monitoring service (e.g., Sentry, DataDog)
        # TODO: Implement external alerting
    
    def get_metrics(self) -> dict:
        """Get security metrics"""
        return {
            "metrics": self.metrics,
            "recent_alerts": self.alerts[-10:]  # Last 10 alerts
        }

# Global security monitor
security_monitor = SecurityMonitor()
EOF

echo "Security implementation complete!"
```

## SUCCESS CRITERIA

Before marking Terminal 4 complete:

- [ ] All critical vulnerabilities patched (0 remaining)
- [ ] All high vulnerabilities patched (0 remaining)
- [ ] JWT implementation secure with expiry
- [ ] WebSocket RBAC fully implemented
- [ ] Rate limiting active on all endpoints
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention verified
- [ ] XSS prevention implemented
- [ ] CORS properly configured
- [ ] Security headers on all responses
- [ ] Audit logging operational
- [ ] All security tests passing
- [ ] Security monitoring active

## HANDOFF TO OTHER TERMINALS

Once complete, notify:

1. **Terminal 5**: Security documentation ready
2. **Terminal 6**: Security optimizations complete
3. **Terminal 7**: Security tests ready for CI/CD
4. **Terminal 8**: Security configurations ready for production

## MONITORING DASHBOARD

Keep this running to monitor security:

```bash
# Create security monitor
cat > monitor_security.sh << 'EOF'
#!/bin/bash

while true; do
    clear
    echo "=== SECURITY MONITOR ==="
    echo "Time: $(date)"
    echo ""
    
    # Check for critical vulnerabilities
    echo "Vulnerability Scan:"
    python security_scanner.py | grep -E "(Critical|High)" | head -5
    
    # Monitor auth failures
    echo ""
    echo "Authentication:"
    grep "auth_failure" logs/*.log | tail -5
    
    # Monitor rate limiting
    echo ""
    echo "Rate Limiting:"
    grep "rate_limit" logs/*.log | tail -5
    
    # Check security headers
    echo ""
    echo "Security Headers:"
    curl -I http://127.0.0.1:8008/health 2>/dev/null | grep -E "(X-Frame|X-XSS|Strict-Transport)"
    
    sleep 5
done
EOF

chmod +x monitor_security.sh
./monitor_security.sh
```

Remember: SECURITY IS NON-NEGOTIABLE. Fix everything!