# Security Implementation Guide - Week 3

## 📋 Table of Contents

1. [Overview](#overview)
2. [HashiCorp Vault Integration](#hashicorp-vault-integration)
3. [Authentication & Authorization](#authentication--authorization)
4. [PII Encryption](#pii-encryption)
5. [GDPR Compliance](#gdpr-compliance)
6. [Security Headers](#security-headers)
7. [Pre-commit Security Hooks](#pre-commit-security-hooks)
8. [Testing](#testing)
9. [Deployment Checklist](#deployment-checklist)

## Overview

This document covers the comprehensive security implementation completed in Week 3 of the ToolBoxAI project. All implementations follow 2025 security best practices and are Python 3.12+ compatible.

### Key Security Features

- 🔐 **HashiCorp Vault**: Centralized secret management with automatic rotation
- 🎫 **JWT with RS256**: Cryptographically signed tokens using public/private key pairs
- 👮 **RBAC**: Fine-grained role-based access control with 9 predefined roles
- 🔒 **PII Encryption**: AES-256-GCM field-level encryption for personal data
- 📜 **GDPR Compliance**: Full compliance with right to erasure, portability, and consent management
- 🛡️ **Security Headers**: Comprehensive headers including HSTS, CSP, and X-Frame-Options
- 🚨 **Pre-commit Hooks**: Automated security scanning before code commits

## HashiCorp Vault Integration

### Configuration

Vault is configured for high availability with automatic secret rotation every 30 days.

```bash
# Environment variables required
export VAULT_ADDR='https://vault.toolboxai.local:8200'
export VAULT_ROLE_ID='your-role-id'
export VAULT_SECRET_ID='your-secret-id'
export VAULT_NAMESPACE='toolboxai'
export VAULT_ENABLED='true'
```

### Usage in Code

```python
from apps.backend.services.vault_manager import get_vault_manager

vault = get_vault_manager()

# Store secret
vault.set_secret("apps/backend/api_keys/service", {
    "api_key": "sk_live_...",
    "created_at": datetime.now().isoformat()
})

# Retrieve secret
api_key = vault.get_secret("apps/backend/api_keys/service", "api_key")

# Rotate secret
vault.rotate_secret("apps/backend/api_keys/service")

# Get dynamic database credentials (auto-expire)
creds = vault.get_dynamic_database_credentials("postgres", ttl="24h")
db_url = f"postgresql://{creds['username']}:{creds['password']}@localhost/toolboxai"
```

### Secret Migration

Migrate existing hardcoded secrets to Vault:

```bash
# Dry run to identify secrets from .env (report written to JSON)
python scripts/vault/migrate_secrets.py \
  --plan scripts/vault/examples/migration_plan.example.json \
  --dry-run \
  --output-report secrets_report.json

# Perform actual migration
python scripts/vault/migrate_secrets.py \
  --plan scripts/vault/examples/migration_plan.example.json

# Rotate all secrets that are due and a specific path
python scripts/vault/rotate_secrets.py --all
python scripts/vault/rotate_secrets.py --path apps/backend/secrets/openai
```

### Automated Rotation Workflow

A dedicated GitHub Actions workflow (`.github/workflows/vault-rotation.yml`) runs nightly at 03:15 UTC to execute `scripts/vault/rotate_secrets.py --all`. It requires the Vault credentials (`VAULT_ADDR`, `VAULT_ROLE_ID`, `VAULT_SECRET_ID`, `VAULT_NAMESPACE`) to be stored as encrypted repository secrets. Monitor the workflow results in GitHub Actions and configure alerts for failures.

### Secret Detection Guardrail

Run the lightweight secret scanner before committing or in CI:

```bash
# Scan entire repo using default patterns and allowlist
python scripts/security/check_secrets.py --root . --allowlist scripts/security/allowlist.txt --fail-on-detect
```

Allowlist entries live in `scripts/security/allowlist.txt`; add only intentional exceptions (for example, a committed `.env` used for local development).
The script is wired into `.pre-commit-config.yaml` (hook id `toolboxai-secret-scanner`) and the GitHub `security-pipeline` workflow so the same rules run locally and in CI.

### Dependencies

Install the tools required for Vault automation (these can be added to your local virtualenv or CI image):

```bash
pip install hvac
```

> The CLI scripts lazily import `apps.backend.services.vault_manager`. Ensure the repository root is on `PYTHONPATH` (for example, run from project root or set `PYTHONPATH=. python scripts/...`).

### Vault Features

- **Automatic Key Rotation**: Every 30 days for API keys, 7 days for JWT keys
- **Dynamic Database Credentials**: Temporary credentials that auto-expire
- **Encryption as a Service**: Use Vault's Transit engine for data encryption
- **Audit Logging**: All secret access is logged for compliance
- **High Availability**: Raft consensus with multiple nodes

## Authentication & Authorization

### JWT Configuration (RS256)

The system uses RS256 (RSA with SHA-256) for stronger security than HS256.

```python
from apps.backend.core.auth.jwt_manager import get_jwt_manager

jwt_manager = get_jwt_manager()

# Create access token with permissions
access_token = jwt_manager.create_access_token(
    user_id="user123",
    username="john.doe",
    roles=["teacher"],
    permissions=["content:read:all", "content:write:own", "class:manage:own"]
)

# Create refresh token
refresh_token = jwt_manager.create_refresh_token(
    user_id="user123",
    username="john.doe"
)

# Verify token with permission check
is_valid, claims = jwt_manager.verify_token(
    token=access_token,
    token_type="access",
    verify_permissions=["content:read:all"]
)

# Refresh tokens
new_access, new_refresh = jwt_manager.refresh_access_token(refresh_token)

# Revoke token (blacklist)
jwt_manager.revoke_token(access_token)
```

### RBAC (Role-Based Access Control)

Nine predefined roles with hierarchical permissions:

```python
from apps.backend.core.auth.rbac_manager import get_rbac_manager, Role

rbac = get_rbac_manager()

# Check permission
has_permission = rbac.check_permission(
    user_roles=[Role.TEACHER],
    required_permission="content:create:own",
    context={"school_id": "school123"}
)

# Get all permissions for roles
permissions = rbac.get_user_permissions([Role.TEACHER, Role.CONTENT_CREATOR])
```

#### Role Hierarchy

1. **SUPER_ADMIN**: Full system access
2. **ADMIN**: Administrative access except super admin functions
3. **TEACHER**: Manage classes and educational content
4. **STUDENT**: Access learning materials and take assessments
5. **PARENT**: Monitor student progress
6. **CONTENT_CREATOR**: Create and manage educational content
7. **MODERATOR**: Review and moderate content
8. **VIEWER**: Read-only access
9. **API_USER**: Programmatic access for integrations

#### Permission Format

`resource:action:scope`

- **Resources**: user, content, class, assessment, report, settings, api, admin, roblox, analytics
- **Actions**: create, read, update, delete, execute, approve, publish, export, import
- **Scopes**: own (user's own), team (organization), all (system-wide)

## PII Encryption

### Field-Level Encryption

Protect personally identifiable information with AES-256-GCM:

```python
from apps.backend.core.security.pii_encryption import get_pii_manager, PIIField

pii_manager = get_pii_manager()

# Encrypt single field
encrypted = pii_manager.encrypt_field(
    value="user@example.com",
    field_type=PIIField.EMAIL
)

# Decrypt field
plaintext = pii_manager.decrypt_field(encrypted)

# Encrypt entire document
user_doc = {
    "user_id": "123",
    "email": "user@example.com",
    "phone": "555-123-4567",
    "ssn": "123-45-6789",
    "address": "123 Main St"
}

field_mappings = {
    "email": PIIField.EMAIL,
    "phone": PIIField.PHONE,
    "ssn": PIIField.SSN,
    "address": PIIField.ADDRESS
}

encrypted_doc = pii_manager.encrypt_document(user_doc, field_mappings)

# Search encrypted data (blind indexing)
search_index = pii_manager.search_encrypted("user@example.com", PIIField.EMAIL)
# Use search_index to query database without decryption
```

### Supported PII Fields

- EMAIL
- PHONE
- SSN
- CREDIT_CARD
- BANK_ACCOUNT
- PASSPORT
- DRIVER_LICENSE
- FULL_NAME
- ADDRESS
- DATE_OF_BIRTH
- MEDICAL_RECORD
- IP_ADDRESS
- BIOMETRIC

### Key Rotation

```python
# Rotate encryption keys
pii_manager.rotate_encryption_key()
# Old data can still be decrypted with versioned keys
```

## GDPR Compliance

### Consent Management

```python
from apps.backend.core.compliance.gdpr_manager import get_gdpr_manager, ConsentType

gdpr = get_gdpr_manager()

# Record consent
await gdpr.record_consent(
    user_id="user123",
    consent_type=ConsentType.ANALYTICS,
    granted=True,
    purpose="Analytics for service improvement",
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent"),
    duration_days=365
)

# Check consent
has_consent = await gdpr.check_consent("user123", ConsentType.MARKETING)

# Get consent history
history = gdpr.get_consent_history("user123")
```

### Right to Erasure (Right to be Forgotten)

```python
# Process erasure request
request = await gdpr.process_erasure_request(
    user_id="user123",
    verification_token="token_xyz"  # Email verification
)

# Check status
status = gdpr.get_request_status(request.request_id)
```

### Data Portability

```python
# Export user data
package = await gdpr.process_portability_request(
    user_id="user123",
    format="json"  # or "csv"
)

# package contains:
# - filename: gdpr_export_user123_20250928.zip
# - content: ZIP with all user data
# - mime_type: application/zip
```

### Data Retention Policies

```python
# Process retention policies (delete old data)
deletion_counts = await gdpr.process_retention_policies()
# Automatically deletes/anonymizes data based on configured policies
```

### Compliance Verification

```python
# Verify GDPR compliance for user
report = await gdpr.verify_compliance("user123")
# Returns compliance score and pending requests
```

## API Key Security (Updated Sept 28, 2025)

### Best Practices Implemented

The system follows strict API key security practices:

1. **Environment Variables Only**: All API keys stored exclusively in `.env` file
2. **No Hardcoding**: Zero hardcoded credentials in source code
3. **Documentation Safety**: Documentation uses placeholder values only
4. **Docker Security**: Docker Compose references environment variables without defaults

### LangChain API Key Management

```python
# Correct implementation (secure)
from core.agents.config import LangChainConfiguration

class LangChainConfiguration:
    def __init__(self):
        # Load from environment only
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project_id = os.getenv("LANGCHAIN_PROJECT_ID")
        # Never hardcode values
```

### Environment Configuration

```bash
# .env file (never commit this file)
LANGCHAIN_API_KEY=your-actual-key-here
LANGCHAIN_PROJECT_ID=your-actual-project-id
OPENAI_API_KEY=your-openai-key
PUSHER_SECRET=your-pusher-secret

# .env.example (safe to commit)
LANGCHAIN_API_KEY=your-langchain-api-key-here
LANGCHAIN_PROJECT_ID=your-project-id-here
OPENAI_API_KEY=your-openai-key-here
PUSHER_SECRET=your-pusher-secret-here
```

### Docker Security

```yaml
# Docker Compose (secure)
environment:
  LANGCHAIN_API_KEY: "${LANGCHAIN_API_KEY}"  # No default value
  OPENAI_API_KEY: "${OPENAI_API_KEY}"        # No default value
```

### Security Audit Commands

```bash
# Verify no exposed keys in codebase
grep -r "sk_" . --exclude-dir=node_modules --exclude=".env"

# Check for hardcoded secrets
grep -r "api_key.*=" . --exclude-dir=node_modules --exclude=".env" | grep -v "os.getenv"

# Scan with security tools
trufflehog filesystem . --exclude-paths=.gitignore
```

## Security Headers

### Middleware Configuration

```python
from apps.backend.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=True,
    enable_csp=True,
    frame_options="DENY",
    enable_nonce=True,
    report_uri="https://toolboxai.report-uri.com/r/d/csp/enforce"
)
```

### Headers Applied

| Header | Value | Purpose |
|--------|-------|---------|
| Strict-Transport-Security | max-age=31536000; includeSubDomains; preload | Force HTTPS |
| Content-Security-Policy | default-src 'self'; ... | Prevent XSS |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-XSS-Protection | 1; mode=block | Legacy XSS protection |
| Referrer-Policy | strict-origin-when-cross-origin | Control referrer |
| Permissions-Policy | camera=(), microphone=(), ... | Limit features |

### CSP Nonce for Inline Scripts

```python
# In route handler
@app.get("/page")
async def page(request: Request):
    nonce = request.state.csp_nonce  # Auto-generated
    return templates.TemplateResponse("page.html", {
        "request": request,
        "csp_nonce": nonce
    })
```

```html
<!-- In template -->
<script nonce="{{ csp_nonce }}">
    // Inline script allowed with nonce
</script>
```

### Secure Error Handling

```python
from apps.backend.middleware.security_headers import handle_api_error

try:
    # Your code
    pass
except Exception as e:
    # Returns sanitized error without sensitive data
    return handle_api_error(e, request)
```

## Pre-commit Security Hooks

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

### Security Checks Performed

1. **Secret Detection** (detect-secrets)
   - Scans for hardcoded API keys, passwords, tokens
   - Uses entropy analysis and pattern matching

2. **Python Security** (bandit)
   - SQL injection vulnerabilities
   - Insecure random usage
   - Hardcoded passwords
   - Shell injection risks

3. **Dependency Scanning** (safety, pip-audit)
   - Checks for known vulnerabilities in dependencies
   - Suggests secure versions

4. **Custom Checks**
   - PII exposure detection
   - GDPR compliance verification
   - Security header validation
   - License compliance

### Bypassing Hooks (Emergency Only)

```bash
# Skip hooks in emergency (NOT RECOMMENDED)
git commit --no-verify

# Skip specific hook
SKIP=bandit git commit

# Mark false positive in code
password = "example"  # pragma: allowlist secret
```

## Testing

### Running Security Tests

```bash
# Run all security tests
pytest tests/security/ -v

# Run specific test categories
pytest tests/security/test_week3_security.py::TestVaultManager -v
pytest tests/security/test_week3_security.py::TestJWTManager -v
pytest tests/security/test_week3_security.py::TestRBACManager -v
pytest tests/security/test_week3_security.py::TestPIIEncryption -v
pytest tests/security/test_week3_security.py::TestGDPRCompliance -v

# Run with coverage
pytest tests/security/ --cov=apps.backend.core.security --cov-report=html
```

### Test Coverage Areas

- ✅ Vault integration and secret management
- ✅ JWT token generation and verification
- ✅ RBAC permission checking
- ✅ PII encryption/decryption
- ✅ GDPR consent and erasure
- ✅ Security headers application
- ✅ Pre-commit hook functionality

## Deployment Checklist

### Environment Variables

```bash
# Required for production
VAULT_ENABLED=true
VAULT_ADDR=https://vault.prod.toolboxai.com:8200
VAULT_ROLE_ID=<from-vault-admin>
VAULT_SECRET_ID=<from-vault-admin>
VAULT_NAMESPACE=toolboxai-prod

JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

PII_ENCRYPTION_ENABLED=true
GDPR_COMPLIANCE_ENABLED=true

# Security headers
ENABLE_HSTS=true
ENABLE_CSP=true
CSP_REPORT_URI=https://toolboxai.report-uri.com/r/d/csp/enforce
```

### Pre-deployment Steps

- [ ] Run security tests: `pytest tests/security/ -v`
- [ ] Run pre-commit hooks: `pre-commit run --all-files`
- [ ] Migrate secrets to Vault: `python scripts/vault/migrate_secrets.py`
- [ ] Verify Vault connectivity: `vault status`
- [ ] Test JWT key rotation: `python -c "from apps.backend.core.auth.jwt_manager import get_jwt_manager; get_jwt_manager().rotate_keys()"`
- [ ] Verify GDPR endpoints: `curl -X GET https://api.toolboxai.com/api/v1/gdpr/compliance/user123`
- [ ] Check security headers: `curl -I https://api.toolboxai.com`
- [ ] Review audit logs for anomalies

### Monitoring

Set up alerts for:

- Failed authentication attempts > 10/minute
- Vault connection failures
- JWT signature verification failures
- GDPR request SLA violations (>30 days)
- CSP violation reports
- Suspicious PII access patterns

## Security Best Practices

### For Developers

1. **Never hardcode secrets** - Use Vault or environment variables
2. **Always validate permissions** - Use RBAC for all sensitive operations
3. **Encrypt PII at rest** - Use PIIEncryptionManager for personal data
4. **Log security events** - Use audit logging for compliance
5. **Run pre-commit hooks** - Never skip security checks
6. **Rotate secrets regularly** - Use automated rotation scripts
7. **Test security features** - Include security tests in CI/CD

### For Operations

1. **Monitor Vault health** - Set up HA with at least 3 nodes
2. **Backup encryption keys** - Store securely with versioning
3. **Review audit logs** - Daily for production environments
4. **Update dependencies** - Weekly security patches
5. **Penetration testing** - Quarterly security assessments
6. **Incident response plan** - Document and practice procedures
7. **Compliance audits** - Annual GDPR compliance review

## Troubleshooting

### Common Issues

#### Vault Connection Failed

```bash
# Check Vault status
vault status

# Verify credentials
vault login -method=approle role_id=$VAULT_ROLE_ID secret_id=$VAULT_SECRET_ID

# Test connectivity
curl -k $VAULT_ADDR/v1/sys/health
```

#### JWT Verification Failed

```python
# Check key version
from apps.backend.core.auth.jwt_manager import get_jwt_manager
manager = get_jwt_manager()
print(f"Current key version: {manager.key_version}")

# Force key refresh
manager._init_keys()
```

#### PII Decryption Failed

```python
# Check key version mismatch
from apps.backend.core.security.pii_encryption import get_pii_manager
manager = get_pii_manager()
print(f"Current key version: {manager.key_version}")

# Retrieve old key for decryption
old_key = manager._get_key_for_version(encrypted_field.key_version)
```

#### GDPR Request Timeout

```python
# Check request status
from apps.backend.core.compliance.gdpr_manager import get_gdpr_manager
gdpr = get_gdpr_manager()
request = gdpr.get_request_status("GDPR-ABC123")
print(f"Status: {request.status}, Deadline: {request.deadline}")
```

## Support

For security issues or questions:

- 🚨 **Security vulnerabilities**: security@toolboxai.com
- 📧 **General support**: support@toolboxai.com
- 📚 **Documentation**: https://docs.toolboxai.com/security
- 🔍 **Audit logs**: Available in Vault UI or via API

---

*Last Updated: September 2025*
*Version: 1.0.0*
*Classification: Internal Use*
