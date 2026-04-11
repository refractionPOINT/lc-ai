---
name: init-feedback
description: Set up interactive feedback channels for LimaCharlie ext-feedback. Subscribes to the extension, configures channels (Web, Slack, Telegram, Microsoft Teams, Email), creates required Tailored Outputs and secrets, and optionally creates a sample D&R rule that requests human approval before containment. Usage - /init-feedback <org_name>
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - Skill
---

# Initialize Feedback Channels

Set up interactive feedback channels for human-in-the-loop workflows in LimaCharlie. This skill subscribes to the ext-feedback extension, configures one or more channels, and optionally creates a sample D&R rule demonstrating approval-gated containment.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output yaml [flags]
```

For command help and discovery: `limacharlie <command> --ai-help`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **Output Format** | `--output json` | `--output yaml` (more token-efficient) |
| **Filter Output** | Pipe to jq/yq | Use `--filter JMESPATH` to select fields |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## What Gets Created

| Component | Type | Purpose |
|-----------|------|---------|
| ext-feedback subscription | Extension | Enables feedback requests for the org |
| Channel(s) | Extension config | One or more feedback channels (web, slack, telegram, ms_teams, email) |
| Tailored Output(s) | Output | Credentials for non-web channels (Slack token, Telegram bot, etc.) |
| Sample D&R rule (optional) | dr-general | Demonstrates approval-gated containment |

## Channel Types

| Type | Requirements | In-Chat Buttons |
|------|-------------|:---------------:|
| `web` | None (built-in UI, returns a shareable URL) | N/A |
| `slack` | Slack App with Interactivity enabled, Bot User OAuth Token, channel ID | Yes |
| `telegram` | Telegram bot (via @BotFather), bot token, chat ID | Yes |
| `ms_teams` | Power Automate Workflow webhook URL | No (links to web UI) |
| `email` | SMTP server, credentials, recipient address | No (links to web UI) |

## Procedure

### Step 1: Resolve the Organization

Parse the org name from the skill argument. Resolve it to an OID:

```bash
limacharlie org list --output yaml
```

Find the org matching the name provided by the user and extract its `oid` UUID. If not found, ask the user which org to use.

### Step 2: Subscribe to ext-feedback

Check if ext-feedback is already subscribed:

```bash
limacharlie extension list --oid <oid> --output yaml
```

Look for `ext-feedback` in the output. If missing, subscribe:

```bash
limacharlie extension subscribe --name ext-feedback --oid <oid>
```

On subscription, the extension automatically creates a webhook adapter and a D&R rule for routing feedback responses. No manual setup is needed for these.

### Step 3: Check Existing Channels

List any channels already configured:

```bash
limacharlie feedback channel list --oid <oid> --output yaml
```

Show the user what already exists (if anything) before adding new channels.

### Step 4: Ask Which Channels to Configure

Ask the user which channel types they want to set up. Present the options:

1. **Web** (simplest — built-in UI, no credentials needed, returns shareable URLs)
2. **Slack** (interactive buttons in Slack)
3. **Telegram** (interactive buttons in Telegram)
4. **Microsoft Teams** (Adaptive Card with link to web UI)
5. **Email** (HTML email with link to web UI)

The user can choose one or more. Always recommend starting with **web** since it requires no external setup.

### Step 5: Configure Each Channel

For each selected channel type, follow the appropriate setup below.

#### Web Channel

No credentials needed. Just add the channel:

```bash
limacharlie feedback channel add --name web --type web --oid <oid> --output yaml
```

#### Slack Channel

Ask the user for:

1. **Slack Bot User OAuth Token** — starts with `xoxb-`. The bot must:
   - Have a Slack App with **Interactivity & Shortcuts** enabled
   - The Request URL must be set to: `https://feedback-system.limacharlie.io/callback/slack`
   - Have the `chat:write` scope
   - Be invited to the target channel
2. **Slack Channel** — the channel name or ID (e.g., `#security-ops` or `C0123456789`)
3. **Channel name** — a short name for this channel in LimaCharlie (e.g., `slack-ops`)
4. **Output name** — name for the Tailored Output (e.g., `feedback-slack`). If the user already has a suitable Slack Tailored Output, they can reuse it.

Create a YAML config file and create the Tailored Output:

```bash
cat > /tmp/feedback-slack-output.yaml << 'EOF'
slack_api_token: "<SLACK_BOT_TOKEN>"
slack_channel: "<SLACK_CHANNEL>"
EOF
limacharlie output create \
  --name <output_name> \
  --module slack \
  --type tailored \
  --input-file /tmp/feedback-slack-output.yaml \
  --oid <oid> --output yaml
```

Add the channel:

```bash
limacharlie feedback channel add --name <channel_name> --type slack --output-name <output_name> --oid <oid> --output yaml
```

#### Telegram Channel

Ask the user for:

1. **Telegram Bot Token** — from @BotFather (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`). The bot must be added to the target group/channel.
2. **Chat ID** — the group or channel ID (typically a negative number like `-1001234567890`). The user can find this by sending a message to the group after adding the bot, then checking `https://api.telegram.org/bot<TOKEN>/getUpdates` for the `chat.id` field.
3. **Channel name** — a short name (e.g., `telegram-ops`)
4. **Output name** — name for the Tailored Output (e.g., `feedback-telegram`)

Create a YAML config file and create the Tailored Output:

```bash
cat > /tmp/feedback-telegram-output.yaml << 'EOF'
bot_token: "<BOT_TOKEN>"
chat_id: "<CHAT_ID>"
EOF
limacharlie output create \
  --name <output_name> \
  --module telegram \
  --type tailored \
  --input-file /tmp/feedback-telegram-output.yaml \
  --oid <oid> --output yaml
```

Add the channel:

```bash
limacharlie feedback channel add --name <channel_name> --type telegram --output-name <output_name> --oid <oid> --output yaml
```

**Note**: The extension automatically registers a Telegram webhook with the bot. If the bot is used for other webhook integrations, this will override the existing webhook. Recommend a dedicated bot for ext-feedback.

#### Microsoft Teams Channel

Ask the user for:

1. **Webhook URL** — from a Power Automate Workflow. To create one:
   - In Teams, navigate to the target channel
   - Click **...** > **Workflows**
   - Select the **Send webhook alerts to a channel** template
   - Name the workflow, authenticate, and copy the webhook URL
2. **Channel name** — a short name (e.g., `teams-ops`)
3. **Output name** — name for the Tailored Output (e.g., `feedback-teams`)

Create a YAML config file and create the Tailored Output:

```bash
cat > /tmp/feedback-teams-output.yaml << 'EOF'
webhook_url: "<WEBHOOK_URL>"
EOF
limacharlie output create \
  --name <output_name> \
  --module ms_teams \
  --type tailored \
  --input-file /tmp/feedback-teams-output.yaml \
  --oid <oid> --output yaml
```

Add the channel:

```bash
limacharlie feedback channel add --name <channel_name> --type ms_teams --output-name <output_name> --oid <oid> --output yaml
```

#### Email Channel

Ask the user for:

1. **SMTP Host** — server address, optionally with port (e.g., `smtp.example.com:587`). Defaults to port 587.
2. **Recipient Email** — where feedback emails are sent (e.g., `soc@example.com`)
3. **From Email** — sender address (e.g., `limacharlie@example.com`)
4. **Username** (optional) — SMTP authentication username
5. **Password** (optional) — SMTP authentication password
6. **Channel name** — a short name (e.g., `email-ops`)
7. **Output name** — name for the Tailored Output (e.g., `feedback-email`)

Create a YAML config file and create the Tailored Output (adjust fields based on whether auth is needed):

```bash
cat > /tmp/feedback-email-output.yaml << 'EOF'
dest_host: "<SMTP_HOST>"
dest_email: "<RECIPIENT_EMAIL>"
from_email: "<FROM_EMAIL>"
user_name: "<USERNAME>"
password: "<PASSWORD>"
EOF
limacharlie output create \
  --name <output_name> \
  --module smtp \
  --type tailored \
  --input-file /tmp/feedback-email-output.yaml \
  --oid <oid> --output yaml
```

Omit `user_name` and `password` from the config file if no SMTP authentication is needed.

Add the channel:

```bash
limacharlie feedback channel add --name <channel_name> --type email --output-name <output_name> --oid <oid> --output yaml
```

### Step 6: Test the Channel

After configuring each channel, send a test feedback request to verify it works:

```bash
limacharlie feedback request-approval \
  --channel <channel_name> \
  --question "Test: Is this feedback channel working?" \
  --destination case --case-id 0 \
  --oid <oid> --output yaml
```

For `web` channels, the response includes a `url` — show the user the URL so they can verify the web UI renders correctly.

For Slack/Telegram channels, ask the user to confirm the message appeared in their channel.

If the test fails, check `limacharlie org errors --oid <oid> --output yaml` for error details.

### Step 7: Offer Sample D&R Rule (Optional)

Ask the user if they want a sample D&R rule that demonstrates human-in-the-loop approval. If yes:

Explain: this rule detects a specific event and sends a feedback request to a channel asking for approval before taking action. The response triggers a playbook. This is a template — the user should customize the detection logic and response actions.

Use the AI generation commands to build the rule. The response component should use `extension request` to `ext-feedback`:

```bash
limacharlie ai generate-response --description "Send a feedback approval request to ext-feedback on channel '<channel_name>' asking whether to isolate the host. Use feedback_destination playbook with playbook_name 'feedback-response-handler'. Include the routing.sid in approved_content. Set timeout_seconds to 300 with timeout_choice denied." --oid <oid> --output yaml
```

Validate the generated rule before deploying:

```bash
limacharlie dr validate --detect /tmp/detect.yaml --respond /tmp/respond.yaml --oid <oid>
```

Deploy with user approval:

```bash
limacharlie dr set --key sample-feedback-approval --input-file /tmp/rule.yaml --oid <oid>
```

**Important**: Remind the user that this sample rule needs a corresponding playbook (`feedback-response-handler`) to act on the approval/denial response. Without the playbook, the response is recorded but no action is taken.

### Step 8: Verify Installation

```bash
# Verify extension is subscribed
limacharlie extension list --oid <oid> --output yaml | grep ext-feedback

# Verify channels exist
limacharlie feedback channel list --oid <oid> --output yaml

# Check for org errors
limacharlie org errors --oid <oid> --output yaml
```

### Step 9: Report to User

Summarize what was created:

- **Extension**: ext-feedback subscribed (webhook adapter and routing D&R rule auto-created)
- **Channels**: List each channel with its name, type, and output name
- **Tailored Outputs**: List each output created
- **Sample D&R rule** (if created): Name and purpose

Remind the user:

- **Web channel** returns a shareable URL for each request — useful for ad-hoc approvals or when no chat platform is available.
- **Slack** requires the bot to be **invited to the channel** and requires **Interactivity & Shortcuts** enabled with the correct Request URL.
- **Telegram** webhook is registered automatically — use a dedicated bot if the bot is shared with other integrations.
- Feedback requests expire after **7 days**.
- Responses are atomic — once processed, duplicates are rejected (safe against retries).
- Use `limacharlie feedback --ai-help` for the full CLI reference.

## Removal

To remove all feedback components:

```bash
# Remove channels
limacharlie feedback channel list --oid <oid> --output yaml
# For each channel:
limacharlie feedback channel remove --name <channel_name> --oid <oid> --output yaml

# Remove Tailored Outputs (optional — user may want to keep for other uses)
limacharlie output delete --name <output_name> --confirm --oid <oid> --output yaml

# Remove sample D&R rule (if created)
limacharlie dr delete --key sample-feedback-approval --oid <oid>

# Unsubscribe extension (removes webhook adapter and routing rule automatically)
limacharlie extension unsubscribe --name ext-feedback --oid <oid>
```
