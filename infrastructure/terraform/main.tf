# ToolBoxAI Solutions - Main Terraform Configuration
# This is the root module that orchestrates all infrastructure components

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Remote state configuration
  backend "s3" {
    bucket         = "toolboxai-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "toolboxai-terraform-locks"
  }
}

# Provider configurations
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "ToolBoxAI-Solutions"
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
      Owner       = var.owner_email
    }
  }
}

provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "ToolBoxAI-Solutions"
      ManagedBy   = "Terraform"
      CostCenter  = var.cost_center
      Owner       = var.owner_email
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Networking Module
module "networking" {
  source = "./modules/networking"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names

  # Subnet configuration
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs

  # NAT Gateway configuration
  enable_nat_gateway = var.environment != "dev"
  single_nat_gateway = var.environment == "staging"

  # VPC Flow Logs
  enable_flow_logs = true

  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"

  environment = var.environment
  vpc_id      = module.networking.vpc_id

  # Security group configurations
  allowed_ssh_ips = var.allowed_ssh_ips
  allowed_http_ips = ["0.0.0.0/0"]

  # KMS key for encryption
  enable_kms_key = true

  tags = local.common_tags
}

# EKS Cluster Module
module "eks" {
  source = "./modules/eks"

  environment = var.environment
  cluster_name = "${var.project_name}-${var.environment}"
  cluster_version = "1.28"

  # Networking
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids

  # Node groups configuration
  node_groups = {
    general = {
      desired_capacity = var.environment == "production" ? 5 : 2
      min_capacity     = var.environment == "production" ? 3 : 1
      max_capacity     = var.environment == "production" ? 10 : 4
      instance_types   = ["t3.large"]

      labels = {
        Environment = var.environment
        Type        = "general"
      }
    }

    mcp = {
      desired_capacity = var.environment == "production" ? 3 : 1
      min_capacity     = var.environment == "production" ? 2 : 1
      max_capacity     = var.environment == "production" ? 5 : 2
      instance_types   = ["r5.xlarge"]  # Memory optimized for MCP

      labels = {
        Environment = var.environment
        Type        = "mcp"
        Workload    = "memory-intensive"
      }

      taints = [{
        key    = "workload"
        value  = "mcp"
        effect = "NoSchedule"
      }]
    }

    gpu = {
      desired_capacity = var.environment == "production" ? 2 : 0
      min_capacity     = 0
      max_capacity     = var.environment == "production" ? 4 : 1
      instance_types   = ["g4dn.xlarge"]  # GPU for AI workloads

      labels = {
        Environment = var.environment
        Type        = "gpu"
        Workload    = "ai"
      }

      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NoSchedule"
      }]
    }
  }

  # Add-ons
  enable_cluster_autoscaler = true
  enable_metrics_server    = true
  enable_aws_load_balancer_controller = true
  enable_external_dns = true
  enable_cert_manager = true

  tags = local.common_tags
}

# RDS Module (Aurora PostgreSQL)
module "rds" {
  source = "./modules/rds"

  environment = var.environment

  # Aurora configuration
  engine         = "aurora-postgresql"
  engine_version = "15.4"

  # Instance configuration
  instance_class = var.environment == "production" ? "db.r6g.xlarge" : "db.t3.medium"
  instances = var.environment == "production" ? 2 : 1

  # Database configuration
  database_name = "toolboxai"
  master_username = "toolboxai_admin"

  # Networking
  vpc_id = module.networking.vpc_id
  subnet_ids = module.networking.database_subnet_ids
  allowed_security_groups = [module.eks.cluster_security_group_id]

  # Backup configuration
  backup_retention_period = var.environment == "production" ? 30 : 7
  preferred_backup_window = "03:00-04:00"

  # Serverless v2 scaling
  enable_serverless = var.environment == "production"
  min_capacity = 0.5
  max_capacity = var.environment == "production" ? 4 : 1

  tags = local.common_tags
}

# MCP Infrastructure Module
module "mcp" {
  source = "./modules/mcp"

  environment = var.environment
  vpc_id      = module.networking.vpc_id

  # DynamoDB tables for MCP
  dynamodb_tables = {
    contexts = {
      billing_mode = "PAY_PER_REQUEST"
      hash_key     = "context_id"
      range_key    = "timestamp"

      global_secondary_indexes = [{
        name            = "agent-index"
        hash_key        = "agent_id"
        range_key       = "timestamp"
        projection_type = "ALL"
      }]

      ttl = {
        enabled        = true
        attribute_name = "expiry"
      }
    }

    agents = {
      billing_mode = "PROVISIONED"
      read_capacity  = 5
      write_capacity = 5
      hash_key       = "agent_id"

      attributes = [
        { name = "agent_id", type = "S" },
        { name = "capability", type = "S" }
      ]

      global_secondary_indexes = [{
        name            = "capability-index"
        hash_key        = "capability"
        projection_type = "ALL"
        read_capacity   = 5
        write_capacity  = 5
      }]
    }

    sessions = {
      billing_mode = "PAY_PER_REQUEST"
      hash_key     = "session_id"

      ttl = {
        enabled        = true
        attribute_name = "expiry"
      }
    }
  }

  # S3 buckets for MCP
  s3_buckets = {
    context_archive = {
      versioning = true
      lifecycle_rules = [{
        id      = "archive-old-contexts"
        enabled = true

        transition = [{
          days          = 30
          storage_class = "INTELLIGENT_TIERING"
        }]

        transition = [{
          days          = 90
          storage_class = "GLACIER"
        }]

        expiration = {
          days = 365
        }
      }]
    }

    agent_artifacts = {
      versioning = true
      cors_rules = [{
        allowed_headers = ["*"]
        allowed_methods = ["GET", "PUT", "POST"]
        allowed_origins = ["https://*.toolboxai.solutions"]
        expose_headers  = ["ETag"]
      }]
    }
  }

  # API Gateway for WebSocket
  enable_websocket_api = true
  websocket_routes = ["$connect", "$disconnect", "$default", "context", "agent", "telemetry"]

  # Lambda functions for MCP handlers
  lambda_functions = {
    context_handler = {
      runtime = "python3.11"
      handler = "handler.main"
      memory  = 512
      timeout = 30

      environment_variables = {
        DYNAMODB_TABLE = "mcp-contexts"
        S3_BUCKET      = "mcp-context-archive"
      }
    }

    agent_handler = {
      runtime = "python3.11"
      handler = "handler.main"
      memory  = 1024
      timeout = 60

      environment_variables = {
        DYNAMODB_TABLE = "mcp-agents"
        SQS_QUEUE_URL  = "https://sqs.us-east-1.amazonaws.com/${data.aws_caller_identity.current.account_id}/mcp-agent-queue"
      }
    }
  }

  tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  environment = var.environment

  # CloudWatch configuration
  log_retention_days = var.environment == "production" ? 90 : 30

  # Alarms configuration
  enable_alarms = true
  sns_topic_email = var.alert_email

  # Metrics to monitor
  monitored_resources = {
    eks_cluster = module.eks.cluster_id
    rds_cluster = module.rds.cluster_id
    mcp_tables  = module.mcp.dynamodb_table_names
  }

  # X-Ray configuration
  enable_xray = var.environment == "production"

  tags = local.common_tags
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "rds_endpoint" {
  description = "RDS cluster endpoint"
  value       = module.rds.cluster_endpoint
  sensitive   = true
}

output "mcp_websocket_url" {
  description = "MCP WebSocket API URL"
  value       = module.mcp.websocket_url
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = module.eks.load_balancer_dns
}

# Local variables
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    CostCenter  = var.cost_center
    Owner       = var.owner_email
    CreatedAt   = timestamp()
  }
}