# 🐳 ToolBoxAI Docker Infrastructure

## Overview

This directory contains the modernized Docker infrastructure for ToolBoxAI, optimized for Docker Engine 25.x with security-first design and best practices for 2025.

## 📁 Directory Structure

```
infrastructure/docker/
├── compose/                 # Docker Compose configurations
│   ├── docker-compose.yml   # Base configuration (security by default)
│   ├── docker-compose.dev.yml    # Development overrides
│   └── docker-compose.prod.yml   # Production overrides
├── dockerfiles/             # Optimized Dockerfiles
│   ├── backend.Dockerfile   # Multi-stage Python backend
│   ├── dashboard.Dockerfile # React dashboard with Nginx
│   ├── agents.Dockerfile    # AI agent coordinator
│   └── mcp.Dockerfile       # Model Context Protocol server
├── config/                  # Configuration files
│   ├── nginx/              # Nginx configurations
│   ├── postgres-init.sql   # Database initialization
│   └── redis.conf          # Redis configuration
├── secrets/                # Docker secrets (never commit actual secrets!)
│   └── README.md           # Secrets management guide
└── scripts/                # Helper scripts
    ├── setup.sh            # Initial setup script
    ├── deploy.sh           # Deployment script
    └── cleanup.sh          # Cleanup script
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop 4.26+ (includes Docker Engine 25.x)
- Docker Compose v2.24+
- 8GB+ RAM allocated to Docker
- VirtioFS enabled for macOS (Settings → Resources → File sharing → VirtioFS)

### Development Setup

1. **Clone and navigate to the project:**
```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
```

2. **Copy environment template:**
```bash
cp .env.example .env
# Edit .env with your actual values (keep secrets secure!)
```

3. **Start development stack:**
```bash
./infrastructure/docker/start-docker-dev.sh
```
This helper performs validation, builds images, and starts services in the proper order. To start manually use:
```bash
docker compose -f infrastructure/docker/compose/docker-compose.yml \
              -f infrastructure/docker/compose/docker-compose.dev.yml up -d
```

4. **Access services:**
- Dashboard: http://localhost:5179
- Backend API: http://localhost:8009
- API Docs: http://localhost:8009/docs
- Adminer (DB): http://localhost:8082
- Redis Commander: http://localhost:8081
- Mailhog: http://localhost:8025

## 🔒 Security Features

### Implemented Security Measures

✅ **No exposed secrets** - All sensitive data in Docker secrets or external vaults
✅ **Non-root users** - All containers run as non-privileged users
✅ **Read-only filesystems** - Containers use read-only root with tmpfs for writable areas
✅ **Network isolation** - Internal networks for database/cache access
✅ **Security options** - `no-new-privileges`, dropped capabilities
✅ **Resource limits** - CPU and memory limits on all containers
✅ **Health checks** - Comprehensive health monitoring
✅ **TLS/SSL** - Encrypted communication in production

## 🏗️ Build Optimization

### Docker BuildKit Features

Our Dockerfiles leverage BuildKit for:
- **Cache mounts** - Persistent package manager caches
- **Multi-stage builds** - Reduced image sizes (60-80% smaller)
- **Parallel builds** - Independent stages build concurrently
- **External cache** - Registry-based caching for CI/CD

## 📝 License

Copyright © 2025 ToolBoxAI Solutions. All rights reserved.
