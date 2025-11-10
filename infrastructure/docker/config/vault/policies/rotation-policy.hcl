# ============================================
# Rotation Service Vault Policy
# ============================================
# Policy for automated secret rotation service
# Allows rotating credentials without full admin access
# Updated: 2025-11-09
# ============================================

# Database Credential Rotation
# ============================================
# Allow rotating database role credentials
# This rotates the password for dynamic database credentials
path "database/rotate-role/*" {
  capabilities = ["update"]
}

# Allow rotating root database credentials
# Use with caution - rotates the connection credentials Vault uses
path "database/rotate-root/*" {
  capabilities = ["update"]
}

# Allow reading database configuration to verify rotation
path "database/config/*" {
  capabilities = ["read"]
}

# Allow reading dynamic credentials to test after rotation
path "database/creds/*" {
  capabilities = ["read"]
}

# Static Secrets Rotation
# ============================================
# Allow updating secrets for rotation
# Specific paths where rotation is allowed
path "secret/data/backend/rotation" {
  capabilities = ["create", "update"]
}

path "secret/data/integrations/rotation" {
  capabilities = ["create", "update"]
}

# Allow reading current secrets before rotation
path "secret/data/backend/*" {
  capabilities = ["read"]
}

path "secret/data/integrations/*" {
  capabilities = ["read"]
}

# Allow reading metadata to track rotation history
path "secret/metadata/backend/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/integrations/*" {
  capabilities = ["read", "list"]
}

# Transit Engine Rotation
# ============================================
# If using Vault's transit engine for encryption
# Allow rotating encryption keys
path "transit/keys/*/rotate" {
  capabilities = ["update"]
}

path "transit/keys/*/config" {
  capabilities = ["read", "update"]
}

# Lease Management
# ============================================
# Allow renewing leases (for long-running rotation tasks)
path "sys/leases/renew" {
  capabilities = ["update"]
}

# Allow revoking old leases after successful rotation
path "sys/leases/revoke" {
  capabilities = ["update"]
}

# Allow looking up leases to check expiration
path "sys/leases/lookup" {
  capabilities = ["update"]
}

# Token Management
# ============================================
# Allow rotation service to renew its own token
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Allow looking up own token
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Deny creating new tokens (rotation service should use provided token)
path "auth/token/create" {
  capabilities = ["deny"]
}

# PKI Certificate Rotation
# ============================================
# If using PKI for certificate management
# Allow issuing new certificates
path "pki/issue/*" {
  capabilities = ["create", "update"]
}

# Allow revoking old certificates
path "pki/revoke" {
  capabilities = ["update"]
}

# Audit and Monitoring
# ============================================
# Allow reading audit configuration (but not modifying)
path "sys/audit" {
  capabilities = ["read", "list"]
}

# Allow reading system health for monitoring
path "sys/health" {
  capabilities = ["read"]
}

# Deny Dangerous Operations
# ============================================
# Explicitly deny system configuration changes
path "sys/mounts" {
  capabilities = ["deny"]
}

path "sys/mounts/*" {
  capabilities = ["deny"]
}

# Deny policy changes
path "sys/policies/*" {
  capabilities = ["deny"]
}

# Deny auth method changes
path "sys/auth" {
  capabilities = ["deny"]
}

path "sys/auth/*" {
  capabilities = ["deny"]
}

# Deny seal/unseal operations
path "sys/seal" {
  capabilities = ["deny"]
}

path "sys/unseal" {
  capabilities = ["deny"]
}

# Usage Notes
# ============================================
# 1. Create rotation service token:
#    vault token create -policy=rotation -period=72h
#
# 2. Rotate database credentials:
#    vault write -f database/rotate-role/toolboxai
#
# 3. Verify rotation:
#    vault read database/creds/toolboxai
#
# 4. Schedule rotation (cron example):
#    0 2 * * 0  /path/to/rotate-secrets.sh
#
# 5. Monitor rotation:
#    vault audit enable file file_path=/vault/logs/rotation-audit.log
#
# Rotation Best Practices
# ============================================
# - Rotate database credentials weekly
# - Rotate API keys monthly
# - Rotate encryption keys quarterly
# - Test credentials before revoking old ones
# - Keep audit logs of all rotations
# - Alert on rotation failures
# - Verify services reconnect after rotation
# - Use automated rotation when possible
# - Have rollback plan for failed rotations
#
# Example Rotation Schedule
# ============================================
# Weekly:  Database credentials
# Monthly: API keys (OpenAI, Pusher, Roblox)
# Quarterly: Encryption keys, JWT secrets
# Annually: Root credentials, admin tokens
