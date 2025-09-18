# AWS Lambda Module for ToolBoxAI Solutions
# Serverless compute for content generation and processing

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

locals {
  function_name = "${var.project_name}-${var.environment}-${var.function_name}"

  # Runtime configuration based on language
  runtime_config = {
    python = {
      runtime = var.python_runtime
      handler = "handler.main"
    }
    nodejs = {
      runtime = var.nodejs_runtime
      handler = "index.handler"
    }
  }

  # Compliance-based environment variables
  compliance_env_vars = merge(
    var.coppa_compliance ? {
      COPPA_ENABLED = "true"
      MIN_USER_AGE  = "13"
    } : {},
    var.ferpa_compliance ? {
      FERPA_ENABLED = "true"
      EDUCATIONAL_RECORDS_PROTECTION = "true"
    } : {},
    var.gdpr_compliance ? {
      GDPR_ENABLED = "true"
      DATA_RETENTION_DAYS = "2555"
      RIGHT_TO_ERASURE = "true"
    } : {}
  )
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda" {
  name = "${local.function_name}-role"

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

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.function_name}-role"
      Environment = var.environment
    }
  )
}

# Basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC execution policy (if VPC is configured)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count = length(var.subnet_ids) > 0 ? 1 : 0

  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# X-Ray tracing policy
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count = var.tracing_mode != "PassThrough" ? 1 : 0

  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Custom policies for Lambda
resource "aws_iam_role_policy" "lambda_custom" {
  name = "${local.function_name}-custom-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      # KMS permissions
      var.kms_key_arn != "" ? [{
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = var.kms_key_arn
      }] : [],

      # Secrets Manager permissions
      length(var.secrets_manager_arns) > 0 ? [{
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = var.secrets_manager_arns
      }] : [],

      # S3 permissions
      length(var.s3_bucket_arns) > 0 ? [{
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          var.s3_bucket_arns,
          [for arn in var.s3_bucket_arns : "${arn}/*"]
        )
      }] : [],

      # DynamoDB permissions
      length(var.dynamodb_table_arns) > 0 ? [{
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = var.dynamodb_table_arns
      }] : [],

      # SQS permissions
      length(var.sqs_queue_arns) > 0 ? [{
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.sqs_queue_arns
      }] : [],

      # Additional custom statements
      var.additional_policy_statements
    )
  })
}

# Security Group for Lambda (if VPC is configured)
resource "aws_security_group" "lambda" {
  count = length(var.subnet_ids) > 0 ? 1 : 0

  name_prefix = "${local.function_name}-sg-"
  description = "Security group for ${local.function_name}"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.function_name}-sg"
      Environment = var.environment
    }
  )
}

# Lambda Layer (for shared dependencies)
resource "aws_lambda_layer_version" "dependencies" {
  count = var.create_layer ? 1 : 0

  filename            = var.layer_filename
  layer_name          = "${local.function_name}-layer"
  compatible_runtimes = [local.runtime_config[var.runtime_type].runtime]
  description         = "Dependencies layer for ${local.function_name}"

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda Function
resource "aws_lambda_function" "main" {
  function_name = local.function_name
  role          = aws_iam_role.lambda.arn

  # Code configuration
  filename         = var.filename
  source_code_hash = var.source_code_hash
  handler          = var.handler != "" ? var.handler : local.runtime_config[var.runtime_type].handler
  runtime          = local.runtime_config[var.runtime_type].runtime

  # Resource configuration
  memory_size                    = var.memory_size
  timeout                        = var.timeout
  reserved_concurrent_executions = var.reserved_concurrent_executions
  ephemeral_storage {
    size = var.ephemeral_storage_size
  }

  # Environment variables
  environment {
    variables = merge(
      {
        ENVIRONMENT    = var.environment
        PROJECT_NAME   = var.project_name
        FUNCTION_NAME  = var.function_name
        AWS_ACCOUNT_ID = data.aws_caller_identity.current.account_id
      },
      local.compliance_env_vars,
      var.environment_variables
    )
  }

  # VPC configuration
  dynamic "vpc_config" {
    for_each = length(var.subnet_ids) > 0 ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = concat([aws_security_group.lambda[0].id], var.additional_security_group_ids)
    }
  }

  # KMS encryption
  kms_key_arn = var.kms_key_arn

  # Tracing
  tracing_config {
    mode = var.tracing_mode
  }

  # Dead letter queue
  dynamic "dead_letter_config" {
    for_each = var.dead_letter_queue_arn != "" ? [1] : []
    content {
      target_arn = var.dead_letter_queue_arn
    }
  }

  # Layers
  layers = concat(
    var.create_layer ? [aws_lambda_layer_version.dependencies[0].arn] : [],
    var.additional_layers
  )

  # Architecture
  architectures = [var.architecture]

  # Logging
  logging_config {
    log_format = var.log_format
    log_group  = aws_cloudwatch_log_group.lambda.name
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda
  ]

  tags = merge(
    var.common_tags,
    {
      Name        = local.function_name
      Environment = var.environment
      Runtime     = local.runtime_config[var.runtime_type].runtime
      Compliance  = join(",", compact([
        var.coppa_compliance ? "COPPA" : "",
        var.ferpa_compliance ? "FERPA" : "",
        var.gdpr_compliance ? "GDPR" : ""
      ]))
    }
  )
}

# Lambda Alias for versioning
resource "aws_lambda_alias" "main" {
  name             = var.environment
  description      = "Alias for ${var.environment} environment"
  function_name    = aws_lambda_function.main.function_name
  function_version = var.publish ? aws_lambda_function.main.version : "$LATEST"

  dynamic "routing_config" {
    for_each = var.canary_deployment_percentage > 0 ? [1] : []
    content {
      additional_version_weights = {
        "$LATEST" = var.canary_deployment_percentage / 100
      }
    }
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.function_name}-logs"
      Environment = var.environment
    }
  )
}

# Lambda Function URL (for HTTP endpoints)
resource "aws_lambda_function_url" "main" {
  count = var.create_function_url ? 1 : 0

  function_name      = aws_lambda_function.main.function_name
  authorization_type = var.function_url_auth_type

  cors {
    allow_origins     = var.cors_allow_origins
    allow_methods     = var.cors_allow_methods
    allow_headers     = var.cors_allow_headers
    expose_headers    = var.cors_expose_headers
    max_age           = var.cors_max_age
    allow_credentials = var.cors_allow_credentials
  }
}

# Async Configuration
resource "aws_lambda_function_event_invoke_config" "main" {
  function_name                = aws_lambda_function.main.function_name
  maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
  maximum_retry_attempts       = var.maximum_retry_attempts

  dynamic "destination_config" {
    for_each = var.on_success_destination_arn != "" || var.on_failure_destination_arn != "" ? [1] : []
    content {
      dynamic "on_success" {
        for_each = var.on_success_destination_arn != "" ? [1] : []
        content {
          destination = var.on_success_destination_arn
        }
      }
      dynamic "on_failure" {
        for_each = var.on_failure_destination_arn != "" ? [1] : []
        content {
          destination = var.on_failure_destination_arn
        }
      }
    }
  }
}

# API Gateway Integration (REST API)
resource "aws_lambda_permission" "api_gateway" {
  count = var.api_gateway_execution_arn != "" ? 1 : 0

  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

# EventBridge Rule Integration
resource "aws_lambda_permission" "eventbridge" {
  for_each = var.eventbridge_rules

  statement_id  = "AllowExecutionFromEventBridge-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"
  source_arn    = each.value
}

# S3 Trigger
resource "aws_lambda_permission" "s3" {
  for_each = var.s3_triggers

  statement_id  = "AllowExecutionFromS3-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = each.value
}

# SQS Trigger
resource "aws_lambda_event_source_mapping" "sqs" {
  for_each = var.sqs_triggers

  event_source_arn = each.value.queue_arn
  function_name    = aws_lambda_function.main.arn

  batch_size                         = each.value.batch_size
  maximum_batching_window_in_seconds = each.value.batching_window

  scaling_config {
    maximum_concurrency = each.value.maximum_concurrency
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_rate_threshold
  alarm_description   = "Lambda function error rate"
  alarm_actions       = var.sns_topic_arns

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.function_name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.throttle_threshold
  alarm_description   = "Lambda function throttles"
  alarm_actions       = var.sns_topic_arns

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = var.duration_threshold
  alarm_description   = "Lambda function duration"
  alarm_actions       = var.sns_topic_arns

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }

  tags = var.common_tags
}

# Data sources
data "aws_caller_identity" "current" {}

# Outputs
output "function_name" {
  value = aws_lambda_function.main.function_name
}

output "function_arn" {
  value = aws_lambda_function.main.arn
}

output "invoke_arn" {
  value = aws_lambda_function.main.invoke_arn
}

output "function_url" {
  value = var.create_function_url ? aws_lambda_function_url.main[0].function_url : null
}

output "role_arn" {
  value = aws_iam_role.lambda.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}