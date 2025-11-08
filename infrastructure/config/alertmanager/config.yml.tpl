global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'slack-primary'

receivers:
  - name: 'slack-primary'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL_1}'
        channel: '#alerts'
        text: "Alert received — check Alertmanager UI for details"

  - name: 'slack-secondary'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL_2}'
        channel: '#alerts'
        text: "Alert received — check Alertmanager UI for details"

inhibit_rules: []
templates: []
