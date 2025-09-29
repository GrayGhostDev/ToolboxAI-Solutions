# ToolBoxAI Solutions - EKS Module Outputs

# Cluster Information
output "cluster_id" {
  description = "The ID of the EKS cluster"
  value       = aws_eks_cluster.main.id
}

output "cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the cluster"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.main.endpoint
  sensitive   = true
}

output "cluster_version" {
  description = "The Kubernetes version of the cluster"
  value       = aws_eks_cluster.main.version
}

output "cluster_platform_version" {
  description = "Platform version for the EKS cluster"
  value       = aws_eks_cluster.main.platform_version
}

output "cluster_status" {
  description = "Status of the EKS cluster"
  value       = aws_eks_cluster.main.status
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.main.cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = aws_iam_role.cluster.name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = aws_iam_role.cluster.arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "cluster_primary_security_group_id" {
  description = "The cluster primary security group ID created by EKS"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

# OIDC Provider
output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = try(aws_iam_openid_connect_provider.eks[0].arn, null)
}

# Node Groups
output "node_groups" {
  description = "Map of attribute maps for all EKS node groups created"
  value       = aws_eks_node_group.main
}

output "node_group_arns" {
  description = "List of the EKS node group ARNs"
  value       = [for ng in aws_eks_node_group.main : ng.arn]
}

output "node_group_statuses" {
  description = "Status of the EKS node groups"
  value       = { for name, ng in aws_eks_node_group.main : name => ng.status }
}

output "node_group_remote_access_security_group_id" {
  description = "The remote access security group ID for node groups"
  value       = try(aws_security_group.node_group_remote_access[0].id, null)
}

# Fargate Profiles
output "fargate_profiles" {
  description = "Map of attribute maps for all EKS Fargate profiles created"
  value       = aws_eks_fargate_profile.main
}

output "fargate_profile_arns" {
  description = "List of the EKS Fargate profile ARNs"
  value       = [for fp in aws_eks_fargate_profile.main : fp.arn]
}

output "fargate_profile_statuses" {
  description = "Status of the EKS Fargate profiles"
  value       = { for name, fp in aws_eks_fargate_profile.main : name => fp.status }
}

# Add-ons
output "cluster_addons" {
  description = "Map of attribute maps for all EKS cluster addons enabled"
  value       = aws_eks_addon.main
}

output "addon_statuses" {
  description = "Status of EKS cluster addons"
  value       = { for name, addon in aws_eks_addon.main : name => addon.status }
}

# Load Balancer
output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = try(data.aws_lb.main[0].dns_name, null)
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = try(data.aws_lb.main[0].arn, null)
}

output "load_balancer_zone_id" {
  description = "The canonical hosted zone ID of the load balancer"
  value       = try(data.aws_lb.main[0].zone_id, null)
}

# CloudWatch Log Group
output "cloudwatch_log_group_name" {
  description = "Name of cloudwatch log group created"
  value       = try(aws_cloudwatch_log_group.main[0].name, null)
}

output "cloudwatch_log_group_arn" {
  description = "ARN of cloudwatch log group created"
  value       = try(aws_cloudwatch_log_group.main[0].arn, null)
}

# IAM Roles
output "node_group_iam_role_name" {
  description = "IAM role name for EKS node groups"
  value       = aws_iam_role.node_group.name
}

output "node_group_iam_role_arn" {
  description = "IAM role ARN for EKS node groups"
  value       = aws_iam_role.node_group.arn
}

output "fargate_profile_iam_role_name" {
  description = "IAM role name for EKS Fargate profiles"
  value       = try(aws_iam_role.fargate_profile[0].name, null)
}

output "fargate_profile_iam_role_arn" {
  description = "IAM role ARN for EKS Fargate profiles"
  value       = try(aws_iam_role.fargate_profile[0].arn, null)
}

# Security Groups
output "cluster_additional_security_group_ids" {
  description = "List of additional security group IDs attached to the cluster"
  value       = var.cluster_additional_security_group_ids
}

output "node_security_group_id" {
  description = "ID of the node shared security group"
  value       = try(aws_security_group.node_group[0].id, null)
}

output "node_security_group_arn" {
  description = "ARN of the node shared security group"
  value       = try(aws_security_group.node_group[0].arn, null)
}

# Auto Scaling Groups
output "node_group_asg_names" {
  description = "List of the autoscaling group names"
  value       = [for ng in aws_eks_node_group.main : ng.resources[0].autoscaling_groups[0].name]
}

output "node_group_remote_access_ec2_ssh_key" {
  description = "EC2 Key Pair name for remote access to node groups"
  value       = var.node_group_remote_access_ec2_ssh_key
}

# Networking
output "cluster_vpc_config" {
  description = "VPC configuration of the cluster"
  value       = aws_eks_cluster.main.vpc_config
}

output "cluster_endpoint_private_access" {
  description = "Whether the Amazon EKS private API server endpoint is enabled"
  value       = aws_eks_cluster.main.vpc_config[0].endpoint_private_access
}

output "cluster_endpoint_public_access" {
  description = "Whether the Amazon EKS public API server endpoint is enabled"
  value       = aws_eks_cluster.main.vpc_config[0].endpoint_public_access
}

output "cluster_endpoint_public_access_cidrs" {
  description = "List of CIDR blocks that can access the Amazon EKS public API server endpoint"
  value       = aws_eks_cluster.main.vpc_config[0].public_access_cidrs
}

# Encryption
output "cluster_encryption_config" {
  description = "Encryption configuration for the cluster"
  value       = aws_eks_cluster.main.encryption_config
}

# Tags
output "cluster_tags" {
  description = "A map of tags assigned to the resource"
  value       = aws_eks_cluster.main.tags_all
}

# Summary Information
output "cluster_summary" {
  description = "Summary information about the EKS cluster"
  value = {
    cluster_name    = aws_eks_cluster.main.name
    cluster_version = aws_eks_cluster.main.version
    cluster_endpoint = aws_eks_cluster.main.endpoint
    cluster_status  = aws_eks_cluster.main.status
    node_groups_count = length(aws_eks_node_group.main)
    fargate_profiles_count = length(aws_eks_fargate_profile.main)
    addons_count = length(aws_eks_addon.main)
    private_access_enabled = aws_eks_cluster.main.vpc_config[0].endpoint_private_access
    public_access_enabled = aws_eks_cluster.main.vpc_config[0].endpoint_public_access
    logging_enabled = length(aws_eks_cluster.main.enabled_cluster_log_types) > 0
    encryption_enabled = length(aws_eks_cluster.main.encryption_config) > 0
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization information for the EKS cluster"
  value = {
    fargate_enabled = length(aws_eks_fargate_profile.main) > 0
    spot_instances_configured = anytrue([for ng_key, ng_config in var.node_groups : contains(ng_config.capacity_type, "SPOT")])
    cluster_autoscaler_enabled = var.enable_cluster_autoscaler
    managed_node_groups = length(aws_eks_node_group.main)
    estimated_monthly_cost = {
      control_plane = "$0.10 per hour"
      data_transfer = "Based on usage"
      load_balancer = var.enable_aws_load_balancer_controller ? "~$16-25 per month" : "Not enabled"
      node_groups = "Based on EC2 instance pricing"
    }
  }
}

# Security Information
output "security_summary" {
  description = "Security configuration summary"
  value = {
    private_endpoint_enabled = aws_eks_cluster.main.vpc_config[0].endpoint_private_access
    public_endpoint_enabled = aws_eks_cluster.main.vpc_config[0].endpoint_public_access
    public_access_cidrs = aws_eks_cluster.main.vpc_config[0].public_access_cidrs
    encryption_at_rest_enabled = length(aws_eks_cluster.main.encryption_config) > 0
    logging_enabled = length(aws_eks_cluster.main.enabled_cluster_log_types) > 0
    oidc_provider_configured = var.enable_oidc_provider
    rbac_enabled = true
    network_policies_supported = true
  }
}