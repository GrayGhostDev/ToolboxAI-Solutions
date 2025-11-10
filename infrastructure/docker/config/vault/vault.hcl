# ============================================
# Vault Production Configuration
# ============================================
# HashiCorp Vault configuration for ToolBoxAI production environment
# Updated: 2025-11-09
# ============================================

# Enable Vault UI
ui = true

# Storage backend - File storage for single-node deployment
# For production HA, consider using Consul or cloud-native backends
storage "file" {
  path = "/vault/data"
}

# TCP Listener Configuration
listener "tcp" {
  address       = "0.0.0.0:8200"

  # TLS Configuration
  # TODO: Enable TLS in production with proper certificates
  tls_disable   = 1  # Set to 0 and configure certs for production

  # Uncomment and configure for production TLS:
  # tls_cert_file = "/vault/config/tls/vault.crt"
  # tls_key_file  = "/vault/config/tls/vault.key"
  # tls_min_version = "tls12"

  # Performance tuning
  tls_require_and_verify_client_cert = false
  tls_disable_client_certs = true
}

# API address for internal Docker communication
api_addr = "http://vault:8200"

# Cluster address (for HA mode)
cluster_addr = "http://vault:8201"

# Disable mlock for containerized environments
# In container environments, mlock() syscall may not be available
disable_mlock = true

# Telemetry configuration for Prometheus
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true

  # Uncomment to publish metrics to a statsd server
  # statsd_address = "localhost:8125"
}

# Logging configuration
log_level = "Info"
log_format = "json"

# Default lease configuration
default_lease_ttl = "1h"
max_lease_ttl = "24h"

# Plugin directory
plugin_directory = "/vault/plugins"

# Additional configuration
# ============================================

# Seal configuration
# By default, Vault uses Shamir seal (5 key shares, 3 required to unseal)
# For production, consider auto-unseal with cloud KMS:
#
# seal "awskms" {
#   region     = "us-west-2"
#   kms_key_id = "your-kms-key-id"
# }
#
# or
#
# seal "gcpckms" {
#   project     = "your-project"
#   region      = "global"
#   key_ring    = "vault"
#   crypto_key  = "vault-key"
# }

# High Availability configuration
# Uncomment for HA setup with Consul backend:
#
# storage "consul" {
#   address = "consul:8500"
#   path    = "vault/"
#
#   # Consul authentication
#   token   = "your-consul-token"
# }
#
# ha_storage "consul" {
#   address = "consul:8500"
#   path    = "vault-ha/"
#   token   = "your-consul-token"
# }

# Audit logging
# Enable audit logs for compliance and security monitoring
# Uncomment to enable file-based audit logging:
#
# audit "file" {
#   file_path = "/vault/logs/audit.log"
#   log_raw   = false
#   hmac_accessor = true
#   mode = "0600"
#   format = "json"
# }

# Sentinel configuration (Enterprise)
# Define policies for fine-grained access control
# Requires Vault Enterprise license
