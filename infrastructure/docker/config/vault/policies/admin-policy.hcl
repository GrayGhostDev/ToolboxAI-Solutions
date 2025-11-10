# ============================================
# Admin Vault Policy
# ============================================
# Full administrative access to Vault
# Use with caution - only for authorized administrators
# Updated: 2025-11-09
# ============================================

# Secrets Engines - Full Access
# ============================================
# KV v2 secrets engine
path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Database secrets engine
path "database/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Transit encryption engine
path "transit/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# PKI (certificates) engine
path "pki/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# SSH secrets engine
path "ssh/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# TOTP secrets engine
path "totp/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Authentication Methods
# ============================================
# Manage all auth methods
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Manage auth method configuration
path "sys/auth" {
  capabilities = ["read", "list"]
}

path "sys/auth/*" {
  capabilities = ["create", "read", "update", "delete", "sudo"]
}

# Policies
# ============================================
# Full access to manage policies
path "sys/policies/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "sys/policy" {
  capabilities = ["read", "list"]
}

path "sys/policy/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# System Configuration
# ============================================
# Manage secrets engines
path "sys/mounts" {
  capabilities = ["read", "list"]
}

path "sys/mounts/*" {
  capabilities = ["create", "read", "update", "delete", "sudo"]
}

# Manage audit devices
path "sys/audit" {
  capabilities = ["read", "list"]
}

path "sys/audit/*" {
  capabilities = ["create", "read", "update", "delete", "sudo"]
}

# System health and status
path "sys/health" {
  capabilities = ["read"]
}

path "sys/capabilities" {
  capabilities = ["read", "update"]
}

path "sys/capabilities-self" {
  capabilities = ["read", "update"]
}

# Seal/Unseal Operations
# ============================================
path "sys/seal" {
  capabilities = ["update", "sudo"]
}

path "sys/unseal" {
  capabilities = ["update", "sudo"]
}

path "sys/seal-status" {
  capabilities = ["read"]
}

# Key Management
# ============================================
path "sys/rekey/*" {
  capabilities = ["update", "sudo"]
}

path "sys/rotate" {
  capabilities = ["update", "sudo"]
}

# Leases
# ============================================
path "sys/leases/lookup/*" {
  capabilities = ["read", "list"]
}

path "sys/leases/revoke/*" {
  capabilities = ["update", "sudo"]
}

path "sys/leases/renew/*" {
  capabilities = ["update"]
}

# Tokens
# ============================================
# Full token management
path "auth/token/create" {
  capabilities = ["create", "update", "sudo"]
}

path "auth/token/create-orphan" {
  capabilities = ["create", "update", "sudo"]
}

path "auth/token/lookup" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}

path "auth/token/renew" {
  capabilities = ["update"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/revoke" {
  capabilities = ["update", "sudo"]
}

path "auth/token/revoke-orphan" {
  capabilities = ["update", "sudo"]
}

path "auth/token/roles/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Namespaces (Enterprise)
# ============================================
path "sys/namespaces/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Control Groups (Enterprise)
# ============================================
path "sys/control-group/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Replication (Enterprise)
# ============================================
path "sys/replication/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Usage Notes
# ============================================
# 1. Create admin token:
#    vault token create -policy=admin -period=24h -orphan
#
# 2. Use admin token sparingly - prefer role-specific tokens
#
# 3. Audit admin actions:
#    vault audit enable file file_path=/vault/logs/admin-audit.log
#
# 4. Rotate admin token regularly:
#    vault token renew
#    vault token create -policy=admin (after validation)
#
# 5. Emergency seal:
#    vault operator seal
#
# Security Best Practices
# ============================================
# - Limit number of admin tokens (1-2 maximum)
# - Use short TTLs (24 hours or less)
# - Enable MFA for admin operations
# - Log all admin actions
# - Rotate admin tokens monthly
# - Never share admin tokens
# - Use specific policies when possible instead of admin
