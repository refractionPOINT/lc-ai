---
name: lc-agent-management
description: |
  Install and remove autonomous LimaCharlie AI agents (lc-agents) and full AI SOC
  definitions (lc-soc) in an organization. Handles subscribing to required extensions,
  creating API keys, setting secrets, and pushing hive configurations.
  Use when user wants to deploy an lc-agent like "l1-bot", or install an entire
  SOC like "lean-soc" or "tiered-soc" to their org, or remove a previously installed
  agent or SOC. Examples: "install the l1-bot agent", "deploy lean-soc to my org",
  "install the tiered SOC", "remove the l1-bot agent", "uninstall lean-soc".
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# LimaCharlie Agent Management

You help users install and remove autonomous AI agents (lc-agents) and full AI SOC definitions (lc-soc) in their LimaCharlie organizations.

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

Individual agents are defined in the `lc-agents/` directory of the lc-ai repository. Each agent has:
- A `README.md` describing what it does and its prerequisites
- A `hives/` directory containing the IaC YAML files to deploy

To discover available agents, list the directories under `lc-agents/` in the lc-ai repository.

## Available SOCs

Full SOC definitions are in the `lc-soc/` directory. Each SOC is a coordinated set of agents that work together:

| SOC | Agents | Description |
|-----|--------|-------------|
| `lean-soc` | 4 agents | Minimal SOC: triage, investigator, responder, reporter |
| `tiered-soc` | 8 agents | Full L1/L2/L3 SOC: triage, l1-investigator, l2-analyst, malware-analyst, containment, threat-hunter, soc-manager, shift-reporter |

Each SOC has a top-level `README.md` describing its architecture, cost profile, and tradeoffs. Each agent within the SOC has its own `README.md` with specific API key permissions.

To discover available SOCs, list the directories under `lc-soc/` in the lc-ai repository.

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

Read all hive YAML files for the agent to understand the full configuration.

### Step 2: Get the Target OID

Ask the user which organization to install into, or use the OID they provided.
Verify with:
```bash
limacharlie org list --output yaml
```

### Step 2b: Verify Permissions

Before proceeding, verify the current credentials have the `ai_agent.operate` permission (required for all agent deployments):
```bash
limacharlie auth whoami --check-perm ai_agent.operate --output yaml
```
If `has_perm: false`, stop and inform the user their API key or user account lacks this permission.

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
  --permissions "sensor.list,sensor.get,sensor.task,dr.list,dr.set,org.get,hive.get,ext.request,ai_agent.operate" \
  --oid <oid> \
  --output yaml
```

**IMPORTANT**: The secret key is only shown once at creation. Capture it and immediately store it.

Secrets are hive records and **must be created with `enabled: true`** to be usable. Use `hive set` with the full record format to ensure this:

```bash
echo '{"data": {"secret": "<the-api-key-value>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key lc-api-key --oid <oid>
```

Adjust permissions based on what the agent needs. For ticket-based agents, also include permissions for ticketing operations.

#### Anthropic API Key (`anthropic-key`)

Ask the user for their Anthropic API key. Then store it:

```bash
echo '{"data": {"secret": "<user-provided-key>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key anthropic-key --oid <oid>
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

## Install a SOC

When the user asks to install/deploy a full SOC (lean-soc or tiered-soc), follow these steps. A SOC is a coordinated set of agents that must all be deployed together.

### Step 1: Read the SOC Definition

Read the SOC's top-level `README.md` and every agent's `README.md` within it:

```bash
# Find the lc-soc directory
find / -path "*/lc-ai/lc-soc" -type d 2>/dev/null | head -1
```

Read the SOC README for the architecture overview, installation order, and agent list. Then read each agent's README for its specific API key permissions.

### Step 2: Get the Target OID

Ask the user which organization to install into, or use the OID they provided.
```bash
limacharlie org list --output yaml
```

### Step 2b: Verify Permissions

```bash
limacharlie auth whoami --check-perm ai_agent.operate --output yaml
```

### Step 3: Subscribe to Required Extensions

All SOC agents require `ext-ticketing`:
```bash
limacharlie extension subscribe --name ext-ticketing --oid <oid>
```

Check if already subscribed first:
```bash
limacharlie extension list --oid <oid> --output yaml
```

### Step 4: Set Up the Anthropic Secret

The Anthropic API key is shared across all agents in the SOC. Ask the user for it and store it once.

Secrets are hive records and **must be created with `enabled: true`** to be usable:

```bash
echo '{"data": {"secret": "<user-provided-key>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key anthropic-key --oid <oid>
```

Check if it already exists (from a previous agent install):
```bash
limacharlie secret list --oid <oid> --output yaml
```

If it already exists, ask the user if they want to reuse it or update it.

### Step 5: Create Per-Agent API Keys and Secrets

**Each agent gets its own API key** with least-privilege permissions from its README. Create them all, storing each immediately since the key is only shown once.

For each agent in the SOC's installation order:

```bash
# Create the API key with agent-specific permissions
limacharlie api-key create \
  --name "<agent-key-name>" \
  --permissions "<comma-separated-permissions-from-readme>" \
  --oid <oid> \
  --output yaml
```

**Capture the key value** from the output and immediately store it as a secret (must be `enabled: true`):

```bash
echo '{"data": {"secret": "<the-api-key-value>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key <agent-secret-name> --oid <oid>
```

The secret name must match what the agent's `ai_agent.yaml` references in its `lc_api_key_secret` field (e.g., `hive://secret/lean-triage-api-key` means the secret key is `lean-triage-api-key`).

### Step 6: Push All Hive Configurations

Push each agent's hive configs using `sync push`. Process each agent's `hives/` directory:

```bash
# For each agent in the SOC, push its ai_agent.yaml
limacharlie sync push \
  --config-file <path-to-agent>/hives/ai_agent.yaml \
  --hive-ai-agent \
  --oid <oid>

# And its dr-general.yaml
limacharlie sync push \
  --config-file <path-to-agent>/hives/dr-general.yaml \
  --hive-dr-general \
  --oid <oid>
```

**Do NOT push secret.yaml files** -- secrets were already set in Steps 4-5 with actual values.

Follow the SOC's documented installation order (typically: triage first, then investigators, then responders/hunters, then scheduled agents).

### Step 7: Verify Installation

```bash
# Verify all AI agent definitions
limacharlie hive list --hive-name ai_agent --oid <oid> --output yaml

# Verify all D&R rules
limacharlie hive list --hive-name dr-general --oid <oid> --output yaml

# Verify secrets exist
limacharlie secret list --oid <oid> --output yaml

# Check for org errors
limacharlie org errors --oid <oid> --output yaml
```

### Step 8: Report to User

Summarize:
- Which SOC was installed and how many agents
- All API keys created (names and permissions)
- All secrets stored
- All hive entries pushed (ai_agent + dr-general per agent)
- The agent pipeline flow (how agents trigger each other)
- Estimated cost profile (from the SOC README)

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

## Remove a SOC

When the user asks to remove/uninstall an entire SOC:

### Step 1: Read the SOC Definition

Read the SOC's README and all agent hive files to know what was deployed.

### Step 2: Remove All Hive Entries

Delete every AI agent definition and D&R rule for the SOC. Use the tags on hive records to identify all components (e.g., `lc-soc:lean-soc:*` tags):

```bash
# For each agent in the SOC:
limacharlie hive delete --hive-name ai_agent --key <agent-name> --confirm --oid <oid>
limacharlie hive delete --hive-name dr-general --key <dr-rule-name> --confirm --oid <oid>
```

### Step 3: Clean Up Secrets (Optional)

Ask the user if they want to remove per-agent API key secrets:

```bash
# For each agent secret:
limacharlie secret delete --key <agent-api-key-secret> --confirm --oid <oid>
```

**Warn**: The `anthropic-key` secret may be shared with other agents or SOCs. Only delete if the user confirms no other agents depend on it.

### Step 4: Clean Up API Keys (Optional)

```bash
limacharlie api-key list --oid <oid> --output yaml
# Delete each agent's API key by hash
limacharlie api-key delete --key-hash <hash> --confirm --oid <oid>
```

### Step 5: Report to User

Summarize what was removed (agent definitions, D&R rules, secrets, API keys) and what was left in place.

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
org.get,sensor.list,sensor.get,sensor.task,dr.list,insight.det.get,insight.evt.get,investigation.get,investigation.set,ext.request,ai_agent.operate
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

