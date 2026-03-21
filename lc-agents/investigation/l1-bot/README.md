# L1 Bot - Automated Case Triage

An AI-powered Level 1 SOC analyst that automatically investigates new security cases and documents findings for human L2 analysts to review.

## How It Works

```
Detection fires
      |
      v
ext-cases creates a case
      |
      v
Webhook adapter emits "case_created" event
      |
      v
D&R rule matches (event=case_created, has case data)
      |
      v
Suppression check (max 10/min)
      |
      v
Debounce check (one active session at a time)
      |
      v
AI agent session starts with case context
      |
      v
Bot investigates: fetches case -> analyzes detection
  -> checks sensor timeline -> assesses scope
      |
      v
Bot documents findings (summary, conclusion, entities, notes)
      |
      v
False positive? --> closed (false_positive)
Everything else --> escalated (for human follow-up)
      |
      v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors in the organization |
| `sensor.get` | Get detailed sensor information |
| `sensor.task` | Task sensors for timeline, process trees, network data |
| `dr.list` | List D&R rules to understand detection context |
| `insight.det.get` | List and read detections |
| `insight.evt.get` | Access event data for IOC searches and timeline queries |
| `investigation.get` | List and read cases |
| `investigation.set` | Update cases, add notes, entities, telemetry, classify |
| `ext.request` | Make requests to extensions (e.g. ext-cases) |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Investigation Workflow

When a new case is created, the bot:

1. **Tags the case** with `investigating` and sets status to `in_progress`
2. **Fetches case details** to understand the detection
3. **Analyzes the detection** - gets the full detection record, identifies sensor/event/indicators
4. **Investigates context** - checks sensor timeline, process trees, network connections, related detections
5. **Assesses scope** - searches for the same IOCs across the organization
6. **Documents findings** - fills out every case section:
   - **Summary**: concise overview of what was detected and found
   - **Conclusion**: determination and reasoning for the outcome
   - **Analysis notes**: detailed technical findings
   - **Entities**: all relevant IOCs with verdicts and context
   - **Telemetry**: linked relevant events
7. **Closes out** with one of two end states:
   - `false_positive` + `closed` if clearly benign
   - `escalated` for everything else (true positive, suspicious, unclear, needs remediation)
8. **Removes** the `investigating` tag

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Claude model used for investigation |
| `max_turns` | `30` | Maximum CLI tool calls per investigation |
| `max_budget_usd` | `2.0` | Cost cap per investigation session |
| `ttl_seconds` | `600` | Hard timeout (10 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| `debounce_key` | `l1-bot` | Serializes sessions: only one investigation runs at a time, pending requests re-fire on completion |
| Suppression | `10/min` | Maximum AI agent invocations per minute (global) |

## Files

- `hives/ai_agent.yaml` - AI agent definition with investigation prompt
- `hives/dr-general.yaml` - D&R rule triggering the bot on case creation
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
