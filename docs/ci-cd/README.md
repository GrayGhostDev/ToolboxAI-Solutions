# ToolBoxAI Solutions - CI/CD Pipeline Documentation

## Overview

This document describes the comprehensive CI/CD pipeline implementation for ToolBoxAI-Solutions, featuring Docker-based containerization, multi-stage deployments, security scanning, and blue-green deployment strategies.

## Pipeline Architecture

### GitHub Actions Pipeline (`.github/workflows/docker-ci-cd.yml`)

The GitHub Actions pipeline provides a complete CI/CD solution with the following stages:

1. **Setup & Preparation**
   - Environment detection
   - Cache key generation
   - Build matrix configuration
   - Version determination

2. **Code Quality**
   - Python linting (Black, Ruff, MyPy)
   - JavaScript/TypeScript linting (ESLint)
   - Dockerfile linting (Hadolint)

3. **Docker Build**
   - Multi-platform builds (linux/amd64, linux/arm64)
   - BuildKit optimization with layer caching
   - Image metadata and labeling
   - Registry push with semantic versioning

4. **Security Scanning**
   - Trivy vulnerability scanning
   - SARIF report generation
   - Critical vulnerability threshold enforcement
   - Results uploaded to GitHub Security tab

5. **Integration Testing**
   - Full stack deployment with Docker Compose
   - Database and Redis connectivity verification
   - API endpoint testing
   - Inter-service communication validation

6. **Performance Testing**
   - K6 load testing framework
   - Response time and error rate thresholds
   - Scalability validation

7. **Deployment**
   - Blue-green deployment to staging
   - Production deployment with rollback capability
   - Health check verification
   - Traffic switching automation

8. **Post-Deployment Verification**
   - Smoke tests execution
   - End-to-end validation
   - Monitoring integration

### GitLab CI Pipeline (`.gitlab-ci.yml`)

The GitLab CI pipeline mirrors the GitHub Actions functionality with GitLab-specific optimizations:

- **Parallel job execution** for faster pipeline completion
- **GitLab Container Registry** integration
- **SAST/DAST security scanning** with GitLab Security Dashboard
- **Auto-scaling runners** support
- **Merge request pipelines** for efficient testing

## Services Architecture

### Core Services

1. **FastAPI Main Backend** (`fastapi-main`)
   - Primary API server
   - JWT authentication
   - Database and Redis integration
   - Pusher real-time features

2. **Dashboard Frontend** (`dashboard-frontend`)
   - React-based SPA
   - Material-UI components
   - Redux state management
   - Real-time updates via Pusher

3. **MCP Server** (`mcp-server`)
   - Model Context Protocol server
   - Agent coordination
   - Context management

4. **Agent Coordinator** (`agent-coordinator`)
   - AI agent orchestration
   - Task queue management
   - SPARC framework integration

5. **Flask Bridge** (`flask-bridge`)
   - Roblox integration service
   - Legacy API compatibility
   - Cross-platform communication

### Infrastructure Services

- **PostgreSQL**: Primary database with connection pooling
- **Redis**: Caching and session management
- **Prometheus**: Metrics collection and monitoring
- **Fluentd**: Log aggregation and forwarding

## Docker Configuration

### Multi-Stage Dockerfiles

Each service uses optimized multi-stage Dockerfiles with:
- **Builder stage**: Dependency installation and compilation
- **Production stage**: Minimal runtime environment
- **Security hardening**: Non-root user execution
- **Health checks**: Container health monitoring

### Docker Compose Configurations

1. **Development** (`docker-compose.dev.yml`)
   - Hot-reload enabled
   - Debug mode active
   - Volume mounts for source code
   - Development-friendly ports

2. **Staging** (`docker-compose.staging.yml`)
   - Production-like environment
   - SSL termination
   - Resource limits enforced

3. **Production Blue/Green** (`docker-compose.prod-{blue|green}.yml`)
   - Zero-downtime deployments
   - Separate network isolation
   - Resource optimization
   - Monitoring integration

## Blue-Green Deployment

### Architecture

The blue-green deployment strategy maintains two identical production environments:

- **Blue Environment**: Currently active production
- **Green Environment**: Standby for new deployments

### Traffic Switching

The `scripts/ci-cd/blue-green-switch.sh` script handles:

1. **Health Checks**: Verify new environment readiness
2. **Load Balancer Update**: Switch traffic routing
3. **Verification**: Confirm successful deployment
4. **Rollback**: Automatic rollback on failure

### Benefits

- **Zero Downtime**: Seamless user experience
- **Risk Mitigation**: Easy rollback capability
- **Testing in Production**: Validate in real environment
- **Resource Efficiency**: Optimal resource utilization

## Security Implementation

### Vulnerability Scanning

- **Trivy**: Container image vulnerability scanning
- **Safety**: Python dependency vulnerability checking
- **TruffleHog**: Secret detection in codebase
- **SAST/DAST**: Static and dynamic application security testing

### Security Policies

- **Critical Vulnerability Threshold**: Max 5 critical vulnerabilities
- **Secrets Detection**: Automatic secret scanning with exclusions
- **Container Hardening**: Non-root execution, minimal base images
- **Network Segmentation**: Isolated Docker networks

### Compliance

- **SARIF Reports**: Security findings in standardized format
- **GitHub Security Tab**: Centralized vulnerability management
- **Audit Logging**: Complete deployment audit trail

## Environment Management

### Environment Variables

Each environment uses specific configuration:

```bash
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARN
```

### Secrets Management

Secrets are managed through:
- **GitHub Secrets**: CI/CD pipeline secrets
- **Docker Secrets**: Runtime secret injection
- **Environment Files**: Environment-specific configuration

## Testing Strategy

### Test Types

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service interaction testing
3. **End-to-End Tests**: Complete workflow validation
4. **Performance Tests**: Load and stress testing
5. **Smoke Tests**: Post-deployment validation

### Test Automation

- **Pytest**: Python unit and integration testing
- **Vitest**: Frontend component testing
- **K6**: Performance and load testing
- **Custom Smoke Tests**: Post-deployment verification

## Monitoring and Observability

### Metrics Collection

- **Prometheus**: System and application metrics
- **Grafana**: Visualization and alerting
- **Health Checks**: Service availability monitoring

### Logging

- **Fluentd**: Log aggregation and forwarding
- **Structured Logging**: JSON-formatted application logs
- **Log Retention**: Configurable retention policies

### Alerting

- **Slack Integration**: Pipeline status notifications
- **Email Alerts**: Critical issue notifications
- **Webhook Integration**: Custom alerting endpoints

## Performance Optimization

### Build Optimization

- **Docker BuildKit**: Advanced build features
- **Multi-stage Builds**: Minimal production images
- **Layer Caching**: Faster subsequent builds
- **Parallel Builds**: Concurrent image building

### Runtime Optimization

- **Resource Limits**: Container resource constraints
- **Auto-scaling**: Horizontal pod autoscaling
- **Connection Pooling**: Database connection optimization
- **Caching**: Redis-based application caching

## Deployment Workflows

### Feature Development

1. **Feature Branch**: Create from main
2. **Development**: Local development with Docker
3. **Pull Request**: Automated testing and review
4. **Merge**: Integration into main branch

### Release Process

1. **Tag Creation**: Semantic version tagging
2. **Build Pipeline**: Automated image building
3. **Security Scan**: Vulnerability assessment
4. **Staging Deploy**: Automated staging deployment
5. **Production Deploy**: Blue-green production deployment
6. **Verification**: Post-deployment validation

### Rollback Process

1. **Issue Detection**: Monitoring or user reports
2. **Rollback Decision**: Team approval
3. **Traffic Switch**: Automated rollback to previous environment
4. **Verification**: Confirm successful rollback
5. **Issue Investigation**: Root cause analysis

## Usage Instructions

### Local Development

```bash
# Start development environment
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# View logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
```

### Production Deployment

```bash
# Deploy to production (manual trigger)
gh workflow run docker-ci-cd.yml -f environment=production

# Monitor deployment
gh run list --workflow=docker-ci-cd.yml

# Check deployment status
./scripts/ci-cd/smoke-tests.py --url https://toolboxai.solutions
```

### Blue-Green Switch

```bash
# Switch to green environment
./scripts/ci-cd/blue-green-switch.sh green

# Rollback to previous environment
./scripts/ci-cd/blue-green-switch.sh --rollback

# Dry run (preview changes)
./scripts/ci-cd/blue-green-switch.sh blue --dry-run
```

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify base image availability
   - Review build logs for specific errors

2. **Test Failures**
   - Check service dependencies
   - Verify database connectivity
   - Review test configuration

3. **Deployment Issues**
   - Check health check endpoints
   - Verify environment variables
   - Review load balancer configuration

4. **Performance Issues**
   - Monitor resource usage
   - Check database connection pooling
   - Review caching configuration

### Debug Commands

```bash
# Check container health
docker ps -a
docker inspect <container_name>

# Review logs
docker logs <container_name>
docker-compose logs <service_name>

# Test connectivity
docker exec <container_name> curl -f http://localhost:8009/health

# Database connectivity
docker exec <container_name> pg_isready -h postgres -U eduplatform
```

## Security Considerations

### Best Practices

1. **Secrets Management**: Never commit secrets to version control
2. **Image Scanning**: Regular vulnerability assessments
3. **Network Security**: Isolated container networks
4. **Access Control**: Principle of least privilege
5. **Audit Logging**: Comprehensive deployment logs

### Security Checklist

- [ ] All secrets stored securely
- [ ] Container images regularly scanned
- [ ] Network policies enforced
- [ ] Access controls configured
- [ ] Audit logging enabled
- [ ] Security policies updated

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review security scan results
   - Update base images
   - Monitor resource usage

2. **Monthly**
   - Dependency updates
   - Performance optimization
   - Documentation updates

3. **Quarterly**
   - Security audit
   - Disaster recovery testing
   - Architecture review

### Monitoring Alerts

Key metrics to monitor:
- **Response Times**: API endpoint performance
- **Error Rates**: Application error frequency
- **Resource Usage**: CPU, memory, disk utilization
- **Security Events**: Failed authentication attempts

## Future Enhancements

### Planned Improvements

1. **Multi-Cloud Support**: AWS, Azure, GCP deployment options
2. **Canary Deployments**: Gradual rollout strategy
3. **Infrastructure as Code**: Terraform/Pulumi integration
4. **Advanced Monitoring**: Distributed tracing with Jaeger
5. **Chaos Engineering**: Resilience testing with Chaos Monkey

### Roadmap

- **Q1 2026**: Multi-cloud deployment support
- **Q2 2026**: Advanced observability stack
- **Q3 2026**: Automated scaling and optimization
- **Q4 2026**: Machine learning-based performance tuning

---

*This documentation is maintained by the ToolBoxAI DevOps team. For questions or updates, please contact the development team or create an issue in the repository.*