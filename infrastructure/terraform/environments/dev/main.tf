# ToolBoxAI Solutions - Development Environment

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
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "toolboxai-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "dev"
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
  environment    = "dev"
  aws_region     = var.aws_region
  project_name   = "toolboxai"
  cost_center    = "engineering"
  owner_email    = var.owner_email
  alert_email    = var.alert_email

  # VPC Configuration - Smaller CIDR for dev
  vpc_cidr                 = "10.10.0.0/16"
  public_subnet_cidrs      = ["10.10.1.0/24", "10.10.2.0/24"]
  private_subnet_cidrs     = ["10.10.10.0/24", "10.10.11.0/24"]
  database_subnet_cidrs    = ["10.10.20.0/24", "10.10.21.0/24"]

  # Security Configuration
  allowed_ssh_ips = var.allowed_ssh_ips

  # EKS Configuration - Minimal for dev
  eks_cluster_version = "1.28"
  eks_node_instance_types = {
    general = ["t3.medium"]
    mcp     = ["t3.large"]
    gpu     = []  # No GPU nodes in dev
  }

  # RDS Configuration - Smaller instance for dev
  rds_instance_class = {
    dev        = "db.t3.micro"
    staging    = "db.t3.small"
    production = "db.r6g.xlarge"
  }

  rds_backup_retention = {
    dev        = 3
    staging    = 7
    production = 30
  }

  # MCP Configuration
  mcp_context_ttl_days = 7  # Shorter TTL for dev
  mcp_max_agents = {
    dev        = 5
    staging    = 10
    production = 50
  }

  # API Keys (from environment variables or parameter store)
  openai_api_key    = var.openai_api_key
  anthropic_api_key = var.anthropic_api_key
  pusher_app_id     = var.pusher_app_id
  pusher_key        = var.pusher_key
  pusher_secret     = var.pusher_secret
  pusher_cluster    = "us2"

  # Monitoring Configuration - Reduced for dev
  log_retention_days = {
    dev        = 7
    staging    = 14
    production = 90
  }

  enable_detailed_monitoring = false  # Reduce costs in dev

  # Auto-scaling Configuration - Conservative for dev
  auto_scaling_config = {
    min_capacity       = 1
    max_capacity       = 3
    target_cpu         = 80
    target_memory      = 85
    scale_in_cooldown  = 300
    scale_out_cooldown = 120
  }

  # Backup Configuration - Minimal for dev
  backup_config = {
    enable_automated_backups = false
    backup_window           = "03:00-04:00"
    retention_period        = 3
    copy_to_region         = ""  # No cross-region backup for dev
  }

  # Domain Configuration
  domain_name = "dev.toolboxai.solutions"
  subdomain_prefixes = {
    api       = "api-dev"
    app       = "app-dev"
    dashboard = "dashboard-dev"
    mcp       = "mcp-dev"
    ws        = "ws-dev"
  }

  # Feature Flags - Optimized for development
  feature_flags = {
    enable_gpu_nodes         = false  # No GPU in dev
    enable_spot_instances    = true   # Use spot for cost savings
    enable_multi_region      = false
    enable_vpc_peering       = false
    enable_private_link      = false
    enable_waf              = false  # Reduce complexity in dev
    enable_shield           = false
    enable_guardduty        = false  # Reduce costs
    enable_security_hub     = false  # Reduce costs
    enable_config          = false  # Reduce costs
    enable_cloudtrail      = true   # Keep for debugging
    enable_xray            = false  # Reduce costs
    enable_container_insights = false # Reduce costs
  }

  # Cost Optimization - Aggressive for dev
  use_spot_instances = true
  spot_max_price     = "0.10"

  reserved_instance_config = {
    enable          = false  # No RIs for dev
    payment_option  = "NO_UPFRONT"
    offering_class  = "STANDARD"
    instance_count  = 0
  }

  # Additional tags for dev environment
  additional_tags = {
    AutoShutdown = "true"
    DeleteAfter  = "30-days"
    Purpose      = "development"
  }
}

# Development-specific resources
resource "aws_instance" "bastion" {
  count = var.enable_bastion ? 1 : 0

  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.nano"
  key_name              = var.bastion_key_name
  vpc_security_group_ids = [module.toolboxai.all_security_group_ids.bastion]
  subnet_id             = module.toolboxai.public_subnet_ids[0]

  user_data = base64encode(templatefile("${path.module}/templates/bastion-userdata.sh", {
    cluster_name = module.toolboxai.cluster_id
  }))

  tags = {
    Name        = "dev-bastion"
    Environment = "dev"
    AutoShutdown = "true"
  }
}

# Dev-specific CloudWatch dashboard
resource "aws_cloudwatch_dashboard" "dev_debugging" {
  dashboard_name = "dev-toolboxai-debugging"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "log"
        x      = 0
        y      = 0
        width  = 24
        height = 12

        properties = {
          query = "SOURCE '${module.toolboxai.application_log_group_name}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
          region = var.aws_region
          title = "Recent Application Logs"
          view = "table"
        }
      }
    ]
  })
}

# Data sources
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
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

output "bastion_ip" {
  description = "Bastion host public IP"
  value       = var.enable_bastion ? aws_instance.bastion[0].public_ip : null
}

output "dev_debugging_dashboard_url" {
  description = "Development debugging dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.dev_debugging.dashboard_name}"
}