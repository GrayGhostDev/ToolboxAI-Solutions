# AWS KMS Terraform Module

This module creates and manages AWS KMS keys for the ToolBoxAI Solutions platform with full compliance support for COPPA, FERPA, and GDPR.

## Features

- 🔐 **Multiple Purpose-Specific Keys**: Separate keys for different services (primary, database, S3, Lambda, EBS, messaging)
- 🔄 **Automatic Key Rotation**: Annual rotation enabled by default
- 🌍 **Multi-Region Support**: Optional multi-region key replication for production
- 📊 **CloudWatch Monitoring**: Usage alerts and metrics
- 🏢 **Compliance Ready**: COPPA, FERPA, and GDPR compliant configuration
- 🔑 **Granular Access Control**: IAM and key policies for fine-grained permissions
- 💰 **Cost Optimized**: S3 bucket keys and efficient encryption strategies

## Usage

```hcl
module "kms" {
  source = "../../modules/kms"

  project_name = "toolboxai"
  environment  = "prod"
  aws_region   = "us-east-1"

  # Enable multi-region for production
  multi_region = true

  # EKS access
  eks_node_role_arns = [
    "arn:aws:iam::123456789012:role/eks-node-role"
  ]

  # Lambda functions
  lambda_function_arns = [
    "arn:aws:lambda:us-east-1:123456789012:function:my-function"
  ]

  # Compliance
  coppa_compliance = true
  ferpa_compliance = true
  gdpr_compliance  = true

  # Monitoring
  enable_cloudwatch_monitoring = true
  sns_alert_topic_arns = ["arn:aws:sns:us-east-1:123456789012:alerts"]
}
```

## Keys Created

| Key | Purpose | Features |
|-----|---------|----------|
| `primary` | General encryption | Multi-region capable, used for Secrets Manager |
| `database` | RDS encryption | Automatic grants for RDS service |
| `s3` | S3 bucket encryption | Bucket key enabled for cost optimization |
| `lambda` | Lambda environment variables | Decrypt-only permissions |
| `ebs` | EBS volume encryption | Regional key for volume encryption |
| `messaging` | SNS/SQS encryption | Used for message queue encryption |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `project_name` | Name of the project | `string` | `"toolboxai"` | no |
| `environment` | Environment (dev, staging, prod) | `string` | n/a | yes |
| `aws_region` | AWS region | `string` | `"us-east-1"` | no |
| `deletion_window` | KMS key deletion window in days | `number` | `30` | no |
| `multi_region` | Enable multi-region replication | `bool` | `false` | no |
| `eks_node_role_arns` | EKS node role ARNs | `list(string)` | `[]` | no |
| `lambda_function_arns` | Lambda function ARNs | `list(string)` | `[]` | no |
| `coppa_compliance` | Enable COPPA compliance | `bool` | `true` | no |
| `ferpa_compliance` | Enable FERPA compliance | `bool` | `true` | no |
| `gdpr_compliance` | Enable GDPR compliance | `bool` | `true` | no |

## Outputs

| Name | Description |
|------|-------------|
| `all_key_arns` | Map of all KMS key ARNs by purpose |
| `all_key_ids` | Map of all KMS key IDs by purpose |
| `all_key_aliases` | Map of all KMS key aliases |
| `kms_configuration` | Summary of KMS configuration |

## Compliance

This module implements encryption controls required for:

- **COPPA**: Protects children's data with encryption at rest
- **FERPA**: Secures educational records with key-based access control
- **GDPR**: Enables data protection and right to erasure

## Security Best Practices

1. **Key Rotation**: Automatic annual rotation enabled
2. **Least Privilege**: Separate keys for different services
3. **Monitoring**: CloudWatch alarms for unusual usage
4. **Access Logging**: CloudTrail integration for audit
5. **Deletion Protection**: 30-day deletion window

## Cost Optimization

- S3 Bucket Keys reduce KMS API calls by up to 99%
- Regional keys for services that don't need multi-region
- Efficient grant management to minimize API calls

## Examples

See the `examples/` directory for:
- [Complete setup](examples/complete/) - Full production configuration
- Integration with other AWS services

## Testing

```bash
# Validate the module
terraform init
terraform validate

# Plan deployment
terraform plan -var="environment=dev"

# Apply configuration
terraform apply -var="environment=dev"
```

## Migration from Existing Keys

If you have existing KMS keys (like the one in .env: `13eb8af0-804c-4115-b97f-e189235c634c`), you can import them:

```bash
terraform import module.kms.aws_kms_key.primary 13eb8af0-804c-4115-b97f-e189235c634c
```

## Support

For issues or questions, contact the ToolBoxAI engineering team.