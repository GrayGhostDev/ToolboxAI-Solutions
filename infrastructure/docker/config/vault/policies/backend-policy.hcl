# ============================================
# Backend Service Vault Policy
# ============================================
# Policy for backend FastAPI service
# Grants access to database credentials and application secrets
# Updated: 2025-11-09
# ============================================

# Database Dynamic Credentials
# ============================================
# Allow reading dynamic PostgreSQL credentials
# These credentials are automatically generated and rotated by Vault
path "database/creds/toolboxai" {
  capabilities = ["read"]
}

# Allow reading database configuration
path "database/config/toolboxai" {
  capabilities = ["read"]
}

# Application Secrets (KV v2)
# ============================================
# Allow reading backend-specific secrets
path "secret/data/backend/*" {
  capabilities = ["read"]
}

# Allow reading integration secrets (OpenAI, Pusher, Roblox, etc.)
path "secret/data/integrations/*" {
  capabilities = ["read"]
}

# Allow reading shared secrets
path "secret/data/shared/*" {
  capabilities = ["read"]
}

# Secret Metadata Access
# ============================================
# Allow listing secrets for discovery
path "secret/metadata/backend" {
  capabilities = ["list"]
}

path "secret/metadata/integrations" {
  capabilities = ["list"]
}

path "secret/metadata/shared" {
  capabilities = ["list"]
}

# Allow reading secret metadata
path "secret/metadata/backend/*" {
  capabilities = ["read"]
}

path "secret/metadata/integrations/*" {
  capabilities = ["read"]
}

# Token Management
# ============================================
# Allow token self-renewal (so backend can keep its token valid)
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Allow looking up own token information
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Deny token creation (prevent backend from creating new tokens)
path "auth/token/create" {
  capabilities = ["deny"]
}

# Transit Engine (Encryption as a Service)
# ============================================
# If using Vault's transit engine for encryption
# Allow encryption and decryption operations
path "transit/encrypt/backend-key" {
  capabilities = ["update"]
}

path "transit/decrypt/backend-key" {
  capabilities = ["update"]
}

# PKI Engine (Certificate Management)
# ============================================
# If using Vault for certificate management
# Allow issuing certificates for backend service
path "pki/issue/backend-role" {
  capabilities = ["create", "update"]
}

# Deny Dangerous Operations
# ============================================
# Explicitly deny access to system operations
path "sys/*" {
  capabilities = ["deny"]
}

# Deny access to auth configuration
path "auth/*" {
  capabilities = ["deny"]
}

# Deny access to policies
path "sys/policies/*" {
  capabilities = ["deny"]
}

# Usage Notes
# ============================================
# 1. Attach this policy to backend service token:
#    vault token create -policy=backend -period=24h
#
# 2. Backend reads dynamic credentials:
#    vault read database/creds/toolboxai
#
# 3. Backend reads application secrets:
#    vault kv get secret/backend/api
#
# 4. Token renewal (automatic in vault_manager.py):
#    vault token renew-self
#
# 5. List available secrets:
#    vault kv list secret/backend
