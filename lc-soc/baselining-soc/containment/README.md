# Containment - Automated Threat Response

Takes action on confirmed threats. When L2 tags a ticket with `needs-containment`, this agent isolates compromised sensors and blocks malicious IOCs. For critical severity threats, it acts automatically. For everything else, it documents recommended actions for human review.

## What It Does

```mermaid
flowchart TD
    trigger["Tag: needs-containment<br/>(webhook event)"] --> tag["Tag: containing<br/>(remove needs-containment)"]
    tag --> review["Review ticket:<br/>Threat, affected sensors,<br/>malicious IOCs, L2 recommendations"]
    review --> severity{Severity check}
    severity -->|"CRITICAL +<br/>confirmed malicious"| auto["AUTO-CONTAIN<br/>Isolate sensors, block IOCs,<br/>document every action"]
    severity -->|"HIGH/MEDIUM/<br/>uncertain"| recommend["RECOMMEND ONLY<br/>Document what SHOULD be done,<br/>flag for human review"]
    auto --> done["Document actions as remediation note<br/>Tag: contained (remove containing)<br/>Resolve ticket, session terminates"]
    recommend --> done
```

## Containment Actions

| Action | Command | When |
|--------|---------|------|
| Sensor Isolation | `limacharlie sensor isolate` | Critical severity, confirmed malicious |
| Block Hash | Add to `soc-blocked-hashes` lookup | Any confirmed malicious hash |
| Block IP | Add to `soc-blocked-ips` lookup | Any confirmed malicious IP |
| Block Domain | Add to `soc-blocked-domains` lookup | Any confirmed malicious domain |

**Note**: The lookup tables (`soc-blocked-hashes`, `soc-blocked-ips`, `soc-blocked-domains`) must exist in the org. Create them manually or via IaC. D&R rules should reference these lookups to enforce blocking.

## Safety Guardrails

- Only auto-contains **CRITICAL severity** tickets with confirmed malicious IOCs
- HIGH/MEDIUM/LOW severity tickets get **documented recommendations only**
- Every action is logged as a ticket note **before** execution
- Conservative by default: when in doubt, recommend instead of acting

## API Key Permissions

Create an API key named `soc-containment` with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | List sensors for isolation |
| `sensor.get` | Get sensor details |
| `sensor.task` | Isolate sensors |
| `investigation.get` | Read tickets |
| `investigation.set` | Update tickets, add notes |
| `ext.request` | Invoke extensions |
| `ai_agent.operate` | Allow the agent to run |
| `lookup.set` | Add IOCs to block lookup tables |

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `sonnet` | Containment follows clear rules, doesn't need deep reasoning |
| `max_turns` | `30` | Enough for review + action |
| `max_budget_usd` | `1.0` | Low budget -- mostly executing commands |
| `ttl_seconds` | `300` | 5 minute hard timeout |
| `one_shot` | `true` | Terminates after completing |
| Suppression | `1 per ticket/30min` | Max one containment per ticket per 30 minutes |

## Files

- `hives/ai_agent.yaml` - Agent definition with containment prompt
- `hives/dr-general.yaml` - D&R rule: triggers on `tags_updated` containing `needs-containment`
- `hives/secret.yaml` - Placeholder secrets
