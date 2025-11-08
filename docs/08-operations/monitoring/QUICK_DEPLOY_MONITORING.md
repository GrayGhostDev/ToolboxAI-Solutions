 # Quick Deploy - Monitoring Stack

## Single Command Deployment

Copy and paste this command to deploy the entire monitoring stack:

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose && export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32) && echo "$GRAFANA_ADMIN_PASSWORD" > /tmp/grafana_admin_password.txt && docker network create toolboxai_backend 2>/dev/null || true && docker-compose -f docker-compose.monitoring.yml up -d && echo "" && echo "✅ Monitoring Stack Deployed!" && echo "" && echo "Access URLs:" && echo "  Grafana:     http://localhost:3000 (admin / see /tmp/grafana_admin_password.txt)" && echo "  Prometheus:  http://localhost:9090" && echo "  Jaeger:      http://localhost:16686" && echo "  AlertManager: http://localhost:9093" && echo ""
```

## Or Step-by-Step

### Step 1: Navigate to compose directory
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose
```

### Step 2: Set up Grafana password
```bash
export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
echo "$GRAFANA_ADMIN_PASSWORD" > /tmp/grafana_admin_password.txt
echo "Password saved to /tmp/grafana_admin_password.txt"
```

### Step 3: Create network
```bash
docker network create toolboxai_backend 2>/dev/null || true
```

### Step 4: Deploy stack
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### Step 5: Check status
```bash
docker-compose -f docker-compose.monitoring.yml ps
```

## Access Services

After deployment completes (wait ~30 seconds for services to start):

- **Grafana Dashboard**: http://localhost:3000
  - Login: `admin` / password in `/tmp/grafana_admin_password.txt`
  
- **Prometheus**: http://localhost:9090
  
- **Jaeger Tracing**: http://localhost:16686
  
- **AlertManager**: http://localhost:9093

## Quick Verification

```bash
# Check all services are running
docker ps | grep toolboxai

# Test Prometheus
curl -s http://localhost:9090/-/healthy

# Test Grafana
curl -s http://localhost:3000/api/health

# Test Jaeger
curl -s http://localhost:16686/
```

## Stop Services

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose
docker-compose -f docker-compose.monitoring.yml down
```

## View Logs

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose
docker-compose -f docker-compose.monitoring.yml logs -f
```

