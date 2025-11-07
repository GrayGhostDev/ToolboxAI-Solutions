# Quick Fix Command for Monitoring Stack

## Problem Summary
Configuration files were being mounted as directories instead of files, causing services to crash.

## One-Line Fix

Copy and paste this command to fix and restart all monitoring services:

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose && docker-compose -f docker-compose.monitoring.yml stop loki promtail alertmanager blackbox-exporter && docker-compose -f docker-compose.monitoring.yml rm -f loki promtail alertmanager blackbox-exporter && docker-compose -f docker-compose.monitoring.yml up -d && echo "✅ Monitoring stack restarted with fixes applied!"
```

## Or Step-by-Step

### 1. Navigate to compose directory
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose
```

### 2. Stop affected services
```bash
docker-compose -f docker-compose.monitoring.yml stop loki promtail alertmanager blackbox-exporter
```

### 3. Remove old containers
```bash
docker-compose -f docker-compose.monitoring.yml rm -f loki promtail alertmanager blackbox-exporter
```

### 4. Start all services
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 5. Verify status
```bash
docker-compose -f docker-compose.monitoring.yml ps
```

## What Was Fixed

✅ **Loki**: Config path corrected  
✅ **Promtail**: Config path corrected  
✅ **AlertManager**: Config path corrected  
✅ **Blackbox Exporter**: Config path corrected  
✅ **Prometheus**: Path updated to `../../config`  
✅ **Grafana**: Port changed to 3000, path updated

## Verify Services Are Working

```bash
# Check Loki
curl http://localhost:3100/ready

# Check AlertManager  
curl http://localhost:9093/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check all service status
docker-compose -f docker-compose.monitoring.yml ps
```

## Access Services

After fix is applied:

- **Grafana**: http://localhost:3000 (admin / password from /tmp/grafana_admin_password.txt)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **AlertManager**: http://localhost:9093

---

**All configuration fixes have been applied to `docker-compose.monitoring.yml`**  
**Just restart the services to apply the fixes!**

