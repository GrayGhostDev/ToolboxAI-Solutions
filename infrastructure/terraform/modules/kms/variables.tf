# KMS Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "toolboxai"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "deletion_window" {
  description = "KMS key deletion window in days (7-30)"
  type        = number
  default     = 30
  validation {
    condition     = var.deletion_window >= 7 && var.deletion_window <= 30
    error_message = "Deletion window must be between 7 and 30 days."
  }
}

variable "multi_region" {
  description = "Enable multi-region replication for keys"
  type        = bool
  default     = false
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy   = "Terraform"
    Project     = "ToolBoxAI"
    CostCenter  = "Engineering"
    Compliance  = "COPPA,FERPA,GDPR"
  }
}

variable "eks_node_role_arns" {
  description = "List of EKS node role ARNs that need access to KMS keys"
  type        = list(string)
  default     = []
}

variable "eks_service_account_arns" {
  description = "List of EKS service account ARNs for IRSA"
  type        = list(string)
  default     = []
}

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs that need decrypt access"
  type        = list(string)
  default     = []
}

variable "kms_usage_threshold" {
  description = "Threshold for KMS usage alerts"
  type        = number
  default     = 10000
}

variable "sns_alert_topic_arns" {
  description = "SNS topic ARNs for CloudWatch alarms"
  type        = list(string)
  default     = []
}

variable "enable_key_rotation" {
  description = "Enable automatic key rotation for all KMS keys"
  type        = bool
  default     = true
}

variable "enable_cloudwatch_monitoring" {
  description = "Enable CloudWatch monitoring and alerting"
  type        = bool
  default     = true
}

variable "key_administrators" {
  description = "List of IAM ARNs that can administer KMS keys"
  type        = list(string)
  default     = []
}

variable "key_users" {
  description = "List of IAM ARNs that can use KMS keys for encryption/decryption"
  type        = list(string)
  default     = []
}

variable "enable_default_policy" {
  description = "Enable default key policy allowing root account full access"
  type        = bool
  default     = true
}

variable "custom_key_policies" {
  description = "Map of custom key policies by key type"
  type        = map(string)
  default     = {}
}

# Compliance-specific settings
variable "coppa_compliance" {
  description = "Enable COPPA compliance features"
  type        = bool
  default     = true
}

variable "ferpa_compliance" {
  description = "Enable FERPA compliance features"
  type        = bool
  default     = true
}

variable "gdpr_compliance" {
  description = "Enable GDPR compliance features"
  type        = bool
  default     = true
}

# Advanced encryption settings
variable "customer_master_key_spec" {
  description = "Key spec for customer master keys"
  type        = string
  default     = "SYMMETRIC_DEFAULT"
  validation {
    condition = contains([
      "SYMMETRIC_DEFAULT",
      "RSA_2048",
      "RSA_3072",
      "RSA_4096",
      "ECC_NIST_P256",
      "ECC_NIST_P384",
      "ECC_NIST_P521",
      "ECC_SECG_P256K1"
    ], var.customer_master_key_spec)
    error_message = "Invalid customer master key spec."
  }
}

variable "key_usage" {
  description = "Intended use of the key"
  type        = string
  default     = "ENCRYPT_DECRYPT"
  validation {
    condition     = contains(["ENCRYPT_DECRYPT", "SIGN_VERIFY"], var.key_usage)
    error_message = "Key usage must be ENCRYPT_DECRYPT or SIGN_VERIFY."
  }
}

# Cost optimization
variable "pending_window_in_days" {
  description = "Number of days to wait before deleting a key"
  type        = number
  default     = 30
}

variable "bypass_policy_lockout_safety_check" {
  description = "Bypass the key policy lockout safety check"
  type        = bool
  default     = false
}

# Service-specific encryption settings
variable "enable_s3_bucket_key" {
  description = "Enable S3 bucket key for cost optimization"
  type        = bool
  default     = true
}

variable "enable_rds_encryption" {
  description = "Enable RDS database encryption"
  type        = bool
  default     = true
}

variable "enable_ebs_encryption_by_default" {
  description = "Enable EBS encryption by default for the region"
  type        = bool
  default     = true
}

# Audit and logging
variable "enable_key_usage_logging" {
  description = "Enable CloudTrail logging for key usage"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 90
}

# Cross-account access
variable "trusted_account_ids" {
  description = "List of AWS account IDs trusted for cross-account access"
  type        = list(string)
  default     = []
}

variable "external_key_users" {
  description = "Map of external principals and their allowed KMS operations"
  type = map(object({
    principal  = string
    operations = list(string)
  }))
  default = {}
}