# ToolBoxAI Solutions - Monitoring Module
# Creates CloudWatch dashboards, alarms, log groups, and monitoring infrastructure

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

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name              = "${var.environment}-alerts"
  kms_master_key_id = var.kms_key_id

  tags = merge(var.tags, {
    Name = "${var.environment}-alerts-topic"
    Type = "monitoring"
  })
}

resource "aws_sns_topic_subscription" "email" {
  count = var.sns_topic_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.sns_topic_email
}

# Slack Webhook Integration (optional)
resource "aws_sns_topic_subscription" "slack" {
  count = var.slack_webhook_url != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier[0].arn
}

# Lambda function for Slack notifications
resource "aws_lambda_function" "slack_notifier" {
  count = var.slack_webhook_url != "" ? 1 : 0

  filename         = data.archive_file.slack_notifier[0].output_path
  function_name    = "${var.environment}-slack-notifier"
  role            = aws_iam_role.slack_notifier[0].arn
  handler         = "index.lambda_handler"
  runtime         = "python3.11"
  timeout         = 10

  environment {
    variables = {
      SLACK_WEBHOOK_URL = var.slack_webhook_url
      ENVIRONMENT      = var.environment
    }
  }

  tags = var.tags
}

# Lambda function code for Slack notifications
data "archive_file" "slack_notifier" {
  count = var.slack_webhook_url != "" ? 1 : 0

  type        = "zip"
  output_path = "/tmp/slack_notifier.zip"
  source {
    content = file("${path.module}/files/slack_notifier.py")
    filename = "index.py"
  }
}

# IAM role for Slack notifier Lambda
resource "aws_iam_role" "slack_notifier" {
  count = var.slack_webhook_url != "" ? 1 : 0

  name = "${var.environment}-slack-notifier-role"

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

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "slack_notifier_basic" {
  count = var.slack_webhook_url != "" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.slack_notifier[0].name
}

# Lambda permission for SNS
resource "aws_lambda_permission" "sns_invoke_slack_notifier" {
  count = var.slack_webhook_url != "" ? 1 : 0

  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_notifier[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alerts.arn
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/toolboxai/${var.environment}/application"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.environment}-application-logs"
    Type = "application"
  })
}

resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/${var.environment}-cluster/cluster"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.environment}-eks-logs"
    Type = "kubernetes"
  })
}

resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/${var.environment}-aurora/postgresql"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.environment}-rds-logs"
    Type = "database"
  })
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.environment}-lambda-logs"
    Type = "serverless"
  })
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-toolboxai-overview"

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
            ["AWS/EKS", "cluster_failed_request_count", "ClusterName", "${var.environment}-cluster"],
            [".", "cluster_request_total", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "EKS Cluster Metrics"
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
            ["AWS/RDS", "CPUUtilization", "DBClusterIdentifier", "${var.environment}-aurora"],
            [".", "DatabaseConnections", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "RDS Aurora Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${var.environment}-alb"],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", "${var.environment}-context-handler"],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."],
            [".", "Throttles", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Lambda Function Metrics"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6

        properties = {
          query   = "SOURCE '/aws/toolboxai/${var.environment}/application' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region  = data.aws_region.current.name
          title   = "Recent Application Errors"
          view    = "table"
        }
      }
    ]
  })
}

# CloudWatch Alarms - EKS
resource "aws_cloudwatch_metric_alarm" "eks_node_cpu_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-eks-node-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EKS node CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    AutoScalingGroupName = "${var.environment}-eks-nodes"
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "eks_node_memory_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-eks-node-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors EKS node memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    AutoScalingGroupName = "${var.environment}-eks-nodes"
  }

  tags = var.tags
}

# CloudWatch Alarms - RDS
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBClusterIdentifier = "${var.environment}-aurora"
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBClusterIdentifier = "${var.environment}-aurora"
  }

  tags = var.tags
}

# CloudWatch Alarms - ALB
resource "aws_cloudwatch_metric_alarm" "alb_response_time_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-alb-response-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = "${var.environment}-alb"
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-alb-5xx-errors-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5XX errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = "${var.environment}-alb"
  }

  tags = var.tags
}

# CloudWatch Alarms - Lambda
resource "aws_cloudwatch_metric_alarm" "lambda_errors_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-lambda-errors-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors Lambda function errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = "${var.environment}-context-handler"
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration_high" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-lambda-duration-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "25000"
  alarm_description   = "This metric monitors Lambda function duration"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = "${var.environment}-context-handler"
  }

  tags = var.tags
}

# CloudWatch Alarms - DynamoDB
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-dynamodb-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "UserRequestExceededThrottleQuota"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors DynamoDB throttling"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TableName = "mcp-contexts"
  }

  tags = var.tags
}

# Custom Metrics for Application Monitoring
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${var.environment}-error-count"
  log_group_name = aws_cloudwatch_log_group.application.name
  pattern        = "[timestamp, requestId, ERROR]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "ToolBoxAI/${var.environment}"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "application_errors" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.environment}-application-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorCount"
  namespace           = "ToolBoxAI/${var.environment}"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors application errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# X-Ray Tracing
resource "aws_xray_sampling_rule" "main" {
  count = var.enable_xray ? 1 : 0

  rule_name      = "${var.environment}-toolboxai-sampling"
  priority       = 9000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  tags = var.tags
}

# Container Insights for EKS
resource "aws_cloudwatch_log_group" "container_insights" {
  count = var.enable_container_insights ? 1 : 0

  name              = "/aws/containerinsights/${var.environment}-cluster/performance"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.environment}-container-insights"
    Type = "monitoring"
  })
}

# CloudWatch Composite Alarms
resource "aws_cloudwatch_composite_alarm" "system_health" {
  count = var.enable_alarms ? 1 : 0

  alarm_name        = "${var.environment}-system-health"
  alarm_description = "Composite alarm for overall system health"

  alarm_rule = join(" OR ", [
    "ALARM(${aws_cloudwatch_metric_alarm.eks_node_cpu_high[0].alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.rds_cpu_high[0].alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.alb_5xx_errors_high[0].alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.lambda_errors_high[0].alarm_name})"
  ])

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# CloudWatch Insights Queries
resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${var.environment}-error-analysis"

  log_group_names = [
    aws_cloudwatch_log_group.application.name,
    aws_cloudwatch_log_group.lambda.name
  ]

  query_string = <<-EOT
    fields @timestamp, @message
    | filter @message like /ERROR/
    | stats count() by bin(5m)
    | sort @timestamp desc
  EOT
}

resource "aws_cloudwatch_query_definition" "performance_analysis" {
  name = "${var.environment}-performance-analysis"

  log_group_names = [
    aws_cloudwatch_log_group.application.name
  ]

  query_string = <<-EOT
    fields @timestamp, @message
    | filter @message like /duration/
    | parse @message "duration: * ms" as duration
    | stats avg(duration), max(duration), min(duration) by bin(5m)
    | sort @timestamp desc
  EOT
}

# Service Map for distributed tracing
resource "aws_xray_encryption_config" "main" {
  count = var.enable_xray ? 1 : 0

  type   = "KMS"
  key_id = var.kms_key_id
}