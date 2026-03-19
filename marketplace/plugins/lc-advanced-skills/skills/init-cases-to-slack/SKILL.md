---
name: init-cases-to-slack
description: Set up automated Slack notifications for LimaCharlie case events. Creates a Python playbook, D&R rules, API key, and secrets so that case escalations, creations, resolutions, severity upgrades, and closures post rich messages to a Slack channel. Usage - /init-cases-to-slack <org_name>
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
  - Skill
---

# Initialize Cases-to-Slack Integration

Set up automated Slack notifications for LimaCharlie case management events. This skill creates all required components in a single org: a Python playbook, D&R trigger rules, an API key, and secrets for the Slack token and channel.

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

| Component | Hive | Key | Purpose |
|-----------|------|-----|---------|
| Playbook | `playbook` | `cases-to-slack` | Python code that posts rich Slack messages |
| D&R Rule | `dr-general` | `cases-to-slack-on-escalated` | Triggers playbook on case escalation |
| D&R Rule | `dr-general` | `cases-to-slack-on-created` | Triggers playbook on case creation |
| D&R Rule | `dr-general` | `cases-to-slack-on-resolved` | Triggers playbook on case resolution |
| D&R Rule | `dr-general` | `cases-to-slack-on-severity-upgraded` | Triggers playbook on severity upgrade |
| D&R Rule | `dr-general` | `cases-to-slack-on-closed` | Triggers playbook on case closure |
| Secret | `secret` | `slack-api-token` | Slack Bot OAuth token |
| Secret | `secret` | `slack-notification-channel` | Slack channel ID for notifications |
| Secret | `secret` | `cases-to-slack-api-key` | LC API key for playbook SDK auth |
| API Key | — | `cases-to-slack` | Scoped key with `secret.get` permission |

## Procedure

### Step 1: Resolve the Organization

Parse the org name from the skill argument. Resolve it to an OID:

```bash
limacharlie org list --output yaml
```

Find the org matching the name provided by the user and extract its `oid` UUID. If not found, ask the user which org to use.

### Step 2: Verify Prerequisites

Check that the required extensions are subscribed:

```bash
limacharlie extension list --oid <oid> --output yaml
```

Look for `ext-cases` and `ext-playbook` in the output. If either is missing, subscribe:

```bash
limacharlie extension subscribe --name ext-cases --oid <oid>
limacharlie extension subscribe --name ext-playbook --oid <oid>
```

### Step 3: Collect Slack Configuration from User

Ask the user for TWO values:

1. **Slack Bot Token** — starts with `xoxb-`. The bot must have the `chat:write` scope and be invited to the target channel.
2. **Slack Channel ID** — the channel ID (e.g., `C0123456789`), NOT the channel name. The user can find this by right-clicking the channel in Slack → "View channel details" → the ID is at the bottom.

### Step 4: Store Slack Secrets

Store the Slack bot token:

```bash
echo '{"data": {"secret": "<SLACK_BOT_TOKEN>"}, "usr_mtd": {"enabled": true}}' \
  | limacharlie hive set --hive-name secret --key slack-api-token --oid <oid>
```

Store the Slack channel ID:

```bash
echo '{"data": {"secret": "<SLACK_CHANNEL_ID>"}, "usr_mtd": {"enabled": true}}' \
  | limacharlie hive set --hive-name secret --key slack-notification-channel --oid <oid>
```

### Step 5: Create the Playbook API Key

Create an LC API key with minimal permissions for the playbook to read secrets:

```bash
limacharlie api-key create \
  --name "cases-to-slack" \
  --permissions "secret.get,investigation.get" \
  --oid <oid> \
  --output yaml
```

Capture the `api_key` value from the output and immediately store it as a secret:

```bash
echo '{"data": {"secret": "<API_KEY_VALUE>"}, "usr_mtd": {"enabled": true}}' \
  | limacharlie hive set --hive-name secret --key cases-to-slack-api-key --oid <oid>
```

### Step 6: Create the Playbook

Write the playbook Python code to a temp file, then push it as a hive record.

The playbook code:

```bash
cat > /tmp/cases-to-slack.py << 'PYEOF'
import json
import urllib.request
from limacharlie.sdk.hive import Hive


def playbook(sdk, data):
    slack_token = Hive(sdk, "secret").get("slack-api-token").data["secret"]
    slack_channel = Hive(sdk, "secret").get("slack-notification-channel").data["secret"]

    action = data.get("action", "unknown")
    case_number = data.get("case_number", "?")
    case_id = data.get("case_id", "")
    by = data.get("by", "system")

    configs = {
        "escalated": {
            "emoji": ":rotating_light:",
            "color": "#FF0000",
            "label": "Case Escalated",
        },
        "created": {
            "emoji": ":new:",
            "color": "#36A64F",
            "label": "New Case Created",
        },
        "resolved": {
            "emoji": ":white_check_mark:",
            "color": "#2EB67D",
            "label": "Case Resolved",
        },
        "severity_upgraded": {
            "emoji": ":warning:",
            "color": "#ECB22E",
            "label": "Severity Upgraded",
        },
        "closed": {
            "emoji": ":lock:",
            "color": "#808080",
            "label": "Case Closed",
        },
    }
    cfg = configs.get(
        action,
        {
            "emoji": ":clipboard:",
            "color": "#808080",
            "label": action.replace("_", " ").title(),
        },
    )

    fields = [
        {"type": "mrkdwn", "text": f"*Case:* #{case_number}"},
        {"type": "mrkdwn", "text": f"*By:* {by}"},
    ]

    from_val = data.get("from_status")
    to_val = data.get("to_status")
    if from_val and to_val:
        fields.append(
            {"type": "mrkdwn", "text": f"*Change:* {from_val} \u2192 {to_val}"}
        )

    group = data.get("group")
    if group:
        fields.append({"type": "mrkdwn", "text": f"*Group:* {group}"})

    attachment = {
        "color": cfg["color"],
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{cfg['emoji']} *{cfg['label']}*: Case *#{case_number}*",
                },
            },
            {"type": "section", "fields": fields},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Case ID: `{case_id[:8]}...`"}
                ],
            },
        ],
    }

    payload = {
        "channel": slack_channel,
        "attachments": [attachment],
        "text": f"{cfg['label']}: Case #{case_number}",
    }

    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {slack_token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if not result.get("ok"):
                return {"error": f"Slack API error: {result.get('error', 'unknown')}"}
    except Exception as e:
        return {"error": str(e)}

    return {"data": {"posted": True, "case_number": case_number, "action": action}}
PYEOF
```

Push the playbook to the hive:

```bash
python3 -c "
import json, sys
with open('/tmp/cases-to-slack.py') as f:
    code = f.read()
record = {'data': {'python': code}, 'usr_mtd': {'enabled': True, 'tags': ['cases-to-slack']}}
json.dump(record, sys.stdout)
" | limacharlie hive set --hive-name playbook --key cases-to-slack --oid <oid>
```

### Step 7: Create the D&R Rules

Create one D&R rule per case event type. Each rule triggers the same playbook but passes
the appropriate action literal and event fields.

For each of these 5 event types, create a D&R rule:

| Event Type | D&R Key | Description |
|------------|---------|-------------|
| `escalated` | `cases-to-slack-on-escalated` | Case escalated — highest priority alert |
| `created` | `cases-to-slack-on-created` | New case created |
| `resolved` | `cases-to-slack-on-resolved` | Case resolved |
| `severity_upgraded` | `cases-to-slack-on-severity-upgraded` | Severity increased |
| `closed` | `cases-to-slack-on-closed` | Case closed |

For each event type, create the rule using this template (substitute `<EVENT_TYPE>` and
`<DR_KEY>` from the table above):

```bash
python3 -c "
import json, sys
event_type = sys.argv[1]
dr_key = sys.argv[2]
rule = {
    'data': {
        'detect': {
            'event': event_type,
            'op': 'exists',
            'path': 'event/case_id'
        },
        'respond': [{
            'action': 'extension request',
            'extension name': 'ext-playbook',
            'extension action': 'run_playbook',
            'extension request': {
                'name': '{{ \"cases-to-slack\" }}',
                'credentials': '{{ \"hive://secret/cases-to-slack-api-key\" }}',
                'data': {
                    'action': '{{ \"' + event_type + '\" }}',
                    'case_id': 'event.case_id',
                    'case_number': 'event.case_number',
                    'by': 'event.by',
                    'from_status': 'event.metadata.from',
                    'to_status': 'event.metadata.to',
                    'group': 'event.metadata.group'
                }
            },
            'suppression': {
                'is_global': True,
                'keys': ['cases-to-slack-' + event_type + '-{{ .event.case_id }}'],
                'max_count': 1,
                'period': '5m'
            }
        }]
    },
    'usr_mtd': {'enabled': True, 'tags': ['cases-to-slack']}
}
json.dump(rule, sys.stdout)
" "<EVENT_TYPE>" "<DR_KEY>" \
  | limacharlie hive set --hive-name dr-general --key <DR_KEY> --oid <oid>
```

Run this command 5 times, once for each event type/key pair from the table.

### Step 8: Verify Installation

```bash
# Verify playbook exists
limacharlie hive get --hive-name playbook --key cases-to-slack --oid <oid> --output yaml | head -5

# Verify D&R rules exist
limacharlie hive list --hive-name dr-general --oid <oid> --output yaml | grep cases-to-slack

# Verify secrets exist
limacharlie secret list --oid <oid> --output yaml | grep -E "slack-api-token|slack-notification-channel|cases-to-slack-api-key"

# Check for org errors
limacharlie org errors --oid <oid> --output yaml
```

### Step 9: Report to User

Summarize what was created:
- Playbook: `cases-to-slack` in the `playbook` hive
- 5 D&R rules triggering the playbook for: escalated, created, resolved, severity_upgraded, closed
- 3 secrets: `slack-api-token`, `slack-notification-channel`, `cases-to-slack-api-key`
- 1 API key: `cases-to-slack` with `secret.get,investigation.get` permissions

Remind the user:
- The Slack bot must be **invited to the channel** for messages to post.
- D&R rules are tagged `cases-to-slack` — they can disable individual rules to reduce noise.
- The `cases-to-slack-on-created` rule fires for ALL new cases. If this is too noisy, suggest disabling it or adding a severity filter.

## Removal

To remove all components:

```bash
# Remove D&R rules
for key in cases-to-slack-on-escalated cases-to-slack-on-created cases-to-slack-on-resolved cases-to-slack-on-severity-upgraded cases-to-slack-on-closed; do
  limacharlie hive delete --hive-name dr-general --key $key --confirm --oid <oid>
done

# Remove playbook
limacharlie hive delete --hive-name playbook --key cases-to-slack --confirm --oid <oid>

# Remove secrets (optional — user may want to keep Slack token for other uses)
limacharlie secret delete --key cases-to-slack-api-key --confirm --oid <oid>
limacharlie secret delete --key slack-api-token --confirm --oid <oid>
limacharlie secret delete --key slack-notification-channel --confirm --oid <oid>

# Remove API key
limacharlie api-key list --oid <oid> --output yaml  # find the hash for cases-to-slack
limacharlie api-key delete --key-hash <hash> --confirm --oid <oid>
```
