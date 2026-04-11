---
name: feedback
description: Send interactive feedback requests to humans via ext-feedback channels. Request approvals (approve/deny), acknowledgements, or free-form text answers through Slack, Telegram, Teams, Email, or built-in Web UI. Responses go to a case (note), playbook (trigger), or ai_agent (starts AI session). Use for human-in-the-loop approval, operator notifications, collecting analyst input, gating containment actions, or asking questions during investigations.
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Feedback — Human-in-the-Loop Requests

Send interactive feedback requests to humans through configured channels and dispatch responses to cases, playbooks, or AI agents.

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

## When to Use

Use this skill when you need to:
- **Ask for approval** before taking a high-impact action (isolate host, block IOC)
- **Notify and acknowledge** — send an alert and wait for someone to confirm they saw it
- **Collect input** — ask an analyst a free-form question during an investigation
- **Gate automated workflows** — pause a playbook or AI agent until a human responds

## Prerequisites

The organization must have:
1. **ext-feedback subscribed** — check with `limacharlie extension list --oid <oid> --output yaml | grep ext-feedback`
2. **At least one channel configured** — check with `limacharlie feedback channel list --oid <oid> --output yaml`

If either is missing, tell the user and suggest running `/init-feedback` to set things up.

---

## Request Types

### 1. Approval (Approve / Deny)

Presents two buttons. Best for gating actions.

```bash
limacharlie feedback request-approval \
  --channel <channel_name> \
  --question "Isolate sensor web-prod-03 (sid abc123)?" \
  --destination case --case-id <case_number> \
  --oid <oid> --output yaml
```

Optional flags:
- `--approved-content '{"action":"isolate","sid":"abc123"}'` — JSON payload sent when approved
- `--denied-content '{"action":"skip"}'` — JSON payload sent when denied
- `--timeout 300 --timeout-choice denied` — auto-deny after 5 minutes

### 2. Acknowledgement

Single Acknowledge button. Best for notifications.

```bash
limacharlie feedback request-ack \
  --channel <channel_name> \
  --question "Alert: lateral movement detected on host-01" \
  --destination case --case-id <case_number> \
  --oid <oid> --output yaml
```

Optional flags:
- `--acknowledged-content '{"status":"seen"}'` — JSON payload on ack
- `--timeout 600` — auto-ack after 10 minutes
- `--timeout-content '{"status":"auto-acked"}'` — override payload for timeout

### 3. Question (Free-Form Text)

Text input field. Best for collecting analyst input.

```bash
limacharlie feedback request-question \
  --channel <channel_name> \
  --question "What is the root cause of incident #42?" \
  --destination case --case-id <case_number> \
  --oid <oid> --output yaml
```

Optional flags:
- `--timeout 300` — auto-answer after timeout (requires `--timeout-content`)
- `--timeout-content '{"answer":"no response"}'` — automatic answer on timeout

---

## Destinations

The `--destination` flag controls where the response goes:

| Destination | Flag | Required With | What Happens |
|-------------|------|---------------|--------------|
| `case` | `--case-id <number>` | case number | Response added as a case note |
| `playbook` | `--playbook <name>` | playbook name | Playbook triggered with response data |

> **ai_agent destination**: ext-feedback also supports `ai_agent` as a destination (starts an AI session with the response data). This destination is available through D&R rule extension requests but not yet in the CLI. To use it, generate a D&R response with `limacharlie ai generate-response` that sends an extension request to ext-feedback with `feedback_destination: ai_agent` and `ai_agent_name: <name>`.

---

## Workflow

### Step 1: Verify Prerequisites

```bash
limacharlie extension list --oid <oid> --output yaml | grep ext-feedback
limacharlie feedback channel list --oid <oid> --output yaml
```

If ext-feedback is not subscribed or no channels exist, stop and suggest `/init-feedback`.

### Step 2: Choose the Right Request Type

| Scenario | Request Type |
|----------|-------------|
| Gate a destructive action | `request-approval` with timeout + auto-deny |
| Alert an operator | `request-ack` |
| Collect analyst input | `request-question` |

### Step 3: Send the Request

Pick the appropriate command from the Request Types section above. Always include:
- `--channel` — the configured channel name
- `--question` — clear, actionable prompt text
- `--destination` and its required companion flag
- `--oid`

### Step 4: Handle the Response

- **`case` destination**: The response appears as a case note. Query it with `limacharlie case get --case-number <N> --oid <oid> --output yaml`.
- **`playbook` destination**: The playbook runs automatically with the response payload.
- **Web channel**: The CLI response includes a `url` field — share it with the user so they can respond via the web UI.

---

## Timeout Behavior

Timeouts prevent indefinite hangs in automated workflows:

| Request Type | Timeout Flags |
|-------------|---------------|
| Approval | `--timeout <seconds> --timeout-choice approved\|denied` |
| Acknowledgement | `--timeout <seconds>` (auto-acks; optional `--timeout-content`) |
| Question | `--timeout <seconds> --timeout-content '<json>'` (content required) |

Minimum timeout is **60 seconds**. Feedback requests expire after **7 days** regardless.

---

## Channel Management

List, add, or remove channels:

```bash
# List channels
limacharlie feedback channel list --oid <oid> --output yaml

# Add a web channel (no credentials needed)
limacharlie feedback channel add --name web --type web --oid <oid> --output yaml

# Add a Slack channel (requires a Tailored Output with slack_api_token + slack_channel)
limacharlie feedback channel add --name ops-slack --type slack --output-name my-slack-output --oid <oid> --output yaml

# Remove a channel
limacharlie feedback channel remove --name old-channel --oid <oid> --output yaml
```

Channel types: `web`, `slack`, `telegram`, `ms_teams`, `email`. All non-web types require a Tailored Output holding credentials. Use `/init-feedback` for guided channel setup.

---

## Examples

### Gate Host Isolation on Approval

```bash
limacharlie feedback request-approval \
  --channel ops-slack \
  --question "Case #17: Isolate sensor db-prod-01 (sid 8a3f...)?" \
  --destination case --case-id 17 \
  --approved-content '{"action":"isolate","sid":"8a3f..."}' \
  --denied-content '{"action":"skip"}' \
  --timeout 300 --timeout-choice denied \
  --oid <oid> --output yaml
```

### Notify SOC of Critical Alert

```bash
limacharlie feedback request-ack \
  --channel ops-slack \
  --question "CRITICAL: Ransomware indicators detected on FILESERVER-01. Case #42 opened." \
  --destination case --case-id 42 \
  --timeout 600 \
  --oid <oid> --output yaml
```

### Ask Analyst for Root Cause

```bash
limacharlie feedback request-question \
  --channel web \
  --question "What is the likely initial access vector for case #42?" \
  --destination case --case-id 42 \
  --oid <oid> --output yaml
```

---

## Related Skills

- `/init-feedback` — Set up ext-feedback: subscribe, configure channels, create sample D&R rules
- `/detection-engineering` — Create D&R rules with feedback approval gates
- `/investigation-creation` — Investigate cases (feedback responses land as case notes)
