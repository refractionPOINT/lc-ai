---
name: cases
description: Working with LimaCharlie Cases — CRUD, lifecycle management, entities, telemetry references, notes, tags, merging, export, and bulk operations. Use when managing cases, adding evidence, updating case status, or querying the case queue.
allowed-tools:
  - Bash
  - Read
---

# Cases

How to work with LimaCharlie Cases (ext-cases extension). Cases are the SOC triage and investigation tracking system. For investigation methodology, see composed skills.

## Case Lifecycle

```
new -> in_progress -> resolved -> closed
resolved -> in_progress (reopen)
closed -> in_progress (reopen)
```

| Status | Description | SLA Impact |
|--------|-------------|------------|
| `new` | Created, not yet reviewed | Clock starts |
| `in_progress` | Active investigation | Records Time-to-Acknowledge |
| `resolved` | Investigation complete | Records Time-to-Resolve |
| `closed` | Terminal state | - |

## CLI Commands

### List Cases

```bash
limacharlie case list --oid <oid> --output yaml

# Filter by status
limacharlie case list --status new --status in_progress --oid <oid> --output yaml

# Filter by severity
limacharlie case list --severity critical --severity high --oid <oid> --output yaml

# Filter by assignee
limacharlie case list --assignee analyst@example.com --oid <oid> --output yaml

# Filter by sensor
limacharlie case list --sensor-id <sid> --oid <oid> --output yaml

# Search
limacharlie case list --search <term> --oid <oid> --output yaml
```

### Get Case

```bash
limacharlie case get --case-number <number> --oid <oid> --output yaml
```

### Create Case (Manual)

Create a case without a detection trigger:

```bash
limacharlie case create --severity <severity> --summary "Description of the case" --oid <oid> --output yaml
```

### Update Case

```bash
# Status
limacharlie case update --case-number <number> --status in_progress --oid <oid> --output yaml

# Severity
limacharlie case update --case-number <number> --severity high --oid <oid> --output yaml

# Classification
limacharlie case update --case-number <number> --classification true_positive --oid <oid> --output yaml

# Summary and conclusion (supports Markdown)
limacharlie case update --case-number <number> \
  --summary "Attack narrative..." \
  --conclusion "Assessment and recommendations..." \
  --classification true_positive \
  --status resolved \
  --oid <oid> --output yaml
```

### Add Notes

```bash
limacharlie case add-note --case-number <number> --type analysis \
  --content "Investigation finding..." --oid <oid> --output yaml

# Long notes via file
limacharlie case add-note --case-number <number> --type analysis \
  --input-file /tmp/note.md --oid <oid> --output yaml
```

Note content supports Markdown formatting.

**Valid note types:** `general`, `analysis`, `remediation`, `recommendation`, `escalation`, `handoff`, `to_stakeholder`, `from_stakeholder`

Notes support an `is_public` flag — when true, the note may be shared externally.

### Add Entities (IOCs)

```bash
limacharlie case entity add --case <number> \
  --type ip --value "203.0.113.50" \
  --verdict malicious \
  --note "C2 server - 60+ beacon connections observed" \
  --oid <oid> --output yaml
```

**Valid entity types:** `ip`, `domain`, `hash`, `url`, `user`, `email`, `file`, `process`, `registry`, `other`

### Search Entities Across Cases

```bash
limacharlie case entity search --type ip --value "203.0.113.50" --oid <oid> --output yaml
```

### Add Telemetry References

```bash
limacharlie case telemetry add --case <number> \
  --atom "<event-atom>" --sid "<sensor-id>" \
  --event-type "NEW_PROCESS" \
  --ts "<event-timestamp>" \
  --verdict malicious \
  --note "Malicious process execution" \
  --oid <oid> --output yaml
```

**Valid verdicts:** `malicious`, `suspicious`, `benign`, `unknown`, `informational`

### Add Detections to Case

```bash
limacharlie case detection add --case <number> \
  --detection '<full detection JSON>' \
  --oid <oid> --output yaml
```

### Add Artifacts

```bash
limacharlie case artifact add --case <number> \
  --path "/forensics/memory/dump.dmp" \
  --source "DESKTOP-001" \
  --verdict malicious \
  --note "Memory dump from compromised host" \
  --oid <oid> --output yaml
```

### Tags

```bash
limacharlie case tag add --case-number <number> --tag phishing --oid <oid> --output yaml
limacharlie case tag remove --case-number <number> --tag <tag> --oid <oid> --output yaml
limacharlie case tag set --case-number <number> --tag <tag> --oid <oid> --output yaml
```

### Merge Cases

When multiple cases are part of the same incident:

```bash
limacharlie case merge --target <primary_number> --sources <num2>,<num3> --oid <oid> --output yaml
```

Source cases transition to `closed` with `merged_into_case_id` set.

### Export

```bash
# JSON to stdout
limacharlie case export --case-number <number> --oid <oid> --output yaml

# Full data export to directory
limacharlie case export --case-number <number> --with-data ./case-export --oid <oid>
```

### Bulk Operations

```bash
limacharlie case bulk-update --numbers <num1>,<num2> \
  --status closed --classification false_positive \
  --oid <oid> --output yaml
```

### Dashboard and Reporting

```bash
# Case count summary
limacharlie case dashboard --oid <oid> --output yaml

# SOC performance report
limacharlie case report --from 2025-01-01T00:00:00Z --to 2025-02-01T00:00:00Z --oid <oid> --output yaml
```

## Schema Reference

| Field | Valid Values |
|-------|-------------|
| **Status** | `new`, `in_progress`, `resolved`, `closed` |
| **Classification** | `pending`, `true_positive`, `false_positive` |
| **Severity** | `critical`, `high`, `medium`, `low`, `info` |
| **Verdict** | `malicious`, `suspicious`, `benign`, `unknown`, `informational` |
| **Entity Types** | `ip`, `domain`, `hash`, `url`, `user`, `email`, `file`, `process`, `registry`, `other` |
| **Note Types** | `general`, `analysis`, `remediation`, `recommendation`, `escalation`, `handoff`, `to_stakeholder`, `from_stakeholder` |
