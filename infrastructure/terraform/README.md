# ToolBoxAI Solutions - Terraform Infrastructure

This repository contains the complete Terraform infrastructure configuration for ToolBoxAI Solutions, providing a scalable, secure, and cost-optimized cloud infrastructure on AWS.

## 🏗️ Architecture Overview

The infrastructure is designed with the following key principles:
- **Multi-environment support** (dev, staging, production)
- **Security-first approach** with encryption, monitoring, and compliance
- **Cost optimization** with spot instances, auto-scaling, and resource tagging
- **High availability** with multi-AZ deployment and disaster recovery
- **Observability** with comprehensive monitoring and alerting

## 📁 Directory Structure

```
infrastructure/terraform/
├── main.tf                    # Root module orchestrating all components
├── variables.tf               # Root module variables
├── README.md                  # This documentation
├── modules/                   # Reusable Terraform modules
│   ├── networking/           # VPC, subnets, NAT gateways, security groups
│   ├── security/             # KMS, WAF, security groups, compliance
│   ├── monitoring/           # CloudWatch, alarms, dashboards, logging
│   ├── eks/                  # Kubernetes cluster and node groups
│   ├── rds/                  # Aurora PostgreSQL database
│   ├── s3/                   # S3 buckets and lifecycle policies
│   ├── lambda/               # Lambda functions and triggers
│   ├── secrets/              # Secrets Manager and KMS keys
│   ├── kms/                  # Encryption key management
│   └── mcp/                  # MCP-specific infrastructure (DynamoDB, API Gateway)
├── environments/             # Environment-specific configurations
│   ├── dev/                  # Development environment
│   ├── staging/              # Staging environment
│   └── production/           # Production environment
└── global/                   # Global resources (S3 state bucket, etc.)
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0 installed
3. **Access to AWS account** with administrative permissions
4. **S3 bucket** for Terraform state storage
5. **DynamoDB table** for state locking

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd infrastructure/terraform
   ```

2. **Configure AWS credentials**:
   ```bash
   aws configure
   # or use AWS_PROFILE environment variable
   export AWS_PROFILE=your-profile-name
   ```

3. **Create Terraform state infrastructure** (if not exists):
   ```bash
   # Create S3 bucket for state
   aws s3 mb s3://toolboxai-terraform-state

   # Create DynamoDB table for locking
   aws dynamodb create-table \
     --table-name toolboxai-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
   ```

4. **Choose your environment** and navigate to it:
   ```bash
   cd environments/dev  # or staging/production
   ```

5. **Copy and configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your specific values
   ```

6. **Set sensitive variables as environment variables**:
   ```bash
   export TF_VAR_openai_api_key="your-openai-key"
   export TF_VAR_anthropic_api_key="your-anthropic-key"
   export TF_VAR_pusher_app_id="your-pusher-app-id"
   export TF_VAR_pusher_key="your-pusher-key"
   export TF_VAR_pusher_secret="your-pusher-secret"
   ```

7. **Initialize and deploy**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## 🏛️ Module Documentation

### Networking Module
- **Purpose**: Creates VPC, subnets, internet gateway, NAT gateways, route tables
- **Features**:
  - Multi-AZ deployment
  - VPC endpoints for cost optimization
  - Flow logs for security monitoring
  - Network ACLs for additional security

### Security Module
- **Purpose**: Manages security groups, KMS keys, WAF, and compliance resources
- **Features**:
  - Application Load Balancer security groups
  - EKS cluster and node security groups
  - Database security groups
  - WAF with managed rule sets
  - AWS Config for compliance monitoring

### Monitoring Module
- **Purpose**: Comprehensive observability and alerting
- **Features**:
  - CloudWatch dashboards and alarms
  - SNS topics for notifications
  - Slack integration for alerts
  - X-Ray tracing
  - Container Insights for EKS

### EKS Module
- **Purpose**: Managed Kubernetes cluster with node groups
- **Features**:
  - Multi-node group setup (general, MCP, GPU)
  - Cluster autoscaler
  - AWS Load Balancer Controller
  - OIDC provider for service accounts

### RDS Module
- **Purpose**: Aurora PostgreSQL database cluster
- **Features**:
  - Multi-AZ deployment
  - Automated backups
  - Performance Insights
  - Serverless v2 scaling

### MCP Module
- **Purpose**: MCP (Model Context Protocol) specific infrastructure
- **Features**:
  - DynamoDB tables for contexts, agents, sessions
  - S3 buckets for artifacts and archives
  - Lambda functions for processing
  - API Gateway for WebSocket connections
  - SQS queues for async processing

## 🌍 Environment Configurations

### Development Environment
- **Purpose**: Feature development and testing
- **Features**:
  - Minimal resources for cost optimization
  - Auto-shutdown capabilities
  - Debug logging enabled
  - Bastion host for debugging

### Staging Environment
- **Purpose**: Pre-production testing and validation
- **Features**:
  - Production-like setup but smaller scale
  - Load testing capabilities
  - Blue-green deployment support
  - Synthetic monitoring

### Production Environment
- **Purpose**: Live production workloads
- **Features**:
  - High availability and disaster recovery
  - Enhanced security and compliance
  - CloudFront CDN for global distribution
  - Comprehensive backup strategy
  - 24/7 monitoring and alerting

## 🔧 Configuration Management

### Variable Hierarchy
1. **Default values** in module variables.tf files
2. **Environment-specific** values in terraform.tfvars
3. **Runtime overrides** via TF_VAR_* environment variables

### Sensitive Data Management
- Use environment variables for API keys and secrets
- Leverage AWS Secrets Manager for application secrets
- KMS encryption for all sensitive data at rest

### Tagging Strategy
All resources are tagged with:
- `Environment`: dev/staging/production
- `Project`: ToolBoxAI-Solutions
- `ManagedBy`: Terraform
- `CostCenter`: engineering
- `Owner`: resource owner email

## 💰 Cost Optimization

### Development
- Spot instances for cost savings
- Minimal resource allocation
- Auto-shutdown during off-hours
- Reduced monitoring and logging retention

### Staging
- Mix of spot and on-demand instances
- Production-like setup but smaller scale
- Cost alerts and budget monitoring

### Production
- On-demand instances for reliability
- Reserved instances for predictable workloads
- Savings plans for flexible compute
- Comprehensive cost tracking and optimization

## 🔒 Security Features

### Network Security
- Private subnets for application workloads
- Security groups with least privilege access
- VPC Flow Logs for network monitoring
- WAF for application-layer protection

### Data Security
- Encryption at rest with customer-managed KMS keys
- Encryption in transit with TLS
- Secrets Manager for credential management
- Regular security scanning and compliance checks

### Access Control
- IAM roles with least privilege principles
- Service accounts for Kubernetes workloads
- Multi-factor authentication requirements
- Audit logging for all administrative actions

## 📊 Monitoring and Alerting

### CloudWatch Integration
- Custom dashboards for each environment
- Proactive alerting based on thresholds
- Log aggregation and analysis
- Performance metrics and insights

### Notification Channels
- Email notifications for standard alerts
- Slack integration for team collaboration
- PagerDuty integration for critical alerts (production)
- SMS notifications for emergency escalation

### Health Checks
- Application health endpoints
- Database connection monitoring
- External service dependency checks
- Synthetic transaction monitoring

## 🔄 Deployment Strategies

### Development
- Direct deployment for rapid iteration
- Feature branch deployments
- Automated rollback on failure

### Staging
- Blue-green deployments
- Canary releases for testing
- Automated integration testing
- Performance benchmarking

### Production
- Rolling deployments with health checks
- Canary deployments for risk mitigation
- Automated rollback mechanisms
- Zero-downtime deployment strategies

## 🆘 Disaster Recovery

### Backup Strategy
- Automated daily backups
- Cross-region backup replication
- Point-in-time recovery capabilities
- Regular backup restoration testing

### Recovery Procedures
- Documented recovery time objectives (RTO)
- Recovery point objectives (RPO)
- Automated failover mechanisms
- Regular disaster recovery drills

## 🧪 Testing

### Infrastructure Testing
- Terraform plan validation
- Resource compliance checking
- Security vulnerability scanning
- Cost impact analysis

### Application Testing
- Health check validation
- Load testing in staging
- Security penetration testing
- Performance benchmarking

## 📚 Additional Resources

### Documentation
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)

### Tools and Utilities
- `terraform fmt` - Format Terraform files
- `terraform validate` - Validate configuration
- `terraform plan` - Preview changes
- `tflint` - Terraform linting
- `checkov` - Security scanning

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test in development environment
4. Submit a pull request
5. Peer review and approval
6. Deploy to staging for validation
7. Production deployment after approval

## 📞 Support

- **Documentation**: Check this README and module documentation
- **Issues**: Create GitHub issues for bugs and feature requests
- **Emergency**: Use critical alert channels for production issues
- **Questions**: Reach out to the infrastructure team

---

**Last Updated**: 2025-01-28
**Version**: 1.0.0
**Maintained By**: ToolBoxAI Infrastructure Team