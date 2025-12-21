# LimaCharlie AI Integrations

This repository contains AI integrations for LimaCharlie, including Claude Code plugins, agents, and skills for security operations.

## Claude Code Plugin Marketplace

The `plugins/` directory contains Claude Code plugins that can be installed to enhance Claude Code with LimaCharlie capabilities.

### Available Plugins

#### lc-essentials

The `lc-essentials` plugin provides comprehensive LimaCharlie integration for Claude Code, including:

- **API Operations**: Full access to LimaCharlie APIs through structured skills
- **Detection Engineering**: Build, test, and deploy D&R rules with AI assistance
- **Investigation Creation**: Automated SOC investigation workflows
- **Threat Report Evaluation**: Parse threat reports and hunt for IOCs
- **Sensor Tasking**: Query and command EDR agents
- **Multi-tenant Reporting**: Generate reports across multiple organizations
- **Adapter Management**: Configure and troubleshoot log adapters

### Installation

#### Option 1: Add as a Marketplace (Recommended)

From within a project directory:

```bash
# Add the marketplace
/plugin marketplace add https://github.com/refractionPOINT/lc-ai

# Install the plugin
/plugin install lc-essentials@lc-marketplace
```

#### Option 2: Local Installation

Clone this repository and add it as a local marketplace:

```bash
git clone https://github.com/refractionPOINT/lc-ai.git
cd your-project
/plugin marketplace add /path/to/lc-ai
/plugin install lc-essentials@lc-marketplace
```

### Configuration

The plugin requires a LimaCharlie API key configured as an MCP server. See the [LimaCharlie MCP documentation](https://github.com/refractionPOINT/lc-mcp) for setup instructions.

### Usage

Once installed, initialize any project with LimaCharlie guidelines:

```bash
/init-lc
```

Then use natural language to interact with LimaCharlie:

- "List all sensors in my organization"
- "Create a detection rule for encoded PowerShell"
- "Investigate this detection and create an investigation record"
- "Get a health report for all my organizations"

See `plugins/lc-essentials/SKILLS_SUMMARY.md` for a complete list of available skills.

## Repository Structure

```
.
├── .claude-plugin/          # Marketplace configuration
│   └── marketplace.json     # Marketplace definition
├── plugins/                 # Claude Code plugins
│   └── lc-essentials/       # Main LimaCharlie plugin
│       ├── .claude-plugin/  # Plugin configuration
│       ├── agents/          # Sub-agent definitions
│       ├── commands/        # Slash commands
│       ├── scripts/         # Helper scripts
│       └── skills/          # Skill definitions
└── LICENSE                  # Apache 2.0 License
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/refractionPOINT/documentation/blob/master/CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Support

- [LimaCharlie Documentation](https://docs.limacharlie.io)
- [LimaCharlie Community](https://community.limacharlie.io)
- [GitHub Issues](https://github.com/refractionPOINT/lc-ai/issues)
