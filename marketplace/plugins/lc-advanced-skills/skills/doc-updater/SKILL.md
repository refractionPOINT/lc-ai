---
name: doc-updater
description: Deploy and manage a daily AI agent that automatically updates GitHub documentation for a LimaCharlie organization. The agent collects org config, diffs against previous state, analyzes changes with full case/session context, renders Jinja2 templates, and pushes annotated updates to a GitHub repo. Templates are read from the lc-ai repo or a user-provided custom repo — no payloads needed. Use for "deploy doc updater", "set up automatic documentation", "install doc-updater agent", "update docs agent".
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
  │ AI Agent                                 │
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

## Template & Script Sources

Templates and scripts are read directly from the filesystem — **no payloads needed**.
The agent finds them in priority order:

| Priority | Source | How to configure |
|----------|--------|-----------------|
| 1 | **Explicit path** | Set `skill_path` in `doc-state` lookup |
| 2 | **Custom git repo** | Set `skill_repo` in `doc-state` lookup |
| 3 | **Default: local plugin** | `/opt/lc-advanced-skills/skills/doc-updater` (no config needed) |

### Default: local plugin directory (no config needed)

In the standard LimaCharlie AI agent runtime, plugin code is mounted at:
- `/opt/lc-essentials/` — core plugin
- `/opt/lc-advanced-skills/` — advanced skills plugin

The agent reads templates and scripts from:
```
/opt/lc-advanced-skills/skills/doc-updater/templates/
/opt/lc-advanced-skills/skills/doc-updater/scripts/
```

No payload uploads, no deployment steps, no drift. Updates to templates in the repo
are picked up on the next agent run automatically.

### Custom templates repo

Users who want to customize the doc templates can provide their own repo:
```yaml
# In the doc-state lookup:
skill_repo: "https://github.com/myorg/my-doc-templates"
```

The custom repo must follow the same directory structure:
```
my-doc-templates/
├── scripts/
│   ├── doc-exporter.py
│   ├── doc-renderer.py
│   └── doc-differ.py
└── templates/
    ├── readme.md.j2
    ├── architecture.md.j2
    ├── sensors.md.j2
    ├── detection-rules.md.j2
    ├── ai-agents.md.j2
    ├── data-pipeline.md.j2
    ├── access-control.md.j2
    ├── runbook-admin.md.j2
    ├── runbook-ir.md.j2
    └── runbook-updating.md.j2
```

### Explicit local path

For testing or non-standard layouts, set an explicit path:
```yaml
# In the doc-state lookup:
skill_path: "/home/user/my-custom-doc-updater"
```

## Components

| Component | Type | Description |
|-----------|------|-------------|
| `doc-updater` | AI Agent (hive) | Sonnet model, daily schedule |
| `doc-updater-daily` | D&R Rule | 24h_per_org schedule trigger |
| `doc-updater` | API Key + Secret | Scoped LC API key for config reads + case queries |
| `github-pat` | Secret | GitHub PAT for repo push access |
| `doc-state` | Lookup | Contains `repo_url`, template source config, and run metadata |

## Scripts (in `scripts/` directory)

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `doc-exporter.py` | OID | `config.yaml` | Collects all org config via LC CLI |
| `doc-differ.py` | old + new `config.yaml` | `diff.yaml` | Deterministic structural diff |
| `doc-renderer.py` | `config.yaml` + templates | 10 markdown files | Jinja2 template rendering |

## Templates (in `templates/` directory)

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

## Git Repo Structure (docs output)

```
<docs-repo>/
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
4. **(Optional) Custom template source** — ask if user wants custom templates

### Phase 2: Create API Key + Secrets

1. Create a scoped API key named `doc-updater` with permissions:
   `org.get`, `sensor.list`, `dr.list`, `fp.ctrl`, `ext.conf.get`,
   `investigation.get`, `investigation.set`, `lookup.get`, `lookup.set`,
   `org_notes.get`, `org_notes.set`, `sop.get`, `ai_agent.operate`,
   `audit.get`, `secret.get`

2. Store the API key as secret `doc-updater`
3. Store the GitHub PAT as secret `github-pat`

### Phase 3: Create Lookup

Create `doc-state` lookup with the repo URL and optional template source:

```yaml
# Minimum required:
repo_url: "https://github.com/<owner>/<repo>"

# Optional — custom template source:
# skill_path: "/path/to/custom/doc-updater"
# skill_repo: "https://github.com/myorg/my-doc-templates"
```

### Phase 4: Deploy Agent + Trigger Rule

Deploy from the `agent/` directory in this skill.

### Phase 5: Verify

The first run will treat everything as "new" and generate a comprehensive
initial changelog. Subsequent runs only document actual changes.

## What the Agent Does (vs Scripts)

| Task | Who Does It | Why |
|------|-------------|-----|
| Collect org config | `doc-exporter.py` | Deterministic, fast |
| Compare old vs new | `doc-differ.py` | Deterministic, structural |
| **Investigate WHY changes happened** | **AI Agent** | **Queries cases, AI sessions, audit logs** |
| **Write contextual changelog** | **AI Agent** | **Natural language with case references** |
| **Write rich commit message** | **AI Agent** | **Summarizes with context** |
| Render markdown from templates | `doc-renderer.py` | Deterministic Jinja2 |
| Git operations | Shell commands | Mechanical push |

## Updating Templates

Since templates are read directly from the repo (not payloads):
- Edit `.j2` files in `templates/` and commit
- Next agent run automatically picks up the changes
- No redeployment or payload re-upload needed

For custom template repos: push changes to the custom repo. Same effect.

## Removing the Agent

```bash
limacharlie hive delete --hive-name ai_agent --key doc-updater --oid <oid> --confirm
limacharlie dr delete --key doc-updater-daily --oid <oid> --confirm

# Delete secrets
limacharlie secret delete --key doc-updater --oid <oid> --confirm
limacharlie secret delete --key github-pat --oid <oid> --confirm

# Delete lookup
limacharlie lookup delete --key doc-state --oid <oid> --confirm

# Delete API key
limacharlie api-key delete --key-hash <hash> --oid <oid> --confirm
```
