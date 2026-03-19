# Endpoint Compliance Checker

Weekly full-fleet endpoint compliance sweep. Analyzes 7 days of endpoint telemetry via LCQL for 8 compliance checks covering services, accounts, software, FIM, network, and driver integrity. Performs targeted active inventory on anomalous or high-value endpoints.

## What It Does

1. **Self-gates to weekly** — runs on the daily schedule but skips if a sweep was done within the last 6 days
2. **Full fleet LCQL sweep** — queries 7 days of telemetry across ALL endpoints (not sampling)
3. **8 compliance checks** — monitoring gaps, service changes, autorun persistence, account compliance, unauthorized software, FIM verification, network compliance, driver integrity
4. **Active inventory** — tasks up to 10 targeted endpoints for package/service/user inventory
5. **Gap tracking** — shares the `compliance-gaps` lookup with the compliance-auditor

## Compliance Checks

| Check | What It Catches | Frameworks |
|-------|----------------|------------|
| Monitoring coverage gaps | Enrolled sensors generating zero events | CIS 1, SOC 2 CC7.2, ISO A.8, PCI 10 |
| Service & daemon changes | Unauthorized services, stopped security services | CIS 4, PCI 2/6, ISO A.12 |
| Autorun & persistence | New persistence mechanisms, suspicious paths | CIS 4/10, PCI 5/11, ISO A.12 |
| Account & authentication | New local accounts, failed logins, root usage | CIS 5-6, SOC 2 CC6.1, PCI 8, ISO A.9 |
| Unauthorized software | Executables from temp/downloads, unsigned binaries | CIS 2, PCI 6, ISO A.12 |
| FIM operational verification | Endpoints with/without FIM events | PCI 11.5, SOC 2 CC6.1, CIS 3, ISO A.12 |
| Network compliance | Unusual ports, excessive connections, DNS anomalies | CIS 13, SOC 2 CC6.6, PCI 1, ISO A.13 |
| Driver & kernel integrity | Driver changes, unsigned drivers | CIS 10, PCI 5, ISO A.12 |

## Trigger

Scheduled: runs once every 24 hours per organization (`24h_per_org`), self-gates to weekly via `last-endpoint-sweep` in the `compliance-state` lookup table.

## Model & Budget

| Parameter | Value |
|-----------|-------|
| Model | opus |
| Budget | $5.00 per run |
| TTL | 900 seconds (15 minutes) |
| Max turns | 60 |

## API Key Permissions

```
org.get,sensor.list,sensor.get,sensor.task,insight.evt.get,insight.stat,ext.request,ext.conf.get,investigation.get,investigation.set,lookup.get,lookup.set,ai_agent.operate
```

## Lookup Tables Used

| Lookup | Purpose |
|--------|---------|
| `compliance-state` | Read/write `last-endpoint-sweep` date for weekly gating |
| `compliance-gaps` | Shared gap tracking with compliance-auditor |

## Case Output

### Weekly Sweep Case (INFO severity)
- **Note 1**: Fleet overview (platform breakdown, coverage percentages, silent endpoints)
- **Note 2**: Compliance check results (per-check findings with hostnames and SIDs)
- **Note 3**: Active inventory results (if performed)
- **Note 4**: Findings summary & recommendations
- **Tags**: `compliance-sweep`, `endpoint-compliance`
- **Disposition**: Closed normally; Escalated if critical endpoint failures found
