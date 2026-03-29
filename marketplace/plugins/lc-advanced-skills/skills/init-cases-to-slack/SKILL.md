---
name: init-cases-to-slack
description: Set up automated Slack notifications for LimaCharlie case events. Creates a Python playbook, D&R rules, API key, and secrets so that case creations, resolutions, severity upgrades, and closures post rich messages to a Slack channel. Usage - /init-cases-to-slack <org_name>
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
from limacharlie import Hive


_CASES_API = "https://cases.limacharlie.io"


def _fetch_case_summary(sdk, case_number):
    """Fetch the case summary from ext-cases REST API."""
    try:
        oid = sdk._oid
        jwt = sdk._jwt
        url = f"{_CASES_API}/api/v1/cases/{case_number}?oid={oid}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {jwt}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("case", {}).get("summary") or None
    except Exception:
        return None


def playbook(sdk, data):
    slack_token = Hive(sdk, "secret").get("slack-api-token").data["secret"]
    slack_channel = Hive(sdk, "secret").get("slack-notification-channel").data["secret"]

    action = data.get("action", "unknown")
    case_number = data.get("case_number", "?")
    case_id = data.get("case_id", "")
    by = data.get("by", "system")

    configs = {
        "case_created": {
            "emoji": ":new:",
            "color": "#36A64F",
            "label": "New Case Created",
        },
        "case_resolved": {
            "emoji": ":white_check_mark:",
            "color": "#2EB67D",
            "label": "Case Resolved",
        },
        "case_severity_upgraded": {
            "emoji": ":warning:",
            "color": "#ECB22E",
            "label": "Severity Upgraded",
        },
        "case_closed": {
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

    # Event-specific fields.
    if action == "case_created":
        severity = data.get("severity")
        if severity:
            fields.append({"type": "mrkdwn", "text": f"*Severity:* {severity}"})
        detection_cat = data.get("detection_cat")
        if detection_cat:
            fields.append({"type": "mrkdwn", "text": f"*Detection:* {detection_cat}"})

    elif action == "case_severity_upgraded":
        from_val = data.get("from_severity")
        to_val = data.get("to_severity")
        if from_val and to_val:
            fields.append(
                {"type": "mrkdwn", "text": f"*Severity:* {from_val} \u2192 {to_val}"}
            )
        reason = data.get("reason")
        if reason:
            fields.append({"type": "mrkdwn", "text": f"*Reason:* {reason}"})

    elif action in ("case_resolved", "case_closed"):
        from_val = data.get("from_status")
        to_val = data.get("to_status")
        if from_val and to_val:
            fields.append(
                {"type": "mrkdwn", "text": f"*Status:* {from_val} \u2192 {to_val}"}
            )

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{cfg['emoji']} *{cfg['label']}*: Case *#{case_number}*",
            },
        },
        {"type": "section", "fields": fields},
    ]

    # Fetch case summary from ext-cases API.
    summary = _fetch_case_summary(sdk, case_number)
    if summary:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Summary:* {summary}"},
            }
        )

    # Context footer.
    case_id_short = case_id[:8] if case_id else "?"
    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Case ID: `{case_id_short}...`"}
            ],
        }
    )

    attachment = {"color": cfg["color"], "blocks": blocks}

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
event-type-specific metadata fields using Go template syntax (`{{ .event.FIELD }}`).

**IMPORTANT**: Values in the `extension request` `data` block must use `{{ .event.FIELD }}`
template syntax to reference event fields. Bare strings like `event.case_id` are passed
as literals, NOT resolved from the event.

#### ext-cases Audit Event Structure

Events from ext-cases have these top-level fields: `action`, `case_id`, `case_number`,
`event_id`, `oid`, `by`, `ts`, and `metadata` (event-type-specific).

Metadata by event type:
- **case_created**: always: `severity`, `detection_cat`, `detection_priority`; optional: `detect_id`, `detection_source`, `sid`, `hostname`, `summary`
- **case_resolved / case_closed**: `from` (old status), `to` (new status); `case_closed` also includes `summary` when set
- **case_severity_upgraded**: `from` (old severity), `to` (new severity), `reason`

**IMPORTANT**: Only template metadata fields that are **always present**. Optional fields
(like `summary`, `hostname`) cause Go template errors when absent, which silently prevents
the extension request from being sent. The playbook fetches optional data (like summary)
directly from the ext-cases REST API instead.

#### case_created

```bash
python3 -c "
import json, sys
rule = {
    'data': {
        'detect': {
            'event': 'case_created',
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
                    'action': '{{ \"case_created\" }}',
                    'case_id': '{{ .event.case_id }}',
                    'case_number': '{{ .event.case_number }}',
                    'by': '{{ .event.by }}',
                    'severity': '{{ .event.metadata.severity }}',
                    'detection_cat': '{{ .event.metadata.detection_cat }}'
                }
            },
            'suppression': {
                'is_global': True,
                'keys': ['cases-to-slack-created-{{ .event.case_id }}'],
                'max_count': 1,
                'period': '5m'
            }
        }]
    },
    'usr_mtd': {'enabled': True, 'tags': ['cases-to-slack']}
}
json.dump(rule, sys.stdout)
" | limacharlie hive set --hive-name dr-general --key cases-to-slack-on-created --oid <oid>
```

#### case_resolved

```bash
python3 -c "
import json, sys
rule = {
    'data': {
        'detect': {
            'event': 'case_resolved',
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
                    'action': '{{ \"case_resolved\" }}',
                    'case_id': '{{ .event.case_id }}',
                    'case_number': '{{ .event.case_number }}',
                    'by': '{{ .event.by }}',
                    'from_status': '{{ .event.metadata.from }}',
                    'to_status': '{{ .event.metadata.to }}'
                }
            },
            'suppression': {
                'is_global': True,
                'keys': ['cases-to-slack-resolved-{{ .event.case_id }}'],
                'max_count': 1,
                'period': '5m'
            }
        }]
    },
    'usr_mtd': {'enabled': True, 'tags': ['cases-to-slack']}
}
json.dump(rule, sys.stdout)
" | limacharlie hive set --hive-name dr-general --key cases-to-slack-on-resolved --oid <oid>
```

#### case_severity_upgraded

```bash
python3 -c "
import json, sys
rule = {
    'data': {
        'detect': {
            'event': 'case_severity_upgraded',
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
                    'action': '{{ \"case_severity_upgraded\" }}',
                    'case_id': '{{ .event.case_id }}',
                    'case_number': '{{ .event.case_number }}',
                    'by': '{{ .event.by }}',
                    'from_severity': '{{ .event.metadata.from }}',
                    'to_severity': '{{ .event.metadata.to }}',
                    'reason': '{{ .event.metadata.reason }}'
                }
            },
            'suppression': {
                'is_global': True,
                'keys': ['cases-to-slack-severity_upgraded-{{ .event.case_id }}'],
                'max_count': 1,
                'period': '5m'
            }
        }]
    },
    'usr_mtd': {'enabled': True, 'tags': ['cases-to-slack']}
}
json.dump(rule, sys.stdout)
" | limacharlie hive set --hive-name dr-general --key cases-to-slack-on-severity-upgraded --oid <oid>
```

#### case_closed

```bash
python3 -c "
import json, sys
rule = {
    'data': {
        'detect': {
            'event': 'case_closed',
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
                    'action': '{{ \"case_closed\" }}',
                    'case_id': '{{ .event.case_id }}',
                    'case_number': '{{ .event.case_number }}',
                    'by': '{{ .event.by }}',
                    'from_status': '{{ .event.metadata.from }}',
                    'to_status': '{{ .event.metadata.to }}'
                }
            },
            'suppression': {
                'is_global': True,
                'keys': ['cases-to-slack-closed-{{ .event.case_id }}'],
                'max_count': 1,
                'period': '5m'
            }
        }]
    },
    'usr_mtd': {'enabled': True, 'tags': ['cases-to-slack']}
}
json.dump(rule, sys.stdout)
" | limacharlie hive set --hive-name dr-general --key cases-to-slack-on-closed --oid <oid>
```

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
- 4 D&R rules triggering the playbook for: case_created, case_resolved, case_severity_upgraded, case_closed
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
for key in cases-to-slack-on-created cases-to-slack-on-resolved cases-to-slack-on-severity-upgraded cases-to-slack-on-closed; do
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
