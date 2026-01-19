# LimaCharlie Claude Code Docker Container

Pre-configured Claude Code environment with the lc-essentials plugin for LimaCharlie operations.

## What's Included

- **Debian bookworm-slim** base image
- **Claude Code** - Anthropic's official CLI
- **lc-essentials plugin** - Pre-configured via GitHub marketplace
- **LimaCharlie Python SDK** - For scripting and automation
- **GitHub CLI (gh)** - For PR/issue workflows
- **Node.js LTS** - For JavaScript-based tooling
- **Common tools** - git, jq, vim, nano, curl

## Quick Start

```bash
docker compose run -it --rm lc-claude
```

## Build Only

```bash
docker compose build
```

## First Run

On first run, authenticate with LimaCharlie:

```
/mcp
```

This opens your browser for OAuth authentication. Once approved, you're ready to use all LimaCharlie skills.

## Mount Your Project

To work on a specific project directory:

```bash
docker compose run -it --rm -v /path/to/your/project:/home/lc/project lc-claude
```

Or create a `project/` directory next to the docker-compose.yml file - it's automatically mounted.

## Persistent Credentials

The container mounts `~/.claude` from your host to persist:
- Claude API credentials
- LimaCharlie OAuth tokens
- Plugin configuration
- Settings and preferences

## Network Mode

This container uses **host networking** (`network_mode: host`) which is required for OAuth callbacks to work correctly. The OAuth flow opens a browser on your host machine and the callback needs to reach the container.

## Available Skills

Once authenticated, you have access to LimaCharlie skills including:

- Sensor management and live investigation
- Detection & Response rule creation
- LCQL queries and historical data analysis
- AI-powered query and rule generation
- Threat report evaluation
- And more...

Run `/help` in Claude Code to explore available commands.
