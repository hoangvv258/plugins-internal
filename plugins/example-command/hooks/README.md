# Hooks Directory

This directory contains logic to execute implicitly during specific lifecycle events within the agent's interaction session.

**Available Hook Points (Examples):**
- `SessionStart`: Executes automatically when a new interaction session boots.
- `PreToolUse`: Triggers immediately before an agent invokes any tool, allowing for security validation or interception.

*Reference: Implement a file like `SessionStart.md` configured to inject internal environment variables contextually before runtime.*
