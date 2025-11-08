# Slack AlertManager Integration - Quick Reference

## 🚀 Quick Setup (5 Minutes)

### 1. Create Slack App
```bash
# Go to: https://api.slack.com/apps
# Click: "Create New App" → "From an app manifest"
# Paste: infrastructure/config/slack/slack-app-manifest.json
```

### 2. Get Webhook URL
```bash
# In your app: "Incoming Webhooks" → "Add New Webhook to Workspace"
# Select channel: #alerts-critical
# Copy webhook URL: https://hooks.slack.com/services/T.../B.../XXX...
```

### 3. Run Setup Script
```bash
chmod +x infrastructure/scripts/setup-slack-integration.sh
./infrastructure/scripts/setup-slack-integration.sh
# Follow prompts and paste your webhook URL
```

---

## 📋 Manual Setup

### Option A: Using Environment Variable (Recommended)

1. **Create .env.local file**
```bash
cd infrastructure/docker/compose
nano .env.local
```

2. **Add webhook URL**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. **Update AlertManager config**
```bash
cp infrastructure/config/alertmanager/alertmanager-slack.yml \
   infrastructure/config/alertmanager/alertmanager.yml
```

4. **Restart AlertManager**
```bash
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

### Option B: Direct Configuration

1. **Edit AlertManager config**
```bash
nano infrastructure/config/alertmanager/alertmanager.yml
```

2. **Replace webhook URL**
```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

3. **Restart AlertManager**
```bash
docker-compose -f docker-compose.monitoring.yml restart alertmanager
```

---

## ✅ Test Integration

### Send Test Alert
```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert from ToolboxAI"
    }
  }]'
```

### Check Slack
- Alert should appear in your channel within 10 seconds
- Look for message from "ToolboxAI Alerts"

---

## 📱 Recommended Channels

Create these channels in Slack:

| Channel | Purpose | Alert Level |
|---------|---------|-------------|
| `#alerts-critical` | Production critical alerts | Critical |
| `#alerts-warning` | Warning-level alerts | Warning |
| `#alerts-database` | Database issues | All |
| `#alerts-infrastructure` | Infrastructure issues | All |
| `#monitoring` | General monitoring | Info |

---

## 🎨 Alert Examples

### Critical Alert
```
🚨 CRITICAL: HighCPUUsage
🖥 Instance: backend-server-01
⚠️ Severity: critical
📝 Summary: CPU usage above 90% for 5 minutes
📋 Description: Immediate action required
🕐 Started: 2025-11-07 15:30:00
```

### Warning Alert
```
⚠️ WARNING: DiskSpaceLow
🖥 Instance: storage-server
📝 Summary: Disk space below 15%
🕐 Started: 15:30:00
```

---

## 🔧 Troubleshooting

### Alerts Not Appearing?

1. **Check webhook URL**
```bash
# Test directly
curl -X POST -H 'Content-Type: application/json' \
  --data '{"text":"Test from terminal"}' \
  YOUR_WEBHOOK_URL
```

2. **Check AlertManager logs**
```bash
docker logs toolboxai-alertmanager | grep -i slack
```

3. **Verify config**
```bash
docker exec toolboxai-alertmanager \
  amtool check-config /etc/alertmanager/config.yml
```

### Rate Limiting
- Slack limit: 1 message/second per webhook
- Adjust `group_interval` in config if hitting limits

---

## 📁 Files Reference

| File | Purpose |
|------|---------|
| `infrastructure/config/slack/slack-app-manifest.json` | Slack app manifest |
| `infrastructure/config/alertmanager/alertmanager-slack.yml` | Full Slack config |
| `infrastructure/scripts/setup-slack-integration.sh` | Automated setup |
| `SLACK_ALERTMANAGER_SETUP.md` | Complete documentation |

---

## 🔐 Security

✅ **Never commit webhook URLs to Git**
✅ **Use environment variables**
✅ **Store in .env.local (gitignored)**
✅ **Rotate webhooks every 90 days**

---

## 📚 Documentation

- Full Guide: `SLACK_ALERTMANAGER_SETUP.md`
- Slack API: https://api.slack.com/messaging/webhooks
- AlertManager Docs: https://prometheus.io/docs/alerting/

---

**Created**: November 7, 2025  
**Status**: Ready to deploy

