# ToolBoxAI Solutions - Security Module Outputs

# KMS
output "kms_key_id" {
  description = "ID of the KMS key for general encryption"
  value       = try(aws_kms_key.general[0].id, null)
}

output "kms_key_arn" {
  description = "ARN of the KMS key for general encryption"
  value       = try(aws_kms_key.general[0].arn, null)
}

output "kms_alias_name" {
  description = "Name of the KMS alias"
  value       = try(aws_kms_alias.general[0].name, null)
}

output "kms_alias_arn" {
  description = "ARN of the KMS alias"
  value       = try(aws_kms_alias.general[0].arn, null)
}

# Security Groups
output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "alb_security_group_arn" {
  description = "ARN of the ALB security group"
  value       = aws_security_group.alb.arn
}

output "eks_control_plane_security_group_id" {
  description = "ID of the EKS control plane security group"
  value       = aws_security_group.eks_control_plane.id
}

output "eks_control_plane_security_group_arn" {
  description = "ARN of the EKS control plane security group"
  value       = aws_security_group.eks_control_plane.arn
}

output "eks_nodes_security_group_id" {
  description = "ID of the EKS nodes security group"
  value       = aws_security_group.eks_nodes.id
}

output "eks_nodes_security_group_arn" {
  description = "ARN of the EKS nodes security group"
  value       = aws_security_group.eks_nodes.arn
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

output "rds_security_group_arn" {
  description = "ARN of the RDS security group"
  value       = aws_security_group.rds.arn
}

output "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  value       = aws_security_group.lambda.id
}

output "lambda_security_group_arn" {
  description = "ARN of the Lambda security group"
  value       = aws_security_group.lambda.arn
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

output "redis_security_group_arn" {
  description = "ARN of the Redis security group"
  value       = aws_security_group.redis.arn
}

output "bastion_security_group_id" {
  description = "ID of the bastion security group"
  value       = try(aws_security_group.bastion[0].id, null)
}

output "bastion_security_group_arn" {
  description = "ARN of the bastion security group"
  value       = try(aws_security_group.bastion[0].arn, null)
}

# WAF
output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = try(aws_wafv2_web_acl.main[0].id, null)
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = try(aws_wafv2_web_acl.main[0].arn, null)
}

output "waf_web_acl_capacity" {
  description = "Web ACL capacity units (WCU) currently being used"
  value       = try(aws_wafv2_web_acl.main[0].capacity, null)
}

output "waf_log_group_name" {
  description = "Name of the WAF CloudWatch log group"
  value       = try(aws_cloudwatch_log_group.waf[0].name, null)
}

output "waf_log_group_arn" {
  description = "ARN of the WAF CloudWatch log group"
  value       = try(aws_cloudwatch_log_group.waf[0].arn, null)
}

# AWS Config
output "config_configuration_recorder_name" {
  description = "Name of the AWS Config configuration recorder"
  value       = try(aws_config_configuration_recorder.main[0].name, null)
}

output "config_delivery_channel_name" {
  description = "Name of the AWS Config delivery channel"
  value       = try(aws_config_delivery_channel.main[0].name, null)
}

output "config_bucket_id" {
  description = "ID of the AWS Config S3 bucket"
  value       = try(aws_s3_bucket.config[0].id, null)
}

output "config_bucket_arn" {
  description = "ARN of the AWS Config S3 bucket"
  value       = try(aws_s3_bucket.config[0].arn, null)
}

output "config_role_arn" {
  description = "ARN of the AWS Config IAM role"
  value       = try(aws_iam_role.config[0].arn, null)
}

# GuardDuty
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = try(aws_guardduty_detector.main[0].id, null)
}

output "guardduty_detector_arn" {
  description = "ARN of the GuardDuty detector"
  value       = try(aws_guardduty_detector.main[0].arn, null)
}

# Security Hub
output "security_hub_account_id" {
  description = "AWS account ID of Security Hub"
  value       = try(aws_securityhub_account.main[0].id, null)
}

# CloudTrail
output "cloudtrail_id" {
  description = "ID of the CloudTrail"
  value       = try(aws_cloudtrail.main[0].id, null)
}

output "cloudtrail_arn" {
  description = "ARN of the CloudTrail"
  value       = try(aws_cloudtrail.main[0].arn, null)
}

output "cloudtrail_bucket_id" {
  description = "ID of the CloudTrail S3 bucket"
  value       = try(aws_s3_bucket.cloudtrail[0].id, null)
}

output "cloudtrail_bucket_arn" {
  description = "ARN of the CloudTrail S3 bucket"
  value       = try(aws_s3_bucket.cloudtrail[0].arn, null)
}

# IAM Access Analyzer
output "iam_access_analyzer_arn" {
  description = "ARN of the IAM Access Analyzer"
  value       = try(aws_accessanalyzer_analyzer.main[0].arn, null)
}

# Inspector
output "inspector_assessment_target_arn" {
  description = "ARN of the Inspector assessment target"
  value       = try(aws_inspector_assessment_target.main[0].arn, null)
}

output "inspector_assessment_template_arn" {
  description = "ARN of the Inspector assessment template"
  value       = try(aws_inspector_assessment_template.main[0].arn, null)
}

# Backup Vault
output "backup_vault_id" {
  description = "ID of the backup vault"
  value       = try(aws_backup_vault.main[0].id, null)
}

output "backup_vault_arn" {
  description = "ARN of the backup vault"
  value       = try(aws_backup_vault.main[0].arn, null)
}

# Certificate Manager
output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = try(aws_acm_certificate.main[0].arn, null)
}

output "acm_certificate_domain_name" {
  description = "Domain name of the ACM certificate"
  value       = try(aws_acm_certificate.main[0].domain_name, null)
}

# SNS Topics for Notifications
output "security_notifications_topic_arn" {
  description = "ARN of the security notifications SNS topic"
  value       = try(aws_sns_topic.security_notifications[0].arn, null)
}

# Summary outputs for easy reference
output "security_summary" {
  description = "Summary of security configurations"
  value = {
    kms_encryption_enabled      = var.enable_kms_key
    waf_enabled                = var.enable_waf
    config_enabled             = var.enable_config
    guardduty_enabled          = var.enable_guardduty
    security_hub_enabled       = var.enable_security_hub
    cloudtrail_enabled         = var.enable_cloudtrail
    inspector_enabled          = var.enable_inspector
    shield_advanced_enabled    = var.enable_shield_advanced
    macie_enabled             = var.enable_macie
    detective_enabled         = var.enable_detective
    network_firewall_enabled  = var.enable_network_firewall
    access_analyzer_enabled   = var.enable_iam_access_analyzer
    backup_vault_enabled      = var.enable_backup_vault
    bastion_access_enabled    = var.enable_bastion_access
  }
}

output "compliance_summary" {
  description = "Summary of compliance configurations"
  value = {
    compliance_framework       = var.compliance_framework
    compliance_rules_enabled   = var.enable_compliance_rules
    password_policy_enforced   = true
    encryption_at_rest        = var.enable_kms_key
    encryption_in_transit     = true
    logging_enabled           = var.enable_cloudtrail && var.enable_waf_logging
    monitoring_enabled        = var.enable_config && var.enable_guardduty
    backup_enabled            = var.enable_backup_vault
  }
}

# All security group IDs for easy reference
output "all_security_group_ids" {
  description = "Map of all security group IDs"
  value = {
    alb                = aws_security_group.alb.id
    eks_control_plane  = aws_security_group.eks_control_plane.id
    eks_nodes         = aws_security_group.eks_nodes.id
    rds               = aws_security_group.rds.id
    lambda            = aws_security_group.lambda.id
    redis             = aws_security_group.redis.id
    bastion           = try(aws_security_group.bastion[0].id, null)
  }
}

# Cost optimization information
output "cost_optimization" {
  description = "Cost optimization features for security"
  value = {
    waf_rate_limit_set         = var.waf_rate_limit
    config_delivery_frequency  = var.config_delivery_frequency
    log_retention_optimized    = var.waf_log_retention_days <= 30
    shield_advanced_disabled   = !var.enable_shield_advanced
    detective_disabled         = !var.enable_detective
    macie_disabled            = !var.enable_macie
    inspector_disabled        = !var.enable_inspector
  }
}