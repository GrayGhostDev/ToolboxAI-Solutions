# 🚀 ToolBoxAI Solutions - Cloud Infrastructure

## Overview

This directory contains the complete Infrastructure as Code (IaC) and configuration for deploying ToolBoxAI Solutions to the cloud. The infrastructure is designed following 2025 best practices including AWS Well-Architected Framework, Kubernetes cloud-native principles, and Anthropic's Model Context Protocol (MCP) for AI orchestration.

## 🏗️ Architecture

### Cloud Providers
- **Primary**: AWS (us-east-1, us-west-2)
- **Secondary**: Google Cloud Platform (disaster recovery)
- **CDN**: CloudFlare

### Core Components
1. **Compute**: AWS EKS (Kubernetes)
2. **Database**: Aurora PostgreSQL, DynamoDB
3. **Cache**: ElastiCache Redis
4. **Storage**: S3, EBS
5. **Networking**: VPC, ALB, CloudFront
6. **AI/ML**: MCP Servers, Agent Fleet
7. **Monitoring**: Prometheus, Grafana, CloudWatch

## 📁 Directory Structure

```
infrastructure/
├── terraform/              # Infrastructure as Code
│   ├── environments/       # Environment-specific configs
│   ├── modules/           # Reusable Terraform modules
│   └── global/            # Global resources
├── kubernetes/            # Kubernetes manifests
│   ├── base/             # Base configurations
│   ├── apps/             # Application deployments
│   └── overlays/         # Environment overlays
├── docker/               # Docker configurations
├── mcp/                  # Model Context Protocol configs
├── ci-cd/                # CI/CD pipelines
├── monitoring/           # Monitoring & alerting
└── scripts/              # Deployment scripts
```

## 🚦 Quick Start

### Prerequisites

1. **Tools Required**:
   ```bash
   # Install required tools
   brew install terraform kubectl helm aws-cli
   ```

2. **AWS Credentials**:
   ```bash
   aws configure --profile toolboxai
   export AWS_PROFILE=toolboxai
   ```

3. **Environment Variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your values
   source .env
   ```

### Deployment

#### Automated Deployment
```bash
# Deploy to staging
./scripts/deploy.sh staging deploy

# Deploy to production
./scripts/deploy.sh production deploy

# Dry run (plan only)
./scripts/deploy.sh staging dry-run
```

#### Manual Step-by-Step

1. **Deploy Infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform plan -var-file=environments/staging/terraform.tfvars
   terraform apply -var-file=environments/staging/terraform.tfvars
   ```

2. **Build & Push Docker Images**:
   ```bash
   # Login to ECR
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY

   # Build and push
   docker build -f docker/backend.Dockerfile -t $ECR_REGISTRY/backend:latest .
   docker push $ECR_REGISTRY/backend:latest
   ```

3. **Deploy to Kubernetes**:
   ```bash
   # Update kubeconfig
   aws eks update-kubeconfig --name toolboxai-staging

   # Apply manifests
   kubectl apply -k kubernetes/overlays/staging
   ```

4. **Verify Deployment**:
   ```bash
   kubectl get pods -A
   kubectl get svc -A
   ```

## 🔧 Configuration

### Terraform Variables

Key variables in `terraform/variables.tf`:
- `environment`: dev, staging, production
- `aws_region`: AWS region for deployment
- `vpc_cidr`: VPC CIDR block
- API keys (stored in secrets)

### Kubernetes ConfigMaps

Located in `kubernetes/base/configmaps/`:
- `backend-config`: Backend API configuration
- `mcp-config`: MCP server settings
- `dashboard-config`: Frontend settings

### Secrets Management

⚠️ **Never commit secrets to Git!**

Create secrets using:
```bash
# Create Kubernetes secrets
kubectl create secret generic api-keys \
  --from-literal=openai-key=$OPENAI_API_KEY \
  --from-literal=anthropic-key=$ANTHROPIC_API_KEY \
  -n toolboxai

# Or use AWS Secrets Manager
aws secretsmanager create-secret \
  --name toolboxai/production/api-keys \
  --secret-string '{"openai":"sk-...","anthropic":"sk-ant-..."}'
```

## 🤖 MCP (Model Context Protocol) Setup

### MCP Architecture
- **Main Server**: WebSocket server for context management
- **Orchestrator**: Task distribution and coordination
- **Agent Fleet**: Specialized AI agents
  - Supervisor Agent
  - Content Agents
  - Quiz Agents
  - Terrain Agents
  - Script Agents
  - Review Agents

### MCP Deployment
```bash
# Deploy MCP infrastructure
kubectl apply -f kubernetes/apps/mcp/

# Check MCP status
kubectl get pods -n mcp
kubectl get pods -n mcp-agents
```

### MCP Configuration
Configuration files in `mcp/`:
- `servers/orchestrator.json`: Orchestrator configuration
- `agents/*.yaml`: Agent-specific configs
- `context/schemas/`: Context validation schemas

## 📊 Monitoring

### Access Dashboards

1. **Grafana**:
   ```bash
   kubectl port-forward -n monitoring svc/grafana 3000:80
   # Access at http://localhost:3000
   # Default: admin/admin
   ```

2. **Prometheus**:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-server 9090:80
   # Access at http://localhost:9090
   ```

### Key Metrics

- **System**: CPU, Memory, Disk, Network
- **Application**: Request rate, Error rate, Latency
- **MCP**: Context tokens, Agent performance, Task completion
- **Business**: User activity, Content generation, Quiz completion

### Alerts

Configured alerts in `monitoring/prometheus/values.yaml`:
- MCPServerDown
- AgentNotResponding
- APIHighLatency
- APIHighErrorRate
- HighMemoryUsage

## 🔐 Security

### Network Security
- Private subnets for compute resources
- Public subnets only for load balancers
- Network ACLs and Security Groups
- AWS WAF for application protection

### Data Security
- Encryption at rest (KMS)
- Encryption in transit (TLS 1.3)
- Secret rotation with AWS Secrets Manager
- IAM roles with least privilege

### Compliance
- COPPA compliant
- FERPA compliant
- SOC 2 Type 2
- GDPR ready

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

Located in `.github/workflows/deploy.yml`:

1. **Test**: Run unit and integration tests
2. **Security Scan**: Trivy and Snyk scanning
3. **Build**: Docker image creation
4. **Deploy**: Terraform and Kubernetes deployment
5. **Smoke Test**: Verify deployment
6. **Rollback**: Automatic on failure

### Trigger Deployment
```bash
# Push to main branch triggers staging deployment
git push origin main

# Manual production deployment
# Go to GitHub Actions → Deploy to Production → Run workflow
```

## 📈 Scaling

### Auto-scaling Configuration

1. **Cluster Autoscaler**: Automatically scales nodes
2. **HPA**: Scales pods based on metrics
3. **VPA**: Right-sizes pod resources

### Manual Scaling
```bash
# Scale deployment
kubectl scale deployment backend --replicas=5 -n toolboxai

# Scale node group
eksctl scale nodegroup --cluster=toolboxai-production --name=general --nodes=10
```

## 🔄 Disaster Recovery

### Backup Strategy
- **Database**: Daily snapshots, 30-day retention
- **S3**: Cross-region replication
- **Configuration**: Git versioning

### Recovery Procedures
1. **Database Recovery**:
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier toolboxai-recovered \
     --db-snapshot-identifier snapshot-id
   ```

2. **Cluster Recovery**:
   ```bash
   # Restore from backup region
   ./scripts/dr-restore.sh us-west-2
   ```

## 💰 Cost Optimization

### Recommendations
1. Use Spot Instances for non-critical workloads
2. Enable S3 Intelligent-Tiering
3. Right-size EC2 instances
4. Use Reserved Instances for predictable workloads
5. Implement resource tagging for cost allocation

### Cost Monitoring
```bash
# View current costs
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=TAG,Key=Environment
```

## 🐛 Troubleshooting

### Common Issues

1. **Pod not starting**:
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   kubectl logs <pod-name> -n <namespace>
   ```

2. **Service not accessible**:
   ```bash
   kubectl get svc -A
   kubectl get ingress -A
   ```

3. **MCP connection issues**:
   ```bash
   # Check MCP server logs
   kubectl logs -n mcp -l app=mcp-server

   # Test WebSocket connection
   wscat -c ws://mcp-server.mcp.svc.cluster.local:9876
   ```

### Debug Commands
```bash
# Get cluster info
kubectl cluster-info dump

# Check node status
kubectl get nodes -o wide

# View events
kubectl get events -A --sort-by='.lastTimestamp'
```

## 📚 Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Model Context Protocol](https://modelcontextprotocol.io)

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test in development environment
4. Submit PR with deployment plan
5. Deploy to staging after approval
6. Production deployment after staging validation

## 📞 Support

- **Slack**: #infrastructure
- **Email**: infrastructure@toolboxai.solutions
- **On-call**: PagerDuty

---

**Last Updated**: 2025-09-17
**Version**: 1.0.0
**Maintained By**: Infrastructure Team