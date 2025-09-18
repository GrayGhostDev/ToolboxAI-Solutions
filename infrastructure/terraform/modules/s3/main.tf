# AWS S3 Module for ToolBoxAI Solutions
# Secure storage with compliance and encryption

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  bucket_prefix = "${var.project_name}-${var.environment}"

  compliance_lifecycle_rules = var.gdpr_compliance ? {
    gdpr_retention = {
      id      = "gdpr-data-retention"
      enabled = true
      expiration = {
        days = 2555 # 7 years for GDPR
      }
    }
  } : {}

  ferpa_lifecycle_rules = var.ferpa_compliance ? {
    ferpa_retention = {
      id      = "ferpa-educational-records"
      enabled = true
      transition = [
        {
          days          = 90
          storage_class = "STANDARD_IA"
        },
        {
          days          = 365
          storage_class = "GLACIER"
        }
      ]
    }
  } : {}

  coppa_settings = var.coppa_compliance ? {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  } : {}
}

# Content Storage Bucket
resource "aws_s3_bucket" "content" {
  bucket = "${local.bucket_prefix}-content"

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.bucket_prefix}-content"
      Purpose     = "Educational content storage"
      Compliance  = join(",", compact([
        var.coppa_compliance ? "COPPA" : "",
        var.ferpa_compliance ? "FERPA" : "",
        var.gdpr_compliance ? "GDPR" : ""
      ]))
    }
  )
}

resource "aws_s3_bucket_versioning" "content" {
  bucket = aws_s3_bucket.content.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "content" {
  bucket = aws_s3_bucket.content.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "content" {
  bucket = aws_s3_bucket.content.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# User Uploads Bucket with strict access controls
resource "aws_s3_bucket" "user_uploads" {
  bucket = "${local.bucket_prefix}-user-uploads"

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.bucket_prefix}-user-uploads"
      Purpose     = "User uploaded content"
      Sensitivity = "High"
      Compliance  = "COPPA,FERPA"
    }
  )
}

resource "aws_s3_bucket_versioning" "user_uploads" {
  bucket = aws_s3_bucket.user_uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "user_uploads" {
  bucket = aws_s3_bucket.user_uploads.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "user_uploads" {
  bucket = aws_s3_bucket.user_uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS configuration for user uploads
resource "aws_s3_bucket_cors_configuration" "user_uploads" {
  bucket = aws_s3_bucket.user_uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = var.allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# Backup Bucket with lifecycle policies
resource "aws_s3_bucket" "backups" {
  bucket = "${local.bucket_prefix}-backups"

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.bucket_prefix}-backups"
      Purpose     = "System backups and archives"
      Retention   = "Long-term"
    }
  )
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "backup-retention"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Distribution Logs Bucket
resource "aws_s3_bucket" "cdn_logs" {
  bucket = "${local.bucket_prefix}-cdn-logs"

  tags = merge(
    var.common_tags,
    {
      Name     = "${local.bucket_prefix}-cdn-logs"
      Purpose  = "CloudFront access logs"
    }
  )
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cdn_logs" {
  bucket = aws_s3_bucket.cdn_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256" # CloudFront doesn't support KMS for logs
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cdn_logs" {
  bucket = aws_s3_bucket.cdn_logs.id

  rule {
    id     = "delete-old-logs"
    status = "Enabled"

    expiration {
      days = var.log_retention_days
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cdn_logs" {
  bucket = aws_s3_bucket.cdn_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Static Assets Bucket (for CloudFront distribution)
resource "aws_s3_bucket" "static_assets" {
  bucket = "${local.bucket_prefix}-static-assets"

  tags = merge(
    var.common_tags,
    {
      Name     = "${local.bucket_prefix}-static-assets"
      Purpose  = "Static website assets"
      CDN      = "CloudFront"
    }
  )
}

resource "aws_s3_bucket_versioning" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Allow CloudFront OAC access
resource "aws_s3_bucket_policy" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static_assets.arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceArn" = var.cloudfront_distribution_arn
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.static_assets]
}

resource "aws_s3_bucket_public_access_block" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = true
  block_public_policy     = false # Allow bucket policy for CloudFront
  ignore_public_acls      = true
  restrict_public_buckets = false # Allow CloudFront access
}

# Compliance Audit Logs Bucket
resource "aws_s3_bucket" "audit_logs" {
  count = var.enable_audit_logging ? 1 : 0

  bucket = "${local.bucket_prefix}-audit-logs"

  tags = merge(
    var.common_tags,
    {
      Name       = "${local.bucket_prefix}-audit-logs"
      Purpose    = "Compliance audit logs"
      Compliance = "SOC2,HIPAA"
      Retention  = "7years"
    }
  )
}

resource "aws_s3_bucket_versioning" "audit_logs" {
  count = var.enable_audit_logging ? 1 : 0

  bucket = aws_s3_bucket.audit_logs[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audit_logs" {
  count = var.enable_audit_logging ? 1 : 0

  bucket = aws_s3_bucket.audit_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_object_lock_configuration" "audit_logs" {
  count = var.enable_audit_logging ? 1 : 0

  bucket = aws_s3_bucket.audit_logs[0].id

  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = 2555 # 7 years
    }
  }
}

resource "aws_s3_bucket_public_access_block" "audit_logs" {
  count = var.enable_audit_logging ? 1 : 0

  bucket = aws_s3_bucket.audit_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Access Logging
resource "aws_s3_bucket_logging" "all_buckets" {
  for_each = {
    content      = aws_s3_bucket.content.id
    user_uploads = aws_s3_bucket.user_uploads.id
    backups      = aws_s3_bucket.backups.id
    static_assets = aws_s3_bucket.static_assets.id
  }

  bucket = each.value

  target_bucket = aws_s3_bucket.cdn_logs.id
  target_prefix = "${each.key}/"
}

# CloudWatch Metrics
resource "aws_cloudwatch_metric_alarm" "bucket_size" {
  for_each = {
    content      = aws_s3_bucket.content.id
    user_uploads = aws_s3_bucket.user_uploads.id
    backups      = aws_s3_bucket.backups.id
  }

  alarm_name          = "${each.key}-bucket-size-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name        = "BucketSizeBytes"
  namespace          = "AWS/S3"
  period             = "86400"
  statistic          = "Average"
  threshold          = var.bucket_size_alarm_threshold
  alarm_description  = "Alert when bucket size exceeds threshold"
  alarm_actions      = var.sns_alert_topic_arns

  dimensions = {
    BucketName = each.value
    StorageType = "StandardStorage"
  }
}

# Bucket Notifications for processing
resource "aws_s3_bucket_notification" "user_uploads" {
  count = var.enable_event_notifications ? 1 : 0

  bucket = aws_s3_bucket.user_uploads.id

  lambda_function {
    lambda_function_arn = var.content_processor_lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }

  queue {
    queue_arn     = var.processing_queue_arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".json"
  }
}

# Intelligent Tiering for cost optimization
resource "aws_s3_bucket_intelligent_tiering_configuration" "content" {
  bucket = aws_s3_bucket.content.id
  name   = "entire-bucket"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

# Outputs
output "bucket_ids" {
  description = "Map of all bucket IDs"
  value = {
    content       = aws_s3_bucket.content.id
    user_uploads  = aws_s3_bucket.user_uploads.id
    backups       = aws_s3_bucket.backups.id
    cdn_logs      = aws_s3_bucket.cdn_logs.id
    static_assets = aws_s3_bucket.static_assets.id
    audit_logs    = var.enable_audit_logging ? aws_s3_bucket.audit_logs[0].id : null
  }
}

output "bucket_arns" {
  description = "Map of all bucket ARNs"
  value = {
    content       = aws_s3_bucket.content.arn
    user_uploads  = aws_s3_bucket.user_uploads.arn
    backups       = aws_s3_bucket.backups.arn
    cdn_logs      = aws_s3_bucket.cdn_logs.arn
    static_assets = aws_s3_bucket.static_assets.arn
    audit_logs    = var.enable_audit_logging ? aws_s3_bucket.audit_logs[0].arn : null
  }
}

output "bucket_domain_names" {
  description = "Map of bucket domain names"
  value = {
    content       = aws_s3_bucket.content.bucket_domain_name
    user_uploads  = aws_s3_bucket.user_uploads.bucket_domain_name
    static_assets = aws_s3_bucket.static_assets.bucket_domain_name
  }
}

output "bucket_regional_domain_names" {
  description = "Map of bucket regional domain names"
  value = {
    content       = aws_s3_bucket.content.bucket_regional_domain_name
    user_uploads  = aws_s3_bucket.user_uploads.bucket_regional_domain_name
    static_assets = aws_s3_bucket.static_assets.bucket_regional_domain_name
  }
}