# Security Remediation Scripts
## Immediate Action Scripts for ToolBoxAI-Solutions Docker Security

---

## 🚨 CRITICAL: Secrets Management Setup

### 1. Generate Secure Secrets Script
```bash
#!/bin/bash
# File: scripts/security/generate-secrets.sh
set -euo pipefail

echo "🔐 Generating secure secrets for ToolBoxAI..."

# Create secrets directory
mkdir -p secrets/

# Generate database password
echo "Generating database password..."
openssl rand -base64 32 > secrets/postgres_password.txt

# Generate JWT secret
echo "Generating JWT secret..."
openssl rand -hex 64 > secrets/jwt_secret.txt

# Generate Redis password  
echo "Generating Redis password..."
openssl rand -base64 24 > secrets/redis_password.txt

# Generate API keys (placeholders - replace with real keys)
echo "your-secure-openai-key-here" > secrets/openai_api_key.txt
echo "your-secure-anthropic-key-here" > secrets/anthropic_api_key.txt
echo "your-secure-pusher-secret-here" > secrets/pusher_secret.txt

# Set proper permissions
chmod 600 secrets/*.txt

echo "✅ Secrets generated successfully!"
echo "⚠️  IMPORTANT: Update API keys with real values before production!"
echo "⚠️  IMPORTANT: Add secrets/ to .gitignore!"

# Add to gitignore if not already there
if ! grep -q "secrets/" .gitignore 2>/dev/null; then
    echo "secrets/" >> .gitignore
    echo "✅ Added secrets/ to .gitignore"
fi
```

### 2. Docker Secrets Setup Script
```bash
#!/bin/bash
# File: scripts/security/setup-docker-secrets.sh
set -euo pipefail

echo "🐳 Setting up Docker Secrets..."

# Check if secrets directory exists
if [ ! -d "secrets/" ]; then
    echo "❌ Secrets directory not found. Run generate-secrets.sh first!"
    exit 1
fi

# Create Docker secrets
echo "Creating Docker secrets..."
docker secret create postgres_password secrets/postgres_password.txt 2>/dev/null || echo "⚠️  postgres_password secret already exists"
docker secret create jwt_secret secrets/jwt_secret.txt 2>/dev/null || echo "⚠️  jwt_secret secret already exists"
docker secret create redis_password secrets/redis_password.txt 2>/dev/null || echo "⚠️  redis_password secret already exists"
docker secret create openai_api_key secrets/openai_api_key.txt 2>/dev/null || echo "⚠️  openai_api_key secret already exists"
docker secret create anthropic_api_key secrets/anthropic_api_key.txt 2>/dev/null || echo "⚠️  anthropic_api_key secret already exists"
docker secret create pusher_secret secrets/pusher_secret.txt 2>/dev/null || echo "⚠️  pusher_secret secret already exists"

echo "✅ Docker secrets created successfully!"
echo "🔍 List of created secrets:"
docker secret ls
```

### 3. Environment File Cleanup Script
```bash
#!/bin/bash
# File: scripts/security/cleanup-env-files.sh
set -euo pipefail

echo "🧹 Cleaning up environment files..."

# Backup existing .env files
for env_file in .env .env.* apps/backend/.env apps/dashboard/.env; do
    if [ -f "$env_file" ]; then
        cp "$env_file" "${env_file}.backup.$(date +%Y%m%d-%H%M%S)"
        echo "✅ Backed up $env_file"
    fi
done

# Create secure .env template
cat > .env.secure << 'ENVEOF'
# ============================================
# SECURE TOOLBOXAI ENVIRONMENT CONFIGURATION  
# ============================================
# Updated: $(date)
# IMPORTANT: All sensitive values use Docker Secrets

# ============================================
# DATABASE CONFIGURATION (Non-sensitive)
# ============================================
POSTGRES_DB=educational_platform_dev
POSTGRES_USER=toolboxai_user
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis Configuration (Non-sensitive)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_SOCKET_TIMEOUT=5

# ============================================
# APPLICATION CONFIGURATION
# ============================================
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8009
WORKERS=4

# ============================================
# FEATURE FLAGS
# ============================================
ENABLE_WEBSOCKET=true
ENABLE_GAMIFICATION=true
ENABLE_ANALYTICS=true
PUSHER_ENABLED=true
PUSHER_CLUSTER=us2

# ============================================
# SECURITY NOTICE
# ============================================
# Sensitive values are managed via Docker Secrets:
# - POSTGRES_PASSWORD -> /run/secrets/postgres_password
# - JWT_SECRET_KEY -> /run/secrets/jwt_secret
# - REDIS_PASSWORD -> /run/secrets/redis_password
# - OPENAI_API_KEY -> /run/secrets/openai_api_key
# - ANTHROPIC_API_KEY -> /run/secrets/anthropic_api_key
# - PUSHER_SECRET -> /run/secrets/pusher_secret
ENVEOF

echo "✅ Created secure .env template"
echo "⚠️  Review and update .env.secure, then rename to .env"
```

---

## 🛡️ Container Hardening Scripts

### 4. Docker Compose Security Hardening
```yaml
# File: infrastructure/docker/docker-compose.security-override.yml
# Use with: docker-compose -f docker-compose.dev.yml -f docker-compose.security-override.yml up

version: '3.9'

services:
  postgres:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - FOWNER
      - SETGID
      - SETUID
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    user: "999:999"
    
  redis:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    user: "999:999"
    
  fastapi-main:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
    user: "1001:1001"
    secrets:
      - postgres_password
      - jwt_secret
      - redis_password
      - openai_api_key
      - anthropic_api_key
      - pusher_secret
    environment:
      # Override to use secrets
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      JWT_SECRET_KEY_FILE: /run/secrets/jwt_secret
      REDIS_PASSWORD_FILE: /run/secrets/redis_password
      OPENAI_API_KEY_FILE: /run/secrets/openai_api_key
      ANTHROPIC_API_KEY_FILE: /run/secrets/anthropic_api_key
      PUSHER_SECRET_FILE: /run/secrets/pusher_secret
      
  dashboard-frontend:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
    user: "1001:1001"

secrets:
  postgres_password:
    external: true
  jwt_secret:
    external: true
  redis_password:
    external: true
  openai_api_key:
    external: true
  anthropic_api_key:
    external: true
  pusher_secret:
    external: true
```

### 5. Network Security Setup Script
```bash
#!/bin/bash
# File: scripts/security/setup-network-security.sh
set -euo pipefail

echo "🌐 Setting up network security..."

# Create secure networks
docker network create --driver bridge \
  --subnet=172.20.0.0/16 \
  --ip-range=172.20.240.0/20 \
  toolboxai-frontend || echo "Frontend network exists"

docker network create --driver bridge \
  --subnet=172.21.0.0/16 \
  --ip-range=172.21.240.0/20 \
  --internal \
  toolboxai-backend || echo "Backend network exists"

docker network create --driver bridge \
  --subnet=172.22.0.0/16 \
  --ip-range=172.22.240.0/20 \
  --internal \
  toolboxai-database || echo "Database network exists"

echo "✅ Secure networks created"
echo "🔍 Network list:"
docker network ls | grep toolboxai
```

---

## 🔍 Security Validation Scripts

### 6. Security Audit Script
```bash
#!/bin/bash
# File: scripts/security/security-audit.sh
set -euo pipefail

echo "🔍 Running security audit..."

# Check for hardcoded secrets
echo "Checking for hardcoded secrets..."
if command -v trufflehog >/dev/null; then
    trufflehog git file://. --only-verified --json > security-audit-secrets.json
    echo "✅ Secret scan completed - check security-audit-secrets.json"
else
    echo "⚠️  trufflehog not found - skipping secret scan"
fi

# Check Docker bench security
echo "Running Docker bench security..."
if command -v docker >/dev/null; then
    docker run --rm --net host --pid host --userns host --cap-add audit_control \
        -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
        -v /var/lib:/var/lib:ro \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        --label docker_bench_security \
        docker/docker-bench-security > security-audit-docker-bench.log 2>&1
    echo "✅ Docker bench completed - check security-audit-docker-bench.log"
fi

# Check for vulnerable dependencies
echo "Checking for vulnerable dependencies..."
if [ -f "requirements.txt" ]; then
    if command -v safety >/dev/null; then
        safety check -r requirements.txt --json > security-audit-python.json
        echo "✅ Python dependency scan completed"
    else
        echo "⚠️  safety not found - install with: pip install safety"
    fi
fi

if [ -f "package.json" ]; then
    if command -v npm >/dev/null; then
        npm audit --audit-level moderate --json > security-audit-npm.json
        echo "✅ NPM audit completed"
    fi
fi

# Check container images for vulnerabilities
echo "Scanning container images..."
if command -v trivy >/dev/null; then
    for dockerfile in $(find . -name "Dockerfile*" -not -path "./node_modules/*"); do
        image_name=$(basename $(dirname $dockerfile))
        echo "Scanning $dockerfile..."
        trivy config $dockerfile > "security-audit-trivy-${image_name}.json"
    done
    echo "✅ Image vulnerability scan completed"
else
    echo "⚠️  trivy not found - install with: brew install trivy"
fi

echo "🎯 Security audit completed!"
echo "📊 Review the following files:"
ls -la security-audit-*.{json,log} 2>/dev/null || echo "No audit files generated"
```

### 7. Secrets Validation Script
```bash
#!/bin/bash
# File: scripts/security/validate-secrets.sh
set -euo pipefail

echo "🔐 Validating secrets configuration..."

# Check if Docker secrets exist
required_secrets=("postgres_password" "jwt_secret" "redis_password" "openai_api_key" "anthropic_api_key" "pusher_secret")

for secret in "${required_secrets[@]}"; do
    if docker secret ls | grep -q "$secret"; then
        echo "✅ Secret '$secret' exists"
    else
        echo "❌ Secret '$secret' missing"
        exit 1
    fi
done

# Check for hardcoded values in compose files
echo "Checking for hardcoded values in compose files..."
hardcoded_patterns=("eduplatform2024" "your-key-here" "changeme" "password123" "secret123")

for pattern in "${hardcoded_patterns[@]}"; do
    if grep -r "$pattern" infrastructure/docker/ >/dev/null 2>&1; then
        echo "❌ Found hardcoded value: $pattern"
        echo "🔍 Locations:"
        grep -r "$pattern" infrastructure/docker/ || true
    else
        echo "✅ No hardcoded '$pattern' found"
    fi
done

# Validate secret file permissions
if [ -d "secrets/" ]; then
    echo "Checking secret file permissions..."
    for file in secrets/*.txt; do
        if [ -f "$file" ]; then
            perms=$(stat -f "%A" "$file" 2>/dev/null || stat -c "%a" "$file" 2>/dev/null)
            if [ "$perms" = "600" ]; then
                echo "✅ $file has correct permissions (600)"
            else
                echo "⚠️  $file has permissions $perms (should be 600)"
                chmod 600 "$file"
                echo "✅ Fixed permissions for $file"
            fi
        fi
    done
fi

echo "🎯 Secrets validation completed!"
```

---

## 🚀 Quick Deployment Script

### 8. Secure Deployment Script
```bash
#!/bin/bash
# File: scripts/security/secure-deploy.sh
set -euo pipefail

echo "🚀 Starting secure deployment..."

# Step 1: Generate secrets if not exists
if [ ! -d "secrets/" ]; then
    echo "🔐 Generating secrets..."
    bash scripts/security/generate-secrets.sh
fi

# Step 2: Setup Docker secrets
echo "🐳 Setting up Docker secrets..."
bash scripts/security/setup-docker-secrets.sh

# Step 3: Setup networks
echo "🌐 Setting up secure networks..."
bash scripts/security/setup-network-security.sh

# Step 4: Validate configuration
echo "🔍 Validating security configuration..."
bash scripts/security/validate-secrets.sh

# Step 5: Deploy with security overrides
echo "🛡️ Deploying with security hardening..."
docker-compose -f infrastructure/docker/docker-compose.dev.yml \
               -f infrastructure/docker/docker-compose.security-override.yml \
               up -d

# Step 6: Run security audit
echo "🔍 Running post-deployment security check..."
sleep 30  # Wait for containers to start
bash scripts/security/security-audit.sh

echo "✅ Secure deployment completed!"
echo "🔍 Check security audit results in security-audit-*.json files"
```

### 9. Security Monitoring Setup
```bash
#!/bin/bash
# File: scripts/security/setup-monitoring.sh
set -euo pipefail

echo "📊 Setting up security monitoring..."

# Create monitoring configuration
mkdir -p monitoring/security

# Falco configuration for runtime security
cat > monitoring/security/falco-rules.yaml << 'FALCOEOF'
- rule: Shell in container
  desc: Detect shell execution in container
  condition: >
    spawned_process and container and
    (proc.name in (sh, bash, zsh, dash) or
     proc.pname in (sh, bash, zsh, dash))
  output: >
    Shell spawned in container (user=%user.name container=%container.name 
    image=%container.image.repository:%container.image.tag shell=%proc.name 
    parent=%proc.pname cmdline=%proc.cmdline terminal=%proc.tty)
  priority: WARNING

- rule: Unexpected network connection
  desc: Detect unexpected network connections from containers
  condition: >
    inbound_outbound and container and
    not fd.net.lproto in (tcp, udp) and
    not proc.name in (nginx, uvicorn, redis-server, postgres)
  output: >
    Unexpected network connection (user=%user.name container=%container.name
    image=%container.image.repository direction=%evt.type protocol=%fd.net.lproto
    local=%fd.net.lip:%fd.net.lport remote=%fd.net.rip:%fd.net.rport)
  priority: WARNING

- rule: Write to system directories
  desc: Detect writes to system directories
  condition: >
    open_write and container and
    (fd.name startswith /bin or
     fd.name startswith /etc or
     fd.name startswith /usr/bin or
     fd.name startswith /sbin)
  output: >
    Write to system directory (user=%user.name container=%container.name
    image=%container.image.repository file=%fd.name)
  priority: CRITICAL
FALCOEOF

# Prometheus alerting rules for security
cat > monitoring/security/security-alerts.yml << 'PROMETHEUSEOF'
groups:
  - name: docker-security
    rules:
    - alert: ContainerHighCPU
      expr: rate(container_cpu_usage_seconds_total[1m]) > 0.8
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Container {{ $labels.name }} high CPU usage"
        
    - alert: ContainerMemoryUsage
      expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Container {{ $labels.name }} high memory usage"
        
    - alert: ContainerDown
      expr: up == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Container {{ $labels.instance }} is down"
PROMETHEUSEOF

echo "✅ Security monitoring configuration created"
echo "📝 Next steps:"
echo "  1. Deploy Falco: helm install falco falcosecurity/falco"
echo "  2. Configure Prometheus to use security-alerts.yml"
echo "  3. Set up Grafana dashboards for security metrics"
```

---

## 📋 Security Checklist

### Daily Security Checks
```bash
#!/bin/bash
# File: scripts/security/daily-security-check.sh

echo "📋 Daily Security Checklist"
echo "=========================="

# 1. Check for container anomalies
echo "🔍 Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20

# 2. Check resource usage
echo "🔍 Checking resource usage..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 3. Check for failed login attempts (if logs are available)
echo "🔍 Checking authentication logs..."
docker-compose logs --tail=100 fastapi-main | grep -i "failed\|error\|unauthorized" | tail -10 || echo "No auth errors found"

# 4. Validate secrets are still secure
echo "🔍 Validating secrets..."
docker secret ls | wc -l | xargs echo "Active secrets:"

# 5. Check for security updates
echo "🔍 Checking for security updates..."
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | head -10

echo "✅ Daily security check completed"
```

---

## 🆘 Emergency Response Scripts

### Security Incident Response
```bash
#!/bin/bash
# File: scripts/security/incident-response.sh
set -euo pipefail

echo "🚨 SECURITY INCIDENT RESPONSE ACTIVATED"
echo "======================================"

# 1. Stop all containers immediately
echo "⚠️  Stopping all containers..."
docker-compose down

# 2. Rotate all secrets
echo "🔐 Rotating all secrets..."
bash scripts/security/generate-secrets.sh
bash scripts/security/setup-docker-secrets.sh

# 3. Capture forensic information
echo "🔍 Capturing forensic information..."
docker system df > incident-forensics-$(date +%Y%m%d-%H%M%S).log
docker system events --since="24h" >> incident-forensics-$(date +%Y%m%d-%H%M%S).log

# 4. Clean potentially compromised images
echo "🧹 Cleaning potentially compromised images..."
docker system prune -af

# 5. Restart with maximum security
echo "🛡️ Restarting with maximum security..."
docker-compose -f infrastructure/docker/docker-compose.dev.yml \
               -f infrastructure/docker/docker-compose.security-override.yml \
               up -d

echo "✅ Incident response completed"
echo "📝 Review incident-forensics-*.log files"
echo "📞 Contact security team if needed"
```

---

## 📚 Usage Instructions

1. **Make scripts executable:**
```bash
chmod +x scripts/security/*.sh
```

2. **Run initial security setup:**
```bash
bash scripts/security/secure-deploy.sh
```

3. **Set up monitoring:**
```bash
bash scripts/security/setup-monitoring.sh
```

4. **Run daily security checks:**
```bash
bash scripts/security/daily-security-check.sh
```

5. **In case of security incident:**
```bash
bash scripts/security/incident-response.sh
```

---

**⚠️ IMPORTANT NOTES:**
- Always test scripts in development environment first
- Keep backup copies of all configurations
- Review and update API keys before production deployment
- Monitor security logs regularly
- Keep this documentation updated with any changes

