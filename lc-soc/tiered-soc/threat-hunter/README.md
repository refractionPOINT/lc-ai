# Threat Hunter - Proactive IOC Hunting

The proactive arm of the SOC. When L2 confirms malicious IOCs and tags a ticket with `needs-threat-hunt`, this agent hunts across the entire organization for related compromise -- lateral movement, additional affected endpoints, and the same IOCs appearing on other sensors.

## What It Does

```
Tag: needs-threat-hunt (webhook event)
      |
      v
Tag: hunting (remove needs-threat-hunt)
      |
      v
Collect confirmed IOCs from ticket:
  - Hashes, IPs, domains, file paths
  - User accounts, process names
  - Registry keys, mutex names
      |
      v
Hunt org-wide (last 7 days):
  - Hash hunting (same files on other sensors)
  - Network IOC hunting (DNS/connections to same infra)
  - Process hunting (same execution patterns)
  - User hunting (compromised accounts elsewhere)
      |
      v
Analyze each hit:
  - Same incident or new compromise?
  - What's the context on that endpoint?
  - Is the endpoint compromised?
      |
      v
Document findings on source ticket
      |
      +--- New compromised endpoint? --> Create new ticket
      |    (picked up by L1 automatically)
      |
      v
Tag: hunted (remove hunting)
Session terminates
```

## Why Threat Hunting Matters

A single detection usually reveals one endpoint. But attackers rarely compromise just one machine. The Threat Hunter closes the gap between "we found it on one endpoint" and "we found it everywhere it exists."

New tickets created by the Threat Hunter automatically enter the SOC pipeline (Triage skipped since they're already tickets, L1 picks them up), creating a recursive investigation loop that expands until the full blast radius is mapped.

## API Key Permissions

Create an API key named `soc-threat-hunter` with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | List and search sensors org-wide |
| `sensor.get` | Get sensor details |
| `sensor.task` | Task sensors for additional context |
| `insight.det.get` | List and read detections org-wide |
| `insight.evt.get` | Access event data for IOC hunting |
| `investigation.get` | Read tickets |
| `investigation.set` | Update tickets, create new tickets, add notes |
| `ext.request` | Invoke extensions |
| `ai_agent.operate` | Allow the agent to run |

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Broad hunting requires strong reasoning |
| `max_turns` | `50` | Many IOCs to hunt, many sensors to check |
| `max_budget_usd` | `5.0` | Higher budget for thorough hunting |
| `ttl_seconds` | `900` | 15 minute hard timeout |
| `one_shot` | `true` | Terminates after completing |
| Suppression | `1 per ticket/30min` | Max one hunt per ticket per 30 minutes |

## Files

- `hives/ai_agent.yaml` - Agent definition with hunting prompt
- `hives/dr-general.yaml` - D&R rule: triggers on `tags_updated` containing `needs-threat-hunt`
- `hives/secret.yaml` - Placeholder secrets
