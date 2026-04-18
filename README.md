# Internal Plugin Repository (`plugin-internal`)

Welcome to your Internal Plugin Repository! 🚀 This repository is configured as a standalone "Marketplace" specifically for Claude Code. It's the perfect place to store your internal team plugins, specialized agents, and custom workflows.

## 1. Directory Structure

Here's how things are laid out:

```text
plugin-internal/
├── .claude-plugin/
│   └── marketplace.json      # The central registry listing all available plugins
├── plugins/
│   └── example-command/      # Our friendly starter plugin!
└── README.md                 # You are here!
```

## 2. How to "Install" (Load) These Plugins in VS Code

You can easily install and manage these plugins directly within the Visual Studio Code interface, without using any CLI commands. Before starting, ensure this repository is pushed to a Git host like GitHub or GitLab.

**Method 1: Install via VS Code Command Palette**
1. Open Visual Studio Code and press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) to open the Command Palette.
2. Search for and select **`Chat: Install Plugin From Source`**.
3. Enter your Git repository URL (for example, `https://github.com/my-org/my-plugin-repo`). VS Code will automatically clone and install the plugin.

**Method 2: Install via the Chat Customizations Editor**
1. Open the GitHub Copilot / Chat view in VS Code.
2. Click the **Gear icon** (Settings) located directly in the chat view, then select **Plugins**.
3. In the Chat Customizations editor, click the **`+` (Add)** button on the Plugins page.
4. Paste your Git repository URL.

**Managing Your Plugins:**
After installing, you can enable, disable, or uninstall them right from the **Agent Plugins - Installed** view within the VS Code Extensions panel, or via the gear icon in the Chat view. Whenever you trigger commands (like our `/hello`), they will seamlessly integrate into your Copilot Agent workflow!

## 3. How to Create a New Plugin (using `plugin-dev`)

The main `claude-code` repository comes with an awesome built-in toolkit called `plugin-dev` to help you scaffold new plugins automatically. Here is the best flow:

1. In your `claude-code` source directory, launch Claude:
   ```bash
   claude
   ```
2. Type the following command to trigger the interactive plugin creator:
   ```bash
   /plugin-dev:create-plugin
   ```
3. Claude will chat with you and guide you step by step!
   - *What do you want your plugin to do?* (For example: "I want a plugin that automatically formats my code")
   - Claude will generate all the necessary scaffolding, hook files, and JSON configurations for you.
4. Once Claude has generated the structure (usually placed in the standard `plugins/` directory), **move that newly generated folder into this repository's `plugin-internal/plugins/` directory.**
5. Finally, open `plugin-internal/.claude-plugin/marketplace.json` and register your new plugin by appending a block like this into the `"plugins"` array:
   ```json
   {
      "name": "your-cool-new-plugin",
      "description": "What it does...",
      "source": "./plugins/your-cool-new-plugin",
      "category": "development",
      "version": "1.0.0"
   }
   ```
   
And that's it! 🎉 Whenever your teammates pull the latest `marketplace.json`, they will instantly have access to your brand new plugin!
