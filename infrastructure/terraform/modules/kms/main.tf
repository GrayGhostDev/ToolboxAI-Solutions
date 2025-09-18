# AWS KMS Module for ToolBoxAI Solutions
# Provides encryption keys for data protection and compliance

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary KMS key for general encryption
resource "aws_kms_key" "primary" {
  description             = "${var.project_name}-${var.environment}-primary-key"
  deletion_window_in_days = var.deletion_window
  enable_key_rotation     = true
  multi_region           = var.multi_region

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-${var.environment}-primary-kms"
      Purpose     = "Primary encryption key"
      Environment = var.environment
      Compliance  = "COPPA,FERPA,GDPR"
    }
  )
}

resource "aws_kms_alias" "primary" {
  name          = "alias/${var.project_name}-${var.environment}-primary"
  target_key_id = aws_kms_key.primary.key_id
}

# KMS key for database encryption
resource "aws_kms_key" "database" {
  description             = "${var.project_name}-${var.environment}-database-key"
  deletion_window_in_days = var.deletion_window
  enable_key_rotation     = true
  multi_region           = var.multi_region

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-${var.environment}-database-kms"
      Purpose     = "Database encryption"
      Environment = var.environment
      Compliance  = "FERPA,GDPR"
    }
  )
}

resource "aws_kms_alias" "database" {
  name          = "alias/${var.project_name}-${var.environment}-database"
  target_key_id = aws_kms_key.database.key_id
}

# KMS key for S3 bucket encryption
resource "aws_kms_key" "s3" {
  description             = "${var.project_name}-${var.environment}-s3-key"
  deletion_window_in_days = var.deletion_window
  enable_key_rotation     = true
  multi_region           = var.multi_region

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-${var.environment}-s3-kms"
      Purpose     = "S3 bucket encryption"
      Environment = var.environment
      Compliance  = "COPPA,FERPA,GDPR"
    }
  )
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${var.project_name}-${var.environment}-s3"
  target_key_id = aws_kms_key.s3.key_id
}

# KMS key for Lambda environment variables
resource "aws_kms_key" "lambda" {
  description             = "${var.project_name}-${var.environment}-lambda-key"
  deletion_window_in_days = var.deletion_window
  enable_key_rotation     = true
  multi_region           = false

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-${var.environment}-lambda-kms"
      Purpose     = "Lambda environment encryption"
      Environment = var.environment
    }
  )
}

resource "aws_kms_alias" "lambda" {
  name          = "alias/${var.project_name}-${var.environment}-lambda"
  target_key_id = aws_kms_key.lambda.key_id
}

# KMS key for EBS volume encryption
resource "aws_kms_key" "ebs" {
  description             = "${var.project_name}-${var.environment}-ebs-key"
  deletion_window_in_days = var.deletion_window
  enable_key_rotation     = true
  multi_region           = false

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-${var.environment}-ebs-kms"
      Purpose     = "EBS volume encryption"
      Environment = var.environment
    }
  )
}

resource "aws_kms_alias" "ebs" {
  name          = "alias/${var.project_name}-${var.environment}-ebs"
  target_key_id = aws_kms_key.ebs.key_id
}

# KMS key for SNS/SQS encryption
resource "aws_kms_key" "messaging" {
  description             = "${var.project_name}-${var.environment}-messaging-key"
  deletion_window_in_days = var.deletion_window
  enable_key_rotation     = true
  multi_region           = false

  tags = merge(
    var.common_tags,
    {
      Name        = "${var.project_name}-${var.environment}-messaging-kms"
      Purpose     = "SNS/SQS encryption"
      Environment = var.environment
    }
  )
}

resource "aws_kms_alias" "messaging" {
  name          = "alias/${var.project_name}-${var.environment}-messaging"
  target_key_id = aws_kms_key.messaging.key_id
}

# Key policies for cross-service access
resource "aws_kms_key_policy" "primary_policy" {
  key_id = aws_kms_key.primary.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow use by EKS nodes"
        Effect = "Allow"
        Principal = {
          AWS = var.eks_node_role_arns
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:CreateGrant"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:*"
          }
        }
      }
    ]
  })
}

resource "aws_kms_key_policy" "database_policy" {
  key_id = aws_kms_key.database.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow RDS to use the key"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_key_policy" "s3_policy" {
  key_id = aws_kms_key.s3.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow S3 to use the key"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:CreateGrant"
        ]
        Resource = "*"
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Grants for specific services
resource "aws_kms_grant" "eks_primary" {
  count             = length(var.eks_service_account_arns)
  key_id            = aws_kms_key.primary.key_id
  grantee_principal = var.eks_service_account_arns[count.index]
  operations        = ["Encrypt", "Decrypt", "GenerateDataKey"]
  name              = "${var.project_name}-eks-grant-${count.index}"
}

resource "aws_kms_grant" "lambda_env" {
  count             = length(var.lambda_function_arns)
  key_id            = aws_kms_key.lambda.key_id
  grantee_principal = var.lambda_function_arns[count.index]
  operations        = ["Decrypt"]
  name              = "${var.project_name}-lambda-grant-${count.index}"
}

# CloudWatch metrics for key usage monitoring
resource "aws_cloudwatch_metric_alarm" "kms_key_usage" {
  for_each = {
    primary  = aws_kms_key.primary.id
    database = aws_kms_key.database.id
    s3       = aws_kms_key.s3.id
  }

  alarm_name          = "${var.project_name}-${var.environment}-kms-${each.key}-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "NumberOfOperations"
  namespace           = "AWS/KMS"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.kms_usage_threshold
  alarm_description   = "Alert when KMS key usage is high"
  alarm_actions       = var.sns_alert_topic_arns

  dimensions = {
    KeyId = each.value
  }
}

# Outputs for use by other modules
output "primary_key_id" {
  value       = aws_kms_key.primary.id
  description = "Primary KMS key ID"
}

output "primary_key_arn" {
  value       = aws_kms_key.primary.arn
  description = "Primary KMS key ARN"
}

output "database_key_id" {
  value       = aws_kms_key.database.id
  description = "Database KMS key ID"
}

output "database_key_arn" {
  value       = aws_kms_key.database.arn
  description = "Database KMS key ARN"
}

output "s3_key_id" {
  value       = aws_kms_key.s3.id
  description = "S3 KMS key ID"
}

output "s3_key_arn" {
  value       = aws_kms_key.s3.arn
  description = "S3 KMS key ARN"
}

output "lambda_key_id" {
  value       = aws_kms_key.lambda.id
  description = "Lambda KMS key ID"
}

output "lambda_key_arn" {
  value       = aws_kms_key.lambda.arn
  description = "Lambda KMS key ARN"
}

output "ebs_key_id" {
  value       = aws_kms_key.ebs.id
  description = "EBS KMS key ID"
}

output "ebs_key_arn" {
  value       = aws_kms_key.ebs.arn
  description = "EBS KMS key ARN"
}

output "messaging_key_id" {
  value       = aws_kms_key.messaging.id
  description = "Messaging KMS key ID"
}

output "messaging_key_arn" {
  value       = aws_kms_key.messaging.arn
  description = "Messaging KMS key ARN"
}

output "key_aliases" {
  value = {
    primary   = aws_kms_alias.primary.name
    database  = aws_kms_alias.database.name
    s3        = aws_kms_alias.s3.name
    lambda    = aws_kms_alias.lambda.name
    ebs       = aws_kms_alias.ebs.name
    messaging = aws_kms_alias.messaging.name
  }
  description = "Map of KMS key aliases"
}