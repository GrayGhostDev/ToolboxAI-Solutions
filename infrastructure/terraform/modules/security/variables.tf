# ToolBoxAI Solutions - Security Module Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "vpc_id" {
  description = "VPC ID where security groups will be created"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "tags" {
  description = "A map of tags to assign to the resources"
  type        = map(string)
  default     = {}
}

# KMS Configuration
variable "enable_kms_key" {
  description = "Enable KMS key creation"
  type        = bool
  default     = true
}

variable "kms_deletion_window" {
  description = "The waiting period, specified in number of days, before the KMS key is deleted"
  type        = number
  default     = 7
  validation {
    condition     = var.kms_deletion_window >= 7 && var.kms_deletion_window <= 30
    error_message = "KMS deletion window must be between 7 and 30 days."
  }
}

# Security Group Configuration
variable "allowed_ssh_ips" {
  description = "List of IP addresses allowed to SSH"
  type        = list(string)
  default     = []
}

variable "allowed_http_ips" {
  description = "List of IP addresses allowed HTTP/HTTPS access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_http" {
  description = "Enable HTTP access (port 80)"
  type        = bool
  default     = true
}

variable "enable_bastion_access" {
  description = "Enable bastion host security group"
  type        = bool
  default     = false
}

# WAF Configuration
variable "enable_waf" {
  description = "Enable AWS WAF"
  type        = bool
  default     = true
}

variable "waf_rate_limit" {
  description = "Rate limit for WAF (requests per 5-minute period)"
  type        = number
  default     = 2000
  validation {
    condition     = var.waf_rate_limit >= 100 && var.waf_rate_limit <= 20000000
    error_message = "WAF rate limit must be between 100 and 20,000,000."
  }
}

variable "enable_waf_logging" {
  description = "Enable WAF logging to CloudWatch"
  type        = bool
  default     = true
}

variable "waf_log_retention_days" {
  description = "CloudWatch log retention for WAF logs"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.waf_log_retention_days)
    error_message = "Log retention must be a valid CloudWatch log retention value."
  }
}

variable "waf_blocked_countries" {
  description = "List of country codes to block in WAF"
  type        = list(string)
  default     = []
}

variable "waf_allowed_countries" {
  description = "List of country codes to allow in WAF (if specified, blocks all others)"
  type        = list(string)
  default     = []
}

# AWS Config
variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "config_delivery_frequency" {
  description = "Frequency for AWS Config snapshot delivery"
  type        = string
  default     = "TwentyFour_Hours"
  validation {
    condition = contains([
      "One_Hour", "Three_Hours", "Six_Hours", "Twelve_Hours", "TwentyFour_Hours"
    ], var.config_delivery_frequency)
    error_message = "Config delivery frequency must be a valid value."
  }
}

# GuardDuty
variable "enable_guardduty" {
  description = "Enable AWS GuardDuty"
  type        = bool
  default     = true
}

variable "guardduty_finding_publishing_frequency" {
  description = "Frequency of notifications sent for GuardDuty findings"
  type        = string
  default     = "SIX_HOURS"
  validation {
    condition = contains([
      "FIFTEEN_MINUTES", "ONE_HOUR", "SIX_HOURS"
    ], var.guardduty_finding_publishing_frequency)
    error_message = "GuardDuty finding publishing frequency must be a valid value."
  }
}

# Security Hub
variable "enable_security_hub" {
  description = "Enable AWS Security Hub"
  type        = bool
  default     = true
}

variable "security_hub_standards" {
  description = "List of Security Hub standards to enable"
  type        = list(string)
  default = [
    "arn:aws:securityhub:::ruleset/finding-format/aws-foundational-security",
    "arn:aws:securityhub:us-east-1::standard/cis-aws-foundations-benchmark/v/1.2.0"
  ]
}

# CloudTrail
variable "enable_cloudtrail" {
  description = "Enable AWS CloudTrail"
  type        = bool
  default     = true
}

variable "cloudtrail_log_retention_days" {
  description = "CloudWatch log retention for CloudTrail logs"
  type        = number
  default     = 90
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudtrail_log_retention_days)
    error_message = "Log retention must be a valid CloudWatch log retention value."
  }
}

variable "cloudtrail_include_global_service_events" {
  description = "Include global service events in CloudTrail"
  type        = bool
  default     = true
}

variable "cloudtrail_is_multi_region_trail" {
  description = "Make CloudTrail a multi-region trail"
  type        = bool
  default     = true
}

variable "cloudtrail_enable_log_file_validation" {
  description = "Enable log file validation for CloudTrail"
  type        = bool
  default     = true
}

# Inspector
variable "enable_inspector" {
  description = "Enable AWS Inspector"
  type        = bool
  default     = false
}

variable "inspector_assessment_duration" {
  description = "Duration of Inspector assessment in seconds"
  type        = number
  default     = 3600
}

# Secrets Manager
variable "enable_secrets_rotation" {
  description = "Enable automatic rotation for secrets"
  type        = bool
  default     = true
}

variable "secrets_rotation_days" {
  description = "Number of days between automatic rotations"
  type        = number
  default     = 30
  validation {
    condition     = var.secrets_rotation_days >= 1 && var.secrets_rotation_days <= 365
    error_message = "Secrets rotation days must be between 1 and 365."
  }
}

# Certificate Manager
variable "enable_acm_certificate" {
  description = "Enable ACM certificate creation"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for ACM certificate"
  type        = string
  default     = ""
}

variable "subject_alternative_names" {
  description = "Subject alternative names for ACM certificate"
  type        = list(string)
  default     = []
}

# Network Security
variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_destination_type" {
  description = "Destination type for VPC Flow Logs (cloud-watch-logs or s3)"
  type        = string
  default     = "cloud-watch-logs"
  validation {
    condition     = contains(["cloud-watch-logs", "s3"], var.flow_logs_destination_type)
    error_message = "Flow logs destination type must be 'cloud-watch-logs' or 's3'."
  }
}

variable "flow_logs_traffic_type" {
  description = "Type of traffic to capture in VPC Flow Logs"
  type        = string
  default     = "ALL"
  validation {
    condition     = contains(["ALL", "ACCEPT", "REJECT"], var.flow_logs_traffic_type)
    error_message = "Flow logs traffic type must be 'ALL', 'ACCEPT', or 'REJECT'."
  }
}

# DDoS Protection
variable "enable_shield_advanced" {
  description = "Enable AWS Shield Advanced"
  type        = bool
  default     = false
}

# Compliance
variable "enable_compliance_rules" {
  description = "Enable compliance-specific AWS Config rules"
  type        = bool
  default     = true
}

variable "compliance_framework" {
  description = "Compliance framework to follow (SOC2, HIPAA, PCI-DSS)"
  type        = string
  default     = "SOC2"
  validation {
    condition     = contains(["SOC2", "HIPAA", "PCI-DSS", "ISO27001"], var.compliance_framework)
    error_message = "Compliance framework must be SOC2, HIPAA, PCI-DSS, or ISO27001."
  }
}

# Notification
variable "security_notification_email" {
  description = "Email address for security notifications"
  type        = string
  default     = ""
}

variable "enable_slack_notifications" {
  description = "Enable Slack notifications for security events"
  type        = bool
  default     = false
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

# Advanced Security Features
variable "enable_macie" {
  description = "Enable AWS Macie for sensitive data discovery"
  type        = bool
  default     = false
}

variable "enable_detective" {
  description = "Enable AWS Detective for security investigation"
  type        = bool
  default     = false
}

variable "enable_network_firewall" {
  description = "Enable AWS Network Firewall"
  type        = bool
  default     = false
}

# Access Control
variable "enable_organizations_scp" {
  description = "Enable Organizations Service Control Policies"
  type        = bool
  default     = false
}

variable "enable_iam_access_analyzer" {
  description = "Enable IAM Access Analyzer"
  type        = bool
  default     = true
}

variable "iam_password_policy" {
  description = "IAM password policy configuration"
  type = object({
    minimum_password_length        = number
    require_lowercase_characters   = bool
    require_numbers               = bool
    require_uppercase_characters   = bool
    require_symbols               = bool
    allow_users_to_change_password = bool
    max_password_age              = number
    password_reuse_prevention     = number
    hard_expiry                   = bool
  })
  default = {
    minimum_password_length        = 14
    require_lowercase_characters   = true
    require_numbers               = true
    require_uppercase_characters   = true
    require_symbols               = true
    allow_users_to_change_password = true
    max_password_age              = 90
    password_reuse_prevention     = 12
    hard_expiry                   = false
  }
}

# Backup and Recovery
variable "enable_backup_vault" {
  description = "Enable AWS Backup vault"
  type        = bool
  default     = true
}

variable "backup_vault_kms_key_id" {
  description = "KMS key ID for backup vault encryption"
  type        = string
  default     = null
}