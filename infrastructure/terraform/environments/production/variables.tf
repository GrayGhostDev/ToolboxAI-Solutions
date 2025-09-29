# ToolBoxAI Solutions - Production Environment Variables

variable "aws_region" {
  description = "AWS region for production environment"
  type        = string
  default     = "us-east-1"
}

variable "disaster_recovery_region" {
  description = "AWS region for disaster recovery"
  type        = string
  default     = "us-west-2"
}

variable "owner_email" {
  description = "Owner email for notifications"
  type        = string
}

variable "alert_email" {
  description = "Email for standard alerts in production"
  type        = string
}

variable "critical_alert_email" {
  description = "Email for critical alerts (may be different from standard alerts)"
  type        = string
}

variable "allowed_ssh_ips" {
  description = "IP addresses allowed to SSH (should be very restricted in production)"
  type        = list(string)
  default     = []
}

# API Keys
variable "openai_api_key" {
  description = "OpenAI API key for production"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key for production"
  type        = string
  sensitive   = true
}

variable "pusher_app_id" {
  description = "Pusher app ID for production"
  type        = string
  sensitive   = true
}

variable "pusher_key" {
  description = "Pusher key for production"
  type        = string
  sensitive   = true
}

variable "pusher_secret" {
  description = "Pusher secret for production"
  type        = string
  sensitive   = true
}

# Domain and SSL Configuration
variable "domain_name" {
  description = "Primary domain name for production"
  type        = string
  default     = "toolboxai.solutions"
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for CloudFront"
  type        = string
}

variable "cloudfront_aliases" {
  description = "List of domain aliases for CloudFront"
  type        = list(string)
  default     = ["toolboxai.solutions", "www.toolboxai.solutions"]
}

variable "cloudfront_price_class" {
  description = "Price class for CloudFront distribution"
  type        = string
  default     = "PriceClass_100"
  validation {
    condition = contains([
      "PriceClass_All", "PriceClass_200", "PriceClass_100"
    ], var.cloudfront_price_class)
    error_message = "CloudFront price class must be PriceClass_All, PriceClass_200, or PriceClass_100."
  }
}

# High Availability Configuration
variable "enable_multi_region" {
  description = "Enable multi-region deployment"
  type        = bool
  default     = false
}

variable "enable_disaster_recovery" {
  description = "Enable disaster recovery setup in secondary region"
  type        = bool
  default     = true
}

variable "enable_vpc_peering" {
  description = "Enable VPC peering between regions"
  type        = bool
  default     = false
}

variable "dr_kms_key_arn" {
  description = "KMS key ARN for disaster recovery region"
  type        = string
  default     = ""
}

# Security Configuration
variable "enable_shield_advanced" {
  description = "Enable AWS Shield Advanced for DDoS protection"
  type        = bool
  default     = false
}

variable "enable_waf_geo_blocking" {
  description = "Enable WAF geographic blocking"
  type        = bool
  default     = false
}

variable "blocked_countries" {
  description = "List of country codes to block"
  type        = list(string)
  default     = []
}

variable "allowed_countries" {
  description = "List of country codes to allow (blocks all others if specified)"
  type        = list(string)
  default     = []
}

# Monitoring and Alerting
variable "pagerduty_endpoint" {
  description = "PagerDuty webhook endpoint for critical alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring and observability"
  type        = bool
  default     = true
}

variable "monitoring_retention_years" {
  description = "Retention period for monitoring data in years"
  type        = number
  default     = 7
  validation {
    condition     = var.monitoring_retention_years >= 1 && var.monitoring_retention_years <= 10
    error_message = "Monitoring retention must be between 1 and 10 years."
  }
}

# Performance Configuration
variable "enable_performance_insights" {
  description = "Enable RDS Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 731  # 2 years
  validation {
    condition     = contains([7, 731], var.performance_insights_retention_period)
    error_message = "Performance Insights retention must be 7 or 731 days."
  }
}

# Cost Optimization
variable "enable_reserved_instances" {
  description = "Enable reserved instances for cost optimization"
  type        = bool
  default     = true
}

variable "reserved_instance_count" {
  description = "Number of reserved instances to purchase"
  type        = number
  default     = 10
}

variable "enable_savings_plans" {
  description = "Enable AWS Savings Plans"
  type        = bool
  default     = true
}

variable "savings_plan_commitment" {
  description = "Hourly commitment for Savings Plans (USD)"
  type        = number
  default     = 100
}

# Compliance Configuration
variable "compliance_frameworks" {
  description = "Compliance frameworks to adhere to"
  type        = list(string)
  default     = ["SOC2", "GDPR", "HIPAA"]
}

variable "enable_audit_logging" {
  description = "Enable comprehensive audit logging"
  type        = bool
  default     = true
}

variable "audit_log_retention_years" {
  description = "Audit log retention period in years"
  type        = number
  default     = 7
}

variable "enable_data_encryption" {
  description = "Enable encryption for all data at rest and in transit"
  type        = bool
  default     = true
}

# Backup and Recovery
variable "backup_retention_years" {
  description = "Backup retention period in years"
  type        = number
  default     = 7
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = true
}

variable "backup_schedule" {
  description = "Backup schedule configuration"
  type = object({
    daily_backup_time   = string
    weekly_backup_day   = string
    monthly_backup_day  = number
    yearly_backup_month = number
  })
  default = {
    daily_backup_time   = "05:00"
    weekly_backup_day   = "SUN"
    monthly_backup_day  = 1
    yearly_backup_month = 1
  }
}

# Scaling Configuration
variable "auto_scaling_policies" {
  description = "Auto-scaling policies for production workloads"
  type = object({
    scale_up_threshold    = number
    scale_down_threshold  = number
    scale_up_cooldown     = number
    scale_down_cooldown   = number
    min_capacity          = number
    max_capacity          = number
  })
  default = {
    scale_up_threshold    = 60
    scale_down_threshold  = 30
    scale_up_cooldown     = 60
    scale_down_cooldown   = 300
    min_capacity          = 5
    max_capacity          = 50
  }
}

variable "enable_predictive_scaling" {
  description = "Enable predictive scaling based on historical patterns"
  type        = bool
  default     = true
}

# Database Configuration
variable "database_performance_tier" {
  description = "Database performance tier (standard, high, enterprise)"
  type        = string
  default     = "high"
  validation {
    condition     = contains(["standard", "high", "enterprise"], var.database_performance_tier)
    error_message = "Database performance tier must be standard, high, or enterprise."
  }
}

variable "enable_read_replicas" {
  description = "Enable read replicas for database scaling"
  type        = bool
  default     = true
}

variable "read_replica_count" {
  description = "Number of read replicas"
  type        = number
  default     = 2
  validation {
    condition     = var.read_replica_count >= 0 && var.read_replica_count <= 15
    error_message = "Read replica count must be between 0 and 15."
  }
}

# CDN Configuration
variable "cdn_configuration" {
  description = "CDN configuration settings"
  type = object({
    enable_compression       = bool
    enable_http2            = bool
    cache_policy_id         = string
    origin_request_policy_id = string
    response_headers_policy_id = string
  })
  default = {
    enable_compression       = true
    enable_http2            = true
    cache_policy_id         = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"  # CachingDisabled
    origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"  # CORS-S3Origin
    response_headers_policy_id = "67f7725c-6f97-4210-82d7-5512b31e9d03"  # SecurityHeadersPolicy
  }
}

# Security Headers
variable "security_headers" {
  description = "Security headers configuration"
  type = object({
    enable_hsts              = bool
    enable_content_type_options = bool
    enable_frame_options     = bool
    enable_xss_protection    = bool
    enable_referrer_policy   = bool
    enable_csp              = bool
    csp_directive           = string
  })
  default = {
    enable_hsts              = true
    enable_content_type_options = true
    enable_frame_options     = true
    enable_xss_protection    = true
    enable_referrer_policy   = true
    enable_csp              = true
    csp_directive           = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
  }
}

# API Rate Limiting
variable "api_rate_limits" {
  description = "API rate limiting configuration"
  type = object({
    requests_per_second = number
    burst_capacity     = number
    enable_throttling  = bool
  })
  default = {
    requests_per_second = 1000
    burst_capacity     = 2000
    enable_throttling  = true
  }
}

# Maintenance Windows
variable "maintenance_windows" {
  description = "Maintenance windows for different services"
  type = object({
    database_maintenance_window = string
    cluster_maintenance_window  = string
    system_maintenance_window   = string
  })
  default = {
    database_maintenance_window = "sun:03:00-sun:04:00"
    cluster_maintenance_window  = "sun:04:00-sun:05:00"
    system_maintenance_window   = "sun:02:00-sun:06:00"
  }
}

# Data Retention Policies
variable "data_retention_policies" {
  description = "Data retention policies for different data types"
  type = object({
    application_logs_days = number
    access_logs_days     = number
    metrics_data_days    = number
    user_data_years      = number
    backup_data_years    = number
  })
  default = {
    application_logs_days = 365
    access_logs_days     = 90
    metrics_data_days    = 365
    user_data_years      = 7
    backup_data_years    = 7
  }
}

# Feature Flags for Production
variable "production_feature_flags" {
  description = "Feature flags specific to production environment"
  type = map(bool)
  default = {
    enable_experimental_features = false
    enable_debug_endpoints      = false
    enable_admin_panel          = true
    enable_metrics_dashboard    = true
    enable_health_checks        = true
    enable_graceful_shutdown    = true
    enable_circuit_breakers     = true
    enable_retry_mechanisms     = true
  }
}

# Business Continuity
variable "business_continuity_config" {
  description = "Business continuity configuration"
  type = object({
    rto_minutes = number  # Recovery Time Objective
    rpo_minutes = number  # Recovery Point Objective
    enable_chaos_engineering = bool
    enable_disaster_recovery_testing = bool
  })
  default = {
    rto_minutes = 60   # 1 hour
    rpo_minutes = 15   # 15 minutes
    enable_chaos_engineering = false
    enable_disaster_recovery_testing = true
  }
}

# Support and Operations
variable "support_configuration" {
  description = "Support and operations configuration"
  type = object({
    enable_24x7_monitoring = bool
    escalation_levels     = number
    on_call_rotation_hours = number
  })
  default = {
    enable_24x7_monitoring = true
    escalation_levels     = 3
    on_call_rotation_hours = 168  # 1 week
  }
}