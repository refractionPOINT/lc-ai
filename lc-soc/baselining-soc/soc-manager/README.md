# SOC Manager - Operational Health Monitor

The self-healing mechanism of the SOC. Runs every hour to catch operational issues: stale investigations where agents timed out, SLA violations where tickets were missed, and abandoned tickets that need human attention.

## What It Does

```
Schedule: every 1 hour
      |
      v
Check for stale lock tags:
  - "l2-investigating" stuck > 30 min?
  - "analyzing" stuck > 30 min?
  - "containing" stuck > 30 min?
  - "hunting" stuck > 30 min?
      |
      +--- Found stale tags --> Remove tag, add note
      |
      v
Check for SLA violations:
  - Critical tickets in "new" > 15 min?
  - High tickets in "new" > 30 min?
  - Medium tickets in "new" > 60 min?
  - Low tickets in "new" > 120 min?
      |
      +--- SLA breached --> Tag: sla-breached, add escalation note
      |
      v
Check for abandoned tickets:
  - In-progress with no updates > 4 hours?
  - Escalated with no updates > 4 hours?
      |
      +--- Abandoned --> Add escalation note
      |
      v
Output summary
Session terminates
```

## Why This Exists

AI agents can fail silently. If an L2 investigation times out at the 15-minute TTL, the `l2-investigating` tag stays on the ticket forever, and no other agent will pick it up (they see the lock tag and assume someone's working on it). The SOC Manager breaks these deadlocks by cleaning up stale tags after 30 minutes.

It also catches tickets that fall through the cracks -- for example, if the D&R suppression rate limit was hit during an alert storm and some tickets were never picked up.

## Design Philosophy

The SOC Manager **monitors** but does not **investigate**. It:
- Removes stale tags (so other agents can retry)
- Flags SLA violations (so humans are aware)
- Adds notes (documenting what it found)

It does NOT:
- Change ticket status
- Close or resolve tickets
- Perform any investigation work

## API Key Permissions

Create an API key named `soc-manager` with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `investigation.get` | List and read tickets, check dashboard |
| `investigation.set` | Add tags, notes to flag issues |
| `ext.request` | Invoke extensions |
| `ai_agent.operate` | Allow the agent to run |

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `sonnet` | Health checks don't need deep reasoning |
| `max_turns` | `30` | Enough to check all ticket states |
| `max_budget_usd` | `0.50` | Low budget -- mostly listing and tagging |
| `ttl_seconds` | `300` | 5 minute hard timeout |
| `one_shot` | `true` | Terminates after completing |
| Schedule | `1h_per_org` | Runs every hour per organization |

## Files

- `hives/ai_agent.yaml` - Agent definition with monitoring prompt
- `hives/dr-general.yaml` - D&R rule: triggers on `1h_per_org` schedule event
- `hives/secret.yaml` - Placeholder secrets
