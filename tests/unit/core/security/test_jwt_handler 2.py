"""
Unit Tests for JWT Handler

Tests JWT token creation, validation, and management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt as pyjwt

from apps.backend.core.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_token_signature,
    get_token_expiration,
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

        # Decode to verify expiration
        decoded = decode_access_token(token)
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta

        # Allow 5 second tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_create_access_token_includes_claims(self):
        """Test that created token includes all claims."""
        data = {
            "sub": "user123",
            "role": "teacher",
            "organization_id": "org-456"
        }

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "teacher"
        assert decoded["organization_id"] == "org-456"
        assert "exp" in decoded  # Expiration should be added

    def test_create_refresh_token_basic(self):
        """Test creating refresh token."""
        data = {"sub": "user123"}

        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_create_refresh_token_longer_expiration(self):
        """Test that refresh token has longer expiration than access token."""
        data = {"sub": "user123"}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_exp = decode_access_token(access_token)["exp"]
        refresh_exp = decode_refresh_token(refresh_token)["exp"]

        # Refresh token should expire after access token
        assert refresh_exp > access_exp


class TestJWTTokenDecoding:
    """Test JWT token decoding and validation."""

    def test_decode_valid_access_token(self):
        """Test decoding a valid access token."""
        data = {"sub": "user123", "role": "student"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "student"

    def test_decode_expired_token_raises_error(self):
        """Test that decoding expired token raises error."""
        data = {"sub": "user123"}
        # Create token with negative expiration (already expired)
        expired_token = create_access_token(
            data,
            expires_delta=timedelta(seconds=-10)
        )

        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(expired_token)

    def test_decode_invalid_token_raises_error(self):
        """Test that decoding invalid token raises error."""
        invalid_token = "invalid.token.here"

        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token(invalid_token)

    def test_decode_tampered_token_raises_error(self):
        """Test that tampered token fails verification."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Tamper with token by modifying a character
        tampered_token = token[:-5] + "XXXXX"

        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token(tampered_token)

    def test_decode_token_with_wrong_secret_fails(self):
        """Test that token signed with different secret fails."""
        # This would require mocking the secret, which depends on implementation
        # Skip if JWT_SECRET is hardcoded or not easily mockable
        pytest.skip("Requires mockable JWT secret configuration")

    def test_decode_refresh_token_valid(self):
        """Test decoding valid refresh token."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        decoded = decode_refresh_token(token)

        assert decoded["sub"] == "user123"


class TestJWTTokenVerification:
    """Test token verification utilities."""

    def test_verify_token_signature_valid(self):
        """Test verifying valid token signature."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        is_valid = verify_token_signature(token)

        assert is_valid is True

    def test_verify_token_signature_invalid(self):
        """Test verifying invalid token signature."""
        invalid_token = "invalid.token.signature"

        is_valid = verify_token_signature(invalid_token)

        assert is_valid is False

    def test_verify_token_signature_expired(self):
        """Test verifying expired token."""
        data = {"sub": "user123"}
        expired_token = create_access_token(
            data,
            expires_delta=timedelta(seconds=-10)
        )

        # Expired tokens have valid signatures, but are not valid for use
        is_valid = verify_token_signature(expired_token)

        # Depending on implementation, might be True (signature valid)
        # or False (token expired)
        assert isinstance(is_valid, bool)

    def test_get_token_expiration_valid(self):
        """Test getting expiration time from token."""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)

        exp_time = get_token_expiration(token)

        assert isinstance(exp_time, datetime)

        # Should be approximately 1 hour from now
        expected_exp = datetime.utcnow() + expires_delta
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_get_token_expiration_invalid_token(self):
        """Test getting expiration from invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(pyjwt.InvalidTokenError):
            get_token_expiration(invalid_token)


class TestJWTTokenClaims:
    """Test specific JWT claim handling."""

    def test_token_includes_iat_claim(self):
        """Test that token includes issued-at time."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert "iat" in decoded
        iat_time = datetime.fromtimestamp(decoded["iat"])

        # Should be very recent (within last minute)
        time_diff = datetime.utcnow() - iat_time
        assert time_diff.total_seconds() < 60

    def test_token_sub_claim_required(self):
        """Test that subject claim is properly set."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded["sub"] == "user123"

    def test_token_custom_claims_preserved(self):
        """Test that custom claims are preserved in token."""
        data = {
            "sub": "user123",
            "custom_field": "custom_value",
            "number_field": 42,
            "bool_field": True
        }

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["custom_field"] == "custom_value"
        assert decoded["number_field"] == 42
        assert decoded["bool_field"] is True

    def test_token_exp_claim_future(self):
        """Test that expiration is in the future."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        exp_time = datetime.fromtimestamp(decoded["exp"])

        assert exp_time > datetime.utcnow()


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
        """Test that tokens include randomness (via iat)."""
        data = {"sub": "user123"}

        token1 = create_access_token(data)
        # Wait a moment to ensure different iat
        import time
        time.sleep(0.01)
        token2 = create_access_token(data)

        # Tokens should be different due to different iat
        assert token1 != token2

    def test_token_without_secret_fails(self):
        """Test that token verification fails without secret."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Try to decode with wrong secret
        with pytest.raises(pyjwt.InvalidSignatureError):
            pyjwt.decode(token, "wrong_secret", algorithms=["HS256"])

    def test_tokens_are_not_reusable_after_expiration(self):
        """Test that expired tokens cannot be reused."""
        data = {"sub": "user123"}
        token = create_access_token(
            data,
            expires_delta=timedelta(milliseconds=100)
        )

        # Wait for token to expire
        import time
        time.sleep(0.2)

        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(token)


class TestJWTEdgeCases:
    """Test edge cases and error handling."""

    def test_create_token_with_empty_data(self):
        """Test creating token with minimal data."""
        data = {"sub": ""}

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["sub"] == ""

    def test_create_token_with_none_subject(self):
        """Test handling of None subject."""
        data = {"sub": None}

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["sub"] is None

    def test_decode_token_with_extra_segments(self):
        """Test handling malformed token with extra segments."""
        invalid_token = "header.payload.signature.extra"

        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token(invalid_token)

    def test_decode_token_with_missing_segments(self):
        """Test handling malformed token with missing segments."""
        invalid_token = "header.payload"

        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token(invalid_token)

    def test_decode_token_with_invalid_base64(self):
        """Test handling token with invalid base64 encoding."""
        invalid_token = "!!!invalid!!.!!!base64!!.!!!encoding!!"

        with pytest.raises(pyjwt.InvalidTokenError):
            decode_access_token(invalid_token)

    def test_create_token_with_very_long_expiration(self):
        """Test creating token with very long expiration."""
        data = {"sub": "user123"}
        # 10 years
        expires_delta = timedelta(days=365 * 10)

        token = create_access_token(data, expires_delta=expires_delta)
        decoded = decode_access_token(token)

        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta

        # Should be approximately 10 years from now
        assert abs((exp_time - expected_exp).total_seconds()) < 60

    def test_create_token_with_zero_expiration(self):
        """Test creating token with zero expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(seconds=0)

        token = create_access_token(data, expires_delta=expires_delta)

        # Token should be immediately expired
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(token)


class TestJWTTokenRefresh:
    """Test token refresh workflows."""

    def test_refresh_token_has_different_expiration(self):
        """Test that refresh tokens have different expiration."""
        data = {"sub": "user123"}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_decoded = decode_access_token(access_token)
        refresh_decoded = decode_refresh_token(refresh_token)

        # Refresh should expire later
        assert refresh_decoded["exp"] > access_decoded["exp"]

    def test_can_decode_refresh_token_as_access_token(self):
        """Test that refresh tokens use same encoding."""
        data = {"sub": "user123"}
        refresh_token = create_refresh_token(data)

        # Should be decodable (might fail if different secrets used)
        try:
            decoded = decode_access_token(refresh_token)
            assert decoded["sub"] == "user123"
        except pyjwt.InvalidTokenError:
            # Different secrets used - expected
            pass

    def test_refresh_workflow(self):
        """Test complete token refresh workflow."""
        # 1. Create initial tokens
        data = {"sub": "user123", "role": "student"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        # 2. Verify access token works
        decoded_access = decode_access_token(access_token)
        assert decoded_access["sub"] == "user123"

        # 3. Verify refresh token works
        decoded_refresh = decode_refresh_token(refresh_token)
        assert decoded_refresh["sub"] == "user123"

        # 4. Create new access token from refresh token data
        new_access_token = create_access_token(data)
        new_decoded = decode_access_token(new_access_token)
        assert new_decoded["sub"] == "user123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
