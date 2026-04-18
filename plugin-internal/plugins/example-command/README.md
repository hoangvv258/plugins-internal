# Example Command Plugin ✨

This plugin provides the simplest possible command. It's meant to serve as a starter template to help us learn how to develop extensions for Claude Code inside our team environment.

## Available Commands

- `/hello`: Triggers a cheerful welcome message displaying the real-time server timestamp to automatically verify that the custom agent is healthy and running!

## Structure Overview
- `.claude-plugin/plugin.json`: Defines the metadata for this specific plugin.
- `commands/hello.md`: Contains the actual logic and prompts for our command. Feel free to open this file to see how easy it is to write commands using pure Markdown!

## How to Expand
If you'd like to add another command (e.g., `/welcome`), simply create a new file at `commands/welcome.md` and follow the exact same format seen in `hello.md`. It's very important to keep the Markdown frontmatter at the top of the file, as it configures the command description and the tools you wish to allow.
