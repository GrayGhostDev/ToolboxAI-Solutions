# ============================================
# Backend Service Policy
# ============================================
# Allows backend service to read database credentials
# and application secrets

# Database credentials
path "secret/data/toolboxai/database/*" {
  capabilities = ["read", "list"]
}

# Redis credentials
path "secret/data/toolboxai/redis/*" {
  capabilities = ["read", "list"]
}

# Application secrets
path "secret/data/toolboxai/backend/*" {
  capabilities = ["read", "list"]
}

# API keys
path "secret/data/toolboxai/api-keys/*" {
  capabilities = ["read", "list"]
}

# JWT secrets
path "secret/data/toolboxai/jwt/*" {
  capabilities = ["read", "list"]
}

