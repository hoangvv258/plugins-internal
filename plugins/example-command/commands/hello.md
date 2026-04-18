---
allowed-tools: Bash(echo *), Bash(date *)
description: Executes a system health check by returning the current server timestamp.
---

## Context

- System timestamp: !`date`

## Task Requirements

Acknowledge the command execution by outputting the following standard system response format:

"[SYSTEM LOG] The internal `/hello` routine executed successfully at <System timestamp>."

Constraint: Do not invoke any unrelated tools or produce conversational output. Strictly adhere to the requested system log format.
