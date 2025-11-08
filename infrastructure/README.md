# ToolboxAI Infrastructure

## Overview

This directory contains all infrastructure configuration, automation scripts, and documentation for the ToolboxAI platform. The infrastructure is designed with security-first principles, following production best practices.

## Directory Structure

```
infrastructure/
├── certificates/          # TLS/SSL certificates
├── config/               # Service configurations
├── docker/               # Docker and container configs
├── docs/                 # Documentation
├── nginx/                # Nginx reverse proxy
├── scripts/              # Automation scripts
└── vault/                # Vault secrets management
```

## Quick Start

### Prerequisites

- Docker 25.x or higher
- Docker Compose v2
- OpenSSL 3.x
- macOS, Linux, or WSL2
- Supabase account (for Phase 2)

### Phase 1: Security Infrastructure

Follow the quick start guide:

```bash
# Read the quick start guide
cat docs/PHASE1_QUICKSTART.md

# Or jump straight to setup:
cd scripts
./generate-certs.sh           # Generate certificates
cd ../docker/compose
docker-compose -f docker-compose.secure.yml up -d
```

See [PHASE1_QUICKSTART.md](docs/PHASE1_QUICKSTART.md) for detailed instructions.

### Phase 2: High Availability with Supabase

```bash
# Read the Supabase integration guide
cat docs/SUPABASE_INTEGRATION.md

# Deploy Phase 2 stack (with Supabase)
cd docker/compose
docker-compose -f docker-compose.phase2.yml up -d
```

See [SUPABASE_INTEGRATION.md](docs/SUPABASE_INTEGRATION.md) for detailed instructions.

## Documentation

### Phase 1: Critical Security
- **[Phase 1 Quick Start](docs/PHASE1_QUICKSTART.md)** - Step-by-step setup guide
- **[TLS Setup Guide](docs/TLS_SETUP.md)** - Certificate management and SSL/TLS configuration
- **[Secrets Management](docs/SECRETS_MANAGEMENT.md)** - HashiCorp Vault setup and usage
- **[Network Security](docs/NETWORK_SECURITY.md)** - Network segmentation and firewall
- **[Security Checklist](docs/SECURITY_CHECKLIST.md)** - Implementation tracking

### Root Level
- **[PHASE1_SECURITY_COMPLETE.md](../PHASE1_SECURITY_COMPLETE.md)** - Implementation summary

## Key Features

### ✅ Security (Phase 1 - COMPLETE)
- TLS/SSL encryption for all services
- HashiCorp Vault for secrets management
- Network segmentation (5 isolated networks)
- Database and cache encryption
- Automated secrets rotation
- Firewall configuration

### 🚧 High Availability (Phase 2 - Planned)
- PostgreSQL replication
- Redis clustering
- Load balancing
- Automated failover

### 🚧 Monitoring (Phase 2 - Planned)
- Prometheus + Grafana
- Distributed tracing
- Log aggregation
- Alerting

## Services

### Core Services
- **nginx-proxy** - HTTPS reverse proxy and load balancer
- **postgres** - Primary database with SSL
- **pgbouncer** - Connection pooling
- **redis** - Cache with TLS
- **vault** - Secrets management

### Security Services
- **certbot** - Let's Encrypt certificate management
- **vault-rotator** - Automated secret rotation

## Configuration Files

### Network & Security
- `docker/compose/docker-compose.secure.yml` - Production-ready stack
- `nginx/ssl.conf` - Modern TLS configuration
- `nginx/sites-enabled/toolboxai.conf` - Virtual hosts

### Database
- `config/postgres/postgresql.conf` - PostgreSQL with SSL
- `config/postgres/pg_hba.conf` - Access control

### Cache
- `config/redis/redis.conf` - Redis with TLS
- `config/redis/users.acl` - Redis access control

### Secrets
- `vault/vault-config.hcl` - Vault configuration
- `vault/policies/*.hcl` - Access policies

## Scripts

All scripts are located in `scripts/` and are executable:

### Certificate Management
- `generate-certs.sh` - Generate all certificates
- `renew-certs.sh` - Renew certificates

### Secrets Management
- `vault-init.sh` - Initialize Vault
- `rotate-secrets.sh` - Rotate secrets manually
- `vault_rotator.py` - Automated rotation service

### Security
- `setup-firewall.sh` - Configure iptables (Linux only)

## Network Architecture

```
Internet
   ↓
[Nginx Proxy - TLS]  (172.20.0.0/24 - frontend)
   ↓
[Backend Services]   (172.21.0.0/24 - backend, internal)
   ↓
[Database/Cache]     (172.22.0.0/24 - database, internal)
                     (172.23.0.0/24 - cache, internal)
```

## Security Highlights

### Encryption
- ✅ HTTPS for all external traffic (TLS 1.2+)
- ✅ PostgreSQL SSL required
- ✅ Redis TLS required
- ✅ Vault HTTPS
- ✅ Internal mTLS for service communication

### Access Control
- ✅ Network segmentation (5 isolated networks)
- ✅ Firewall rules (iptables)
- ✅ Database ACL (pg_hba.conf)
- ✅ Redis ACL with role-based access
- ✅ Vault policies (RBAC)

### Secrets
- ✅ All secrets in Vault (zero plaintext)
- ✅ Automated rotation (weekly)
- ✅ Secret versioning
- ✅ Audit logging

## Common Tasks

### Start Services
```bash
cd docker/compose
docker-compose -f docker-compose.secure.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.secure.yml down
```

### View Logs
```bash
docker-compose -f docker-compose.secure.yml logs -f [service]
```

### Check Service Health
```bash
docker ps
docker-compose -f docker-compose.secure.yml ps
```

### Unseal Vault (after restart)
```bash
export VAULT_ADDR=http://localhost:8200
vault operator unseal <key-1>
vault operator unseal <key-2>
vault operator unseal <key-3>
```

### Rotate Secrets
```bash
cd scripts
./rotate-secrets.sh all
```

### Renew Certificates
```bash
cd scripts
./renew-certs.sh
```

## Troubleshooting

### Check Service Logs
```bash
cd docker/compose
docker-compose -f docker-compose.secure.yml logs [service]
```

### Test TLS Connections
```bash
# Test HTTPS
curl -k https://localhost:443/health

# Test PostgreSQL SSL
docker exec toolboxai-postgres psql "postgresql://toolboxai@localhost/toolboxai?sslmode=require" -c "SELECT version();"

# Test Redis TLS
docker exec toolboxai-redis redis-cli --tls -p 6380 ping
```

### Verify Network Isolation
```bash
# Backend should NOT access internet
docker exec toolboxai-backend curl -I --max-time 5 https://google.com
# Expected: Should timeout/fail

# Backend should access database
docker exec toolboxai-backend nc -zv postgres 5432
# Expected: Should succeed
```

## Maintenance

### Daily
- Monitor service health
- Check logs for errors
- Verify Vault is unsealed

### Weekly
- Run certificate renewal check
- Review security logs
- Check for updates

### Monthly
- Rotate secrets
- Review firewall rules
- Update documentation

### Quarterly
- Security audit
- Penetration testing
- Backup testing

## Environment Variables

Required environment variables are documented in `.env.example`:

```bash
# Copy and customize
cp .env.example .env
```

Key variables:
- `POSTGRES_DB`, `POSTGRES_USER` - Database configuration
- `VAULT_ADDR` - Vault address
- `NODE_ENV` - Environment (development/production)
- `DOMAIN` - Your domain name
- `CERT_EMAIL` - Email for Let's Encrypt

## Production Deployment

### Pre-Deployment
1. Review [PHASE1_QUICKSTART.md](docs/PHASE1_QUICKSTART.md)
2. Update domain names in configurations
3. Generate production certificates
4. Configure DNS records
5. Setup firewall rules
6. Initialize Vault
7. Store all secrets

### Deployment
```bash
# Generate production certificates
cd scripts
sudo ./generate-certs.sh --letsencrypt --domain yourdomain.com --email admin@yourdomain.com

# Create secrets
docker swarm init
./create-production-secrets.sh

# Start services
cd ../docker/compose
docker-compose -f docker-compose.secure.yml up -d

# Initialize Vault
cd ../../scripts
./vault-init.sh

# Configure firewall (Linux only)
sudo ./setup-firewall.sh
```

### Post-Deployment
1. Verify all services healthy
2. Test HTTPS endpoints
3. Validate SSL/TLS connections
4. Test backup procedures
5. Configure monitoring (Phase 2)
6. Setup alerts (Phase 2)

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Check troubleshooting sections in documentation
- **Updates**: Review `PHASE1_SECURITY_COMPLETE.md` for latest status

## Next Steps

After Phase 1 validation:
- **Phase 2**: High Availability & Disaster Recovery
- **Phase 3**: Monitoring & Observability
- **Phase 4**: CI/CD Pipeline
- **Phase 5**: Performance & Scaling
- **Phase 6**: Compliance & Documentation

## License

See [LICENSE](../LICENSE) file in the repository root.

## Version

- **Phase 1**: v1.0.0 - Critical Security (COMPLETE)
- **Phase 2**: Planned
- **Phase 3**: Planned

Last Updated: November 7, 2025

