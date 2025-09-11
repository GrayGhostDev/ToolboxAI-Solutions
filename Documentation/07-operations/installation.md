# Installation Guide

This comprehensive guide covers the installation and initial setup of ToolBoxAI-Solutions for different deployment scenarios.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Production Installation](#production-installation)
5. [Development Installation](#development-installation)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

#### Core Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS 11+, or Windows Server 2019+
- **Python**: 3.10 or higher
- **Node.js**: 18.x LTS or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 6.2 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Kubernetes**: 1.24+ (for orchestrated deployment)

#### Additional Tools

```bash
# Package managers
- pip 22.0+
- npm 8.0+
- yarn 1.22+ (optional, alternative to npm)

# Build tools
- git 2.30+
- make 4.0+
- gcc/g++ (for native dependencies)

# Monitoring (optional but recommended)
- Prometheus
- Grafana
- Elasticsearch
```

### Service Accounts

Create dedicated service accounts:

```bash
# Create application user
sudo useradd -m -s /bin/bash toolboxai
sudo usermod -aG sudo toolboxai

# Set up directory permissions
sudo mkdir -p /opt/toolboxai
sudo chown -R toolboxai:toolboxai /opt/toolboxai
```

### Network Requirements

Open the following ports:

| Port | Service    | Protocol | Direction |
| ---- | ---------- | -------- | --------- |
| 80   | HTTP       | TCP      | Inbound   |
| 443  | HTTPS      | TCP      | Inbound   |
| 5432 | PostgreSQL | TCP      | Internal  |
| 6379 | Redis      | TCP      | Internal  |
| 8000 | API Server | TCP      | Internal  |
| 3000 | Web UI     | TCP      | Internal  |
| 9090 | Prometheus | TCP      | Internal  |
| 3100 | Grafana    | TCP      | Internal  |

## System Requirements

### Minimum Requirements (Development)

```yaml
CPU: 2 cores (2.4 GHz+)
RAM: 4 GB
Storage: 20 GB SSD
Network: 10 Mbps
OS: Ubuntu 20.04 / macOS 11 / Windows 10
```

### Recommended Requirements (Production)

```yaml
CPU: 8 cores (3.0 GHz+)
RAM: 16 GB
Storage: 100 GB SSD
Network: 100 Mbps
OS: Ubuntu 22.04 LTS
Database: Dedicated PostgreSQL server
Cache: Dedicated Redis server
```

### Enterprise Requirements (1000+ users)

```yaml
CPU: 16+ cores
RAM: 32+ GB
Storage: 500 GB+ SSD (RAID 10)
Network: 1 Gbps
Load Balancer: Nginx/HAProxy
Database: PostgreSQL cluster
Cache: Redis cluster
CDN: CloudFlare/AWS CloudFront
```

## Installation Methods

### Method 1: Docker Compose (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/toolboxai/solutions.git
cd solutions

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Method 2: Kubernetes (Recommended for Production)

```bash
# Add Helm repository
helm repo add toolboxai https://charts.toolboxai.com
helm repo update

# Install with custom values
helm install toolboxai toolboxai/solutions \
  --namespace toolboxai \
  --create-namespace \
  --values values.yaml
```

### Method 3: Manual Installation

See [Production Installation](#production-installation) below.

## Production Installation

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  build-essential \
  curl \
  wget \
  git \
  nginx \
  supervisor \
  ufw \
  certbot \
  python3-certbot-nginx

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Step 2: Install Python and Dependencies

```bash
# Install Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# Create virtual environment
cd /opt/toolboxai
python3.10 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 3: Install Node.js and Frontend

```bash
# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build frontend
cd /opt/toolboxai/frontend
npm ci --production
npm run build

# Copy static files
sudo cp -r dist/* /var/www/toolboxai/
```

### Step 4: Database Setup

```bash
# Install PostgreSQL
sudo apt install -y postgresql-14 postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE toolboxai;
CREATE USER toolboxai_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE toolboxai TO toolboxai_user;
ALTER DATABASE toolboxai OWNER TO toolboxai_user;
EOF

# Configure PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = 'localhost'
# Set: max_connections = 200
# Set: shared_buffers = 256MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 5: Redis Setup

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru
# Set: bind 127.0.0.1
# Set: protected-mode yes

# Set Redis password
echo "requirepass your_redis_password" | sudo tee -a /etc/redis/redis.conf

# Restart Redis
sudo systemctl restart redis-server
```

### Step 6: Configure Application

```bash
# Create configuration directory
sudo mkdir -p /etc/toolboxai

# Create main configuration
sudo nano /etc/toolboxai/config.yaml
```

```yaml
# /etc/toolboxai/config.yaml
app:
  name: ToolBoxAI-Solutions
  environment: production
  debug: false
  secret_key: ${SECRET_KEY}

database:
  host: localhost
  port: 5432
  name: toolboxai
  user: toolboxai_user
  password: ${DB_PASSWORD}
  pool_size: 20

redis:
  host: localhost
  port: 6379
  password: ${REDIS_PASSWORD}
  db: 0

api:
  host: 127.0.0.1
  port: 8000
  workers: 4
  timeout: 30

security:
  cors_origins:
    - https://yourdomain.com
  jwt_expire_minutes: 60
  password_min_length: 12

storage:
  type: s3
  bucket: toolboxai-storage
  region: us-east-1

logging:
  level: INFO
  file: /var/log/toolboxai/app.log
  max_size: 100MB
  backup_count: 10
```

### Step 7: Set Up Services

```bash
# Create systemd service for API
sudo nano /etc/systemd/system/toolboxai-api.service
```

```ini
[Unit]
Description=ToolBoxAI API Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=toolboxai
Group=toolboxai
WorkingDirectory=/opt/toolboxai
Environment="PATH=/opt/toolboxai/venv/bin"
ExecStart=/opt/toolboxai/venv/bin/uvicorn main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-config /etc/toolboxai/logging.yaml

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create worker service
sudo nano /etc/systemd/system/toolboxai-worker.service
```

```ini
[Unit]
Description=ToolBoxAI Background Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=toolboxai
Group=toolboxai
WorkingDirectory=/opt/toolboxai
Environment="PATH=/opt/toolboxai/venv/bin"
ExecStart=/opt/toolboxai/venv/bin/celery -A app.worker worker \
    --loglevel=info \
    --concurrency=4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 8: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/toolboxai
```

```nginx
upstream toolboxai_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:;" always;

    # Static files
    location / {
        root /var/www/toolboxai;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://toolboxai_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Media files
    location /media {
        alias /opt/toolboxai/media;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Monitoring endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/toolboxai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up SSL
sudo certbot --nginx -d yourdomain.com
```

### Step 9: Initialize Database

```bash
# Run migrations
cd /opt/toolboxai
source venv/bin/activate
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py loaddata initial_data.json

# Collect static files
python manage.py collectstatic --noinput
```

### Step 10: Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable toolboxai-api
sudo systemctl enable toolboxai-worker
sudo systemctl enable postgresql
sudo systemctl enable redis-server
sudo systemctl enable nginx

# Start services
sudo systemctl start toolboxai-api
sudo systemctl start toolboxai-worker

# Check status
sudo systemctl status toolboxai-api
sudo systemctl status toolboxai-worker
```

## Development Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/toolboxai/solutions.git
cd solutions

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Frontend setup
cd frontend
npm install

# Database setup (using Docker)
docker run -d \
  --name toolboxai-postgres \
  -e POSTGRES_DB=toolboxai \
  -e POSTGRES_USER=developer \
  -e POSTGRES_PASSWORD=devpass \
  -p 5432:5432 \
  postgres:14

# Redis setup (using Docker)
docker run -d \
  --name toolboxai-redis \
  -p 6379:6379 \
  redis:6-alpine

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Start development servers
# Terminal 1: Backend
python manage.py runserver

# Terminal 2: Frontend
npm run dev

# Terminal 3: Worker
celery -A app.worker worker --loglevel=debug
```

## Configuration

### Environment Variables

```bash
# Application
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=your-secret-key-here
API_URL=https://api.yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/toolboxai
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# Authentication
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AWS (for S3 storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=toolboxai-storage
AWS_REGION=us-east-1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@yourdomain.com
SMTP_PASSWORD=your-password
EMAIL_FROM=ToolBoxAI <noreply@yourdomain.com>

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
PROMETHEUS_ENABLED=true
GRAFANA_API_KEY=your-grafana-key

# LMS Integration
CANVAS_API_URL=https://your-school.instructure.com/api/v1
CANVAS_API_KEY=your-canvas-key

SCHOOLOGY_CONSUMER_KEY=your-key
SCHOOLOGY_CONSUMER_SECRET=your-secret

GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret

# Roblox
ROBLOX_API_KEY=your-roblox-key
ROBLOX_WEBHOOK_SECRET=your-webhook-secret
```

### Configuration Files

Create these configuration files:

#### logging.yaml

```yaml
version: 1
disable_existing_loggers: false

formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /var/log/toolboxai/app.log
    maxBytes: 104857600 # 100MB
    backupCount: 10

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: /var/log/toolboxai/error.log
    maxBytes: 104857600
    backupCount: 10

root:
  level: INFO
  handlers: [console, file, error_file]

loggers:
  uvicorn.access:
    level: INFO
    handlers: [console]
    propagate: no

  sqlalchemy.engine:
    level: WARNING
    handlers: [file]
    propagate: no
```

## Verification

### Step 1: Check Services

```bash
# Check service status
sudo systemctl status toolboxai-api
sudo systemctl status toolboxai-worker
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx

# Check ports
sudo netstat -tlpn | grep -E '(80|443|8000|5432|6379)'

# Check logs
sudo journalctl -u toolboxai-api -f
sudo tail -f /var/log/toolboxai/app.log
```

### Step 2: Test Endpoints

```bash
# Health check
curl https://yourdomain.com/health

# API status
curl https://yourdomain.com/api/status

# Frontend
curl -I https://yourdomain.com

# WebSocket test
wscat -c wss://yourdomain.com/ws
```

### Step 3: Run Test Suite

```bash
# Backend tests
cd /opt/toolboxai
source venv/bin/activate
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
python manage.py test integration

# Load testing
locust -f tests/load_test.py --host=https://yourdomain.com
```

### Step 4: Verify Integrations

```python
# Test LMS connections
python manage.py test_lms_connection --all

# Test Roblox plugin
python manage.py test_roblox_integration

# Test email
python manage.py sendtestemail admin@yourdomain.com

# Test storage
python manage.py test_storage
```

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U toolboxai_user -d toolboxai -h localhost

# Check pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure: local all all md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Redis Connection Failed

```bash
# Check Redis is running
sudo systemctl status redis-server

# Test connection
redis-cli ping

# With password
redis-cli -a your_password ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### API Server Won't Start

```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for port conflicts
sudo lsof -i :8000

# Run in debug mode
python manage.py runserver --debug
```

#### Frontend Build Fails

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Check Node version
node --version  # Should be 18.x
```

#### SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run

# Check certificate
sudo openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout
```

### Performance Issues

```bash
# Check system resources
htop
df -h
free -m

# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Optimize PostgreSQL
sudo -u postgres psql -c "VACUUM ANALYZE;"

# Check Redis memory
redis-cli INFO memory

# Monitor API performance
python manage.py monitor_performance
```

### Security Audit

```bash
# Run security scan
python manage.py security_audit

# Check for vulnerabilities
pip audit
npm audit

# Update dependencies
pip install --upgrade -r requirements.txt
npm update

# Check file permissions
find /opt/toolboxai -type f -perm 0777
find /opt/toolboxai -type d -perm 0777
```

## Next Steps

After successful installation:

1. **Configure monitoring** - Set up Prometheus and Grafana dashboards
2. **Set up backups** - Configure automated database and file backups
3. **Configure CDN** - Set up CloudFlare or AWS CloudFront
4. **Enable logging** - Configure centralized logging with ELK stack
5. **Security hardening** - Run security audit and apply recommendations
6. **Load testing** - Test system capacity and optimize
7. **Documentation** - Update deployment documentation with specifics

For detailed configuration options, see [Configuration Guide](configuration.md).
For deployment strategies, see [Deployment Guide](../04-implementation/deployment.md).

---

_Last updated: September 2025_
