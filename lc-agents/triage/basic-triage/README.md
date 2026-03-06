# Basic Triage - Automated Detection Routing

An AI-powered triage bot that evaluates every new detection, dismisses obvious false positives, and routes legitimate detections to the appropriate ticket (new or existing).

## How It Works

```
Detection fires (D&R rule reports)
      |
      v
_detect event emitted
      |
      v
D&R rule matches (target=detection)
      |
      v
Suppression check (max 20/min)
      |
      v
AI agent session starts with detection context
      |
      v
Step 1: FP check - obvious false positive?
      |           |
     YES          NO
      |           |
      v           v
   STOP     Step 2: Gather context
              - Recent detections from same sensor (last hour)
              - Existing tickets for this sensor
              |
              v
            Step 3: Route to ticket
              - Add to existing ticket (re-open if resolved)
              - OR create a new ticket
      |
      v
Session terminates (one_shot)
```

## Prerequisites

- [ext-ticketing](https://doc.limacharlie.io/docs/extensions/ext-ticketing) extension subscribed and configured
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `insight.det.get` | List and read detections from the sensor |
| `investigation.get` | List and read tickets |
| `investigation.set` | Create tickets, update status, add notes, link detections |
| `ext.request` | Invoke the ext-ticketing extension to create/update tickets |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-agent-management` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `sonnet` | Claude model used for triage (fast and cost-effective) |
| `max_turns` | `30` | Maximum CLI tool calls per triage session |
| `max_budget_usd` | `0.50` | Cost cap per triage session |
| `ttl_seconds` | `300` | Hard timeout (5 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| Suppression | `20/min` | Maximum AI agent invocations per minute (global) |

## Data Extraction

The agent uses `detection: "@this"` to receive the **full detection object** (including `detect_id`, `cat`, `routing`, etc.) rather than just the inner `detect` field. This is required because ticketing commands need the top-level `detect_id` to properly link detections. See [Agent Data Extraction Patterns](../../README.md#data-extraction-patterns).

## Files

- `hives/ai_agent.yaml` - AI agent definition with triage prompt
- `hives/dr-general.yaml` - D&R rule triggering the bot on every detection
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
