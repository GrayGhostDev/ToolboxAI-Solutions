# ============================================
# Vault Development Configuration
# ============================================
# HashiCorp Vault configuration for ToolBoxAI development environment
# Optimized for local development with minimal security restrictions
# Updated: 2025-11-09
# ============================================

# Enable Vault UI
ui = true

# Storage backend - In-memory for development
# Data is lost when Vault stops, but faster for testing
storage "inmem" {}

# Alternative: Use file storage for persistence in development
# storage "file" {
#   path = "/vault/data"
# }

# TCP Listener Configuration
listener "tcp" {
  address     = "0.0.0.0:8200"

  # Disable TLS for local development
  tls_disable = 1
}

# API address for Docker internal communication
api_addr = "http://localhost:8200"

# Development mode settings
# ============================================

# Disable mlock (not needed in containers)
disable_mlock = true

# Verbose logging for development
log_level = "Debug"
log_format = "standard"  # More readable for development

# Telemetry for Prometheus (same as production)
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Shorter lease times for faster testing
default_lease_ttl = "15m"
max_lease_ttl = "1h"

# Development Features
# ============================================

# Note: When running `vault server -dev`:
# - Vault is automatically initialized and unsealed
# - A root token is printed to stdout
# - All data is stored in-memory
# - TLS is disabled
# - mlock is disabled
# - UI is enabled at http://localhost:8200/ui

# Development Root Token
# Set via VAULT_DEV_ROOT_TOKEN_ID environment variable
# Default: "devtoken" (configured in docker-compose.dev.yml)

# Quick Start Commands for Development
# ============================================

# 1. Start Vault in dev mode:
#    docker compose up vault -d

# 2. Access Vault UI:
#    http://localhost:8200/ui
#    Token: devtoken

# 3. Set environment variables:
#    export VAULT_ADDR='http://localhost:8200'
#    export VAULT_TOKEN='devtoken'

# 4. Interact with Vault CLI:
#    docker exec -it toolboxai-vault vault status
#    docker exec -it toolboxai-vault vault secrets list

# 5. Enable secrets engines:
#    docker exec -it toolboxai-vault vault secrets enable -path=secret kv-v2
#    docker exec -it toolboxai-vault vault secrets enable database

# 6. Write test secrets:
#    docker exec -it toolboxai-vault vault kv put secret/test key=value

# Development Best Practices
# ============================================

# 1. Use in-memory storage (default)
# 2. Use simple root token for easy access
# 3. Enable debug logging
# 4. No TLS required
# 5. Auto-unseal enabled
# 6. Test secret rotation regularly
# 7. Reset Vault state between major changes:
#    docker compose down vault && docker volume rm toolboxai_vault_data
