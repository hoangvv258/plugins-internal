# Reference Plugin Implementation (`example-command`)

This directory contains a structural reference implementation demonstrating how to architect and expose custom agent extensions within the internal environment.

## Supported Commands

- `/hello`: Invokes a system health protocol that fetches and surfaces the active server timestamp to validate agent execution capabilities.

## Architectural Components

- `.claude-plugin/plugin.json`: Contains the essential metadata and dependency definitions for this package.
- `commands/hello.md`: Standardized Markdown file containing the frontmatter configuration and execution logic for the specific slash command.
- `agents/`: Directory reserved for defining custom Copilot agents with dedicated contexts.
- `hooks/`: Directory for lifecycle event handlers (e.g., `SessionStart`, `PreToolUse`).
- `skills/`: Directory for housing modular prompt capabilities and tools.
- `.mcp.json`: External tool configurations utilizing the Model Context Protocol.

## Extension Guidelines

To expand the capability of this plugin (e.g., adding a `/status` command):
1. Create a corresponding Markdown file within the `commands/` directory (`commands/status.md`).
2. Implement the standard YAML frontmatter to define the `description` and `allowed-tools` parameters.
3. Structure the prompt clearly following the contextual paradigm demonstrated in `hello.md`.
