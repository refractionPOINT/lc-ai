# LimaCharlie Essentials Plugin Architecture

This document describes the hierarchy and design patterns used in the lc-essentials plugin.

## Plugin Hierarchy

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill (e.g., detection-engineering, sensor-health, etc.)  │
│  - Orchestrates workflow                                    │
│  - Calls CLI directly via Bash for simple operations       │
│  - Spawns sub-agents for parallel multi-org/multi-item work│
│  - Aggregates results                                       │
└─────────────────────────────────────────────────────────────┘
    │                          │
    │ direct CLI calls         │ spawns via Task tool
    ▼                          ▼
┌──────────────────┐  ┌─────────────────────────────────────────┐
│  limacharlie CLI │  │  Specialized Agent (e.g., org-reporter) │
│  via Bash        │  │  - Handles ONE org/item                  │
│                  │  │  - Calls CLI directly via Bash            │
│  limacharlie     │  │  - Returns structured data to parent     │
│  <noun> <verb>   │  └─────────────────────────────────────────┘
│  --oid <oid>     │                    │
│  --output json   │                    │ direct CLI calls
└────────┬─────────┘                    ▼
         │                    ┌──────────────────┐
         │                    │  limacharlie CLI │
         │                    │  via Bash        │
         ▼                    └────────┬─────────┘
┌─────────────────────────────────────────────────────────────┐
│  LimaCharlie Platform API                                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Rules

### 1. Skills Call CLI Directly via Bash

**Wrong:**
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="list_sensors",
  parameters={...}
)
```

**Also Wrong:**
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors ..."
)
```

**Right:**
```bash
limacharlie sensor list --oid <oid> --output json
```

### 2. All Agents Call CLI Directly Too

Specialized agents (sensor-health-reporter, org-reporter, etc.) call the CLI directly via Bash. There is no intermediate api-executor agent.

### 3. Use `--ai-help` for Command Documentation

When unsure about a CLI command's flags:
```bash
limacharlie <command> --ai-help
```

### 4. Always Pass `--output json`

All CLI operations must include `--output json` for machine-readable output.

### 5. Parallel Execution Pattern

Spawn multiple agents in a SINGLE message for true parallelism:

```
# RIGHT - All in one message = parallel
Task(subagent_type="lc-essentials:sensor-health-reporter", prompt="...org1...")
Task(subagent_type="lc-essentials:sensor-health-reporter", prompt="...org2...")
Task(subagent_type="lc-essentials:sensor-health-reporter", prompt="...org3...")

# WRONG - Sequential messages = sequential execution
Task(prompt="...org1...")
[wait for result]
Task(prompt="...org2...")
[wait for result]
```

## Component Types

### Skills (./skills/)

User-invocable capabilities that orchestrate workflows:

| Category | Skills |
|----------|--------|
| **Detection** | detection-engineering, detection-tuner, fp-pattern-finder |
| **Data Collection** | sensor-tasking, fleet-payload-tasking, velociraptor |
| **Analysis** | sensor-health, sensor-coverage, threat-report-evaluation |
| **Reporting** | reporting, graphic-output, web-ui-link |
| **Configuration** | adapter-assistant, parsing-helper, limacharlie-iac |
| **Onboarding** | init-lc, onboard-new-org, test-limacharlie-adapter, test-limacharlie-edr |
| **Documentation** | lookup-lc-doc, ask, add-new-skill |

### Agents (./agents/)

Sub-agents spawned by skills for specific tasks. All agents call the CLI directly via Bash:

| Agent | Purpose | Model |
|-------|---------|-------|
| sensor-health-reporter | Check sensors for one org | sonnet |
| org-reporter | Collect reporting data for one org | sonnet |
| org-coverage-reporter | Collect coverage data for one org | sonnet |
| ioc-hunter | Search IOCs in one org | sonnet |
| behavior-hunter | Search behaviors via LCQL | sonnet |
| detection-builder | Generate D&R rules | sonnet |
| dr-replay-tester | Test D&R rules via replay | sonnet |
| threat-report-parser | Parse threat reports, extract IOCs | sonnet |
| asset-profiler | Profile a single sensor | sonnet |
| gap-analyzer | Analyze coverage gaps for one org | sonnet |
| sensor-tasking-executor | Execute tasks on one sensor | sonnet |
| fp-pattern-investigator | Investigate one FP pattern | sonnet |
| multi-org-adapter-auditor | Audit adapters for one org | sonnet |
| cloud-discoverer | Survey one cloud platform | sonnet |
| vm-edr-installer | Deploy EDR on one cloud platform | sonnet |
| fleet-pattern-analyzer | Analyze cross-tenant patterns | sonnet |
| adapter-doc-researcher | Research adapter docs | sonnet |
| html-renderer | Render HTML dashboards | sonnet |

## Critical Rules Summary

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **LCQL Queries** | Write syntax manually | Use `limacharlie ai generate-query` first |
| **D&R Rules** | Write YAML manually | Use `limacharlie ai generate-*` + `limacharlie rule validate` |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (from `limacharlie org list`) |

## File Organization

```
lc-essentials/
├── ARCHITECTURE.md          # This file
├── AUTOINIT.md              # Bootstrap procedure
├── CALLING_API.md           # CLI usage guide
├── CONSTANTS.md             # Platform codes, IOC types, timestamps
├── skills/
│   ├── _shared/
│   │   └── SKILL_TEMPLATE.md  # Reference template
│   └── [skill-name]/
│       └── SKILL.md
├── agents/
│   ├── README.md            # Agent registry
│   └── [agent-name].md
├── commands/
│   ├── add-new-skill.md
│   └── init-lc.md
└── scripts/
    └── render-html.py       # HTML rendering script
```
