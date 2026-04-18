---
name: Extract Enterprise Logs
description: This skill should be used when the user asks to "fetch active error traces", "extract enterprise logs", or wants to securely check `/var/log/enterprise.log`.
version: 1.0.0
---

# Extract Enterprise Logs Skill

## Skill Execution Logic

When asked to fetch logs, perform the following:

1. Use Bash tools to invoke `cat /var/log/enterprise.log` efficiently.
2. Filter the traces for `ERROR` and `FATAL` severities.
3. Output the final aggregated summary directly to the user in structured JSON.
