"""Security utilities for plugin validation and authentication"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class PluginSecurity:
    """Plugin security and validation manager"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.rate_limits: Dict[str, List[float]] = {}
        self.plugin_tokens: Dict[str, str] = {}
        self.plugin_permissions: Dict[str, Set[str]] = {}
    
    def generate_token(self, plugin_id: str) -> str:
        """Generate secure token for plugin"""
        timestamp = str(int(time.time()))
        message = f"{plugin_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        token = f"{message}:{signature}"
        self.plugin_tokens[plugin_id] = token
        return token
    
    def validate_token(self, plugin_id: str, token: str) -> bool:
        """Validate plugin token"""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            received_plugin_id, timestamp, signature = parts
            if received_plugin_id != plugin_id:
                return False
            
            # Check token age (24 hours max)
            token_age = time.time() - int(timestamp)
            if token_age > 86400:
                return False
            
            # Verify signature
            message = f"{plugin_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error("Token validation failed: %s", e)
            return False
    
    def check_rate_limit(self, plugin_id: str, max_requests: int = 60, 
                        window_seconds: int = 60) -> bool:
        """Check if plugin is within rate limits"""
        now = time.time()
        
        if plugin_id not in self.rate_limits:
            self.rate_limits[plugin_id] = []
        
        # Clean old requests
        self.rate_limits[plugin_id] = [
            req_time for req_time in self.rate_limits[plugin_id]
            if now - req_time < window_seconds
        ]
        
        # Check limit
        if len(self.rate_limits[plugin_id]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limits[plugin_id].append(now)
        return True
    
    def set_permissions(self, plugin_id: str, permissions: List[str]) -> None:
        """Set plugin permissions"""
        self.plugin_permissions[plugin_id] = set(permissions)
    
    def check_permission(self, plugin_id: str, permission: str) -> bool:
        """Check if plugin has permission"""
        return permission in self.plugin_permissions.get(plugin_id, set())
    
    def validate_plugin_data(self, plugin_data: Dict) -> Dict[str, str]:
        """Validate plugin registration data"""
        errors = {}
        
        if not plugin_data.get('studio_id'):
            errors['studio_id'] = 'Studio ID is required'
        
        if not isinstance(plugin_data.get('port'), int):
            errors['port'] = 'Port must be an integer'
        elif not (1024 <= plugin_data['port'] <= 65535):
            errors['port'] = 'Port must be between 1024 and 65535'
        
        version = plugin_data.get('version', '')
        if not version or len(version) > 20:
            errors['version'] = 'Version must be 1-20 characters'
        
        return errors