---
name: doc-updater
description: Deploy and manage a daily AI agent that automatically updates GitHub documentation for a LimaCharlie organization. The agent collects org config, diffs against previous state, analyzes changes with full case/session context, renders Jinja2 templates, and pushes annotated updates to a GitHub repo. Use for "deploy doc updater", "set up automatic documentation", "install doc-updater agent", "update docs agent".
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# Doc-Updater Agent Deployment

Deploy a daily AI agent that keeps GitHub documentation in sync with a LimaCharlie organization's configuration — with contextual explanations for every change.

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
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |
| **Secrets** | Include values in outputs | Only document secret **names**, NEVER values |

***

## Architecture

```
EXPORT → DIFF → ANALYZE → RENDER → PUSH

  ┌─────────────────┐
  │ doc-exporter.py  │  LC CLI → config.yaml (current state)
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ doc-differ.py    │  config.yaml (old vs new) → diff.yaml
  └────────┬────────┘
           │
  ┌────────▼─────────────────────────────────┐
  │ AI Agent (Claude)                        │
  │                                          │
  │  Reads diff.yaml, queries LC cases and   │
  │  AI sessions for context, generates:     │
  │  - recent_changes (for README template)  │
  │  - CHANGELOG.md entry                    │
  │  - Rich git commit message               │
  └────────┬─────────────────────────────────┘
           │
  ┌────────▼────────┐
  │ doc-renderer.py  │  config.yaml + templates → 10 markdown files
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ git push         │  commit annotated docs + config snapshot
  └─────────────────┘
```

The scripts handle mechanical work. The AI agent handles the intelligence:
investigating WHY things changed and writing explanations with case references.

## Components

| Component | Type | Description |
|-----------|------|-------------|
| `doc-updater` | AI Agent (hive) | Sonnet model, daily schedule |
| `doc-updater-daily` | D&R Rule | 24h_per_org schedule trigger |
| `doc-updater` | API Key + Secret | Scoped LC API key for config reads + case queries |
| `github-pat` | Secret | GitHub PAT for repo push access |
| `doc-state` | Lookup | Contains `repo_url` and `last_updated` |
| `doc-exporter.py` | Payload | Collects org config → config.yaml |
| `doc-renderer.py` | Payload | Renders Jinja2 templates → markdown |
| `doc-differ.py` | Payload | Compares old vs new config → structured diff |
| `doc-tpl-*` | Payloads | 10 Jinja2 documentation templates |

## Scripts

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `doc-exporter.py` | OID | `config.yaml` | Collects all org config via LC CLI |
| `doc-differ.py` | old + new `config.yaml` | `diff.yaml` | Deterministic structural diff |
| `doc-renderer.py` | `config.yaml` + templates | 10 markdown files | Jinja2 template rendering |

## Templates

Stored in `templates/` directory, uploaded as payloads with `doc-tpl-` prefix:

| Template | Output File |
|----------|------------|
| `readme.md.j2` | `README.md` (includes Recent Changes section) |
| `architecture.md.j2` | `architecture.md` |
| `sensors.md.j2` | `sensors.md` |
| `detection-rules.md.j2` | `detection-rules.md` |
| `ai-agents.md.j2` | `ai-agents.md` |
| `data-pipeline.md.j2` | `data-pipeline.md` |
| `access-control.md.j2` | `access-control.md` |
| `runbook-admin.md.j2` | `runbooks/common-admin-tasks.md` |
| `runbook-ir.md.j2` | `runbooks/incident-response.md` |
| `runbook-updating.md.j2` | `runbooks/updating-docs.md` |

## Git Repo Structure

The agent maintains this structure in the target GitHub repo:

```
<repo>/
├── README.md                 # Includes "Recent Changes" section
├── CHANGELOG.md              # Accumulates change entries with context
├── architecture.md
├── sensors.md
├── detection-rules.md
├── ai-agents.md
├── data-pipeline.md
├── access-control.md
├── runbooks/
│   ├── common-admin-tasks.md
│   ├── incident-response.md
│   └── updating-docs.md
└── .doc-updater/
    └── config.yaml           # Config snapshot for next run's diff
```

## Deployment Workflow

### Phase 1: Gather Requirements

1. **Identify the target organization** — resolve name to OID
2. **Get the GitHub repo URL** — existing or create new (must be HTTPS)
3. **Get the GitHub PAT** — user provides a PAT with `repo` scope
4. **Confirm deployment**

### Phase 2: Upload Payloads

Upload all scripts and templates from this skill's directory:

```bash
SKILL_DIR="<base_directory_for_this_skill>"

# Upload scripts
for script in doc-exporter.py doc-renderer.py doc-differ.py; do
  limacharlie payload set --name "$script" \
    --file "$SKILL_DIR/scripts/$script" --oid <oid>
done

# Upload templates
for template in "$SKILL_DIR/templates/"*.j2; do
  name="doc-tpl-$(basename "$template")"
  limacharlie payload set --name "$name" \
    --file "$template" --oid <oid>
done
```

### Phase 3: Create API Key + Secrets

1. Create a scoped API key named `doc-updater` with permissions:
   `org.get`, `sensor.list`, `dr.list`, `fp.ctrl`, `ext.conf.get`,
   `investigation.get`, `investigation.set`, `lookup.get`, `lookup.set`,
   `org_notes.get`, `sop.get`, `ai_agent.operate`, `payload.ctrl`

2. Store the API key as secret `doc-updater`
3. Store the GitHub PAT as secret `github-pat`

### Phase 4: Create Lookup

Create `doc-state` lookup with the repo URL:

```bash
limacharlie lookup set --name doc-state --oid <oid> \
  --data '{"repo_url": "https://github.com/<owner>/<repo>"}'
```

### Phase 5: Deploy Agent + Trigger Rule

Deploy from the `agent/` directory:

```bash
limacharlie hive set ai_agent --key doc-updater --oid <oid> \
  --input-file agent/hives/ai_agent.yaml

# Deploy trigger rule
limacharlie dr set --name doc-updater-daily --oid <oid> \
  --input-file agent/hives/dr-general.yaml
```

### Phase 6: Initial Run

For the first run, the differ will detect everything as "new" and the agent
will generate a comprehensive initial changelog. Subsequent runs will only
document actual changes.

Manually trigger or wait for the 24h schedule.

## What the Agent Actually Does (vs Scripts)

| Task | Who Does It | Why |
|------|-------------|-----|
| Collect org config | `doc-exporter.py` | Deterministic, fast, no AI needed |
| Compare old vs new | `doc-differ.py` | Deterministic, structural comparison |
| **Investigate WHY changes happened** | **AI Agent** | **Queries cases, AI sessions, detections** |
| **Write contextual changelog** | **AI Agent** | **Natural language explanations** |
| **Write rich commit message** | **AI Agent** | **Summarizes with case references** |
| Render markdown from templates | `doc-renderer.py` | Deterministic Jinja2 rendering |
| Git operations | Shell commands | Mechanical push |

The AI budget goes to the analysis step — querying LC for context and
writing explanations. Not to running scripts.

## Updating Templates

1. Edit `.j2` files in this skill's `templates/` directory
2. Re-run Phase 2 to re-upload payloads
3. Next agent run uses updated templates

## Removing the Agent

```bash
limacharlie hive delete ai_agent --key doc-updater --oid <oid>
limacharlie dr delete --name doc-updater-daily --oid <oid>

# Delete payloads
for p in doc-exporter.py doc-renderer.py doc-differ.py; do
  limacharlie payload delete --name "$p" --oid <oid>
done
for name in $(limacharlie payload list --oid <oid> --output yaml | grep 'doc-tpl-'); do
  limacharlie payload delete --name "$name" --oid <oid>
done

# Delete secrets
limacharlie secret delete --key doc-updater --oid <oid>
limacharlie secret delete --key github-pat --oid <oid>

# Delete lookup
limacharlie lookup delete --name doc-state --oid <oid>
```
