# 🚀 Deployment Guide

**Last Updated**: September 24, 2025
**Docker Version**: 25.x / Compose v2
**Architecture**: Microservices with Docker Orchestration

## Overview

This guide covers deployment procedures for ToolBoxAI using the modernized Docker infrastructure implemented on September 24, 2025. The system uses a three-tier Docker Compose configuration with enterprise-grade security.

## 📋 Prerequisites

### System Requirements
- **Docker Engine**: 25.x or later
- **Docker Compose**: v2.24 or later
- **RAM**: Minimum 8GB (16GB recommended for production)
- **Storage**: 50GB available space
- **CPU**: 4+ cores recommended

### Required Tools
```bash
# Verify installations
docker --version         # Should be 25.x+
docker compose version    # Should be v2.24+
git --version            # For source control
openssl version          # For generating secrets
```

## 🏗️ Deployment Environments

### Environment Overview
| Environment | Purpose | Config File | URL |
|------------|---------|-------------|-----|
| Development | Local development | docker-compose.dev.yml | http://localhost:5179 |
| Staging | Pre-production testing | docker-compose.staging.yml | https://staging.toolboxai.com |
| Production | Live system | docker-compose.prod.yml | https://app.toolboxai.com |

## 🚀 Development Deployment

### 1. Initial Setup
```bash
# Clone repository
git clone https://github.com/toolboxai/toolboxai-solutions.git
cd toolboxai-solutions

# Create environment file from template
cp .env.example .env

# Generate secure keys
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 24)" >> .env
```

### 2. Configure Development Environment
```bash
# Edit .env file with your development API keys
nano .env

# Required variables for development:
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://toolboxai:devpass2024@postgres:5432/toolboxai
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your_development_key  # Optional
```

### 3. Start Development Stack
```bash
cd infrastructure/docker/compose

# Start with development configuration
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f

# Check service health
docker compose ps
```

### 4. Development URLs
- **Dashboard**: http://localhost:5179
- **Backend API**: http://localhost:8009
- **API Documentation**: http://localhost:8009/docs
- **Database Admin**: http://localhost:8080 (Adminer)
- **Redis Commander**: http://localhost:8081
- **Mail Testing**: http://localhost:8025 (Mailhog)

## 🎬 Staging Deployment

### 1. Prepare Staging Environment
```bash
# Create staging branch
git checkout -b staging
git pull origin main

# Create staging environment file
cp .env.example .env.staging

# Configure staging variables
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://staging_user:$STAGING_DB_PASS@postgres:5432/staging_db
```

### 2. Build Staging Images
```bash
# Build with BuildKit optimizations
export DOCKER_BUILDKIT=1

# Build all services
docker compose -f docker-compose.yml -f docker-compose.staging.yml build

# Tag for staging registry
docker tag toolboxai/backend:latest registry.toolboxai.com/backend:staging
docker tag toolboxai/dashboard:latest registry.toolboxai.com/dashboard:staging
```

### 3. Deploy to Staging
```bash
# Push to registry
docker push registry.toolboxai.com/backend:staging
docker push registry.toolboxai.com/dashboard:staging

# Deploy on staging server
ssh staging.toolboxai.com
cd /opt/toolboxai
docker compose -f docker-compose.yml -f docker-compose.staging.yml pull
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

## 🏭 Production Deployment

### 1. Security Prerequisites

#### Create Docker Secrets
```bash
# Initialize Docker Swarm (if not already done)
docker swarm init

# Create production secrets
echo "production_db_password" | docker secret create db_password -
echo "production_redis_password" | docker secret create redis_password -
echo "production_jwt_secret" | docker secret create jwt_secret -
echo "production_openai_key" | docker secret create openai_api_key -
echo "production_anthropic_key" | docker secret create anthropic_api_key -

# Verify secrets
docker secret ls
```

#### Configure SSL/TLS
```bash
# Obtain SSL certificates (using Let's Encrypt)
certbot certonly --standalone -d app.toolboxai.com -d api.toolboxai.com

# Copy certificates to Docker config
cp /etc/letsencrypt/live/app.toolboxai.com/fullchain.pem infrastructure/docker/config/nginx/ssl/
cp /etc/letsencrypt/live/app.toolboxai.com/privkey.pem infrastructure/docker/config/nginx/ssl/
```

### 2. Production Configuration
```bash
# Create production environment
cp .env.example .env.production

# Essential production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
```

### 3. Deploy to Production

#### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Database backed up
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Team notified

#### Deployment Steps
```bash
# 1. Build production images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# 2. Run security scan
docker scout cves toolboxai/backend:latest
docker scout cves toolboxai/dashboard:latest

# 3. Push to production registry
docker tag toolboxai/backend:latest registry.toolboxai.com/backend:v1.0.0
docker tag toolboxai/dashboard:latest registry.toolboxai.com/dashboard:v1.0.0
docker push registry.toolboxai.com/backend:v1.0.0
docker push registry.toolboxai.com/dashboard:v1.0.0

# 4. Deploy with zero downtime
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --scale backend=3
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --scale dashboard=2

# 5. Health check
./scripts/health-check.sh production

# 6. Remove old containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans
```

### 4. Post-Deployment Verification
```bash
# Check service health
curl https://api.toolboxai.com/health

# Verify frontend
curl -I https://app.toolboxai.com

# Check logs for errors
docker compose logs --tail=100 backend
docker compose logs --tail=100 dashboard

# Monitor metrics
open https://metrics.toolboxai.com  # Grafana dashboard
```

## 📊 Monitoring & Logging

### Production Monitoring Stack
```bash
# Included in docker-compose.prod.yml:
- Prometheus (metrics collection)
- Grafana (visualization)
- Loki (log aggregation)
- Promtail (log shipping)

# Access monitoring
https://metrics.toolboxai.com     # Grafana
https://metrics.toolboxai.com/prometheus  # Prometheus
```

### Key Metrics to Monitor
- **Application Metrics**
  - Request rate and latency
  - Error rate (4xx, 5xx)
  - Active users
  - API usage by endpoint

- **Infrastructure Metrics**
  - CPU and memory usage
  - Disk I/O
  - Network traffic
  - Container health

## 🔄 Rolling Updates

### Update Process
```bash
# 1. Build new version
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend

# 2. Deploy with rolling update
docker service update --image toolboxai/backend:v1.0.1 toolboxai_backend

# 3. Monitor rollout
docker service ps toolboxai_backend

# 4. Rollback if needed
docker service rollback toolboxai_backend
```

## 🚨 Rollback Procedures

### Automatic Rollback
```yaml
# Configured in docker-compose.prod.yml
deploy:
  update_config:
    failure_action: rollback
    monitor: 60s
    max_failure_ratio: 0.3
```

### Manual Rollback
```bash
# Quick rollback to previous version
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
git checkout tags/v1.0.0
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Database rollback (if needed)
docker exec toolboxai-postgres psql -U toolboxai -d toolboxai_prod < /backup/backup-20250924.sql
```

## 🔧 Maintenance Mode

### Enable Maintenance Mode
```bash
# Deploy maintenance page
docker run -d --name maintenance -p 80:80 -v ./maintenance.html:/usr/share/nginx/html/index.html nginx:alpine

# Stop production services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### Disable Maintenance Mode
```bash
# Start production services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Remove maintenance page
docker stop maintenance && docker rm maintenance
```

## 📦 Backup & Recovery

### Automated Backups
```bash
# Database backup (runs daily via cron)
0 2 * * * docker exec toolboxai-postgres pg_dumpall -U toolboxai > /backup/db-$(date +\%Y\%m\%d).sql

# Volume backup
docker run --rm -v toolboxai_postgres_data:/data -v /backup:/backup alpine tar czf /backup/postgres-data-$(date +\%Y\%m\%d).tar.gz /data
```

### Disaster Recovery
```bash
# Restore database
docker exec -i toolboxai-postgres psql -U toolboxai < /backup/latest.sql

# Restore volumes
docker run --rm -v toolboxai_postgres_data:/data -v /backup:/backup alpine tar xzf /backup/postgres-data-latest.tar.gz -C /
```

## 🌍 Multi-Region Deployment

### Geographic Distribution
```yaml
# Region configuration
regions:
  us-east-1:
    primary: true
    url: https://us.toolboxai.com
  eu-west-1:
    replica: true
    url: https://eu.toolboxai.com
  ap-southeast-1:
    replica: true
    url: https://asia.toolboxai.com
```

## 🔐 Security Considerations

### Production Security Checklist
- [ ] All secrets in Docker Secrets or external vault
- [ ] TLS/SSL certificates configured
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Container scanning enabled
- [ ] Audit logging active
- [ ] Backup encryption enabled

## 📚 Additional Resources

- [Docker Infrastructure README](infrastructure/docker/README.md)
- [Security Documentation](../../09-reference/security/templates/SECURITY_POLICY_TEMPLATE.md)
- [API Documentation](http://localhost:8009/docs)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## 🆘 Support

- **Slack**: #toolboxai-deployment
- **Email**: devops@toolboxai.com
- **On-Call**: See PagerDuty rotation

---

*For emergency deployments, contact the on-call engineer via PagerDuty*
