# Monitoring stack (Prometheus / Grafana / Loki / Alertmanager)

This document explains how to manage the local monitoring stack and regenerate Alertmanager configuration that injects Slack webhook URLs from the compose `.env` file.

Quick checklist
- `docker compose -f infrastructure/docker/compose/docker-compose.monitoring.yml up -d` — start stack
- Alertmanager config generator: `infrastructure/config/alertmanager/generate_config.py`

Regenerate Alertmanager config (after changing `.env`)

1. Edit `infrastructure/docker/compose/.env` with your Slack webhook URLs and other variables. Do NOT commit secrets — use `.env.example` as a template.

2. Run the generator script to create `infrastructure/config/alertmanager/config.yml`:

```bash
python3 infrastructure/config/alertmanager/generate_config.py
```

This reads `infrastructure/docker/compose/.env` and `infrastructure/config/alertmanager/config.yml.tpl` and writes `infrastructure/config/alertmanager/config.yml`.

3. (Optional) Copy generated config to `alertmanager.yml` if you use that path in compose:

```bash
cp infrastructure/config/alertmanager/config.yml infrastructure/config/alertmanager/alertmanager.yml
```

4. Restart Alertmanager via docker compose:

```bash
cd infrastructure/docker/compose
docker compose -f docker-compose.monitoring.yml up -d alertmanager
```

Testing Alertmanager -> Slack end-to-end

1. Ensure Prometheus has the test rule loaded:

```bash
curl -X POST http://localhost:9090/-/reload
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="toolboxai_test_rules")'
```

2. After ~1 minute (rule has `for: 1m`) the `ToolboxAIAlwaysFiring` alert will be firing. Check Prometheus alerts:

```bash
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {labels: .labels, state: .state, annotations: .annotations}'
```

3. Monitor Alertmanager logs to see delivery attempts to Slack webhooks:

```bash
docker logs -f toolboxai-alertmanager
```

If Alertmanager retries/drops notifications, check the logs for `Notify for alerts failed` messages.

Security recommendations
- Immediately rotate Slack app tokens and incoming webhook URLs you used for testing.
- Move secrets to a secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager) instead of `.env` in repo.
- Keep an `.env.example` (already present) in repo and ensure `.env` is listed in `.gitignore` (already present).

Grafana provisioning
- Provisioning files are expected under `infrastructure/config/grafana/provisioning/{dashboards,datasources,notifiers,alerting}`. We seeded `dashboards` and `datasources` with existing `.yml` files. Add any notifier/alerting provisioning files if required.

If you want, I can:
- Replace the Slack-only config with the richer `alertmanager-slack.yml` and re-test end-to-end (only after rotating webhooks)
- Add Prometheus alert rules for critical monitoring checks and SLOs
- Wire Supabase (postgres) metrics into Prometheus using the `postgres-exporter` and secure connections


