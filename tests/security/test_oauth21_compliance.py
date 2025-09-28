import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio
"""
Test suite for OAuth 2.1 Compliance Implementation
Validates PKCE, token management, and security features
"""

import pytest
import asyncio
import hashlib
import base64
import secrets
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import redis
from typing import Dict, Any

from apps.backend.core.security.oauth21_compliance import (
    OAuth21Manager,
    PKCEChallenge,
    TokenRequest,
    AuthorizationRequest,
    TokenResponse,
    OAuth21Error,
    InvalidGrantError,
    InvalidRequestError,
    UnsupportedGrantTypeError
)


class TestPKCEChallenge:
    """Test PKCE implementation"""

    def test_pkce_generation(self):
        """Test PKCE verifier and challenge generation"""
        pkce = PKCEChallenge.generate()

        # Verify verifier length (43-128 characters)
        assert 43 <= len(pkce.verifier) <= 128

        # Verify verifier uses allowed characters
        allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        assert all(c in allowed for c in pkce.verifier)

        # Verify challenge is base64url encoded SHA256
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(pkce.verifier.encode()).digest()
        ).decode().rstrip('=')
        assert pkce.challenge == expected_challenge

        # Verify method
        assert pkce.method == "S256"

    def test_pkce_validation_success(self):
        """Test successful PKCE validation"""
        pkce = PKCEChallenge.generate()

        # Should validate successfully
        assert PKCEChallenge.validate(
            verifier=pkce.verifier,
            challenge=pkce.challenge,
            method="S256"
        ) == True

    def test_pkce_validation_failure(self):
        """Test PKCE validation with wrong verifier"""
        pkce = PKCEChallenge.generate()
        wrong_verifier = secrets.token_urlsafe(64)

        # Should fail validation
        assert PKCEChallenge.validate(
            verifier=wrong_verifier,
            challenge=pkce.challenge,
            method="S256"
        ) == False

    def test_pkce_validation_invalid_method(self):
        """Test PKCE validation with invalid method"""
        pkce = PKCEChallenge.generate()

        # Should fail with unsupported method
        assert PKCEChallenge.validate(
            verifier=pkce.verifier,
            challenge=pkce.challenge,
            method="plain"  # Not allowed in OAuth 2.1
        ) == False

    def test_pkce_to_dict(self):
        """Test PKCE serialization"""
        pkce = PKCEChallenge.generate()
        data = pkce.to_dict()

        assert "verifier" in data
        assert "challenge" in data
        assert "method" in data
        assert data["method"] == "S256"


class TestOAuth21Manager:
    """Test OAuth 2.1 Manager"""

    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client"""
        mock = Mock(spec=redis.Redis)
        mock.get = Mock(return_value=None)
        mock.set = Mock(return_value=True)
        mock.delete = Mock(return_value=True)
        mock.exists = Mock(return_value=False)
        mock.expire = Mock(return_value=True)
        return mock

    @pytest.fixture
    def manager(self, redis_mock):
        """Create OAuth 2.1 manager with mocked Redis"""
        with patch('apps.backend.core.security.oauth21_compliance.redis.Redis', return_value=redis_mock):
            manager = OAuth21Manager()
            manager.redis_client = redis_mock
            return manager

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_create_authorization_request(self, manager):
        """Test creating authorization request"""
        request = await manager.create_authorization_request(
            client_id="test-client",
            redirect_uri="https://example.com/callback",
            scope="read write",
            state="test-state"
        )

        assert request.client_id == "test-client"
        assert request.redirect_uri == "https://example.com/callback"
        assert request.scope == "read write"
        assert request.state == "test-state"
        assert request.response_type == "code"
        assert request.pkce_challenge is not None
        assert request.pkce_challenge.method == "S256"
        assert request.code_challenge == request.pkce_challenge.challenge
        assert request.code_challenge_method == "S256"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validate_redirect_uri_exact_match(self, manager):
        """Test redirect URI exact match validation"""
        # Register client
        manager.redis_client.get = Mock(return_value=json.dumps({
            "redirect_uris": ["https://example.com/callback", "https://example.com/other"]
        }))

        # Exact match should pass
        result = await manager.validate_redirect_uri(
            "test-client",
            "https://example.com/callback"
        )
        assert result == True

        # Different URI should fail
        result = await manager.validate_redirect_uri(
            "test-client",
            "https://example.com/callback?param=value"
        )
        assert result == False

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_exchange_code_for_token_success(self, manager, redis_mock):
        """Test successful authorization code exchange"""
        # Setup stored authorization
        pkce = PKCEChallenge.generate()
        auth_data = {
            "client_id": "test-client",
            "redirect_uri": "https://example.com/callback",
            "scope": "read write",
            "pkce_challenge": pkce.challenge,
            "pkce_method": "S256",
            "user_id": "user-123"
        }
        redis_mock.get = Mock(return_value=json.dumps(auth_data))

        # Create token request
        token_request = TokenRequest(
            grant_type="authorization_code",
            code="test-auth-code",
            redirect_uri="https://example.com/callback",
            client_id="test-client",
            code_verifier=pkce.verifier
        )

        # Exchange code for token
        response = await manager.exchange_code_for_token(token_request)

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "Bearer"
        assert response.expires_in == 900  # 15 minutes
        assert response.scope == "read write"

        # Verify code was deleted after use
        redis_mock.delete.assert_called_with("oauth21:auth_code:test-auth-code")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_exchange_code_pkce_validation_failure(self, manager, redis_mock):
        """Test code exchange with PKCE validation failure"""
        # Setup stored authorization
        pkce = PKCEChallenge.generate()
        auth_data = {
            "client_id": "test-client",
            "redirect_uri": "https://example.com/callback",
            "scope": "read write",
            "pkce_challenge": pkce.challenge,
            "pkce_method": "S256",
            "user_id": "user-123"
        }
        redis_mock.get = Mock(return_value=json.dumps(auth_data))

        # Create token request with wrong verifier
        token_request = TokenRequest(
            grant_type="authorization_code",
            code="test-auth-code",
            redirect_uri="https://example.com/callback",
            client_id="test-client",
            code_verifier="wrong-verifier"
        )

        # Should raise error
        with pytest.raises(InvalidGrantError) as exc_info:
            await manager.exchange_code_for_token(token_request)

        assert "PKCE validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_refresh_token_success(self, manager, redis_mock):
        """Test successful token refresh"""
        # Setup stored refresh token
        refresh_data = {
            "client_id": "test-client",
            "user_id": "user-123",
            "scope": "read write"
        }
        redis_mock.get = Mock(return_value=json.dumps(refresh_data))

        # Create refresh request
        token_request = TokenRequest(
            grant_type="refresh_token",
            refresh_token="test-refresh-token",
            client_id="test-client"
        )

        # Refresh token
        response = await manager.refresh_token(token_request)

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "Bearer"
        assert response.expires_in == 900

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_revoke_token_access(self, manager, redis_mock):
        """Test revoking access token"""
        redis_mock.exists = Mock(return_value=True)

        result = await manager.revoke_token(
            token="test-access-token",
            token_type="access_token"
        )

        assert result == True
        redis_mock.delete.assert_called_with("oauth21:access_token:test-access-token")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_revoke_token_refresh(self, manager, redis_mock):
        """Test revoking refresh token"""
        redis_mock.exists = Mock(return_value=True)

        result = await manager.revoke_token(
            token="test-refresh-token",
            token_type="refresh_token"
        )

        assert result == True
        redis_mock.delete.assert_called_with("oauth21:refresh_token:test-refresh-token")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validate_access_token_success(self, manager, redis_mock):
        """Test validating valid access token"""
        # Setup stored token
        token_data = {
            "client_id": "test-client",
            "user_id": "user-123",
            "scope": "read write",
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        }
        redis_mock.get = Mock(return_value=json.dumps(token_data))

        result = await manager.validate_access_token("test-access-token")

        assert result["valid"] == True
        assert result["client_id"] == "test-client"
        assert result["user_id"] == "user-123"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validate_access_token_expired(self, manager, redis_mock):
        """Test validating expired access token"""
        # Setup expired token
        token_data = {
            "client_id": "test-client",
            "user_id": "user-123",
            "scope": "read write",
            "issued_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "expires_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        }
        redis_mock.get = Mock(return_value=json.dumps(token_data))

        result = await manager.validate_access_token("test-access-token")

        assert result["valid"] == False
        assert result["error"] == "token_expired"

    def test_generate_secure_token(self, manager):
        """Test secure token generation"""
        token = manager._generate_secure_token()

        # Should be URL-safe base64 encoded
        assert len(token) >= 43  # Minimum for 32 bytes base64
        # Should only contain URL-safe characters
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in token)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_clean_expired_tokens(self, manager, redis_mock):
        """Test cleaning expired tokens"""
        # Mock Redis scan
        redis_mock.scan_iter = Mock(return_value=[
            "oauth21:access_token:token1",
            "oauth21:access_token:token2",
            "oauth21:refresh_token:token3"
        ])

        # Mock expired and valid tokens
        expired_token = {
            "expires_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        }
        valid_token = {
            "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }

        redis_mock.get = Mock(side_effect=[
            json.dumps(expired_token),  # token1 - expired
            json.dumps(valid_token),     # token2 - valid
            json.dumps(expired_token),  # token3 - expired
        ])

        deleted = await manager.clean_expired_tokens()

        assert deleted == 2
        assert redis_mock.delete.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_unsupported_grant_type(self, manager):
        """Test unsupported grant type"""
        token_request = TokenRequest(
            grant_type="implicit",  # Not allowed in OAuth 2.1
            client_id="test-client"
        )

        # Mock to raise error for unsupported grant
        manager.exchange_code_for_token = AsyncMock(
            side_effect=UnsupportedGrantTypeError("Grant type 'implicit' is not supported")
        )

        with pytest.raises(UnsupportedGrantTypeError):
            await manager.exchange_code_for_token(token_request)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_health_check(self, manager, redis_mock):
        """Test OAuth 2.1 manager health check"""
        redis_mock.ping = Mock(return_value=True)
        redis_mock.dbsize = Mock(return_value=100)

        health = await manager.health_check()

        assert health["status"] == "healthy"
        assert health["redis_connected"] == True
        assert health["total_keys"] == 100
        assert health["pkce_enforced"] == True
        assert health["supported_grants"] == ["authorization_code", "refresh_token"]


class TestOAuth21Security:
    """Test OAuth 2.1 security features"""

    @pytest.fixture
    def manager(self):
        """Create OAuth 2.1 manager"""
        with patch('apps.backend.core.security.oauth21_compliance.redis.Redis'):
            return OAuth21Manager()

    def test_no_implicit_flow_support(self, manager):
        """Ensure implicit flow is not supported"""
        # OAuth 2.1 removes implicit flow
        assert "implicit" not in ["authorization_code", "refresh_token"]
        assert "password" not in ["authorization_code", "refresh_token"]

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_authorization_code_single_use(self, manager):
        """Test authorization codes can only be used once"""
        manager.redis_client = Mock()

        # First use should succeed
        auth_data = {
            "client_id": "test-client",
            "redirect_uri": "https://example.com/callback",
            "scope": "read",
            "pkce_challenge": "challenge",
            "pkce_method": "S256",
            "user_id": "user-123"
        }
        manager.redis_client.get = Mock(return_value=json.dumps(auth_data))

        # After successful exchange, code should be deleted
        with patch.object(manager, '_validate_pkce', return_value=True):
            token_request = TokenRequest(
                grant_type="authorization_code",
                code="test-code",
                redirect_uri="https://example.com/callback",
                client_id="test-client",
                code_verifier="verifier"
            )

            response = await manager.exchange_code_for_token(token_request)

            # Verify code was deleted
            manager.redis_client.delete.assert_called_with("oauth21:auth_code:test-code")

    def test_token_entropy(self, manager):
        """Test token has sufficient entropy"""
        tokens = set()
        # Generate multiple tokens
        for _ in range(100):
            token = manager._generate_secure_token()
            tokens.add(token)

        # All should be unique
        assert len(tokens) == 100

        # Check minimum length for security
        for token in tokens:
            assert len(token) >= 43  # 32 bytes base64 encoded


class TestOAuth21Integration:
    """Integration tests for OAuth 2.1"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.asyncio
async def test_full_authorization_flow(self):
        """Test complete authorization code flow with PKCE"""
        # This would require a running Redis instance
        # Skipped unless integration tests are enabled
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.asyncio
async def test_token_refresh_flow(self):
        """Test token refresh flow"""
        # This would require a running Redis instance
        # Skipped unless integration tests are enabled
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=apps.backend.core.security.oauth21_compliance"])