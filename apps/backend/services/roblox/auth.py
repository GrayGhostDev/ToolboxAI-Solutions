"""
Roblox OAuth2 Authentication Service
Implements 2025 Roblox OAuth2 standards with PKCE flow
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel, Field

from apps.backend.core.config import settings

logger = logging.getLogger(__name__)


class OAuth2Config(BaseModel):
    """Roblox OAuth2 configuration for 2025 standards"""

    client_id: str = Field(default="", description="Roblox OAuth2 client ID")
    client_secret: str = Field(default="", description="Roblox OAuth2 client secret")
    redirect_uri: str = Field(default="http://localhost:8008/api/v1/roblox/oauth/callback")
    authorization_endpoint: str = Field(default="https://authorize.roblox.com/v1/authorize")
    token_endpoint: str = Field(default="https://apis.roblox.com/oauth/v1/token")
    userinfo_endpoint: str = Field(default="https://apis.roblox.com/oauth/v1/userinfo")
    scopes: list[str] = Field(
        default_factory=lambda: [
            "openid",
            "profile",
            "asset:read",
            "asset:write",
            "universe-messaging-service:publish",
            "data-store:read",
            "data-store:write",
        ]
    )


class TokenResponse(BaseModel):
    """OAuth2 token response model"""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


class UserInfo(BaseModel):
    """Roblox user information from OAuth2"""

    sub: str  # User ID
    name: Optional[str] = None
    nickname: Optional[str] = None
    preferred_username: Optional[str] = None
    created_at: Optional[int] = None
    profile: Optional[str] = None
    picture: Optional[str] = None


class RobloxOAuth2Service:
    """
    Roblox OAuth2 authentication service implementing 2025 standards
    with PKCE (Proof Key for Code Exchange) for enhanced security
    """

    def __init__(self):
        self.config = OAuth2Config(
            client_id=getattr(settings, "ROBLOX_CLIENT_ID", ""),
            client_secret=getattr(settings, "ROBLOX_CLIENT_SECRET", ""),
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self._state_storage: Dict[str, Dict[str, Any]] = {}  # In production, use Redis
        self._token_storage: Dict[str, TokenResponse] = {}  # In production, use secure storage

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge for OAuth2 flow

        Returns:
            tuple: (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = (
            base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        )

        # Generate code challenge using SHA256
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode("utf-8")
            .rstrip("=")
        )

        return code_verifier, code_challenge

    def generate_authorization_url(
        self, user_id: str, additional_scopes: Optional[list[str]] = None
    ) -> Dict[str, str]:
        """
        Generate OAuth2 authorization URL with PKCE

        Args:
            user_id: Internal user ID for state tracking
            additional_scopes: Additional scopes beyond defaults

        Returns:
            Dict containing authorization URL and state
        """
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Generate PKCE pair
        code_verifier, code_challenge = self._generate_pkce_pair()

        # Combine scopes
        scopes = self.config.scopes.copy()
        if additional_scopes:
            scopes.extend(additional_scopes)

        # Store state and PKCE verifier for later verification
        self._state_storage[state] = {
            "user_id": user_id,
            "code_verifier": code_verifier,
            "created_at": datetime.utcnow().isoformat(),
            "scopes": scopes,
        }

        # Build authorization URL
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "prompt": "consent",  # Always show consent screen
            "access_type": "offline",  # Request refresh token
        }

        auth_url = f"{self.config.authorization_endpoint}?{urlencode(params)}"

        logger.info(f"Generated authorization URL for user {user_id}")

        return {
            "authorization_url": auth_url,
            "state": state,
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        }

    async def exchange_code_for_token(self, code: str, state: str) -> TokenResponse:
        """
        Exchange authorization code for access token using PKCE

        Args:
            code: Authorization code from Roblox
            state: State parameter for verification

        Returns:
            TokenResponse with access token and refresh token
        """
        # Verify state
        if state not in self._state_storage:
            raise ValueError("Invalid state parameter - possible CSRF attack")

        state_data = self._state_storage.pop(state)

        # Check state expiration (10 minutes)
        created_at = datetime.fromisoformat(state_data["created_at"])
        if (datetime.utcnow() - created_at) > timedelta(minutes=10):
            raise ValueError("State expired - authorization took too long")

        # Prepare token exchange request
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code_verifier": state_data["code_verifier"],  # PKCE verifier
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                self.config.token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    logger.error(f"Token exchange failed: {error_data}")
                    raise ValueError(f"Token exchange failed: {response.status}")

                token_json = await response.json()
                token_response = TokenResponse(**token_json)

                # Store token securely (encrypted in production)
                user_id = state_data["user_id"]
                self._token_storage[user_id] = token_response

                logger.info(f"Successfully exchanged code for token for user {user_id}")

                return token_response

        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise

    async def refresh_access_token(self, user_id: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            user_id: Internal user ID

        Returns:
            New TokenResponse with refreshed access token
        """
        if user_id not in self._token_storage:
            raise ValueError(f"No token found for user {user_id}")

        current_token = self._token_storage[user_id]

        if not current_token.refresh_token:
            raise ValueError("No refresh token available")

        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": current_token.refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                self.config.token_endpoint,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    logger.error(f"Token refresh failed: {error_data}")
                    raise ValueError(f"Token refresh failed: {response.status}")

                token_json = await response.json()
                new_token = TokenResponse(**token_json)

                # Update stored token
                self._token_storage[user_id] = new_token

                logger.info(f"Successfully refreshed token for user {user_id}")

                return new_token

        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise

    async def get_user_info(self, access_token: str) -> UserInfo:
        """
        Get user information from Roblox using access token

        Args:
            access_token: Valid OAuth2 access token

        Returns:
            UserInfo with Roblox user details
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                self.config.userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    logger.error(f"Failed to get user info: {error_data}")
                    raise ValueError(f"Failed to get user info: {response.status}")

                user_json = await response.json()
                user_info = UserInfo(**user_json)

                logger.info(f"Successfully retrieved user info for {user_info.sub}")

                return user_info

        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise

    async def revoke_token(self, user_id: str) -> bool:
        """
        Revoke user's access and refresh tokens

        Args:
            user_id: Internal user ID

        Returns:
            True if revocation successful
        """
        if user_id not in self._token_storage:
            return True  # Already revoked

        token = self._token_storage[user_id]

        # Revoke access token
        revoke_data = {
            "token": token.access_token,
            "token_type_hint": "access_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Revoke access token
            async with self.session.post(
                f"{self.config.token_endpoint}/revoke",
                data=revoke_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    logger.warning(f"Access token revocation returned {response.status}")

            # Revoke refresh token if present
            if token.refresh_token:
                revoke_data["token"] = token.refresh_token
                revoke_data["token_type_hint"] = "refresh_token"

                async with self.session.post(
                    f"{self.config.token_endpoint}/revoke",
                    data=revoke_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Refresh token revocation returned {response.status}")

            # Remove from storage
            del self._token_storage[user_id]

            logger.info(f"Successfully revoked tokens for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False

    def get_stored_token(self, user_id: str) -> Optional[TokenResponse]:
        """
        Get stored token for user (if exists)

        Args:
            user_id: Internal user ID

        Returns:
            TokenResponse if exists, None otherwise
        """
        return self._token_storage.get(user_id)

    async def validate_token(self, access_token: str) -> bool:
        """
        Validate if access token is still valid

        Args:
            access_token: Access token to validate

        Returns:
            True if token is valid
        """
        try:
            # Try to get user info as validation
            await self.get_user_info(access_token)
            return True
        except Exception:
            return False


# Global instance
roblox_auth_service = RobloxOAuth2Service()
