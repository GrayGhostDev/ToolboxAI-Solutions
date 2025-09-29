# ToolBoxAI Solutions - Terraform Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production"
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "toolboxai"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "engineering"
}

variable "owner_email" {
  description = "Owner email for notifications"
  type        = string
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
}

# Security Configuration
variable "allowed_ssh_ips" {
  description = "IP addresses allowed to SSH"
  type        = list(string)
  default     = []
}

# EKS Configuration
variable "eks_cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "eks_node_instance_types" {
  description = "Instance types for EKS nodes"
  type        = map(list(string))
  default = {
    general = ["t3.large", "t3a.large"]
    mcp     = ["r5.xlarge", "r5a.xlarge"]
    gpu     = ["g4dn.xlarge"]
  }
}

# RDS Configuration
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = map(string)
  default = {
    dev        = "db.t3.medium"
    staging    = "db.r6g.large"
    production = "db.r6g.xlarge"
  }
}

variable "rds_backup_retention" {
  description = "RDS backup retention in days"
  type        = map(number)
  default = {
    dev        = 7
    staging    = 14
    production = 30
  }
}

# MCP Configuration
variable "mcp_context_ttl_days" {
  description = "TTL for MCP contexts in days"
  type        = number
  default     = 30
}

variable "mcp_max_agents" {
  description = "Maximum number of MCP agents"
  type        = map(number)
  default = {
    dev        = 10
    staging    = 20
    production = 50
  }
}

# API Keys (sensitive)
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
}

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

# Monitoring Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = map(number)
  default = {
    dev        = 30
    staging    = 60
    production = 90
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = true
}

# Auto-scaling Configuration
variable "auto_scaling_config" {
  description = "Auto-scaling configuration"
  type = object({
    min_capacity     = number
    max_capacity     = number
    target_cpu       = number
    target_memory    = number
    scale_in_cooldown  = number
    scale_out_cooldown = number
  })
  default = {
    min_capacity     = 2
    max_capacity     = 10
    target_cpu       = 70
    target_memory    = 80
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Backup Configuration
variable "backup_config" {
  description = "Backup configuration"
  type = object({
    enable_automated_backups = bool
    backup_window           = string
    retention_period        = number
    copy_to_region         = string
  })
  default = {
    enable_automated_backups = true
    backup_window           = "03:00-04:00"
    retention_period        = 30
    copy_to_region         = "us-west-2"
  }
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "toolboxai.solutions"
}

variable "subdomain_prefixes" {
  description = "Subdomain prefixes for different services"
  type        = map(string)
  default = {
    api       = "api"
    app       = "app"
    dashboard = "dashboard"
    mcp       = "mcp"
    ws        = "ws"
  }
}

# Feature Flags
variable "feature_flags" {
  description = "Feature flags for enabling/disabling features"
  type        = map(bool)
  default = {
    enable_gpu_nodes         = true
    enable_spot_instances    = true
    enable_multi_region      = false
    enable_vpc_peering       = false
    enable_private_link      = true
    enable_waf              = true
    enable_shield           = false
    enable_guardduty        = true
    enable_security_hub     = true
    enable_config          = true
    enable_cloudtrail      = true
    enable_xray            = true
    enable_container_insights = true
  }
}

# Cost Optimization
variable "use_spot_instances" {
  description = "Use spot instances for non-critical workloads"
  type        = bool
  default     = true
}

variable "spot_max_price" {
  description = "Maximum price for spot instances"
  type        = string
  default     = "0.5"
}

variable "reserved_instance_config" {
  description = "Reserved instance configuration"
  type = object({
    enable          = bool
    payment_option  = string
    offering_class  = string
    instance_count  = number
  })
  default = {
    enable          = true
    payment_option  = "PARTIAL_UPFRONT"
    offering_class  = "STANDARD"
    instance_count  = 5
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}