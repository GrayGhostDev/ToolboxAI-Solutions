# Lambda Module Outputs

# Function Details
output "function" {
  description = "Complete Lambda function details"
  value = {
    name          = aws_lambda_function.main.function_name
    arn           = aws_lambda_function.main.arn
    invoke_arn    = aws_lambda_function.main.invoke_arn
    qualified_arn = aws_lambda_function.main.qualified_arn
    version       = aws_lambda_function.main.version
    last_modified = aws_lambda_function.main.last_modified
    runtime       = aws_lambda_function.main.runtime
    handler       = aws_lambda_function.main.handler
    memory_size   = aws_lambda_function.main.memory_size
    timeout       = aws_lambda_function.main.timeout
  }
}

# Alias Information
output "alias" {
  description = "Lambda alias details"
  value = {
    name         = aws_lambda_alias.main.name
    arn          = aws_lambda_alias.main.arn
    invoke_arn   = aws_lambda_alias.main.invoke_arn
    description  = aws_lambda_alias.main.description
    function_version = aws_lambda_alias.main.function_version
  }
}

# Function URL
output "function_url_details" {
  description = "Function URL configuration"
  value = var.create_function_url ? {
    url               = aws_lambda_function_url.main[0].function_url
    url_id            = aws_lambda_function_url.main[0].url_id
    creation_time     = aws_lambda_function_url.main[0].creation_time
    authorization_type = aws_lambda_function_url.main[0].authorization_type
    cors_config       = {
      allow_origins     = var.cors_allow_origins
      allow_methods     = var.cors_allow_methods
      allow_headers     = var.cors_allow_headers
      expose_headers    = var.cors_expose_headers
      max_age          = var.cors_max_age
      allow_credentials = var.cors_allow_credentials
    }
  } : null
}

# IAM Role
output "role" {
  description = "IAM role details"
  value = {
    id          = aws_iam_role.lambda.id
    arn         = aws_iam_role.lambda.arn
    name        = aws_iam_role.lambda.name
    unique_id   = aws_iam_role.lambda.unique_id
    create_date = aws_iam_role.lambda.create_date
  }
}

# Security Group (if VPC configured)
output "security_group" {
  description = "Security group details"
  value = length(var.subnet_ids) > 0 ? {
    id   = aws_security_group.lambda[0].id
    arn  = aws_security_group.lambda[0].arn
    name = aws_security_group.lambda[0].name
  } : null
}

# Layer Information
output "layer" {
  description = "Lambda layer details"
  value = var.create_layer ? {
    arn                  = aws_lambda_layer_version.dependencies[0].arn
    layer_arn            = aws_lambda_layer_version.dependencies[0].layer_arn
    version              = aws_lambda_layer_version.dependencies[0].version
    created_date         = aws_lambda_layer_version.dependencies[0].created_date
    compatible_runtimes  = aws_lambda_layer_version.dependencies[0].compatible_runtimes
  } : null
}

# CloudWatch Logs
output "logging" {
  description = "CloudWatch logging configuration"
  value = {
    log_group_name     = aws_cloudwatch_log_group.lambda.name
    log_group_arn      = aws_cloudwatch_log_group.lambda.arn
    retention_in_days  = aws_cloudwatch_log_group.lambda.retention_in_days
    log_format         = var.log_format
  }
}

# CloudWatch Alarms
output "alarms" {
  description = "CloudWatch alarm names"
  value = {
    errors_alarm    = aws_cloudwatch_metric_alarm.lambda_errors.alarm_name
    throttles_alarm = aws_cloudwatch_metric_alarm.lambda_throttles.alarm_name
    duration_alarm  = aws_cloudwatch_metric_alarm.lambda_duration.alarm_name
  }
}

# VPC Configuration
output "vpc_config" {
  description = "VPC configuration details"
  value = length(var.subnet_ids) > 0 ? {
    subnet_ids         = var.subnet_ids
    security_group_ids = concat([aws_security_group.lambda[0].id], var.additional_security_group_ids)
    vpc_id            = var.vpc_id
  } : null
}

# Environment Configuration
output "environment_config" {
  description = "Environment configuration"
  value = {
    variables = merge(
      {
        ENVIRONMENT   = var.environment
        PROJECT_NAME  = var.project_name
        FUNCTION_NAME = var.function_name
      },
      var.coppa_compliance ? {
        COPPA_ENABLED = "true"
        MIN_USER_AGE  = "13"
      } : {},
      var.ferpa_compliance ? {
        FERPA_ENABLED = "true"
        EDUCATIONAL_RECORDS_PROTECTION = "true"
      } : {},
      var.gdpr_compliance ? {
        GDPR_ENABLED        = "true"
        DATA_RETENTION_DAYS = "2555"
        RIGHT_TO_ERASURE   = "true"
      } : {}
    )
  }
  sensitive = true
}

# Async Configuration
output "async_config" {
  description = "Asynchronous invocation configuration"
  value = {
    maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
    maximum_retry_attempts       = var.maximum_retry_attempts
    on_success_destination      = var.on_success_destination_arn
    on_failure_destination      = var.on_failure_destination_arn
    dead_letter_queue           = var.dead_letter_queue_arn
  }
}

# Permissions Summary
output "permissions" {
  description = "IAM permissions granted to the function"
  value = {
    secrets_manager_access = length(var.secrets_manager_arns) > 0
    s3_access             = length(var.s3_bucket_arns) > 0
    dynamodb_access       = length(var.dynamodb_table_arns) > 0
    sqs_access            = length(var.sqs_queue_arns) > 0
    kms_encryption        = var.kms_key_arn != ""
    xray_tracing          = var.tracing_mode != "PassThrough"
    vpc_access            = length(var.subnet_ids) > 0
  }
}

# Triggers and Integrations
output "triggers" {
  description = "Function triggers and integrations"
  value = {
    api_gateway_enabled = var.api_gateway_execution_arn != ""
    eventbridge_rules   = keys(var.eventbridge_rules)
    s3_buckets         = keys(var.s3_triggers)
    sqs_queues         = keys(var.sqs_triggers)
    function_url       = var.create_function_url
  }
}

# Resource ARNs for IAM Policies
output "resource_arns" {
  description = "Resource ARNs for IAM policy creation"
  value = {
    function_arn   = aws_lambda_function.main.arn
    role_arn      = aws_iam_role.lambda.arn
    log_group_arn = aws_cloudwatch_log_group.lambda.arn
    layer_arn     = var.create_layer ? aws_lambda_layer_version.dependencies[0].arn : null
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance configuration status"
  value = {
    coppa_enabled = var.coppa_compliance
    ferpa_enabled = var.ferpa_compliance
    gdpr_enabled  = var.gdpr_compliance
    encryption_enabled = var.kms_key_arn != ""
    tracing_enabled   = var.tracing_mode == "Active"
    logging_enabled   = true
  }
}

# Performance Configuration
output "performance_config" {
  description = "Performance-related configuration"
  value = {
    memory_size                    = aws_lambda_function.main.memory_size
    timeout                       = aws_lambda_function.main.timeout
    reserved_concurrent_executions = aws_lambda_function.main.reserved_concurrent_executions
    ephemeral_storage_size        = var.ephemeral_storage_size
    architecture                  = var.architecture
  }
}

# Module Summary
output "lambda_module_summary" {
  description = "Summary of Lambda module configuration"
  value = {
    environment     = var.environment
    project_name    = var.project_name
    function_name   = local.function_name
    runtime        = local.runtime_config[var.runtime_type].runtime
    architecture   = var.architecture
    vpc_enabled    = length(var.subnet_ids) > 0
    url_enabled    = var.create_function_url
    layer_enabled  = var.create_layer
    monitoring = {
      xray_tracing = var.tracing_mode == "Active"
      alarms_enabled = length(var.sns_topic_arns) > 0
      log_retention = var.log_retention_days
    }
    compliance = {
      coppa = var.coppa_compliance
      ferpa = var.ferpa_compliance
      gdpr  = var.gdpr_compliance
    }
  }
}