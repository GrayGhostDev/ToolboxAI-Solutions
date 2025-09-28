# ToolBoxAI Solutions - Staging Environment

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
    key            = "environments/staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "toolboxai-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "staging"
      Project     = "ToolBoxAI-Solutions"
      ManagedBy   = "Terraform"
      CostCenter  = "engineering"
      Owner       = var.owner_email
    }
  }
}

# Call the root module
module "toolboxai" {
  source = "../../"

  # Environment Configuration
  environment    = "staging"
  aws_region     = var.aws_region
  project_name   = "toolboxai"
  cost_center    = "engineering"
  owner_email    = var.owner_email
  alert_email    = var.alert_email

  # VPC Configuration - Production-like but smaller
  vpc_cidr                 = "10.20.0.0/16"
  public_subnet_cidrs      = ["10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24"]
  private_subnet_cidrs     = ["10.20.10.0/24", "10.20.11.0/24", "10.20.12.0/24"]
  database_subnet_cidrs    = ["10.20.20.0/24", "10.20.21.0/24", "10.20.22.0/24"]

  # Security Configuration
  allowed_ssh_ips = var.allowed_ssh_ips

  # EKS Configuration - Production-like but smaller
  eks_cluster_version = "1.28"
  eks_node_instance_types = {
    general = ["t3.large", "t3a.large"]
    mcp     = ["r5.large"]
    gpu     = ["g4dn.large"]  # Smaller GPU instances for staging
  }

  # RDS Configuration - Production-like setup
  rds_instance_class = {
    dev        = "db.t3.micro"
    staging    = "db.r6g.large"
    production = "db.r6g.xlarge"
  }

  rds_backup_retention = {
    dev        = 3
    staging    = 14
    production = 30
  }

  # MCP Configuration
  mcp_context_ttl_days = 14
  mcp_max_agents = {
    dev        = 5
    staging    = 20
    production = 50
  }

  # API Keys
  openai_api_key    = var.openai_api_key
  anthropic_api_key = var.anthropic_api_key
  pusher_app_id     = var.pusher_app_id
  pusher_key        = var.pusher_key
  pusher_secret     = var.pusher_secret
  pusher_cluster    = "us2"

  # Monitoring Configuration - Enhanced for staging
  log_retention_days = {
    dev        = 7
    staging    = 30
    production = 90
  }

  enable_detailed_monitoring = true

  # Auto-scaling Configuration - Production-like
  auto_scaling_config = {
    min_capacity       = 2
    max_capacity       = 8
    target_cpu         = 70
    target_memory      = 80
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }

  # Backup Configuration - Production-like
  backup_config = {
    enable_automated_backups = true
    backup_window           = "03:00-04:00"
    retention_period        = 14
    copy_to_region         = "us-west-2"
  }

  # Domain Configuration
  domain_name = "staging.toolboxai.solutions"
  subdomain_prefixes = {
    api       = "api-staging"
    app       = "app-staging"
    dashboard = "dashboard-staging"
    mcp       = "mcp-staging"
    ws        = "ws-staging"
  }

  # Feature Flags - Production-like with some optimizations
  feature_flags = {
    enable_gpu_nodes         = true
    enable_spot_instances    = true   # Still use spot for cost savings
    enable_multi_region      = false
    enable_vpc_peering       = false
    enable_private_link      = true
    enable_waf              = true   # Enable for staging testing
    enable_shield           = false  # No advanced DDoS protection
    enable_guardduty        = true   # Enable security monitoring
    enable_security_hub     = true   # Enable compliance monitoring
    enable_config          = true   # Enable configuration monitoring
    enable_cloudtrail      = true
    enable_xray            = true   # Enable tracing for performance testing
    enable_container_insights = true
  }

  # Cost Optimization - Balanced approach
  use_spot_instances = true
  spot_max_price     = "0.30"

  reserved_instance_config = {
    enable          = false  # No RIs for staging yet
    payment_option  = "PARTIAL_UPFRONT"
    offering_class  = "STANDARD"
    instance_count  = 0
  }

  # Additional tags for staging environment
  additional_tags = {
    Purpose           = "staging"
    PreProduction    = "true"
    LoadTesting      = "enabled"
    SecurityTesting  = "enabled"
  }
}

# Load testing resources
resource "aws_cloudwatch_event_rule" "load_test_schedule" {
  count = var.enable_load_testing ? 1 : 0

  name                = "staging-load-test-schedule"
  description         = "Trigger load tests in staging"
  schedule_expression = var.load_test_schedule

  tags = {
    Environment = "staging"
    Purpose     = "load-testing"
  }
}

# Staging-specific monitoring dashboard
resource "aws_cloudwatch_dashboard" "staging_performance" {
  dashboard_name = "staging-toolboxai-performance"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${module.toolboxai.load_balancer_dns}"],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Staging Load Balancer Performance"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EKS", "cluster_failed_request_count", "ClusterName", "${module.toolboxai.cluster_id}"],
            [".", "cluster_request_total", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Staging EKS Performance"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6

        properties = {
          query   = "SOURCE '${module.toolboxai.application_log_group_name}' | fields @timestamp, @message | filter @message like /performance/ | sort @timestamp desc | limit 50"
          region  = var.aws_region
          title   = "Performance Logs"
          view    = "table"
        }
      }
    ]
  })
}

# Blue-Green Deployment Support
resource "aws_route53_record" "blue" {
  count = var.enable_blue_green ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "blue.staging.toolboxai.solutions"
  type    = "CNAME"
  ttl     = 60
  records = [module.toolboxai.load_balancer_dns]
}

resource "aws_route53_record" "green" {
  count = var.enable_blue_green ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "green.staging.toolboxai.solutions"
  type    = "CNAME"
  ttl     = 60
  records = [module.toolboxai.load_balancer_dns]
}

# Synthetic monitoring for staging
resource "aws_synthetics_canary" "api_health" {
  count = var.enable_synthetic_monitoring ? 1 : 0

  name                 = "staging-api-health"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics[0].bucket}/canary-artifacts/"
  execution_role_arn   = aws_iam_role.synthetics[0].arn
  handler              = "apiCanaryBlueprint.handler"
  zip_file            = "api-health-canary.zip"
  runtime_version      = "syn-nodejs-puppeteer-3.9"

  schedule {
    expression = "rate(5 minutes)"
  }

  run_config {
    timeout_in_seconds = 60
  }

  tags = {
    Environment = "staging"
    Purpose     = "synthetic-monitoring"
  }
}

resource "aws_s3_bucket" "synthetics" {
  count = var.enable_synthetic_monitoring ? 1 : 0

  bucket        = "toolboxai-staging-synthetics-${random_string.bucket_suffix[0].result}"
  force_destroy = true

  tags = {
    Environment = "staging"
    Purpose     = "synthetic-monitoring"
  }
}

resource "aws_iam_role" "synthetics" {
  count = var.enable_synthetic_monitoring ? 1 : 0

  name = "staging-synthetics-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "synthetics" {
  count = var.enable_synthetic_monitoring ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/CloudWatchSyntheticsExecutionRolePolicy"
  role       = aws_iam_role.synthetics[0].name
}

resource "random_string" "bucket_suffix" {
  count = var.enable_synthetic_monitoring ? 1 : 0

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

output "blue_green_endpoints" {
  description = "Blue-Green deployment endpoints"
  value = var.enable_blue_green ? {
    blue  = aws_route53_record.blue[0].fqdn
    green = aws_route53_record.green[0].fqdn
  } : null
}

output "staging_dashboard_url" {
  description = "Staging performance dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.staging_performance.dashboard_name}"
}

output "synthetic_monitoring_status" {
  description = "Synthetic monitoring canary status"
  value       = var.enable_synthetic_monitoring ? aws_synthetics_canary.api_health[0].status : "disabled"
}