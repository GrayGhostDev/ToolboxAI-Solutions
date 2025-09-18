# AWS RDS Module for ToolBoxAI Solutions
# PostgreSQL database with high availability and compliance

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

locals {
  db_identifier = "${var.project_name}-${var.environment}-db"

  # Enhanced monitoring for production
  enhanced_monitoring = var.environment == "prod" ? {
    enabled                       = true
    monitoring_interval          = 30
    monitoring_role_name         = "${local.db_identifier}-monitoring-role"
  } : {
    enabled                       = var.enable_enhanced_monitoring
    monitoring_interval          = var.monitoring_interval
    monitoring_role_name         = "${local.db_identifier}-monitoring-role"
  }

  # Multi-AZ for production
  multi_az = var.environment == "prod" ? true : var.multi_az

  # Backup settings based on environment
  backup_config = var.environment == "prod" ? {
    retention_period   = 30
    backup_window     = "03:00-04:00"
    maintenance_window = "sun:04:00-sun:05:00"
  } : {
    retention_period   = var.backup_retention_period
    backup_window     = var.backup_window
    maintenance_window = var.maintenance_window
  }
}

# Generate secure password
resource "random_password" "master" {
  length  = 32
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name        = "${local.db_identifier}-subnet-group"
  description = "Database subnet group for ${local.db_identifier}"
  subnet_ids  = var.subnet_ids

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.db_identifier}-subnet-group"
      Environment = var.environment
    }
  )
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name_prefix = "${local.db_identifier}-sg-"
  description = "Security group for ${local.db_identifier}"
  vpc_id      = var.vpc_id

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.db_identifier}-sg"
      Environment = var.environment
    }
  )
}

resource "aws_security_group_rule" "rds_ingress" {
  for_each = var.allowed_security_groups

  type                     = "ingress"
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = each.value
  security_group_id        = aws_security_group.rds.id
  description              = "Allow PostgreSQL from ${each.key}"
}

resource "aws_security_group_rule" "rds_ingress_cidr" {
  count = length(var.allowed_cidr_blocks) > 0 ? 1 : 0

  type              = "ingress"
  from_port         = var.port
  to_port           = var.port
  protocol          = "tcp"
  cidr_blocks       = var.allowed_cidr_blocks
  security_group_id = aws_security_group.rds.id
  description       = "Allow PostgreSQL from CIDR blocks"
}

resource "aws_security_group_rule" "rds_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.rds.id
  description       = "Allow all outbound traffic"
}

# IAM Role for Enhanced Monitoring
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = local.enhanced_monitoring.enabled ? 1 : 0

  name = local.enhanced_monitoring.monitoring_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = local.enhanced_monitoring.enabled ? 1 : 0

  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Parameter Group for PostgreSQL optimization
resource "aws_db_parameter_group" "main" {
  name_prefix = "${local.db_identifier}-"
  family      = var.parameter_group_family
  description = "Custom parameter group for ${local.db_identifier}"

  # Performance tuning parameters
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements,pglogical"
  }

  parameter {
    name  = "max_connections"
    value = var.max_connections
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # Log queries taking more than 1 second
  }

  # SSL enforcement
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  # Compliance logging
  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_hostname"
    value = "1"
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.db_identifier}-parameter-group"
      Environment = var.environment
    }
  )
}

# Option Group (for additional features)
resource "aws_db_option_group" "main" {
  name_prefix              = "${local.db_identifier}-"
  option_group_description = "Option group for ${local.db_identifier}"
  engine_name              = var.engine
  major_engine_version     = var.major_engine_version

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.db_identifier}-option-group"
      Environment = var.environment
    }
  )
}

# Primary RDS Instance
resource "aws_db_instance" "main" {
  identifier = local.db_identifier

  # Engine configuration
  engine                      = var.engine
  engine_version             = var.engine_version
  instance_class             = var.instance_class
  allocated_storage          = var.allocated_storage
  max_allocated_storage      = var.max_allocated_storage
  storage_type               = var.storage_type
  storage_encrypted          = true
  kms_key_id                 = var.kms_key_arn
  storage_throughput         = var.storage_type == "gp3" ? var.storage_throughput : null
  iops                       = var.storage_type == "gp3" ? var.iops : null

  # Database configuration
  db_name  = var.database_name
  username = var.master_username
  password = random_password.master.result
  port     = var.port

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # High availability
  multi_az               = local.multi_az
  availability_zone      = !local.multi_az ? var.availability_zone : null

  # Backup configuration
  backup_retention_period = local.backup_config.retention_period
  backup_window          = local.backup_config.backup_window
  maintenance_window     = local.backup_config.maintenance_window
  copy_tags_to_snapshot  = true
  delete_automated_backups = var.environment != "prod"

  # Monitoring
  enabled_cloudwatch_logs_exports = var.enabled_cloudwatch_logs_exports
  monitoring_interval            = local.enhanced_monitoring.enabled ? local.enhanced_monitoring.monitoring_interval : 0
  monitoring_role_arn            = local.enhanced_monitoring.enabled ? aws_iam_role.rds_enhanced_monitoring[0].arn : null
  performance_insights_enabled    = var.performance_insights_enabled
  performance_insights_kms_key_id = var.performance_insights_enabled ? var.kms_key_arn : null
  performance_insights_retention_period = var.performance_insights_enabled ? var.performance_insights_retention_period : null

  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = aws_db_option_group.main.name

  # Auto minor version upgrade
  auto_minor_version_upgrade = var.auto_minor_version_upgrade
  allow_major_version_upgrade = false

  # Final snapshot
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${local.db_identifier}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Deletion protection for production
  deletion_protection = var.environment == "prod" ? true : var.deletion_protection

  # Apply changes immediately in non-prod
  apply_immediately = var.environment != "prod"

  # Dependencies
  depends_on = [
    aws_db_subnet_group.main,
    aws_security_group.rds,
    aws_iam_role_policy_attachment.rds_enhanced_monitoring
  ]

  tags = merge(
    var.common_tags,
    {
      Name        = local.db_identifier
      Environment = var.environment
      Compliance  = var.coppa_compliance || var.ferpa_compliance || var.gdpr_compliance ? "Required" : "None"
    }
  )

  lifecycle {
    ignore_changes = [password]
  }
}

# Read Replica (for production)
resource "aws_db_instance" "read_replica" {
  count = var.create_read_replica ? 1 : 0

  identifier             = "${local.db_identifier}-read-replica"
  replicate_source_db    = aws_db_instance.main.identifier

  instance_class         = var.read_replica_instance_class != "" ? var.read_replica_instance_class : var.instance_class

  # Storage is inherited from primary
  storage_encrypted      = true

  # Network configuration
  publicly_accessible    = false

  # No backups on read replica
  backup_retention_period = 0

  # Monitoring
  monitoring_interval    = local.enhanced_monitoring.enabled ? local.enhanced_monitoring.monitoring_interval : 0
  monitoring_role_arn    = local.enhanced_monitoring.enabled ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  # Auto minor version upgrade
  auto_minor_version_upgrade = var.auto_minor_version_upgrade

  # Final snapshot
  skip_final_snapshot = true

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.db_identifier}-read-replica"
      Environment = var.environment
      Type        = "ReadReplica"
    }
  )
}

# Store credentials in Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  name_prefix             = "${local.db_identifier}-credentials-"
  description            = "Database credentials for ${local.db_identifier}"
  kms_key_id             = var.kms_key_arn
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = merge(
    var.common_tags,
    {
      Name        = "${local.db_identifier}-credentials"
      Environment = var.environment
    }
  )
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.master.result
    endpoint = aws_db_instance.main.endpoint
    address  = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    database = aws_db_instance.main.db_name
    engine   = aws_db_instance.main.engine
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${local.db_identifier}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.cpu_utilization_threshold
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = var.sns_topic_arns

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "${local.db_identifier}-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.free_storage_space_threshold
  alarm_description   = "This metric monitors RDS free storage"
  alarm_actions       = var.sns_topic_arns

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${local.db_identifier}-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.database_connections_threshold
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = var.sns_topic_arns

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.common_tags
}

# Automated Backup Replication (for disaster recovery)
resource "aws_db_instance_automated_backups_replication" "main" {
  count = var.enable_backup_replication ? 1 : 0

  source_db_instance_arn = aws_db_instance.main.arn
  kms_key_id            = var.backup_replication_kms_key_arn != "" ? var.backup_replication_kms_key_arn : var.kms_key_arn

  retention_period = var.backup_replication_retention_period

  lifecycle {
    ignore_changes = [retention_period]
  }
}

# Outputs
output "db_instance_id" {
  description = "The RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_instance_arn" {
  description = "The ARN of the RDS instance"
  value       = aws_db_instance.main.arn
}

output "db_instance_endpoint" {
  description = "The connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_address" {
  description = "The hostname of the RDS instance"
  value       = aws_db_instance.main.address
}

output "db_credentials_secret_arn" {
  description = "ARN of the secret containing database credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}