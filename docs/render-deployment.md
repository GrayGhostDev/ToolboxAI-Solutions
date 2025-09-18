# Render.com Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the ToolboxAI Educational Platform to Render.com. The deployment includes:
- FastAPI backend service
- React dashboard (static site)
- PostgreSQL database
- Redis cache
- Background workers
- Scheduled jobs

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub/GitLab Repository**: Code must be in a git repository
3. **API Keys**: Have your OpenAI, Anthropic, and Pusher keys ready
4. **Domain (Optional)**: Custom domain for production deployment

## Quick Start

### 1. Connect Repository

1. Log into Render Dashboard
2. Click "New +" → "Blueprint"
3. Connect your GitHub/GitLab account
4. Select your repository
5. Select the branch (usually `main`)
6. Render will detect the `render.yaml` file

### 2. Configure Environment Variables

Navigate to each service and add required secrets:

```bash
# Backend Service
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PUSHER_APP_ID=your_app_id
PUSHER_KEY=your_key
PUSHER_SECRET=your_secret
SENTRY_DSN=https://...@sentry.io/... (optional)
```

### 3. Deploy

Click "Apply" to start deployment. Render will:
- Create all services defined in `render.yaml`
- Set up databases and Redis
- Configure networking
- Deploy your application

## Detailed Configuration

### Backend Service

The backend runs as a Docker container with:
- **Runtime**: Python 3.12
- **Framework**: FastAPI with Uvicorn
- **Workers**: 4 (configurable)
- **Port**: Dynamic (uses `$PORT`)
- **Health Check**: `/health`

#### Key Environment Variables

```env
# Core Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Database (auto-configured by Render)
DATABASE_URL=postgresql://...

# Redis (auto-configured by Render)
REDIS_URL=redis://...

# CORS (update with your domains)
CORS_ORIGINS=["https://toolboxai-dashboard.onrender.com"]

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend Dashboard

The dashboard is deployed as a static site:
- **Build Command**: `cd apps/dashboard && npm ci && npm run build`
- **Publish Directory**: `apps/dashboard/dist`
- **Environment**: Node.js 20.12.0

#### Configuration

```env
VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
VITE_WS_URL=wss://toolboxai-backend.onrender.com
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=us2
```

### Database Configuration

PostgreSQL database with:
- **Plan**: Standard (for production)
- **Version**: PostgreSQL 15
- **Backup**: Daily automatic backups
- **Connection Pooling**: Enabled

### Redis Configuration

Redis cache with:
- **Plan**: Standard (for production)
- **Eviction Policy**: allkeys-lru
- **Persistence**: Enabled

## Deployment Process

### Using the Deployment Script

```bash
# Full deployment
./scripts/deploy-render.sh deploy

# Validate configuration only
./scripts/deploy-render.sh validate

# Run tests before deployment
./scripts/deploy-render.sh test

# Build locally to verify
./scripts/deploy-render.sh build
```

### Manual Deployment

1. **Commit Changes**
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Trigger Deployment**
   - Automatic: Push to connected branch
   - Manual: Click "Manual Deploy" in Render dashboard

3. **Monitor Deployment**
   - Check service logs in Render dashboard
   - Monitor build progress
   - Verify health checks

## Environment Management

### Development vs Production

Use separate Render projects for different environments:

```yaml
# Development
toolboxai-dev:
  - Backend: toolboxai-backend-dev.onrender.com
  - Frontend: toolboxai-dashboard-dev.onrender.com

# Production
toolboxai-prod:
  - Backend: api.yourdomain.com
  - Frontend: app.yourdomain.com
```

### Environment Groups

Render supports environment groups for shared variables:

1. Create groups in Render dashboard
2. Reference in `render.yaml`:
   ```yaml
   envVars:
     - fromGroup: toolboxai-secrets
   ```

## Custom Domains

### Backend API

1. Go to service settings
2. Add custom domain (e.g., `api.yourdomain.com`)
3. Configure DNS:
   ```
   CNAME api.yourdomain.com → toolboxai-backend.onrender.com
   ```

### Frontend Dashboard

1. Go to static site settings
2. Add custom domain (e.g., `app.yourdomain.com`)
3. Configure DNS:
   ```
   CNAME app.yourdomain.com → toolboxai-dashboard.onrender.com
   ```

## Monitoring

### Health Checks

Monitor service health:
- **Basic**: `https://your-backend.onrender.com/health`
- **Readiness**: `https://your-backend.onrender.com/ready`
- **Liveness**: `https://your-backend.onrender.com/live`
- **Metrics**: `https://your-backend.onrender.com/metrics`

### Logs

Access logs in Render dashboard:
1. Navigate to service
2. Click "Logs" tab
3. Filter by timestamp or search

### Alerts

Configure alerts in Render:
1. Go to service settings
2. Add notification endpoints
3. Set up alert conditions

## Scaling

### Horizontal Scaling

Upgrade service plan for auto-scaling:
```yaml
services:
  - type: web
    name: toolboxai-backend
    plan: pro  # Supports auto-scaling
    scaling:
      minInstances: 2
      maxInstances: 10
      targetCPUPercent: 70
```

### Vertical Scaling

Change instance types:
- **Starter**: 512MB RAM, 0.5 CPU
- **Standard**: 2GB RAM, 1 CPU
- **Pro**: 4GB RAM, 2 CPU
- **Pro Plus**: 8GB RAM, 4 CPU

## Troubleshooting

### Common Issues

#### 1. Build Failures

```bash
# Check build logs
# Common fixes:
- Verify Python version in runtime.txt
- Check requirements.txt syntax
- Ensure all files are committed
```

#### 2. Database Connection Issues

```bash
# Verify DATABASE_URL is set
# Check database status in Render dashboard
# Ensure IP allowlist is configured correctly
```

#### 3. CORS Errors

```bash
# Update CORS_ORIGINS in environment variables
# Include your frontend URL
CORS_ORIGINS=["https://your-frontend.onrender.com"]
```

#### 4. Health Check Failures

```bash
# Check application logs
# Verify dependencies are running (DB, Redis)
# Test locally with same environment variables
```

### Debug Mode

Enable debug logging:
```env
DEBUG=true
LOG_LEVEL=debug
```

**Warning**: Only use in development/staging!

## Rollback

### Via Dashboard

1. Go to service → Events
2. Find previous successful deployment
3. Click "Rollback to this deploy"

### Via API

```bash
curl -X POST https://api.render.com/v1/services/{service-id}/deploys/{deploy-id}/rollback \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy to Render
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/deploy/srv-xxx?key=$RENDER_API_KEY
```

### Pre-deployment Checks

Add to your CI pipeline:
```yaml
- name: Run Tests
  run: |
    pytest tests/
    npm test

- name: Validate Configuration
  run: |
    python scripts/validate_render_config.py
```

## Security Best Practices

1. **Secrets Management**
   - Never commit secrets to git
   - Use Render's secret management
   - Rotate keys regularly

2. **Network Security**
   - Use private services for internal communication
   - Configure IP allowlists for databases
   - Enable WAF for public services

3. **SSL/TLS**
   - Automatic HTTPS for all services
   - Force SSL redirects
   - Configure HSTS headers

4. **Access Control**
   - Use Render teams for collaboration
   - Implement RBAC in application
   - Audit access logs regularly

## Cost Optimization

### Tips for Reducing Costs

1. **Right-size instances**: Start small, scale as needed
2. **Use free tier**: For development/testing
3. **Schedule workers**: Run batch jobs during off-peak
4. **Optimize builds**: Cache dependencies
5. **Monitor usage**: Set up billing alerts

### Free Tier Limits

- **Web Services**: 750 hours/month
- **Static Sites**: Unlimited
- **PostgreSQL**: 256MB storage
- **Redis**: 25MB memory
- **Bandwidth**: 100GB/month

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review logs for errors
   - Check resource usage
   - Update dependencies

2. **Monthly**
   - Rotate API keys
   - Review and optimize database
   - Audit security settings

3. **Quarterly**
   - Load testing
   - Disaster recovery drill
   - Cost optimization review

### Database Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Support

### Render Support

- **Documentation**: [render.com/docs](https://render.com/docs)
- **Status Page**: [status.render.com](https://status.render.com)
- **Support**: support@render.com

### Application Support

- **GitHub Issues**: Report bugs and feature requests
- **Logs**: Check service logs in Render dashboard
- **Monitoring**: Use health check endpoints

## Appendix

### Useful Commands

```bash
# Check deployment status
curl https://your-backend.onrender.com/health

# View current configuration
cat render.yaml

# Validate environment
./scripts/deploy-render.sh validate

# Run local tests
pytest tests/
npm test

# Build Docker image locally
docker build -f Dockerfile.backend -t toolboxai-backend .
```

### Environment Variable Reference

See `.env.render` for complete list of configuration options.

### Migration from Other Platforms

#### From Heroku
1. Export Heroku config vars
2. Create Render services
3. Import environment variables
4. Update git remote
5. Deploy

#### From AWS
1. Export RDS database
2. Create Render PostgreSQL
3. Import data
4. Update connection strings
5. Deploy services

---

Last Updated: 2025-09-15
Version: 1.0.0