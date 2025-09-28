# ToolBoxAI Solutions - Secrets Module Outputs

# Secrets Manager Secrets
output "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai.arn
}

output "openai_secret_name" {
  description = "Name of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai.name
}

output "anthropic_secret_arn" {
  description = "ARN of the Anthropic API key secret"
  value       = aws_secretsmanager_secret.anthropic.arn
}

output "anthropic_secret_name" {
  description = "Name of the Anthropic API key secret"
  value       = aws_secretsmanager_secret.anthropic.name
}

output "pusher_secret_arn" {
  description = "ARN of the Pusher configuration secret"
  value       = aws_secretsmanager_secret.pusher.arn
}

output "pusher_secret_name" {
  description = "Name of the Pusher configuration secret"
  value       = aws_secretsmanager_secret.pusher.name
}

output "database_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.database.arn
}

output "database_secret_name" {
  description = "Name of the database credentials secret"
  value       = aws_secretsmanager_secret.database.name
}

output "jwt_secret_arn" {
  description = "ARN of the JWT signing key secret"
  value       = aws_secretsmanager_secret.jwt.arn
}

output "jwt_secret_name" {
  description = "Name of the JWT signing key secret"
  value       = aws_secretsmanager_secret.jwt.name
}

output "encryption_secret_arn" {
  description = "ARN of the application encryption key secret"
  value       = aws_secretsmanager_secret.encryption.arn
}

output "encryption_secret_name" {
  description = "Name of the application encryption key secret"
  value       = aws_secretsmanager_secret.encryption.name
}

# Webhook Secrets
output "webhook_secrets" {
  description = "Map of webhook secret ARNs"
  value = {
    for name, secret in aws_secretsmanager_secret.webhooks : name => {
      arn  = secret.arn
      name = secret.name
    }
  }
}

# External Service Secrets
output "external_service_secrets" {
  description = "Map of external service secret ARNs"
  value = {
    for name, secret in aws_secretsmanager_secret.external_services : name => {
      arn  = secret.arn
      name = secret.name
    }
  }
}

# SSL/TLS Certificates
output "ssl_certificate_secrets" {
  description = "Map of SSL certificate secret ARNs"
  value = {
    for name, secret in aws_secretsmanager_secret.ssl_certificates : name => {
      arn  = secret.arn
      name = secret.name
    }
  }
}

# IAM Roles
output "secrets_access_role_arn" {
  description = "ARN of the IAM role for accessing secrets"
  value       = aws_iam_role.secrets_access.arn
}

output "secrets_access_role_name" {
  description = "Name of the IAM role for accessing secrets"
  value       = aws_iam_role.secrets_access.name
}

output "secrets_rotation_role_arn" {
  description = "ARN of the IAM role for secrets rotation"
  value       = try(aws_iam_role.secrets_rotation[0].arn, null)
}

output "secrets_rotation_role_name" {
  description = "Name of the IAM role for secrets rotation"
  value       = try(aws_iam_role.secrets_rotation[0].name, null)
}

# Lambda Functions for Rotation
output "rotation_lambda_functions" {
  description = "Map of rotation Lambda function ARNs"
  value = {
    for name, function in aws_lambda_function.rotation : name => {
      arn           = function.arn
      function_name = function.function_name
    }
  }
}

# KMS Keys
output "secrets_kms_key_id" {
  description = "ID of the KMS key used for secrets encryption"
  value       = try(aws_kms_key.secrets[0].id, null)
}

output "secrets_kms_key_arn" {
  description = "ARN of the KMS key used for secrets encryption"
  value       = try(aws_kms_key.secrets[0].arn, null)
}

output "secrets_kms_alias_name" {
  description = "Name of the KMS alias for secrets encryption"
  value       = try(aws_kms_alias.secrets[0].name, null)
}

# VPC Endpoint
output "secrets_manager_vpc_endpoint_id" {
  description = "ID of the Secrets Manager VPC endpoint"
  value       = try(aws_vpc_endpoint.secretsmanager[0].id, null)
}

output "secrets_manager_vpc_endpoint_dns_entry" {
  description = "DNS entries for the Secrets Manager VPC endpoint"
  value       = try(aws_vpc_endpoint.secretsmanager[0].dns_entry, null)
}

# All Secret ARNs
output "all_secret_arns" {
  description = "List of all secret ARNs"
  value = compact([
    aws_secretsmanager_secret.openai.arn,
    aws_secretsmanager_secret.anthropic.arn,
    aws_secretsmanager_secret.pusher.arn,
    aws_secretsmanager_secret.database.arn,
    aws_secretsmanager_secret.jwt.arn,
    aws_secretsmanager_secret.encryption.arn,
    [for secret in aws_secretsmanager_secret.webhooks : secret.arn]...,
    [for secret in aws_secretsmanager_secret.external_services : secret.arn]...,
    [for secret in aws_secretsmanager_secret.ssl_certificates : secret.arn]...
  ])
}

# All Secret Names
output "all_secret_names" {
  description = "List of all secret names"
  value = compact([
    aws_secretsmanager_secret.openai.name,
    aws_secretsmanager_secret.anthropic.name,
    aws_secretsmanager_secret.pusher.name,
    aws_secretsmanager_secret.database.name,
    aws_secretsmanager_secret.jwt.name,
    aws_secretsmanager_secret.encryption.name,
    [for secret in aws_secretsmanager_secret.webhooks : secret.name]...,
    [for secret in aws_secretsmanager_secret.external_services : secret.name]...,
    [for secret in aws_secretsmanager_secret.ssl_certificates : secret.name]...
  ])
}

# Secrets Summary
output "secrets_summary" {
  description = "Summary of secrets configuration"
  value = {
    environment = var.environment
    total_secrets = length(compact([
      aws_secretsmanager_secret.openai.arn,
      aws_secretsmanager_secret.anthropic.arn,
      aws_secretsmanager_secret.pusher.arn,
      aws_secretsmanager_secret.database.arn,
      aws_secretsmanager_secret.jwt.arn,
      aws_secretsmanager_secret.encryption.arn,
      [for secret in aws_secretsmanager_secret.webhooks : secret.arn]...,
      [for secret in aws_secretsmanager_secret.external_services : secret.arn]...,
      [for secret in aws_secretsmanager_secret.ssl_certificates : secret.arn]...
    ]))
    rotation_enabled = var.enable_automatic_rotation
    kms_encryption_enabled = var.create_kms_key
    vpc_endpoint_enabled = var.create_vpc_endpoint
    cross_region_replication = length(var.replica_regions) > 0
    webhook_secrets_count = length(var.webhook_secrets)
    external_service_secrets_count = length(var.external_service_secrets)
    ssl_certificate_secrets_count = length(var.ssl_certificate_secrets)
  }
}

# Security Configuration
output "security_configuration" {
  description = "Security configuration for secrets"
  value = {
    kms_encryption = var.create_kms_key
    automatic_rotation = var.enable_automatic_rotation
    rotation_interval_days = var.rotation_interval_days
    cross_region_backup = length(var.replica_regions) > 0
    vpc_endpoint_private_dns = var.create_vpc_endpoint
    iam_role_least_privilege = true
    secret_recovery_window = var.recovery_window_in_days
  }
}

# Cost Optimization
output "cost_optimization" {
  description = "Cost optimization information for secrets"
  value = {
    estimated_monthly_cost = {
      secrets_storage = "$0.40 per secret per month"
      api_requests = "$0.05 per 10,000 requests"
      kms_key = var.create_kms_key ? "$1.00 per month" : "Using AWS managed key"
      rotation_lambda = var.enable_automatic_rotation ? "Based on Lambda execution time" : "Disabled"
      vpc_endpoint = var.create_vpc_endpoint ? "Based on data processing" : "Disabled"
    }
    total_secrets = length(compact([
      aws_secretsmanager_secret.openai.arn,
      aws_secretsmanager_secret.anthropic.arn,
      aws_secretsmanager_secret.pusher.arn,
      aws_secretsmanager_secret.database.arn,
      aws_secretsmanager_secret.jwt.arn,
      aws_secretsmanager_secret.encryption.arn,
      [for secret in aws_secretsmanager_secret.webhooks : secret.arn]...,
      [for secret in aws_secretsmanager_secret.external_services : secret.arn]...,
      [for secret in aws_secretsmanager_secret.ssl_certificates : secret.arn]...
    ]))
    rotation_optimized = var.rotation_interval_days >= 30
  }
}

# Quick Access Information
output "quick_access" {
  description = "Quick access information for secrets management"
  value = {
    secrets_manager_console = "https://console.aws.amazon.com/secretsmanager/home?region=${data.aws_region.current.name}"
    kms_console = var.create_kms_key ? "https://console.aws.amazon.com/kms/home?region=${data.aws_region.current.name}" : null
    iam_console = "https://console.aws.amazon.com/iam/home"
    lambda_console = var.enable_automatic_rotation ? "https://console.aws.amazon.com/lambda/home?region=${data.aws_region.current.name}" : null
  }
}

# Environment-Specific Configuration
output "environment_config" {
  description = "Environment-specific configuration"
  value = {
    environment = var.environment
    secret_name_prefix = "${var.environment}/toolboxai"
    rotation_enabled_for_env = var.environment == "production" ? true : var.enable_automatic_rotation
    cross_region_replication = var.environment == "production" ? length(var.replica_regions) > 0 : false
    kms_key_rotation = var.environment == "production" ? true : false
  }
}