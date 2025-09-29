# ToolBoxAI Solutions - Monitoring Module Outputs

# SNS Topic
output "alerts_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "alerts_topic_name" {
  description = "Name of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.name
}

# CloudWatch Log Groups
output "application_log_group_name" {
  description = "Name of the application log group"
  value       = aws_cloudwatch_log_group.application.name
}

output "application_log_group_arn" {
  description = "ARN of the application log group"
  value       = aws_cloudwatch_log_group.application.arn
}

output "eks_log_group_name" {
  description = "Name of the EKS log group"
  value       = aws_cloudwatch_log_group.eks.name
}

output "eks_log_group_arn" {
  description = "ARN of the EKS log group"
  value       = aws_cloudwatch_log_group.eks.arn
}

output "rds_log_group_name" {
  description = "Name of the RDS log group"
  value       = aws_cloudwatch_log_group.rds.name
}

output "rds_log_group_arn" {
  description = "ARN of the RDS log group"
  value       = aws_cloudwatch_log_group.rds.arn
}

output "lambda_log_group_name" {
  description = "Name of the Lambda log group"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "lambda_log_group_arn" {
  description = "ARN of the Lambda log group"
  value       = aws_cloudwatch_log_group.lambda.arn
}

output "container_insights_log_group_name" {
  description = "Name of the Container Insights log group"
  value       = try(aws_cloudwatch_log_group.container_insights[0].name, null)
}

output "container_insights_log_group_arn" {
  description = "ARN of the Container Insights log group"
  value       = try(aws_cloudwatch_log_group.container_insights[0].arn, null)
}

# CloudWatch Dashboard
output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

# CloudWatch Alarms
output "eks_cpu_alarm_name" {
  description = "Name of the EKS CPU alarm"
  value       = try(aws_cloudwatch_metric_alarm.eks_node_cpu_high[0].alarm_name, null)
}

output "eks_memory_alarm_name" {
  description = "Name of the EKS memory alarm"
  value       = try(aws_cloudwatch_metric_alarm.eks_node_memory_high[0].alarm_name, null)
}

output "rds_cpu_alarm_name" {
  description = "Name of the RDS CPU alarm"
  value       = try(aws_cloudwatch_metric_alarm.rds_cpu_high[0].alarm_name, null)
}

output "rds_connections_alarm_name" {
  description = "Name of the RDS connections alarm"
  value       = try(aws_cloudwatch_metric_alarm.rds_connections_high[0].alarm_name, null)
}

output "alb_response_time_alarm_name" {
  description = "Name of the ALB response time alarm"
  value       = try(aws_cloudwatch_metric_alarm.alb_response_time_high[0].alarm_name, null)
}

output "alb_5xx_errors_alarm_name" {
  description = "Name of the ALB 5XX errors alarm"
  value       = try(aws_cloudwatch_metric_alarm.alb_5xx_errors_high[0].alarm_name, null)
}

output "lambda_errors_alarm_name" {
  description = "Name of the Lambda errors alarm"
  value       = try(aws_cloudwatch_metric_alarm.lambda_errors_high[0].alarm_name, null)
}

output "lambda_duration_alarm_name" {
  description = "Name of the Lambda duration alarm"
  value       = try(aws_cloudwatch_metric_alarm.lambda_duration_high[0].alarm_name, null)
}

output "dynamodb_throttles_alarm_name" {
  description = "Name of the DynamoDB throttles alarm"
  value       = try(aws_cloudwatch_metric_alarm.dynamodb_throttles[0].alarm_name, null)
}

output "application_errors_alarm_name" {
  description = "Name of the application errors alarm"
  value       = try(aws_cloudwatch_metric_alarm.application_errors[0].alarm_name, null)
}

output "system_health_composite_alarm_name" {
  description = "Name of the system health composite alarm"
  value       = try(aws_cloudwatch_composite_alarm.system_health[0].alarm_name, null)
}

# X-Ray
output "xray_sampling_rule_name" {
  description = "Name of the X-Ray sampling rule"
  value       = try(aws_xray_sampling_rule.main[0].rule_name, null)
}

output "xray_sampling_rule_arn" {
  description = "ARN of the X-Ray sampling rule"
  value       = try(aws_xray_sampling_rule.main[0].arn, null)
}

output "xray_encryption_config_type" {
  description = "Type of X-Ray encryption configuration"
  value       = try(aws_xray_encryption_config.main[0].type, null)
}

# Lambda Function for Slack Notifications
output "slack_notifier_function_name" {
  description = "Name of the Slack notifier Lambda function"
  value       = try(aws_lambda_function.slack_notifier[0].function_name, null)
}

output "slack_notifier_function_arn" {
  description = "ARN of the Slack notifier Lambda function"
  value       = try(aws_lambda_function.slack_notifier[0].arn, null)
}

# CloudWatch Insights Queries
output "error_analysis_query_name" {
  description = "Name of the error analysis CloudWatch Insights query"
  value       = aws_cloudwatch_query_definition.error_analysis.name
}

output "performance_analysis_query_name" {
  description = "Name of the performance analysis CloudWatch Insights query"
  value       = aws_cloudwatch_query_definition.performance_analysis.name
}

# Metric Filters
output "error_count_metric_filter_name" {
  description = "Name of the error count metric filter"
  value       = aws_cloudwatch_log_metric_filter.error_count.name
}

# All Log Group Names
output "all_log_group_names" {
  description = "List of all log group names"
  value = [
    aws_cloudwatch_log_group.application.name,
    aws_cloudwatch_log_group.eks.name,
    aws_cloudwatch_log_group.rds.name,
    aws_cloudwatch_log_group.lambda.name,
  ]
}

# All Log Group ARNs
output "all_log_group_arns" {
  description = "List of all log group ARNs"
  value = [
    aws_cloudwatch_log_group.application.arn,
    aws_cloudwatch_log_group.eks.arn,
    aws_cloudwatch_log_group.rds.arn,
    aws_cloudwatch_log_group.lambda.arn,
  ]
}

# All Alarm Names
output "all_alarm_names" {
  description = "List of all CloudWatch alarm names"
  value = compact([
    try(aws_cloudwatch_metric_alarm.eks_node_cpu_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.eks_node_memory_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.rds_cpu_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.rds_connections_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.alb_response_time_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.alb_5xx_errors_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.lambda_errors_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.lambda_duration_high[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.dynamodb_throttles[0].alarm_name, null),
    try(aws_cloudwatch_metric_alarm.application_errors[0].alarm_name, null),
  ])
}

# Monitoring Summary
output "monitoring_summary" {
  description = "Summary of monitoring configuration"
  value = {
    environment                = var.environment
    log_retention_days         = var.log_retention_days
    alarms_enabled            = var.enable_alarms
    xray_enabled              = var.enable_xray
    container_insights_enabled = var.enable_container_insights
    dashboard_created         = var.enable_dashboard
    sns_notifications_enabled = var.sns_topic_email != ""
    slack_notifications_enabled = var.slack_webhook_url != ""
    total_log_groups          = length([
      aws_cloudwatch_log_group.application,
      aws_cloudwatch_log_group.eks,
      aws_cloudwatch_log_group.rds,
      aws_cloudwatch_log_group.lambda,
    ])
    total_alarms = length(compact([
      try(aws_cloudwatch_metric_alarm.eks_node_cpu_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.eks_node_memory_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.rds_cpu_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.rds_connections_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.alb_response_time_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.alb_5xx_errors_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.lambda_errors_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.lambda_duration_high[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.dynamodb_throttles[0].alarm_name, null),
      try(aws_cloudwatch_metric_alarm.application_errors[0].alarm_name, null),
    ]))
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization information for monitoring"
  value = {
    log_retention_optimized = var.log_retention_days <= 30
    detailed_monitoring_status = var.enable_detailed_monitoring
    xray_sampling_rate = var.xray_sampling_rate
    container_insights_enabled = var.enable_container_insights
    estimated_monthly_cost_usd = {
      log_ingestion = "Based on log volume"
      log_storage = "Based on retention: ${var.log_retention_days} days"
      alarms = "~$0.10 per alarm"
      dashboard = "~$3.00 per dashboard"
      xray_traces = var.enable_xray ? "Based on trace volume" : "Disabled"
      container_insights = var.enable_container_insights ? "~$0.50 per node" : "Disabled"
    }
  }
}

# Quick Access URLs
output "quick_access_urls" {
  description = "Quick access URLs for monitoring resources"
  value = {
    cloudwatch_console = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}"
    dashboard_url = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
    logs_console = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#logsV2:log-groups"
    alarms_console = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#alarmsV2:"
    xray_console = var.enable_xray ? "https://console.aws.amazon.com/xray/home?region=${data.aws_region.current.name}" : null
    insights_console = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#logsV2:logs-insights"
  }
}

# Notification Configuration
output "notification_configuration" {
  description = "Notification configuration summary"
  value = {
    sns_topic_arn = aws_sns_topic.alerts.arn
    email_subscription_configured = var.sns_topic_email != ""
    slack_integration_configured = var.slack_webhook_url != ""
    total_subscribers = (var.sns_topic_email != "" ? 1 : 0) + (var.slack_webhook_url != "" ? 1 : 0)
  }
}