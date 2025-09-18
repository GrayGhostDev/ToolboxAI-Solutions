# Variables for AWS Secrets Manager Module

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "toolboxai"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production"
  }
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "ToolBoxAI"
    ManagedBy   = "Terraform"
    Environment = "production"
  }
}

# EKS Configuration
variable "eks_oidc_provider_arn" {
  description = "ARN of the EKS OIDC provider"
  type        = string
}

variable "eks_oidc_provider_url" {
  description = "URL of the EKS OIDC provider"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "toolboxai"
}

variable "service_account_name" {
  description = "Kubernetes service account name"
  type        = string
  default     = "toolboxai-backend"
}

# API Keys
variable "anthropic_api_key" {
  description = "Anthropic Claude API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "langchain_api_key" {
  description = "LangChain API key"
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API key"
  type        = string
  sensitive   = true
}

# Stripe Configuration
variable "stripe_public_key" {
  description = "Stripe public key"
  type        = string
  sensitive   = true
}

variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  sensitive   = true
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook secret"
  type        = string
  sensitive   = true
}

# Database Configuration
variable "database_host" {
  description = "Database host"
  type        = string
  default     = "localhost"
}

variable "database_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "educational_platform_dev"
}

variable "database_username" {
  description = "Database username"
  type        = string
  sensitive   = true
  default     = "eduplatform"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# JWT Configuration
variable "jwt_secret_key" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

# Pusher Configuration
variable "pusher_app_id" {
  description = "Pusher app ID"
  type        = string
  sensitive   = true
}

variable "pusher_key" {
  description = "Pusher key"
  type        = string
  sensitive   = true
}

variable "pusher_secret" {
  description = "Pusher secret"
  type        = string
  sensitive   = true
}

variable "pusher_cluster" {
  description = "Pusher cluster"
  type        = string
  default     = "us2"
}

# Roblox Configuration
variable "roblox_api_key" {
  description = "Roblox API key"
  type        = string
  sensitive   = true
}

variable "roblox_client_id" {
  description = "Roblox client ID"
  type        = string
  sensitive   = true
}

variable "roblox_client_secret" {
  description = "Roblox client secret"
  type        = string
  sensitive   = true
}