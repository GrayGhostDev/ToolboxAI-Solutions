global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'slack-primary'

receivers:
  - name: 'slack-primary'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL_1}'
        channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: |-
          {{ range .Alerts }}
          *Alert:* `{{ .Labels.alertname }}`
          *Severity:* `{{ .Labels.severity }}`
          *Summary:* {{ .Annotations.summary }}
          {{ end }}
        send_resolved: true

  - name: 'slack-secondary'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL_2}'
        channel: '#alerts'
        send_resolved: true

inhibit_rules: []
templates: []

