# L2 Analyst - Deep Investigation and Scope Assessment

The senior analyst. Only sees tickets that L1 has already investigated and escalated. Goes deep: lateral movement hunting, root cause analysis, full scope assessment, and MITRE ATT&CK mapping. Decides whether to trigger containment, threat hunting, or malware analysis downstream.

## What It Does

```
Ticket escalated (webhook event)
      |
      v
Tag ticket: "l2-investigating"
      |
      v
Review L1 findings (DO NOT repeat L1's work)
      |
      v
Deep investigation:
  - Lateral movement hunting
  - Root cause / initial access
  - Credential compromise assessment
  - Full scope across all sensors
  - C2 communication patterns
  - MITRE ATT&CK mapping
      |
      v
Update ticket with full picture:
  - Expanded summary and conclusion
  - Additional IOCs with verdicts
  - Attack timeline with MITRE mapping
      |
      +--- Needs containment? -----> tag: needs-containment
      |
      +--- Needs org-wide hunt? ---> tag: needs-threat-hunt
      |
      +--- Needs binary forensics? -> tag: needs-malware-analysis
      |
      +--- Fully resolved? --------> status: resolved
      |
      v
Remove "l2-investigating" tag
Session terminates
```

## Downstream Signaling

| Tag Added | Triggers | When |
|-----------|----------|------|
| `needs-containment` | Containment | Confirmed malicious, endpoints need isolation or IOCs need blocking |
| `needs-threat-hunt` | Threat Hunter | Confirmed IOCs that should be hunted org-wide |
| `needs-malware-analysis` | Malware Analyst | Binary needs deep forensic analysis (if L1 didn't already tag it) |

## What Sets L2 Apart from L1

- **L1** does systematic evidence gathering on the detection itself
- **L2** does cross-endpoint analysis, lateral movement hunting, and strategic assessment
- **L1** documents what happened on the affected sensor
- **L2** determines the full blast radius across the organization

## API Key Permissions

Create an API key named `soc-l2-analyst` with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | List and search sensors org-wide |
| `sensor.get` | Get sensor details |
| `sensor.task` | Task sensors for timeline, process trees |
| `dr.list` | List D&R rules for context |
| `insight.det.get` | List and read detections org-wide |
| `insight.evt.get` | Access event data for IOC searches |
| `investigation.get` | Read tickets |
| `investigation.set` | Update tickets, add notes, entities, telemetry |
| `ext.request` | Invoke extensions |
| `ai_agent.operate` | Allow the agent to run |

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Deep analysis requires strong reasoning |
| `max_turns` | `50` | More turns for org-wide investigation |
| `max_budget_usd` | `5.0` | Higher budget for thorough analysis |
| `ttl_seconds` | `900` | 15 minute hard timeout |
| `one_shot` | `true` | Terminates after completing |
| Suppression | `1 per ticket/30min` | Max one L2 session per ticket per 30 minutes |

## Files

- `hives/ai_agent.yaml` - Agent definition with deep investigation prompt
- `hives/dr-general.yaml` - D&R rule: triggers on ticket `escalated` webhook event
- `hives/secret.yaml` - Placeholder secrets
