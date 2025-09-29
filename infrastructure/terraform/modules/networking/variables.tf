# ToolBoxAI Solutions - Networking Module Variables

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  validation {
    condition     = can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/[0-9]{1,2}$", var.vpc_cidr))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones must be provided for high availability."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  validation {
    condition     = length(var.public_subnet_cidrs) >= 2
    error_message = "At least 2 public subnets must be provided for high availability."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  validation {
    condition     = length(var.private_subnet_cidrs) >= 2
    error_message = "At least 2 private subnets must be provided for high availability."
  }
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
  validation {
    condition     = length(var.database_subnet_cidrs) >= 2
    error_message = "At least 2 database subnets must be provided for RDS high availability."
  }
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all private subnets (cost optimization)"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_log_retention_days" {
  description = "CloudWatch log retention for VPC Flow Logs"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.flow_log_retention_days)
    error_message = "Log retention must be a valid CloudWatch log retention value."
  }
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services"
  type        = bool
  default     = true
}

variable "enable_custom_dhcp" {
  description = "Enable custom DHCP options set"
  type        = bool
  default     = false
}

variable "enable_network_acls" {
  description = "Enable custom Network ACLs for additional security"
  type        = bool
  default     = false
}

variable "tags" {
  description = "A map of tags to assign to the resources"
  type        = map(string)
  default     = {}
}

# Cost optimization variables
variable "nat_instance_type" {
  description = "Instance type for NAT instances (alternative to NAT Gateway for cost savings)"
  type        = string
  default     = "t3.nano"
}

variable "use_nat_instance" {
  description = "Use NAT instances instead of NAT Gateway for cost optimization"
  type        = bool
  default     = false
}

# Multi-AZ configuration
variable "max_azs" {
  description = "Maximum number of AZs to use"
  type        = number
  default     = 3
  validation {
    condition     = var.max_azs >= 2 && var.max_azs <= 6
    error_message = "max_azs must be between 2 and 6."
  }
}

# IPv6 support
variable "enable_ipv6" {
  description = "Enable IPv6 support"
  type        = bool
  default     = false
}

variable "assign_ipv6_address_on_creation" {
  description = "Assign IPv6 address on subnet creation"
  type        = bool
  default     = false
}

# DNS configuration
variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in the VPC"
  type        = bool
  default     = true
}

# Security configuration
variable "enable_flow_log_s3" {
  description = "Store VPC Flow Logs in S3 instead of CloudWatch"
  type        = bool
  default     = false
}

variable "flow_log_s3_bucket" {
  description = "S3 bucket for VPC Flow Logs (if enable_flow_log_s3 is true)"
  type        = string
  default     = ""
}

variable "flow_log_format" {
  description = "Custom format for VPC Flow Logs"
  type        = string
  default     = null
}

# Advanced networking
variable "enable_classiclink" {
  description = "Enable ClassicLink for the VPC"
  type        = bool
  default     = false
}

variable "enable_classiclink_dns_support" {
  description = "Enable ClassicLink DNS Support for the VPC"
  type        = bool
  default     = false
}

# Transit Gateway
variable "enable_transit_gateway" {
  description = "Enable Transit Gateway attachment"
  type        = bool
  default     = false
}

variable "transit_gateway_id" {
  description = "Transit Gateway ID for attachment"
  type        = string
  default     = ""
}

# Peering connections
variable "enable_peering" {
  description = "Enable VPC peering connections"
  type        = bool
  default     = false
}

variable "peer_vpc_ids" {
  description = "List of VPC IDs to peer with"
  type        = list(string)
  default     = []
}

variable "peer_vpc_cidrs" {
  description = "List of CIDR blocks for peered VPCs"
  type        = list(string)
  default     = []
}

# Route53 private hosted zone
variable "enable_private_hosted_zone" {
  description = "Create a private hosted zone for the VPC"
  type        = bool
  default     = false
}

variable "private_domain_name" {
  description = "Domain name for the private hosted zone"
  type        = string
  default     = "toolboxai.local"
}

# Security groups default settings
variable "default_security_group_ingress" {
  description = "List of maps of ingress rules to set on the default security group"
  type        = list(map(string))
  default     = []
}

variable "default_security_group_egress" {
  description = "List of maps of egress rules to set on the default security group"
  type        = list(map(string))
  default = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = "0.0.0.0/0"
    }
  ]
}

variable "manage_default_security_group" {
  description = "Should be true to adopt and manage the default security group"
  type        = bool
  default     = true
}