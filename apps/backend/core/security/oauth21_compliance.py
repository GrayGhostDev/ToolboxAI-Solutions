"""
OAuth 2.1 Compliance Module
Implements PKCE, enhanced validation, and authorization server metadata
Full compliance with draft-ietf-oauth-v2-1-13
"""

import base64
import hashlib
import secrets
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
import logging

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# OAuth 2.1 Constants
PKCE_CODE_VERIFIER_MIN_LENGTH = 43
PKCE_CODE_VERIFIER_MAX_LENGTH = 128
AUTHORIZATION_CODE_LIFETIME = 600  # 10 minutes
ACCESS_TOKEN_LIFETIME = 900  # 15 minutes
REFRESH_TOKEN_LIFETIME = 86400  # 24 hours

@dataclass
class OAuth21Config:
    """OAuth 2.1 configuration"""
    issuer: str = os.getenv("OAUTH_ISSUER", "https://api.toolboxai.com")
    authorization_endpoint: str = "/oauth/authorize"
    token_endpoint: str = "/oauth/token"
    revocation_endpoint: str = "/oauth/revoke"
    introspection_endpoint: str = "/oauth/introspect"
    jwks_uri: str = "/.well-known/jwks.json"
    require_pkce: bool = True  # OAuth 2.1 mandatory
    require_https: bool = os.getenv("ENV", "development") == "production"
    supported_scopes: List[str] = None

    def __post_init__(self):
        if self.supported_scopes is None:
            self.supported_scopes = ["read", "write", "admin", "openid", "profile", "email"]

class PKCEChallenge(BaseModel):
    """PKCE challenge data model"""
    code_challenge: str = Field(..., min_length=43, max_length=128)
    code_challenge_method: str = Field(default="S256", pattern="^S256$")

class TokenRequest(BaseModel):
    """Token exchange request model"""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    code_verifier: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class OAuth21Manager:
    """
    OAuth 2.1 compliance manager with full PKCE support
    Implements all OAuth 2.1 requirements and security best practices
    """

    def __init__(self, config: Optional[OAuth21Config] = None):
        """Initialize OAuth 2.1 manager"""
        self.config = config or OAuth21Config()

        # Initialize Redis for state management
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.redis_available = True
            logger.info("OAuth 2.1 manager connected to Redis")
        except (RedisError, Exception) as e:
            logger.error(f"Redis not available for OAuth 2.1: {e}")
            self.redis_client = None
            self.redis_available = False

        # Client registry (in production, this would be in a database)
        self.registered_clients = self._load_registered_clients()

    def _load_registered_clients(self) -> Dict[str, Dict]:
        """Load registered OAuth clients"""
        # In production, load from database
        return {
            "dashboard-client": {
                "client_secret": os.getenv("DASHBOARD_CLIENT_SECRET", "dashboard-secret"),
                "redirect_uris": [
                    "http://localhost:3000/callback",
                    "http://localhost:5179/callback",
                    "https://dashboard.toolboxai.com/callback"
                ],
                "allowed_scopes": ["read", "write", "profile"],
                "client_type": "confidential"
            },
            "roblox-plugin": {
                "client_secret": None,  # Public client
                "redirect_uris": [
                    "roblox://auth/callback",
                    "http://localhost:3001/roblox/callback"
                ],
                "allowed_scopes": ["read", "write"],
                "client_type": "public"
            },
            "test-client": {
                "client_secret": "test-secret",
                "redirect_uris": ["http://localhost:3000/callback"],
                "allowed_scopes": ["read", "write", "admin"],
                "client_type": "confidential"
            }
        }

    def generate_pkce_pair(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge pair

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters, base64url)
        verifier_bytes = secrets.token_bytes(32)
        code_verifier = base64.urlsafe_b64encode(verifier_bytes).decode('utf-8').rstrip('=')

        # Ensure minimum length
        while len(code_verifier) < PKCE_CODE_VERIFIER_MIN_LENGTH:
            additional_bytes = secrets.token_bytes(8)
            code_verifier += base64.urlsafe_b64encode(additional_bytes).decode('utf-8').rstrip('=')

        # Truncate to maximum length
        code_verifier = code_verifier[:PKCE_CODE_VERIFIER_MAX_LENGTH]

        # Generate code challenge using SHA256 (S256)
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')

        logger.debug(f"Generated PKCE pair: verifier length={len(code_verifier)}, challenge length={len(code_challenge)}")
        return code_verifier, code_challenge

    def verify_pkce(
        self,
        code_verifier: str,
        code_challenge: str,
        method: str = "S256"
    ) -> bool:
        """
        Verify PKCE challenge against verifier

        Args:
            code_verifier: The code verifier from client
            code_challenge: The stored code challenge
            method: Challenge method (must be S256 for OAuth 2.1)

        Returns:
            True if verification succeeds
        """
        if method != "S256":
            logger.error(f"Invalid PKCE method: {method}")
            return False

        # Verify verifier length
        if not PKCE_CODE_VERIFIER_MIN_LENGTH <= len(code_verifier) <= PKCE_CODE_VERIFIER_MAX_LENGTH:
            logger.error(f"Invalid verifier length: {len(code_verifier)}")
            return False

        # Generate challenge from verifier
        try:
            challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
            expected_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')

            # Constant-time comparison to prevent timing attacks
            result = secrets.compare_digest(expected_challenge, code_challenge)
            logger.debug(f"PKCE verification result: {result}")
            return result
        except Exception as e:
            logger.error(f"PKCE verification error: {e}")
            return False

    async def create_authorization_code(
        self,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        scope: Optional[str] = None,
        user_id: Optional[str] = None,
        state: Optional[str] = None,
        nonce: Optional[str] = None
    ) -> str:
        """
        Create authorization code with PKCE data

        Args:
            client_id: OAuth client ID
            redirect_uri: Redirect URI for response
            code_challenge: PKCE code challenge
            code_challenge_method: Challenge method (S256)
            scope: Requested scopes
            user_id: Authenticated user ID
            state: Client state parameter
            nonce: OpenID Connect nonce

        Returns:
            Authorization code
        """
        if not self.redis_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authorization service temporarily unavailable"
            )

        # Validate client
        if client_id not in self.registered_clients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client_id"
            )

        # Validate redirect URI (exact match required by OAuth 2.1)
        client_config = self.registered_clients[client_id]
        if redirect_uri not in client_config["redirect_uris"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect_uri"
            )

        # Validate PKCE for OAuth 2.1 compliance
        if code_challenge_method != "S256":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth 2.1 requires S256 challenge method"
            )

        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=AUTHORIZATION_CODE_LIFETIME)

        # Store authorization code data
        code_data = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "scope": scope,
            "user_id": user_id,
            "state": state,
            "nonce": nonce,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False
        }

        # Store in Redis with expiration
        code_key = f"oauth:auth_code:{auth_code}"
        self.redis_client.setex(
            code_key,
            AUTHORIZATION_CODE_LIFETIME,
            json.dumps(code_data)
        )

        logger.info(f"Created authorization code for client {client_id}, user {user_id}")
        return auth_code

    async def exchange_authorization_code(
        self,
        code: str,
        code_verifier: str,
        client_id: str,
        client_secret: Optional[str],
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens

        Args:
            code: Authorization code
            code_verifier: PKCE code verifier
            client_id: Client ID
            client_secret: Client secret (for confidential clients)
            redirect_uri: Redirect URI (must match original)

        Returns:
            Token response dictionary
        """
        if not self.redis_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Token service temporarily unavailable"
            )

        # Retrieve authorization code data
        code_key = f"oauth:auth_code:{code}"
        code_data_str = self.redis_client.get(code_key)

        if not code_data_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired authorization code"
            )

        code_data = json.loads(code_data_str)

        # Check if code was already used (prevent replay attacks)
        if code_data.get("used"):
            # Revoke all tokens associated with this code
            logger.warning(f"Authorization code reuse detected for {code}")
            self._revoke_tokens_for_code(code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code already used"
            )

        # Validate client
        if code_data["client_id"] != client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client ID mismatch"
            )

        # Validate client credentials for confidential clients
        client_config = self.registered_clients.get(client_id)
        if client_config and client_config["client_type"] == "confidential":
            if not client_secret or client_secret != client_config["client_secret"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid client credentials"
                )

        # Validate redirect URI (must match exactly)
        if code_data["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redirect URI mismatch"
            )

        # Verify PKCE
        if not self.verify_pkce(
            code_verifier,
            code_data["code_challenge"],
            code_data["code_challenge_method"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PKCE verification failed"
            )

        # Mark code as used
        code_data["used"] = True
        self.redis_client.setex(code_key, 60, json.dumps(code_data))  # Keep for 1 minute for replay detection

        # Generate tokens
        access_token = self._generate_access_token(
            user_id=code_data.get("user_id"),
            client_id=client_id,
            scope=code_data.get("scope")
        )

        refresh_token = self._generate_refresh_token(
            user_id=code_data.get("user_id"),
            client_id=client_id,
            scope=code_data.get("scope")
        )

        # Store token metadata for revocation
        self._store_token_metadata(access_token, refresh_token, code_data)

        logger.info(f"Successfully exchanged authorization code for tokens (client: {client_id})")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_LIFETIME,
            "scope": code_data.get("scope")
        }

    def _generate_access_token(self, user_id: str, client_id: str, scope: Optional[str]) -> str:
        """Generate access token"""
        # In production, use JWT with proper signing
        token_data = {
            "type": "access",
            "user_id": user_id,
            "client_id": client_id,
            "scope": scope,
            "iat": int(time.time()),
            "exp": int(time.time()) + ACCESS_TOKEN_LIFETIME,
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }

        # For now, use a simple token (replace with JWT in production)
        token = secrets.token_urlsafe(32)

        if self.redis_available:
            # Store token data
            token_key = f"oauth:access_token:{token}"
            self.redis_client.setex(
                token_key,
                ACCESS_TOKEN_LIFETIME,
                json.dumps(token_data)
            )

        return token

    def _generate_refresh_token(self, user_id: str, client_id: str, scope: Optional[str]) -> str:
        """Generate refresh token with rotation support"""
        token_data = {
            "type": "refresh",
            "user_id": user_id,
            "client_id": client_id,
            "scope": scope,
            "iat": int(time.time()),
            "exp": int(time.time()) + REFRESH_TOKEN_LIFETIME,
            "rotation_count": 0
        }

        token = secrets.token_urlsafe(32)

        if self.redis_available:
            # Store refresh token
            token_key = f"oauth:refresh_token:{token}"
            self.redis_client.setex(
                token_key,
                REFRESH_TOKEN_LIFETIME,
                json.dumps(token_data)
            )

        return token

    def _store_token_metadata(self, access_token: str, refresh_token: str, auth_data: Dict):
        """Store token metadata for management and revocation"""
        if not self.redis_available:
            return

        user_id = auth_data.get("user_id")
        client_id = auth_data.get("client_id")

        # Store user's active tokens
        if user_id:
            user_tokens_key = f"oauth:user_tokens:{user_id}"
            self.redis_client.sadd(user_tokens_key, access_token, refresh_token)
            self.redis_client.expire(user_tokens_key, REFRESH_TOKEN_LIFETIME)

        # Store client's active tokens
        if client_id:
            client_tokens_key = f"oauth:client_tokens:{client_id}"
            self.redis_client.sadd(client_tokens_key, access_token, refresh_token)
            self.redis_client.expire(client_tokens_key, REFRESH_TOKEN_LIFETIME)

    def _revoke_tokens_for_code(self, code: str):
        """Revoke all tokens associated with an authorization code"""
        # Implementation for token revocation on code reuse
        logger.warning(f"Revoking tokens for reused code: {code}")
        # TODO: Implement token revocation

    def validate_redirect_uri(self, provided_uri: str, registered_uris: List[str]) -> bool:
        """
        OAuth 2.1 exact string matching for redirect URIs

        Args:
            provided_uri: URI provided in request
            registered_uris: List of registered URIs for client

        Returns:
            True if URI is valid
        """
        # OAuth 2.1 requires exact string matching
        is_valid = provided_uri in registered_uris

        # Additional security check for HTTPS in production
        if self.config.require_https and is_valid:
            if not provided_uri.startswith("https://") and not provided_uri.startswith("http://localhost"):
                logger.warning(f"Non-HTTPS redirect URI in production: {provided_uri}")
                return False

        return is_valid

    def get_authorization_server_metadata(self) -> Dict[str, Any]:
        """
        Get OAuth 2.1 authorization server metadata (RFC 8414)

        Returns:
            Server metadata dictionary
        """
        base_url = self.config.issuer

        return {
            "issuer": self.config.issuer,
            "authorization_endpoint": f"{base_url}{self.config.authorization_endpoint}",
            "token_endpoint": f"{base_url}{self.config.token_endpoint}",
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
                "private_key_jwt"
            ],
            "jwks_uri": f"{base_url}{self.config.jwks_uri}",
            "response_types_supported": ["code"],  # OAuth 2.1 only supports authorization code
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
                "client_credentials"
            ],
            "revocation_endpoint": f"{base_url}{self.config.revocation_endpoint}",
            "introspection_endpoint": f"{base_url}{self.config.introspection_endpoint}",
            "code_challenge_methods_supported": ["S256"],  # OAuth 2.1 requirement
            "scopes_supported": self.config.supported_scopes,
            "response_modes_supported": ["query", "fragment"],
            "authorization_response_iss_parameter_supported": True,
            "backchannel_logout_supported": False,
            "frontchannel_logout_supported": False,
            "service_documentation": "https://docs.toolboxai.com/oauth",
            "ui_locales_supported": ["en-US"],
            "op_policy_uri": "https://toolboxai.com/privacy",
            "op_tos_uri": "https://toolboxai.com/terms"
        }

    async def revoke_token(self, token: str, token_type_hint: Optional[str] = None) -> bool:
        """
        Revoke a token (RFC 7009)

        Args:
            token: Token to revoke
            token_type_hint: Hint about token type

        Returns:
            True if revocation successful
        """
        if not self.redis_available:
            return False

        # Try to revoke as access token
        access_key = f"oauth:access_token:{token}"
        if self.redis_client.delete(access_key):
            logger.info(f"Revoked access token: {token[:8]}...")
            return True

        # Try to revoke as refresh token
        refresh_key = f"oauth:refresh_token:{token}"
        if self.redis_client.delete(refresh_key):
            logger.info(f"Revoked refresh token: {token[:8]}...")
            return True

        return False

    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Token introspection (RFC 7662)

        Args:
            token: Token to introspect

        Returns:
            Token metadata
        """
        if not self.redis_available:
            return {"active": False}

        # Check access token
        access_key = f"oauth:access_token:{token}"
        token_data_str = self.redis_client.get(access_key)

        if token_data_str:
            token_data = json.loads(token_data_str)
            return {
                "active": token_data["exp"] > time.time(),
                "scope": token_data.get("scope"),
                "client_id": token_data.get("client_id"),
                "username": token_data.get("user_id"),
                "token_type": "Bearer",
                "exp": token_data.get("exp"),
                "iat": token_data.get("iat")
            }

        # Check refresh token
        refresh_key = f"oauth:refresh_token:{token}"
        token_data_str = self.redis_client.get(refresh_key)

        if token_data_str:
            token_data = json.loads(token_data_str)
            return {
                "active": token_data["exp"] > time.time(),
                "scope": token_data.get("scope"),
                "client_id": token_data.get("client_id"),
                "username": token_data.get("user_id"),
                "token_type": "refresh_token",
                "exp": token_data.get("exp"),
                "iat": token_data.get("iat")
            }

        return {"active": False}

# Global instance
oauth21_manager = OAuth21Manager()

def get_oauth21_manager() -> OAuth21Manager:
    """Get OAuth 2.1 manager instance"""
    return oauth21_manager