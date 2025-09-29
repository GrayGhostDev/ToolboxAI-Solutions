---
name: monitor
description: Monitors queue/workers and alerts only on genuine issues
---

Inputs
- Queue state, worker heartbeats
Outputs
- Low-noise alerts; summary reports
Rules
- Redact sensitive info; avoid noisy alerts; exponential backoff for retries.
