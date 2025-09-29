# S3 Module Outputs

# Individual Bucket Outputs
output "content_bucket" {
  description = "Content bucket details"
  value = {
    id                   = aws_s3_bucket.content.id
    arn                  = aws_s3_bucket.content.arn
    domain_name          = aws_s3_bucket.content.bucket_domain_name
    regional_domain_name = aws_s3_bucket.content.bucket_regional_domain_name
    hosted_zone_id       = aws_s3_bucket.content.hosted_zone_id
    region               = aws_s3_bucket.content.region
  }
}

output "user_uploads_bucket" {
  description = "User uploads bucket details"
  value = {
    id                   = aws_s3_bucket.user_uploads.id
    arn                  = aws_s3_bucket.user_uploads.arn
    domain_name          = aws_s3_bucket.user_uploads.bucket_domain_name
    regional_domain_name = aws_s3_bucket.user_uploads.bucket_regional_domain_name
    hosted_zone_id       = aws_s3_bucket.user_uploads.hosted_zone_id
    region               = aws_s3_bucket.user_uploads.region
  }
}

output "backups_bucket" {
  description = "Backups bucket details"
  value = {
    id                   = aws_s3_bucket.backups.id
    arn                  = aws_s3_bucket.backups.arn
    domain_name          = aws_s3_bucket.backups.bucket_domain_name
    regional_domain_name = aws_s3_bucket.backups.bucket_regional_domain_name
    hosted_zone_id       = aws_s3_bucket.backups.hosted_zone_id
    region               = aws_s3_bucket.backups.region
  }
}

output "static_assets_bucket" {
  description = "Static assets bucket details"
  value = {
    id                   = aws_s3_bucket.static_assets.id
    arn                  = aws_s3_bucket.static_assets.arn
    domain_name          = aws_s3_bucket.static_assets.bucket_domain_name
    regional_domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    hosted_zone_id       = aws_s3_bucket.static_assets.hosted_zone_id
    region               = aws_s3_bucket.static_assets.region
  }
}

output "cdn_logs_bucket" {
  description = "CDN logs bucket details"
  value = {
    id                   = aws_s3_bucket.cdn_logs.id
    arn                  = aws_s3_bucket.cdn_logs.arn
    domain_name          = aws_s3_bucket.cdn_logs.bucket_domain_name
    regional_domain_name = aws_s3_bucket.cdn_logs.bucket_regional_domain_name
    hosted_zone_id       = aws_s3_bucket.cdn_logs.hosted_zone_id
    region               = aws_s3_bucket.cdn_logs.region
  }
}

output "audit_logs_bucket" {
  description = "Audit logs bucket details (if enabled)"
  value = var.enable_audit_logging ? {
    id                   = aws_s3_bucket.audit_logs[0].id
    arn                  = aws_s3_bucket.audit_logs[0].arn
    domain_name          = aws_s3_bucket.audit_logs[0].bucket_domain_name
    regional_domain_name = aws_s3_bucket.audit_logs[0].bucket_regional_domain_name
    hosted_zone_id       = aws_s3_bucket.audit_logs[0].hosted_zone_id
    region               = aws_s3_bucket.audit_logs[0].region
  } : null
}

# Consolidated Outputs
output "all_bucket_ids" {
  description = "Map of all bucket IDs by purpose"
  value = {
    content       = aws_s3_bucket.content.id
    user_uploads  = aws_s3_bucket.user_uploads.id
    backups       = aws_s3_bucket.backups.id
    cdn_logs      = aws_s3_bucket.cdn_logs.id
    static_assets = aws_s3_bucket.static_assets.id
    audit_logs    = var.enable_audit_logging ? aws_s3_bucket.audit_logs[0].id : null
  }
}

output "all_bucket_arns" {
  description = "Map of all bucket ARNs by purpose"
  value = {
    content       = aws_s3_bucket.content.arn
    user_uploads  = aws_s3_bucket.user_uploads.arn
    backups       = aws_s3_bucket.backups.arn
    cdn_logs      = aws_s3_bucket.cdn_logs.arn
    static_assets = aws_s3_bucket.static_assets.arn
    audit_logs    = var.enable_audit_logging ? aws_s3_bucket.audit_logs[0].arn : null
  }
}

# CloudFront Integration
output "static_assets_origin" {
  description = "Origin configuration for CloudFront"
  value = {
    domain_name              = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id               = "S3-${aws_s3_bucket.static_assets.id}"
    origin_access_control_id = null # Set when CloudFront OAC is created
  }
}

# Upload Configuration
output "upload_endpoints" {
  description = "Upload endpoints for different content types"
  value = {
    content      = "s3://${aws_s3_bucket.content.id}"
    user_uploads = "s3://${aws_s3_bucket.user_uploads.id}"
    static_assets = "s3://${aws_s3_bucket.static_assets.id}"
  }
}

# CORS Configuration
output "cors_configuration" {
  description = "CORS configuration for user uploads"
  value = {
    allowed_origins = var.allowed_origins
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_headers = ["*"]
    max_age_seconds = 3600
  }
}

# Encryption Configuration
output "encryption_configuration" {
  description = "Encryption settings for all buckets"
  value = {
    algorithm          = "aws:kms"
    kms_key_arn       = var.kms_key_arn
    bucket_key_enabled = true
  }
}

# Lifecycle Configuration
output "lifecycle_policies" {
  description = "Lifecycle policies applied to buckets"
  value = {
    backups = {
      transition_to_ia           = var.backup_transition_days.to_ia
      transition_to_glacier      = var.backup_transition_days.to_glacier
      transition_to_deep_archive = var.backup_transition_days.to_deep_archive
    }
    logs = {
      retention_days = var.log_retention_days
    }
  }
}

# Compliance Status
output "compliance_configuration" {
  description = "Compliance settings for buckets"
  value = {
    coppa_enabled = var.coppa_compliance
    ferpa_enabled = var.ferpa_compliance
    gdpr_enabled  = var.gdpr_compliance
    audit_logging = var.enable_audit_logging
    object_lock   = var.enable_object_lock
    versioning    = var.enable_versioning
  }
}

# Monitoring Configuration
output "monitoring" {
  description = "Monitoring configuration for buckets"
  value = {
    cloudwatch_alarms = [for alarm in aws_cloudwatch_metric_alarm.bucket_size : alarm.alarm_name]
    size_threshold    = var.bucket_size_alarm_threshold
    sns_topics        = var.sns_alert_topic_arns
  }
}

# Access Configuration
output "public_access_block" {
  description = "Public access block configuration (all buckets)"
  value = {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }
}

# Event Notifications
output "event_notifications" {
  description = "Event notification configuration"
  value = var.enable_event_notifications ? {
    lambda_processor = var.content_processor_lambda_arn
    sqs_queue       = var.processing_queue_arn
  } : null
}

# Data Classification
output "data_classification_tags" {
  description = "Data classification for each bucket"
  value = var.data_classification
}

# Module Summary
output "s3_module_summary" {
  description = "Summary of S3 module configuration"
  value = {
    environment              = var.environment
    project_name            = var.project_name
    total_buckets_created   = var.enable_audit_logging ? 6 : 5
    encryption_enabled      = true
    versioning_enabled      = var.enable_versioning
    intelligent_tiering     = var.enable_intelligent_tiering
    compliance = {
      coppa = var.coppa_compliance
      ferpa = var.ferpa_compliance
      gdpr  = var.gdpr_compliance
    }
  }
}