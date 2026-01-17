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

### Getting Started

Before using the lc-essentials plugin, you need access to Claude Code through one of these options:

#### Option A: Local Installation

Install Claude Code on your local machine:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

For detailed setup instructions, see the [Claude Code Quickstart Guide](https://code.claude.com/docs/en/quickstart).

Then continue to the [Plugin Installation](#plugin-installation) section below.

#### Option B: Web-Based (No Installation)

Use Claude Code directly through the LimaCharlie web interface at [app.limacharlie.io](https://app.limacharlie.io). The lc-essentials plugin is already pre-configured - **you're ready to go with no additional setup required**.

---

### Plugin Installation

*Only required for [Option A](#option-a-local-installation) (local installation)*

#### Option 1: Add as a Marketplace (Recommended)

<p align="center">
  <a href="https://youtu.be/0ANw5Xgftzo">
    <img src="https://images.ctfassets.net/8ypp714zy4gs/35FhLnqWkbvOBnHHX54oY9/d194c0ac3099e9c60c7794d8095dc4b7/screencap.png" alt="Installing the AgenticSecOps Workspace" width="600">
  </a>
  <br>
  <em>Installing the AgenticSecOps Workspace</em>
</p>

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

### Authentication

After installing the plugin:

1. Restart the `claude` tool
2. Run `/mcp` and select the LimaCharlie MCP server
3. Authenticate using OAuth when prompted

### Configuration

For advanced configuration options, see the [LimaCharlie MCP documentation](https://github.com/refractionPOINT/lc-mcp-server).

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

See `marketplace/plugins/lc-essentials/SKILLS_SUMMARY.md` for a complete list of available skills.

## Repository Structure

```
.
├── .claude-plugin/              # Marketplace configuration
│   └── marketplace.json         # Marketplace definition
├── marketplace/                 # Claude Code marketplace
│   └── plugins/
│       └── lc-essentials/       # Main LimaCharlie plugin
│           ├── .claude-plugin/  # Plugin configuration
│           ├── agents/          # Sub-agent definitions
│           ├── commands/        # Slash commands
│           ├── scripts/         # Helper scripts
│           └── skills/          # Skill definitions
├── docker/                      # Docker container files
│   ├── Dockerfile               # Container definition
│   ├── docker-compose.yml       # Docker Compose configuration
│   └── entrypoint.sh            # Container entrypoint script
└── LICENSE                      # Apache 2.0 License
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

Once authenticated, you have access to 20+ LimaCharlie skills and 120+ API functions including:

- Sensor management and live investigation
- Detection & Response rule creation
- LCQL queries and historical data analysis
- AI-powered query and rule generation
- Threat report evaluation
- And more...

Run `/help` in Claude Code to explore available commands.

## Contributing

Thank you for your interest in contributing to LimaCharlie AI Integrations!

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/refractionPOINT/lc-ai.git
cd lc-ai
```

2. Add as a local marketplace in your project:
```bash
cd your-project
/plugin marketplace add /path/to/lc-ai
/plugin install lc-essentials@lc-marketplace
```

### Making Changes

#### Editing Skills

1. Find the relevant skill in `marketplace/plugins/lc-essentials/skills/`
2. Make your changes to the `SKILL.md` file
3. Test locally by reinstalling the plugin
4. Submit a pull request

#### Adding New Skills

1. Create a new directory in `marketplace/plugins/lc-essentials/skills/`
2. Add a `SKILL.md` file following the existing skill format
3. Update `SKILLS_SUMMARY.md` with your new skill
4. Test the skill locally
5. Submit a pull request

#### Adding New Agents

1. Create a new markdown file in `marketplace/plugins/lc-essentials/agents/`
2. Follow the existing agent format
3. Reference the agent in relevant skills
4. Test locally and submit a pull request

### Pull Request Guidelines

1. **Focus**: Keep PRs focused on a single topic or issue
2. **Testing**: Test your changes locally before submitting
3. **Description**: Provide a clear description of what changed and why
4. **Screenshots**: Include screenshots for visual changes
5. **Links**: Verify all internal links work correctly

### Code of Conduct

Please be respectful and professional in all interactions. We're building tools to help the security community, and we appreciate your contributions!

### Questions?

- Join our [Community Slack](https://slack.limacharlie.io)
- Email [support@limacharlie.io](mailto:support@limacharlie.io)
- Open an [issue on GitHub](https://github.com/refractionPOINT/lc-ai/issues)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Support

- [LimaCharlie Documentation](https://docs.limacharlie.io)
- [LimaCharlie Community](https://community.limacharlie.io)
- [GitHub Issues](https://github.com/refractionPOINT/lc-ai/issues)
