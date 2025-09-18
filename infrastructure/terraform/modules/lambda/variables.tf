# Lambda Module Variables

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

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
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

# Runtime Configuration
variable "runtime_type" {
  description = "Type of runtime (python or nodejs)"
  type        = string
  default     = "python"
  validation {
    condition     = contains(["python", "nodejs"], var.runtime_type)
    error_message = "Runtime type must be python or nodejs."
  }
}

variable "python_runtime" {
  description = "Python runtime version"
  type        = string
  default     = "python3.11"
}

variable "nodejs_runtime" {
  description = "Node.js runtime version"
  type        = string
  default     = "nodejs20.x"
}

variable "architecture" {
  description = "Instruction set architecture (x86_64 or arm64)"
  type        = string
  default     = "x86_64"
  validation {
    condition     = contains(["x86_64", "arm64"], var.architecture)
    error_message = "Architecture must be x86_64 or arm64."
  }
}

# Code Configuration
variable "filename" {
  description = "Path to the function's deployment package"
  type        = string
}

variable "source_code_hash" {
  description = "Hash of the deployment package file"
  type        = string
  default     = null
}

variable "handler" {
  description = "Function entrypoint (e.g., index.handler)"
  type        = string
  default     = ""
}

# Resource Configuration
variable "memory_size" {
  description = "Amount of memory in MB (128 - 10240)"
  type        = number
  default     = 512
  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 and 10240 MB."
  }
}

variable "timeout" {
  description = "Function timeout in seconds (1 - 900)"
  type        = number
  default     = 30
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "ephemeral_storage_size" {
  description = "Ephemeral storage in MB (512 - 10240)"
  type        = number
  default     = 512
  validation {
    condition     = var.ephemeral_storage_size >= 512 && var.ephemeral_storage_size <= 10240
    error_message = "Ephemeral storage must be between 512 and 10240 MB."
  }
}

variable "reserved_concurrent_executions" {
  description = "Reserved concurrent executions (-1 for unreserved)"
  type        = number
  default     = -1
}

# Environment Variables
variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# VPC Configuration
variable "vpc_id" {
  description = "VPC ID for Lambda function"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for Lambda function"
  type        = list(string)
  default     = []
}

variable "additional_security_group_ids" {
  description = "Additional security group IDs"
  type        = list(string)
  default     = []
}

# Encryption
variable "kms_key_arn" {
  description = "KMS key ARN for environment variables encryption"
  type        = string
  default     = ""
}

# Tracing
variable "tracing_mode" {
  description = "X-Ray tracing mode (PassThrough or Active)"
  type        = string
  default     = "PassThrough"
  validation {
    condition     = contains(["PassThrough", "Active"], var.tracing_mode)
    error_message = "Tracing mode must be PassThrough or Active."
  }
}

# Dead Letter Queue
variable "dead_letter_queue_arn" {
  description = "ARN of SQS queue or SNS topic for failed executions"
  type        = string
  default     = ""
}

# Layers
variable "create_layer" {
  description = "Create a Lambda layer for dependencies"
  type        = bool
  default     = false
}

variable "layer_filename" {
  description = "Path to the layer deployment package"
  type        = string
  default     = ""
}

variable "additional_layers" {
  description = "Additional Lambda layer ARNs"
  type        = list(string)
  default     = []
}

# Versioning
variable "publish" {
  description = "Publish a new version on changes"
  type        = bool
  default     = true
}

variable "canary_deployment_percentage" {
  description = "Percentage of traffic for canary deployment (0-100)"
  type        = number
  default     = 0
  validation {
    condition     = var.canary_deployment_percentage >= 0 && var.canary_deployment_percentage <= 100
    error_message = "Canary deployment percentage must be between 0 and 100."
  }
}

# Logging
variable "log_format" {
  description = "Log format (JSON or Text)"
  type        = string
  default     = "JSON"
  validation {
    condition     = contains(["JSON", "Text"], var.log_format)
    error_message = "Log format must be JSON or Text."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Function URL
variable "create_function_url" {
  description = "Create a function URL for HTTP access"
  type        = bool
  default     = false
}

variable "function_url_auth_type" {
  description = "Authorization type for function URL"
  type        = string
  default     = "AWS_IAM"
  validation {
    condition     = contains(["AWS_IAM", "NONE"], var.function_url_auth_type)
    error_message = "Function URL auth type must be AWS_IAM or NONE."
  }
}

# CORS Configuration
variable "cors_allow_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allow_methods" {
  description = "CORS allowed methods"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allow_headers" {
  description = "CORS allowed headers"
  type        = list(string)
  default     = ["*"]
}

variable "cors_expose_headers" {
  description = "CORS expose headers"
  type        = list(string)
  default     = []
}

variable "cors_max_age" {
  description = "CORS max age in seconds"
  type        = number
  default     = 86400
}

variable "cors_allow_credentials" {
  description = "CORS allow credentials"
  type        = bool
  default     = false
}

# Async Configuration
variable "maximum_event_age_in_seconds" {
  description = "Maximum age of a request in seconds"
  type        = number
  default     = 21600
}

variable "maximum_retry_attempts" {
  description = "Maximum number of retry attempts"
  type        = number
  default     = 2
}

variable "on_success_destination_arn" {
  description = "ARN of destination for successful invocations"
  type        = string
  default     = ""
}

variable "on_failure_destination_arn" {
  description = "ARN of destination for failed invocations"
  type        = string
  default     = ""
}

# Permissions and Policies
variable "secrets_manager_arns" {
  description = "Secrets Manager secret ARNs to access"
  type        = list(string)
  default     = []
}

variable "s3_bucket_arns" {
  description = "S3 bucket ARNs to access"
  type        = list(string)
  default     = []
}

variable "dynamodb_table_arns" {
  description = "DynamoDB table ARNs to access"
  type        = list(string)
  default     = []
}

variable "sqs_queue_arns" {
  description = "SQS queue ARNs to access"
  type        = list(string)
  default     = []
}

variable "additional_policy_statements" {
  description = "Additional IAM policy statements"
  type        = list(any)
  default     = []
}

# Triggers and Integrations
variable "api_gateway_execution_arn" {
  description = "API Gateway execution ARN for Lambda permission"
  type        = string
  default     = ""
}

variable "eventbridge_rules" {
  description = "Map of EventBridge rule ARNs that can invoke the function"
  type        = map(string)
  default     = {}
}

variable "s3_triggers" {
  description = "Map of S3 bucket ARNs that can invoke the function"
  type        = map(string)
  default     = {}
}

variable "sqs_triggers" {
  description = "Map of SQS queue configurations for event source mapping"
  type = map(object({
    queue_arn            = string
    batch_size          = number
    batching_window     = number
    maximum_concurrency = number
  }))
  default = {}
}

# CloudWatch Alarms
variable "sns_topic_arns" {
  description = "SNS topic ARNs for CloudWatch alarms"
  type        = list(string)
  default     = []
}

variable "error_rate_threshold" {
  description = "Error rate threshold for alarms"
  type        = number
  default     = 10
}

variable "throttle_threshold" {
  description = "Throttle threshold for alarms"
  type        = number
  default     = 10
}

variable "duration_threshold" {
  description = "Duration threshold in milliseconds for alarms"
  type        = number
  default     = 3000
}

# Compliance
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