# ToolBoxAI Solutions - Monitoring Module Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "tags" {
  description = "A map of tags to assign to the resources"
  type        = map(string)
  default     = {}
}

# CloudWatch Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch log retention value."
  }
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "sns_topic_email" {
  description = "Email address for SNS notifications"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = null
}

# Monitored Resources
variable "monitored_resources" {
  description = "Map of resource identifiers to monitor"
  type = object({
    eks_cluster = string
    rds_cluster = string
    mcp_tables  = list(string)
  })
  default = {
    eks_cluster = ""
    rds_cluster = ""
    mcp_tables  = []
  }
}

# X-Ray Configuration
variable "enable_xray" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = false
}

variable "xray_sampling_rate" {
  description = "X-Ray sampling rate (0.0 to 1.0)"
  type        = number
  default     = 0.1
  validation {
    condition     = var.xray_sampling_rate >= 0.0 && var.xray_sampling_rate <= 1.0
    error_message = "X-Ray sampling rate must be between 0.0 and 1.0."
  }
}

variable "xray_reservoir_size" {
  description = "X-Ray reservoir size for sampling"
  type        = number
  default     = 1
  validation {
    condition     = var.xray_reservoir_size >= 0
    error_message = "X-Ray reservoir size must be non-negative."
  }
}

# Container Insights
variable "enable_container_insights" {
  description = "Enable Container Insights for EKS"
  type        = bool
  default     = true
}

# Alarm Thresholds
variable "alarm_thresholds" {
  description = "Threshold values for various alarms"
  type = object({
    cpu_utilization_threshold           = number
    memory_utilization_threshold        = number
    rds_cpu_threshold                  = number
    rds_connections_threshold          = number
    alb_response_time_threshold        = number
    alb_5xx_errors_threshold           = number
    lambda_errors_threshold            = number
    lambda_duration_threshold          = number
    dynamodb_throttles_threshold       = number
    application_errors_threshold       = number
  })
  default = {
    cpu_utilization_threshold           = 80
    memory_utilization_threshold        = 85
    rds_cpu_threshold                  = 80
    rds_connections_threshold          = 80
    alb_response_time_threshold        = 1
    alb_5xx_errors_threshold           = 10
    lambda_errors_threshold            = 5
    lambda_duration_threshold          = 25000
    dynamodb_throttles_threshold       = 0
    application_errors_threshold       = 10
  }
}

variable "alarm_evaluation_periods" {
  description = "Number of evaluation periods for alarms"
  type        = number
  default     = 2
  validation {
    condition     = var.alarm_evaluation_periods >= 1
    error_message = "Alarm evaluation periods must be at least 1."
  }
}

variable "alarm_period" {
  description = "Period in seconds for alarm evaluation"
  type        = number
  default     = 300
  validation {
    condition     = var.alarm_period >= 60
    error_message = "Alarm period must be at least 60 seconds."
  }
}

# Dashboard Configuration
variable "enable_dashboard" {
  description = "Enable CloudWatch dashboard creation"
  type        = bool
  default     = true
}

variable "dashboard_widgets" {
  description = "List of widgets to include in the dashboard"
  type        = list(string)
  default     = ["eks", "rds", "alb", "lambda", "logs"]
  validation {
    condition = alltrue([
      for widget in var.dashboard_widgets : contains(["eks", "rds", "alb", "lambda", "logs", "dynamodb", "custom"], widget)
    ])
    error_message = "Dashboard widgets must be from the allowed list: eks, rds, alb, lambda, logs, dynamodb, custom."
  }
}

# Log Groups Configuration
variable "custom_log_groups" {
  description = "Additional custom log groups to create"
  type = map(object({
    retention_in_days = number
    kms_key_id       = string
  }))
  default = {}
}

# Metric Filters
variable "custom_metric_filters" {
  description = "Custom metric filters to create"
  type = map(object({
    log_group_name = string
    filter_pattern = string
    metric_transformation = object({
      name      = string
      namespace = string
      value     = string
    })
  }))
  default = {}
}

# Cost Optimization
variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = true
}

variable "cost_anomaly_detection_threshold" {
  description = "Threshold for cost anomaly detection (USD)"
  type        = number
  default     = 100
  validation {
    condition     = var.cost_anomaly_detection_threshold > 0
    error_message = "Cost anomaly detection threshold must be positive."
  }
}

# Enhanced Monitoring
variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for resources"
  type        = bool
  default     = true
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights data retention period in days"
  type        = number
  default     = 7
  validation {
    condition     = contains([7, 731], var.performance_insights_retention_period)
    error_message = "Performance Insights retention period must be 7 or 731 days."
  }
}

# Service Map and Distributed Tracing
variable "enable_service_map" {
  description = "Enable X-Ray service map"
  type        = bool
  default     = true
}

variable "enable_distributed_tracing" {
  description = "Enable distributed tracing for applications"
  type        = bool
  default     = true
}

# Custom Metrics
variable "custom_metrics" {
  description = "Custom CloudWatch metrics to create"
  type = map(object({
    namespace   = string
    metric_name = string
    dimensions  = map(string)
    unit        = string
  }))
  default = {}
}

# Log Shipping Configuration
variable "enable_log_shipping" {
  description = "Enable log shipping to external systems"
  type        = bool
  default     = false
}

variable "log_shipping_destination" {
  description = "Destination for log shipping (elasticsearch, splunk, datadog)"
  type        = string
  default     = "elasticsearch"
  validation {
    condition     = contains(["elasticsearch", "splunk", "datadog", "s3"], var.log_shipping_destination)
    error_message = "Log shipping destination must be elasticsearch, splunk, datadog, or s3."
  }
}

variable "log_shipping_config" {
  description = "Configuration for log shipping"
  type = object({
    endpoint = string
    api_key  = string
    index    = string
  })
  default = {
    endpoint = ""
    api_key  = ""
    index    = ""
  }
  sensitive = true
}

# Notification Configuration
variable "notification_channels" {
  description = "Notification channels configuration"
  type = object({
    email_enabled      = bool
    slack_enabled      = bool
    pagerduty_enabled  = bool
    webhook_enabled    = bool
  })
  default = {
    email_enabled      = true
    slack_enabled      = false
    pagerduty_enabled  = false
    webhook_enabled    = false
  }
}

variable "pagerduty_integration_key" {
  description = "PagerDuty integration key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "webhook_url" {
  description = "Webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

# Advanced Monitoring Features
variable "enable_anomaly_detection" {
  description = "Enable CloudWatch Anomaly Detection"
  type        = bool
  default     = false
}

variable "anomaly_detection_metrics" {
  description = "Metrics to monitor for anomalies"
  type        = list(string)
  default     = ["CPUUtilization", "NetworkIn", "NetworkOut"]
}

variable "enable_application_insights" {
  description = "Enable CloudWatch Application Insights"
  type        = bool
  default     = false
}

variable "application_insights_config" {
  description = "Configuration for Application Insights"
  type = object({
    resource_group_name = string
    application_type    = string
  })
  default = {
    resource_group_name = ""
    application_type    = "OTHER"
  }
}

# Backup and Archival
variable "enable_log_archival" {
  description = "Enable automatic log archival to S3"
  type        = bool
  default     = true
}

variable "log_archival_days" {
  description = "Days after which logs are archived to S3"
  type        = number
  default     = 30
  validation {
    condition     = var.log_archival_days > 0
    error_message = "Log archival days must be positive."
  }
}

variable "log_archival_storage_class" {
  description = "S3 storage class for archived logs"
  type        = string
  default     = "STANDARD_IA"
  validation {
    condition = contains([
      "STANDARD", "STANDARD_IA", "ONEZONE_IA", "REDUCED_REDUNDANCY", "GLACIER", "DEEP_ARCHIVE"
    ], var.log_archival_storage_class)
    error_message = "Invalid S3 storage class for log archival."
  }
}

# Compliance and Governance
variable "enable_compliance_monitoring" {
  description = "Enable compliance monitoring"
  type        = bool
  default     = true
}

variable "compliance_framework" {
  description = "Compliance framework to monitor"
  type        = string
  default     = "SOC2"
  validation {
    condition     = contains(["SOC2", "HIPAA", "PCI-DSS", "ISO27001"], var.compliance_framework)
    error_message = "Compliance framework must be SOC2, HIPAA, PCI-DSS, or ISO27001."
  }
}

variable "enable_audit_logging" {
  description = "Enable audit logging for monitoring activities"
  type        = bool
  default     = true
}

# Resource Tagging for Monitoring
variable "monitoring_tags" {
  description = "Additional tags specific to monitoring resources"
  type        = map(string)
  default = {
    MonitoringEnabled = "true"
    AlertingEnabled   = "true"
  }
}