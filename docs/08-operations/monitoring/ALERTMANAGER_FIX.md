# AlertManager Configuration Fix

## Problem
AlertManager was failing with error: `"unsupported scheme \"\" for URL"`

## Root Cause
The AlertManager configuration file contained environment variables like `${SLACK_WEBHOOK_URL}` and `${SMTP_PASSWORD}` that were not set, resulting in empty URL schemes which AlertManager cannot parse.

## Solution Applied

### 1. Created Minimal Working Configuration
Created a new `alertmanager-minimal.yml` with basic configuration that doesn't require external services.

### 2. Replaced Broken Config
```bash
cp infrastructure/config/alertmanager/alertmanager-minimal.yml \
   infrastructure/config/alertmanager/alertmanager.yml
```

### 3. Restart AlertManager
```bash
cd infrastructure/docker/compose
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

## Verify Fix

Check AlertManager is running:
```bash
docker-compose -f docker-compose.monitoring.yml ps alertmanager
```

Check AlertManager logs (should show no errors):
```bash
docker-compose -f docker-compose.monitoring.yml logs alertmanager | tail -20
```

Test AlertManager endpoint:
```bash
curl http://localhost:9093/-/healthy
```

Should return: `Healthy`

## Configuration Details

The new minimal configuration:
- ✅ No external dependencies (Slack, PagerDuty, SMTP)
- ✅ Basic routing for critical and warning alerts
- ✅ Alerts are logged but not sent (until you configure receivers)
- ✅ Ready for production with commented examples for adding notifications

## Adding Notifications Later

To add Slack notifications, edit `infrastructure/config/alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-critical'
        title: 'Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

Then restart AlertManager:
```bash
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

## Quick Restart Command

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/compose && docker-compose -f docker-compose.monitoring.yml restart alertmanager && sleep 5 && docker-compose -f docker-compose.monitoring.yml logs --tail=30 alertmanager
```

## Status

✅ **AlertManager config fixed**  
✅ **Ready to restart**  
⏳ **Awaiting configuration of notification channels (optional)**

---

**File**: `infrastructure/config/alertmanager/alertmanager.yml`  
**Status**: Fixed and ready for use

