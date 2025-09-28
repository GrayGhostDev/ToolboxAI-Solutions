import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest_asyncio
"""
Comprehensive test suite for auth_secure.py
Tests secure authentication, JWT handling, rate limiting, and CSRF protection.
"""

import pytest
import jwt
import time
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from apps.backend.api.auth.auth_secure import (
    SecureAuth, RateLimiter, CSRFProtection, TokenData,
    get_current_user, require_role, 
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials


class TestSecureAuth:
    """Test SecureAuth class functionality"""

    def test_password_validation_requirements(self):
        """Test password strength validation"""
        # Valid password
        valid_password = "Test123!@#"
        hashed = SecureAuth.hash_password(valid_password)
        assert hashed is not None
        assert SecureAuth.verify_password(valid_password, hashed)

        # Too short
        with pytest.raises(ValueError, match="at least 8 characters"):
            SecureAuth.hash_password("Test1!")

        # Missing uppercase
        with pytest.raises(ValueError, match="uppercase letter"):
            SecureAuth.hash_password("test123!@#")

        # Missing lowercase  
        with pytest.raises(ValueError, match="lowercase letter"):
            SecureAuth.hash_password("TEST123!@#")

        # Missing digit
        with pytest.raises(ValueError, match="number"):
            SecureAuth.hash_password("TestABC!@#")

    def test_password_hashing_and_verification(self):
        """Test bcrypt password hashing"""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = SecureAuth.hash_password(password)
        assert hashed is not None
        assert len(hashed) > 50  # Bcrypt hashes are long
        
        # Verify correct password
        assert SecureAuth.verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert SecureAuth.verify_password("WrongPassword", hashed) is False
        
        # Verify with malformed hash
        assert SecureAuth.verify_password(password, "invalid_hash") is False

    def test_token_creation_and_validation(self):
        """Test JWT token creation and validation"""
        user_data = {
            "sub": "user123",
            "role": "student"
        }
        
        # Create token
        token = SecureAuth.create_access_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = SecureAuth.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "student"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
        assert payload["type"] == "access"

    def test_token_expiration(self):
        """Test token expiration handling"""
        user_data = {"sub": "user123", "role": "student"}
        
        # Create expired token
        expired_delta = timedelta(seconds=-1)
        expired_token = SecureAuth.create_access_token(user_data, expired_delta)
        
        # Should raise exception for expired token
        with pytest.raises(HTTPException) as exc_info:
            SecureAuth.verify_token(expired_token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in str(exc_info.value.detail).lower()

    def test_invalid_token_handling(self):
        """Test invalid token scenarios"""
        # Invalid JWT format
        with pytest.raises(HTTPException) as exc_info:
            SecureAuth.verify_token("invalid.jwt.token")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

        # Valid JWT but wrong type
        wrong_type_data = {"sub": "user123", "type": "refresh"}
        wrong_type_token = jwt.encode(wrong_type_data, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            SecureAuth.verify_token(wrong_type_token, "access")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_creation(self):
        """Test refresh token creation"""
        user_id = "user123"
        refresh_token = SecureAuth.create_refresh_token(user_id)
        
        assert refresh_token is not None
        payload = SecureAuth.verify_token(refresh_token, "refresh")
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    @patch('apps.backend.api.auth.auth_secure.redis_client')
    def test_token_blacklist(self, mock_redis):
        """Test token revocation and blacklist"""
        mock_redis.get.return_value = None  # Not blacklisted
        mock_redis.setex.return_value = True
        
        user_data = {"sub": "user123", "role": "student"}
        token = SecureAuth.create_access_token(user_data)
        
        # Token should be valid initially
        payload = SecureAuth.verify_token(token)
        assert payload is not None
        
        # Revoke token
        SecureAuth.revoke_token(token)
        
        # Mock blacklisted token
        mock_redis.get.return_value = "revoked"
        
        # Should raise exception for blacklisted token
        with pytest.raises(HTTPException) as exc_info:
            SecureAuth.verify_token(token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('apps.backend.api.auth.auth_secure.redis_client')
    def test_login_attempts_tracking(self, mock_redis):
        """Test login attempt tracking and lockout"""
        username = "testuser"
        
        # No lockout initially
        mock_redis.get.return_value = None
        assert SecureAuth.check_login_attempts(username) is True
        
        # Record failed attempts
        mock_redis.incr.return_value = 1
        SecureAuth.record_failed_login(username)
        
        # Still allowed after few attempts
        mock_redis.get.side_effect = [None, "3"]
        assert SecureAuth.check_login_attempts(username) is True
        
        # Locked out after max attempts
        mock_redis.get.side_effect = [None, "5"]
        assert SecureAuth.check_login_attempts(username) is False
        
        # Clear attempts
        SecureAuth.clear_login_attempts(username)
        mock_redis.delete.assert_called()

    def test_no_redis_fallback(self):
        """Test graceful handling when Redis is unavailable"""
        with patch('apps.backend.api.auth.auth_secure.redis_client', None):
            # Should still work without Redis
            assert SecureAuth.check_login_attempts("user") is True
            SecureAuth.record_failed_login("user")  # Should not raise
            SecureAuth.clear_login_attempts("user")  # Should not raise


class TestTokenData:
    """Test TokenData validation"""

    def test_valid_token_data(self):
        """Test valid token data creation"""
        token_data = TokenData(
            sub="user123",
            role="student",
            exp=datetime.now(timezone.utc) + timedelta(minutes=30),
            iat=datetime.now(timezone.utc),
            jti="unique_token_id"
        )
        assert token_data.sub == "user123"
        assert token_data.role == "student"

    def test_invalid_role_validation(self):
        """Test role validation"""
        with pytest.raises(ValueError, match="Invalid role"):
            TokenData(
                sub="user123",
                role="invalid_role",
                exp=datetime.now(timezone.utc) + timedelta(minutes=30),
                iat=datetime.now(timezone.utc),
                jti="unique_token_id"
            )


class TestRateLimiter:
    """Test rate limiting functionality"""

    @patch('apps.backend.api.auth.auth_secure.redis_client')
    def test_rate_limit_check(self, mock_redis):
        """Test rate limit checking"""
        key = "test_key"
        max_requests = 5
        window = 60
        
        # First request
        mock_redis.incr.return_value = 1
        assert RateLimiter.check_rate_limit(key, max_requests, window) is True
        
        # Within limit
        mock_redis.incr.return_value = 3
        assert RateLimiter.check_rate_limit(key, max_requests, window) is True
        
        # Exceed limit
        mock_redis.incr.return_value = 6
        assert RateLimiter.check_rate_limit(key, max_requests, window) is False

    def test_rate_limit_no_redis(self):
        """Test rate limiting without Redis"""
        with patch('apps.backend.api.auth.auth_secure.redis_client', None):
            # Should allow requests when Redis unavailable
            assert RateLimiter.check_rate_limit("key", 5, 60) is True

    @pytest.mark.asyncio
    async def test_rate_limit_decorator(self):
        """Test rate limiting decorator"""
        @RateLimiter.rate_limit_decorator(max_requests=2, window=60)
        async def test_endpoint(**kwargs):
            return "success"
        
        # Mock request object
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        with patch.object(RateLimiter, 'check_rate_limit', return_value=True):
            result = await test_endpoint(request=mock_request)
            assert result == "success"
        
        # Test rate limit exceeded
        with patch.object(RateLimiter, 'check_rate_limit', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(request=mock_request)
            assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestCSRFProtection:
    """Test CSRF protection functionality"""

    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        session_id = "session123"
        token = CSRFProtection.generate_csrf_token(session_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert ":" in token  # Should contain separators
        
        # Verify token
        assert CSRFProtection.verify_csrf_token(token, session_id) is True

    def test_csrf_token_verification(self):
        """Test CSRF token verification"""
        session_id = "session123"
        token = CSRFProtection.generate_csrf_token(session_id)
        
        # Valid token
        assert CSRFProtection.verify_csrf_token(token, session_id) is True
        
        # Wrong session ID
        assert CSRFProtection.verify_csrf_token(token, "wrong_session") is False
        
        # Malformed token
        assert CSRFProtection.verify_csrf_token("invalid_token", session_id) is False
        
        # Empty token
        assert CSRFProtection.verify_csrf_token("", session_id) is False

    def test_csrf_token_expiry(self):
        """Test CSRF token expiry"""
        session_id = "session123"
        
        # Create token with past timestamp
        old_time = time.time() - 7200  # 2 hours ago
        message = f"{session_id}:{old_time}"
        import hashlib
        import hmac
        from apps.backend.api.auth.auth_secure import SECRET_KEY
        
        signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        old_token = f"{message}:{signature}"
        
        # Should be invalid due to age
        assert CSRFProtection.verify_csrf_token(old_token, session_id) is False


class TestDependencyFunctions:
    """Test FastAPI dependency functions"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid token"""
        user_data = {"sub": "user123", "role": "student"}
        token = SecureAuth.create_access_token(user_data)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        user = await get_current_user(credentials)
        assert user["id"] == "user123"
        assert user["role"] == "student"
        assert "token_id" in user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_require_role_decorator(self):
        """Test role-based access control decorator"""
        @require_role(["admin", "teacher"])
        async def admin_endpoint(**kwargs):
            return "admin_access"
        
        # Test with valid role
        current_user = {"id": "user123", "role": "admin"}
        result = await admin_endpoint(current_user=current_user)
        assert result == "admin_access"
        
        # Test with invalid role
        current_user = {"id": "user123", "role": "student"}
        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint(current_user=current_user)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        
        # Test with no user
        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint()
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestSecurityConfiguration:
    """Test security configuration and constants"""

    def test_secret_key_security(self):
        """Test that secret key meets security requirements"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) >= 32  # Minimum 256 bits
        assert SECRET_KEY != "your-secret-key-change-in-production"

    def test_algorithm_configuration(self):
        """Test JWT algorithm configuration"""
        assert ALGORITHM == "HS256"

    def test_token_expiration_configuration(self):
        """Test token expiration settings"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert ACCESS_TOKEN_EXPIRE_MINUTES <= 60  # Not too long for security


@pytest.mark.integration
class TestIntegrationScenarios:
    """Test complete authentication flows"""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self):
        """Test complete authentication and authorization flow"""
        # 1. Create user credentials
        user_data = {"sub": "user123", "role": "student"}
        
        # 2. Create access token
        access_token = SecureAuth.create_access_token(user_data)
        assert access_token is not None
        
        # 3. Verify token and get user
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=access_token
        )
        user = await get_current_user(credentials)
        assert user["id"] == "user123"
        
        # 4. Test role-based access
        @require_role(["student", "teacher"])
        async def student_endpoint(**kwargs):
            return "success"
        
        result = await student_endpoint(current_user=user)
        assert result == "success"

    @pytest.mark.asyncio
    @patch('apps.backend.api.auth.auth_secure.redis_client')
    async def test_rate_limited_auth_flow(self, mock_redis):
        """Test authentication with rate limiting"""
        # Setup rate limiting
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        
        @RateLimiter.rate_limit_decorator(max_requests=2, window=60)
        async def login_endpoint(**kwargs):
            user_data = {"sub": "user123", "role": "student"}
            return SecureAuth.create_access_token(user_data)
        
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # First request should succeed
        with patch.object(RateLimiter, 'check_rate_limit', return_value=True):
            token = await login_endpoint(request=mock_request)
            assert token is not None
        
        # Rate limited request should fail
        with patch.object(RateLimiter, 'check_rate_limit', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await login_endpoint(request=mock_request)
            assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_password_security_edge_cases(self):
        """Test password security edge cases"""
        # Test with special characters
        special_password = "Test123!@#$%^&*()"
        hashed = SecureAuth.hash_password(special_password)
        assert SecureAuth.verify_password(special_password, hashed)
        
        # Test with Unicode characters
        unicode_password = "Test123!αβγδε"
        hashed = SecureAuth.hash_password(unicode_password)
        assert SecureAuth.verify_password(unicode_password, hashed)
        
        # Test timing attack resistance (basic check)
        password1 = "Test123!@#"
        password2 = "WrongPassword!@#"
        hashed = SecureAuth.hash_password(password1)
        
        # Both should take similar time (bcrypt property)
        start = time.time()
        SecureAuth.verify_password(password1, hashed)
        time1 = time.time() - start
        
        start = time.time()
        SecureAuth.verify_password(password2, hashed)
        time2 = time.time() - start
        
        # Times should be relatively close (within order of magnitude)
        assert abs(time1 - time2) < 1.0  # Should be much closer in practice


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_malformed_jwt_handling(self):
        """Test handling of malformed JWT tokens"""
        malformed_tokens = [
            "",
            "not.a.jwt",
            "header.payload",
            "header.payload.signature.extra",
            "invalid_base64.invalid_base64.invalid_base64"
        ]
        
        for token in malformed_tokens:
            with pytest.raises(HTTPException) as exc_info:
                SecureAuth.verify_token(token)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_none_values_handling(self):
        """Test handling of None and empty values"""
        # None password should raise ValueError
        with pytest.raises((ValueError, TypeError)):
            SecureAuth.hash_password(None)
        
        # Empty password should raise ValueError
        with pytest.raises(ValueError):
            SecureAuth.hash_password("")
        
        # None token should raise HTTPException
        with pytest.raises(HTTPException):
            SecureAuth.verify_token(None)

    def test_concurrent_token_operations(self):
        """Test concurrent token operations (basic thread safety)"""
        import threading
        import concurrent.futures
        
        def create_and_verify_token(user_id):
            user_data = {"sub": f"user{user_id}", "role": "student"}
            token = SecureAuth.create_access_token(user_data)
            payload = SecureAuth.verify_token(token)
            return payload["sub"] == f"user{user_id}"
        
        # Test with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_verify_token, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All operations should succeed
        assert all(results)
