---
name: org-documentation
description: Generate comprehensive architecture and operations documentation for one or more LimaCharlie organizations. Accepts org names or OIDs. Produces markdown files covering sensors, D&R rules, AI agents, extensions, outputs, cloud adapters, access control, and operational runbooks. Includes Mermaid diagrams, GitHub callouts, collapsible sections, and verified LC docs links. Use for "document this org", "document all my orgs", "create architecture docs", "generate a wiki", "org inventory".
allowed-tools:
  - Task
  - Read
  - Bash
  - Write
  - Glob
  - Grep
  - Edit
  - AskUserQuestion
---

# LimaCharlie Organization Documentation Generator

Generate complete, wiki-ready architecture and operations guides for one or more LimaCharlie organizations. Supports single org, multiple orgs by name or OID, or all accessible orgs.

***

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
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |
| **Secrets** | Include values in docs | Only document secret **names**, NEVER values |

***

## Overview

This skill generates a complete set of markdown documentation files for a LimaCharlie organization, suitable for upload to a GitHub wiki, MkDocs site, or Confluence. The output covers:

- System architecture and data flow diagrams (Mermaid)
- Sensor inventory (EDR, extensions, cloud adapters)
- D&R rule catalog organized by category
- AI agent teams, workflows, and inter-agent communication
- Extension subscriptions and data pipeline
- Access control (API keys, secrets, installation keys, SOPs)
- Operational runbooks for day-to-day administration
- Automation scripts for keeping documentation current

## When to Use

- **"Document this org"** / **"Create architecture docs for white-sands"**
- **"Generate a wiki for all my orgs"** / **"Document all organizations"**
- **"Create docs for white-sands and red-rock"** (multiple by name)
- **"Document orgs b85fd2bd-... and c1ffedc0-..."** (multiple by OID)
- **"Create onboarding documentation for a new SOC engineer"**
- **"Audit the org configuration and produce a report"**
- **"Export org architecture to markdown"**

## Workflow

### Phase 1: Gather Requirements

1. **Identify the target organization(s)**. The user may specify:
   - A single org by name or OID
   - Multiple orgs by name or OID (comma-separated or listed)
   - "all" / "all orgs" / "every org" to document all accessible organizations

   First, list all accessible orgs to resolve names to OIDs:
   ```bash
   limacharlie org list --output yaml
   ```

   **Resolving org identifiers:**
   - If the user provides a UUID (matches `[0-9a-f-]{36}`), use it directly as the OID
   - If the user provides a name, match it against the `name` field from `org list`
   - If the user says "all", use every org returned by `org list`
   - If an org name doesn't match, ask the user to clarify — never guess

2. **Ask where to write the output**:
   - Single org: default `./docs/<org-name>/`
   - Multiple orgs: default `./docs/` with subdirectories per org: `./docs/<org-name>/`
   Confirm with the user.

3. **Check for optional GitHub repo creation**: Ask if they want the docs pushed to a new GitHub repo.

### Phase 2: Collect Organization Data

Spawn one `org-doc-collector` sub-agent **per organization** to gather the full configuration inventory. For multiple orgs, spawn ALL agents in a **SINGLE message** for parallel execution.

**Single org:**
```
Task(
  subagent_type="lc-advanced-skills:org-doc-collector",
  prompt="Collect full configuration inventory for organization '<org-name>' (OID: <oid>)."
)
```

**Multiple orgs (spawn ALL in parallel in one message):**
```
Task(
  subagent_type="lc-advanced-skills:org-doc-collector",
  prompt="Collect full configuration inventory for organization '<org-1-name>' (OID: <oid-1>)."
)
Task(
  subagent_type="lc-advanced-skills:org-doc-collector",
  prompt="Collect full configuration inventory for organization '<org-2-name>' (OID: <oid-2>)."
)
// ... one per org, all in the same message
```

Each agent returns a structured YAML document with all sensors, rules, agents, extensions, etc.

### Phase 3: Generate Documentation Files

For **each organization**, generate a complete set of documentation files under `<output-dir>/<org-name>/`. Use the templates below as the structure — populate them with the actual data from that org's collector agent.

If documenting multiple orgs, also generate a top-level `README.md` index at `<output-dir>/README.md` that links to each org's documentation:

```markdown
# LimaCharlie Organization Documentation

| Organization | OID | Docs |
|--------------|-----|------|
| <org-1-name> | `<oid-1>` | [View docs](<org-1-name>/README.md) |
| <org-2-name> | `<oid-2>` | [View docs](<org-2-name>/README.md) |
```

**Files to generate:**

| File | Content |
|------|---------|
| `README.md` | Main entry point with badges, Mermaid overview, navigation flowchart |
| `architecture.md` | System topology, data flow diagrams for each pipeline |
| `sensors.md` | EDR sensors, extension sensors, tags, health monitoring |
| `detection-rules.md` | D&R rules by category with chaining diagram and pie chart |
| `ai-agents.md` | Agent teams, pipeline flows, budgets, secrets mapping |
| `data-pipeline.md` | Extensions, cloud adapters, outputs, lookups, payloads |
| `access-control.md` | API keys, secrets, installation keys, SOPs, rotation checklist |
| `runbooks/common-admin-tasks.md` | Day-to-day CLI operations |
| `runbooks/incident-response.md` | How the SOC pipeline handles incidents |
| `runbooks/updating-docs.md` | Export script, CI workflow, review cadence |

### Phase 4: Optional GitHub Push

If the user requested GitHub repo creation:

1. Confirm the GitHub account and repo name
2. Create the repo: `gh repo create <account>/<repo-name> --private`
3. Initialize git in the output directory, commit all files, and push
4. Ensure no sensitive data (secret values, webhook URLs, IPs) is committed
5. For multi-org docs, push all org subdirectories + the top-level index as a single repo

### Error Handling (Multi-Org)

If one org's collector agent fails:
- Document the failure in the top-level README index
- Continue generating docs for all other orgs
- Report which orgs succeeded and which failed at the end

***

## Documentation Templates

### Template: README.md

```markdown
# <Org-Name> Organization — Architecture & Operations Guide

![Org: <org-name>](https://img.shields.io/badge/Org-<org-name-url-encoded>-blue)
![OID](https://img.shields.io/badge/OID-<oid-abbreviated>-lightgrey)
![Last Updated](https://img.shields.io/badge/Last_Updated-<YYYY--MM--DD>-green)
![Owner](https://img.shields.io/badge/Owner-SOC_Engineering-purple)

Complete operational reference for the **<org-name>** LimaCharlie organization.

> [!IMPORTANT]
> **OID**: Always use `<oid>` (never the org name) in all CLI commands.
> All commands require `--output yaml`. Timestamps in API params are epoch **seconds** (10 digits).

***

## Architecture at a Glance

<!-- Mermaid flowchart showing: Data Sources → D&R Engine → AI Agent Teams → Outputs -->
<!-- Adapt based on what actually exists in the org -->

***

## Where Do I Start?

> New to LimaCharlie? Start with the [Quickstart Guide](https://docs.limacharlie.io/1-getting-started/quickstart/) and [Core Concepts](https://docs.limacharlie.io/1-getting-started/core-concepts/).

<!-- Mermaid decision flowchart linking to each doc file -->

***

## Documentation Map

| | Document | Description |
|---|----------|-------------|
| **Core** | [Architecture Overview](architecture.md) | System topology and data flow |
| **Core** | [Sensors & Endpoints](sensors.md) | EDR, extensions, cloud adapters |
| **Core** | [Detection & Response Rules](detection-rules.md) | Rule catalog by category |
| **Core** | [AI Agents & Automation](ai-agents.md) | Agent teams and workflows |
| **Core** | [Data Pipeline](data-pipeline.md) | Extensions, outputs, lookups |
| **Core** | [Access Control](access-control.md) | Keys, secrets, SOPs |
| **Runbook** | [Common Admin Tasks](runbooks/common-admin-tasks.md) | Day-to-day operations |
| **Runbook** | [Incident Response](runbooks/incident-response.md) | SOC pipeline and manual IR |
| **Runbook** | [Updating Docs](runbooks/updating-docs.md) | Automation and review |

***

## System Overview

<!-- Table of capabilities: EDR Coverage, SOC agents, BAS, Intel, etc. -->
<!-- Only include rows for capabilities that actually exist -->

***

## Key Resources

| Resource | Access |
|----------|--------|
| LimaCharlie Web UI | `https://app.limacharlie.io` |
| CLI Auth Check | `limacharlie auth whoami --output yaml` |
| LimaCharlie Docs | [docs.limacharlie.io](https://docs.limacharlie.io) |
```

### Template: architecture.md

Structure:
1. **System Topology** — Mermaid `graph TB` with subgraphs for Data Sources, D&R Engine, AI Agent Layer, Outputs, Managed Rule Packs. Only include subgraphs for components that actually exist.
2. **Data Flow sections** — One Mermaid `flowchart` per pipeline:
   - Telemetry Ingestion (always present)
   - SOC Pipeline (if SOC agents exist)
   - BAS Pipeline (if BAS agents exist)
   - Intel Pipeline (if Intel agents exist)
   - Other pipelines (based on D&R rule chaining patterns)
3. **Infrastructure** — Sensor summary table (no IPs or internal hostnames)
4. **Cloud Integrations** — Adapter status table
5. **Key Design Decisions** — Numbered list in `> [!TIP]` callout

### Template: sensors.md

Structure:
1. **EDR Sensors** table (hostname, SID, platform, version, status, isolated, enrolled)
   - `> [!NOTE]` for security redaction of IPs
   - `> [!WARNING]` for offline sensors
2. **Extension Sensors** in collapsible `<details>` (they're always a long list)
3. **Offline Sensors** table (if any)
4. **Sensor Tags** table
5. **Health Monitoring** — CLI commands in collapsible `<details>`
6. **Known Issues** — `> [!WARNING]` callout
7. **Further Reading** — Links to LC docs

### Template: detection-rules.md

Structure:
1. **Overview** with rule state definitions and links to [D&R docs](https://docs.limacharlie.io/3-detection-response/), [detection operators](https://docs.limacharlie.io/8-reference/detection-logic-operators/), [response actions](https://docs.limacharlie.io/8-reference/response-actions/)
2. **Rule Chaining diagram** — Mermaid `flowchart LR` showing feedback loops between telemetry, rules, agents, lookups
3. **Rule Category Summary** — Mermaid `pie` chart
4. **Category sections** — One per category with tables. Use collapsible `<details>` for categories with 5+ rules
5. **AI Trigger rules** — `> [!CAUTION]` warning that disabling them stops automation
6. **Managed Rule Packs** — Link each to its Soteria docs page
7. **FP Rules** section
8. **CLI Commands** in collapsible `<details>`
9. **Review Queue** — `> [!WARNING]` listing all disabled rules awaiting review
10. **Further Reading** — Links to LC docs

### Template: ai-agents.md

Structure:
1. **Overview** with links to [AI Sessions](https://docs.limacharlie.io/9-ai-sessions/), [D&R sessions](https://docs.limacharlie.io/9-ai-sessions/dr-sessions/), [config hive](https://docs.limacharlie.io/7-administration/config-hive/), [ext-cases](https://docs.limacharlie.io/5-integrations/extensions/limacharlie/cases/)
2. `> [!IMPORTANT]` about shared Anthropic key dependency
3. **Team sections** — One per team with:
   - Mermaid `flowchart` showing the pipeline (for teams with chained agents)
   - Agent table (name, model, trigger, schedule, budget, TTL, purpose)
   - Inter-agent communication tags table (if applicable)
   - Mention triggers table (if applicable)
4. **Agent Configuration** — Common settings, budget summary table
5. **Secrets mapping** in collapsible `<details>`
6. **CLI Commands** in collapsible `<details>`
7. **Troubleshooting** — `> [!TIP]` callouts
8. **Further Reading**

### Template: data-pipeline.md

Structure:
1. **Extensions** — Grouped by category, each extension name linked to its LC docs page
2. **Cloud Adapters** — Mermaid architecture diagram + adapter tables (active/disabled)
3. **Outputs** — Table + `> [!WARNING]` for missing output destinations
4. **Payloads** in collapsible `<details>`
5. **Lookups** table
6. **Services NOT Registered** — `> [!CAUTION]` callout
7. **Further Reading**

### Template: access-control.md

Structure:
1. **API Keys** — Agent keys in collapsible `<details>`, `> [!CAUTION]` about extension keys
2. **Secrets** — `> [!IMPORTANT]` about Anthropic key, table of names only
3. **Installation Keys** — User-created vs system keys
4. **SOPs** — Content summary, `> [!NOTE]` callout
5. **Key Rotation Checklist** — `> [!TIP]` about zero-downtime rotation
6. **Further Reading**

### Template: runbooks/common-admin-tasks.md

Sections for: Sensor Management, D&R Rule Management, AI Agent Management, Case Management, Extension Operations, LCQL Queries, Lookup Tables, Troubleshooting Quick Reference table.

Each section has CLI commands and links to relevant LC docs.

### Template: runbooks/incident-response.md

Structure:
1. **Pipeline Overview** — Mermaid `flowchart` with color-coded outcomes (green=resolved, red=containment, yellow=manual)
2. **When to Intervene** — 4 scenarios with CLI commands
3. **Manual IR** — Step-by-step with `> [!NOTE]` callout
4. **Emergency Shutdown** — `> [!CAUTION]` with disable commands
5. **Escalation Path** — Mermaid `flowchart LR`

### Template: runbooks/updating-docs.md

Structure:
1. **Export Script** in collapsible `<details>` — bash script that exports all config to YAML files
2. **GitHub Actions Workflow** in collapsible `<details>`
3. **Manual Update Procedures** — When-to-update table
4. **Documentation Standards** — `> [!CAUTION]` for sensitive data, `> [!NOTE]` for formatting
5. **Review Cadence** table

***

## Verified LimaCharlie Documentation Links

Use ONLY these verified links. Do NOT guess or construct URLs.

### Core
- Quickstart: `https://docs.limacharlie.io/1-getting-started/quickstart/`
- Core Concepts: `https://docs.limacharlie.io/1-getting-started/core-concepts/`

### Sensors
- Deployment Overview: `https://docs.limacharlie.io/2-sensors-deployment/`
- Installation Keys: `https://docs.limacharlie.io/2-sensors-deployment/installation-keys/`
- Sensor Tags: `https://docs.limacharlie.io/2-sensors-deployment/sensor-tags/`
- Cloud Adapters: `https://docs.limacharlie.io/2-sensors-deployment/adapters/`
- Azure Event Hub: `https://docs.limacharlie.io/2-sensors-deployment/adapters/types/azure-event-hub/`
- MS Defender Adapter: `https://docs.limacharlie.io/2-sensors-deployment/adapters/types/microsoft-defender/`
- Payloads: `https://docs.limacharlie.io/2-sensors-deployment/endpoint-agent/payloads/`

### Detection & Response
- D&R Overview: `https://docs.limacharlie.io/3-detection-response/`
- Writing & Testing Rules: `https://docs.limacharlie.io/3-detection-response/tutorials/writing-testing-rules/`
- False Positives: `https://docs.limacharlie.io/3-detection-response/false-positives/`
- Unit Tests: `https://docs.limacharlie.io/3-detection-response/unit-tests/`
- Soteria EDR: `https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/edr/`
- Soteria AWS: `https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/aws/`
- Soteria M365: `https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/m365/`
- Detection Operators: `https://docs.limacharlie.io/8-reference/detection-logic-operators/`
- Response Actions: `https://docs.limacharlie.io/8-reference/response-actions/`

### Data & Queries
- LCQL: `https://docs.limacharlie.io/4-data-queries/`

### Extensions
- Extensions Overview: `https://docs.limacharlie.io/5-integrations/extensions/`
- ext-cases: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/cases/`
- ext-reliable-tasking: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/reliable-tasking/`
- ext-integrity: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/integrity/`
- ext-exfil: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/exfil/`
- ext-sensor-cull: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/sensor-cull/`
- ext-dumper: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/dumper/`
- ext-artifact: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/artifact/`
- ext-binlib: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/binlib/`
- ext-lookup-manager: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/lookup-manager/`
- ext-payload-manager: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/payload-manager/`
- ext-yara-manager: `https://docs.limacharlie.io/5-integrations/extensions/limacharlie/yara-manager/`
- ext-velociraptor: `https://docs.limacharlie.io/5-integrations/extensions/third-party/velociraptor/`
- ext-hayabusa: `https://docs.limacharlie.io/5-integrations/extensions/third-party/hayabusa/`
- ext-plaso: `https://docs.limacharlie.io/5-integrations/extensions/third-party/plaso/`
- ext-atomic-red-team: `https://docs.limacharlie.io/5-integrations/extensions/third-party/atomic-red-team/`
- ext-yara: `https://docs.limacharlie.io/5-integrations/extensions/third-party/yara/`
- ext-zeek: `https://docs.limacharlie.io/5-integrations/extensions/third-party/zeek/`
- ext-pagerduty: `https://docs.limacharlie.io/5-integrations/extensions/third-party/pagerduty/`
- ext-twilio: `https://docs.limacharlie.io/5-integrations/extensions/third-party/twilio/`
- ext-govee: `https://docs.limacharlie.io/5-integrations/extensions/third-party/govee/`

### Outputs
- Outputs Overview: `https://docs.limacharlie.io/5-integrations/outputs/`
- Webhook Output: `https://docs.limacharlie.io/5-integrations/outputs/destinations/webhook/`
- BigQuery Output: `https://docs.limacharlie.io/5-integrations/outputs/destinations/bigquery/`

### API Integrations
- VirusTotal: `https://docs.limacharlie.io/5-integrations/api-integrations/virustotal/`
- GreyNoise: `https://docs.limacharlie.io/5-integrations/api-integrations/greynoise/`

### Services
- Replay: `https://docs.limacharlie.io/5-integrations/services/replay/`

### Administration
- API Keys: `https://docs.limacharlie.io/7-administration/access/api-keys/`
- Config Hive: `https://docs.limacharlie.io/7-administration/config-hive/`
- Lookups: `https://docs.limacharlie.io/7-administration/config-hive/lookups/`
- Secrets: `https://docs.limacharlie.io/7-administration/config-hive/secrets/`
- D&R Rules Config: `https://docs.limacharlie.io/7-administration/config-hive/dr-rules/`

### Reference
- Endpoint Commands: `https://docs.limacharlie.io/8-reference/endpoint-commands/`
- Permissions: `https://docs.limacharlie.io/8-reference/permissions/`
- Sensor Selectors: `https://docs.limacharlie.io/8-reference/sensor-selector-expressions/`

### AI
- AI Sessions: `https://docs.limacharlie.io/9-ai-sessions/`
- D&R-Triggered Sessions: `https://docs.limacharlie.io/9-ai-sessions/dr-sessions/`

### CLI
- CLI / SDK Overview: `https://docs.limacharlie.io/6-developer-guide/sdk-overview/`

***

## Visual Standards

All generated documentation MUST use these GitHub-compatible features:

### Mermaid Diagrams
- System topology: `graph TB` with subgraphs
- Data flows: `flowchart TD` or `flowchart LR`
- Rule distribution: `pie` chart
- Decision trees: `flowchart TD` with clickable nodes
- Color coding: green (#2d6a2d) = resolved, red (#8b1a1a) = containment, yellow (#8b6914) = manual, blue (#1a5276) = agents, purple (#6c3483) = intel
- **NEVER use `@` in Mermaid edge labels** — it breaks the parser. Use `mention:` prefix instead (e.g., `|"mention: malware-analyst"|` not `|"@malware-analyst"|`)

### GitHub Alert Callouts
- `> [!CAUTION]` — Destructive/irreversible actions (emergency shutdown, deleting keys)
- `> [!WARNING]` — Needs attention (offline sensors, review queues, missing outputs)
- `> [!IMPORTANT]` — Key dependencies (Anthropic key, OID format)
- `> [!TIP]` — Helpful shortcuts (design decisions, troubleshooting, replay thresholds)
- `> [!NOTE]` — Supplementary info (security redactions, formatting standards)

### Collapsible Sections
Use `<details><summary>` for:
- Tables with 5+ rows that aren't primary content (extension sensors, API keys)
- CLI command reference sections
- Payloads, BAS workflow details, export scripts
- GitHub Actions workflows

### Other
- Shields.io badges in README.md header
- Horizontal rules (`---`) between major sections
- Tables for all inventories
- "Further Reading" sections with links to LC docs at the bottom of each file

***

## Security Rules

1. **NEVER include secret values** — only document secret names
2. **NEVER include API key tokens** — only names and permission summaries
3. **NEVER include webhook URLs or secrets** — reference them generically
4. **NEVER include external/internal IP addresses** — note they're available via CLI
5. **NEVER include full internal hostnames** (FQDNs) — use short hostnames only
6. **NEVER include connection strings** (Azure Event Hub, etc.) — note they exist
7. Installation key UUIDs are safe to include
8. Sensor SIDs are safe to include

***

## Adaptability

The templates above are designed for a **fully-featured** org with EDR sensors, AI agents, BAS pipeline, intel pipeline, and managed rule packs. For simpler orgs:

- **No AI agents?** → Skip `ai-agents.md`, simplify architecture diagrams, remove agent-related sections from runbooks
- **No BAS pipeline?** → Skip BAS sections in architecture and detection rules
- **No managed rule packs?** → Skip Category 8 in detection rules
- **Single sensor?** → Simplify sensors.md, skip fleet-related runbook sections
- **No extensions?** → Simplify data-pipeline.md to just outputs and adapters

Always generate documentation proportional to the org's actual complexity. Don't create empty sections or placeholder content.
