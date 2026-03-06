# L1 Bot - Automated Ticket Triage

An AI-powered Level 1 SOC analyst that automatically investigates new security tickets and documents findings for human L2 analysts to review.

## How It Works

```
Detection fires
      |
      v
ext-ticketing creates a ticket
      |
      v
Webhook adapter emits "created" event
      |
      v
D&R rule matches (event=created, has ticket data)
      |
      v
Suppression check (max 10/min)
      |
      v
AI agent session starts with ticket context
      |
      v
Bot investigates: fetches ticket -> analyzes detection
  -> checks sensor timeline -> assesses scope
      |
      v
Bot documents findings and classifies ticket
(false_positive / true_positive / needs L2 review)
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
| `sensor.list` | List sensors in the organization |
| `sensor.get` | Get detailed sensor information |
| `sensor.task` | Task sensors for timeline, process trees, network data |
| `dr.list` | List D&R rules to understand detection context |
| `insight.det.get` | List and read detections |
| `insight.evt.get` | Access event data for IOC searches and timeline queries |
| `investigation.get` | List and read tickets |
| `investigation.set` | Update tickets, add notes, entities, telemetry, classify |
| `ext.request` | Make requests to extensions (e.g. ext-ticketing) |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-agent-management` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Investigation Workflow

When a new ticket is created, the bot:

1. **Acknowledges** the ticket (sets status to `acknowledged`)
2. **Fetches ticket details** to understand the detection
3. **Analyzes the detection** - gets the full detection record, identifies sensor/event/indicators
4. **Investigates context** - checks sensor timeline, process trees, network connections, related detections
5. **Assesses scope** - searches for the same IOCs across the organization
6. **Documents findings** - adds structured analysis notes and entities to the ticket
7. **Classifies** the ticket:
   - `false_positive` + `resolved` if clearly benign
   - `true_positive` + `escalated` if clearly malicious
   - `in_progress` with notes if unclear (for L2 review)

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Claude model used for investigation |
| `max_turns` | `30` | Maximum CLI tool calls per investigation |
| `max_budget_usd` | `2.0` | Cost cap per investigation session |
| `ttl_seconds` | `600` | Hard timeout (10 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| Suppression | `10/min` | Maximum AI agent invocations per minute (global) |

## Files

- `hives/ai_agent.yaml` - AI agent definition with investigation prompt
- `hives/dr-general.yaml` - D&R rule triggering the bot on ticket creation
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
