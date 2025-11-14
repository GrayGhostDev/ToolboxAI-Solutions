"""
Enhanced Security MCP

Advanced Model Context Protocol with OAuth 2.0, Multi-Factor Authentication,
and intelligent rate limiting for the ToolBoxAI educational platform.

Author: ToolboxAI Team
Created: 2025-09-21
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

# Optional imports with fallbacks
try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    import base64
    from io import BytesIO

    import pyotp
    import qrcode

    MFA_AVAILABLE = True
except ImportError:
    MFA_AVAILABLE = False

logger = logging.getLogger(__name__)


class AuthProvider(Enum):
    """Supported OAuth providers"""

    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    APPLE = "apple"
    CUSTOM = "custom"


class MFAMethod(Enum):
    """Multi-factor authentication methods"""

    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_KEY = "hardware_key"
    BACKUP_CODES = "backup_codes"


class RateLimitType(Enum):
    """Rate limiting types"""

    STANDARD = "standard"
    ADAPTIVE = "adaptive"
    ML_BASED = "ml_based"
    BEHAVIOR_BASED = "behavior_based"


@dataclass
class OAuthCredentials:
    """OAuth provider credentials"""

    provider: AuthProvider
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: list[str]
    additional_params: dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


@dataclass
class MFASetup:
    """Multi-factor authentication setup"""

    user_id: str
    method: MFAMethod
    secret: str
    backup_codes: list[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True

    def generate_qr_code(self, issuer: str, account_name: str) -> str:
        """Generate QR code for TOTP setup"""
        if self.method != MFAMethod.TOTP:
            raise ValueError("QR code only available for TOTP method")

        if not MFA_AVAILABLE:
            return "QR_CODE_NOT_AVAILABLE_MISSING_DEPENDENCIES"

        totp_uri = pyotp.totp.TOTP(self.secret).provisioning_uri(
            name=account_name, issuer_name=issuer
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()


@dataclass
class RateLimitRule:
    """Rate limiting rule"""

    rule_id: str
    resource: str
    limit_type: RateLimitType
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int
    window_size_seconds: int
    penalty_duration_seconds: int
    ml_model_path: Optional[str] = None
    behavior_patterns: list[str] = None

    def __post_init__(self):
        if self.behavior_patterns is None:
            self.behavior_patterns = []


class EnhancedSecurityMCP:
    """
    Enhanced security MCP with advanced authentication and rate limiting.

    Features:
    - OAuth 2.0 integration with multiple providers
    - Multi-factor authentication (TOTP, SMS, Email)
    - ML-based rate limiting and anomaly detection
    - Behavioral analysis for security threats
    - Advanced session management
    - Audit logging and compliance
    """

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

        # OAuth configuration
        self.oauth_providers: dict[AuthProvider, OAuthCredentials] = {}
        self.oauth_sessions: dict[str, dict[str, Any]] = {}

        # MFA configuration
        self.mfa_setups: dict[str, MFASetup] = {}
        self.mfa_sessions: dict[str, dict[str, Any]] = {}

        # Rate limiting configuration
        self.rate_limit_rules: dict[str, RateLimitRule] = {}
        self.rate_limit_counters: dict[str, dict[str, Any]] = {}
        self.rate_limit_violations: list[dict[str, Any]] = []

        # Security monitoring
        self.security_events: list[dict[str, Any]] = []
        self.threat_patterns: dict[str, Any] = {}
        self.anomaly_detector = None

        # Session management
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.session_config = {
            "max_session_duration": timedelta(hours=24),
            "idle_timeout": timedelta(minutes=30),
            "concurrent_sessions_limit": 5,
            "session_rotation_interval": timedelta(hours=4),
        }

        # Initialize default configurations
        self._initialize_default_configs()

        logger.info("EnhancedSecurityMCP initialized")

    def _initialize_default_configs(self):
        """Initialize default security configurations"""
        # Default rate limiting rules
        default_rules = [
            RateLimitRule(
                rule_id="api_general",
                resource="/api/*",
                limit_type=RateLimitType.STANDARD,
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=10,
                window_size_seconds=60,
                penalty_duration_seconds=300,
            ),
            RateLimitRule(
                rule_id="auth_endpoints",
                resource="/api/auth/*",
                limit_type=RateLimitType.ADAPTIVE,
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=500,
                burst_limit=3,
                window_size_seconds=60,
                penalty_duration_seconds=600,
            ),
            RateLimitRule(
                rule_id="content_generation",
                resource="/api/content/*",
                limit_type=RateLimitType.BEHAVIOR_BASED,
                requests_per_minute=20,
                requests_per_hour=200,
                requests_per_day=1000,
                burst_limit=5,
                window_size_seconds=60,
                penalty_duration_seconds=180,
            ),
        ]

        for rule in default_rules:
            self.rate_limit_rules[rule.rule_id] = rule

        # Default threat patterns
        self.threat_patterns = {
            "brute_force": {
                "pattern": "multiple_failed_logins",
                "threshold": 5,
                "window_minutes": 15,
                "action": "temporary_ban",
            },
            "credential_stuffing": {
                "pattern": "rapid_login_attempts",
                "threshold": 20,
                "window_minutes": 5,
                "action": "captcha_required",
            },
            "suspicious_behavior": {
                "pattern": "unusual_access_pattern",
                "threshold": 3,
                "window_minutes": 60,
                "action": "additional_verification",
            },
        }

    async def setup_oauth_provider(
        self, provider: AuthProvider, credentials: OAuthCredentials
    ) -> dict[str, Any]:
        """Setup OAuth provider configuration"""
        try:
            # Validate credentials
            validation_result = await self._validate_oauth_credentials(credentials)

            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid OAuth credentials: {validation_result['errors']}",
                }

            # Store provider configuration
            self.oauth_providers[provider] = credentials

            logger.info("OAuth provider %s configured successfully", provider.value)

            return {
                "success": True,
                "provider": provider.value,
                "redirect_uri": credentials.redirect_uri,
                "scopes": credentials.scope,
            }

        except Exception as e:
            logger.error("Failed to setup OAuth provider %s: %s", provider.value, str(e))
            return {"success": False, "error": str(e)}

    async def authenticate_with_oauth(
        self, provider: AuthProvider, auth_code: str, state: str
    ) -> dict[str, Any]:
        """Authenticate user with OAuth provider"""
        try:
            if provider not in self.oauth_providers:
                return {
                    "success": False,
                    "error": f"OAuth provider {provider.value} not configured",
                }

            credentials = self.oauth_providers[provider]

            # Exchange authorization code for access token
            token_result = await self._exchange_oauth_code(credentials, auth_code, state)

            if not token_result["success"]:
                return token_result

            # Get user information from provider
            user_info = await self._get_oauth_user_info(provider, token_result["access_token"])

            if not user_info["success"]:
                return user_info

            # Create or update user session
            session_id = str(uuid.uuid4())
            session_data = {
                "session_id": session_id,
                "user_id": user_info["user_id"],
                "provider": provider.value,
                "user_info": user_info["data"],
                "access_token": token_result["access_token"],
                "refresh_token": token_result.get("refresh_token"),
                "created_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "mfa_required": self._check_mfa_requirement(user_info["user_id"]),
                "mfa_verified": False,
            }

            self.active_sessions[session_id] = session_data

            # Log security event
            await self._log_security_event(
                "oauth_login",
                {
                    "user_id": user_info["user_id"],
                    "provider": provider.value,
                    "session_id": session_id,
                },
            )

            logger.info(
                "OAuth authentication successful for user %s via %s",
                user_info["user_id"],
                provider.value,
            )

            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_info["user_id"],
                "mfa_required": session_data["mfa_required"],
                "session_expires_at": (
                    session_data["created_at"] + self.session_config["max_session_duration"]
                ).isoformat(),
            }

        except Exception as e:
            logger.error("OAuth authentication failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def setup_mfa(
        self, user_id: str, method: MFAMethod, contact_info: str = None
    ) -> dict[str, Any]:
        """Setup multi-factor authentication for user"""
        try:
            # Generate secret for TOTP or validation code for other methods
            if method == MFAMethod.TOTP:
                if not MFA_AVAILABLE:
                    return {
                        "success": False,
                        "error": "TOTP not available - missing pyotp dependency",
                    }

                secret = pyotp.random_base32()
                backup_codes = [secrets.token_hex(4) for _ in range(10)]

                mfa_setup = MFASetup(
                    user_id=user_id,
                    method=method,
                    secret=secret,
                    backup_codes=backup_codes,
                    created_at=datetime.now(timezone.utc),
                )

                # Generate QR code for TOTP setup
                qr_code = mfa_setup.generate_qr_code("ToolBoxAI", f"user_{user_id}")

                self.mfa_setups[user_id] = mfa_setup

                logger.info("TOTP MFA setup completed for user %s", user_id)

                return {
                    "success": True,
                    "method": method.value,
                    "qr_code": qr_code,
                    "backup_codes": backup_codes,
                    "secret": secret,  # Only return for initial setup
                }

            elif method in [MFAMethod.SMS, MFAMethod.EMAIL]:
                if not contact_info:
                    return {
                        "success": False,
                        "error": f"{method.value} requires contact information",
                    }

                # Generate verification code
                verification_code = secrets.randbelow(1000000)
                verification_code_str = f"{verification_code:06d}"

                # Store temporary MFA setup
                temp_setup_id = str(uuid.uuid4())
                self.mfa_sessions[temp_setup_id] = {
                    "user_id": user_id,
                    "method": method,
                    "contact_info": contact_info,
                    "verification_code": verification_code_str,
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
                }

                # Send verification code (simulated)
                await self._send_verification_code(method, contact_info, verification_code_str)

                logger.info("%s MFA setup initiated for user %s", method.value.upper(), user_id)

                return {
                    "success": True,
                    "method": method.value,
                    "setup_id": temp_setup_id,
                    "contact_info": self._mask_contact_info(contact_info),
                    "expires_in_minutes": 10,
                }

            else:
                return {
                    "success": False,
                    "error": f"MFA method {method.value} not yet implemented",
                }

        except Exception as e:
            logger.error("MFA setup failed for user %s: %s", user_id, str(e))
            return {"success": False, "error": str(e)}

    async def verify_mfa(
        self, user_id: str, verification_code: str, session_id: str = None
    ) -> dict[str, Any]:
        """Verify multi-factor authentication code"""
        try:
            if user_id not in self.mfa_setups:
                return {"success": False, "error": "MFA not setup for this user"}

            mfa_setup = self.mfa_setups[user_id]

            if mfa_setup.method == MFAMethod.TOTP:
                # Verify TOTP code
                totp = pyotp.TOTP(mfa_setup.secret)
                is_valid = totp.verify(verification_code, valid_window=1)

                # Check backup codes if TOTP fails
                if not is_valid and verification_code in mfa_setup.backup_codes:
                    is_valid = True
                    mfa_setup.backup_codes.remove(verification_code)  # Use backup code once
                    logger.info("Backup code used for user %s", user_id)

            else:
                # For SMS/Email, check against stored verification code
                temp_sessions = [
                    session
                    for session in self.mfa_sessions.values()
                    if session["user_id"] == user_id and session["method"] == mfa_setup.method
                ]

                is_valid = False
                for session in temp_sessions:
                    if (
                        session["verification_code"] == verification_code
                        and datetime.now(timezone.utc) < session["expires_at"]
                    ):
                        is_valid = True
                        # Clean up used session
                        for session_id, session_data in list(self.mfa_sessions.items()):
                            if session_data == session:
                                del self.mfa_sessions[session_id]
                        break

            if is_valid:
                # Update MFA usage
                mfa_setup.last_used = datetime.now(timezone.utc)

                # Update session if provided
                if session_id and session_id in self.active_sessions:
                    self.active_sessions[session_id]["mfa_verified"] = True
                    self.active_sessions[session_id]["mfa_verified_at"] = datetime.now(timezone.utc)

                # Log security event
                await self._log_security_event(
                    "mfa_verified",
                    {
                        "user_id": user_id,
                        "method": mfa_setup.method.value,
                        "session_id": session_id,
                    },
                )

                logger.info("MFA verification successful for user %s", user_id)

                return {
                    "success": True,
                    "user_id": user_id,
                    "method": mfa_setup.method.value,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                # Log failed attempt
                await self._log_security_event(
                    "mfa_failed",
                    {
                        "user_id": user_id,
                        "method": mfa_setup.method.value,
                        "session_id": session_id,
                    },
                )

                return {"success": False, "error": "Invalid verification code"}

        except Exception as e:
            logger.error("MFA verification failed for user %s: %s", user_id, str(e))
            return {"success": False, "error": str(e)}

    async def apply_advanced_rate_limiting(self, request: dict[str, Any]) -> dict[str, Any]:
        """Apply advanced rate limiting with ML-based detection"""
        try:
            resource = request.get("resource", "/api/unknown")
            user_id = request.get("user_id", "anonymous")
            ip_address = request.get("ip_address", "unknown")
            request.get("user_agent", "unknown")

            # Find applicable rate limit rule
            applicable_rule = self._find_applicable_rate_limit_rule(resource)

            if not applicable_rule:
                # No rate limiting rule - allow request
                return {"allowed": True, "reason": "no_rule_applicable"}

            # Check rate limits based on rule type
            if applicable_rule.limit_type == RateLimitType.STANDARD:
                limit_result = await self._check_standard_rate_limit(
                    user_id, ip_address, applicable_rule
                )

            elif applicable_rule.limit_type == RateLimitType.ADAPTIVE:
                limit_result = await self._check_adaptive_rate_limit(
                    user_id, ip_address, applicable_rule, request
                )

            elif applicable_rule.limit_type == RateLimitType.ML_BASED:
                limit_result = await self._check_ml_based_rate_limit(
                    user_id, request, applicable_rule
                )

            elif applicable_rule.limit_type == RateLimitType.BEHAVIOR_BASED:
                limit_result = await self._check_behavior_based_rate_limit(
                    user_id, request, applicable_rule
                )

            else:
                limit_result = {"allowed": True, "reason": "unknown_limit_type"}

            # Log rate limiting decision
            await self._log_rate_limit_decision(user_id, resource, limit_result, applicable_rule)

            # Apply penalties if needed
            if not limit_result["allowed"]:
                await self._apply_rate_limit_penalty(user_id, ip_address, applicable_rule)

            return limit_result

        except Exception as e:
            logger.error("Rate limiting check failed: %s", str(e))
            return {"allowed": True, "error": str(e)}  # Fail open for availability

    async def _check_standard_rate_limit(
        self, user_id: str, ip_address: str, rule: RateLimitRule
    ) -> dict[str, Any]:
        """Check standard rate limiting"""
        current_time = time.time()
        window_start = current_time - rule.window_size_seconds

        # Get or create counter
        counter_key = f"{rule.rule_id}:{user_id}:{ip_address}"
        if counter_key not in self.rate_limit_counters:
            self.rate_limit_counters[counter_key] = {
                "requests": [],
                "burst_count": 0,
                "last_reset": current_time,
            }

        counter = self.rate_limit_counters[counter_key]

        # Clean old requests
        counter["requests"] = [
            req_time for req_time in counter["requests"] if req_time > window_start
        ]

        # Check limits
        requests_in_window = len(counter["requests"])

        if requests_in_window >= rule.requests_per_minute:
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "limit_type": "standard",
                "requests_in_window": requests_in_window,
                "limit": rule.requests_per_minute,
                "retry_after": rule.window_size_seconds,
            }

        # Check burst limit
        recent_requests = [
            req_time for req_time in counter["requests"] if req_time > current_time - 10
        ]  # Last 10 seconds
        if len(recent_requests) >= rule.burst_limit:
            return {
                "allowed": False,
                "reason": "burst_limit_exceeded",
                "limit_type": "standard",
                "burst_requests": len(recent_requests),
                "burst_limit": rule.burst_limit,
                "retry_after": 10,
            }

        # Allow request and update counter
        counter["requests"].append(current_time)

        return {
            "allowed": True,
            "reason": "within_limits",
            "requests_remaining": rule.requests_per_minute - requests_in_window - 1,
            "window_reset_in": rule.window_size_seconds - (current_time - min(counter["requests"])),
        }

    async def _check_adaptive_rate_limit(
        self,
        user_id: str,
        ip_address: str,
        rule: RateLimitRule,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """Check adaptive rate limiting based on user behavior"""
        # Get user's recent behavior
        user_behavior = await self._analyze_user_behavior(user_id)

        # Adjust limits based on behavior
        trust_score = user_behavior.get("trust_score", 0.5)

        # Adaptive multipliers based on trust score
        if trust_score >= 0.8:
            # Trusted user - higher limits
            adjusted_limit = int(rule.requests_per_minute * 1.5)
            adjusted_burst = int(rule.burst_limit * 2)
        elif trust_score >= 0.5:
            # Normal user - standard limits
            adjusted_limit = rule.requests_per_minute
            adjusted_burst = rule.burst_limit
        else:
            # Suspicious user - lower limits
            adjusted_limit = int(rule.requests_per_minute * 0.5)
            adjusted_burst = max(1, int(rule.burst_limit * 0.5))

        # Create adjusted rule
        adjusted_rule = RateLimitRule(
            rule_id=rule.rule_id,
            resource=rule.resource,
            limit_type=rule.limit_type,
            requests_per_minute=adjusted_limit,
            requests_per_hour=rule.requests_per_hour,
            requests_per_day=rule.requests_per_day,
            burst_limit=adjusted_burst,
            window_size_seconds=rule.window_size_seconds,
            penalty_duration_seconds=rule.penalty_duration_seconds,
        )

        # Check with adjusted limits
        result = await self._check_standard_rate_limit(user_id, ip_address, adjusted_rule)
        result["limit_type"] = "adaptive"
        result["trust_score"] = trust_score
        result["original_limit"] = rule.requests_per_minute
        result["adjusted_limit"] = adjusted_limit

        return result

    async def _check_ml_based_rate_limit(
        self, user_id: str, request: dict[str, Any], rule: RateLimitRule
    ) -> dict[str, Any]:
        """Check ML-based rate limiting using anomaly detection"""
        try:
            # Extract features for ML model
            features = await self._extract_request_features(user_id, request)

            # Use ML model to predict if request is suspicious
            if self.anomaly_detector:
                anomaly_score = await self._predict_anomaly(features)
            else:
                # Fallback to heuristic-based detection
                anomaly_score = await self._heuristic_anomaly_detection(features)

            # Determine if request should be allowed
            anomaly_threshold = 0.7  # Configurable threshold

            if anomaly_score > anomaly_threshold:
                return {
                    "allowed": False,
                    "reason": "anomaly_detected",
                    "limit_type": "ml_based",
                    "anomaly_score": anomaly_score,
                    "threshold": anomaly_threshold,
                    "features": features,
                }
            else:
                # Apply standard rate limiting with ML-adjusted limits
                ml_adjusted_limit = int(rule.requests_per_minute * (1.0 - anomaly_score * 0.5))

                adjusted_rule = RateLimitRule(
                    rule_id=rule.rule_id,
                    resource=rule.resource,
                    limit_type=rule.limit_type,
                    requests_per_minute=ml_adjusted_limit,
                    requests_per_hour=rule.requests_per_hour,
                    requests_per_day=rule.requests_per_day,
                    burst_limit=rule.burst_limit,
                    window_size_seconds=rule.window_size_seconds,
                    penalty_duration_seconds=rule.penalty_duration_seconds,
                )

                result = await self._check_standard_rate_limit(
                    user_id, request.get("ip_address", "unknown"), adjusted_rule
                )
                result["limit_type"] = "ml_based"
                result["anomaly_score"] = anomaly_score

                return result

        except Exception as e:
            logger.error("ML-based rate limiting failed: %s", str(e))
            # Fallback to standard rate limiting
            return await self._check_standard_rate_limit(
                user_id, request.get("ip_address", "unknown"), rule
            )

    async def _analyze_user_behavior(self, user_id: str) -> dict[str, Any]:
        """Analyze user behavior for adaptive rate limiting"""
        # Get recent security events for user
        user_events = [
            event
            for event in self.security_events
            if event.get("data", {}).get("user_id") == user_id
            and event["timestamp"] > datetime.now(timezone.utc) - timedelta(days=7)
        ]

        # Calculate trust score based on behavior
        trust_score = 0.5  # Base trust score

        # Positive indicators
        successful_logins = len([e for e in user_events if e["event_type"] == "oauth_login"])
        mfa_verifications = len([e for e in user_events if e["event_type"] == "mfa_verified"])

        if successful_logins > 0:
            trust_score += min(0.2, successful_logins * 0.05)

        if mfa_verifications > 0:
            trust_score += min(0.2, mfa_verifications * 0.03)

        # Negative indicators
        failed_attempts = len([e for e in user_events if e["event_type"] == "mfa_failed"])
        security_violations = len(
            [e for e in user_events if e["event_type"] == "security_violation"]
        )

        if failed_attempts > 0:
            trust_score -= min(0.3, failed_attempts * 0.1)

        if security_violations > 0:
            trust_score -= min(0.4, security_violations * 0.2)

        # Normalize trust score
        trust_score = max(0.0, min(1.0, trust_score))

        return {
            "trust_score": trust_score,
            "successful_logins": successful_logins,
            "mfa_verifications": mfa_verifications,
            "failed_attempts": failed_attempts,
            "security_violations": security_violations,
            "analysis_period_days": 7,
        }

    async def _extract_request_features(
        self, user_id: str, request: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract features for ML-based analysis"""
        return {
            "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:16],
            "request_hour": datetime.now(timezone.utc).hour,
            "request_day_of_week": datetime.now(timezone.utc).weekday(),
            "resource_type": self._categorize_resource(request.get("resource", "")),
            "request_size": len(json.dumps(request)),
            "has_auth_token": bool(request.get("auth_token")),
            "ip_reputation": await self._get_ip_reputation(request.get("ip_address", "")),
            "user_agent_category": self._categorize_user_agent(request.get("user_agent", "")),
            "session_age_minutes": self._get_session_age(request.get("session_id", "")),
            "recent_request_frequency": await self._get_recent_request_frequency(user_id),
        }

    async def _heuristic_anomaly_detection(self, features: dict[str, Any]) -> float:
        """Heuristic-based anomaly detection as ML fallback"""
        anomaly_score = 0.0

        # Time-based anomalies
        request_hour = features.get("request_hour", 12)
        if request_hour < 6 or request_hour > 23:  # Unusual hours
            anomaly_score += 0.2

        # Request size anomalies
        request_size = features.get("request_size", 1000)
        if request_size > 10000:  # Very large request
            anomaly_score += 0.3

        # IP reputation anomalies
        ip_reputation = features.get("ip_reputation", 0.5)
        if ip_reputation < 0.3:  # Bad IP reputation
            anomaly_score += 0.4

        # Session age anomalies
        session_age = features.get("session_age_minutes", 30)
        if session_age > 1440:  # Session older than 24 hours
            anomaly_score += 0.2

        # Request frequency anomalies
        request_frequency = features.get("recent_request_frequency", 1)
        if request_frequency > 100:  # Very high frequency
            anomaly_score += 0.3

        return min(anomaly_score, 1.0)

    def _find_applicable_rate_limit_rule(self, resource: str) -> Optional[RateLimitRule]:
        """Find applicable rate limiting rule for resource"""
        # Check for exact match first
        for rule in self.rate_limit_rules.values():
            if rule.resource == resource:
                return rule

        # Check for pattern matches
        for rule in self.rate_limit_rules.values():
            if rule.resource.endswith("*"):
                prefix = rule.resource[:-1]
                if resource.startswith(prefix):
                    return rule

        # Return general API rule if available
        return self.rate_limit_rules.get("api_general")

    async def _validate_oauth_credentials(self, credentials: OAuthCredentials) -> dict[str, Any]:
        """Validate OAuth provider credentials"""
        validation_result = {"valid": True, "errors": []}

        # Check required fields
        if not credentials.client_id:
            validation_result["valid"] = False
            validation_result["errors"].append("Client ID is required")

        if not credentials.client_secret:
            validation_result["valid"] = False
            validation_result["errors"].append("Client secret is required")

        if not credentials.redirect_uri:
            validation_result["valid"] = False
            validation_result["errors"].append("Redirect URI is required")

        # Validate redirect URI format
        if credentials.redirect_uri and not credentials.redirect_uri.startswith(
            ("http://", "https://")
        ):
            validation_result["valid"] = False
            validation_result["errors"].append("Redirect URI must be a valid HTTP/HTTPS URL")

        # Validate scopes
        if not credentials.scope:
            validation_result["errors"].append("At least one scope is recommended")

        return validation_result

    async def _exchange_oauth_code(
        self, credentials: OAuthCredentials, auth_code: str, state: str
    ) -> dict[str, Any]:
        """Exchange OAuth authorization code for access token"""
        # In production, this would make actual HTTP requests to OAuth provider
        # For testing, simulate successful token exchange

        await asyncio.sleep(0.1)  # Simulate network delay

        return {
            "success": True,
            "access_token": f"oauth_token_{secrets.token_hex(16)}",
            "refresh_token": f"refresh_token_{secrets.token_hex(16)}",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    async def _get_oauth_user_info(
        self, provider: AuthProvider, access_token: str
    ) -> dict[str, Any]:
        """Get user information from OAuth provider"""
        # In production, this would make actual API calls to get user info
        # For testing, simulate user info retrieval

        await asyncio.sleep(0.1)  # Simulate network delay

        return {
            "success": True,
            "user_id": f"oauth_user_{secrets.token_hex(8)}",
            "data": {
                "email": f"user@{provider.value}.com",
                "name": "Test User",
                "provider": provider.value,
                "verified": True,
            },
        }

    def _check_mfa_requirement(self, user_id: str) -> bool:
        """Check if MFA is required for user"""
        # In production, this would check user settings and security policies
        # For now, require MFA for all users
        return True

    async def _send_verification_code(self, method: MFAMethod, contact_info: str, code: str):
        """Send verification code via specified method"""
        # In production, this would send actual SMS/Email
        # For testing, just log the action

        logger.info(
            "Verification code sent via %s to %s: %s",
            method.value,
            self._mask_contact_info(contact_info),
            code,
        )

    def _mask_contact_info(self, contact_info: str) -> str:
        """Mask contact information for logging"""
        if "@" in contact_info:  # Email
            local, domain = contact_info.split("@")
            return f"{local[:2]}***@{domain}"
        elif contact_info.isdigit():  # Phone number
            return f"***-***-{contact_info[-4:]}"
        else:
            return "***"

    async def _log_security_event(self, event_type: str, data: dict[str, Any]):
        """Log security event for audit trail"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc),
            "data": data,
            "source": "enhanced_security_mcp",
        }

        self.security_events.append(event)

        # Maintain event history size
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-5000:]  # Keep last 5000 events

        logger.debug("Security event logged: %s", event_type)

    async def _log_rate_limit_decision(
        self, user_id: str, resource: str, decision: dict[str, Any], rule: RateLimitRule
    ):
        """Log rate limiting decision"""
        await self._log_security_event(
            "rate_limit_decision",
            {
                "user_id": user_id,
                "resource": resource,
                "allowed": decision.get("allowed", False),
                "reason": decision.get("reason", "unknown"),
                "rule_id": rule.rule_id,
                "limit_type": rule.limit_type.value,
            },
        )

    async def _apply_rate_limit_penalty(self, user_id: str, ip_address: str, rule: RateLimitRule):
        """Apply penalty for rate limit violation"""
        penalty = {
            "user_id": user_id,
            "ip_address": ip_address,
            "rule_id": rule.rule_id,
            "penalty_start": datetime.now(timezone.utc),
            "penalty_end": datetime.now(timezone.utc)
            + timedelta(seconds=rule.penalty_duration_seconds),
            "penalty_type": "temporary_ban",
        }

        self.rate_limit_violations.append(penalty)

        await self._log_security_event("rate_limit_violation", penalty)

        logger.warning(
            "Rate limit penalty applied to user %s for %d seconds",
            user_id,
            rule.penalty_duration_seconds,
        )

    def _categorize_resource(self, resource: str) -> str:
        """Categorize API resource for analysis"""
        if "/auth/" in resource:
            return "authentication"
        elif "/content/" in resource:
            return "content_generation"
        elif "/quiz/" in resource:
            return "assessment"
        elif "/roblox/" in resource:
            return "roblox_integration"
        else:
            return "general"

    def _categorize_user_agent(self, user_agent: str) -> str:
        """Categorize user agent for analysis"""
        user_agent_lower = user_agent.lower()

        if "bot" in user_agent_lower or "crawler" in user_agent_lower:
            return "bot"
        elif (
            "mobile" in user_agent_lower
            or "android" in user_agent_lower
            or "iphone" in user_agent_lower
        ):
            return "mobile"
        elif (
            "chrome" in user_agent_lower
            or "firefox" in user_agent_lower
            or "safari" in user_agent_lower
        ):
            return "browser"
        else:
            return "unknown"

    async def _get_ip_reputation(self, ip_address: str) -> float:
        """Get IP address reputation score"""
        # In production, this would query IP reputation services
        # For testing, return a simulated score

        # Simple heuristic based on IP pattern
        if ip_address.startswith("127.") or ip_address.startswith("192.168."):
            return 0.9  # Local/private IPs are trusted
        elif ip_address.startswith("10."):
            return 0.8  # Private network
        else:
            return 0.6  # Unknown public IP

    def _get_session_age(self, session_id: str) -> float:
        """Get session age in minutes"""
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            created_at = session.get("created_at", datetime.now(timezone.utc))
            age = datetime.now(timezone.utc) - created_at
            return age.total_seconds() / 60
        return 0.0

    async def _get_recent_request_frequency(self, user_id: str) -> int:
        """Get recent request frequency for user"""
        # Count requests in last 5 minutes
        recent_events = [
            event
            for event in self.security_events
            if (
                event.get("data", {}).get("user_id") == user_id
                and event["timestamp"] > datetime.now(timezone.utc) - timedelta(minutes=5)
            )
        ]

        return len(recent_events)

    def get_security_metrics(self) -> dict[str, Any]:
        """Get comprehensive security metrics"""
        current_time = datetime.now(timezone.utc)

        # Active sessions metrics
        active_sessions_count = len(self.active_sessions)
        mfa_verified_sessions = sum(
            1 for session in self.active_sessions.values() if session.get("mfa_verified", False)
        )

        # OAuth metrics
        oauth_providers_configured = len(self.oauth_providers)

        # MFA metrics
        mfa_users = len(self.mfa_setups)
        active_mfa_users = sum(1 for setup in self.mfa_setups.values() if setup.is_active)

        # Rate limiting metrics
        rate_limit_rules_count = len(self.rate_limit_rules)
        recent_violations = len(
            [v for v in self.rate_limit_violations if v["penalty_end"] > current_time]
        )

        # Security events metrics
        recent_events = [
            e for e in self.security_events if e["timestamp"] > current_time - timedelta(hours=24)
        ]

        event_types = {}
        for event in recent_events:
            event_type = event["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "sessions": {
                "active_sessions": active_sessions_count,
                "mfa_verified_sessions": mfa_verified_sessions,
                "mfa_verification_rate": (
                    mfa_verified_sessions / active_sessions_count
                    if active_sessions_count > 0
                    else 0
                ),
            },
            "oauth": {
                "providers_configured": oauth_providers_configured,
                "providers": [p.value for p in self.oauth_providers.keys()],
            },
            "mfa": {
                "users_with_mfa": mfa_users,
                "active_mfa_users": active_mfa_users,
                "mfa_adoption_rate": active_mfa_users / mfa_users if mfa_users > 0 else 0,
            },
            "rate_limiting": {
                "rules_configured": rate_limit_rules_count,
                "active_violations": recent_violations,
                "violation_rate": recent_violations / max(len(recent_events), 1),
            },
            "security_events": {
                "events_last_24h": len(recent_events),
                "event_types": event_types,
                "total_events_stored": len(self.security_events),
            },
            "system_health": {
                "security_score": self._calculate_security_score(),
                "threat_level": self._assess_threat_level(),
                "compliance_status": self._check_compliance_status(),
            },
        }

    def _calculate_security_score(self) -> float:
        """Calculate overall security score"""
        score = 0.5  # Base score

        # OAuth configuration bonus
        if len(self.oauth_providers) > 0:
            score += 0.1

        # MFA adoption bonus
        if len(self.mfa_setups) > 0:
            score += 0.2

        # Rate limiting configuration bonus
        if len(self.rate_limit_rules) >= 3:
            score += 0.1

        # Recent violations penalty
        recent_violations = len(
            [v for v in self.rate_limit_violations if v["penalty_end"] > datetime.now(timezone.utc)]
        )

        if recent_violations > 0:
            score -= min(0.3, recent_violations * 0.1)

        # Security events analysis
        recent_events = [
            e
            for e in self.security_events
            if e["timestamp"] > datetime.now(timezone.utc) - timedelta(hours=24)
        ]

        failed_events = [e for e in recent_events if "failed" in e["event_type"]]
        if len(recent_events) > 0:
            failure_rate = len(failed_events) / len(recent_events)
            score -= failure_rate * 0.2

        return max(0.0, min(1.0, score))

    def _assess_threat_level(self) -> str:
        """Assess current threat level"""
        security_score = self._calculate_security_score()
        recent_violations = len(
            [v for v in self.rate_limit_violations if v["penalty_end"] > datetime.now(timezone.utc)]
        )

        if security_score < 0.3 or recent_violations > 10:
            return "high"
        elif security_score < 0.6 or recent_violations > 5:
            return "medium"
        elif security_score < 0.8 or recent_violations > 1:
            return "low"
        else:
            return "minimal"

    def _check_compliance_status(self) -> str:
        """Check compliance with security standards"""
        compliance_checks = {
            "oauth_configured": len(self.oauth_providers) > 0,
            "mfa_available": len(self.mfa_setups) > 0,
            "rate_limiting_active": len(self.rate_limit_rules) > 0,
            "audit_logging_enabled": len(self.security_events) > 0,
            "session_management": len(self.active_sessions) >= 0,
        }

        compliance_score = sum(compliance_checks.values()) / len(compliance_checks)

        if compliance_score >= 0.9:
            return "fully_compliant"
        elif compliance_score >= 0.7:
            return "mostly_compliant"
        elif compliance_score >= 0.5:
            return "partially_compliant"
        else:
            return "non_compliant"
