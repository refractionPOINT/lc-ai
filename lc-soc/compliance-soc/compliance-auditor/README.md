# Compliance Auditor

Daily compliance posture assessment agent. Discovers all connected data sources (EDR, identity providers, cloud audit, email/collaboration), analyzes real telemetry for compliance-relevant events, calculates framework scores, and tracks gaps until resolution.

## What It Does

1. **Discovers the environment** — lists all sensors and adapters to understand what's connected
2. **Verifies data source health** — confirms each adapter is actually sending data (catches silent failures)
3. **Analyzes compliance-relevant telemetry** — queries identity provider logs for access control events, cloud audit logs for infrastructure changes, EDR telemetry for monitoring health
4. **Calculates framework scores** — weighted scoring per SOC 2, ISO 27001, PCI-DSS v4, and CIS v8
5. **Tracks compliance gaps** — creates dedicated cases for each gap, updates them daily until resolved
6. **Produces audit evidence** — each daily case is a complete compliance evidence artifact

## Configuration

### Framework Selection (Optional)

Create a `compliance-frameworks` SOP (hive record) to customize:
```yaml
# limacharlie hive set --hive-name sop --key compliance-frameworks --oid <oid>
data:
  text: |
    Frameworks: SOC 2, PCI-DSS v4
    PCI scope limited to sensors tagged "pci-scope"
    Audit period: Jan 1 - Dec 31 2026
usr_mtd:
  enabled: true
```

If no SOP exists, all four frameworks are assessed with all sensors in scope.

## Trigger

Scheduled: runs once every 24 hours per organization (`24h_per_org`).

## Model & Budget

| Parameter | Value |
|-----------|-------|
| Model | opus |
| Budget | $5.00 per run |
| TTL | 900 seconds (15 minutes) |
| Max turns | 60 |

## API Key Permissions

```
org.get,sensor.list,sensor.get,dr.list,dr.list.managed,insight.evt.get,insight.det.get,insight.stat,ext.request,ext.conf.get,investigation.get,investigation.set,output.list,lookup.get,lookup.set,audit.get,ai_agent.operate
```

## Lookup Tables Used

| Lookup | Purpose |
|--------|---------|
| `compliance-state` | Previous run metrics, posture scores, data source inventory (for trend comparison) |
| `compliance-gaps` | Active compliance gaps with case number references |

## Case Output

### Daily Audit Case (INFO severity)
- **Note 1**: Environment & data source map (what's connected, health status)
- **Note 2**: Identity & access findings (if identity provider connected)
- **Note 3**: Cloud security findings (if cloud audit connected)
- **Note 4**: Endpoint & detection coverage
- **Note 5**: Incident response posture (if ext-cases subscribed)
- **Note 6**: Framework posture summary (scores, trends, gaps, recommendations)
- **Tags**: `compliance-audit`, `daily-audit`
- **Disposition**: Closed if no critical gaps; Escalated if critical gaps found

### Gap Cases (severity varies)
- One case per compliance gap, tracked by stable key in lookup table
- Updated daily with current status until resolved
- **Tags**: `compliance-gap`, `framework:<name>`
