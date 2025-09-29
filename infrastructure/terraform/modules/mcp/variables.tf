# MCP Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
}

variable "lambda_subnet_ids" {
  description = "Subnet IDs for Lambda functions"
  type        = list(string)
  default     = []
}

variable "dynamodb_tables" {
  description = "Configuration for DynamoDB tables"
  type = map(object({
    billing_mode   = string
    read_capacity  = optional(number)
    write_capacity = optional(number)
    hash_key       = string
    range_key      = optional(string)

    attributes = optional(list(object({
      name = string
      type = string
    })))

    global_secondary_indexes = optional(list(object({
      name               = string
      hash_key           = string
      range_key          = optional(string)
      projection_type    = string
      read_capacity      = optional(number)
      write_capacity     = optional(number)
      non_key_attributes = optional(list(string))
    })))

    ttl = optional(object({
      enabled        = bool
      attribute_name = string
    }))
  }))
}

variable "s3_buckets" {
  description = "Configuration for S3 buckets"
  type = map(object({
    versioning = bool

    lifecycle_rules = optional(list(object({
      id      = string
      enabled = bool

      transition = optional(list(object({
        days          = number
        storage_class = string
      })))

      expiration = optional(object({
        days = number
      }))
    })))

    cors_rules = optional(list(object({
      allowed_headers = list(string)
      allowed_methods = list(string)
      allowed_origins = list(string)
      expose_headers  = list(string)
      max_age_seconds = optional(number)
    })))
  }))
}

variable "enable_websocket_api" {
  description = "Enable API Gateway WebSocket API"
  type        = bool
  default     = true
}

variable "websocket_routes" {
  description = "WebSocket route keys"
  type        = list(string)
  default     = ["$connect", "$disconnect", "$default", "context", "agent", "telemetry"]
}

variable "lambda_functions" {
  description = "Lambda function configurations"
  type = map(object({
    runtime = string
    handler = string
    memory  = number
    timeout = number

    environment_variables = map(string)
  }))
}

variable "agent_types" {
  description = "Types of MCP agents"
  type        = list(string)
  default     = ["supervisor", "content", "quiz", "terrain", "script", "review"]
}

variable "agent_visibility_timeouts" {
  description = "SQS visibility timeout for each agent type (in seconds)"
  type        = map(number)
  default = {
    supervisor = 60
    content    = 120
    quiz       = 90
    terrain    = 180
    script     = 90
    review     = 60
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}