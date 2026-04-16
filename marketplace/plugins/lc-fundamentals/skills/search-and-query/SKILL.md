---
name: search-and-query
description: Querying data in LimaCharlie — LCQL generation, validation, execution, cost estimation, saved queries, detection listing, and event schema exploration. Use when searching telemetry, analyzing detections, exploring event types, or running LCQL queries.
allowed-tools:
  - Bash
  - Read
---

# Search & Query

How to query and explore data in LimaCharlie using LCQL, detection listing, and event schema tools.

## Critical Rule: NEVER Write LCQL Manually

LCQL uses a unique pipe-based syntax validated against org-specific schemas. **LLMs do NOT know correct LCQL syntax.** Any manually written LCQL will be invalid.

**ALWAYS use the generation + validation workflow below.**

## LCQL Workflow

### Step 1: Generate Query

Convert natural language to LCQL:

```bash
limacharlie ai generate-query --prompt "Find all NEW_PROCESS events with encoded PowerShell commands in the last hour" --oid <oid> --output yaml
```

### Step 2: Validate Query

**Mandatory for ALL queries** — even generated ones, user-provided ones, or saved queries:

```bash
limacharlie search validate --query "<query>" --oid <oid> --output yaml
```

### Step 3: Execute Query

```bash
start=$(date -d '1 hour ago' +%s) && end=$(date +%s)
limacharlie search run --query "<validated_query>" --start $start --end $end --oid <oid> --output yaml
```

Valid `--stream` values: `event`, `detect`, `audit`.

### Cost Estimation (Queries Beyond 30 Days)

For queries older than 30 days (paid queries), estimate cost first:

```bash
limacharlie search estimate --query "<query>" --start <ts> --end <ts> --oid <oid> --output yaml
```

Show the estimated cost to the user. If estimate > 0, ask for approval before running.

### On Validation Failure

Re-call `limacharlie ai generate-query` with the error message in the prompt. Never fix LCQL syntax manually. After 3 failures, report to user.

## Timestamp Rules

**NEVER calculate timestamps manually.** LLMs consistently produce incorrect values.

```bash
date +%s                              # Current time (seconds)
date -d '1 hour ago' +%s             # 1 hour ago
date -d '7 days ago' +%s             # 7 days ago
date -d '2025-01-15 00:00:00 UTC' +%s  # Specific date
```

**Milliseconds vs seconds:**
- Detection/event data timestamps: **milliseconds** (13 digits)
- API parameters (--start, --end): **seconds** (10 digits)
- **Always divide by 1000** when using detection timestamps for API queries

## Event Schema Exploration

### List Available Event Types

```bash
limacharlie event types --oid <oid> --output yaml
# Platform-specific:
limacharlie event types --platform windows --oid <oid> --output yaml
```

### Get Event Schema

```bash
limacharlie event schema --event-type NEW_PROCESS --oid <oid> --output yaml
```

### Check Data Availability

```bash
limacharlie event retention --sid <sid> --start <epoch> --end <epoch> --oid <oid> --output yaml
```

### List Events from a Sensor

```bash
start=$(date -d '1 hour ago' +%s) && end=$(date +%s)
limacharlie event list --sid <sid> --start $start --end $end --oid <oid> --output yaml
```

### Get a Specific Event by Atom

```bash
limacharlie event get --sid <sid> --atom <atom> --oid <oid> --output yaml
```

### Get Child Events

```bash
limacharlie event children --sid <sid> --atom <atom> --oid <oid> --output yaml
```

## Detection Listing

### List Detections

```bash
start=$(date -d '7 days ago' +%s) && end=$(date +%s)
limacharlie detection list --start $start --end $end --oid <oid> --output yaml
```

Filter by category:
```bash
limacharlie detection list --start $start --end $end --filter "[?cat=='suspicious_process']" --oid <oid> --output yaml
```

### Get a Specific Detection

```bash
limacharlie detection get --id <detect_id> --oid <oid> --output yaml
```

## IOC Search

Search for indicators of compromise across all sensors in an org:

```bash
limacharlie ioc search --type <type> --value "<value>" --oid <oid> --output yaml
```

Valid IOC types: `ip`, `domain`, `file_hash`, `file_path`, `file_name`, `user`, `service_name`, `package_name`.

## Saved Queries

### List Saved Queries

```bash
limacharlie search saved-list --oid <oid> --output yaml
```

### Create Saved Query

```bash
limacharlie search saved-create --name <name> --query "<lcql_query>" --stream event --oid <oid> --output yaml
```

### Run Saved Query

```bash
limacharlie search saved-run --name <name> --start <ts> --end <ts> --oid <oid> --output yaml
```

### Delete Saved Query

```bash
limacharlie search saved-delete --name <name> --oid <oid> --output yaml
```

## Data Streams

LimaCharlie has four data streams, each queryable differently:

| Stream | Content | Query Method |
|--------|---------|-------------|
| `event` | Real-time telemetry (processes, DNS, network, files) | LCQL, event list |
| `detection` | Alerts from D&R rules | detection list, LCQL |
| `audit` | Platform management events | LCQL |
| `deployment` | Sensor lifecycle events | LCQL |

## Downloading Large Results

When API calls return a `resource_link` URL:

```bash
# curl handles decompression automatically — do NOT pipe through gunzip
curl -sS "<resource_link_url>" | jq '.'
```
