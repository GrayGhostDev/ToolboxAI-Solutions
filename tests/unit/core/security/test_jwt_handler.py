"""
Unit Tests for JWT Handler

Tests JWT token creation, validation, and management.
Aligned with actual jwt_handler.py implementation (2025-10-11).
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
import jwt as pyjwt
from fastapi import HTTPException

from apps.backend.core.security.jwt_handler import (
    create_access_token,
    verify_token,
    TokenData,
    Token,
    SECRET_KEY,
    ALGORITHM,
)


class TestJWTTokenCreation:
    """Test JWT token creation functions."""

    def test_create_access_token_basic(self):
        """Test creating a basic access token."""
        data = {"sub": "user123", "role": "student"}

        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert token.count(".") == 2

    def test_create_access_token_with_expiration(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta=expires_delta)

        # Verify token and check expiration
        token_data = verify_token(token)
        assert token_data.username == "user123"
        assert token_data.exp is not None

        expected_exp = datetime.now(timezone.utc) + expires_delta
        # Allow 5 second tolerance for test execution time
        assert abs((token_data.exp - expected_exp).total_seconds()) < 5

    def test_create_access_token_includes_claims(self):
        """Test that created token includes all claims."""
        data = {
            "sub": "user123",
            "role": "teacher",
            "user_id": 456
        }

        token = create_access_token(data)

        # Decode using pyjwt to check raw claims
        decoded = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "teacher"
        assert decoded["user_id"] == 456
        assert "exp" in decoded  # Expiration should be added

    def test_token_structure_is_valid_jwt(self):
        """Test that token follows JWT structure."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Should be decodable as JWT
        header = pyjwt.get_unverified_header(token)
        assert "alg" in header
        assert "typ" in header


class TestJWTTokenVerification:
    """Test JWT token verification and validation."""

    def test_verify_valid_token(self):
        """Test verifying a valid access token."""
        data = {"sub": "user123", "role": "student", "user_id": 123}
        token = create_access_token(data)

        token_data = verify_token(token)

        assert isinstance(token_data, TokenData)
        assert token_data.username == "user123"
        assert token_data.role == "student"
        assert token_data.user_id == 123

    def test_verify_token_with_expiration(self):
        """Test that verified token includes expiration."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        token_data = verify_token(token)

        assert token_data.exp is not None
        assert isinstance(token_data.exp, datetime)
        # Expiration should be in the future
        assert token_data.exp > datetime.now(timezone.utc)

    def test_verify_expired_token_raises_error(self):
        """Test that verifying expired token raises HTTPException."""
        data = {"sub": "user123"}
        # Create token with negative expiration (already expired)
        expired_token = create_access_token(
            data,
            expires_delta=timedelta(seconds=-10)
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_verify_invalid_token_raises_error(self):
        """Test that verifying invalid token raises HTTPException."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_tampered_token_raises_error(self):
        """Test that tampered token fails verification."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Tamper with token by modifying signature
        tampered_token = token[:-5] + "XXXXX"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_without_subject_fails(self):
        """Test that token without subject fails validation."""
        # Create token manually without 'sub' claim
        payload = {
            "user_id": 123,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401

    def test_verify_token_with_wrong_secret_fails(self):
        """Test that token signed with different secret fails."""
        data = {"sub": "user123"}

        # Create token with wrong secret
        wrong_secret_token = pyjwt.encode(
            {**data, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong_secret_key",
            algorithm=ALGORITHM
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(wrong_secret_token)

        assert exc_info.value.status_code == 401


class TestJWTTokenClaims:
    """Test specific JWT claim handling."""

    def test_token_includes_subject(self):
        """Test that token includes subject claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        token_data = verify_token(token)
        assert token_data.username == "user123"

    def test_token_includes_role(self):
        """Test that role claim is properly handled."""
        data = {"sub": "user123", "role": "teacher"}
        token = create_access_token(data)

        token_data = verify_token(token)
        assert token_data.role == "teacher"

    def test_token_includes_user_id(self):
        """Test that user_id claim is properly handled."""
        data = {"sub": "user123", "user_id": 456}
        token = create_access_token(data)

        token_data = verify_token(token)
        assert token_data.user_id == 456

    def test_token_custom_claims_preserved(self):
        """Test that custom claims are preserved in token."""
        data = {
            "sub": "user123",
            "role": "admin",
            "user_id": 789,
        }

        token = create_access_token(data)

        # Decode raw to check all claims
        decoded = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert decoded["user_id"] == 789
        assert "exp" in decoded

    def test_token_exp_claim_is_future(self):
        """Test that expiration is in the future."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        token_data = verify_token(token)
        assert token_data.exp > datetime.now(timezone.utc)


class TestJWTTokenSecurity:
    """Test security aspects of JWT tokens."""

    def test_token_algorithm_is_secure(self):
        """Test that secure algorithm is used."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Decode header to check algorithm
        header = pyjwt.get_unverified_header(token)

        # Should use HS256 or stronger
        assert header["alg"] in ["HS256", "HS384", "HS512", "RS256"]

    def test_token_different_for_same_data(self):
        """Test that tokens include timestamp variation."""
        data = {"sub": "user123"}

        token1 = create_access_token(data)
        # Wait a moment to ensure different timestamp
        import time
        time.sleep(0.01)
        token2 = create_access_token(data)

        # Tokens should be different due to different exp timestamp
        assert token1 != token2

    def test_token_without_correct_secret_fails(self):
        """Test that token verification fails with wrong secret."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Try to decode with wrong secret
        with pytest.raises(pyjwt.InvalidSignatureError):
            pyjwt.decode(token, "wrong_secret", algorithms=[ALGORITHM])

    def test_tokens_expire_correctly(self):
        """Test that expired tokens cannot be used."""
        data = {"sub": "user123"}
        token = create_access_token(
            data,
            expires_delta=timedelta(milliseconds=100)
        )

        # Wait for token to expire
        import time
        time.sleep(0.2)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401

    def test_token_has_bearer_authentication_header(self):
        """Test that HTTPException includes WWW-Authenticate header."""
        invalid_token = "invalid.token"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


class TestJWTEdgeCases:
    """Test edge cases and error handling."""

    def test_create_token_with_empty_subject(self):
        """Test creating token with empty subject."""
        data = {"sub": ""}

        token = create_access_token(data)

        # Empty subject should still work (validation happens at app level)
        decoded = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == ""

    def test_create_token_with_none_values(self):
        """Test handling of None values in data."""
        data = {"sub": "user123", "role": None}

        token = create_access_token(data)
        token_data = verify_token(token)

        assert token_data.username == "user123"
        assert token_data.role is None

    def test_verify_token_with_extra_segments(self):
        """Test handling malformed token with extra segments."""
        invalid_token = "header.payload.signature.extra"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_with_missing_segments(self):
        """Test handling malformed token with missing segments."""
        invalid_token = "header.payload"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_with_invalid_base64(self):
        """Test handling token with invalid base64 encoding."""
        invalid_token = "!!!invalid!!.!!!base64!!.!!!encoding!!"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_create_token_with_very_long_expiration(self):
        """Test creating token with very long expiration."""
        data = {"sub": "user123"}
        # 10 years
        expires_delta = timedelta(days=365 * 10)

        token = create_access_token(data, expires_delta=expires_delta)
        token_data = verify_token(token)

        expected_exp = datetime.now(timezone.utc) + expires_delta

        # Should be approximately 10 years from now (within 1 minute tolerance)
        assert abs((token_data.exp - expected_exp).total_seconds()) < 60

    def test_create_token_with_zero_expiration(self):
        """Test creating token with zero expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(seconds=0)

        token = create_access_token(data, expires_delta=expires_delta)

        # Token should be immediately expired or expire very soon
        # Give it a moment to definitely be expired
        import time
        time.sleep(0.01)

        with pytest.raises(HTTPException):
            verify_token(token)


class TestTokenDataModel:
    """Test the TokenData Pydantic model."""

    def test_token_data_creation(self):
        """Test creating TokenData instance."""
        token_data = TokenData(
            username="user123",
            user_id=456,
            role="teacher",
            exp=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        assert token_data.username == "user123"
        assert token_data.user_id == 456
        assert token_data.role == "teacher"
        assert token_data.exp is not None

    def test_token_data_optional_fields(self):
        """Test that TokenData fields are optional."""
        token_data = TokenData()

        assert token_data.username is None
        assert token_data.user_id is None
        assert token_data.role is None
        assert token_data.exp is None

    def test_token_data_from_verification(self):
        """Test that verify_token returns proper TokenData."""
        data = {"sub": "user123", "user_id": 789, "role": "admin"}
        token = create_access_token(data)

        token_data = verify_token(token)

        assert isinstance(token_data, TokenData)
        assert token_data.username == "user123"
        assert token_data.user_id == 789
        assert token_data.role == "admin"


class TestTokenModel:
    """Test the Token response model."""

    def test_token_model_creation(self):
        """Test creating Token response model."""
        token = Token(
            access_token="sample.jwt.token",
            expires_in=3600,
            role="teacher"
        )

        assert token.access_token == "sample.jwt.token"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
        assert token.role == "teacher"

    def test_token_model_default_token_type(self):
        """Test that token_type defaults to 'bearer'."""
        token = Token(
            access_token="sample.jwt.token",
            expires_in=3600
        )

        assert token.token_type == "bearer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
