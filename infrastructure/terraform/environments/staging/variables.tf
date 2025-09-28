# ToolBoxAI Solutions - Staging Environment Variables

variable "aws_region" {
  description = "AWS region for staging environment"
  type        = string
  default     = "us-east-1"
}

variable "owner_email" {
  description = "Owner email for notifications"
  type        = string
}

variable "alert_email" {
  description = "Email for alerts in staging"
  type        = string
}

variable "allowed_ssh_ips" {
  description = "IP addresses allowed to SSH"
  type        = list(string)
  default     = []
}

# API Keys
variable "openai_api_key" {
  description = "OpenAI API key for staging"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key for staging"
  type        = string
  sensitive   = true
}

variable "pusher_app_id" {
  description = "Pusher app ID for staging"
  type        = string
  sensitive   = true
}

variable "pusher_key" {
  description = "Pusher key for staging"
  type        = string
  sensitive   = true
}

variable "pusher_secret" {
  description = "Pusher secret for staging"
  type        = string
  sensitive   = true
}

# Load Testing Configuration
variable "enable_load_testing" {
  description = "Enable automated load testing"
  type        = bool
  default     = true
}

variable "load_test_schedule" {
  description = "Cron schedule for automated load tests"
  type        = string
  default     = "0 2 * * MON-FRI"  # 2 AM weekdays
}

variable "load_test_duration_minutes" {
  description = "Duration of load tests in minutes"
  type        = number
  default     = 30
}

variable "load_test_concurrent_users" {
  description = "Number of concurrent users for load testing"
  type        = number
  default     = 100
}

# Blue-Green Deployment
variable "enable_blue_green" {
  description = "Enable blue-green deployment support"
  type        = bool
  default     = true
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for DNS records"
  type        = string
  default     = ""
}

variable "deployment_strategy" {
  description = "Deployment strategy (blue-green, rolling, canary)"
  type        = string
  default     = "blue-green"
  validation {
    condition     = contains(["blue-green", "rolling", "canary"], var.deployment_strategy)
    error_message = "Deployment strategy must be blue-green, rolling, or canary."
  }
}

# Synthetic Monitoring
variable "enable_synthetic_monitoring" {
  description = "Enable synthetic monitoring with CloudWatch Synthetics"
  type        = bool
  default     = true
}

variable "synthetic_monitoring_frequency" {
  description = "Frequency for synthetic monitoring checks"
  type        = string
  default     = "rate(5 minutes)"
}

variable "synthetic_monitoring_endpoints" {
  description = "List of endpoints to monitor synthetically"
  type        = list(string)
  default = [
    "/health",
    "/api/v1/status",
    "/api/v1/agents"
  ]
}

# Performance Testing
variable "enable_performance_testing" {
  description = "Enable automated performance testing"
  type        = bool
  default     = true
}

variable "performance_test_scenarios" {
  description = "Performance test scenarios configuration"
  type = map(object({
    endpoint           = string
    method            = string
    concurrent_users  = number
    duration_minutes  = number
    target_rps        = number
  }))
  default = {
    api_load = {
      endpoint          = "/api/v1/agents"
      method           = "GET"
      concurrent_users = 50
      duration_minutes = 10
      target_rps       = 100
    }
    websocket_load = {
      endpoint          = "/ws"
      method           = "WS"
      concurrent_users = 20
      duration_minutes = 5
      target_rps       = 50
    }
  }
}

# Security Testing
variable "enable_security_testing" {
  description = "Enable automated security testing"
  type        = bool
  default     = true
}

variable "security_test_schedule" {
  description = "Schedule for automated security tests"
  type        = string
  default     = "0 3 * * MON"  # 3 AM Monday
}

variable "security_test_types" {
  description = "Types of security tests to run"
  type        = list(string)
  default = [
    "vulnerability_scan",
    "dependency_check",
    "secrets_scan",
    "compliance_check"
  ]
}

# Data Seeding
variable "enable_data_seeding" {
  description = "Enable data seeding for staging environment"
  type        = bool
  default     = true
}

variable "data_seed_scenarios" {
  description = "Data seeding scenarios"
  type = map(object({
    agent_count     = number
    context_count   = number
    session_count   = number
    historical_days = number
  }))
  default = {
    minimal = {
      agent_count     = 5
      context_count   = 100
      session_count   = 50
      historical_days = 7
    }
    standard = {
      agent_count     = 20
      context_count   = 1000
      session_count   = 500
      historical_days = 30
    }
    stress = {
      agent_count     = 50
      context_count   = 10000
      session_count   = 5000
      historical_days = 90
    }
  }
}

variable "active_data_scenario" {
  description = "Active data seeding scenario"
  type        = string
  default     = "standard"
}

# Environment Management
variable "staging_refresh_schedule" {
  description = "Schedule for refreshing staging environment from production"
  type        = string
  default     = "0 1 * * SUN"  # 1 AM Sunday
}

variable "enable_auto_refresh" {
  description = "Enable automatic refresh of staging environment"
  type        = bool
  default     = false
}

variable "preserve_test_data" {
  description = "Preserve test data during environment refresh"
  type        = bool
  default     = true
}

# Monitoring and Alerting
variable "staging_alert_thresholds" {
  description = "Alert thresholds specific to staging environment"
  type = object({
    cpu_utilization_threshold     = number
    memory_utilization_threshold  = number
    response_time_threshold       = number
    error_rate_threshold          = number
  })
  default = {
    cpu_utilization_threshold     = 85
    memory_utilization_threshold  = 90
    response_time_threshold       = 2
    error_rate_threshold          = 5
  }
}

variable "enable_slack_notifications" {
  description = "Enable Slack notifications for staging"
  type        = bool
  default     = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for staging notifications"
  type        = string
  default     = ""
  sensitive   = true
}

# Cost Management
variable "staging_budget_limit" {
  description = "Monthly budget limit for staging environment (USD)"
  type        = number
  default     = 500
}

variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "spot_instance_percentage" {
  description = "Percentage of instances to run as spot instances"
  type        = number
  default     = 70
  validation {
    condition     = var.spot_instance_percentage >= 0 && var.spot_instance_percentage <= 100
    error_message = "Spot instance percentage must be between 0 and 100."
  }
}

# Database Management
variable "enable_database_cloning" {
  description = "Enable database cloning from production"
  type        = bool
  default     = false
}

variable "database_clone_schedule" {
  description = "Schedule for database cloning"
  type        = string
  default     = "0 2 * * SUN"  # 2 AM Sunday
}

variable "sanitize_cloned_data" {
  description = "Sanitize sensitive data in cloned database"
  type        = bool
  default     = true
}

# Feature Flags for Staging
variable "staging_feature_flags" {
  description = "Feature flags specific to staging environment"
  type = map(bool)
  default = {
    enable_experimental_features = true
    enable_debug_endpoints      = true
    enable_performance_profiling = true
    enable_chaos_engineering    = false
    enable_feature_toggles      = true
  }
}

# Compliance and Governance
variable "enable_compliance_testing" {
  description = "Enable compliance testing in staging"
  type        = bool
  default     = true
}

variable "compliance_frameworks" {
  description = "Compliance frameworks to test"
  type        = list(string)
  default     = ["SOC2", "GDPR"]
}

# Integration Testing
variable "enable_integration_testing" {
  description = "Enable automated integration testing"
  type        = bool
  default     = true
}

variable "integration_test_suites" {
  description = "Integration test suites to run"
  type        = list(string)
  default = [
    "api_integration",
    "database_integration",
    "external_service_integration",
    "websocket_integration"
  ]
}

variable "integration_test_schedule" {
  description = "Schedule for integration tests"
  type        = string
  default     = "0 */4 * * *"  # Every 4 hours
}