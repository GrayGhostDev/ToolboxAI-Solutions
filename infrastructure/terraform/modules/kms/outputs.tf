# KMS Module Outputs

# Primary Key Outputs
output "primary_key" {
  description = "Primary KMS key details"
  value = {
    id       = aws_kms_key.primary.id
    arn      = aws_kms_key.primary.arn
    alias    = aws_kms_alias.primary.name
    key_id   = aws_kms_key.primary.key_id
  }
}

# Database Key Outputs
output "database_key" {
  description = "Database KMS key details"
  value = {
    id       = aws_kms_key.database.id
    arn      = aws_kms_key.database.arn
    alias    = aws_kms_alias.database.name
    key_id   = aws_kms_key.database.key_id
  }
}

# S3 Key Outputs
output "s3_key" {
  description = "S3 KMS key details"
  value = {
    id       = aws_kms_key.s3.id
    arn      = aws_kms_key.s3.arn
    alias    = aws_kms_alias.s3.name
    key_id   = aws_kms_key.s3.key_id
  }
}

# Lambda Key Outputs
output "lambda_key" {
  description = "Lambda KMS key details"
  value = {
    id       = aws_kms_key.lambda.id
    arn      = aws_kms_key.lambda.arn
    alias    = aws_kms_alias.lambda.name
    key_id   = aws_kms_key.lambda.key_id
  }
}

# EBS Key Outputs
output "ebs_key" {
  description = "EBS KMS key details"
  value = {
    id       = aws_kms_key.ebs.id
    arn      = aws_kms_key.ebs.arn
    alias    = aws_kms_alias.ebs.name
    key_id   = aws_kms_key.ebs.key_id
  }
}

# Messaging Key Outputs
output "messaging_key" {
  description = "Messaging (SNS/SQS) KMS key details"
  value = {
    id       = aws_kms_key.messaging.id
    arn      = aws_kms_key.messaging.arn
    alias    = aws_kms_alias.messaging.name
    key_id   = aws_kms_key.messaging.key_id
  }
}

# Consolidated outputs for easy reference
output "all_key_arns" {
  description = "Map of all KMS key ARNs by purpose"
  value = {
    primary   = aws_kms_key.primary.arn
    database  = aws_kms_key.database.arn
    s3        = aws_kms_key.s3.arn
    lambda    = aws_kms_key.lambda.arn
    ebs       = aws_kms_key.ebs.arn
    messaging = aws_kms_key.messaging.arn
  }
}

output "all_key_ids" {
  description = "Map of all KMS key IDs by purpose"
  value = {
    primary   = aws_kms_key.primary.id
    database  = aws_kms_key.database.id
    s3        = aws_kms_key.s3.id
    lambda    = aws_kms_key.lambda.id
    ebs       = aws_kms_key.ebs.id
    messaging = aws_kms_key.messaging.id
  }
}

output "all_key_aliases" {
  description = "Map of all KMS key aliases by purpose"
  value = {
    primary   = aws_kms_alias.primary.name
    database  = aws_kms_alias.database.name
    s3        = aws_kms_alias.s3.name
    lambda    = aws_kms_alias.lambda.name
    ebs       = aws_kms_alias.ebs.name
    messaging = aws_kms_alias.messaging.name
  }
}

# Grants information
output "eks_grants" {
  description = "EKS grants created for service accounts"
  value       = aws_kms_grant.eks_primary[*].grant_id
  sensitive   = true
}

output "lambda_grants" {
  description = "Lambda grants created for functions"
  value       = aws_kms_grant.lambda_env[*].grant_id
  sensitive   = true
}

# Monitoring outputs
output "cloudwatch_alarms" {
  description = "CloudWatch alarm names for KMS monitoring"
  value       = [for alarm in aws_cloudwatch_metric_alarm.kms_key_usage : alarm.alarm_name]
}

# Compliance tags
output "compliance_tags" {
  description = "Compliance tags applied to KMS keys"
  value = {
    coppa = var.coppa_compliance
    ferpa = var.ferpa_compliance
    gdpr  = var.gdpr_compliance
  }
}

# Configuration summary
output "kms_configuration" {
  description = "Summary of KMS configuration"
  value = {
    environment            = var.environment
    region                = var.aws_region
    multi_region          = var.multi_region
    deletion_window       = var.deletion_window
    key_rotation_enabled  = var.enable_key_rotation
    monitoring_enabled    = var.enable_cloudwatch_monitoring
    s3_bucket_key_enabled = var.enable_s3_bucket_key
    ebs_default_encryption = var.enable_ebs_encryption_by_default
  }
}

# Export for use in other modules
output "kms_module_config" {
  description = "Complete module configuration for reference"
  value = {
    keys = {
      primary   = aws_kms_key.primary
      database  = aws_kms_key.database
      s3        = aws_kms_key.s3
      lambda    = aws_kms_key.lambda
      ebs       = aws_kms_key.ebs
      messaging = aws_kms_key.messaging
    }
    aliases = {
      primary   = aws_kms_alias.primary
      database  = aws_kms_alias.database
      s3        = aws_kms_alias.s3
      lambda    = aws_kms_alias.lambda
      ebs       = aws_kms_alias.ebs
      messaging = aws_kms_alias.messaging
    }
    policies = {
      primary  = aws_kms_key_policy.primary_policy
      database = aws_kms_key_policy.database_policy
      s3       = aws_kms_key_policy.s3_policy
    }
  }
  sensitive = true
}