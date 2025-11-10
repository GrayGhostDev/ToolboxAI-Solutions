# HashiCorp Vault Setup and Operations Guide

**Last Updated:** November 2025
**Status:** Production-Ready
**Version:** Vault 1.15.6

---

## Overview

### What Vault Does for ToolBoxAI

HashiCorp Vault provides centralized secret management for the ToolBoxAI platform with:

- **Dynamic Secret Generation**: Database credentials created on-demand with automatic expiration
- **Secret Versioning**: KV v2 engine tracks all secret changes with rollback capability
- **Access Control**: Fine-grained policies limit what each service can access
- **Audit Logging**: Complete audit trail of all secret operations
- **Automatic Rotation**: Scheduled rotation of credentials without service interruption
- **Encryption as a Service**: Transit engine for encrypting application data

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vault Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐           ┌──────────┐           ┌──────────┐    │
│  │ Backend  │──Token────▶│  Vault   │───Audit───▶│  Logs  │    │
│  │ Service  │◀──Secret───│(Port8200)│           │          │    │
│  └──────────┘           └──────────┘           └──────────┘    │
│                              │                                   │
│                         Policies                                │
│                              │                                   │
│      ┌───────────────────────┼───────────────────────┐         │
│      │                       │                       │          │
│  ┌───▼────┐            ┌─────▼─────┐          ┌─────▼─────┐  │
│  │KV v2   │            │Database   │          │Transit    │  │
│  │Secrets │            │Engine     │          │Encryption │  │
│  │        │            │(Dynamic   │          │Engine     │  │
│  │API Keys│            │ Creds)    │          │           │  │
│  │JWT Keys│            │           │          │           │  │
│  └────────┘            └───────────┘          └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Security Benefits

1. **Eliminates Hardcoded Secrets**: No credentials in code or .env files
2. **Short-Lived Credentials**: Database passwords expire automatically (1h TTL)
3. **Principle of Least Privilege**: Each service only accesses what it needs
4. **Complete Audit Trail**: Every secret access is logged
5. **Automatic Rotation**: Credentials rotate without manual intervention
6. **Encrypted Storage**: All secrets encrypted at rest and in transit

---

## Prerequisites

### Required Software
- Docker 25.x or higher
- Docker Compose v2
- `jq` command-line tool (for JSON parsing)
- `curl` or `wget` for health checks

### Required Access
- Access to Vault service (port 8200)
- Docker daemon permissions
- Vault unsealing keys (production only)
- Root token or AppRole credentials

### Environment Variables

```bash
# Required
VAULT_ADDR=http://vault:8200        # Vault server address
VAULT_TOKEN=<your-token-here>        # Authentication token

# Optional
VAULT_NAMESPACE=                     # Vault namespace (Enterprise only)
VAULT_SKIP_VERIFY=false              # Skip TLS verification (dev only)
```

---

## Quick Start

### Development Mode (In-Memory)

```bash
# Start Vault in development mode
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d vault

# Verify Vault is running
docker exec toolboxai-vault vault status

# Dev mode root token is: devtoken
export VAULT_TOKEN=devtoken

# Test secret operations
docker exec -e VAULT_TOKEN=devtoken toolboxai-vault \\
  vault kv put secret/test message="Hello Vault"

docker exec -e VAULT_TOKEN=devtoken toolboxai-vault \\
  vault kv get secret/test
```

### Production Mode (Persistent Storage)

```bash
# Start Vault in production mode
docker compose up -d vault

# Initialize Vault (FIRST TIME ONLY)
docker exec toolboxai-vault vault operator init

# Save the output! You'll receive:
# - 5 unseal keys
# - 1 root token

# Unseal Vault (requires 3 of 5 keys)
docker exec toolboxai-vault vault operator unseal <key1>
docker exec toolboxai-vault vault operator unseal <key2>
docker exec toolboxai-vault vault operator unseal <key3>

# Verify Vault is unsealed
docker exec toolboxai-vault vault status

# Login with root token
docker exec -e VAULT_TOKEN=<root-token> toolboxai-vault \\
  vault login <root-token>
```

---

## Initial Setup (First Time Only)

### Step 1: Initialize Vault

**Run the initialization script:**

```bash
cd infrastructure/vault/scripts
chmod +x init-vault.sh
./init-vault.sh
```

This script will:
1. Check if Vault is running
2. Initialize Vault with 5 key shares (threshold: 3)
3. Save unseal keys to `.vault-keys.json` (**KEEP SECURE!**)
4. Unseal Vault automatically
5. Create security policies (backend, admin, rotation)
6. Enable KV v2 secrets engine
7. Enable database secrets engine
8. Configure PostgreSQL connection
9. Create database role for dynamic credentials

**Output Example:**
```
============================================
Vault Initialization
============================================
✅ Vault is ready
📝 Initializing Vault...
✅ Vault initialized
⚠️  IMPORTANT: Unseal keys and root token saved to: /infrastructure/vault/scripts/../.vault-keys.json
⚠️  Keep this file secure and back it up!

🔓 Unsealing Vault (3 of 5 keys required)...
✅ Vault unsealed

📋 Configuring Vault...
1. Enabling KV v2 secrets engine...
2. Enabling database secrets engine...
3. Creating policies...
   ✅ Backend policy created
   ✅ Admin policy created
   ✅ Rotation policy created
4. Configuring PostgreSQL connection...
   ✅ PostgreSQL connection configured
5. Creating database role...
   ✅ Database role created (TTL: 1h, Max: 24h)

✅ Vault initialization complete!
```

### Step 2: Populate Secrets

**Migrate existing secrets from .env file:**

```bash
cd infrastructure/vault/scripts
chmod +x populate-secrets.sh
./populate-secrets.sh
```

This script migrates:
- Backend API secrets (JWT, encryption keys)
- Database credentials (PostgreSQL, Redis)
- API keys (OpenAI, Anthropic)
- Integration secrets (Pusher, Roblox, LangChain)

**Output Example:**
```
============================================
Vault Secret Population
============================================
📁 Reading secrets from: /infrastructure/docker/compose/.env

📝 Populating secrets...

1. Backend API secrets...
   ✅ API secrets stored
2. Database secrets...
   ✅ Database secrets stored
3. Redis secrets...
   ✅ Redis secrets stored
4. OpenAI integration...
   ✅ OpenAI secrets stored
5. Pusher integration...
   ✅ Pusher secrets stored
6. Roblox integration...
   ⏭️  Skipping Roblox (ROBLOX_API_KEY not found)
7. LangChain/LangSmith integration...
   ⏭️  Skipping LangChain (LANGCHAIN_API_KEY not found)

✅ All secrets populated successfully!
```

### Step 3: Create Service Tokens

**Create backend service token:**

```bash
docker exec -e VAULT_TOKEN=<root-token> toolboxai-vault \\
  vault token create -policy=backend -period=24h -format=json
```

**Add token to .env file:**

```bash
# In .env file
VAULT_ENABLED=true
VAULT_TOKEN=<backend-service-token>
```

---

## Secret Paths and Structure

### Database Secrets

#### PostgreSQL
**Path:** `secret/backend/database`

```json
{
  "url": "postgresql://user:pass@postgres:5432/toolboxai",
  "password": "<secure-password>"
}
```

**Access:**
```bash
vault kv get secret/backend/database
```

#### Redis
**Path:** `secret/backend/redis`

```json
{
  "url": "redis://:password@redis:6379/0",
  "password": "<secure-password>"
}
```

### API Keys and Integrations

#### OpenAI
**Path:** `secret/integrations/openai`

```json
{
  "api_key": "sk-proj-...",
  "organization": "org-..."
}
```

#### Pusher Channels
**Path:** `secret/integrations/pusher`

```json
{
  "app_id": "2050003",
  "key": "...",
  "secret": "...",
  "cluster": "us2",
  "ssl": "true"
}
```

#### Roblox
**Path:** `secret/integrations/roblox`

```json
{
  "api_key": "...",
  "cookie": "..."
}
```

#### LangChain/LangSmith
**Path:** `secret/integrations/langchain`

```json
{
  "api_key": "...",
  "project": "ToolboxAI-Solutions",
  "tracing_v2": "true"
}
```

### Backend Authentication Secrets

**Path:** `secret/backend/api`

```json
{
  "jwt_secret": "<256-bit-secret>",
  "encryption_key": "<encryption-key>"
}
```

---

## Operations

### Reading Secrets

#### Via CLI

```bash
# Read entire secret
vault kv get secret/backend/api

# Read specific field
vault kv get -field=jwt_secret secret/backend/api

# Read as JSON
vault kv get -format=json secret/backend/api | jq .data.data
```

#### Via Python Backend

```python
from apps.backend.services.vault_manager import VaultManager

# Initialize VaultManager
vault = VaultManager()

# Get database credentials
db_secret = vault.get_secret("backend/database")
db_url = db_secret.get("url")

# Get API key
openai_secret = vault.get_secret("integrations/openai")
api_key = openai_secret.get("api_key")

# Get specific field
jwt_secret = vault.get_secret("backend/api", key="jwt_secret")
```

#### Via HTTP API

```bash
# Get secret
curl -H "X-Vault-Token: $VAULT_TOKEN" \\
  http://localhost:8200/v1/secret/data/backend/api

# Response
{
  "data": {
    "data": {
      "jwt_secret": "...",
      "encryption_key": "..."
    },
    "metadata": {
      "created_time": "2025-11-09T...",
      "version": 1
    }
  }
}
```

### Writing Secrets

#### Via CLI

```bash
# Write new secret
vault kv put secret/backend/api \\
  jwt_secret="new-secret-key" \\
  encryption_key="new-encryption-key"

# Update single field (preserves others)
vault kv patch secret/backend/api \\
  jwt_secret="updated-secret"
```

#### Via Python Backend

```python
from apps.backend.services.vault_manager import VaultManager

vault = VaultManager()

# Write new secret
vault.set_secret("backend/custom", {
    "api_key": "custom-key",
    "endpoint": "https://api.example.com"
})

# Write with metadata
from apps.backend.services.vault_manager import SecretMetadata, SecretType

metadata = SecretMetadata(
    name="custom-api",
    path="backend/custom",
    type=SecretType.API_KEY,
    rotation_period_days=90,
    description="Custom API integration"
)

vault.set_secret("backend/custom", data, metadata=metadata)
```

### Secret Rotation

#### Automated Rotation

```bash
# Run rotation script (recommended: weekly cron job)
cd infrastructure/vault/scripts
chmod +x rotate-secrets.sh
./rotate-secrets.sh
```

**Output Example:**
```
============================================
Vault Secret Rotation
============================================
Container: toolboxai-vault

🔍 Current database credentials:
   Username: v-token-toolboxai-abc123def456
   Lease duration: 3600s (1h)

🔄 Rotating database credentials...
✅ Database credentials rotated

🔑 New credentials:
   Username: v-token-toolboxai-xyz789ghi012
   Password: A1B2C3D4... (masked)
   Lease duration: 3600s (1h)
   Expires: 2025-11-10 05:00:00

🧪 Testing new credentials...
   ✅ New credentials work correctly

✅ Rotation complete!
```

#### Manual Rotation

```bash
# Rotate database role
vault write -f database/rotate-role/toolboxai

# Get new credentials
vault read database/creds/toolboxai
```

### Dynamic Database Credentials

**How it works:**
1. Backend requests credentials from Vault
2. Vault generates temporary PostgreSQL user
3. Credentials returned with 1h TTL
4. Backend uses credentials for database connections
5. After 1h, credentials automatically expire and are revoked

**Request credentials:**

```bash
# Via CLI
vault read database/creds/toolboxai

# Output
Key                Value
---                -----
lease_id           database/creds/toolboxai/abc123
lease_duration     1h
username           v-token-toolboxai-xyz789
password           A1b2C3d4E5f6...
```

**Via Python:**

```python
vault = VaultManager()
creds = vault.get_dynamic_database_credentials("toolboxai", ttl="1h")

# Returns:
# {
#   'username': 'v-token-toolboxai-xyz789',
#   'password': 'A1b2C3d4E5f6...',
#   'expires_at': datetime(2025, 11, 10, 5, 0, 0)
# }
```

---

## Security Policies

### Backend Service Policy

**Location:** `infrastructure/docker/config/vault/policies/backend-policy.hcl`

**Capabilities:**
- ✅ Read database dynamic credentials
- ✅ Read API keys and secrets
- ✅ Renew own token
- ❌ Cannot write secrets
- ❌ Cannot delete secrets
- ❌ Cannot modify policies

**Usage:**

```bash
# Create backend service token
vault token create -policy=backend -period=24h

# Test policy
vault token capabilities <token> secret/data/backend/api
# Output: ["read"]
```

### Admin Policy

**Location:** `infrastructure/docker/config/vault/policies/admin-policy.hcl`

**Capabilities:**
- ✅ Full CRUD on all secrets
- ✅ Manage policies
- ✅ Configure auth methods
- ✅ Manage secrets engines
- ✅ Seal/unseal Vault

**Usage:**

```bash
# Create admin token (use sparingly!)
vault token create -policy=admin -period=24h -orphan
```

### Rotation Policy

**Location:** `infrastructure/docker/config/vault/policies/rotation-policy.hcl`

**Capabilities:**
- ✅ Rotate database credentials
- ✅ Read secrets to verify rotation
- ✅ Manage leases
- ❌ Cannot create new policies
- ❌ Cannot modify mount points

**Usage:**

```bash
# Create rotation service token
vault token create -policy=rotation -period=72h
```

---

## Troubleshooting

### Vault is Sealed

**Symptom:** `vault status` shows `Sealed: true`

**Solution:**

```bash
# Unseal with 3 of 5 keys
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>

# Verify unsealed
vault status
```

### Backend Cannot Access Secrets

**Symptom:** Backend logs show `403 Forbidden` or authentication errors

**Debug Steps:**

```bash
# 1. Verify token is valid
vault token lookup

# 2. Check policy permissions
vault policy read backend-policy

# 3. Test secret access manually
vault kv get secret/backend/api

# 4. Check backend service token in .env
grep VAULT_TOKEN .env
```

### Secret Not Found

**Symptom:** `no secret found at path`

**Solution:**

```bash
# List all secrets to find correct path
vault kv list secret/
vault kv list secret/backend
vault kv list secret/integrations

# Check specific path
vault kv get -format=json secret/backend/api
```

### Database Connection Issues

**Symptom:** Dynamic credentials don't work for database connections

**Debug Steps:**

```bash
# 1. Verify database engine is configured
vault read database/config/toolboxai

# 2. Test credential generation
vault read database/creds/toolboxai

# 3. Test connection with generated credentials
psql "postgresql://<username>:<password>@postgres:5432/toolboxai"

# 4. Check PostgreSQL logs
docker logs toolboxai-postgres
```

### Token Expired

**Symptom:** `permission denied` after token was working

**Solution:**

```bash
# Check token TTL
vault token lookup

# Renew token
vault token renew

# Or create new token
vault token create -policy=backend -period=24h
```

---

## Best Practices

### Security

1. **✅ Never commit unsealing keys to version control**
   - Store keys in secure password manager
   - Use separate keys for each environment
   - Back up keys to multiple secure locations

2. **✅ Use AppRole authentication for services**
   - More secure than long-lived tokens
   - Automatic token renewal
   - Machine identity-based

3. **✅ Rotate secrets on a regular schedule**
   - Database credentials: Weekly
   - API keys: Monthly
   - JWT secrets: Quarterly
   - Root credentials: Annually

4. **✅ Monitor Vault audit logs**
   - Review access patterns
   - Alert on unusual activity
   - Track secret modifications

5. **✅ Backup Vault data regularly**
   - Export secrets to encrypted backup
   - Store in secure, off-site location
   - Test restoration procedures

6. **✅ Use least-privilege policies**
   - Services only access what they need
   - Time-bound tokens
   - Regular policy audits

7. **✅ Enable TLS in production**
   - Use valid certificates
   - Force HTTPS only
   - Set VAULT_SKIP_VERIFY=false

### Operations

1. **Schedule automated rotation:**

```bash
# Add to cron
0 2 * * 0  /path/to/rotate-secrets.sh
```

2. **Monitor Vault health:**

```bash
# Prometheus metrics
curl http://localhost:8200/v1/sys/metrics?format=prometheus

# Health check
curl http://localhost:8200/v1/sys/health
```

3. **Regular audits:**

```bash
# List all active tokens
vault list auth/token/accessors

# Review policies
vault policy list
vault policy read backend-policy
```

---

## Production Deployment

### TLS Configuration

**Generate certificates:**

```bash
cd infrastructure/docker/config/nginx/ssl
./generate-certs.sh
```

**Update vault.hcl:**

```hcl
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/config/ssl/fullchain.pem"
  tls_key_file  = "/vault/config/ssl/privkey.pem"
}
```

**Update environment:**

```bash
# In .env
VAULT_ADDR=https://vault:8200
VAULT_SKIP_VERIFY=false
```

### High Availability

**Configure Raft storage backend in vault.hcl:**

```hcl
storage "raft" {
  path    = "/vault/data"
  node_id = "vault-1"
}
```

**Deploy multiple Vault instances:**

```bash
# Scale Vault service
docker compose up -d --scale vault=3
```

**Use load balancer for Vault access:**

```yaml
# nginx.conf
upstream vault_backend {
  server vault-1:8200;
  server vault-2:8200;
  server vault-3:8200;
}
```

### Monitoring

**Enable Prometheus metrics:**

```yaml
# prometheus.yml
- job_name: 'vault'
  static_configs:
    - targets: ['vault:8200']
  metrics_path: /v1/sys/metrics
  params:
    format: ['prometheus']
```

**Configure alerting:**

```yaml
# alert_rules.yml
- alert: VaultSealed
  expr: vault_core_unsealed == 0
  for: 5m
  annotations:
    summary: "Vault is sealed"
```

**Monitor audit logs:**

```bash
# Enable audit logging
vault audit enable file file_path=/vault/logs/audit.log

# Monitor logs
tail -f /vault/logs/audit.log | jq
```

---

## Integration with Backend

### VaultManager Class

**Location:** `apps/backend/services/vault_manager.py`

**Basic Usage:**

```python
from apps.backend.services.vault_manager import VaultManager

# Initialize (uses VAULT_ADDR and VAULT_TOKEN from environment)
vault = VaultManager()

# Check if authenticated
if not vault.client.is_authenticated():
    raise Exception("Not authenticated to Vault")

# Get secret
db_secret = vault.get_secret("backend/database")

# Get dynamic database credentials
creds = vault.get_dynamic_database_credentials("toolboxai", ttl="1h")

# Rotate secret
vault.rotate_secret("backend/api")

# List secrets
secrets = vault.list_secrets("backend")
```

### Configuration Integration

**In apps/backend/core/config.py:**

```python
from apps.backend.services.vault_manager import get_vault_manager

# Enable Vault if configured
VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() in ("true", "1", "yes")

if VAULT_ENABLED:
    _vault_manager = get_vault_manager()

# Get secrets with Vault fallback
@property
def DATABASE_URL(self):
    if self._vault:
        creds = self._vault.get_dynamic_database_credentials("toolboxai")
        return f"postgresql://{creds['username']}:{creds['password']}@postgres/toolboxai"
    return self._config.DATABASE_URL
```

---

## References

- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [Vault Best Practices](https://www.vaultproject.io/docs/internals/security)
- [Vault API Reference](https://www.vaultproject.io/api-docs)
- [Secret Paths Reference](./vault-secret-paths.md)
- [Troubleshooting Guide](./vault-troubleshooting.md)

---

**Document Version:** 1.0
**Last Updated:** November 2025
**Maintained By:** ToolBoxAI DevOps Team
