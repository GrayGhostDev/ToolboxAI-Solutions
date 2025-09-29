# RDS Module Outputs

# Primary Instance Outputs
output "db_instance" {
  description = "Complete database instance details"
  value = {
    id                = aws_db_instance.main.id
    arn               = aws_db_instance.main.arn
    endpoint          = aws_db_instance.main.endpoint
    address           = aws_db_instance.main.address
    port              = aws_db_instance.main.port
    engine            = aws_db_instance.main.engine
    engine_version    = aws_db_instance.main.engine_version
    instance_class    = aws_db_instance.main.instance_class
    allocated_storage = aws_db_instance.main.allocated_storage
    multi_az          = aws_db_instance.main.multi_az
    availability_zone = aws_db_instance.main.availability_zone
    status            = aws_db_instance.main.status
  }
}

# Connection Information
output "connection_info" {
  description = "Database connection information"
  value = {
    endpoint         = aws_db_instance.main.endpoint
    reader_endpoint  = var.create_read_replica ? aws_db_instance.read_replica[0].endpoint : null
    port            = aws_db_instance.main.port
    database_name   = aws_db_instance.main.db_name
    master_username = aws_db_instance.main.username
  }
  sensitive = true
}

# Read Replica Outputs
output "read_replica" {
  description = "Read replica instance details"
  value = var.create_read_replica ? {
    id               = aws_db_instance.read_replica[0].id
    arn              = aws_db_instance.read_replica[0].arn
    endpoint         = aws_db_instance.read_replica[0].endpoint
    address          = aws_db_instance.read_replica[0].address
    instance_class   = aws_db_instance.read_replica[0].instance_class
    availability_zone = aws_db_instance.read_replica[0].availability_zone
  } : null
}

# Security Configuration
output "security_group" {
  description = "Security group details"
  value = {
    id   = aws_security_group.rds.id
    arn  = aws_security_group.rds.arn
    name = aws_security_group.rds.name
  }
}

output "db_subnet_group" {
  description = "DB subnet group details"
  value = {
    id         = aws_db_subnet_group.main.id
    arn        = aws_db_subnet_group.main.arn
    name       = aws_db_subnet_group.main.name
    subnet_ids = aws_db_subnet_group.main.subnet_ids
  }
}

# Credentials and Secrets
output "db_credentials_secret" {
  description = "Secrets Manager secret containing database credentials"
  value = {
    arn              = aws_secretsmanager_secret.db_credentials.arn
    name             = aws_secretsmanager_secret.db_credentials.name
    version_id       = aws_secretsmanager_secret_version.db_credentials.version_id
    secret_string_key = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${aws_secretsmanager_secret.db_credentials.name}"
  }
  sensitive = true
}

# Parameter and Option Groups
output "parameter_group" {
  description = "DB parameter group details"
  value = {
    id     = aws_db_parameter_group.main.id
    arn    = aws_db_parameter_group.main.arn
    name   = aws_db_parameter_group.main.name
    family = aws_db_parameter_group.main.family
  }
}

output "option_group" {
  description = "DB option group details"
  value = {
    id                   = aws_db_option_group.main.id
    arn                  = aws_db_option_group.main.arn
    name                 = aws_db_option_group.main.name
    engine_name          = aws_db_option_group.main.engine_name
    major_engine_version = aws_db_option_group.main.major_engine_version
  }
}

# Monitoring Configuration
output "monitoring" {
  description = "Monitoring configuration details"
  value = {
    enhanced_monitoring_enabled = local.enhanced_monitoring.enabled
    monitoring_interval        = local.enhanced_monitoring.enabled ? local.enhanced_monitoring.monitoring_interval : 0
    monitoring_role_arn        = local.enhanced_monitoring.enabled ? aws_iam_role.rds_enhanced_monitoring[0].arn : null
    performance_insights_enabled = aws_db_instance.main.performance_insights_enabled
    cloudwatch_log_exports      = aws_db_instance.main.enabled_cloudwatch_logs_exports
  }
}

# CloudWatch Alarms
output "cloudwatch_alarms" {
  description = "CloudWatch alarm names"
  value = {
    cpu_alarm         = aws_cloudwatch_metric_alarm.database_cpu.alarm_name
    storage_alarm     = aws_cloudwatch_metric_alarm.database_storage.alarm_name
    connections_alarm = aws_cloudwatch_metric_alarm.database_connections.alarm_name
  }
}

# Backup Configuration
output "backup_config" {
  description = "Backup configuration details"
  value = {
    retention_period     = aws_db_instance.main.backup_retention_period
    backup_window        = aws_db_instance.main.backup_window
    maintenance_window   = aws_db_instance.main.maintenance_window
    latest_restorable_time = aws_db_instance.main.latest_restorable_time
    backup_replication_enabled = var.enable_backup_replication
  }
}

# Encryption Status
output "encryption" {
  description = "Encryption configuration"
  value = {
    storage_encrypted = aws_db_instance.main.storage_encrypted
    kms_key_id       = aws_db_instance.main.kms_key_id
  }
}

# Resource ARNs for IAM Policies
output "resource_arns" {
  description = "Resource ARNs for IAM policy creation"
  value = {
    db_instance_arn = aws_db_instance.main.arn
    secret_arn     = aws_secretsmanager_secret.db_credentials.arn
    kms_key_arn    = var.kms_key_arn
  }
}

# Connection String Templates
output "connection_strings" {
  description = "Database connection string templates"
  value = {
    jdbc = "jdbc:postgresql://${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
    psql = "postgresql://${aws_db_instance.main.username}:PASSWORD@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
    node = "postgresql://${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
    python = "postgresql+psycopg2://${aws_db_instance.main.username}:PASSWORD@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
  }
  sensitive = true
}

# Status Information
output "status" {
  description = "Current status of the database"
  value = {
    db_instance_status     = aws_db_instance.main.status
    deletion_protection    = aws_db_instance.main.deletion_protection
    publicly_accessible    = aws_db_instance.main.publicly_accessible
  }
}

# Module Configuration Summary
output "rds_module_summary" {
  description = "Summary of RDS module configuration"
  value = {
    environment      = var.environment
    project_name     = var.project_name
    engine          = "${var.engine} ${var.engine_version}"
    instance_class   = var.instance_class
    multi_az        = local.multi_az
    read_replica    = var.create_read_replica
    encryption      = true
    compliance = {
      coppa = var.coppa_compliance
      ferpa = var.ferpa_compliance
      gdpr  = var.gdpr_compliance
    }
  }
}

# Data sources for outputs
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}