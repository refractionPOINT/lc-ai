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
- [ext-ai-agent-engine](https://doc.limacharlie.io/docs/extensions/ext-ai-agent-engine) extension subscribed
- An Anthropic API key
- A LimaCharlie API key with appropriate permissions

## Installation

### Option A: Using the lc-essentials Plugin (Recommended)

If you have the [lc-essentials](../../marketplace/plugins/lc-essentials/) Claude Code plugin installed, simply ask:

> "Install the l1-bot agent in my org"

The plugin's `lc-agent-management` skill will handle subscribing to extensions, creating API keys, setting secrets, and pushing all hive configurations for you.

### Option B: Manual Setup

#### 1. Subscribe to Required Extensions

```bash
# Subscribe to the AI agent engine
limacharlie extension subscribe --name ext-ai-agent-engine --oid <your-oid>

# Subscribe to ticketing (if not already)
limacharlie extension subscribe --name ext-ticketing --oid <your-oid>
```

Make sure `ext-ticketing` is also **configured** with your ticketing preferences (see [ext-ticketing docs](https://doc.limacharlie.io/docs/extensions/ext-ticketing)).

#### 2. Create a LimaCharlie API Key

Create a dedicated API key for the bot:

```bash
limacharlie api-key create \
  --name "l1-bot-api-key" \
  --permissions "sensor.list,sensor.get,sensor.task,dr.list,org.get,hive.get" \
  --oid <your-oid> \
  --output yaml
```

**Save the key value** - it is only shown once.

#### 3. Set Secrets

Store both API keys as secrets in LimaCharlie:

```bash
# Store the LimaCharlie API key
limacharlie secret set --key lc-api-key --oid <your-oid> <<< '{"secret": "<your-lc-api-key>"}'

# Store your Anthropic API key
limacharlie secret set --key anthropic-key --oid <your-oid> <<< '{"secret": "<your-anthropic-api-key>"}'
```

#### 4. Push the Hive Configurations

Deploy the AI agent definition and D&R rule (**do not push `secret.yaml`**, secrets were set in step 3):

```bash
limacharlie sync push --oid <your-oid> --dir ./hives --hive-ai-agent --hive-dr-general
```

#### 5. Verify Deployment

```bash
# Check the AI agent definition
limacharlie hive get --hive-name ai_agent --key l1-bot --oid <your-oid> --output yaml

# Check the D&R rule
limacharlie hive list --hive-name dr-general --oid <your-oid> --output yaml

# Check secrets exist
limacharlie secret list --oid <your-oid> --output yaml

# Check for errors
limacharlie org errors --oid <your-oid> --output yaml
```

## Uninstalling

### Option A: Using the lc-essentials Plugin

> "Remove the l1-bot agent from my org"

### Option B: Manual Removal

```bash
# Remove the D&R rule
limacharlie hive delete --hive-name dr-general --key l1-bot-ticket-triage --confirm --oid <your-oid>

# Remove the AI agent definition
limacharlie hive delete --hive-name ai_agent --key l1-bot --confirm --oid <your-oid>

# Optionally remove secrets (only if no other agents use them)
limacharlie secret delete --key anthropic-key --confirm --oid <your-oid>
limacharlie secret delete --key lc-api-key --confirm --oid <your-oid>

# Optionally delete the API key
limacharlie api-key list --oid <your-oid> --output yaml
limacharlie api-key delete --key-hash <hash-of-l1-bot-api-key> --confirm --oid <your-oid>
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
