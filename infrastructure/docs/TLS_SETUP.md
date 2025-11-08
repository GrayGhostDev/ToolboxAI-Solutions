# TLS/SSL Setup Guide

## Overview
This guide covers the setup and configuration of TLS/SSL encryption for all ToolboxAI services.

## Certificate Generation

### Development Environment

Generate self-signed certificates for local development:

```bash
cd infrastructure/scripts
./generate-certs.sh
```

This will create:
- Internal CA certificate
- Self-signed certificates for development
- Service-specific certificates for PostgreSQL and Redis

### Production Environment

For production, use Let's Encrypt certificates:

```bash
# Install certbot (if not already installed)
brew install certbot  # macOS
# or
apt-get install certbot  # Linux

# Generate certificates
cd infrastructure/scripts
sudo ./generate-certs.sh --letsencrypt --domain toolboxai.com --email admin@toolboxai.com
```

## Certificate Locations

```
infrastructure/certificates/
├── production/        # Let's Encrypt certificates for production
│   ├── fullchain.pem
│   ├── privkey.pem
│   └── ca-bundle.crt
├── staging/          # Staging environment certificates
├── development/      # Self-signed certificates for development
├── postgres/         # PostgreSQL TLS certificates
│   ├── server.crt
│   ├── server.key
│   └── ca.crt
├── redis/           # Redis TLS certificates
│   ├── server.crt
│   ├── server.key
│   └── ca.crt
└── internal/        # Internal CA for service-to-service communication
    ├── ca-cert.pem
    └── ca-key.pem
```

## Nginx Configuration

### Enable HTTPS

The nginx reverse proxy is configured to:
1. Redirect all HTTP traffic to HTTPS
2. Terminate TLS at the proxy layer
3. Forward decrypted traffic to backend services

Configuration files:
- `infrastructure/nginx/nginx.conf` - Main nginx configuration
- `infrastructure/nginx/ssl.conf` - SSL/TLS settings
- `infrastructure/nginx/sites-enabled/toolboxai.conf` - Virtual host configuration

### Testing HTTPS

```bash
# Test nginx configuration
docker exec toolboxai-nginx-proxy nginx -t

# Check SSL certificate
openssl s_client -connect localhost:443 -servername toolboxai.local

# Test with curl
curl -k https://localhost:443/health
```

## PostgreSQL TLS

### Configuration

PostgreSQL is configured to require SSL/TLS connections:

- Configuration: `infrastructure/config/postgres/postgresql.conf`
- Access control: `infrastructure/config/postgres/pg_hba.conf`

Key settings:
```ini
ssl = on
ssl_cert_file = '/var/lib/postgresql/certs/server.crt'
ssl_key_file = '/var/lib/postgresql/certs/server.key'
ssl_min_protocol_version = 'TLSv1.2'
```

### Testing PostgreSQL SSL

```bash
# Connect with SSL
psql "postgresql://toolboxai@localhost:5432/toolboxai?sslmode=require"

# Verify SSL connection
psql -c "SELECT * FROM pg_stat_ssl WHERE pid = pg_backend_pid();"
```

## Redis TLS

### Configuration

Redis is configured to use TLS on port 6380:

- Configuration: `infrastructure/config/redis/redis.conf`
- ACL: `infrastructure/config/redis/users.acl`

Key settings:
```conf
port 0                    # Disable non-TLS port
tls-port 6380            # Enable TLS port
tls-protocols "TLSv1.2 TLSv1.3"
```

### Testing Redis TLS

```bash
# Connect with TLS
redis-cli --tls \
  --cert infrastructure/certificates/redis/server.crt \
  --key infrastructure/certificates/redis/server.key \
  --cacert infrastructure/certificates/redis/ca.crt \
  -p 6380 ping
```

## Certificate Renewal

### Automatic Renewal

Certificates are automatically renewed using certbot and a cron job:

```bash
# Setup automatic renewal (run once)
crontab -e

# Add this line:
0 0 * * 0 /path/to/infrastructure/scripts/renew-certs.sh
```

### Manual Renewal

```bash
cd infrastructure/scripts
./renew-certs.sh
```

## Service-to-Service mTLS

Internal services use mutual TLS (mTLS) for authentication:

1. All services have client certificates signed by the internal CA
2. Services verify each other's certificates
3. Communication is encrypted end-to-end

## Security Best Practices

1. **Certificate Storage**
   - Store private keys with 600 permissions
   - Never commit certificates to version control
   - Use Vault for certificate management in production

2. **Certificate Rotation**
   - Rotate certificates every 90 days
   - Monitor certificate expiration
   - Test rotation procedures regularly

3. **TLS Configuration**
   - Use TLS 1.2 or higher only
   - Disable weak cipher suites
   - Enable HSTS headers

4. **Monitoring**
   - Monitor certificate expiration dates
   - Alert 30 days before expiration
   - Log all TLS handshake failures

## Troubleshooting

### Certificate Issues

```bash
# Check certificate validity
openssl x509 -in certificate.crt -text -noout

# Verify certificate chain
openssl verify -CAfile ca.crt certificate.crt

# Test TLS connection
openssl s_client -connect host:port -showcerts
```

### Common Problems

1. **"Certificate has expired"**
   - Solution: Run `./renew-certs.sh`

2. **"SSL handshake failed"**
   - Check certificate permissions
   - Verify certificate paths in configuration
   - Check TLS version compatibility

3. **"Certificate name mismatch"**
   - Ensure certificate CN matches hostname
   - Add SANs (Subject Alternative Names) for multiple domains

## References

- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [PostgreSQL SSL Documentation](https://www.postgresql.org/docs/current/ssl-tcp.html)
- [Redis TLS Documentation](https://redis.io/docs/manual/security/encryption/)

