# LimaCharlie Agents

Autonomous AI agents that run inside LimaCharlie organizations. Each agent is deployed as Infrastructure as Code (IaC) via hive configurations and triggered by D&R rules.

## Agent Categories

| Category | Description |
|----------|-------------|
| [analyst](analyst/) | General-purpose analysts invoked on demand via @mentions |
| [investigation](investigation/) | Agents that investigate and triage security events |
| [reporting](reporting/) | Scheduled agents that produce summary reports |
| [triage](triage/) | Agents that evaluate and route new detections |

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

## Data Extraction Patterns

The `data` field in `ai_agent.yaml` maps names to [GJSON](https://github.com/tidwall/gjson) paths evaluated against the event that triggered the D&R rule. Extracted values are appended to the agent's prompt as JSON.

### Passing the full detection object

When an agent triggers on detections (`target: detection`), use `@this` to pass the **entire** detection object — including top-level fields like `detect_id`, `cat`, `source`, `routing`, and `detect_mtd`:

```yaml
data:
  detection: "@this"
```

Do **not** use `detect: detect` — that only extracts the inner `detect` field (event payload + event routing) and omits top-level fields like `detect_id`. This causes problems when the agent needs to pass the detection to cases commands that require `detect_id`.

### Extracting specific fields

For events where only specific fields are needed (e.g., case webhook events):

```yaml
data:
  oid: routing.oid
  case_id: event.case_id
  case_number: event.case_number
```

Paths use GJSON dot notation (not slash-separated).

## Session Serialization (Debounce)

The `debounce_key` field in `ai_agent.yaml` serializes sessions so only one runs at a time per key. When multiple events trigger the same agent concurrently, the first creates a session and subsequent requests are queued. When the active session ends, the most recent queued request is automatically re-fired.

```yaml
data:
  debounce_key: l1-bot
```

This is useful for agents that should process events sequentially rather than in parallel (e.g., a triage bot investigating cases one at a time). The key supports Go template syntax for dynamic values (e.g., `triage-{{.sid}}`).

Unlike D&R suppression which silently drops excess requests, debounce guarantees the latest request will eventually be processed.

## Installation

Use the `lc-deployer` skill from the [lc-essentials](../marketplace/plugins/lc-essentials/) plugin to install and remove agents.

## Running Agents Manually from the CLI

Once an `ai_agent.yaml` is deployed to a Hive, the same definition can be invoked ad-hoc from the LimaCharlie CLI without waiting for a D&R event. The Hive record is treated as a **template** — individual fields (prompt, model, budget, tools, environment, credentials) can be overridden for a single run.

```bash
# Run the deployed agent as-is.
limacharlie ai start-session --definition l1-bot

# Swap the prompt for an ad-hoc question, keep everything else from the template.
limacharlie ai start-session --definition l1-bot \
  --prompt "Investigate sensor srv-01 for persistence mechanisms"

# Cap cost and lower max turns for a cheap exploratory run.
limacharlie ai start-session --definition l1-bot \
  --max-budget-usd 0.50 --max-turns 10

# Provide the data the agent would normally get from a D&R event.
limacharlie ai start-session --definition l1-bot \
  --data '{"hostname": "srv-01", "alert_id": "abc-123"}'
```

Scalars and lists replace the template value. `--env KEY=VALUE` (repeatable) merges with the template's environment, with the override winning on key collisions. Override values may be literal strings or `hive://secret/<name>` references — the same syntax the YAML uses.

To watch what the agent does in real time, attach to the returned session:

```bash
limacharlie ai session attach --id <SESSION_ID>
```

Or start and attach in one step:

```bash
SID=$(limacharlie ai start-session --definition l1-bot \
        --output json | jq -r '.session_id')
limacharlie ai session attach --id "$SID"
```

See the [CLI reference](https://docs.limacharlie.io/9-ai-sessions/cli/) for the full list of override flags and `attach` options.
