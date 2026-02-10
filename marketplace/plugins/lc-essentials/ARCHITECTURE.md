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
│  - Spawns sub-agents for API calls                         │
│  - Aggregates results                                       │
└─────────────────────────────────────────────────────────────┘
    │
    │ references function docs
    ▼
┌─────────────────────────────────────────────────────────────┐
│  limacharlie-call skill                                     │
│  - Central function documentation (143 functions)          │
│  - Parameter specifications in ./functions/*.md            │
│  - Defines the API Access Pattern                          │
└─────────────────────────────────────────────────────────────┘
    │
    │ spawns via Task tool
    ▼
┌─────────────────────────────────────────────────────────────┐
│  limacharlie-api-executor agent (Sonnet model)              │
│  - Executes single API operations                          │
│  - Handles large result downloads autonomously             │
│  - Returns structured JSON to parent                       │
└─────────────────────────────────────────────────────────────┘
    │
    │ calls MCP tool
    ▼
┌─────────────────────────────────────────────────────────────┐
│  mcp__plugin_lc-essentials_limacharlie__lc_call_tool       │
│  - Unified MCP tool for all LimaCharlie API operations     │
│  - Handles authentication, rate limiting, retries          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  LimaCharlie Platform API                                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Rules

### 1. Skills NEVER Call MCP Tools Directly

**Wrong:**
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="list_sensors",
  parameters={...}
)
```

**Right:**
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="sonnet",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {...}
    - Return: RAW
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

### 2. Only limacharlie-api-executor Calls MCP Tools

The executor agent is the only component that directly calls the MCP tool. This provides:
- **Reliability**: Sonnet model for accurate API operations
- **Consistency**: Better handling of complex parameters and responses
- **Parallel execution**: Multiple executors can run simultaneously
- **Large result handling**: Executor handles downloads autonomously

### 3. Parallel Execution Pattern

Spawn multiple agents in a SINGLE message for true parallelism:

```
# RIGHT - All in one message = parallel
Task(subagent_type="lc-essentials:limacharlie-api-executor", prompt="...org1...")
Task(subagent_type="lc-essentials:limacharlie-api-executor", prompt="...org2...")
Task(subagent_type="lc-essentials:limacharlie-api-executor", prompt="...org3...")

# WRONG - Sequential messages = sequential execution
Task(prompt="...org1...")
[wait for result]
Task(prompt="...org2...")
[wait for result]
```

### 4. Read Function Docs Before Calling

Before calling any LimaCharlie function, read its documentation:
```
Read ${CLAUDE_PLUGIN_ROOT}/skills/limacharlie-call/functions/{function-name}.md
```

Parameter names are often prefixed (e.g., `secret_name` not `name`). Wrong names cause silent failures.

## Component Types

### Skills (./skills/)

User-invocable capabilities that orchestrate workflows:

| Category | Skills |
|----------|--------|
| **Core API** | limacharlie-call |
| **Detection** | detection-engineering, detection-tuner, fp-pattern-finder |
| **Data Collection** | sensor-tasking, fleet-payload-tasking, velociraptor |
| **Analysis** | sensor-health, sensor-coverage, threat-report-evaluation |
| **Reporting** | reporting, graphic-output, web-ui-link |
| **Configuration** | adapter-assistant, parsing-helper, limacharlie-iac |
| **Onboarding** | init-lc, onboard-new-org, test-limacharlie-adapter, test-limacharlie-edr |
| **Documentation** | lookup-lc-doc, ask, add-new-skill |

### Agents (./agents/)

Sub-agents spawned by skills for specific tasks:

| Agent | Purpose | Model |
|-------|---------|-------|
| limacharlie-api-executor | Execute single API operations | sonnet |
| sensor-health-reporter | Check sensors for one org | sonnet |
| org-reporter | Collect reporting data for one org | sonnet |
| ioc-hunter | Search IOCs in one org | sonnet |
| behavior-hunter | Search behaviors via LCQL | sonnet |
| detection-builder | Generate D&R rules | sonnet |
| threat-report-parser | Parse threat reports, extract IOCs | sonnet |
| And more... | | |

## Critical Rules Summary

| Rule | Wrong | Right |
|------|-------|-------|
| **MCP Access** | Call `mcp__*` directly | Use `limacharlie-api-executor` |
| **LCQL Queries** | Write syntax manually | Use `generate_lcql_query()` first |
| **D&R Rules** | Write YAML manually | Use `generate_dr_rule_*()` functions |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (from `list_user_orgs`) |

## File Organization

```
lc-essentials/
├── ARCHITECTURE.md          # This file
├── CALLING_API.md           # Detailed API usage guide
├── skills/
│   ├── _shared/
│   │   └── SKILL_TEMPLATE.md  # Reference template
│   ├── limacharlie-call/
│   │   ├── SKILL.md         # Core skill with function index
│   │   └── functions/       # 143 function documentation files
│   └── [other-skills]/
│       └── SKILL.md
├── agents/
│   ├── README.md            # Agent registry
│   ├── limacharlie-api-executor.md
│   └── [other-agents].md
└── scripts/
    └── analyze-lc-result.sh # Large result schema analyzer
```
