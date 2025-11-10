# Vault Troubleshooting Guide

**Last Updated:** November 2025
**Vault Version:** 1.15.6
**Purpose:** Common issues, solutions, and debugging procedures

---

## Table of Contents

1. [Vault Status Issues](#vault-status-issues)
2. [Authentication Problems](#authentication-problems)
3. [Secret Access Issues](#secret-access-issues)
4. [Database Integration](#database-integration)
5. [Backend Integration](#backend-integration)
6. [Performance Issues](#performance-issues)
7. [Network and Connectivity](#network-and-connectivity)
8. [Emergency Procedures](#emergency-procedures)

---

## Vault Status Issues

### Issue: Vault is Sealed

**Symptoms:**
- `vault status` shows `Sealed: true`
- Backend logs show "Vault is sealed" errors
- Cannot access secrets

**Cause:**
- Vault restart without auto-unseal
- Manual seal operation
- Vault crash or container restart

**Solution:**

```bash
# 1. Check seal status
docker exec toolboxai-vault vault status

# Output shows:
# Sealed: true
# Total Shares: 5
# Threshold: 3

# 2. Unseal with 3 of 5 keys
docker exec toolboxai-vault vault operator unseal <unseal-key-1>
docker exec toolboxai-vault vault operator unseal <unseal-key-2>
docker exec toolboxai-vault vault operator unseal <unseal-key-3>

# 3. Verify unsealed
docker exec toolboxai-vault vault status | grep "Sealed"
# Should show: Sealed: false
```

**Prevention:**
- Store unseal keys securely in password manager
- Document unseal procedure
- Consider auto-unseal with cloud KMS (production)
- Set up monitoring alert for seal status

---

### Issue: Vault Not Initialized

**Symptoms:**
- `vault status` shows `Initialized: false`
- "Vault is not initialized" error
- No secrets accessible

**Cause:**
- Fresh Vault installation
- Data volume was deleted
- Wrong Vault data directory

**Solution:**

```bash
# 1. Initialize Vault
docker exec toolboxai-vault vault operator init

# 2. IMMEDIATELY save the output:
# - 5 unseal keys
# - 1 root token

# 3. Unseal Vault (see above)

# 4. Login with root token
docker exec -e VAULT_TOKEN=<root-token> toolboxai-vault \\
  vault login <root-token>

# 5. Run setup script
cd infrastructure/vault/scripts
./init-vault.sh
```

**Prevention:**
- Backup `.vault-keys.json` file
- Use persistent volumes for Vault data
- Document initialization procedure
- Test restoration from backup regularly

---

### Issue: Vault Container Not Starting

**Symptoms:**
- `docker ps` doesn't show `toolboxai-vault`
- Container exits immediately
- Logs show startup errors

**Diagnosis:**

```bash
# Check container status
docker ps -a | grep vault

# View logs
docker logs toolboxai-vault

# Common errors:
# - "permission denied" → Volume mount issues
# - "address already in use" → Port 8200 conflict
# - "config file not found" → Missing vault.hcl
```

**Solutions:**

**For permission errors:**
```bash
# Fix volume permissions
sudo chown -R 100:1000 /path/to/vault/data
```

**For port conflicts:**
```bash
# Check port usage
lsof -i :8200

# Kill conflicting process or change port in docker-compose.yml
```

**For config errors:**
```bash
# Verify config file exists
ls -la infrastructure/docker/config/vault/

# Check config syntax
docker exec toolboxai-vault vault operator diagnose \\
  -config=/vault/config/vault.hcl
```

---

## Authentication Problems

### Issue: Token Expired

**Symptoms:**
- "permission denied" after token was working
- "token TTL expired" error
- Backend cannot authenticate

**Diagnosis:**

```bash
# Check token status
vault token lookup

# Output shows:
# ttl: 0s  ← Token expired
```

**Solution:**

```bash
# Option 1: Renew existing token (if renewable)
vault token renew

# Option 2: Create new token
vault token create -policy=backend -period=24h

# Option 3: Use AppRole for automatic renewal
vault write auth/approle/login \\
  role_id=<role-id> \\
  secret_id=<secret-id>
```

**Prevention:**
- Use tokens with sufficient TTL (24h for backend)
- Use periodic tokens (`-period=24h`) that auto-renew
- Implement AppRole authentication for services
- Set up monitoring for token expiration

---

### Issue: Permission Denied

**Symptoms:**
- "permission denied" error when reading secrets
- Backend logs show 403 errors
- Specific operations fail

**Diagnosis:**

```bash
# Check token capabilities for path
vault token capabilities secret/backend/database

# Output should show: ["read"]
# If shows: ["deny"] → Token doesn't have access
```

**Solution:**

```bash
# 1. Check which policy is attached to token
vault token lookup

# Output shows:
# policies: ["backend"]

# 2. Review policy contents
vault policy read backend

# 3. Verify policy includes required path
# Should see:
# path "secret/data/backend/*" {
#   capabilities = ["read"]
# }

# 4. If policy is wrong, update it
vault policy write backend /path/to/backend-policy.hcl

# 5. Create new token with correct policy
vault token create -policy=backend -period=24h
```

**Prevention:**
- Test policies before deploying
- Use least-privilege principle
- Document policy requirements
- Regular policy audits

---

### Issue: AppRole Authentication Failure

**Symptoms:**
- Backend fails to authenticate on startup
- "invalid role_id or secret_id" error
- AppRole login returns 400 error

**Diagnosis:**

```bash
# Check if AppRole auth is enabled
vault auth list

# Check if role exists
vault list auth/approle/role

# Read role configuration
vault read auth/approle/role/backend/role-id
```

**Solution:**

```bash
# 1. Enable AppRole (if not enabled)
vault auth enable approle

# 2. Create role
vault write auth/approle/role/backend \\
  token_policies="backend" \\
  token_ttl=1h \\
  token_max_ttl=4h

# 3. Get role ID
vault read auth/approle/role/backend/role-id

# 4. Generate secret ID
vault write -f auth/approle/role/backend/secret-id

# 5. Test authentication
vault write auth/approle/login \\
  role_id=<role-id> \\
  secret_id=<secret-id>
```

---

## Secret Access Issues

### Issue: Secret Not Found

**Symptoms:**
- "no secret found at path" error
- Backend logs show secret path errors
- Secret exists but cannot be read

**Diagnosis:**

```bash
# List all secrets
vault kv list secret/

# Check specific path
vault kv list secret/backend

# Try reading with full path
vault kv get secret/backend/database
```

**Common Mistakes:**

```bash
# ❌ Wrong: Including "data" in KV v2 path
vault kv get secret/data/backend/database

# ✅ Correct: Use path without "data"
vault kv get secret/backend/database

# ❌ Wrong: Trailing slash
vault kv get secret/backend/database/

# ✅ Correct: No trailing slash
vault kv get secret/backend/database
```

**Solution:**

```bash
# 1. Verify secret exists
vault kv metadata get secret/backend/database

# 2. If doesn't exist, create it
vault kv put secret/backend/database \\
  url="postgresql://user:pass@postgres:5432/toolboxai" \\
  password="secure-password"

# 3. Verify can read
vault kv get secret/backend/database
```

---

### Issue: Getting Old Secret Version

**Symptoms:**
- Secret was updated but old value is returned
- Backend uses outdated credentials
- Rotation doesn't take effect

**Diagnosis:**

```bash
# Check secret versions
vault kv metadata get secret/backend/database

# Output shows:
# current_version: 3
# versions:
#   1: created_time...
#   2: created_time...
#   3: created_time...

# Read specific version
vault kv get -version=2 secret/backend/database
vault kv get -version=3 secret/backend/database
```

**Solution:**

```bash
# 1. Force read latest version
vault kv get secret/backend/database

# 2. Verify version number
vault kv get -format=json secret/backend/database | jq .data.metadata.version

# 3. If backend is cached, restart
docker restart toolboxai-backend
```

**Prevention:**
- Don't cache Vault secrets for too long
- Use secret versioning properly
- Restart services after secret updates
- Monitor secret access patterns

---

### Issue: Secret Write Fails

**Symptoms:**
- Cannot update secrets
- "permission denied" on write
- Secret doesn't change after update

**Diagnosis:**

```bash
# Check write permissions
vault token capabilities secret/backend/database

# Should show: ["create", "update"] or ["read", "update"]
# If shows: ["read"] → Token cannot write
```

**Solution:**

```bash
# 1. Use token with write permissions (admin or root)
export VAULT_TOKEN=<admin-token>

# 2. Write secret
vault kv put secret/backend/database \\
  url="new-url" \\
  password="new-password"

# 3. Verify update
vault kv get secret/backend/database

# 4. Check version increased
vault kv metadata get secret/backend/database
```

---

## Database Integration

### Issue: Dynamic Credentials Don't Work

**Symptoms:**
- Cannot connect to database with generated credentials
- "authentication failed" errors
- Generated username not found in PostgreSQL

**Diagnosis:**

```bash
# 1. Generate credentials
vault read database/creds/toolboxai

# 2. Test credentials immediately
export USERNAME=<generated-username>
export PASSWORD=<generated-password>

psql "postgresql://$USERNAME:$PASSWORD@postgres:5432/toolboxai" \\
  -c "SELECT current_user;"

# If fails, check PostgreSQL logs
docker logs toolboxai-postgres | tail -20
```

**Common Causes:**

1. **Database engine not configured:**
```bash
# Check configuration
vault read database/config/toolboxai

# If empty, run init script
cd infrastructure/vault/scripts
./init-vault.sh
```

2. **Role not created:**
```bash
# Check role exists
vault read database/roles/toolboxai

# If not, create role
vault write database/roles/toolboxai \\
  db_name=toolboxai \\
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \\
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \\
  default_ttl="1h" \\
  max_ttl="24h"
```

3. **PostgreSQL connection failed:**
```bash
# Test connection from Vault to PostgreSQL
docker exec toolboxai-vault \\
  nc -zv postgres 5432

# If fails, check networks
docker network inspect toolboxai_database
```

**Solution:**

```bash
# 1. Verify Vault can connect to PostgreSQL
vault read database/config/toolboxai

# 2. Rotate root credentials
vault write -f database/rotate-root/toolboxai

# 3. Test credential generation
vault read database/creds/toolboxai

# 4. Test connection
psql "postgresql://<username>:<password>@postgres:5432/toolboxai"
```

---

### Issue: Credentials Expire Too Quickly

**Symptoms:**
- Database connections fail after 1 hour
- "password authentication failed" after TTL
- Backend loses database access

**Cause:**
- Default TTL too short (1h)
- Credentials not renewed before expiration

**Solution:**

```bash
# 1. Increase default TTL for role
vault write database/roles/toolboxai \\
  db_name=toolboxai \\
  default_ttl="24h" \\
  max_ttl="72h"

# 2. Request credentials with longer TTL
vault read database/creds/toolboxai ttl=24h

# 3. Implement automatic renewal in backend
# See backend integration guide
```

**Backend Code for Auto-Renewal:**

```python
from apps.backend.services.vault_manager import VaultManager
import asyncio

async def maintain_database_credentials():
    vault = VaultManager()
    while True:
        # Renew 5 minutes before expiration
        await asyncio.sleep((60 * 60) - (5 * 60))  # 55 minutes

        # Get new credentials
        new_creds = vault.get_dynamic_database_credentials("toolboxai")

        # Update database connection pool
        await update_database_pool(new_creds)
```

---

## Backend Integration

### Issue: Backend Cannot Connect to Vault

**Symptoms:**
- Backend logs show "connection refused"
- "dial tcp: lookup vault" DNS errors
- Vault health check fails

**Diagnosis:**

```bash
# 1. Check Vault is running
docker ps | grep vault

# 2. Check Vault health from backend container
docker exec toolboxai-backend curl http://vault:8200/v1/sys/health

# 3. Check network connectivity
docker exec toolboxai-backend nc -zv vault 8200

# 4. Check Docker networks
docker network inspect toolboxai_backend
```

**Solution:**

```bash
# 1. Verify both on same network
docker inspect toolboxai-backend | jq '.[0].NetworkSettings.Networks'
docker inspect toolboxai-vault | jq '.[0].NetworkSettings.Networks'

# 2. If not, add to network
docker network connect toolboxai_backend toolboxai-vault

# 3. Restart backend
docker restart toolboxai-backend

# 4. Test connection
docker exec toolboxai-backend curl http://vault:8200/v1/sys/health
```

---

### Issue: VaultManager Import Errors

**Symptoms:**
- `ImportError: cannot import name 'VaultManager'`
- Backend fails to start
- Module not found errors

**Diagnosis:**

```bash
# Check if file exists
ls -la apps/backend/services/vault_manager.py

# Check Python path
docker exec toolboxai-backend python -c "import sys; print(sys.path)"

# Test import
docker exec toolboxai-backend python -c \\
  "from apps.backend.services.vault_manager import VaultManager"
```

**Solution:**

```bash
# 1. Verify file exists
cat apps/backend/services/vault_manager.py | head -20

# 2. Check dependencies installed
docker exec toolboxai-backend pip list | grep hvac

# 3. If missing, install
docker exec toolboxai-backend pip install hvac

# 4. Restart backend
docker restart toolboxai-backend
```

---

### Issue: Vault Integration Disabled

**Symptoms:**
- Backend uses .env values instead of Vault
- No Vault connection attempts in logs
- Secrets not fetched from Vault

**Diagnosis:**

```bash
# Check VAULT_ENABLED setting
docker exec toolboxai-backend env | grep VAULT_ENABLED

# Check if VaultManager initialized
docker exec toolboxai-backend python -c \\
  "from apps.backend.core.config import VAULT_ENABLED; print(VAULT_ENABLED)"
```

**Solution:**

```bash
# 1. Enable Vault in .env
echo "VAULT_ENABLED=true" >> .env

# 2. Set Vault token
echo "VAULT_TOKEN=<your-token>" >> .env

# 3. Restart backend
docker restart toolboxai-backend

# 4. Verify Vault is used
docker logs toolboxai-backend | grep "Vault integration enabled"
```

---

## Performance Issues

### Issue: Slow Secret Retrieval

**Symptoms:**
- Backend startup takes minutes
- Secret reads timeout
- High Vault CPU usage

**Diagnosis:**

```bash
# Check Vault metrics
curl http://localhost:8200/v1/sys/metrics?format=prometheus | grep vault_

# Check backend timing
docker logs toolboxai-backend | grep -i "vault\|secret" | grep -i "time\|duration"

# Monitor Vault resource usage
docker stats toolboxai-vault
```

**Solution:**

```bash
# 1. Enable secret caching in backend
# VaultManager already caches for 5 minutes

# 2. Increase cache TTL if needed
# Edit apps/backend/services/vault_manager.py:
# self._cache_ttl = 600  # 10 minutes

# 3. Use batch secret retrieval
# Get multiple secrets in single call

# 4. Increase Vault resources
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
```

---

### Issue: High Memory Usage

**Symptoms:**
- Vault container using >1GB memory
- Out of memory errors
- Container restarts

**Diagnosis:**

```bash
# Check memory usage
docker stats toolboxai-vault --no-stream

# Check Vault storage size
docker exec toolboxai-vault du -sh /vault/data

# Check secret count
vault kv list -format=json secret/ | jq length
```

**Solution:**

```bash
# 1. Clear old secret versions
vault kv metadata put -max-versions=5 secret/backend/database

# 2. Delete unnecessary secrets
vault kv metadata delete secret/old/unused

# 3. Increase container memory limit
# docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 512M
```

---

## Network and Connectivity

### Issue: Cannot Access Vault UI

**Symptoms:**
- http://localhost:8200/ui not accessible
- Connection refused
- Timeout errors

**Diagnosis:**

```bash
# Check Vault is running
docker ps | grep vault

# Check port mapping
docker port toolboxai-vault

# Test local access
curl http://localhost:8200/ui/

# Check firewall
sudo iptables -L | grep 8200
```

**Solution:**

```bash
# 1. Verify port binding in docker-compose.yml
# Should have: "8200:8200"

# 2. Restart Vault
docker restart toolboxai-vault

# 3. Test from host
curl http://localhost:8200/v1/sys/health

# 4. Access UI
open http://localhost:8200/ui
```

---

### Issue: TLS Certificate Errors

**Symptoms:**
- "x509: certificate signed by unknown authority"
- HTTPS connection fails
- VAULT_SKIP_VERIFY required

**Diagnosis:**

```bash
# Check TLS configuration
vault read sys/health

# Test certificate
openssl s_client -connect vault:8200
```

**Solution:**

**Development (use HTTP):**
```bash
# In .env
VAULT_ADDR=http://vault:8200
VAULT_SKIP_VERIFY=false
```

**Production (use proper TLS):**
```bash
# Generate certificates
cd infrastructure/docker/config/nginx/ssl
./generate-certs.sh

# Update vault.hcl
listener "tcp" {
  tls_cert_file = "/vault/config/ssl/fullchain.pem"
  tls_key_file = "/vault/config/ssl/privkey.pem"
}

# Restart Vault
docker restart toolboxai-vault
```

---

## Emergency Procedures

### Emergency: All Unseal Keys Lost

**Impact:** CRITICAL - Cannot unseal Vault, all secrets inaccessible

**Immediate Actions:**

1. **DO NOT DELETE VAULT DATA**
2. Check all backup locations for `.vault-keys.json`
3. Check password managers
4. Check secure notes
5. Check team members

**If Keys Cannot Be Recovered:**

1. **Accept data loss** - Vault contents cannot be recovered
2. Re-initialize Vault (creates new keys)
3. Manually recreate all secrets from .env files
4. Update all service tokens
5. Document incident for post-mortem

**Prevention:**
- Store keys in multiple secure locations
- Use cloud KMS for auto-unseal
- Regular backup verification
- Document key storage procedures

---

### Emergency: Root Token Lost

**Impact:** HIGH - Cannot perform admin operations

**Solution:**

```bash
# Generate new root token using unseal keys
vault operator generate-root -init

# Follow prompts with unseal keys
vault operator generate-root

# Use new root token
vault login <new-root-token>

# Immediately rotate
vault token create -policy=admin -period=24h
vault token revoke <old-root-token>
```

---

### Emergency: Vault Data Corruption

**Impact:** CRITICAL - Secrets may be lost

**Immediate Actions:**

```bash
# 1. Stop Vault immediately
docker stop toolboxai-vault

# 2. Backup current state (even if corrupted)
cp -r /vault/data /vault/data.backup.$(date +%Y%m%d-%H%M%S)

# 3. Restore from last good backup
cp -r /vault/data.backup.20251109 /vault/data

# 4. Restart Vault
docker start toolboxai-vault

# 5. Verify data
vault kv list secret/
```

---

## Debugging Commands

### Health Checks

```bash
# Vault status
vault status

# Health endpoint
curl http://localhost:8200/v1/sys/health

# Container health
docker inspect toolboxai-vault | jq '.[0].State.Health'
```

### Token Debugging

```bash
# Current token info
vault token lookup

# Check capabilities
vault token capabilities secret/backend/database

# List token accessories
vault list auth/token/accessors
```

### Secret Debugging

```bash
# List all secrets
vault kv list secret/

# Get secret metadata
vault kv metadata get secret/backend/database

# Get specific version
vault kv get -version=2 secret/backend/database
```

### Audit Logging

```bash
# Enable audit log
vault audit enable file file_path=/vault/logs/audit.log

# View audit log
docker exec toolboxai-vault tail -f /vault/logs/audit.log | jq
```

---

## Getting Help

### Log Files

```bash
# Vault logs
docker logs toolboxai-vault

# Backend logs (Vault integration)
docker logs toolboxai-backend | grep -i vault

# System logs
journalctl -u docker | grep vault
```

### Diagnostic Information

When requesting help, provide:

1. Vault version: `vault version`
2. Vault status: `vault status`
3. Error messages: Full error text
4. Logs: Last 50 lines of relevant logs
5. Configuration: Sanitized vault.hcl

### Support Resources

- [Vault Documentation](https://www.vaultproject.io/docs)
- [Vault Community Forum](https://discuss.hashicorp.com/c/vault)
- [GitHub Issues](https://github.com/hashicorp/vault/issues)
- Internal: `#devops` Slack channel

---

**Document Version:** 1.0
**Last Updated:** November 2025
**Maintained By:** ToolBoxAI DevOps Team
