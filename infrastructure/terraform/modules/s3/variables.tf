# S3 Module Variables

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

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    ManagedBy  = "Terraform"
    Project    = "ToolBoxAI"
    CostCenter = "Engineering"
  }
}

# Encryption Settings
variable "kms_key_arn" {
  description = "ARN of KMS key for S3 encryption"
  type        = string
}

# Compliance Settings
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

# Access Control
variable "allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default = [
    "https://app.toolboxai.solutions",
    "https://toolboxai.solutions"
  ]
}

variable "cloudfront_distribution_arn" {
  description = "ARN of CloudFront distribution for static assets"
  type        = string
  default     = ""
}

# Logging and Monitoring
variable "enable_audit_logging" {
  description = "Enable audit logging bucket with object lock"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 90
}

variable "bucket_size_alarm_threshold" {
  description = "Bucket size threshold in bytes for CloudWatch alarms"
  type        = number
  default     = 107374182400 # 100 GB
}

variable "sns_alert_topic_arns" {
  description = "SNS topic ARNs for CloudWatch alarms"
  type        = list(string)
  default     = []
}

# Event Notifications
variable "enable_event_notifications" {
  description = "Enable S3 event notifications"
  type        = bool
  default     = false
}

variable "content_processor_lambda_arn" {
  description = "ARN of Lambda function for content processing"
  type        = string
  default     = ""
}

variable "processing_queue_arn" {
  description = "ARN of SQS queue for processing events"
  type        = string
  default     = ""
}

# Lifecycle Management
variable "enable_intelligent_tiering" {
  description = "Enable Intelligent-Tiering for cost optimization"
  type        = bool
  default     = true
}

variable "backup_transition_days" {
  description = "Days before transitioning backups to cheaper storage"
  type = object({
    to_ia           = number
    to_glacier      = number
    to_deep_archive = number
  })
  default = {
    to_ia           = 30
    to_glacier      = 90
    to_deep_archive = 365
  }
}

# Versioning
variable "enable_versioning" {
  description = "Enable versioning for all buckets"
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  description = "Days before deleting noncurrent versions"
  type        = number
  default     = 90
}

# Replication
variable "enable_replication" {
  description = "Enable cross-region replication"
  type        = bool
  default     = false
}

variable "replication_destination_region" {
  description = "Destination region for replication"
  type        = string
  default     = "us-west-2"
}

variable "replication_destination_bucket_arn" {
  description = "ARN of destination bucket for replication"
  type        = string
  default     = ""
}

# Object Lock
variable "enable_object_lock" {
  description = "Enable object lock for compliance"
  type        = bool
  default     = false
}

variable "object_lock_mode" {
  description = "Object lock mode (COMPLIANCE or GOVERNANCE)"
  type        = string
  default     = "COMPLIANCE"
  validation {
    condition     = contains(["COMPLIANCE", "GOVERNANCE"], var.object_lock_mode)
    error_message = "Object lock mode must be COMPLIANCE or GOVERNANCE."
  }
}

variable "object_lock_days" {
  description = "Number of days for object lock retention"
  type        = number
  default     = 2555 # 7 years
}

# Access Points
variable "create_access_points" {
  description = "Create S3 access points for fine-grained access"
  type        = bool
  default     = false
}

variable "access_point_configs" {
  description = "Configuration for S3 access points"
  type = map(object({
    name               = string
    public_access_block = bool
    policy             = string
  }))
  default = {}
}

# Performance
variable "transfer_acceleration" {
  description = "Enable transfer acceleration for uploads"
  type        = bool
  default     = false
}

variable "request_payer" {
  description = "Who pays for requests (BucketOwner or Requester)"
  type        = string
  default     = "BucketOwner"
  validation {
    condition     = contains(["BucketOwner", "Requester"], var.request_payer)
    error_message = "Request payer must be BucketOwner or Requester."
  }
}

# Cost Management
variable "storage_class" {
  description = "Default storage class for objects"
  type        = string
  default     = "STANDARD"
  validation {
    condition = contains([
      "STANDARD",
      "REDUCED_REDUNDANCY",
      "STANDARD_IA",
      "ONEZONE_IA",
      "INTELLIGENT_TIERING",
      "GLACIER",
      "DEEP_ARCHIVE"
    ], var.storage_class)
    error_message = "Invalid storage class."
  }
}

# Bucket Policies
variable "additional_bucket_policies" {
  description = "Additional bucket policies to apply"
  type        = map(string)
  default     = {}
}

# Data Classification
variable "data_classification" {
  description = "Data classification levels for buckets"
  type = object({
    content       = string
    user_uploads  = string
    backups       = string
    static_assets = string
    audit_logs    = string
  })
  default = {
    content       = "Internal"
    user_uploads  = "Confidential"
    backups       = "Restricted"
    static_assets = "Public"
    audit_logs    = "Restricted"
  }
}