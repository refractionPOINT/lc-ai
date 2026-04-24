---
name: lc-deployer
description: |
  REQUIRED for ANY operation involving ai-team or ai-agent definitions: deploy, install,
  update, upgrade, remove, push, sync, or modify AI agents and Agentic SOC configurations
  in a LimaCharlie organization. This includes modifying agent prompts, updating hive
  configs (ai_agent, dr-general), managing API keys and secrets, subscribing to extensions,
  and pushing changes after editing source YAML files in ai-teams/ or ai-agents/ directories.
  Trigger words: ai-team, ai-agent, ai_agent hive, deploy SOC, install agent, push agent,
  update agent, sync agent, baselining-soc, tiered-soc, lean-soc, exposure-team, intel-team,
  l1-bot, general-analyst, bulk-triage, l2-analyst, malware-analyst, containment,
  threat-hunter, soc-manager, shift-reporter. Examples: "deploy tiered-soc to my org",
  "install lean-soc", "update the l1-bot agent", "push agent changes to the org",
  "remove the tiered SOC", "modify the bulk-triage prompt".
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# LimaCharlie Agentic SOC & Agent Deployer

You help users deploy, install, and remove Agentic SOC as Code definitions (ai-team) and individual AI agents (ai-agents) in their LimaCharlie organizations.

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

Individual agents are defined in the `ai-agents/` directory of the lc-ai repository. Each agent has:
- A `README.md` describing what it does and its prerequisites
- A `hives/` directory containing the IaC YAML files to deploy

To discover available agents, list the directories under `ai-agents/` in the lc-ai repository.

## Available SOCs

Full SOC definitions are in the `ai-teams/` directory. Each SOC is a coordinated set of agents that work together:

| SOC | Agents | Description |
|-----|--------|-------------|
| `lean-soc` | 4 agents | Minimal SOC: triage, investigator, responder, reporter |
| `tiered-soc` | 8 agents | Full L1/L2/L3 SOC: triage, l1-investigator, l2-analyst, malware-analyst, containment, threat-hunter, soc-manager, shift-reporter |
| `baselining-soc` | 7 agents | Noise-reduction SOC for new orgs: bulk-triage, l2-analyst, malware-analyst, containment, threat-hunter, soc-manager, shift-reporter |

Each SOC has a top-level `README.md` describing its architecture, cost profile, and tradeoffs. Each agent within the SOC has its own `README.md` with specific API key permissions.

To discover available SOCs, list the directories under `ai-teams/` in the lc-ai repository.

### Tag Convention

Every `ai_agent` hive record carries structured tags that describe **what the agent is** and **how it relates** to other things in the org. Two tag vocabularies coexist on every record today:

- **`ai-rel:…`** — the canonical relationship grammar. All new work should read and emit these. Rich enough to describe edges from an agent to any other LC entity (other agents, sensors, outputs, D&R rules, case tags, secrets, extensions, …).
- **`ai-team:…`** / **`ai-agent:…`** — legacy identity and `sends-to` tags. Kept in sync automatically during deployment so older consumers (the main webapp graph, existing scripts) don't break. Do not drop these from existing records.

#### The `ai-rel` grammar

```
ai-rel:<scope>:<verb>:<kind>:<id>
```

| Segment | Values | Notes |
|---------|--------|-------|
| `<scope>` | team name (`tiered-soc`, `intel-team`, …), `standalone`, `global` | Use the team name for in-team edges. Use `standalone` for ungrouped ai-agents. Use `global` for cross-scope references (secrets, extensions, anything not specific to one team). |
| `<verb>` | `role`, `sends-to`, `reads-from`, `writes-to`, `triggers-on`, `depends-on`, `enriches` | See verb table below. |
| `<kind>` | `agent`, `sensor`, `adapter`, `output`, `rule`, `hive`, `secret`, `case-tag`, `extension`, `team` | The entity type of the other end. |
| `<id>` | entity-specific | Agent role for `agent`, secret name for `secret`, case tag string for `case-tag`, etc. Sensors accept selector form (`plat:windows`) as well as literal SIDs. |

**Verb reference:**

| Verb | Direction | Typical uses |
|------|-----------|--------------|
| `role` | self | Membership / identity within `<scope>`. Every agent has exactly one per scope it participates in. |
| `sends-to` | agent → agent | Handoff / mention / case-tag-triggered next step. |
| `reads-from` | agent → sensor, adapter, output, hive | Ingest or context source. |
| `writes-to` | agent → output, hive, case-tag | Artifact destination. |
| `triggers-on` | agent → rule, case-tag, event | Invocation condition (used when the D&R wiring is external to the agent's own rule). |
| `depends-on` | agent → secret, extension | Hard prerequisite — if missing, the agent cannot operate. |
| `enriches` | agent → case, case-tag | Side effect that downstream agents key on (e.g. appending a `needs-malware-analysis` tag that another agent triggers on). |

**Worked example — `tiered-soc/l2-analyst`:**

```yaml
tags:
  # legacy (kept for backward compat)
  - ai-team:tiered-soc:l2-analyst
  - ai-team:tiered-soc:sends-to:containment
  - ai-team:tiered-soc:sends-to:threat-hunter
  - ai-team:tiered-soc:sends-to:malware-analyst
  - ai-team:api-key:soc-l2-analyst
  # canonical ai-rel grammar
  - ai-rel:tiered-soc:role:agent:l2-analyst
  - ai-rel:tiered-soc:sends-to:agent:containment
  - ai-rel:tiered-soc:sends-to:agent:threat-hunter
  - ai-rel:tiered-soc:sends-to:agent:malware-analyst
  - ai-rel:global:depends-on:secret:soc-l2-analyst
```

**Standalone agents** (not part of a team, under `ai-agents/`) use `standalone` as the scope:

```yaml
tags:
  - ai-agent:case-investigator
  - ai-agent:api-key:case-investigator
  - ai-rel:standalone:role:agent:case-investigator
  - ai-rel:global:depends-on:secret:case-investigator
```

#### Legacy → canonical mapping (reference)

When you write new agents or read existing ones, these are the exact correspondences that must be hand-maintained in each agent's hive yaml:

| Legacy tag | Canonical tag |
|------------|---------------|
| `ai-team:<team>:<role>` | `ai-rel:<team>:role:agent:<role>` |
| `ai-team:<team>:sends-to:<target>` | `ai-rel:<team>:sends-to:agent:<target>` |
| `ai-team:api-key:<secret>` | `ai-rel:global:depends-on:secret:<secret>` |
| `ai-agent:<name>` | `ai-rel:standalone:role:agent:<name>` |
| `ai-agent:api-key:<secret>` | `ai-rel:global:depends-on:secret:<secret>` |

#### Authoring richer relationships

The legacy vocabulary only expresses identity + agent→agent. The canonical vocabulary can express anything. When authoring or editing an agent, add extra `ai-rel:` tags for any of these that apply — they unlock a richer relationship graph for any consumer (ops dashboards, analytics, agent catalogues):

- An agent that reads specific outputs to gather context → `ai-rel:<scope>:reads-from:output:<output-name>`
- An agent that pulls from a sensor subset → `ai-rel:<scope>:reads-from:sensor:plat:windows` (selector) or `ai-rel:<scope>:reads-from:sensor:sid:<sid>`
- An agent that writes into a hive (e.g. a lookup table it maintains) → `ai-rel:<scope>:writes-to:hive:lookup:<key>`
- An agent triggered by a specific case tag → `ai-rel:<scope>:triggers-on:case-tag:needs-escalation`
- An agent that adds case tags for downstream agents → `ai-rel:<scope>:writes-to:case-tag:needs-malware-analysis`
- An agent that requires an extension → `ai-rel:global:depends-on:extension:ext-cases`

The only hard requirement today is the mapping table above — every agent must carry the canonical equivalent of each legacy tag it has. Additional `ai-rel:` tags are optional and purely descriptive.

#### Reconstructing the flow graph

List all `ai_agent` records, parse `ai-rel:…` tags, and build nodes/edges from them:

- `ai-rel:<scope>:role:agent:<role>` → node `(<scope>, agent, <role>)`, agent record resolved by hive key.
- `ai-rel:<scope>:<verb>:<kind>:<id>` (with `<verb>` ≠ `role`) → edge `(from: this agent) → (to: resolve <scope>/<kind>/<id>)`, labelled by `<verb>`. Resolve the target against the appropriate source: `agent` → another `ai_agent` record in the same scope; `sensor`, `output`, `adapter` → the LC org's corresponding API; `secret`, `extension` → auxiliary nodes.
- Group by `<scope>` for layout. `global` edges cross scopes and point to shared resources.

Fall back to `ai-team:` / `ai-agent:` parsing only if no `ai-rel:` tags are present (some very old records).

**Multi-scope coexistence**: When tiered-soc and baselining-soc are installed in the same org, some agents share the same hive key (e.g., `soc-l2-analyst`). Each SOC contributes its own `role` and `sends-to` tags under its own `<scope>`, so the record carries tags from both scopes simultaneously. See the "Install a SOC" section for the tag-merging procedure.

---

## Install an Agent

When the user asks to install/deploy an agent, follow these steps:

### Step 1: Read the Agent Definition

Read the agent's `README.md` and all files in its `hives/` directory to understand:
- What the agent does
- What extensions it requires
- What secrets it needs
- What hive entries it creates (ai_agent, dr-general, etc.)

The agent definitions are in the `ai-agents/` directory at the root of the lc-ai repository. The lc-ai repo is the marketplace source for this plugin, so find it by searching for it relative to the plugin installation:

```bash
# The ai-agents dir is 3 levels up from this skill's directory
# (skills/lc-deployer/ -> skills/ -> lc-advanced-skills/ -> plugins/ -> marketplace/ -> repo root)
find / -path "*/lc-ai/ai-agents" -type d 2>/dev/null | head -1
```

Read all hive YAML files for the agent to understand the full configuration.

### Step 2: Get the Target OID

Ask the user which organization to install into, or use the OID they provided.
Verify with:
```bash
limacharlie org list --output yaml
```

### Step 2b: Verify Permissions

Before proceeding, verify the current credentials have the `ai_agent.operate` permission (required for all agent deployments).
**IMPORTANT**: You MUST include `--oid <oid>` — without it, the check runs against a null org context and will always return `has_perm: false`:
```bash
limacharlie auth whoami --oid <oid> --check-perm ai_agent.operate --output yaml
```
If `has_perm: false`, stop and inform the user their API key or user account lacks this permission.

### Step 3: Subscribe to Required Extensions

Check the agent's README for required extensions. Subscribe to each:
```bash
limacharlie extension subscribe --name <extension-name> --oid <oid>
```

Common extensions for agents:
- `ext-cases` - Required for case-based agents

Check if already subscribed first:
```bash
limacharlie extension list --oid <oid> --output yaml
```

### Step 4: Set Up Secrets

Each agent has a `secret.yaml` defining required secrets. For each secret:

#### LimaCharlie API Key

Offer to create the API key for the user automatically:

```bash
limacharlie api-key create \
  --name "<agent-name>" \
  --permissions "sensor.list,sensor.get,sensor.task,dr.list,dr.set,org.get,hive.get,ext.request,org_notes.get,org_notes.set,ai_agent.operate" \
  --oid <oid> \
  --output yaml
```

**IMPORTANT**: The secret key is only shown once at creation. Capture it and immediately store it.

Secrets are hive records and **must be created with `enabled: true`** to be usable. Use `hive set` with the full record format to ensure this:

```bash
echo '{"data": {"secret": "<the-api-key-value>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key <agent-name> --oid <oid>
```

Adjust permissions based on what the agent needs. For case-based agents, also include permissions for cases operations.

#### Anthropic API Key (`anthropic-key`)

Ask the user for their Anthropic API key. Then store it:

```bash
echo '{"data": {"secret": "<user-provided-key>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key anthropic-key --oid <oid>
```

**NEVER** generate, guess, or fabricate API keys. The user must provide their own Anthropic key.

#### Other Secrets

If the agent requires additional secrets, ask the user for the values.

### Step 5: Push the Hive Configurations

Each agent has a root IaC file (e.g., `basic-triage.yaml`) that uses `include:` to pull in all its hive configs. Push it with a single command:

```bash
limacharlie sync push \
  --config-file <path-to-agent>/<agent-name>.yaml \
  --hive-ai-agent \
  --hive-dr-general \
  --oid <oid>
```

The root file uses the sync `include:` mechanism to merge all per-agent hive YAMLs automatically. Use `--dry-run` first to preview changes.

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
# Find the ai-teams directory
find / -path "*/lc-ai/ai-teams" -type d 2>/dev/null | head -1
```

Read the SOC README for the architecture overview, installation order, and agent list. Then read each agent's README for its specific API key permissions.

### Step 2: Get the Target OID

Ask the user which organization to install into, or use the OID they provided.
```bash
limacharlie org list --output yaml
```

### Step 2b: Verify Permissions

**IMPORTANT**: You MUST include `--oid <oid>` — without it, the check runs against a null org context and will always return `has_perm: false`:
```bash
limacharlie auth whoami --oid <oid> --check-perm ai_agent.operate --output yaml
```

### Step 3: Subscribe to Required Extensions

All SOC agents require `ext-cases`:
```bash
limacharlie extension subscribe --name ext-cases --oid <oid>
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
echo '{"data": {"secret": "<the-api-key-value>"}, "usr_mtd": {"enabled": true}}' | limacharlie hive set --hive-name secret --key <agent-name> --oid <oid>
```

The secret name must match what the agent's `ai_agent.yaml` references in its `lc_api_key_secret` field (e.g., `hive://secret/lean-triage` means the secret key is `lean-triage`). The secret name is the same as the agent's hive key.

### Step 5b: Save Existing Tags (Multi-SOC Awareness)

Before pushing hive configs, check whether any `ai_agent` keys that this SOC will create already exist in the org (from another SOC). If they do, save their current tags so they can be merged back after the push.

**Shared keys between tiered-soc and baselining-soc:**

| Hive | Shared Keys |
|------|-------------|
| `ai_agent` | `soc-l2-analyst`, `malware-analyst`, `containment`, `threat-hunter`, `soc-manager`, `soc-shift-reporter` |
| `dr-general` | `soc-l2-on-case-escalated`, `malware-analyst-on-mention`, `containment-on-mention`, `threat-hunter-on-mention`, `soc-manager-hourly`, `soc-shift-reporter-daily` |

For each shared key that already exists:
```bash
# Save the existing record's tags before the push overwrites them
limacharlie hive get --hive-name ai_agent --key <shared-key> --oid <oid> --output yaml
# Note down all tags from usr_mtd.tags
```

If no shared keys exist yet, skip to Step 6.

### Step 6: Push All Hive Configurations

Each SOC has a root IaC file (e.g., `lean-soc.yaml`) that uses `include:` to pull in all agent hive configs. Push the entire SOC with a single command:

```bash
limacharlie sync push \
  --config-file <path-to-soc>/<soc-name>.yaml \
  --hive-ai-agent \
  --hive-dr-general \
  --oid <oid>
```

The root file uses the sync `include:` mechanism to merge all per-agent hive YAMLs automatically. Use `--dry-run` first to preview changes.

**Do NOT push secret.yaml files** -- secrets were already set in Steps 4-5 with actual values.

### Step 6b: Reconcile Tags (Multi-SOC)

If you saved tags from existing records in Step 5b, the push will have overwritten those records with the new SOC's tags only. You must merge the other SOC's tags back.

For each shared key where you saved prior tags:

1. Read the freshly pushed record:
   ```bash
   limacharlie hive get --hive-name ai_agent --key <shared-key> --oid <oid> --output yaml
   ```

2. Identify tags from the **other** SOC that were lost. A tag belongs to a specific scope if it starts with `ai-team:<scope>:` or `ai-rel:<scope>:` — anything in a scope other than the currently-pushed SOC must be preserved. Tags with scope `global` (e.g. `ai-rel:global:depends-on:secret:...`) and any `ai-team:api-key:...` entries are SOC-independent and must also be preserved.

3. Write the merged record back with all tags from both SOCs:
   ```bash
   # Build the full record with merged tags and pipe to hive set
   echo '<full record JSON with merged tags>' | limacharlie hive set --hive-name ai_agent --key <shared-key> --oid <oid>
   ```

**Example**: Installing baselining-soc when tiered-soc is already present. The `soc-l2-analyst` key previously carried the tiered-soc tags:

```
ai-team:tiered-soc:l2-analyst
ai-team:tiered-soc:sends-to:containment
ai-team:tiered-soc:sends-to:threat-hunter
ai-rel:tiered-soc:role:agent:l2-analyst
ai-rel:tiered-soc:sends-to:agent:containment
ai-rel:tiered-soc:sends-to:agent:threat-hunter
```

After pushing baselining-soc, the record is overwritten with only the baselining-soc equivalents. Merge both sets so the record carries the full twelve tags (six per scope) plus any `global` / `api-key` tags.

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
limacharlie secret delete --key <agent-name> --confirm --oid <oid>
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

### Step 2: Check for Multi-SOC Coexistence

Before deleting records, check whether another SOC shares any hive keys with the SOC being removed. Shared keys exist between tiered-soc and baselining-soc:

| Hive | Shared Keys |
|------|-------------|
| `ai_agent` | `soc-l2-analyst`, `malware-analyst`, `containment`, `threat-hunter`, `soc-manager`, `soc-shift-reporter` |
| `dr-general` | `soc-l2-on-case-escalated`, `malware-analyst-on-mention`, `containment-on-mention`, `threat-hunter-on-mention`, `soc-manager-hourly`, `soc-shift-reporter-daily` |

For each hive key in the SOC being removed:
- **If the key is shared** and the other SOC is still installed: read the record, remove only the departing SOC's tags (any tag starting with `ai-team:<soc-being-removed>:` **or** `ai-rel:<soc-being-removed>:`), keep the other SOC's tags and all `global` / `api-key` tags, and write the record back. Do NOT delete the record.
- **If the key is NOT shared** (unique to this SOC): delete the record entirely.

### Step 3: Remove Non-Shared Hive Entries

Delete hive records that belong exclusively to the SOC being removed:

```bash
# For each NON-shared agent in the SOC:
limacharlie hive delete --hive-name ai_agent --key <agent-name> --confirm --oid <oid>
limacharlie hive delete --hive-name dr-general --key <dr-rule-name> --confirm --oid <oid>
```

### Step 3b: Clean Shared Hive Entries

For shared keys where the other SOC is still installed, strip only the departing SOC's tags:

```bash
# Read the current record
limacharlie hive get --hive-name ai_agent --key <shared-key> --oid <oid> --output yaml
# Remove tags starting with ai-team:<soc-being-removed>: or ai-rel:<soc-being-removed>: and write back
echo '<record JSON with only the remaining SOCs tags>' | limacharlie hive set --hive-name ai_agent --key <shared-key> --oid <oid>
```

### Step 4: Clean Up Secrets (Optional)

Ask the user if they want to remove per-agent API key secrets:

```bash
# For each agent secret:
limacharlie secret delete --key <agent-name> --confirm --oid <oid>
```

**Warn**: The `anthropic-key` secret may be shared with other agents or SOCs. Only delete if the user confirms no other agents depend on it. Shared agent secrets (e.g., `soc-l2-analyst`) should be kept if the other SOC is still installed.

### Step 5: Clean Up API Keys (Optional)

```bash
limacharlie api-key list --oid <oid> --output yaml
# Delete each agent's API key by hash (only for non-shared agents)
limacharlie api-key delete --key-hash <hash> --confirm --oid <oid>
```

### Step 6: Report to User

Summarize what was removed (agent definitions, D&R rules, secrets, API keys), what was left in place (shared records with tags stripped), and which SOC(s) remain active.

---

## Agent Reference: l1-bot

### Description
Automated Level 1 SOC analyst that investigates new security cases and documents findings for L2 review.

### Required Extensions
- `ext-cases` - Must be subscribed AND configured

### Required Secrets
| Secret Key | Description |
|-----------|-------------|
| `anthropic-key` | Anthropic API key (user provides) |
| `l1-bot` | LimaCharlie API key (can create for user) |

### Recommended API Key Permissions
For the `l1-bot` secret, create the API key with these permissions:
```
org.get,sensor.list,sensor.get,sensor.task,dr.list,insight.det.get,insight.evt.get,investigation.get,investigation.set,ext.request,org_notes.get,org_notes.set,ai_agent.operate
```

### Hive Entries Created
| Hive | Key | Description |
|------|-----|-------------|
| `ai_agent` | `l1-bot` | AI agent definition with investigation prompt |
| `dr-general` | `l1-bot-case-triage` | D&R rule triggering bot on case creation |

### How It's Triggered
When `ext-cases` creates a case, it emits a `created` event. The D&R rule matches events with a `case_id` field and starts the AI agent session with case context.

### Configuration
| Parameter | Value |
|-----------|-------|
| Model | `opus` |
| Max turns | 30 |
| Budget cap | $2.00 per investigation |
| Timeout | 600 seconds |
| Mode | One-shot (terminates after completion) |
| Debounce | `l1-bot` (one active session at a time, pending requests re-fire on completion) |
| Suppression | Max 10 invocations per minute |

