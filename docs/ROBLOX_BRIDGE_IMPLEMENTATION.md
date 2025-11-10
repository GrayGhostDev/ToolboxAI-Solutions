# Roblox Bridge Implementation Documentation

## Overview
This document provides comprehensive documentation for the Roblox Bridge integration implemented in September 2025, following the latest Open Cloud API standards with enterprise-grade security.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Security Implementation](#security-implementation)
3. [API Documentation](#api-documentation)
4. [Configuration Guide](#configuration-guide)
5. [Development Workflow](#development-workflow)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Roblox Studio                            │
│  ┌─────────────────┐        ┌──────────────────┐           │
│  │ AI Content      │        │  Rojo Plugin     │           │
│  │ Generator Plugin│        │  (Port 34872)    │           │
│  └────────┬────────┘        └────────┬─────────┘           │
└───────────┼──────────────────────────┼─────────────────────┘
            │ OAuth2/HTTPS              │ Pusher Channels (via Bridge)
            ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Services                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            FastAPI Application (Port 8009)           │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • Roblox Router (/api/v1/roblox/*)                  │  │
│  │  • OAuth2 Authentication (PKCE)                      │  │
│  │  • Content Generation Pipeline                       │  │
│  │  • Rojo Server Management                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Credential       │  │  Encryption      │               │
│  │ Manager          │  │  Service         │               │
│  └──────────────────┘  └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│              External Services                               │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Roblox Open      │  │  Pusher          │               │
│  │ Cloud API        │  │  Channels        │               │
│  └──────────────────┘  └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Key Files and Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| Encryption Service | `apps/backend/services/encryption.py` | AES-256 credential encryption |
| Credential Manager | `apps/backend/services/credential_manager.py` | Secure credential access with audit logging |
| Roblox Router | `apps/backend/routers/roblox.py` | API endpoints for Roblox integration |
| Schemas | `apps/backend/schemas/roblox.py` | Pydantic models for validation |
| Rojo Config | `roblox/Config/default.project.json` | Rojo project configuration |
| Studio Plugin | `roblox/plugins/AIContentGenerator.lua` | Roblox Studio plugin (Pusher via bridge) |
| Environment Config | `.env.local` | Encrypted credentials and settings |

## Security Implementation

### Credential Encryption

All sensitive credentials are encrypted using AES-256 encryption via the Fernet cipher:

```python
# Encryption Process
1. Generate encryption key (44 bytes, base64 encoded)
2. Encrypt credentials using Fernet cipher
3. Store encrypted values in .env.local
4. Decrypt on-demand with audit logging
```

### Security Features

1. **Encryption at Rest**
   - API keys and secrets encrypted with AES-256
   - Encryption key stored separately from encrypted data
   - Support for key rotation

2. **Access Control**
   - Audit logging for all credential access
   - IP whitelisting (configurable)
   - Rate limiting (100 requests/minute default)

3. **OAuth2 Security**
   - PKCE (Proof Key for Code Exchange) implementation
   - State parameter validation (5-minute TTL)
   - Secure token storage with encryption

4. **Request Security**
   - Optional HMAC signature verification
   - HTTPS-only in production
   - CORS configuration for allowed origins

### Audit Logging

All credential access is logged with the following information:
- Timestamp
- Credential type accessed
- Accessor information (IP, user agent)
- Success/failure status
- Stack trace for failures

## API Documentation

### Bridge Endpoints (Plugin ↔ Bridge)

- `POST /register_plugin` — register Studio plugin session
- `POST /unregister_plugin` — unregister plugin session
- `POST /plugin/messages` — long‑poll for realtime messages (Pusher relayed)
- `POST /plugin/send-message` — send plugin event (bridge relays to Pusher)
- `POST /plugin/pusher/send` — alternative send endpoint
- `GET /pusher/status` — realtime health status

Dev note: The backend exposes a minimal dev bridge (disabled by default) if `BRIDGE_DEV_ENABLED=true` or when `ENVIRONMENT=development`. Use this for local parity at `http://127.0.0.1:8009`.

### Authentication Endpoints

### Minimal Bridge Handler (FastAPI Example)

```python
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI()

class Message(BaseModel):
    id: str
    timestamp: float
    plugin_id: str
    studio_id: str
    data: Dict[str, Any]

_SESSIONS: Dict[str, Dict[str, Any]] = {}
_QUEUES: Dict[str, List[Message]] = {}

@app.post('/register_plugin')
def register(payload: Dict[str, Any]):
    sid = payload.get('studio_id') or 'studio'
    pid = f"session_{int(datetime.utcnow().timestamp())}"
    _SESSIONS[pid] = {"studio_id": sid, "created_at": datetime.utcnow().isoformat()}
    _QUEUES.setdefault(pid, [])
    return {"success": True, "session_id": pid}

@app.post('/unregister_plugin')
def unregister(payload: Dict[str, Any]):
    pid = payload.get('session_id')
    _SESSIONS.pop(pid, None)
    _QUEUES.pop(pid, None)
    return {"success": True}

@app.post('/plugin/send-message')
def send_message(msg: Message):
    # Enqueue for demonstration (in production, trigger Pusher here)
    _QUEUES.setdefault(msg.plugin_id, []).append(msg)
    return {"success": True}

@app.post('/plugin/messages')
def poll_messages(payload: Dict[str, Any] = Body(...)):
    pid = payload.get('plugin_id')
    messages = _QUEUES.get(pid, [])
    _QUEUES[pid] = []  # drain
    return {"messages": [m.model_dump() for m in messages]}

@app.get('/pusher/status')
def pusher_status():
    # Report static OK (in production, reflect actual Pusher state)
    return {"connected": True, "cluster": "mt1", "channel": "toolboxai-dev"}
```

#### POST /api/v1/roblox/auth/initiate
Initiates OAuth2 flow with Roblox.

**Request Body:**
```json
{
  "redirect_uri": "http://127.0.0.1:8009/api/v1/roblox/auth/callback",
  "scopes": ["openid", "profile", "asset:read", "asset:write"],
  "state": "optional_state_parameter"
}
```

**Response:**
```json
{
  "authorization_url": "https://authorize.roblox.com/v1/authorize?...",
  "state": "generated_state_token",
  "code_verifier": "pkce_verifier_for_secure_flow",
  "expires_at": "2025-09-28T12:00:00Z"
}
```

#### GET /api/v1/roblox/auth/callback
Handles OAuth2 callback from Roblox.

**Query Parameters:**
- `code`: Authorization code from Roblox
- `state`: State parameter for CSRF validation

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_value",
  "scope": "openid profile asset:read asset:write"
}
```

#### POST /api/v1/roblox/auth/refresh
Refreshes an expired access token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_value"
}
```

#### POST /api/v1/roblox/auth/revoke
Revokes an access or refresh token.

**Request Body:**
```json
{
  "token": "token_to_revoke",
  "token_type_hint": "access_token"
}
```

### Conversation Flow Endpoints

#### POST /api/v1/roblox/conversation/start
Starts the 8-stage conversation flow for content generation.

**Request Body:**
```json
{
  "user_id": "user_123",
  "initial_message": "I want to create a math learning environment",
  "context": {
    "grade_level": 5,
    "subject": "math"
  }
}
```

**Response:**
```json
{
  "session_id": "session_abc123",
  "current_stage": "greeting",
  "message": "Welcome to the ToolboxAI Educational Content Generator!",
  "pusher_channel": "roblox-conversation-session_abc123",
  "created_at": "2025-09-28T10:00:00Z"
}
```

#### POST /api/v1/roblox/conversation/input
Processes user input in the conversation.

**Request Body:**
```json
{
  "session_id": "session_abc123",
  "user_input": "I want students to learn fractions",
  "metadata": {}
}
```

### Rojo Management Endpoints

#### GET /api/v1/roblox/rojo/check
Checks if Rojo is installed and available.

**Response:**
```json
{
  "installed": true,
  "version": "7.5.1",
  "path": "rojo"
}
```

#### GET /api/v1/roblox/rojo/projects
Lists all active Rojo projects.

**Response:**
```json
{
  "projects": [
    {
      "project_id": "proj_123",
      "name": "math-environment",
      "path": "/tmp/rojo_projects/math-environment",
      "port": 34872,
      "status": "running",
      "created_at": "2025-09-28T10:00:00Z",
      "user_id": "user_123"
    }
  ],
  "total": 1
}
```

## Configuration Guide

### Initial Setup

1. **Generate Encrypted Credentials**
   ```bash
   python scripts/generate_encrypted_roblox_config.py
   ```
   This creates `.env.local` with encrypted credentials.

2. **Verify Configuration**
   ```bash
   python test_roblox_simple.py
   ```
   This validates all configuration settings.

### Environment Variables

#### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `ENCRYPTION_KEY` | Fernet encryption key | `<44-byte base64 key>` |
| `ROBLOX_API_KEY_ENCRYPTED` | Encrypted API key | `<encrypted_value>` |
| `ROBLOX_CLIENT_SECRET_ENCRYPTED` | Encrypted client secret | `<encrypted_value>` |
| `ROBLOX_CLIENT_ID` | OAuth2 client ID | `2214511122270781418` |
| `ROBLOX_UNIVERSE_ID` | Target universe ID | `8505376973` |
| `ROJO_SERVER_PORT` | Rojo server port | `34872` |
| `ENABLE_ROBLOX_INTEGRATION` | Enable integration | `true` |

#### Security Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_CREDENTIAL_AUDIT` | Enable audit logging | `true` |
| `CREDENTIAL_CACHE_TTL` | Cache TTL in seconds | `300` |
| `ROBLOX_API_RATE_LIMIT` | Requests per minute | `100` |
| `ENABLE_IP_WHITELIST` | Enable IP restrictions | `true` |
| `ROBLOX_ALLOWED_IPS` | Whitelisted IPs | `127.0.0.1,::1` |

### Rojo Configuration

The Rojo server is configured to run on port 34872 (default for ToolboxAI-Solutions):

```json
{
  "name": "ToolboxAI-Roblox",
  "servePlaceIds": {
    "production": 8505376973
  }
}
```

## Development Workflow

### Starting the Services

1. **Start Backend Server**
   ```bash
   cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
   uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload
   ```

2. **Start Rojo Server**
   ```bash
   rojo serve roblox/Config/default.project.json --port 34872
   ```

3. **Open Roblox Studio**
   - Install the AIContentGenerator plugin
   - Connect to `http://127.0.0.1:8009`
   - Authenticate via OAuth2

### Testing OAuth2 Flow

1. **Initiate Authentication**
   ```bash
   curl -X POST http://127.0.0.1:8009/api/v1/roblox/auth/initiate \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

2. **Open Authorization URL**
   - Copy the `authorization_url` from response
   - Open in browser
   - Authorize the application

3. **Handle Callback**
   - The callback will be handled automatically
   - Access token will be returned

## Testing & Validation

### Unit Tests

Run the test suite:
```bash
pytest tests/test_roblox_integration.py -v
```

### Integration Tests

Test the complete flow:
```bash
python test_roblox_integration.py
```

### Security Tests

Validate security features:
```bash
pytest tests/security/test_roblox_security.py -v
```

### Manual Testing

1. **Test Encryption**
   ```python
   from apps.backend.services.credential_manager import get_credential_manager
   manager = get_credential_manager()
   api_key = manager.get_roblox_api_key()
   print(f"API Key retrieved: {bool(api_key)}")
   ```

2. **Test API Endpoints**
   ```bash
   # Health check
   curl http://127.0.0.1:8009/api/v1/roblox/health

   # Rojo check
   curl http://127.0.0.1:8009/api/v1/roblox/rojo/check
   ```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem:** `ImportError: cannot import name 'PBKDF2' from 'cryptography.hazmat.primitives.kdf.pbkdf2'`

**Solution:** The import has been updated to use `PBKDF2HMAC` instead of `PBKDF2`.

#### 2. Credential Decryption Fails
**Problem:** `Failed to decrypt credential - invalid key or corrupted data`

**Solution:**
- Verify `ENCRYPTION_KEY` is correct
- Check that encrypted values haven't been modified
- Regenerate credentials if needed

#### 3. OAuth2 State Invalid
**Problem:** `Invalid state parameter`

**Solution:**
- State parameters expire after 5 minutes
- Ensure callback is handled promptly
- Check for clock synchronization issues

#### 4. Rate Limit Exceeded
**Problem:** `429 Too Many Requests`

**Solution:**
- Default limit is 100 requests/minute
- Implement exponential backoff
- Increase `ROBLOX_API_RATE_LIMIT` if needed

### Debug Mode

Enable detailed logging:
```python
# In apps/backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Checking Logs

View credential access logs:
```python
from apps.backend.services.credential_manager import get_credential_manager
manager = get_credential_manager()
logs = manager.get_audit_log(limit=10)
for log in logs:
    print(f"{log['accessed_at']}: {log['credential_type']} - {log['success']}")
```

## Production Deployment

### Security Checklist

- [ ] Use different encryption key for production
- [ ] Store credentials in AWS Secrets Manager or HashiCorp Vault
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and alerting
- [ ] Enable rate limiting and DDoS protection
- [ ] Implement log aggregation
- [ ] Set up backup and disaster recovery

### Environment Variables for Production

```env
# Production configuration
ENVIRONMENT=production
DEBUG=false
SECRET_MANAGER=aws_secrets_manager
SECRET_MANAGER_REGION=us-east-1
SECRET_MANAGER_PREFIX=toolboxai/prod/roblox/

# Security
ENABLE_IP_WHITELIST=true
REQUIRE_SIGNATURE=true
OAUTH2_USE_PKCE=true
OAUTH2_TOKEN_ENCRYPTION=true

# Monitoring
SENTRY_DSN=your-sentry-dsn
ENABLE_SECURITY_ALERTS=true
```

### Docker Deployment

```yaml
# docker-compose.prod.yml
services:
  backend:
    image: toolboxai/backend:latest
    environment:
      - ENVIRONMENT=production
    secrets:
      - roblox_api_key
      - roblox_client_secret
      - encryption_key
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Monitoring

1. **Metrics to Track**
   - OAuth2 success rate
   - API response times
   - Credential access frequency
   - Error rates by endpoint

2. **Alerts to Configure**
   - Failed authentication attempts > 5/minute
   - API errors > 1% of requests
   - Response time > 2 seconds
   - Credential rotation due

## Maintenance

### Key Rotation

Rotate encryption keys quarterly:
```python
from apps.backend.services.encryption import EncryptionKeyManager
manager = EncryptionKeyManager()
new_version = manager.rotate_keys()
print(f"Keys rotated to version {new_version}")
```

### Credential Updates

Update Roblox credentials:
```python
from apps.backend.services.credential_manager import get_credential_manager
manager = get_credential_manager()
manager.rotate_credentials(
    CredentialType.ROBLOX_API_KEY,
    "new_api_key_value"
)
```

### Database Cleanup

Remove old OAuth2 states:
```sql
DELETE FROM oauth2_states
WHERE created_at < NOW() - INTERVAL '1 day';
```

## API Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `/auth/initiate` | 10 | 1 minute |
| `/auth/callback` | 20 | 1 minute |
| `/conversation/*` | 100 | 1 minute |
| `/rojo/*` | 50 | 1 minute |

## Compliance

### GDPR Compliance
- User data encrypted at rest
- Audit logs for data access
- Data retention policies implemented
- User data deletion on request

### Security Standards
- OWASP Top 10 compliance
- OAuth2 best practices (RFC 6749)
- PKCE implementation (RFC 7636)
- Secure credential storage (NIST 800-57)

## Support

### Getting Help
1. Check this documentation
2. Review error logs
3. Run diagnostic tests
4. Contact support with correlation ID

### Useful Commands

```bash
# Check system status
curl http://127.0.0.1:8009/api/v1/roblox/health

# View recent logs
tail -f logs/roblox_integration.log

# Test configuration
python test_roblox_simple.py

# Validate credentials
python -c "from apps.backend.services.credential_manager import get_credential_manager; m = get_credential_manager(); print('OK' if m.get_roblox_api_key() else 'FAIL')"
```

---

*Last Updated: September 28, 2025*
*Version: 1.0.0*
*Status: Production Ready*
