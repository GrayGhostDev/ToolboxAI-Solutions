"""
OAuth 2.1 Authorization Server Implementation
Phase 3 - Complete OAuth 2.1 with PKCE
Compliant with RFC 6749, RFC 7636, and OAuth 2.1 draft
"""

import base64
import hashlib
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import jwt
import redis

logger = logging.getLogger(__name__)


# Request/Response Models
@dataclass
class AuthorizationRequest:
    """OAuth 2.1 Authorization Request"""

    client_id: str
    redirect_uri: str
    scope: str
    state: str
    code_challenge: str
    code_challenge_method: str = "S256"
    response_type: str = "code"
    user_id: str | None = None
    nonce: str | None = None


@dataclass
class TokenRequest:
    """OAuth 2.1 Token Request"""

    grant_type: str
    code: str | None = None
    redirect_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None
    scope: str | None = None


class ResponseType(Enum):
    """OAuth 2.1 supported response types"""

    CODE = "code"  # Only authorization code flow in OAuth 2.1


class GrantType(Enum):
    """OAuth 2.1 supported grant types"""

    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"


class TokenType(Enum):
    """Token types"""

    BEARER = "Bearer"


class PKCEMethod(Enum):
    """PKCE challenge methods"""

    S256 = "S256"  # SHA256 - Only supported method in OAuth 2.1


@dataclass
class OAuth21Config:
    """OAuth 2.1 Server Configuration"""

    issuer: str = "https://auth.toolboxai.com"
    authorization_endpoint: str = "/oauth/authorize"
    token_endpoint: str = "/oauth/token"
    revocation_endpoint: str = "/oauth/revoke"
    introspection_endpoint: str = "/oauth/introspect"
    jwks_endpoint: str = "/oauth/jwks"

    # Security settings (OAuth 2.1 requirements)
    require_pkce: bool = True  # Mandatory in OAuth 2.1
    require_https: bool = True  # Mandatory in OAuth 2.1
    require_exact_redirect_uri: bool = True  # Mandatory in OAuth 2.1

    # Token lifetimes
    authorization_code_lifetime: int = 600  # 10 minutes
    access_token_lifetime: int = 3600  # 1 hour
    refresh_token_lifetime: int = 2592000  # 30 days
    refresh_token_rotation: bool = True  # OAuth 2.1 recommendation

    # Client authentication
    supported_client_auth_methods: List[str] = field(
        default_factory=lambda: [
            "client_secret_basic",
            "client_secret_post",
            "private_key_jwt",
        ]
    )

    # PKCE settings
    pkce_code_challenge_methods: List[str] = field(default_factory=lambda: ["S256"])
    pkce_required_for_public_clients: bool = True


@dataclass
class Client:
    """OAuth client representation"""

    client_id: str
    client_secret: str | None
    client_name: str
    client_type: str  # "confidential" or "public"
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    scope: str
    contacts: List[str] = field(default_factory=list)
    logo_uri: str | None = None
    client_uri: str | None = None
    policy_uri: str | None = None
    tos_uri: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class OAuth21Server:
    """OAuth 2.1 compliant authorization server"""

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        config: OAuth21Config | None = None,
    ):
        self.redis = redis_client or self._create_redis_client()
        self.config = config or OAuth21Config()

        # Require JWT secret from environment for security
        self.jwt_secret = os.getenv("OAUTH_JWT_SECRET")
        if not self.jwt_secret:
            raise RuntimeError("OAUTH_JWT_SECRET must be set in environment variables")

        self.jwt_algorithm = "RS256"  # Use RS256 for better security

    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client"""
        return redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
        )

    # ===== PKCE Implementation =====

    def generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        # RFC 7636: 43-128 characters
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

    def generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        challenge = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(challenge).decode("utf-8").rstrip("=")

    def verify_pkce(self, verifier: str, challenge: str, method: str = "S256") -> bool:
        """Verify PKCE challenge"""
        if method != "S256":
            logger.error(f"Unsupported PKCE method: {method}")
            return False

        computed_challenge = self.generate_code_challenge(verifier)
        return secrets.compare_digest(computed_challenge, challenge)

    # ===== Client Management =====

    async def register_client(self, client_data: Dict[str, Any]) -> Client:
        """Register new OAuth client (Dynamic Client Registration)"""

        # Generate client credentials
        client_id = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode("utf-8").rstrip("=")

        # Only confidential clients get a secret
        client_secret = None
        if client_data.get("client_type") == "confidential":
            client_secret = (
                base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
            )

        # Create client object
        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_data["client_name"],
            client_type=client_data.get("client_type", "public"),
            redirect_uris=client_data["redirect_uris"],
            grant_types=client_data.get("grant_types", ["authorization_code"]),
            response_types=client_data.get("response_types", ["code"]),
            scope=client_data.get("scope", "read"),
            contacts=client_data.get("contacts", []),
            logo_uri=client_data.get("logo_uri"),
            client_uri=client_data.get("client_uri"),
            policy_uri=client_data.get("policy_uri"),
            tos_uri=client_data.get("tos_uri"),
        )

        # Store client
        key = f"oauth:client:{client_id}"
        self.redis.set(
            key,
            json.dumps(
                {
                    "client_id": client.client_id,
                    "client_secret": client.client_secret,
                    "client_name": client.client_name,
                    "client_type": client.client_type,
                    "redirect_uris": client.redirect_uris,
                    "grant_types": client.grant_types,
                    "response_types": client.response_types,
                    "scope": client.scope,
                    "contacts": client.contacts,
                    "logo_uri": client.logo_uri,
                    "client_uri": client.client_uri,
                    "policy_uri": client.policy_uri,
                    "tos_uri": client.tos_uri,
                    "created_at": client.created_at.isoformat(),
                    "updated_at": client.updated_at.isoformat(),
                }
            ),
        )

        logger.info(f"Client registered: {client_id}")
        return client

    async def get_client(self, client_id: str) -> dict[str, Any] | None:
        """Retrieve client by ID - returns dict for compatibility"""
        key = f"oauth:client:{client_id}"
        client_json = self.redis.get(key)

        if not client_json:
            return None

        return json.loads(client_json)

    async def verify_client(self, client_id: str, client_secret: str | None = None) -> bool:
        """Verify client credentials"""
        client = await self.get_client(client_id)

        if not client:
            return False

        # Public clients don't have secrets
        if client.get("client_type") == "public":
            return client_secret is None

        # Confidential clients must provide secret
        stored_secret = client.get("client_secret")
        if not client_secret or not stored_secret:
            return False

        return secrets.compare_digest(stored_secret, client_secret)

    # ===== Additional Client Methods =====

    async def store_client(self, client_data: Dict[str, Any]) -> None:
        """Store client data"""
        client_id = client_data["client_id"]
        key = f"oauth:client:{client_id}"
        self.redis.set(key, json.dumps(client_data))
        logger.info(f"Client stored: {client_id}")

    async def get_user_clients(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all clients for a user"""
        # Get all client keys
        clients = []
        for key in self.redis.scan_iter(match="oauth:client:*"):
            client_json = self.redis.get(key)
            if client_json:
                client = json.loads(client_json)
                if client.get("owner_id") == user_id:
                    clients.append(client)
        return clients

    async def delete_client(self, client_id: str) -> bool:
        """Delete a client and its associated tokens"""
        # Delete client
        client_key = f"oauth:client:{client_id}"
        if self.redis.delete(client_key):
            # Delete associated tokens
            for key in self.redis.scan_iter(match=f"oauth:*:{client_id}:*"):
                self.redis.delete(key)
            logger.info(f"Client deleted: {client_id}")
            return True
        return False

    # ===== Authorization Flow =====

    async def create_authorization_request(
        self, request: AuthorizationRequest, user_id: str
    ) -> str:
        """Create authorization request (Step 1 of auth code flow)"""

        # Validate client
        client = await self.get_client(request.client_id)
        if not client:
            raise ValueError(f"Invalid client_id: {request.client_id}")

        # Validate redirect URI (exact match required in OAuth 2.1)
        redirect_uris = client.get("redirect_uris", [])
        if request.redirect_uri not in redirect_uris:
            raise ValueError(f"Invalid redirect_uri: {request.redirect_uri}")

        # Validate PKCE (required in OAuth 2.1)
        if not request.code_challenge:
            raise ValueError("code_challenge required (PKCE)")

        # OAuth 2.1 requires S256 only
        if request.code_challenge_method != "S256":
            raise ValueError("Only S256 PKCE method supported in OAuth 2.1")

        # Generate authorization code
        auth_code = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

        # Store authorization data
        auth_data = {
            "code": auth_code,
            "client_id": request.client_id,
            "redirect_uri": request.redirect_uri,
            "scope": request.scope,
            "state": request.state,
            "code_challenge": request.code_challenge,
            "code_challenge_method": request.code_challenge_method,
            "user_id": user_id,
            "nonce": request.nonce,
            "created_at": datetime.utcnow().isoformat(),
        }

        key = f"oauth:auth_code:{auth_code}"
        self.redis.setex(key, self.config.authorization_code_lifetime, json.dumps(auth_data))

        logger.info(f"Authorization code created for client {request.client_id}")

        return auth_code

    async def exchange_authorization_code(self, request: TokenRequest) -> Dict[str, Any]:
        """Exchange authorization code for tokens (Step 2 of auth code flow)"""

        if not request.code:
            raise ValueError("Authorization code required")

        # Retrieve authorization data
        key = f"oauth:auth_code:{request.code}"
        auth_json = self.redis.get(key)

        if not auth_json:
            raise ValueError("Invalid or expired authorization code")

        auth_data = json.loads(auth_json)

        # Validate client
        if auth_data["client_id"] != request.client_id:
            raise ValueError("Client mismatch")

        if not await self.verify_client(request.client_id, request.client_secret):
            raise ValueError("Client authentication failed")

        # Validate redirect URI (exact match)
        if auth_data["redirect_uri"] != request.redirect_uri:
            raise ValueError("Redirect URI mismatch")

        # Validate PKCE
        if not request.code_verifier:
            raise ValueError("PKCE code_verifier required")

        if not self.verify_pkce(
            request.code_verifier,
            auth_data["code_challenge"],
            auth_data["code_challenge_method"],
        ):
            raise ValueError("Invalid PKCE verifier")

        # Delete used authorization code (one-time use)
        self.redis.delete(key)

        # Generate tokens
        access_token = await self._generate_access_token(
            user_id=auth_data["user_id"],
            client_id=request.client_id,
            scope=auth_data["scope"],
            nonce=auth_data.get("nonce"),
        )

        refresh_token = await self._generate_refresh_token(
            user_id=auth_data["user_id"],
            client_id=request.client_id,
            scope=auth_data["scope"],
        )

        # ID token for OpenID Connect
        id_token = None
        if "openid" in auth_data["scope"]:
            id_token = await self._generate_id_token(
                user_id=auth_data["user_id"],
                client_id=request.client_id,
                nonce=auth_data.get("nonce"),
            )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.config.access_token_lifetime,
            "refresh_token": refresh_token,
            "scope": auth_data["scope"],
            "id_token": id_token,
        }

    # ===== Token Management =====

    async def _generate_access_token(
        self, user_id: str, client_id: str, scope: str, nonce: str | None = None
    ) -> str:
        """Generate JWT access token"""

        jti = secrets.token_urlsafe(16)
        now = datetime.utcnow()

        payload = {
            "iss": self.config.issuer,
            "sub": user_id,
            "aud": client_id,
            "exp": (now + timedelta(seconds=self.config.access_token_lifetime)).timestamp(),
            "iat": now.timestamp(),
            "nbf": now.timestamp(),
            "jti": jti,
            "scope": scope,
            "token_type": "access_token",
        }

        if nonce:
            payload["nonce"] = nonce

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        # Store token metadata for revocation
        key = f"oauth:access_token:{jti}"
        self.redis.setex(
            key,
            self.config.access_token_lifetime,
            json.dumps(
                {
                    "user_id": user_id,
                    "client_id": client_id,
                    "scope": scope,
                    "created_at": now.isoformat(),
                }
            ),
        )

        return token

    async def _generate_refresh_token(self, user_id: str, client_id: str, scope: str) -> str:
        """Generate refresh token"""

        token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

        # Store refresh token
        key = f"oauth:refresh_token:{token}"
        self.redis.setex(
            key,
            self.config.refresh_token_lifetime,
            json.dumps(
                {
                    "user_id": user_id,
                    "client_id": client_id,
                    "scope": scope,
                    "created_at": datetime.utcnow().isoformat(),
                }
            ),
        )

        return token

    async def _generate_id_token(
        self, user_id: str, client_id: str, nonce: str | None = None
    ) -> str:
        """Generate OpenID Connect ID token"""

        now = datetime.utcnow()

        payload = {
            "iss": self.config.issuer,
            "sub": user_id,
            "aud": client_id,
            "exp": (now + timedelta(seconds=self.config.access_token_lifetime)).timestamp(),
            "iat": now.timestamp(),
            "auth_time": now.timestamp(),
        }

        if nonce:
            payload["nonce"] = nonce

        # Add user claims (simplified)
        payload.update({"email": f"{user_id}@toolboxai.com", "email_verified": True})

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def refresh_access_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str | None = None,
        scope: str | None = None,
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token"""

        # Verify client
        if not await self.verify_client(client_id, client_secret):
            raise ValueError("Client authentication failed")

        # Retrieve refresh token data
        key = f"oauth:refresh_token:{refresh_token}"
        token_json = self.redis.get(key)

        if not token_json:
            raise ValueError("Invalid or expired refresh token")

        token_data = json.loads(token_json)

        # Validate client match
        if token_data["client_id"] != client_id:
            raise ValueError("Client mismatch")

        # Validate scope (can't increase scope)
        requested_scope = scope or token_data["scope"]
        if not self._is_scope_subset(requested_scope, token_data["scope"]):
            raise ValueError("Invalid scope")

        # Rotate refresh token if configured
        if self.config.refresh_token_rotation:
            # Delete old refresh token
            self.redis.delete(key)

            # Generate new refresh token
            new_refresh_token = await self._generate_refresh_token(
                user_id=token_data["user_id"],
                client_id=client_id,
                scope=requested_scope,
            )
        else:
            new_refresh_token = refresh_token

        # Generate new access token
        access_token = await self._generate_access_token(
            user_id=token_data["user_id"], client_id=client_id, scope=requested_scope
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.config.access_token_lifetime,
            "refresh_token": new_refresh_token,
            "scope": requested_scope,
        }

    # ===== Token Introspection & Revocation =====

    async def introspect_token(
        self, token: str, token_type_hint: str | None = None
    ) -> Dict[str, Any]:
        """Token introspection (RFC 7662)"""

        try:
            # Try as JWT access token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Check if token is revoked
            jti = payload.get("jti")
            if jti:
                key = f"oauth:revoked:{jti}"
                if self.redis.get(key):
                    return {"active": False}

            # Token is active
            return {
                "active": True,
                "scope": payload.get("scope"),
                "client_id": payload.get("aud"),
                "username": payload.get("sub"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "nbf": payload.get("nbf"),
                "sub": payload.get("sub"),
                "aud": payload.get("aud"),
                "iss": payload.get("iss"),
                "jti": payload.get("jti"),
            }

        except jwt.ExpiredSignatureError:
            return {"active": False}
        except jwt.InvalidTokenError:
            # Try as refresh token
            key = f"oauth:refresh_token:{token}"
            token_data = self.redis.get(key)

            if token_data:
                data = json.loads(token_data)
                return {
                    "active": True,
                    "scope": data.get("scope"),
                    "client_id": data.get("client_id"),
                    "username": data.get("user_id"),
                    "token_type": "refresh_token",
                }

            return {"active": False}

    async def revoke_token(
        self,
        token: str,
        token_type_hint: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> bool:
        """Token revocation (RFC 7009)"""

        # Verify client if provided
        if client_id:
            if not await self.verify_client(client_id, client_secret):
                return False

        # Try to revoke as refresh token
        refresh_key = f"oauth:refresh_token:{token}"
        if self.redis.delete(refresh_key):
            logger.info(f"Refresh token revoked: {token[:8]}...")
            return True

        # Try to revoke as access token
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Add to revocation list
            jti = payload.get("jti")
            if jti:
                exp = payload.get("exp", 0)
                ttl = int(exp - time.time())

                if ttl > 0:
                    key = f"oauth:revoked:{jti}"
                    self.redis.setex(key, ttl, "1")
                    logger.info(f"Access token revoked: JTI {jti}")
                    return True

        except jwt.InvalidTokenError:
            pass

        return False

    # ===== Utility Methods =====

    def _is_scope_subset(self, requested: str, granted: str) -> bool:
        """Check if requested scope is subset of granted scope"""
        requested_scopes = set(requested.split())
        granted_scopes = set(granted.split())
        return requested_scopes.issubset(granted_scopes)

    async def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set (for token verification)"""
        # In production, use proper key management
        return {
            "keys": [
                {
                    "kty": "oct",
                    "kid": "default",
                    "use": "sig",
                    "alg": self.jwt_algorithm,
                }
            ]
        }


# ===== Singleton =====

_oauth_server: OAuth21Server | None = None


def get_oauth_server() -> OAuth21Server:
    """Get or create OAuth server singleton"""
    global _oauth_server
    if _oauth_server is None:
        _oauth_server = OAuth21Server()
    return _oauth_server
