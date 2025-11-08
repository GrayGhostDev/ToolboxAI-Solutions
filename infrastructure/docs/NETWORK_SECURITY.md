# Network Security Configuration

## Overview
This document describes the network security architecture and configuration for ToolboxAI.

## Network Architecture

```
┌─────────────────────────────────────────┐
│          Internet                        │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│     Nginx Reverse Proxy (TLS)            │
│     172.20.0.0/24 (frontend network)     │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│     Backend Services                      │
│     172.21.0.0/24 (backend network)      │
│     - API Server                          │
│     - Celery Workers                      │
│     - MCP Servers                         │
└──────┬───────────────────┬───────────────┘
       │                   │
       ↓                   ↓
┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │
│  PgBouncer   │    │ 172.23.0.0/24│
│172.22.0.0/24 │    │   (cache)    │
│  (database)  │    │              │
└──────────────┘    └──────────────┘
```

## Network Segmentation

### 1. Frontend Network (172.20.0.0/24)
- **Purpose**: Public-facing services
- **Services**: Nginx reverse proxy, certbot
- **Access**: Internet → Frontend
- **Security**: TLS termination, rate limiting

### 2. Backend Network (172.21.0.0/24)
- **Purpose**: Application logic
- **Services**: Backend API, Celery workers, MCP servers
- **Access**: Frontend → Backend only
- **Security**: Internal only, no direct internet access

### 3. Database Network (172.22.0.0/24)
- **Purpose**: Database services
- **Services**: PostgreSQL, PgBouncer
- **Access**: Backend → Database only
- **Security**: Internal only, SSL required

### 4. Cache Network (172.23.0.0/24)
- **Purpose**: Caching layer
- **Services**: Redis
- **Access**: Backend → Cache only
- **Security**: Internal only, TLS required

### 5. Vault Network (172.24.0.0/24)
- **Purpose**: Secrets management
- **Services**: HashiCorp Vault
- **Access**: Backend → Vault only
- **Security**: Token-based authentication

## Docker Network Configuration

```yaml
networks:
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
    ipam:
      config:
        - subnet: 172.20.0.0/24

  backend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
    internal: true  # No internet access
    ipam:
      config:
        - subnet: 172.21.0.0/24
```

## Firewall Rules (iptables)

### Setup Firewall

```bash
cd infrastructure/scripts
sudo ./setup-firewall.sh
```

### Rules Overview

1. **Default Policies**
   - INPUT: DROP (deny all incoming)
   - FORWARD: DROP (deny forwarding)
   - OUTPUT: ACCEPT (allow all outgoing)

2. **Allowed Incoming**
   - HTTPS (443)
   - HTTP (80) - for ACME challenge and redirect
   - SSH (22) - restricted to specific IPs
   - Docker networks (172.16.0.0/12, 10.0.0.0/8)
   - ICMP (ping)

3. **Connection Tracking**
   - ESTABLISHED,RELATED connections allowed
   - Invalid packets dropped

### Custom Firewall Rules

Add custom rules in `/etc/iptables/rules.v4`:

```bash
# Allow from specific IP
iptables -A INPUT -p tcp --dport 22 -s 203.0.113.0/24 -j ACCEPT

# Block specific IP
iptables -A INPUT -s 198.51.100.0/24 -j DROP

# Rate limiting
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

## Service Network Policies

### PostgreSQL

**Allowed Connections**:
- From: Backend network (172.21.0.0/24)
- Protocol: PostgreSQL (5432)
- Encryption: SSL/TLS required

**pg_hba.conf**:
```conf
hostssl all toolboxai 172.21.0.0/24 scram-sha-256
hostnossl all all 0.0.0.0/0 reject
```

### Redis

**Allowed Connections**:
- From: Backend network (172.21.0.0/24)
- Protocol: Redis TLS (6380)
- Authentication: ACL + password

**redis.conf**:
```conf
bind 0.0.0.0
protected-mode yes
port 0
tls-port 6380
```

### Vault

**Allowed Connections**:
- From: Backend network (172.21.0.0/24)
- Protocol: HTTPS (8200)
- Authentication: Token/AppRole

## DDoS Protection

### Rate Limiting

Nginx configuration:

```nginx
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# Apply rate limits
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    limit_req_status 429;
}

location /api/auth/login {
    limit_req zone=login_limit burst=5 nodelay;
}
```

### Connection Limits

```nginx
# Limit concurrent connections per IP
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    limit_conn conn_limit 10;
}
```

### Request Size Limits

```nginx
# Limit request body size
client_max_body_size 100M;
client_body_buffer_size 1M;

# Limit headers
large_client_header_buffers 4 8k;
```

## IP Whitelisting

### Admin Endpoints

Restrict access to sensitive endpoints:

```nginx
location /admin/ {
    allow 203.0.113.0/24;  # Office network
    allow 198.51.100.50;   # VPN server
    deny all;
    
    proxy_pass http://backend:8000/admin/;
}

location /metrics {
    allow 127.0.0.1;       # Localhost
    allow 172.16.0.0/12;   # Docker networks
    deny all;
    
    proxy_pass http://backend:8000/metrics;
}
```

### Database Access

Only allow specific backend services:

```conf
# pg_hba.conf
hostssl all toolboxai 172.21.0.5/32 scram-sha-256  # Backend service
hostssl all toolboxai 172.21.0.6/32 scram-sha-256  # Celery worker
hostnossl all all 0.0.0.0/0 reject
```

## VPN Configuration

For secure remote access, set up WireGuard VPN:

```bash
# Install WireGuard
apt-get install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Configure interface
cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
PrivateKey = <server-private-key>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <client-public-key>
AllowedIPs = 10.0.0.2/32
EOF

# Start VPN
wg-quick up wg0
```

## Monitoring and Alerting

### Monitor Firewall

```bash
# View blocked connections
tail -f /var/log/syslog | grep "iptables-dropped"

# Monitor connection states
watch -n 1 'netstat -ant | awk "{print \$6}" | sort | uniq -c'

# Check active connections
ss -tunap
```

### Intrusion Detection

Install and configure Fail2Ban:

```bash
# Install
apt-get install fail2ban

# Configure
cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

# Start
systemctl start fail2ban
```

## Security Testing

### Port Scanning

```bash
# Scan from external host
nmap -sS -sV -p- toolboxai.com

# Expected results:
# 22/tcp   open  ssh
# 80/tcp   open  http
# 443/tcp  open  https
```

### Network Penetration Testing

```bash
# Test with nmap scripts
nmap --script vuln toolboxai.com

# Test SSL/TLS
nmap --script ssl-enum-ciphers -p 443 toolboxai.com
```

## Compliance

### PCI DSS Requirements

- ✅ Firewall protection (iptables)
- ✅ Encrypted transmission (TLS 1.2+)
- ✅ Network segmentation
- ✅ Access control lists
- ✅ Logging and monitoring

### GDPR Requirements

- ✅ Data encryption in transit
- ✅ Network isolation
- ✅ Access logging
- ✅ Data breach detection

## Disaster Recovery

### Network Configuration Backup

```bash
# Backup iptables rules
iptables-save > /backup/iptables-$(date +%Y%m%d).rules

# Backup nginx configuration
tar czf /backup/nginx-$(date +%Y%m%d).tar.gz /etc/nginx/

# Backup Docker network settings
docker network inspect toolboxai_frontend > /backup/network-frontend.json
```

### Recovery Procedure

```bash
# Restore iptables
iptables-restore < /backup/iptables-20250107.rules

# Restore nginx
tar xzf /backup/nginx-20250107.tar.gz -C /

# Restart services
systemctl restart nginx
docker-compose restart
```

## Best Practices

1. **Principle of Least Privilege**
   - Only open required ports
   - Restrict access by IP when possible
   - Use service-specific networks

2. **Defense in Depth**
   - Multiple layers of security
   - Firewall + network segmentation + TLS
   - Monitoring at each layer

3. **Regular Audits**
   - Review firewall rules monthly
   - Test network isolation quarterly
   - Penetration testing annually

4. **Documentation**
   - Document all network changes
   - Maintain network diagrams
   - Update runbooks

## Troubleshooting

### Cannot Connect to Service

```bash
# Check firewall rules
iptables -L -n -v

# Check Docker networks
docker network ls
docker network inspect <network-name>

# Test connectivity
telnet <host> <port>
curl -v http://<host>:<port>
```

### Service Cannot Reach Database

```bash
# Check network membership
docker inspect <container> | jq '.[0].NetworkSettings.Networks'

# Test connection
docker exec <container> ping postgres
docker exec <container> nc -zv postgres 5432
```

## References

- [Docker Network Security](https://docs.docker.com/network/security/)
- [Nginx Security Best Practices](https://nginx.org/en/docs/security_controls.html)
- [PostgreSQL Network Security](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)

