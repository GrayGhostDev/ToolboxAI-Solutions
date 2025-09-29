"""
JWT Security Module

Provides secure JWT token generation, validation, and secret management
for the ToolboxAI authentication system.
"""

from .jwt_secret_generator import JWTSecretGenerator, generate_secure_jwt_secret
from .jwt_manager import JWTSecurityManager, init_jwt_security, get_secure_jwt_secret

# Alias for compatibility
JWTManager = JWTSecurityManager

__all__ = [
    "JWTSecretGenerator",
    "JWTSecurityManager",
    "JWTManager",  # Alias
    "generate_secure_jwt_secret",
    "get_secure_jwt_secret",
    "init_jwt_security",
]
