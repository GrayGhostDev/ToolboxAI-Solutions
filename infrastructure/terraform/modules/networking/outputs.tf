# ToolBoxAI Solutions - Networking Module Outputs

# VPC
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = aws_vpc.main.arn
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "vpc_default_security_group_id" {
  description = "ID of the default security group"
  value       = aws_vpc.main.default_security_group_id
}

output "vpc_default_network_acl_id" {
  description = "ID of the default network ACL"
  value       = aws_vpc.main.default_network_acl_id
}

output "vpc_default_route_table_id" {
  description = "ID of the default route table"
  value       = aws_vpc.main.default_route_table_id
}

output "vpc_owner_id" {
  description = "ID of the AWS account that owns the VPC"
  value       = aws_vpc.main.owner_id
}

# Internet Gateway
output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "internet_gateway_arn" {
  description = "ARN of the Internet Gateway"
  value       = aws_internet_gateway.main.arn
}

# Public Subnets
output "public_subnet_ids" {
  description = "List of IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "public_subnet_arns" {
  description = "List of ARNs of the public subnets"
  value       = aws_subnet.public[*].arn
}

output "public_subnet_cidr_blocks" {
  description = "List of CIDR blocks of the public subnets"
  value       = aws_subnet.public[*].cidr_block
}

output "public_subnet_availability_zones" {
  description = "List of availability zones of the public subnets"
  value       = aws_subnet.public[*].availability_zone
}

# Private Subnets
output "private_subnet_ids" {
  description = "List of IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "private_subnet_arns" {
  description = "List of ARNs of the private subnets"
  value       = aws_subnet.private[*].arn
}

output "private_subnet_cidr_blocks" {
  description = "List of CIDR blocks of the private subnets"
  value       = aws_subnet.private[*].cidr_block
}

output "private_subnet_availability_zones" {
  description = "List of availability zones of the private subnets"
  value       = aws_subnet.private[*].availability_zone
}

# Database Subnets
output "database_subnet_ids" {
  description = "List of IDs of the database subnets"
  value       = aws_subnet.database[*].id
}

output "database_subnet_arns" {
  description = "List of ARNs of the database subnets"
  value       = aws_subnet.database[*].arn
}

output "database_subnet_cidr_blocks" {
  description = "List of CIDR blocks of the database subnets"
  value       = aws_subnet.database[*].cidr_block
}

output "database_subnet_availability_zones" {
  description = "List of availability zones of the database subnets"
  value       = aws_subnet.database[*].availability_zone
}

output "database_subnet_group_name" {
  description = "Name of the database subnet group"
  value       = try(aws_db_subnet_group.database[0].name, null)
}

# NAT Gateways
output "nat_gateway_ids" {
  description = "List of IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_allocation_ids" {
  description = "List of Allocation IDs of the Elastic IP address for the NAT Gateways"
  value       = aws_nat_gateway.main[*].allocation_id
}

output "nat_gateway_subnet_ids" {
  description = "List of Subnet IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].subnet_id
}

output "nat_gateway_network_interface_ids" {
  description = "List of ENI IDs of the network interface created by the NAT Gateways"
  value       = aws_nat_gateway.main[*].network_interface_id
}

output "nat_gateway_private_ips" {
  description = "List of private IP addresses of the NAT Gateways"
  value       = aws_nat_gateway.main[*].private_ip
}

output "nat_gateway_public_ips" {
  description = "List of public IP addresses of the NAT Gateways"
  value       = aws_nat_gateway.main[*].public_ip
}

# Elastic IPs
output "nat_eip_ids" {
  description = "List of IDs of the Elastic IP addresses for NAT Gateways"
  value       = aws_eip.nat[*].id
}

output "nat_eip_public_ips" {
  description = "List of public IP addresses of the Elastic IP addresses for NAT Gateways"
  value       = aws_eip.nat[*].public_ip
}

# Route Tables
output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of IDs of the private route tables"
  value       = aws_route_table.private[*].id
}

output "database_route_table_id" {
  description = "ID of the database route table"
  value       = aws_route_table.database.id
}

# VPC Endpoints
output "vpc_endpoint_s3_id" {
  description = "ID of VPC endpoint for S3"
  value       = try(aws_vpc_endpoint.s3[0].id, null)
}

output "vpc_endpoint_dynamodb_id" {
  description = "ID of VPC endpoint for DynamoDB"
  value       = try(aws_vpc_endpoint.dynamodb[0].id, null)
}

output "vpc_endpoint_ec2_id" {
  description = "ID of VPC endpoint for EC2"
  value       = try(aws_vpc_endpoint.ec2[0].id, null)
}

output "vpc_endpoint_ecr_api_id" {
  description = "ID of VPC endpoint for ECR API"
  value       = try(aws_vpc_endpoint.ecr_api[0].id, null)
}

output "vpc_endpoint_ecr_dkr_id" {
  description = "ID of VPC endpoint for ECR DKR"
  value       = try(aws_vpc_endpoint.ecr_dkr[0].id, null)
}

# VPC Flow Logs
output "vpc_flow_log_id" {
  description = "ID of the VPC Flow Log"
  value       = try(aws_flow_log.vpc[0].id, null)
}

output "vpc_flow_log_cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for VPC Flow Logs"
  value       = try(aws_cloudwatch_log_group.vpc_flow_log[0].name, null)
}

# Network ACLs
output "public_network_acl_id" {
  description = "ID of the public network ACL"
  value       = try(aws_network_acl.public[0].id, null)
}

output "private_network_acl_id" {
  description = "ID of the private network ACL"
  value       = try(aws_network_acl.private[0].id, null)
}

# DHCP Options
output "vpc_dhcp_options_id" {
  description = "ID of the DHCP options"
  value       = try(aws_vpc_dhcp_options.main[0].id, null)
}

# Security Group for VPC Endpoints
output "vpc_endpoint_security_group_id" {
  description = "ID of the security group for VPC endpoints"
  value       = try(aws_security_group.vpc_endpoint[0].id, null)
}

# Availability Zones
output "availability_zones" {
  description = "List of availability zones used"
  value       = var.availability_zones
}

# Summary information
output "vpc_summary" {
  description = "Summary of VPC configuration"
  value = {
    vpc_id                    = aws_vpc.main.id
    vpc_cidr                  = aws_vpc.main.cidr_block
    public_subnet_count       = length(aws_subnet.public)
    private_subnet_count      = length(aws_subnet.private)
    database_subnet_count     = length(aws_subnet.database)
    nat_gateway_count         = length(aws_nat_gateway.main)
    availability_zone_count   = min(length(var.availability_zones), var.max_azs)
    vpc_endpoints_enabled     = var.enable_vpc_endpoints
    flow_logs_enabled         = var.enable_flow_logs
    nat_gateway_enabled       = var.enable_nat_gateway
    single_nat_gateway        = var.single_nat_gateway
  }
}

# Cost optimization information
output "cost_optimization" {
  description = "Cost optimization features enabled"
  value = {
    single_nat_gateway        = var.single_nat_gateway
    nat_instances_used        = var.use_nat_instance
    vpc_endpoints_enabled     = var.enable_vpc_endpoints
    flow_logs_to_s3          = var.enable_flow_log_s3
  }
}