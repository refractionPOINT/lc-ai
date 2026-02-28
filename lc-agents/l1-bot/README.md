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
D&R rule matches (event=created, has ticket_id)
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
- [ext-ai-agent-engine](https://doc.limacharlie.io/docs/extensions/ext-ai-agent-engine) extension subscribed
- An Anthropic API key
- A LimaCharlie API key with appropriate permissions

## Setup

1. **Edit secrets** - Replace the placeholder values in `hives/secret.yaml`:
   - `REPLACE_WITH_YOUR_ANTHROPIC_API_KEY` with your Anthropic API key
   - `REPLACE_WITH_YOUR_LIMACHARLIE_API_KEY` with your LimaCharlie API key

2. **Apply the IaC files** using the LimaCharlie CLI:
   ```bash
   limacharlie sync push --oid <your-oid> --dir ./hives
   ```

3. **Verify deployment**:
   ```bash
   # Check the AI agent definition
   limacharlie hive get ai_agent l1-bot --oid <your-oid>

   # Check the D&R rule
   limacharlie dr get l1-bot-ticket-triage --oid <your-oid>
   ```

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
| `model` | `claude-sonnet-4-20250514` | Claude model used for investigation |
| `max_turns` | `30` | Maximum CLI tool calls per investigation |
| `max_budget_usd` | `2.0` | Cost cap per investigation session |
| `ttl_seconds` | `600` | Hard timeout (10 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| Suppression | `10/min` | Maximum AI agent invocations per minute (global) |

## Files

- `hives/ai_agent.yaml` - AI agent definition with investigation prompt
- `hives/dr-general.yaml` - D&R rule triggering the bot on ticket creation
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
