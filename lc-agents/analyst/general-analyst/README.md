# General Analyst - On-Demand AI Security Analyst

A versatile AI analyst invoked by humans via @mentions in LimaCharlie cases. Unlike workflow-driven agents, the general analyst has no fixed procedure -- it reads the human's instructions from the mentioning note and executes accordingly.

## How It Works

```
Human adds case note: "@general-analyst investigate lateral movement from this host"
      |
      v
D&R rule matches case_note_added containing "@general-analyst"
      |
      v
Permission check (note author must have ai_agent.exec)
      |
      v
AI agent session starts with case context
      |
      v
Agent reads the case and mentioning note
      |
      v
Executes the requested task (investigation, analysis, containment, etc.)
      |
      v
Documents findings as case notes
      |
      v
Session terminates (one_shot)
```

## Use Cases

- **Investigation**: "Look at the process tree on this sensor and check for persistence"
- **Analysis**: "Correlate these IOCs across the org and summarize what you find"
- **Containment**: "Isolate sensor X and kill process Y"
- **Enrichment**: "Search for this hash across all sensors in the last 24 hours"
- **Triage**: "Review the detections on this case and assess severity"

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | List and search sensors |
| `sensor.get` | Get sensor details and timeline |
| `sensor.task` | Live response (process listing, isolation, file ops) |
| `dr.list` | Read D&R rules for context |
| `insight.det.get` | List and read detections |
| `insight.evt.get` | Read events and sensor timeline |
| `investigation.get` | Read cases |
| `investigation.set` | Update cases, add notes, entities, telemetry |
| `ext.request` | Invoke extensions |
| `ai_agent.operate` | Allow the agent to run |

The note author must also have `ai_agent.exec` permission for the D&R rule to trigger.

## Installation

Use the `lc-deployer` skill to install and manage this agent.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Claude model (needs broad reasoning for diverse tasks) |
| `max_turns` | `50` | Maximum CLI tool calls per session |
| `max_budget_usd` | `5.00` | Cost cap per session |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| Suppression | `1 per 30min per case` | Prevents duplicate triggers on the same case |

## Files

- `hives/ai_agent.yaml` - AI agent definition with general-purpose prompt
- `hives/dr-general.yaml` - D&R rule triggering on @general-analyst mentions
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
