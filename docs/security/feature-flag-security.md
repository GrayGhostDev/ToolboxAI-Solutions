# Security Feature Flag Configuration

This document describes the security-related feature flags and how to properly configure them for different environments.

## Critical Security Features

### Development Authentication Bypass

**Feature Flag**: `DEVELOPMENT_AUTH_BYPASS`
**Default**: `false` (DISABLED)

This feature flag controls whether the development authentication bypass is enabled. When disabled, all authentication must go through proper JWT validation.

#### Enabling Development Bypass (Local Development Only)

The development bypass requires **multiple conditions** to be met:

1. Feature flag must be explicitly enabled
2. `DEBUG=true` in environment
3. `ENVIRONMENT=development`
4. `TESTING=false` (or not set)
5. `DISABLE_AUTH_BYPASS=false` (or not set)

#### Methods to Enable:

**Environment Variable**:
```bash
FF_DEVELOPMENT_AUTH_BYPASS=true
```

**Redis (preferred for runtime control)**:
```bash
redis-cli SET "feature_flag:development_auth_bypass" "true"
```

**Python/Feature Flag Manager**:
```python
from apps.backend.core.feature_flags import get_feature_flags, FeatureFlag
flags = get_feature_flags()
flags.set_flag(FeatureFlag.DEVELOPMENT_AUTH_BYPASS, True)
```

#### IMPORTANT SECURITY NOTES:

- ⚠️ **NEVER enable in production**
- ⚠️ **Multiple safeguards prevent accidental activation**
- ⚠️ **Always verify this is disabled before deploying**
- ⚠️ **Logs warning when bypass is active**

### Test Data Fallback

The system uses dynamically generated test credentials instead of hardcoded passwords.

**Controls**:
- `TESTING=true` - Enables test credential fallback
- `ALLOW_TEST_FALLBACK=true` - Alternative enable flag

**Security Benefits**:
- No hardcoded passwords in source code
- Credentials are generated with secure randomness
- Test data uses proper password hashing
- Deterministic when seeded (for testing consistency)

## CORS Configuration

### Flask Bridge CORS

**File**: `apps/backend/flask_bridge.py`

CORS origins are environment-specific:

#### Development
```
http://localhost:5179
http://localhost:3000
http://localhost:8080
http://127.0.0.1:5179
http://127.0.0.1:3000
http://127.0.0.1:8080
```

#### Staging
```
https://staging.toolboxai.com
https://staging-app.toolboxai.com
http://localhost:5179  # For local testing
http://localhost:3000
```

#### Production
```
https://toolboxai.com
https://www.toolboxai.com
https://app.toolboxai.com
https://dashboard.toolboxai.com
```

Custom origins can be added via `FLASK_CORS_ORIGINS` environment variable (comma-separated).

## Security Checklist

### Before Deployment

1. ✅ Verify `DEVELOPMENT_AUTH_BYPASS` is disabled
2. ✅ Check CORS origins are environment-appropriate
3. ✅ Confirm no hardcoded test credentials
4. ✅ Validate JWT secret is not default value
5. ✅ Ensure Redis is properly secured
6. ✅ Review environment variables for test flags

### Runtime Monitoring

1. Monitor logs for "DEVELOPMENT AUTH BYPASS ACTIVE" warnings
2. Check feature flag status via health endpoints
3. Verify CORS headers in browser developer tools
4. Monitor authentication metrics for unusual patterns

## Environment Configuration Examples

### Development (.env.development)
```bash
DEBUG=true
ENVIRONMENT=development
FF_DEVELOPMENT_AUTH_BYPASS=false  # Only enable when needed
TESTING=false
CORS_ORIGINS=["http://localhost:5179", "http://localhost:3000"]
```

### Testing (.env.testing)
```bash
DEBUG=true
ENVIRONMENT=testing
TESTING=true
FF_DEVELOPMENT_AUTH_BYPASS=false
ALLOW_TEST_FALLBACK=true
```

### Production (.env.production)
```bash
DEBUG=false
ENVIRONMENT=production
FF_DEVELOPMENT_AUTH_BYPASS=false  # CRITICAL: Must be false
TESTING=false
ALLOW_TEST_FALLBACK=false
CORS_ORIGINS=["https://app.toolboxai.com"]
```

## Emergency Procedures

### Disable All Development Features Immediately

```bash
# Via environment variables
export FF_DEVELOPMENT_AUTH_BYPASS=false
export DISABLE_AUTH_BYPASS=true
export TESTING=false
export ALLOW_TEST_FALLBACK=false

# Via Redis
redis-cli SET "feature_flag:development_auth_bypass" "false"
redis-cli DEL "feature_flag:development_auth_bypass"

# Restart services
systemctl restart toolboxai-backend
systemctl restart toolboxai-flask-bridge
```

### Verify Security Status

```bash
# Check feature flag status
curl http://localhost:8009/health/feature-flags

# Check CORS configuration
curl -H "Origin: http://evil.com" http://localhost:5001/health

# Verify authentication requirement
curl http://localhost:8009/api/v1/protected-endpoint
```

## Troubleshooting

### Development Bypass Not Working

1. Check all required conditions are met
2. Verify feature flag is enabled in Redis/environment
3. Check logs for security warnings
4. Ensure not in testing mode (`TESTING=false`)

### CORS Errors

1. Verify origin is in allowed list for environment
2. Check `ENVIRONMENT` variable is set correctly
3. Review Flask bridge logs for CORS configuration
4. Ensure protocol (http/https) matches exactly

### Authentication Failures

1. Verify JWT secret is configured correctly
2. Check token expiration settings
3. Ensure proper database connectivity
4. Review rate limiting configuration

## Security Contact

For security-related issues or questions about these configurations, contact the security team or create a confidential issue in the repository.