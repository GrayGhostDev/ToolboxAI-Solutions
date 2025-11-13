"""Session and authentication test data factories."""

from datetime import datetime, timedelta, timezone

import factory
import jwt
from factory import fuzzy
from faker import Faker

from .base_factory import AsyncMixin, DictFactory

fake = Faker()


class SessionFactory(DictFactory, AsyncMixin):
    """Factory for user session data."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    session_id = factory.LazyFunction(lambda: fake.sha256())
    user_id = factory.LazyFunction(lambda: fake.uuid4())

    # Session details
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    last_activity = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    expires_at = factory.LazyFunction(
        lambda: (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    )

    # Device and location
    ip_address = factory.LazyFunction(lambda: fake.ipv4())
    user_agent = factory.LazyFunction(lambda: fake.user_agent())

    device_info = factory.LazyFunction(
        lambda: {
            "type": fake.random_element(["desktop", "mobile", "tablet"]),
            "os": fake.random_element(["Windows", "macOS", "iOS", "Android", "Linux"]),
            "browser": fake.random_element(["Chrome", "Firefox", "Safari", "Edge"]),
            "version": f"{fake.random_int(70, 120)}.{fake.random_int(0, 9)}",
        }
    )

    location = factory.LazyFunction(
        lambda: {
            "country": fake.country(),
            "city": fake.city(),
            "region": fake.state(),
            "timezone": fake.timezone(),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
        }
    )

    # Session state
    is_active = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=80))
    is_authenticated = True
    authentication_method = fuzzy.FuzzyChoice(["password", "oauth", "sso", "2fa"])

    # Security
    security_flags = factory.LazyFunction(
        lambda: {
            "suspicious_activity": fake.boolean(chance_of_getting_true=5),
            "new_device": fake.boolean(chance_of_getting_true=20),
            "vpn_detected": fake.boolean(chance_of_getting_true=10),
            "rate_limited": fake.boolean(chance_of_getting_true=5),
        }
    )

    # Activity tracking
    pages_visited = factory.LazyFunction(
        lambda: [
            {
                "url": fake.uri_path(),
                "title": fake.sentence(),
                "timestamp": fake.date_time_this_week().isoformat(),
                "duration_seconds": fake.random_int(5, 300),
            }
            for _ in range(fake.random_int(5, 20))
        ]
    )

    actions_performed = factory.LazyFunction(
        lambda: [
            {
                "action": fake.random_element(
                    [
                        "view_content",
                        "create_quiz",
                        "submit_answer",
                        "download_resource",
                        "send_message",
                        "update_profile",
                    ]
                ),
                "timestamp": fake.date_time_this_week().isoformat(),
                "details": fake.sentence() if fake.boolean() else None,
            }
            for _ in range(fake.random_int(10, 50))
        ]
    )

    # Permissions for this session
    permissions = factory.LazyFunction(
        lambda: fake.random_elements(
            ["read", "write", "delete", "admin", "moderate", "analyze"],
            length=fake.random_int(1, 6),
        )
    )

    @classmethod
    def expired(cls, **kwargs):
        """Create an expired session."""
        return cls.create(
            expires_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            is_active=False,
            **kwargs,
        )

    @classmethod
    def with_rate_limiting(cls, **kwargs):
        """Create session with rate limiting info."""
        session = cls.create(**kwargs)
        session["rate_limit"] = {
            "requests_made": fake.random_int(50, 500),
            "limit": 1000,
            "reset_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "remaining": fake.random_int(0, 500),
        }
        return session


class AuthTokenFactory(DictFactory):
    """Factory for authentication tokens."""

    # Token configuration
    secret_key = "test-secret-key-for-testing-only"
    algorithm = "HS256"

    # Token data
    user_id = factory.LazyFunction(lambda: fake.uuid4())
    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    role = fuzzy.FuzzyChoice(["student", "teacher", "admin"])

    # Token metadata
    issued_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    expires_at = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(hours=1))

    # Additional claims
    permissions = factory.LazyFunction(
        lambda: fake.random_elements(
            ["read", "write", "delete", "admin"], length=fake.random_int(1, 4)
        )
    )

    session_id = factory.LazyFunction(lambda: fake.uuid4())
    token_type = "access"

    @classmethod
    def create_token(cls, **kwargs):
        """Create a JWT token."""
        data = cls.create(**kwargs)

        payload = {
            "sub": data["user_id"],
            "username": data["username"],
            "email": data["email"],
            "role": data["role"],
            "permissions": data["permissions"],
            "session_id": data["session_id"],
            "type": data["token_type"],
            "iat": data["issued_at"].timestamp(),
            "exp": data["expires_at"].timestamp(),
        }

        token = jwt.encode(payload, data["secret_key"], algorithm=data["algorithm"])
        data["token"] = token
        return data

    @classmethod
    def create_token_pair(cls, **kwargs):
        """Create access and refresh token pair."""
        # Access token (short-lived)
        access_data = cls.create_token(
            token_type="access",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            **kwargs,
        )

        # Refresh token (long-lived)
        refresh_data = cls.create_token(
            token_type="refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            permissions=[],  # Refresh tokens have minimal permissions
            **kwargs,
        )

        return {
            "access_token": access_data["token"],
            "refresh_token": refresh_data["token"],
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes in seconds
        }

    @classmethod
    def expired_token(cls, **kwargs):
        """Create an expired token."""
        return cls.create_token(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1), **kwargs
        )


class OAuth2Factory(DictFactory):
    """Factory for OAuth2 authentication data."""

    # OAuth provider
    provider = fuzzy.FuzzyChoice(["google", "github", "microsoft", "facebook"])

    # OAuth tokens
    access_token = factory.LazyFunction(lambda: fake.sha256())
    refresh_token = factory.LazyFunction(lambda: fake.sha256())
    id_token = factory.LazyFunction(lambda: fake.sha256())

    # Token metadata
    token_type = "Bearer"
    expires_in = factory.LazyFunction(lambda: fake.random_int(3600, 7200))
    scope = factory.LazyFunction(
        lambda: " ".join(
            fake.random_elements(
                ["openid", "profile", "email", "offline_access"], length=fake.random_int(2, 4)
            )
        )
    )

    # User info from provider
    provider_user_info = factory.LazyFunction(
        lambda: {
            "id": fake.uuid4(),
            "email": fake.email(),
            "name": fake.name(),
            "picture": fake.image_url(),
            "email_verified": fake.boolean(chance_of_getting_true=90),
            "locale": fake.locale(),
        }
    )

    # OAuth state
    state = factory.LazyFunction(lambda: fake.sha256())
    nonce = factory.LazyFunction(lambda: fake.sha256())
    code_verifier = factory.LazyFunction(lambda: fake.sha256())
    code_challenge = factory.LazyFunction(lambda: fake.sha256())

    # Timestamps
    authorized_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    token_refreshed_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc).isoformat() if fake.boolean() else None
    )


class APIKeyFactory(DictFactory):
    """Factory for API key data."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    key = factory.LazyFunction(lambda: f"sk_{fake.sha256()[:32]}")
    name = factory.LazyFunction(lambda: f"{fake.word()}_api_key")

    # Key metadata
    created_at = factory.LazyFunction(lambda: fake.date_time_this_year().isoformat())
    last_used = factory.LazyFunction(
        lambda: fake.date_time_this_month().isoformat() if fake.boolean() else None
    )
    expires_at = factory.LazyFunction(
        lambda: (
            (datetime.now(timezone.utc) + timedelta(days=fake.random_int(30, 365))).isoformat()
            if fake.boolean()
            else None
        )
    )

    # Permissions
    scopes = factory.LazyFunction(
        lambda: fake.random_elements(
            [
                "read:content",
                "write:content",
                "read:users",
                "write:users",
                "read:analytics",
                "admin:system",
            ],
            length=fake.random_int(1, 6),
        )
    )

    # Rate limiting
    rate_limit = factory.LazyFunction(
        lambda: {
            "requests_per_hour": fake.random_int(100, 10000),
            "requests_per_day": fake.random_int(1000, 100000),
            "burst_limit": fake.random_int(10, 100),
        }
    )

    # Usage statistics
    usage_stats = factory.LazyFunction(
        lambda: {
            "total_requests": fake.random_int(0, 1000000),
            "requests_today": fake.random_int(0, 10000),
            "requests_this_month": fake.random_int(0, 100000),
            "last_request": fake.date_time_this_week().isoformat() if fake.boolean() else None,
            "error_count": fake.random_int(0, 100),
        }
    )

    # Security
    is_active = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=90))
    revoked = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=10))
    revoked_at = factory.LazyFunction(
        lambda: (
            fake.date_time_this_month().isoformat()
            if fake.boolean(chance_of_getting_true=10)
            else None
        )
    )
