# MCP (Model Context Protocol) Infrastructure Module

locals {
  mcp_prefix = "mcp-${var.environment}"
}

# DynamoDB Tables for MCP Context Storage
resource "aws_dynamodb_table" "mcp_tables" {
  for_each = var.dynamodb_tables

  name           = "${local.mcp_prefix}-${each.key}"
  billing_mode   = each.value.billing_mode
  read_capacity  = each.value.billing_mode == "PROVISIONED" ? each.value.read_capacity : null
  write_capacity = each.value.billing_mode == "PROVISIONED" ? each.value.write_capacity : null
  hash_key       = each.value.hash_key
  range_key      = lookup(each.value, "range_key", null)

  # Attributes
  dynamic "attribute" {
    for_each = concat(
      [{ name = each.value.hash_key, type = "S" }],
      lookup(each.value, "range_key", null) != null ? [{ name = each.value.range_key, type = "S" }] : [],
      lookup(each.value, "attributes", [])
    )
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  # Global Secondary Indexes
  dynamic "global_secondary_index" {
    for_each = lookup(each.value, "global_secondary_indexes", [])
    content {
      name               = global_secondary_index.value.name
      hash_key           = global_secondary_index.value.hash_key
      range_key          = lookup(global_secondary_index.value, "range_key", null)
      projection_type    = global_secondary_index.value.projection_type
      read_capacity      = each.value.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "read_capacity", 5) : null
      write_capacity     = each.value.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "write_capacity", 5) : null
      non_key_attributes = lookup(global_secondary_index.value, "non_key_attributes", null)
    }
  }

  # TTL Configuration
  dynamic "ttl" {
    for_each = lookup(each.value, "ttl", null) != null ? [each.value.ttl] : []
    content {
      enabled        = ttl.value.enabled
      attribute_name = ttl.value.attribute_name
    }
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.environment == "production"
  }

  # Server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.mcp.arn
  }

  # Stream specification for change data capture
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = merge(
    var.tags,
    {
      Name        = "${local.mcp_prefix}-${each.key}"
      Component   = "MCP"
      TableType   = each.key
    }
  )
}

# KMS Key for MCP Encryption
resource "aws_kms_key" "mcp" {
  description             = "KMS key for MCP data encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-kms"
      Component = "MCP"
    }
  )
}

resource "aws_kms_alias" "mcp" {
  name          = "alias/${local.mcp_prefix}"
  target_key_id = aws_kms_key.mcp.key_id
}

# S3 Buckets for MCP Artifacts and Archives
resource "aws_s3_bucket" "mcp_buckets" {
  for_each = var.s3_buckets

  bucket = "${local.mcp_prefix}-${each.key}"

  tags = merge(
    var.tags,
    {
      Name        = "${local.mcp_prefix}-${each.key}"
      Component   = "MCP"
      BucketType  = each.key
    }
  )
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "mcp_buckets" {
  for_each = { for k, v in var.s3_buckets : k => v if v.versioning }

  bucket = aws_s3_bucket.mcp_buckets[each.key].id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server-side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "mcp_buckets" {
  for_each = aws_s3_bucket.mcp_buckets

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.mcp.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# S3 Bucket Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "mcp_buckets" {
  for_each = { for k, v in var.s3_buckets : k => v if length(lookup(v, "lifecycle_rules", [])) > 0 }

  bucket = aws_s3_bucket.mcp_buckets[each.key].id

  dynamic "rule" {
    for_each = each.value.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      dynamic "transition" {
        for_each = lookup(rule.value, "transition", [])
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = lookup(rule.value, "expiration", null) != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "mcp_buckets" {
  for_each = { for k, v in var.s3_buckets : k => v if length(lookup(v, "cors_rules", [])) > 0 }

  bucket = aws_s3_bucket.mcp_buckets[each.key].id

  dynamic "cors_rule" {
    for_each = each.value.cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = lookup(cors_rule.value, "max_age_seconds", 3000)
    }
  }
}

# API Gateway for WebSocket connections
resource "aws_apigatewayv2_api" "mcp_websocket" {
  count = var.enable_websocket_api ? 1 : 0

  name                       = "${local.mcp_prefix}-websocket"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-websocket"
      Component = "MCP"
    }
  )
}

# WebSocket Routes
resource "aws_apigatewayv2_route" "mcp_routes" {
  for_each = var.enable_websocket_api ? toset(var.websocket_routes) : []

  api_id    = aws_apigatewayv2_api.mcp_websocket[0].id
  route_key = each.value

  target = "integrations/${aws_apigatewayv2_integration.mcp_lambda[each.value].id}"
}

# Lambda Integration for WebSocket
resource "aws_apigatewayv2_integration" "mcp_lambda" {
  for_each = var.enable_websocket_api ? toset(var.websocket_routes) : []

  api_id           = aws_apigatewayv2_api.mcp_websocket[0].id
  integration_type = "AWS_PROXY"

  connection_type           = "INTERNET"
  content_handling_strategy = "CONVERT_TO_TEXT"
  integration_method        = "POST"
  integration_uri           = aws_lambda_function.mcp_handlers[
    contains(["$connect", "$disconnect"], each.value) ? "connection_handler" : "message_handler"
  ].invoke_arn
}

# Lambda Functions for MCP Handlers
resource "aws_lambda_function" "mcp_handlers" {
  for_each = var.lambda_functions

  function_name = "${local.mcp_prefix}-${replace(each.key, "_", "-")}"
  role          = aws_iam_role.lambda_execution.arn

  runtime = each.value.runtime
  handler = each.value.handler
  timeout = each.value.timeout
  memory_size = each.value.memory

  filename         = "${path.module}/lambda/${each.key}.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda/${each.key}.zip")

  environment {
    variables = merge(
      each.value.environment_variables,
      {
        ENVIRONMENT = var.environment
        MCP_PREFIX  = local.mcp_prefix
      }
    )
  }

  vpc_config {
    subnet_ids         = var.lambda_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  reserved_concurrent_executions = var.environment == "production" ? 100 : 10

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-${each.key}"
      Component = "MCP"
      Type      = "Lambda"
    }
  )
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution" {
  name = "${local.mcp_prefix}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

# Lambda Execution Policy
resource "aws_iam_role_policy" "lambda_execution" {
  name = "${local.mcp_prefix}-lambda-execution-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.mcp_tables["contexts"].arn,
          aws_dynamodb_table.mcp_tables["agents"].arn,
          aws_dynamodb_table.mcp_tables["sessions"].arn,
          "${aws_dynamodb_table.mcp_tables["contexts"].arn}/index/*",
          "${aws_dynamodb_table.mcp_tables["agents"].arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          for bucket in aws_s3_bucket.mcp_buckets :
          "${bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = var.enable_websocket_api ? "${aws_apigatewayv2_api.mcp_websocket[0].execution_arn}/*" : "*"
      }
    ]
  })
}

# Lambda VPC Security Group
resource "aws_security_group" "lambda" {
  name_prefix = "${local.mcp_prefix}-lambda-sg"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${local.mcp_prefix}-lambda-sg"
    }
  )
}

# SQS Queues for Agent Communication
resource "aws_sqs_queue" "mcp_agent_queues" {
  for_each = toset(var.agent_types)

  name                      = "${local.mcp_prefix}-${each.value}-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 20       # Long polling

  visibility_timeout_seconds = var.agent_visibility_timeouts[each.value]

  kms_master_key_id = aws_kms_key.mcp.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.mcp_dlq[each.value].arn
    maxReceiveCount     = 3
  })

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-${each.value}-queue"
      Component = "MCP"
      AgentType = each.value
    }
  )
}

# Dead Letter Queues
resource "aws_sqs_queue" "mcp_dlq" {
  for_each = toset(var.agent_types)

  name                      = "${local.mcp_prefix}-${each.value}-dlq"
  message_retention_seconds = 1209600  # 14 days

  kms_master_key_id = aws_kms_key.mcp.id

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-${each.value}-dlq"
      Component = "MCP"
      Type      = "DLQ"
    }
  )
}

# SNS Topics for MCP Events
resource "aws_sns_topic" "mcp_events" {
  name = "${local.mcp_prefix}-events"

  kms_master_key_id = aws_kms_key.mcp.id

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-events"
      Component = "MCP"
    }
  )
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "mcp_logs" {
  for_each = toset(["api", "agents", "context", "telemetry"])

  name              = "/aws/mcp/${var.environment}/${each.value}"
  retention_in_days = var.log_retention_days

  kms_key_id = aws_kms_key.mcp.arn

  tags = merge(
    var.tags,
    {
      Name      = "${local.mcp_prefix}-logs-${each.value}"
      Component = "MCP"
      LogType   = each.value
    }
  )
}

# Outputs
output "dynamodb_table_names" {
  description = "Names of DynamoDB tables"
  value       = { for k, v in aws_dynamodb_table.mcp_tables : k => v.name }
}

output "dynamodb_table_arns" {
  description = "ARNs of DynamoDB tables"
  value       = { for k, v in aws_dynamodb_table.mcp_tables : k => v.arn }
}

output "s3_bucket_names" {
  description = "Names of S3 buckets"
  value       = { for k, v in aws_s3_bucket.mcp_buckets : k => v.id }
}

output "s3_bucket_arns" {
  description = "ARNs of S3 buckets"
  value       = { for k, v in aws_s3_bucket.mcp_buckets : k => v.arn }
}

output "websocket_url" {
  description = "WebSocket API URL"
  value       = var.enable_websocket_api ? aws_apigatewayv2_api.mcp_websocket[0].api_endpoint : null
}

output "sqs_queue_urls" {
  description = "SQS queue URLs"
  value       = { for k, v in aws_sqs_queue.mcp_agent_queues : k => v.id }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for MCP events"
  value       = aws_sns_topic.mcp_events.arn
}

output "kms_key_id" {
  description = "KMS key ID for MCP encryption"
  value       = aws_kms_key.mcp.id
}