---
name: lc-agent-management
description: |
  Install and remove autonomous LimaCharlie AI agents (lc-agents) in an organization.
  Handles subscribing to required extensions, creating API keys, setting secrets,
  and pushing hive configurations. Use when user wants to deploy an lc-agent like
  "l1-bot" to their org, or remove a previously installed agent. Examples: "install
  the l1-bot agent", "deploy l1-bot to my org", "remove the l1-bot agent".
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# LimaCharlie Agent Management

You help users install and remove autonomous AI agents (lc-agents) in their LimaCharlie organizations.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output yaml [flags]
```

For command help and discovery: `limacharlie <command> --ai-help`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **Output Format** | `--output json` | `--output yaml` (more token-efficient) |
| **Filter Output** | Pipe to jq/yq | Use `--filter JMESPATH` to select fields |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## Available Agents

Agents are defined in the `lc-agents/` directory of the lc-ai repository. Each agent has:
- A `README.md` describing what it does and its prerequisites
- A `hives/` directory containing the IaC YAML files to deploy

To discover available agents, list the directories under `lc-agents/` in the lc-ai repository.

---

## Install an Agent

When the user asks to install/deploy an agent, follow these steps:

### Step 1: Read the Agent Definition

Read the agent's `README.md` and all files in its `hives/` directory to understand:
- What the agent does
- What extensions it requires
- What secrets it needs
- What hive entries it creates (ai_agent, dr-general, etc.)

The agent definitions are in the `lc-agents/` directory at the root of the lc-ai repository. The lc-ai repo is the marketplace source for this plugin, so find it by searching for it relative to the plugin installation:

```bash
# The lc-agents dir is 3 levels up from this skill's directory
# (skills/lc-agent-management/ -> skills/ -> lc-essentials/ -> plugins/ -> marketplace/ -> repo root)
find / -path "*/lc-ai/lc-agents" -type d 2>/dev/null | head -1
```

Read all hive YAML files for the agent to understand the full configuration. If you already know the agent (e.g. l1-bot), you can also use the embedded reference at the bottom of this document.

### Step 2: Get the Target OID

Ask the user which organization to install into, or use the OID they provided.
Verify with:
```bash
limacharlie org list --output yaml
```

### Step 3: Subscribe to Required Extensions

Check the agent's README for required extensions. Subscribe to each:
```bash
limacharlie extension subscribe --name <extension-name> --oid <oid>
```

Common extensions for agents:
- `ext-ticketing` - Required for ticket-based agents

Check if already subscribed first:
```bash
limacharlie extension list --oid <oid> --output yaml
```

### Step 4: Set Up Secrets

Each agent has a `secret.yaml` defining required secrets. For each secret:

#### LimaCharlie API Key (`lc-api-key`)

Offer to create the API key for the user automatically:

```bash
limacharlie api-key create \
  --name "<agent-name>-api-key" \
  --permissions "sensor.list,sensor.get,sensor.task,dr.list,dr.set,org.get,hive.get,ai_agent.operate" \
  --oid <oid> \
  --output yaml
```

**IMPORTANT**: The secret key is only shown once at creation. Capture it and immediately store it:

```bash
limacharlie secret set --key lc-api-key --oid <oid> <<< '{"secret": "<the-api-key-value>"}'
```

Adjust permissions based on what the agent needs. For ticket-based agents, also include permissions for ticketing operations.

#### Anthropic API Key (`anthropic-key`)

Ask the user for their Anthropic API key. Then store it:

```bash
limacharlie secret set --key anthropic-key --oid <oid> <<< '{"secret": "<user-provided-key>"}'
```

**NEVER** generate, guess, or fabricate API keys. The user must provide their own Anthropic key.

#### Other Secrets

If the agent requires additional secrets, ask the user for the values.

### Step 5: Push the Hive Configurations

Use `limacharlie sync push` to deploy the agent's hive configurations:

```bash
limacharlie sync push \
  --oid <oid> \
  --dir <path-to-agent-hives-dir> \
  --hive-ai-agent \
  --hive-dr-general
```

Include the relevant `--hive-*` flags based on what the agent's YAML files define. Look at the top-level keys in each YAML file to determine which hive types are used.

Alternatively, push individual hive entries:

```bash
# Push AI agent definition
limacharlie hive import \
  --hive-name ai_agent \
  --input-file <path-to-ai_agent.yaml-content> \
  --oid <oid>

# Push D&R rules
limacharlie hive import \
  --hive-name dr-general \
  --input-file <path-to-dr-general.yaml-content> \
  --oid <oid>
```

**Do NOT push secret.yaml** - secrets were already set in Step 4 with the actual values.

### Step 6: Verify Installation

```bash
# Verify AI agent definition
limacharlie hive get --hive-name ai_agent --key <agent-name> --oid <oid> --output yaml

# Verify D&R rules
limacharlie hive list --hive-name dr-general --oid <oid> --output yaml

# Verify secrets exist (won't show values)
limacharlie secret list --oid <oid> --output yaml

# Check for org errors
limacharlie org errors --oid <oid> --output yaml
```

### Step 7: Report to User

Summarize what was installed:
- Extensions subscribed
- Secrets created
- Hive entries pushed (AI agent definitions, D&R rules)
- How the agent will be triggered
- Any configuration parameters (model, budget, TTL, etc.)

---

## Remove an Agent

When the user asks to remove/uninstall an agent:

### Step 1: Read the Agent Definition

Read the agent's hive files to know what was deployed.

### Step 2: Remove Hive Entries

Delete the AI agent definition and D&R rules:

```bash
# Delete AI agent definition
limacharlie hive delete --hive-name ai_agent --key <agent-name> --confirm --oid <oid>

# Delete D&R rules created by the agent
limacharlie hive delete --hive-name dr-general --key <rule-name> --confirm --oid <oid>
```

### Step 3: Clean Up Secrets (Optional)

Ask the user if they want to remove the secrets too:

```bash
limacharlie secret delete --key anthropic-key --confirm --oid <oid>
limacharlie secret delete --key lc-api-key --confirm --oid <oid>
```

**Warn the user** that other agents or configurations may depend on these secrets. Only delete if the user confirms.

### Step 4: Clean Up API Key (Optional)

If an API key was created during install, offer to delete it:

```bash
# List API keys to find the one created for this agent
limacharlie api-key list --oid <oid> --output yaml

# Delete by key hash
limacharlie api-key delete --key-hash <hash> --confirm --oid <oid>
```

### Step 5: Unsubscribe Extensions (Optional)

Only offer to unsubscribe extensions if no other agents or configurations depend on them:

```bash
limacharlie extension unsubscribe --name <extension-name> --oid <oid>
```

**Warn the user** that unsubscribing extensions may break other functionality.

### Step 6: Report to User

Summarize what was removed and what was left in place (with reasons).

---

## Agent Reference: l1-bot

### Description
Automated Level 1 SOC analyst that investigates new security tickets and documents findings for L2 review.

### Required Extensions
- `ext-ticketing` - Must be subscribed AND configured

### Required Secrets
| Secret Key | Description |
|-----------|-------------|
| `anthropic-key` | Anthropic API key (user provides) |
| `lc-api-key` | LimaCharlie API key (can create for user) |

### Recommended API Key Permissions
For the `lc-api-key`, create with these permissions:
```
sensor.list,sensor.get,sensor.task,dr.list,org.get,hive.get,ai_agent.operate
```

### Hive Entries Created
| Hive | Key | Description |
|------|-----|-------------|
| `ai_agent` | `l1-bot` | AI agent definition with investigation prompt |
| `dr-general` | `l1-bot-ticket-triage` | D&R rule triggering bot on ticket creation |

### How It's Triggered
When `ext-ticketing` creates a ticket, it emits a `created` event. The D&R rule matches events with a `ticket_id` field and starts the AI agent session with ticket context.

### Configuration
| Parameter | Value |
|-----------|-------|
| Model | `opus` |
| Max turns | 30 |
| Budget cap | $2.00 per investigation |
| Timeout | 600 seconds |
| Mode | One-shot (terminates after completion) |
| Suppression | Max 10 invocations per minute |
