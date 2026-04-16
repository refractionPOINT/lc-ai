---
name: output-streams
description: Understanding LimaCharlie output stream structures — the four data streams (event, detect, audit, deployment) have different schemas, fields, and use cases. Covers stream structures, detection fields, audit log format, deployment events, filtering, and configuration. Use when configuring outputs, parsing LimaCharlie data in external systems, or understanding detection/audit/deployment stream formats.
allowed-tools:
  - Bash
  - Read
---

# Output Streams

LimaCharlie routes data through four distinct output streams. Each has a **different schema** — they are NOT interchangeable. Understanding these structures is essential for configuring outputs, building parsers in external systems, and filtering data.

## Stream Overview

| Stream | Purpose | Volume | Common Destinations |
|--------|---------|--------|---------------------|
| `event` | Real-time telemetry from sensors/adapters | High | SIEM, data lake, long-term storage |
| `detect` | Alerts from D&R rules | Low-Medium | SIEM, SOAR, incident response |
| `audit` | Platform management actions | Low | Compliance logging, audit trails |
| `deployment` | Sensor lifecycle events | Very Low | Asset management, deployment tracking |

## Event Stream

Canonical two-level structure. Every event has `routing` (metadata) and `event` (payload):

```json
{
  "routing": {
    "oid": "8cbe27f4-...",
    "sid": "bb4b30af-...",
    "event_type": "NEW_PROCESS",
    "event_time": 1656959942437,
    "event_id": "8cec565d-...",
    "hostname": "workstation-01",
    "iid": "7d23bee6-...",
    "did": "b97e9d00-...",
    "ext_ip": "203.0.113.45",
    "int_ip": "10.0.1.25",
    "plat": 268435456,
    "arch": 2,
    "this": "a443f9c48bef700740ef27e062c333c6",
    "parent": "42217cb0326ca254999554a862c3298e",
    "tags": ["production"]
  },
  "event": {
    "FILE_PATH": "C:\\Windows\\System32\\cmd.exe",
    "COMMAND_LINE": "cmd.exe /c whoami",
    "PROCESS_ID": 4812,
    "USER_NAME": "Administrator",
    "PARENT": {
      "FILE_PATH": "C:\\Windows\\explorer.exe",
      "PROCESS_ID": 2156
    }
  }
}
```

Key event types: `NEW_PROCESS`, `DNS_REQUEST`, `NETWORK_CONNECTIONS`, `FILE_MODIFIED`, `WEL` (Windows Event Logs), `MODULE_LOAD`, `REGISTRY_WRITE`, `SENSITIVE_PROCESS_ACCESS`.

## Detection Stream

Alerts from D&R rules. **Different structure from events** — flat object with detection-specific fields:

```json
{
  "cat": "Suspicious PowerShell Execution",
  "source": "dr-general",
  "routing": { "..." },
  "detect": {
    "FILE_PATH": "C:\\...\\powershell.exe",
    "COMMAND_LINE": "powershell.exe -enc SGVsbG8="
  },
  "detect_id": "f1e2d3c4-...",
  "priority": 7,
  "detect_mtd": { "rule_name": "detect-encoded-powershell" },
  "detect_data": {
    "suspicious_process": "powershell.exe",
    "encoded_command": "SGVsbG8="
  },
  "source_rule": "detect-encoded-powershell",
  "rule_tags": ["windows", "powershell"],
  "gen_time": 1656959942500
}
```

### Detection Fields

| Field | Type | Description |
|-------|------|-------------|
| `cat` | string | Detection name/category (from `report` action's `name`) |
| `source` | string | Rule source: `dr-general`, `dr-managed`, `dr-service` |
| `routing` | object | Inherited from triggering event |
| `detect` | object | Copy of event data that triggered detection |
| `detect_id` | UUID | Unique detection identifier |
| `priority` | integer | Detection priority (0-10, from `report` action) |
| `detect_mtd` | object | Rule metadata (from `report` action's `metadata`) |
| `detect_data` | object | **Structured IOCs** (from `report` action's `detect_data`) |
| `source_rule` | string | Rule name that generated this |
| `rule_tags` | list | Tags from the D&R rule |
| `gen_time` | integer | Detection creation timestamp (ms) |

### `detect_data` — Structured IOCs

The `detect_data` field contains pre-parsed IOCs extracted by the rule. This is the primary integration point for:
- Automated enrichment (lookup IPs, domains, hashes)
- SOAR playbook inputs
- Case management systems
- Threat intelligence platforms

## Audit Stream

Platform management events. **Completely different structure** — flat object, does NOT use the routing/event split:

```json
{
  "oid": "8cbe27f4-...",
  "ts": "2024-06-05T14:23:18Z",
  "etype": "config_change",
  "msg": "D&R rule created",
  "origin": "api",
  "time": 1656959942,
  "ident": "user@company.com",
  "entity": {
    "type": "dr_rule",
    "name": "detect-encoded-powershell",
    "hive": "dr-general"
  },
  "mtd": {
    "action": "create",
    "source_ip": "203.0.113.10"
  }
}
```

### Audit Fields

| Field | Type | Description |
|-------|------|-------------|
| `oid` | UUID | Organization ID |
| `ts` | string | ISO 8601 timestamp |
| `etype` | string | Event type (config_change, api_call, user_action, error) |
| `msg` | string | Human-readable message |
| `origin` | string | Origin: `api`, `ui`, `cli`, `system` |
| `ident` | string | Identity (email, API key name) |
| `entity` | object | Object acted upon (type, name, hive) |
| `mtd` | object | Metadata (action, source_ip, user_agent) |
| `error` | string | Error message (if applicable) |

## Deployment Stream

Sensor lifecycle events. Uses routing/event structure like events but with deployment-specific event types:

| Event Type | Description |
|------------|-------------|
| `sensor_installed` | New sensor deployment |
| `sensor_uninstalled` | Sensor removal |
| `sensor_upgraded` | Version update |
| `sensor_clone` | Duplicate sensor ID detected |
| `sensor_over_quota` | Sensor exceeds org quota |
| `deleted_sensor` | Sensor deletion |
| `sensor_checkin` | Periodic heartbeat |

Use deployment events to detect unexpected sensor removals (potential evasion), track sensor versions, and monitor fleet coverage.

## Output Configuration

### CLI Commands

```bash
# List outputs
limacharlie output list --oid <oid> --output yaml

# Create output
cat > /tmp/output.yaml << 'EOF'
name: my-syslog
module: syslog
for: detect
dest_host: siem.example.com:514
EOF
limacharlie output create --input-file /tmp/output.yaml --oid <oid> --output yaml

# Delete output
limacharlie output delete --name <name> --confirm --oid <oid>
```

### Stream Filtering

**Filter parameters use newline-separated string format, NOT YAML arrays.**

```yaml
# Event type filtering (whitelist)
event_white_list: |
  NEW_PROCESS
  DNS_REQUEST

# Event type filtering (blacklist)
event_black_list: |
  CONNECTED
  DNS_REQUEST

# Detection category filtering
cat_white_list: |
  high-priority
  critical

# Tag-based filtering (single tag)
tag: production

# Tag blacklist
tag_black_list: |
  dev
  test

# Rule tag filtering (detection stream only)
rule_tag_white_list: |
  compliance
  ransomware
```

### Tailored Output Stream

The `output` D&R response action forwards a matched event to a specific output in the `tailored` stream. This enables highly granular routing — e.g., send only specific detection types to a specific webhook:

```yaml
- action: output
  name: my-webhook-output
```

## Gotchas Summary

| Gotcha | Detail |
|--------|--------|
| Streams have different schemas | Event (routing+event), detect (flat+detect), audit (flat, no routing/event), deployment (routing+event) |
| Filter format is newline-separated | NOT YAML arrays — use pipe `\|` multiline strings |
| Audit stream is flat | No routing/event split — uses `oid`, `ts`, `etype`, `ident` |
| `detect_data` is the integration point | Pre-parsed IOCs for SOAR/SIEM integration |
| Detection timestamps in milliseconds | `event_time` and `gen_time` are ms (13 digits) |
| Batch outputs have latency | S3, SFTP, GCS batch by size/time. Syslog is live. |
