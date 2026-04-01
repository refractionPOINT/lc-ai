# Basic Triage - Automated Detection Routing

An AI-powered triage bot that evaluates every new detection, dismisses obvious false positives, and routes legitimate detections to the appropriate case (new or existing).

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
              - Existing cases for this sensor
              |
              v
            Step 3: Route to case
              - Add to existing case (re-open if resolved)
              - OR create a new case
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
| `insight.det.get` | List and read detections from the sensor |
| `investigation.get` | List and read cases |
| `investigation.set` | Create cases, update status, add notes, link detections |
| `ext.request` | Invoke the ext-cases extension to create/update cases |
| `org_notes.*` | Read and write org notes |
| `sop.get` | Read SOPs for operational guidance |
| `sop.get.mtd` | Read SOP metadata |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

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

The agent uses `detection: "@this"` to receive the **full detection object** (including `detect_id`, `cat`, `routing`, etc.) rather than just the inner `detect` field. This is required because cases commands need the top-level `detect_id` to properly link detections. See [Agent Data Extraction Patterns](../../README.md#data-extraction-patterns).

## Files

- `hives/ai_agent.yaml` - AI agent definition with triage prompt
- `hives/dr-general.yaml` - D&R rule triggering the bot on every detection
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
