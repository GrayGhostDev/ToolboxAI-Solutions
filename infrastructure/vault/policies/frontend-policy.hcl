# ============================================
# Dashboard/Frontend Policy
# ============================================
# Minimal read access for frontend configuration

# Public API keys only
path "secret/data/toolboxai/public/*" {
  capabilities = ["read"]
}

# Frontend configuration
path "secret/data/toolboxai/frontend/*" {
  capabilities = ["read"]
}

