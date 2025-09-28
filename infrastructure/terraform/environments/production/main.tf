# ToolBoxAI Solutions - Production Environment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "toolboxai-terraform-state"
    key            = "environments/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "toolboxai-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "production"
      Project     = "ToolBoxAI-Solutions"
      ManagedBy   = "Terraform"
      CostCenter  = "engineering"
      Owner       = var.owner_email
      Compliance  = "SOC2"
      Backup      = "required"
    }
  }
}

# Multi-region provider for disaster recovery
provider "aws" {
  alias  = "disaster_recovery"
  region = var.disaster_recovery_region

  default_tags {
    tags = {
      Environment = "production"
      Project     = "ToolBoxAI-Solutions"
      ManagedBy   = "Terraform"
      CostCenter  = "engineering"
      Owner       = var.owner_email
      Purpose     = "disaster-recovery"
    }
  }
}

# Call the root module
module "toolboxai" {
  source = "../../"

  # Environment Configuration
  environment    = "production"
  aws_region     = var.aws_region
  project_name   = "toolboxai"
  cost_center    = "engineering"
  owner_email    = var.owner_email
  alert_email    = var.alert_email

  # VPC Configuration - Full production setup
  vpc_cidr                 = "10.0.0.0/16"
  public_subnet_cidrs      = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs     = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  database_subnet_cidrs    = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

  # Security Configuration - Strict for production
  allowed_ssh_ips = var.allowed_ssh_ips

  # EKS Configuration - Full production setup
  eks_cluster_version = "1.28"
  eks_node_instance_types = {
    general = ["m6i.xlarge", "m6i.2xlarge"]
    mcp     = ["r6i.xlarge", "r6i.2xlarge"]
    gpu     = ["g5.xlarge", "g5.2xlarge"]
  }

  # RDS Configuration - High availability
  rds_instance_class = {
    dev        = "db.t3.micro"
    staging    = "db.r6g.large"
    production = "db.r6g.2xlarge"
  }

  rds_backup_retention = {
    dev        = 3
    staging    = 14
    production = 35
  }

  # MCP Configuration - Full scale
  mcp_context_ttl_days = 90
  mcp_max_agents = {
    dev        = 5
    staging    = 20
    production = 100
  }

  # API Keys
  openai_api_key    = var.openai_api_key
  anthropic_api_key = var.anthropic_api_key
  pusher_app_id     = var.pusher_app_id
  pusher_key        = var.pusher_key
  pusher_secret     = var.pusher_secret
  pusher_cluster    = "us2"

  # Monitoring Configuration - Enhanced for production
  log_retention_days = {
    dev        = 7
    staging    = 30
    production = 365
  }

  enable_detailed_monitoring = true

  # Auto-scaling Configuration - Production optimized
  auto_scaling_config = {
    min_capacity       = 5
    max_capacity       = 20
    target_cpu         = 60
    target_memory      = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }

  # Backup Configuration - Comprehensive
  backup_config = {
    enable_automated_backups = true
    backup_window           = "02:00-03:00"
    retention_period        = 35
    copy_to_region         = var.disaster_recovery_region
  }

  # Domain Configuration
  domain_name = var.domain_name
  subdomain_prefixes = {
    api       = "api"
    app       = "app"
    dashboard = "dashboard"
    mcp       = "mcp"
    ws        = "ws"
  }

  # Feature Flags - Full production features
  feature_flags = {
    enable_gpu_nodes         = true
    enable_spot_instances    = false  # On-demand for production reliability
    enable_multi_region      = var.enable_multi_region
    enable_vpc_peering       = var.enable_vpc_peering
    enable_private_link      = true
    enable_waf              = true
    enable_shield           = var.enable_shield_advanced
    enable_guardduty        = true
    enable_security_hub     = true
    enable_config          = true
    enable_cloudtrail      = true
    enable_xray            = true
    enable_container_insights = true
  }

  # Cost Optimization - Balanced for production
  use_spot_instances = false  # Reliability over cost savings
  spot_max_price     = "0.50"

  reserved_instance_config = {
    enable          = var.enable_reserved_instances
    payment_option  = "PARTIAL_UPFRONT"
    offering_class  = "STANDARD"
    instance_count  = var.reserved_instance_count
  }

  # Additional tags for production environment
  additional_tags = {
    Purpose         = "production"
    CriticalSystem  = "true"
    DataRetention   = "7-years"
    ComplianceRequired = "true"
    DisasterRecovery = "enabled"
  }
}

# Disaster Recovery Setup
module "disaster_recovery" {
  count = var.enable_disaster_recovery ? 1 : 0

  source = "../../"
  providers = {
    aws = aws.disaster_recovery
  }

  # Environment Configuration
  environment    = "production-dr"
  aws_region     = var.disaster_recovery_region
  project_name   = "toolboxai-dr"
  cost_center    = "engineering"
  owner_email    = var.owner_email
  alert_email    = var.alert_email

  # Smaller configuration for DR
  vpc_cidr                 = "10.1.0.0/16"
  public_subnet_cidrs      = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs     = ["10.1.10.0/24", "10.1.11.0/24"]
  database_subnet_cidrs    = ["10.1.20.0/24", "10.1.21.0/24"]

  # Minimal setup for DR standby
  eks_node_instance_types = {
    general = ["m6i.large"]
    mcp     = ["r6i.large"]
    gpu     = []
  }

  # Same secrets for DR
  openai_api_key    = var.openai_api_key
  anthropic_api_key = var.anthropic_api_key
  pusher_app_id     = var.pusher_app_id
  pusher_key        = var.pusher_key
  pusher_secret     = var.pusher_secret

  # Minimal monitoring for DR
  log_retention_days = {
    dev        = 7
    staging    = 30
    production = 90
  }

  # DR-specific tags
  additional_tags = {
    Purpose = "disaster-recovery"
    MainRegion = var.aws_region
  }
}

# CloudFront Distribution for Global CDN
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = module.toolboxai.load_balancer_dns
    origin_id   = "ALB-${module.toolboxai.load_balancer_dns}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "ToolBoxAI Production CDN"
  default_root_object = "index.html"

  aliases = var.cloudfront_aliases

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${module.toolboxai.load_balancer_dns}"

    forwarded_values {
      query_string = false
      headers      = ["Authorization", "CloudFront-Forwarded-Proto"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # Cache behavior for API endpoints
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${module.toolboxai.load_balancer_dns}"

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
    viewer_protocol_policy = "https-only"
  }

  # Cache behavior for WebSocket
  ordered_cache_behavior {
    path_pattern     = "/ws/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${module.toolboxai.load_balancer_dns}"

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = false
    viewer_protocol_policy = "https-only"
  }

  price_class = var.cloudfront_price_class

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.ssl_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  web_acl_id = module.toolboxai.waf_web_acl_arn

  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    prefix          = "cloudfront-logs/"
  }

  tags = {
    Environment = "production"
    Purpose     = "cdn"
  }
}

# S3 bucket for CloudFront logs
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket        = "toolboxai-production-cloudfront-logs-${random_string.bucket_suffix.result}"
  force_destroy = false

  tags = {
    Environment = "production"
    Purpose     = "logging"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    id     = "cloudfront_logs_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years
    }
  }
}

# Route53 Health Checks
resource "aws_route53_health_check" "primary" {
  fqdn                            = var.domain_name
  port                           = 443
  type                           = "HTTPS"
  resource_path                  = "/health"
  failure_threshold              = "3"
  request_interval               = "30"
  cloudwatch_alarm_region        = var.aws_region
  cloudwatch_alarm_name          = "production-health-check-failed"
  insufficient_data_health_status = "Failure"

  tags = {
    Name        = "production-primary-health-check"
    Environment = "production"
  }
}

resource "aws_route53_health_check" "api" {
  fqdn                            = "api.${var.domain_name}"
  port                           = 443
  type                           = "HTTPS"
  resource_path                  = "/health"
  failure_threshold              = "3"
  request_interval               = "30"
  cloudwatch_alarm_region        = var.aws_region
  cloudwatch_alarm_name          = "production-api-health-check-failed"
  insufficient_data_health_status = "Failure"

  tags = {
    Name        = "production-api-health-check"
    Environment = "production"
  }
}

# CloudWatch Alarms for Health Checks
resource "aws_cloudwatch_metric_alarm" "health_check_failed" {
  alarm_name          = "production-health-check-failed"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "This metric monitors health check"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.primary.id
  }

  tags = {
    Environment = "production"
    Severity    = "critical"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_health_check_failed" {
  alarm_name          = "production-api-health-check-failed"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "This metric monitors API health check"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.api.id
  }

  tags = {
    Environment = "production"
    Severity    = "critical"
  }
}

# Critical Alerts SNS Topic
resource "aws_sns_topic" "critical_alerts" {
  name              = "production-critical-alerts"
  kms_master_key_id = module.toolboxai.kms_key_id

  tags = {
    Environment = "production"
    Purpose     = "critical-alerting"
  }
}

resource "aws_sns_topic_subscription" "critical_email" {
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "email"
  endpoint  = var.critical_alert_email
}

resource "aws_sns_topic_subscription" "critical_pagerduty" {
  count = var.pagerduty_endpoint != "" ? 1 : 0

  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "https"
  endpoint  = var.pagerduty_endpoint
}

# AWS Backup for Production
resource "aws_backup_vault" "production" {
  name        = "production-backup-vault"
  kms_key_arn = module.toolboxai.kms_key_arn

  tags = {
    Environment = "production"
    Purpose     = "backup"
  }
}

resource "aws_backup_plan" "production" {
  name = "production-backup-plan"

  rule {
    rule_name         = "daily_backup"
    target_vault_name = aws_backup_vault.production.name
    schedule          = "cron(0 5 ? * * *)"  # 5 AM daily

    recovery_point_tags = {
      Environment = "production"
      Frequency   = "daily"
    }

    lifecycle {
      cold_storage_after = 30
      delete_after       = 365
    }

    copy_action {
      destination_vault_arn = aws_backup_vault.production_cross_region.arn

      lifecycle {
        cold_storage_after = 30
        delete_after       = 365
      }
    }
  }

  rule {
    rule_name         = "weekly_backup"
    target_vault_name = aws_backup_vault.production.name
    schedule          = "cron(0 6 ? * SUN *)"  # 6 AM Sunday

    recovery_point_tags = {
      Environment = "production"
      Frequency   = "weekly"
    }

    lifecycle {
      cold_storage_after = 30
      delete_after       = 2555  # 7 years
    }
  }

  tags = {
    Environment = "production"
    Purpose     = "backup"
  }
}

# Cross-region backup vault
resource "aws_backup_vault" "production_cross_region" {
  provider = aws.disaster_recovery

  name        = "production-backup-vault-cross-region"
  kms_key_arn = var.dr_kms_key_arn

  tags = {
    Environment = "production"
    Purpose     = "cross-region-backup"
  }
}

# Random string for unique naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.toolboxai.eks_cluster_endpoint
  sensitive   = true
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.toolboxai.vpc_id
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = module.toolboxai.load_balancer_dns
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "disaster_recovery_vpc_id" {
  description = "Disaster recovery VPC ID"
  value       = var.enable_disaster_recovery ? module.disaster_recovery[0].vpc_id : null
}

output "backup_vault_arn" {
  description = "Production backup vault ARN"
  value       = aws_backup_vault.production.arn
}

output "health_check_ids" {
  description = "Route53 health check IDs"
  value = {
    primary = aws_route53_health_check.primary.id
    api     = aws_route53_health_check.api.id
  }
}

output "critical_alerts_topic_arn" {
  description = "Critical alerts SNS topic ARN"
  value       = aws_sns_topic.critical_alerts.arn
}