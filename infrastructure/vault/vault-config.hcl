# HashiCorp Vault Configuration for ToolBoxAI
# Production-ready configuration with high availability

# Storage backend - using integrated Raft storage for HA
storage "raft" {
  path    = "/vault/data"
  node_id = "vault_1"

  # High availability configuration
  retry_join {
    leader_api_addr = "https://vault-2.toolboxai.local:8200"
  }
  retry_join {
    leader_api_addr = "https://vault-3.toolboxai.local:8200"
  }

  # Performance tuning
  performance_multiplier = 1
  max_entry_size         = "1MB"

  # Automatic snapshots
  autopilot {
    cleanup_dead_servers      = true
    last_contact_threshold    = "200ms"
    max_trailing_logs         = 250
    server_stabilization_time = "10s"
  }
}

# Listener configuration with TLS
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/vault/certs/vault.crt"
  tls_key_file  = "/vault/certs/vault.key"

  # TLS configuration
  tls_min_version = "tls12"
  tls_cipher_suites = [
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
  ]

  # Security headers
  custom_response_headers {
    "Strict-Transport-Security" = ["max-age=31536000; includeSubDomains"]
    "X-Frame-Options"           = ["DENY"]
    "X-Content-Type-Options"    = ["nosniff"]
    "X-XSS-Protection"          = ["1; mode=block"]
  }
}

# API address for cluster communication
api_addr     = "https://vault.toolboxai.local:8200"
cluster_addr = "https://vault.toolboxai.local:8201"

# UI configuration
ui = true

# Telemetry for monitoring
telemetry {
  prometheus_retention_time = "24h"
  disable_hostname          = false

  # StatsD integration (optional)
  # statsd_address = "127.0.0.1:8125"
  # statsite_address = "127.0.0.1:8125"
}

# Seal configuration (using AWS KMS for auto-unseal)
seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/vault-unseal"
  endpoint   = "https://kms.us-east-1.amazonaws.com"
}

# Alternative: Shamir seal for non-cloud environments
# seal "shamir" {
#   # 5 shares, 3 required to unseal
# }

# Log level and format
log_level  = "info"
log_format = "json"

# PID file for process management
pid_file = "/vault/vault.pid"

# Cluster name
cluster_name = "toolboxai-vault"

# Disable mlock if running in container
disable_mlock = true

# Cache configuration
cache_size = "32000"

# Default and max lease TTLs
default_lease_ttl = "768h"  # 32 days
max_lease_ttl     = "8760h" # 365 days

# Plugin directory
plugin_directory = "/vault/plugins"

# Enable raw endpoint (disable in production)
raw_storage_endpoint = false

# Entropy augmentation (AWS only)
# entropy "seal" {
#   mode = "augmentation"
# }

# Service registration with Consul (optional)
# service_registration "consul" {
#   address = "127.0.0.1:8500"
#   service = "vault"
#   service_tags = ["active"]
# }