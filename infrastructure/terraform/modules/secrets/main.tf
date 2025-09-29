# AWS Secrets Manager Module for ToolBoxAI Solutions
# This module manages all application secrets with KMS encryption

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# KMS key for encrypting secrets
resource "aws_kms_key" "secrets" {
  description             = "KMS key for encrypting ToolBoxAI secrets"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-secrets-kms"
      Purpose = "Secrets encryption"
    }
  )
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.project_name}-${var.environment}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# API Keys Secret
resource "aws_secretsmanager_secret" "api_keys" {
  name_prefix = "${var.project_name}-${var.environment}-api-keys-"
  description = "API keys for external services"
  kms_key_id  = aws_kms_key.secrets.arn

  rotation_rules {
    automatically_after_days = 90
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-api-keys"
      Type = "api-keys"
    }
  )
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    anthropic_api_key = var.anthropic_api_key
    openai_api_key    = var.openai_api_key
    langchain_api_key = var.langchain_api_key
    langsmith_api_key = var.langsmith_api_key
  })
}

# Stripe Secrets
resource "aws_secretsmanager_secret" "stripe" {
  name_prefix = "${var.project_name}-${var.environment}-stripe-"
  description = "Stripe payment processing credentials"
  kms_key_id  = aws_kms_key.secrets.arn

  rotation_rules {
    automatically_after_days = 180
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-stripe"
      Type = "payment"
    }
  )
}

resource "aws_secretsmanager_secret_version" "stripe" {
  secret_id = aws_secretsmanager_secret.stripe.id
  secret_string = jsonencode({
    stripe_public_key    = var.stripe_public_key
    stripe_secret_key    = var.stripe_secret_key
    stripe_webhook_secret = var.stripe_webhook_secret
  })
}

# Database Credentials
resource "aws_secretsmanager_secret" "database" {
  name_prefix = "${var.project_name}-${var.environment}-database-"
  description = "PostgreSQL database credentials"
  kms_key_id  = aws_kms_key.secrets.arn

  rotation_rules {
    automatically_after_days = 30
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-database"
      Type = "database"
    }
  )
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    host     = var.database_host
    port     = var.database_port
    database = var.database_name
    username = var.database_username
    password = var.database_password
  })
}

# JWT Secret
resource "aws_secretsmanager_secret" "jwt" {
  name_prefix = "${var.project_name}-${var.environment}-jwt-"
  description = "JWT signing secret"
  kms_key_id  = aws_kms_key.secrets.arn

  rotation_rules {
    automatically_after_days = 60
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-jwt"
      Type = "authentication"
    }
  )
}

resource "aws_secretsmanager_secret_version" "jwt" {
  secret_id = aws_secretsmanager_secret.jwt.id
  secret_string = jsonencode({
    jwt_secret_key = var.jwt_secret_key
    jwt_algorithm  = "HS256"
    jwt_expiration_minutes = 1440
  })
}

# Pusher Credentials
resource "aws_secretsmanager_secret" "pusher" {
  name_prefix = "${var.project_name}-${var.environment}-pusher-"
  description = "Pusher realtime messaging credentials"
  kms_key_id  = aws_kms_key.secrets.arn

  rotation_rules {
    automatically_after_days = 180
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-pusher"
      Type = "messaging"
    }
  )
}

resource "aws_secretsmanager_secret_version" "pusher" {
  secret_id = aws_secretsmanager_secret.pusher.id
  secret_string = jsonencode({
    app_id    = var.pusher_app_id
    key       = var.pusher_key
    secret    = var.pusher_secret
    cluster   = var.pusher_cluster
  })
}

# Roblox API Credentials
resource "aws_secretsmanager_secret" "roblox" {
  name_prefix = "${var.project_name}-${var.environment}-roblox-"
  description = "Roblox integration credentials"
  kms_key_id  = aws_kms_key.secrets.arn

  rotation_rules {
    automatically_after_days = 90
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-roblox"
      Type = "integration"
    }
  )
}

resource "aws_secretsmanager_secret_version" "roblox" {
  secret_id = aws_secretsmanager_secret.roblox.id
  secret_string = jsonencode({
    api_key       = var.roblox_api_key
    client_id     = var.roblox_client_id
    client_secret = var.roblox_client_secret
  })
}

# IAM Role for accessing secrets from EKS
resource "aws_iam_role" "secrets_access" {
  name = "${var.project_name}-${var.environment}-secrets-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = var.eks_oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${replace(var.eks_oidc_provider_url, "https://", "")}:sub" = "system:serviceaccount:${var.namespace}:${var.service_account_name}"
            "${replace(var.eks_oidc_provider_url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

# IAM Policy for accessing secrets
resource "aws_iam_policy" "secrets_access" {
  name        = "${var.project_name}-${var.environment}-secrets-access"
  description = "Policy for accessing secrets from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.api_keys.arn,
          aws_secretsmanager_secret.stripe.arn,
          aws_secretsmanager_secret.database.arn,
          aws_secretsmanager_secret.jwt.arn,
          aws_secretsmanager_secret.pusher.arn,
          aws_secretsmanager_secret.roblox.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.secrets.arn
        ]
      }
    ]
  })

  tags = var.common_tags
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "secrets_access" {
  policy_arn = aws_iam_policy.secrets_access.arn
  role       = aws_iam_role.secrets_access.name
}

# Outputs
output "kms_key_id" {
  description = "KMS key ID for secrets encryption"
  value       = aws_kms_key.secrets.id
}

output "kms_key_arn" {
  description = "KMS key ARN for secrets encryption"
  value       = aws_kms_key.secrets.arn
}

output "secrets_role_arn" {
  description = "IAM role ARN for accessing secrets"
  value       = aws_iam_role.secrets_access.arn
}

output "secret_arns" {
  description = "ARNs of all secrets"
  value = {
    api_keys = aws_secretsmanager_secret.api_keys.arn
    stripe   = aws_secretsmanager_secret.stripe.arn
    database = aws_secretsmanager_secret.database.arn
    jwt      = aws_secretsmanager_secret.jwt.arn
    pusher   = aws_secretsmanager_secret.pusher.arn
    roblox   = aws_secretsmanager_secret.roblox.arn
  }
}

output "secret_names" {
  description = "Names of all secrets"
  value = {
    api_keys = aws_secretsmanager_secret.api_keys.name
    stripe   = aws_secretsmanager_secret.stripe.name
    database = aws_secretsmanager_secret.database.name
    jwt      = aws_secretsmanager_secret.jwt.name
    pusher   = aws_secretsmanager_secret.pusher.name
    roblox   = aws_secretsmanager_secret.roblox.name
  }
}