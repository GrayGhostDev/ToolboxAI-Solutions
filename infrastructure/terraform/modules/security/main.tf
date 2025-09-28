# ToolBoxAI Solutions - Security Module
# Creates security groups, KMS keys, and security-related resources

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# KMS Key for general encryption
resource "aws_kms_key" "general" {
  count = var.enable_kms_key ? 1 : 0

  description             = "KMS key for ${var.environment} environment general encryption"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true

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
        Sid    = "Allow EKS Service"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow RDS Service"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.environment}-general-kms-key"
    Type = "encryption"
  })
}

resource "aws_kms_alias" "general" {
  count = var.enable_kms_key ? 1 : 0

  name          = "alias/${var.environment}-general-encryption"
  target_key_id = aws_kms_key.general[0].key_id
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.environment}-alb-"
  vpc_id      = var.vpc_id
  description = "Security group for Application Load Balancer"

  # HTTP access
  dynamic "ingress" {
    for_each = var.enable_http ? [1] : []
    content {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = var.allowed_http_ips
      description = "HTTP access"
    }
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_http_ips
    description = "HTTPS access"
  }

  # Health check port
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Health check port"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-alb-sg"
    Type = "load-balancer"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for EKS Control Plane
resource "aws_security_group" "eks_control_plane" {
  name_prefix = "${var.environment}-eks-control-plane-"
  vpc_id      = var.vpc_id
  description = "Security group for EKS control plane"

  # Allow ALB to communicate with control plane
  ingress {
    from_port                = 443
    to_port                  = 443
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.alb.id
    description              = "ALB to control plane"
  }

  # Allow node groups to communicate with control plane
  ingress {
    from_port                = 443
    to_port                  = 443
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
    description              = "Node groups to control plane"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-eks-control-plane-sg"
    Type = "kubernetes-control-plane"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for EKS Node Groups
resource "aws_security_group" "eks_nodes" {
  name_prefix = "${var.environment}-eks-nodes-"
  vpc_id      = var.vpc_id
  description = "Security group for EKS node groups"

  # Allow nodes to communicate with each other
  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
    description = "Node to node communication"
  }

  # Allow control plane to communicate with nodes
  ingress {
    from_port                = 1025
    to_port                  = 65535
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.eks_control_plane.id
    description              = "Control plane to node kubelets"
  }

  # Allow control plane to communicate with node groups (API server)
  ingress {
    from_port                = 443
    to_port                  = 443
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.eks_control_plane.id
    description              = "Control plane API server"
  }

  # Allow ALB to reach nodes
  ingress {
    from_port                = 30000
    to_port                  = 32767
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.alb.id
    description              = "ALB to NodePort services"
  }

  # Allow RDS access
  ingress {
    from_port                = 5432
    to_port                  = 5432
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.rds.id
    description              = "PostgreSQL access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-eks-nodes-sg"
    Type = "kubernetes-nodes"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name_prefix = "${var.environment}-rds-"
  vpc_id      = var.vpc_id
  description = "Security group for RDS PostgreSQL"

  # PostgreSQL access from EKS nodes
  ingress {
    from_port                = 5432
    to_port                  = 5432
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
    description              = "PostgreSQL from EKS nodes"
  }

  # PostgreSQL access from Lambda functions
  ingress {
    from_port                = 5432
    to_port                  = 5432
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.lambda.id
    description              = "PostgreSQL from Lambda"
  }

  # Optional: Allow access from bastion host for debugging
  dynamic "ingress" {
    for_each = var.enable_bastion_access ? [1] : []
    content {
      from_port                = 5432
      to_port                  = 5432
      protocol                 = "tcp"
      source_security_group_id = aws_security_group.bastion[0].id
      description              = "PostgreSQL from bastion"
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-rds-sg"
    Type = "database"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for Lambda Functions
resource "aws_security_group" "lambda" {
  name_prefix = "${var.environment}-lambda-"
  vpc_id      = var.vpc_id
  description = "Security group for Lambda functions"

  # No inbound rules needed for Lambda

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound"
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP outbound"
  }

  # Database access
  egress {
    from_port                = 5432
    to_port                  = 5432
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.rds.id
    description              = "PostgreSQL access"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-lambda-sg"
    Type = "compute"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Optional Bastion Host Security Group
resource "aws_security_group" "bastion" {
  count = var.enable_bastion_access ? 1 : 0

  name_prefix = "${var.environment}-bastion-"
  vpc_id      = var.vpc_id
  description = "Security group for bastion host"

  # SSH access from allowed IPs
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_ips
    description = "SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-bastion-sg"
    Type = "bastion"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for Redis/ElastiCache
resource "aws_security_group" "redis" {
  name_prefix = "${var.environment}-redis-"
  vpc_id      = var.vpc_id
  description = "Security group for Redis/ElastiCache"

  # Redis access from EKS nodes
  ingress {
    from_port                = 6379
    to_port                  = 6379
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
    description              = "Redis from EKS nodes"
  }

  # Redis access from Lambda functions
  ingress {
    from_port                = 6379
    to_port                  = 6379
    protocol                 = "tcp"
    source_security_group_id = aws_security_group.lambda.id
    description              = "Redis from Lambda"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-redis-sg"
    Type = "cache"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# WAF Web ACL for ALB protection
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_waf ? 1 : 0

  name  = "${var.environment}-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.environment}RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.environment}CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Known Bad Inputs Rule Set
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.environment}KnownBadInputs"
      sampled_requests_enabled   = true
    }
  }

  # IP reputation list
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.environment}IpReputationList"
      sampled_requests_enabled   = true
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-web-acl"
    Type = "security"
  })

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.environment}WebAcl"
    sampled_requests_enabled   = true
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count = var.enable_waf && var.enable_waf_logging ? 1 : 0

  resource_arn            = aws_wafv2_web_acl.main[0].arn
  log_destination_configs = [aws_cloudwatch_log_group.waf[0].arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }
}

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf" {
  count = var.enable_waf && var.enable_waf_logging ? 1 : 0

  name              = "/aws/wafv2/${var.environment}"
  retention_in_days = var.waf_log_retention_days

  tags = merge(var.tags, {
    Name = "${var.environment}-waf-logs"
  })
}

# AWS Config for compliance monitoring
resource "aws_config_configuration_recorder" "main" {
  count = var.enable_config ? 1 : 0

  name     = "${var.environment}-config-recorder"
  role_arn = aws_iam_role.config[0].arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }

  depends_on = [aws_config_delivery_channel.main]
}

resource "aws_config_delivery_channel" "main" {
  count = var.enable_config ? 1 : 0

  name           = "${var.environment}-config-delivery-channel"
  s3_bucket_name = aws_s3_bucket.config[0].bucket
}

# S3 bucket for AWS Config
resource "aws_s3_bucket" "config" {
  count = var.enable_config ? 1 : 0

  bucket        = "${var.environment}-toolboxai-config-${random_string.bucket_suffix[0].result}"
  force_destroy = var.environment != "production"

  tags = merge(var.tags, {
    Name = "${var.environment}-config-bucket"
    Type = "compliance"
  })
}

resource "aws_s3_bucket_policy" "config" {
  count = var.enable_config ? 1 : 0

  bucket = aws_s3_bucket.config[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.config[0].arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "AWSConfigBucketExistenceCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.config[0].arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "AWSConfigBucketDelivery"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.config[0].arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# IAM Role for AWS Config
resource "aws_iam_role" "config" {
  count = var.enable_config ? 1 : 0

  name = "${var.environment}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "config" {
  count = var.enable_config ? 1 : 0

  role       = aws_iam_role.config[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# Random string for unique resource names
resource "random_string" "bucket_suffix" {
  count = var.enable_config ? 1 : 0

  length  = 8
  special = false
  upper   = false
}