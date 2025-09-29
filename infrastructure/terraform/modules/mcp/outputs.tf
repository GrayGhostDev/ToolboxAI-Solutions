# ToolBoxAI Solutions - MCP Module Outputs

# DynamoDB Tables
output "dynamodb_table_names" {
  description = "Names of the DynamoDB tables"
  value       = { for name, table in aws_dynamodb_table.main : name => table.name }
}

output "dynamodb_table_arns" {
  description = "ARNs of the DynamoDB tables"
  value       = { for name, table in aws_dynamodb_table.main : name => table.arn }
}

output "contexts_table_name" {
  description = "Name of the contexts DynamoDB table"
  value       = aws_dynamodb_table.main["contexts"].name
}

output "contexts_table_arn" {
  description = "ARN of the contexts DynamoDB table"
  value       = aws_dynamodb_table.main["contexts"].arn
}

output "agents_table_name" {
  description = "Name of the agents DynamoDB table"
  value       = aws_dynamodb_table.main["agents"].name
}

output "agents_table_arn" {
  description = "ARN of the agents DynamoDB table"
  value       = aws_dynamodb_table.main["agents"].arn
}

output "sessions_table_name" {
  description = "Name of the sessions DynamoDB table"
  value       = aws_dynamodb_table.main["sessions"].name
}

output "sessions_table_arn" {
  description = "ARN of the sessions DynamoDB table"
  value       = aws_dynamodb_table.main["sessions"].arn
}

# S3 Buckets
output "s3_bucket_names" {
  description = "Names of the S3 buckets"
  value       = { for name, bucket in aws_s3_bucket.main : name => bucket.id }
}

output "s3_bucket_arns" {
  description = "ARNs of the S3 buckets"
  value       = { for name, bucket in aws_s3_bucket.main : name => bucket.arn }
}

output "context_archive_bucket_name" {
  description = "Name of the context archive S3 bucket"
  value       = aws_s3_bucket.main["context_archive"].id
}

output "context_archive_bucket_arn" {
  description = "ARN of the context archive S3 bucket"
  value       = aws_s3_bucket.main["context_archive"].arn
}

output "agent_artifacts_bucket_name" {
  description = "Name of the agent artifacts S3 bucket"
  value       = aws_s3_bucket.main["agent_artifacts"].id
}

output "agent_artifacts_bucket_arn" {
  description = "ARN of the agent artifacts S3 bucket"
  value       = aws_s3_bucket.main["agent_artifacts"].arn
}

# API Gateway
output "websocket_api_id" {
  description = "ID of the WebSocket API Gateway"
  value       = try(aws_apigatewayv2_api.websocket[0].id, null)
}

output "websocket_api_endpoint" {
  description = "WebSocket API Gateway endpoint"
  value       = try(aws_apigatewayv2_api.websocket[0].api_endpoint, null)
}

output "websocket_url" {
  description = "WebSocket connection URL"
  value       = try("${replace(aws_apigatewayv2_api.websocket[0].api_endpoint, "https://", "wss://")}/prod", null)
}

output "websocket_stage_name" {
  description = "Name of the WebSocket API stage"
  value       = try(aws_apigatewayv2_stage.websocket[0].name, null)
}

output "websocket_stage_arn" {
  description = "ARN of the WebSocket API stage"
  value       = try(aws_apigatewayv2_stage.websocket[0].arn, null)
}

# Lambda Functions
output "lambda_function_names" {
  description = "Names of the Lambda functions"
  value       = { for name, function in aws_lambda_function.main : name => function.function_name }
}

output "lambda_function_arns" {
  description = "ARNs of the Lambda functions"
  value       = { for name, function in aws_lambda_function.main : name => function.arn }
}

output "context_handler_function_name" {
  description = "Name of the context handler Lambda function"
  value       = aws_lambda_function.main["context_handler"].function_name
}

output "context_handler_function_arn" {
  description = "ARN of the context handler Lambda function"
  value       = aws_lambda_function.main["context_handler"].arn
}

output "agent_handler_function_name" {
  description = "Name of the agent handler Lambda function"
  value       = aws_lambda_function.main["agent_handler"].function_name
}

output "agent_handler_function_arn" {
  description = "ARN of the agent handler Lambda function"
  value       = aws_lambda_function.main["agent_handler"].arn
}

# SQS Queues
output "sqs_queue_names" {
  description = "Names of the SQS queues"
  value       = { for name, queue in aws_sqs_queue.main : name => queue.name }
}

output "sqs_queue_arns" {
  description = "ARNs of the SQS queues"
  value       = { for name, queue in aws_sqs_queue.main : name => queue.arn }
}

output "sqs_queue_urls" {
  description = "URLs of the SQS queues"
  value       = { for name, queue in aws_sqs_queue.main : name => queue.url }
}

output "agent_queue_url" {
  description = "URL of the agent processing queue"
  value       = aws_sqs_queue.main["agent_queue"].url
}

output "context_queue_url" {
  description = "URL of the context processing queue"
  value       = aws_sqs_queue.main["context_queue"].url
}

output "dlq_queue_url" {
  description = "URL of the dead letter queue"
  value       = aws_sqs_queue.main["dlq"].url
}

# SNS Topics
output "sns_topic_arns" {
  description = "ARNs of the SNS topics"
  value       = { for name, topic in aws_sns_topic.main : name => topic.arn }
}

output "mcp_events_topic_arn" {
  description = "ARN of the MCP events SNS topic"
  value       = aws_sns_topic.main["mcp_events"].arn
}

output "agent_notifications_topic_arn" {
  description = "ARN of the agent notifications SNS topic"
  value       = aws_sns_topic.main["agent_notifications"].arn
}

# IAM Roles
output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.name
}

output "api_gateway_role_arn" {
  description = "ARN of the API Gateway execution role"
  value       = try(aws_iam_role.api_gateway[0].arn, null)
}

output "api_gateway_role_name" {
  description = "Name of the API Gateway execution role"
  value       = try(aws_iam_role.api_gateway[0].name, null)
}

# CloudWatch Log Groups
output "lambda_log_group_names" {
  description = "Names of the Lambda CloudWatch log groups"
  value       = { for name, lg in aws_cloudwatch_log_group.lambda : name => lg.name }
}

output "lambda_log_group_arns" {
  description = "ARNs of the Lambda CloudWatch log groups"
  value       = { for name, lg in aws_cloudwatch_log_group.lambda : name => lg.arn }
}

output "api_gateway_log_group_name" {
  description = "Name of the API Gateway CloudWatch log group"
  value       = try(aws_cloudwatch_log_group.api_gateway[0].name, null)
}

output "api_gateway_log_group_arn" {
  description = "ARN of the API Gateway CloudWatch log group"
  value       = try(aws_cloudwatch_log_group.api_gateway[0].arn, null)
}

# ElastiCache Redis Cluster
output "redis_cluster_id" {
  description = "ID of the Redis cluster"
  value       = try(aws_elasticache_replication_group.redis[0].id, null)
}

output "redis_cluster_endpoint" {
  description = "Redis cluster endpoint"
  value       = try(aws_elasticache_replication_group.redis[0].configuration_endpoint_address, null)
}

output "redis_cluster_port" {
  description = "Redis cluster port"
  value       = try(aws_elasticache_replication_group.redis[0].port, null)
}

output "redis_cluster_arn" {
  description = "ARN of the Redis cluster"
  value       = try(aws_elasticache_replication_group.redis[0].arn, null)
}

# Security Groups
output "mcp_security_group_id" {
  description = "ID of the MCP security group"
  value       = try(aws_security_group.mcp[0].id, null)
}

output "mcp_security_group_arn" {
  description = "ARN of the MCP security group"
  value       = try(aws_security_group.mcp[0].arn, null)
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = try(aws_security_group.redis[0].id, null)
}

output "redis_security_group_arn" {
  description = "ARN of the Redis security group"
  value       = try(aws_security_group.redis[0].arn, null)
}

# VPC Endpoints
output "dynamodb_vpc_endpoint_id" {
  description = "ID of the DynamoDB VPC endpoint"
  value       = try(aws_vpc_endpoint.dynamodb[0].id, null)
}

output "s3_vpc_endpoint_id" {
  description = "ID of the S3 VPC endpoint"
  value       = try(aws_vpc_endpoint.s3[0].id, null)
}

# Event Bridge Rules
output "event_rules" {
  description = "Map of EventBridge rule ARNs"
  value       = { for name, rule in aws_cloudwatch_event_rule.main : name => rule.arn }
}

# All Resources Summary
output "mcp_summary" {
  description = "Summary of all MCP resources"
  value = {
    environment = var.environment
    dynamodb_tables = {
      count = length(aws_dynamodb_table.main)
      names = [for table in aws_dynamodb_table.main : table.name]
    }
    s3_buckets = {
      count = length(aws_s3_bucket.main)
      names = [for bucket in aws_s3_bucket.main : bucket.id]
    }
    lambda_functions = {
      count = length(aws_lambda_function.main)
      names = [for function in aws_lambda_function.main : function.function_name]
    }
    sqs_queues = {
      count = length(aws_sqs_queue.main)
      names = [for queue in aws_sqs_queue.main : queue.name]
    }
    sns_topics = {
      count = length(aws_sns_topic.main)
      names = [for topic in aws_sns_topic.main : topic.name]
    }
    websocket_api_enabled = var.enable_websocket_api
    redis_enabled = var.enable_redis
    vpc_endpoints_enabled = var.enable_vpc_endpoints
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization information for MCP infrastructure"
  value = {
    dynamodb_billing_mode = {
      for name, config in var.dynamodb_tables : name => lookup(config, "billing_mode", "PAY_PER_REQUEST")
    }
    lambda_memory_optimized = {
      for name, config in var.lambda_functions : name => lookup(config, "memory", 512) <= 1024
    }
    s3_lifecycle_enabled = {
      for name, config in var.s3_buckets : name => length(lookup(config, "lifecycle_rules", [])) > 0
    }
    redis_node_type = try(var.redis_config.node_type, "cache.t3.micro")
    estimated_monthly_cost = {
      dynamodb = "Based on read/write capacity and storage"
      lambda = "Based on invocations and duration"
      s3 = "Based on storage and requests"
      api_gateway = "Based on API calls"
      redis = var.enable_redis ? "Based on node type and hours" : "Disabled"
      sqs = "Based on requests (first 1M requests free)"
      sns = "Based on notifications"
    }
  }
}

# Security Configuration
output "security_configuration" {
  description = "Security configuration summary"
  value = {
    encryption_at_rest = {
      dynamodb = true
      s3 = true
      lambda = true
      sqs = true
      sns = true
      redis = var.enable_redis
    }
    encryption_in_transit = {
      api_gateway = true
      lambda = true
      redis = var.enable_redis
    }
    vpc_endpoints_enabled = var.enable_vpc_endpoints
    security_groups_configured = var.vpc_id != null
    iam_roles_least_privilege = true
    cloudwatch_logging_enabled = true
  }
}

# Integration Points
output "integration_endpoints" {
  description = "Integration endpoints for MCP services"
  value = {
    websocket_url = try("${replace(aws_apigatewayv2_api.websocket[0].api_endpoint, "https://", "wss://")}/prod", null)
    rest_api_url = try("${aws_apigatewayv2_api.websocket[0].api_endpoint}/prod", null)
    agent_queue_url = aws_sqs_queue.main["agent_queue"].url
    context_queue_url = aws_sqs_queue.main["context_queue"].url
    events_topic_arn = aws_sns_topic.main["mcp_events"].arn
    redis_endpoint = try(aws_elasticache_replication_group.redis[0].configuration_endpoint_address, null)
  }
}

# Monitoring Resources
output "monitoring_resources" {
  description = "Monitoring and observability resources"
  value = {
    cloudwatch_log_groups = [for lg in aws_cloudwatch_log_group.lambda : lg.name]
    lambda_function_names = [for function in aws_lambda_function.main : function.function_name]
    dynamodb_table_names = [for table in aws_dynamodb_table.main : table.name]
    api_gateway_stage = try(aws_apigatewayv2_stage.websocket[0].name, null)
    redis_cluster_id = try(aws_elasticache_replication_group.redis[0].id, null)
  }
}