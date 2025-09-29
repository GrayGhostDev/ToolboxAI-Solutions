# RDS Module Variables

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

# Network Configuration
variable "vpc_id" {
  description = "VPC ID where the database will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "allowed_security_groups" {
  description = "Map of security group IDs allowed to connect to the database"
  type        = map(string)
  default     = {}
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to connect to the database"
  type        = list(string)
  default     = []
}

variable "availability_zone" {
  description = "Availability zone for single-AZ deployments"
  type        = string
  default     = null
}

# Engine Configuration
variable "engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "Engine version to use"
  type        = string
  default     = "15.4"
}

variable "major_engine_version" {
  description = "Major engine version for option group"
  type        = string
  default     = "15"
}

variable "parameter_group_family" {
  description = "DB parameter group family"
  type        = string
  default     = "postgres15"
}

# Instance Configuration
variable "instance_class" {
  description = "Instance type of the RDS instance"
  type        = string
  default     = "db.t3.medium"
}

variable "allocated_storage" {
  description = "Allocated storage in gigabytes"
  type        = number
  default     = 100
}

variable "max_allocated_storage" {
  description = "Maximum storage for autoscaling"
  type        = number
  default     = 1000
}

variable "storage_type" {
  description = "Storage type (gp2, gp3, io1)"
  type        = string
  default     = "gp3"
  validation {
    condition     = contains(["gp2", "gp3", "io1"], var.storage_type)
    error_message = "Storage type must be gp2, gp3, or io1."
  }
}

variable "storage_throughput" {
  description = "Storage throughput in MiBps (only for gp3)"
  type        = number
  default     = 125
}

variable "iops" {
  description = "The amount of provisioned IOPS (only for gp3 and io1)"
  type        = number
  default     = 3000
}

# Database Configuration
variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "toolboxai"
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "port" {
  description = "Port on which the database accepts connections"
  type        = number
  default     = 5432
}

variable "max_connections" {
  description = "Maximum number of database connections"
  type        = string
  default     = "200"
}

# Encryption
variable "kms_key_arn" {
  description = "ARN of KMS key for encryption"
  type        = string
}

# High Availability
variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "create_read_replica" {
  description = "Create a read replica"
  type        = bool
  default     = false
}

variable "read_replica_instance_class" {
  description = "Instance class for read replica (defaults to primary instance class)"
  type        = string
  default     = ""
}

# Backup Configuration
variable "backup_retention_period" {
  description = "Days to retain backups"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "auto_minor_version_upgrade" {
  description = "Enable automatic minor version upgrades"
  type        = bool
  default     = true
}

# Backup Replication
variable "enable_backup_replication" {
  description = "Enable automated backup replication to another region"
  type        = bool
  default     = false
}

variable "backup_replication_kms_key_arn" {
  description = "KMS key ARN for backup replication encryption"
  type        = string
  default     = ""
}

variable "backup_replication_retention_period" {
  description = "Retention period for replicated backups"
  type        = number
  default     = 7
}

# Monitoring
variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring"
  type        = bool
  default     = true
}

variable "monitoring_interval" {
  description = "Monitoring interval in seconds (0, 1, 5, 10, 15, 30, 60)"
  type        = number
  default     = 60
  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.monitoring_interval)
    error_message = "Monitoring interval must be 0, 1, 5, 10, 15, 30, or 60."
  }
}

variable "performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
  validation {
    condition     = contains([7, 31, 62, 93, 124, 155, 186, 217, 248, 279, 310, 341, 372, 403, 434, 465, 496, 527, 558, 589, 620, 651, 682, 713, 731], var.performance_insights_retention_period)
    error_message = "Performance Insights retention must be 7 days or a multiple of 31 days up to 731."
  }
}

variable "enabled_cloudwatch_logs_exports" {
  description = "List of log types to export to CloudWatch"
  type        = list(string)
  default     = ["postgresql"]
}

# CloudWatch Alarms
variable "sns_topic_arns" {
  description = "SNS topic ARNs for CloudWatch alarms"
  type        = list(string)
  default     = []
}

variable "cpu_utilization_threshold" {
  description = "CPU utilization threshold for alarms (%)"
  type        = number
  default     = 80
}

variable "free_storage_space_threshold" {
  description = "Free storage space threshold for alarms (bytes)"
  type        = number
  default     = 10737418240 # 10 GB
}

variable "database_connections_threshold" {
  description = "Database connections threshold for alarms"
  type        = number
  default     = 150
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