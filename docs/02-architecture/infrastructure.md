# Infrastructure Architecture

## Overview

The ToolboxAI Solutions platform uses a microservices architecture deployed on Kubernetes with automated CI/CD pipelines and comprehensive monitoring.

> **📚 Updated for 2025 Standards**: This document has been superseded by comprehensive 2025 infrastructure documentation. For the latest implementation details, see:
> - [Infrastructure Overview 2025](infrastructure-overview-2025.md) - Complete 2025 infrastructure architecture
> - [Docker Deployment Guide 2025](../04-implementation/docker-deployment-guide.md) - Container deployment strategy
> - [Kubernetes Deployment Guide 2025](../04-implementation/kubernetes-deployment-guide.md) - Orchestration and scaling
> - [Infrastructure Monitoring 2025](../07-operations/infrastructure-monitoring.md) - Monitoring and observability
> - [Infrastructure Security 2025](../07-operations/infrastructure-security.md) - Security and compliance

## Infrastructure Components

### Container Orchestration

#### Kubernetes Deployment

```yaml
# Production Cluster Configuration
apiVersion: v1
kind: Namespace
metadata:
  name: toolboxai-production
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: toolboxai-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: toolboxai/api:latest
          ports:
            - containerPort: 8008
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: url
          resources:
            requests:
              memory: '256Mi'
              cpu: '250m'
            limits:
              memory: '512Mi'
              cpu: '500m'
          livenessProbe:
            httpGet:
              path: /health
              port: 8008
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8008
            initialDelaySeconds: 5
            periodSeconds: 5
```text
#### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: toolboxai-production
spec:
  selector:
    app: api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8008
  type: LoadBalancer
```text
### Docker Configuration

#### API Dockerfile

```dockerfile
# Multi-stage build for FastAPI application
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8008/health')"

EXPOSE 8008

CMD ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", "8008"]
```text
#### Dashboard Dockerfile

```dockerfile
# Multi-stage build for React application
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine

# Custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# Security headers
RUN echo 'add_header X-Frame-Options "SAMEORIGIN" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-Content-Type-Options "nosniff" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-XSS-Protection "1; mode=block" always;' >> /etc/nginx/conf.d/security.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```text
### Load Balancing

#### NGINX Configuration

```nginx
upstream api_backend {
    least_conn;
    server api-1:8008 max_fails=3 fail_timeout=30s;
    server api-2:8008 max_fails=3 fail_timeout=30s;
    server api-3:8008 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream websocket_backend {
    ip_hash;  # Sticky sessions for WebSocket
    server ws-1:9876;
    server ws-2:9876;
}

server {
    listen 80;
    listen [::]:80;
    server_name api.toolboxai.com;

    # API endpoints
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # WebSocket endpoints
    location /ws/ {
        proxy_pass http://websocket_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket specific
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```text
### Database Infrastructure

#### PostgreSQL Cluster

```yaml
# PostgreSQL StatefulSet for production
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: toolboxai-production
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15
          env:
            - name: POSTGRES_REPLICATION_MODE
              value: master
            - name: POSTGRES_REPLICATION_USER
              value: replicator
            - name: POSTGRES_REPLICATION_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: replication-password
            - name: POSTGRES_DB
              value: toolboxai
            - name: POSTGRES_USER
              value: toolboxai
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: password
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: '2Gi'
              cpu: '1'
            limits:
              memory: '4Gi'
              cpu: '2'
  volumeClaimTemplates:
    - metadata:
        name: postgres-storage
      spec:
        accessModes: ['ReadWriteOnce']
        resources:
          requests:
            storage: 100Gi
```text
#### Redis Cluster

```yaml
# Redis deployment for caching
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: toolboxai-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command:
            - redis-server
            - --appendonly
            - 'yes'
            - --requirepass
            - '$(REDIS_PASSWORD)'
          env:
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: redis-secrets
                  key: password
          ports:
            - containerPort: 6379
          volumeMounts:
            - name: redis-storage
              mountPath: /data
          resources:
            requests:
              memory: '512Mi'
              cpu: '250m'
            limits:
              memory: '1Gi'
              cpu: '500m'
      volumes:
        - name: redis-storage
          persistentVolumeClaim:
            claimName: redis-pvc
```text
### Terraform Configuration

#### AWS Infrastructure

```hcl
# main.tf - AWS EKS Cluster
provider "aws" {
  region = var.aws_region
}

# VPC Configuration
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "toolboxai-vpc"
  cidr = "1127.0.0.1/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true
  enable_dns_hostnames = true

  tags = {
    Environment = var.environment
    Project     = "ToolboxAI"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.0.0"

  cluster_name    = "toolboxai-${var.environment}"
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    main = {
      desired_size = 3
      min_size     = 2
      max_size     = 10

      instance_types = ["t3.large"]

      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "main"
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "ToolboxAI"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier = "toolboxai-${var.environment}"

  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.r6g.large"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true

  db_name  = "toolboxai"
  username = "toolboxai"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  multi_az               = true
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "toolboxai-${var.environment}-final-${timestamp()}"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Environment = var.environment
    Project     = "ToolboxAI"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "toolboxai-${var.environment}"
  engine              = "redis"
  node_type           = "cache.r6g.large"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379

  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"

  tags = {
    Environment = var.environment
    Project     = "ToolboxAI"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "assets" {
  bucket = "toolboxai-assets-${var.environment}"

  tags = {
    Environment = var.environment
    Project     = "ToolboxAI"
  }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "assets" {
  bucket = aws_s3_bucket.assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.assets.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.assets.id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Environment = var.environment
    Project     = "ToolboxAI"
  }
}
```text
### CI/CD Pipeline

#### GitHub Actions Workflow

The complete CI/CD pipeline is defined in `.github/workflows/deploy.yml` with:

1. **Test Stage**: Runs all tests with PostgreSQL and Redis services
2. **Build Stage**: Creates optimized Docker images
3. **Deploy Staging**: Deploys to staging environment
4. **Deploy Production**: Deploys to production on release
5. **Rollback**: Automatic rollback on failure

### Monitoring and Observability

#### Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

    - job_name: 'node-exporter'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```text
#### Grafana Dashboards

Custom dashboards for:

- API performance metrics
- Database query performance
- Cache hit rates
- WebSocket connections
- Agent processing times
- Error rates and types

### Security Infrastructure

#### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: toolboxai-production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8008
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: toolboxai-production
      ports:
        - protocol: TCP
          port: 5432 # PostgreSQL
        - protocol: TCP
          port: 6379 # Redis
```text
#### Secrets Management

```yaml
# External Secrets Operator configuration
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
  namespace: toolboxai-production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: toolboxai-production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
    - secretKey: url
      remoteRef:
        key: toolboxai/production/database
        property: connection_string
```text
### Backup and Disaster Recovery

#### Database Backup

```bash
#!/bin/bash
# backup-postgres.sh - Automated PostgreSQL backup

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
S3_BUCKET="toolboxai-backups"

# Create backup
pg_dump $DATABASE_URL | gzip > ${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz

# Upload to S3
aws s3 cp ${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz s3://${S3_BUCKET}/postgres/

# Cleanup old local backups (keep last 7 days)
find ${BACKUP_DIR} -type f -mtime +7 -delete

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup successful: backup_${TIMESTAMP}.sql.gz"
else
    echo "Backup failed" >&2
    exit 1
fi
```text
#### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour
3. **Backup Schedule**:
   - Database: Every hour
   - Application state: Continuous replication
   - Configuration: Version controlled
4. **Recovery Procedures**:
   - Automated failover for database
   - Blue-green deployment for applications
   - DNS failover for traffic routing

### Scaling Strategy

#### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: toolboxai-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
```text
### Cost Optimization

1. **Reserved Instances**: 60% of baseline capacity
2. **Spot Instances**: For batch processing workloads
3. **Auto-scaling**: Based on actual usage patterns
4. **Resource Tagging**: For cost allocation
5. **Unused Resource Cleanup**: Automated weekly scans

### Compliance and Governance

1. **Data Residency**: Configurable per region
2. **Audit Logging**: All API calls logged
3. **Access Control**: RBAC with least privilege
4. **Compliance Standards**: SOC 2, GDPR ready
5. **Regular Security Audits**: Quarterly penetration testing

## Infrastructure as Code Best Practices

1. **Version Control**: All infrastructure code in Git
2. **Code Review**: Required for production changes
3. **Testing**: Terraform plan before apply
4. **Documentation**: Inline comments and README files
5. **Secrets Management**: Never commit secrets
6. **Immutable Infrastructure**: Replace, don't modify
7. **Blue-Green Deployments**: Zero-downtime updates
8. **Monitoring First**: Deploy monitoring before services
9. **Backup Verification**: Regular restore testing
10. **Disaster Recovery Drills**: Quarterly DR exercises
