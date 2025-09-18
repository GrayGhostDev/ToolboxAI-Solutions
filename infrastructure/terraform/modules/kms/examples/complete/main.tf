# Example: Complete KMS Setup for ToolBoxAI Solutions
# This example demonstrates a full KMS configuration with all features enabled

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ToolBoxAI"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Engineering"
    }
  }
}

# Use the existing KMS key from .env file if available
locals {
  existing_kms_key_id = "13eb8af0-804c-4115-b97f-e189235c634c"

  # EKS cluster configuration (assumes EKS module outputs)
  eks_node_role_arns = [
    "arn:aws:iam::389548781781:role/toolboxai-${var.environment}-eks-node-role"
  ]

  eks_service_account_arns = [
    "arn:aws:iam::389548781781:role/toolboxai-${var.environment}-backend-sa",
    "arn:aws:iam::389548781781:role/toolboxai-${var.environment}-dashboard-sa"
  ]

  lambda_function_arns = [
    "arn:aws:lambda:${var.aws_region}:389548781781:function:toolboxai-${var.environment}-content-generator",
    "arn:aws:lambda:${var.aws_region}:389548781781:function:toolboxai-${var.environment}-compliance-validator"
  ]

  sns_topics = [
    aws_sns_topic.alerts.arn
  ]
}

# Create SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "toolboxai-${var.environment}-kms-alerts"

  kms_master_key_id = module.kms.messaging_key.id
}

resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Deploy the KMS module
module "kms" {
  source = "../.."

  project_name = "toolboxai"
  environment  = var.environment
  aws_region   = var.aws_region

  # Key configuration
  deletion_window     = 30
  multi_region       = var.environment == "prod" ? true : false
  enable_key_rotation = true

  # Access configuration
  eks_node_role_arns       = local.eks_node_role_arns
  eks_service_account_arns = local.eks_service_account_arns
  lambda_function_arns     = local.lambda_function_arns

  # Monitoring
  enable_cloudwatch_monitoring = true
  kms_usage_threshold         = 10000
  sns_alert_topic_arns        = local.sns_topics

  # Compliance
  coppa_compliance = true
  ferpa_compliance = true
  gdpr_compliance  = true

  # Service-specific settings
  enable_s3_bucket_key            = true
  enable_rds_encryption           = true
  enable_ebs_encryption_by_default = true

  # Audit and logging
  enable_key_usage_logging = true
  log_retention_days       = 90

  # Tags
  common_tags = {
    ManagedBy   = "Terraform"
    Project     = "ToolBoxAI"
    Environment = var.environment
    CostCenter  = "Engineering"
    Compliance  = "COPPA,FERPA,GDPR"
    Repository  = "toolboxai-solutions"
  }
}

# Create an S3 bucket using the KMS key
resource "aws_s3_bucket" "encrypted_content" {
  bucket = "toolboxai-${var.environment}-encrypted-content"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encrypted_content" {
  bucket = aws_s3_bucket.encrypted_content.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = module.kms.s3_key.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Create a Secrets Manager secret using KMS encryption
resource "aws_secretsmanager_secret" "api_keys" {
  name_prefix = "toolboxai-${var.environment}-api-keys-"
  description = "API keys for external services"
  kms_key_id  = module.kms.primary_key.arn

  rotation_rules {
    automatically_after_days = 90
  }
}

# Create an RDS instance with KMS encryption
resource "aws_db_instance" "main" {
  identifier = "toolboxai-${var.environment}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  storage_encrypted     = true
  kms_key_id           = module.kms.database_key.arn
  storage_type         = "gp3"

  db_name  = "toolboxai"
  username = "admin"
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment != "prod" ? true : false

  tags = {
    Name        = "toolboxai-${var.environment}-database"
    Environment = var.environment
  }
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store database password in Secrets Manager
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    endpoint = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
  })
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name_prefix = "toolboxai-${var.environment}-db-credentials-"
  kms_key_id  = module.kms.database_key.arn
}

# Security group for RDS (example)
resource "aws_security_group" "rds" {
  name_prefix = "toolboxai-${var.environment}-rds-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "main" {
  name_prefix = "toolboxai-${var.environment}-"
  subnet_ids  = var.private_subnet_ids

  tags = {
    Name = "toolboxai-${var.environment}-db-subnet-group"
  }
}

# Enable EBS encryption by default for the region
resource "aws_ebs_encryption_by_default" "main" {
  enabled = true
}

resource "aws_ebs_default_kms_key" "main" {
  key_arn = module.kms.ebs_key.arn
}

# Outputs
output "kms_keys" {
  description = "All KMS key ARNs"
  value       = module.kms.all_key_arns
}

output "s3_bucket" {
  description = "Encrypted S3 bucket"
  value       = aws_s3_bucket.encrypted_content.id
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "secrets_arns" {
  description = "Secrets Manager secret ARNs"
  value = {
    api_keys       = aws_secretsmanager_secret.api_keys.arn
    db_credentials = aws_secretsmanager_secret.db_credentials.arn
  }
}

output "kms_config_summary" {
  description = "KMS configuration summary"
  value       = module.kms.kms_configuration
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = "ops@toolboxai.solutions"
}

variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for RDS"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Application security group ID"
  type        = string
}