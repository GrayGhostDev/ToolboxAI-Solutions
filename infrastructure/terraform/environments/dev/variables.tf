# ToolBoxAI Solutions - Development Environment Variables

variable "aws_region" {
  description = "AWS region for development environment"
  type        = string
  default     = "us-east-1"
}

variable "owner_email" {
  description = "Owner email for notifications"
  type        = string
}

variable "alert_email" {
  description = "Email for alerts in development"
  type        = string
}

variable "allowed_ssh_ips" {
  description = "IP addresses allowed to SSH (for bastion and debugging)"
  type        = list(string)
  default     = []
}

# API Keys (should be provided via environment variables or parameter store)
variable "openai_api_key" {
  description = "OpenAI API key for development"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key for development"
  type        = string
  sensitive   = true
}

variable "pusher_app_id" {
  description = "Pusher app ID for development"
  type        = string
  sensitive   = true
}

variable "pusher_key" {
  description = "Pusher key for development"
  type        = string
  sensitive   = true
}

variable "pusher_secret" {
  description = "Pusher secret for development"
  type        = string
  sensitive   = true
}

# Development-specific variables
variable "enable_bastion" {
  description = "Enable bastion host for development debugging"
  type        = bool
  default     = true
}

variable "bastion_key_name" {
  description = "EC2 Key Pair name for bastion host"
  type        = string
  default     = "dev-toolboxai-key"
}

variable "auto_shutdown_schedule" {
  description = "Schedule for auto-shutdown of development resources"
  type        = string
  default     = "0 22 * * MON-FRI"  # Shutdown at 10 PM Monday-Friday
}

variable "auto_startup_schedule" {
  description = "Schedule for auto-startup of development resources"
  type        = string
  default     = "0 8 * * MON-FRI"   # Start at 8 AM Monday-Friday
}

variable "enable_auto_shutdown" {
  description = "Enable automatic shutdown/startup of development resources"
  type        = bool
  default     = true
}

variable "developer_access_hours" {
  description = "Hours when developers typically access the environment"
  type = object({
    start_hour = number
    end_hour   = number
    timezone   = string
  })
  default = {
    start_hour = 8
    end_hour   = 22
    timezone   = "America/New_York"
  }
}

variable "enable_cost_alerts" {
  description = "Enable cost alerts for development environment"
  type        = bool
  default     = true
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit for development environment (USD)"
  type        = number
  default     = 200
}

variable "enable_debug_logging" {
  description = "Enable debug-level logging for development"
  type        = bool
  default     = true
}

variable "temporary_access_duration" {
  description = "Duration for temporary access credentials (hours)"
  type        = number
  default     = 8
}

variable "cleanup_retention_days" {
  description = "Days to retain resources before cleanup in development"
  type        = number
  default     = 7
}

variable "enable_experimental_features" {
  description = "Enable experimental features in development"
  type        = bool
  default     = true
}

variable "mock_external_services" {
  description = "Use mock external services for development"
  type        = bool
  default     = false
}

variable "local_development_mode" {
  description = "Configure for local development integration"
  type        = bool
  default     = false
}

variable "developer_workstation_ips" {
  description = "IP addresses of developer workstations for direct access"
  type        = list(string)
  default     = []
}

variable "enable_hot_reload" {
  description = "Enable hot reload capabilities for development"
  type        = bool
  default     = true
}

variable "resource_tags" {
  description = "Additional tags for development resources"
  type        = map(string)
  default = {
    Environment   = "development"
    AutoShutdown  = "enabled"
    CostCenter    = "engineering"
    Backup        = "minimal"
    Monitoring    = "basic"
  }
}