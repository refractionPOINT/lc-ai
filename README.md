<p align="center">
  <img src="https://images.ctfassets.net/8ypp714zy4gs/5QH5UdlNkikGfeWICDnN6k/511a03a00aff79bec59959d5facb846e/Group_1798.png" alt="LimaCharlie AI">
</p>

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

### Option 3: Docker Container

Use the pre-configured Docker container with everything ready to go:

```bash
cd docker && docker compose run --rm lc-claude
```

See the [Docker section](#docker-container) below for more details.

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
├── docker/                  # Docker container files
│   ├── Dockerfile           # Container definition
│   ├── docker-compose.yml   # Docker Compose configuration
│   └── entrypoint.sh        # Container entrypoint script
└── LICENSE                  # Apache 2.0 License
```

## Docker Container

Pre-configured Claude Code environment with the lc-essentials plugin for LimaCharlie operations.

### What's Included

- **Debian bookworm-slim** base image
- **Claude Code** - Anthropic's official CLI
- **lc-essentials plugin** - Pre-configured via GitHub marketplace
- **LimaCharlie Python SDK** - For scripting and automation
- **GitHub CLI (gh)** - For PR/issue workflows
- **Node.js LTS** - For JavaScript-based tooling
- **Common tools** - git, jq, vim, nano, curl

### Quick Start

```bash
cd docker && docker compose run --rm lc-claude
```

### Build Only

```bash
cd docker && docker compose build
```

### First Run

On first run, authenticate with LimaCharlie:

```
/mcp
```

This opens your browser for OAuth authentication. Once approved, you're ready to use all LimaCharlie skills.

### Mount Your Project

To work on a specific project directory:

```bash
cd docker && docker compose run --rm -v /path/to/your/project:/home/lc/project lc-claude
```

Or create a `project/` directory inside the `docker/` directory - it's automatically mounted.

### Persistent Credentials

The container mounts `~/.claude` from your host to persist:
- Claude API credentials
- LimaCharlie OAuth tokens
- Plugin configuration
- Settings and preferences

### Network Mode

This container uses **host networking** (`network_mode: host`) which is required for OAuth callbacks to work correctly. The OAuth flow opens a browser on your host machine and the callback needs to reach the container.

### Available Skills

Once authenticated, you have access to 121+ LimaCharlie skills including:

- Sensor management and live investigation
- Detection & Response rule creation
- LCQL queries and historical data analysis
- AI-powered query and rule generation
- Threat report evaluation
- And more...

Run `/help` in Claude Code to explore available commands.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/refractionPOINT/documentation/blob/master/CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Support

- [LimaCharlie Documentation](https://docs.limacharlie.io)
- [LimaCharlie Community](https://community.limacharlie.io)
- [GitHub Issues](https://github.com/refractionPOINT/lc-ai/issues)
