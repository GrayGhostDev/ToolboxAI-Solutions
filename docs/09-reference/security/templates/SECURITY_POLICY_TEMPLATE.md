# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 5.1.x   | :white_check_mark: |
| 5.0.x   | :x:                |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a Vulnerability

Use this section to tell people how to report a vulnerability.

Tell them where to go, how often they can expect to get an update on a
reported vulnerability, what to expect if the vulnerability is accepted or
declined, etc.

---

## Example Secrets and Placeholders

- Documentation and examples use placeholders instead of real secrets:
  - {{TOKEN}}, {{ACCESS_TOKEN}}, {{REFRESH_TOKEN}}, {{API_KEY}}
  - {{GRAFANA_USER}}/{{GRAFANA_PASSWORD}}, {{BASIC_AUTH_B64}}
- Do not replace these in committed code. Provide real values via environment variables at runtime only.

## Local Scripts and Environment Variables

The dashboard startup scripts require the following environment variables:

- VITE_PUSHER_KEY
- VITE_CLERK_PUBLISHABLE_KEY

Set them in your shell or use a .env file loaded by your shell before running scripts like start-dashboard.sh or docker-dashboard.sh.

## Secret Management

- Secrets must be passed via environment variables or a secrets manager.
- Do not commit real credentials, tokens, or API keys. Generated artifacts (docs/api, openapi.json) are ignored.
- Encrypted historical secret files are not tracked in git.
