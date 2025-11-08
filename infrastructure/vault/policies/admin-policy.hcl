# ============================================
# Admin Policy
# ============================================
# Full access to all secrets for administration

# Full access to all secrets
path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Full access to all policies
path "sys/policies/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Access to auth methods
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Manage secret engines
path "sys/mounts/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

