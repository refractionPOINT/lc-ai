# LimaCharlie Agents

Autonomous AI agents that run inside LimaCharlie organizations. Each agent is deployed as Infrastructure as Code (IaC) via hive configurations and triggered by D&R rules.

## Agent Categories

| Category | Description |
|----------|-------------|
| [investigation](investigation/) | Agents that investigate and triage security events |

## Structure

Each agent directory contains:

```
<agent-name>/
├── README.md          # What the agent does, prerequisites, configuration
└── hives/             # IaC YAML files to deploy
    ├── ai_agent.yaml  # AI agent definition (prompt, model, budget)
    ├── dr-general.yaml # D&R rule(s) that trigger the agent
    └── secret.yaml    # Placeholder secrets (not deployed directly)
```

## Installation

Use the `lc-agent-management` skill from the [lc-essentials](../marketplace/plugins/lc-essentials/) plugin to install and remove agents.
