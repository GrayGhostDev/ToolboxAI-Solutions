# Infrastructure Security Guide

## 🛡️ Overview

This document outlines security best practices, secret management, and compliance requirements for the ToolBoxAI infrastructure.

## 🚨 Critical Security Requirements

### Secret Management

**NEVER commit secrets to Git!** All sensitive information must be managed through proper channels:

#### Production Secrets Management
- **AWS**: AWS Secrets Manager or AWS Systems Manager Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Google Secret Manager
- **Kubernetes**: Kubernetes Secrets with encryption at rest
- **Docker Swarm**: Docker Secrets

#### Development Secrets
- Use `.env` files (excluded from Git)
- Use Docker secrets for local development
- Use environment variables for CI/CD

### Docker Secrets Setup

1. **Create secrets directory** (one-time setup):
   ```bash
   cd infrastructure/docker
   cp -r secrets.example/ secrets/
   cd secrets/
   ```

2. **Generate secure passwords**:
   ```bash
   # Database password (32 chars, mixed)
   openssl rand -base64 32 | tr -d "=+/" | cut -c1-32 > db_password
   
   # Redis password (32 chars, mixed)
   openssl rand -base64 32 | tr -d "=+/" | cut -c1-32 > redis_password
   
   # JWT secret (64 chars)
   openssl rand -base64 64 | tr -d "=+/" | cut -c1-64 > jwt_secret
   ```

3. **Create Docker secrets**:
   ```bash
   # Create external secrets for Docker Compose
   docker secret create db_password secrets/db_password
   docker secret create redis_password secrets/redis_password
   docker secret create jwt_secret secrets/jwt_secret
   
   # For API keys, create from environment
   echo "$OPENAI_API_KEY" | docker secret create openai_api_key -
   echo "$ANTHROPIC_API_KEY" | docker secret create anthropic_api_key -
   ```

## 🔐 Password Requirements

### Minimum Standards
- **Length**: 32 characters minimum
- **Complexity**: Mixed case, numbers, special characters
- **Uniqueness**: Different password per service
- **Rotation**: Quarterly for production systems

### Secure Generation Commands
```bash
# Strong password (32 chars)
openssl rand -base64 32 | tr -d "=+/" | cut -c1-32

# Extra strong password (64 chars)
openssl rand -base64 64 | tr -d "=+/" | cut -c1-64

# Alphanumeric only (for compatibility)
cat /dev/urandom | LC_CTYPE=C tr -dc 'a-zA-Z0-9' | head -c 32

# With special characters
cat /dev/urandom | LC_CTYPE=C tr -dc 'a-zA-Z0-9!@#$%^&*()_+-=' | head -c 32
```

## 🏗️ Infrastructure Security Architecture

### Network Security
- **Network Segmentation**: Separate networks for frontend, backend, database, cache
- **Internal Networks**: Database and cache networks are internal-only
- **Firewall Rules**: Minimal required ports exposed
- **TLS Encryption**: All external communication encrypted

### Container Security
- **Non-root Users**: All containers run as non-root
- **Read-only Filesystems**: Containers use read-only root filesystems
- **Security Contexts**: Dropped capabilities, no new privileges
- **Resource Limits**: CPU and memory limits enforced
- **Image Scanning**: All images scanned for vulnerabilities

### Data Security
- **Encryption at Rest**: Database volumes encrypted
- **Encryption in Transit**: TLS for all connections
- **Backup Encryption**: All backups encrypted
- **Secret Rotation**: Regular rotation schedule

## 🚀 Environment-Specific Security

### Development Environment
```bash
# Use weak passwords only for local development
export POSTGRES_PASSWORD="devpass2024"
export REDIS_PASSWORD="" # No password for dev Redis
export JWT_SECRET_KEY="dev-secret-key-change-in-production"
```

### Staging Environment
```bash
# Use staging-specific strong passwords
export POSTGRES_PASSWORD="$(cat /run/secrets/staging_db_password)"
export REDIS_PASSWORD="$(cat /run/secrets/staging_redis_password)"
export JWT_SECRET_KEY="$(cat /run/secrets/staging_jwt_secret)"
```

### Production Environment
```bash
# Use production secrets from secret management service
export POSTGRES_PASSWORD="$(aws secretsmanager get-secret-value --secret-id prod/db/password --query SecretString --output text)"
export REDIS_PASSWORD="$(aws secretsmanager get-secret-value --secret-id prod/redis/password --query SecretString --output text)"
export JWT_SECRET_KEY="$(aws secretsmanager get-secret-value --secret-id prod/jwt/secret --query SecretString --output text)"
```

## 🔍 Security Monitoring

### Implemented Monitoring
- **Failed Authentication Attempts**: Monitored and alerted
- **Suspicious Database Queries**: Logged and analyzed
- **Resource Usage Anomalies**: Monitored for DDoS/resource exhaustion
- **Certificate Expiration**: Automated monitoring and renewal
- **Vulnerability Scanning**: Regular automated scans

### Security Metrics
- Authentication success/failure rates
- API endpoint response times and error rates
- Database connection patterns
- Network traffic anomalies
- Container resource usage

## 🛠️ Security Tools and Utilities

### Vulnerability Scanning
```bash
# Scan Docker images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image toolboxai/backend:latest

# Scan infrastructure code
checkov -d infrastructure/

# Scan for secrets in code
trufflehog git file://. --only-verified
```

### Security Testing
```bash
# Test TLS configuration
testssl.sh your-domain.com

# Test API security
zap-baseline.py -t https://your-api.com

# Test container security
docker run --rm -it --cap-add=SYS_ADMIN \
  -v /var/lib/docker:/var/lib/docker \
  aquasec/docker-bench-security
```

## 📋 Security Checklist

### Pre-Deployment Security Review
- [ ] No hardcoded secrets in code
- [ ] All containers run as non-root
- [ ] Network segmentation implemented
- [ ] TLS certificates valid and current
- [ ] Secret rotation schedule implemented
- [ ] Monitoring and alerting configured
- [ ] Backup encryption verified
- [ ] Vulnerability scan completed
- [ ] Penetration testing completed
- [ ] Security documentation updated

### Regular Security Maintenance
- [ ] Weekly vulnerability scans
- [ ] Monthly access review
- [ ] Quarterly password rotation
- [ ] Semi-annual penetration testing
- [ ] Annual security architecture review

## 🔄 Incident Response

### Security Incident Procedure
1. **Immediate Response**
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Assessment**
   - Determine scope of breach
   - Identify compromised data
   - Assess business impact

3. **Containment**
   - Stop ongoing attack
   - Patch vulnerabilities
   - Rotate all potentially compromised secrets

4. **Recovery**
   - Restore systems from clean backups
   - Verify system integrity
   - Implement additional monitoring

5. **Post-Incident**
   - Document lessons learned
   - Update security procedures
   - Conduct security training

### Emergency Contacts
- **Security Team**: security@toolboxai.com
- **Incident Response**: incidents@toolboxai.com
- **Management**: management@toolboxai.com

## 📚 Compliance and Standards

### Standards Compliance
- **OWASP Top 10**: Application security practices
- **NIST Cybersecurity Framework**: Overall security strategy
- **CIS Controls**: Infrastructure security baselines
- **ISO 27001**: Information security management

### Data Protection
- **GDPR**: EU data protection requirements
- **CCPA**: California consumer privacy act
- **COPPA**: Children's online privacy protection

### Industry Standards
- **SOC 2 Type II**: Service organization controls
- **PCI DSS**: Payment card industry standards (if applicable)
- **HIPAA**: Healthcare information protection (if applicable)

## 🎓 Security Training Resources

### Required Reading
- [OWASP Application Security Guide](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

### Internal Training
- Monthly security awareness sessions
- Quarterly incident response drills
- Annual penetration testing reviews

## 📈 Security Metrics and KPIs

### Key Performance Indicators
- Mean Time to Detection (MTTD): < 1 hour
- Mean Time to Response (MTTR): < 4 hours
- Vulnerability Remediation: < 48 hours (critical), < 7 days (high)
- Security Training Completion: 100% annual
- Penetration Test Findings: Decreasing trend

### Reporting
- Daily: Security event summaries
- Weekly: Vulnerability scan reports
- Monthly: Security posture dashboard
- Quarterly: Executive security briefing
- Annually: Security program assessment

---

**Last Updated**: 2025-09-26  
**Next Review**: 2025-12-26  
**Owner**: Security Team  
**Approved By**: CISO
