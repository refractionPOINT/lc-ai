---
name: velociraptor
description: "Velociraptor DFIR integration for LimaCharlie. List available VQL artifacts, view artifact definitions, launch forensic collections on endpoints. Find raw collection data in Artifacts (type:velociraptor, source:SID). Query processed JSON events from the 'velociraptor' sensor (tag:ext:ext-velociraptor). Build D&R rules for velociraptor_collection events. Use for: forensic triage, incident response, threat hunting, VQL artifact collection."
allowed-tools:
  - Task
  - Read
  - Bash
---

# Velociraptor DFIR Integration

Launch Velociraptor forensic collections and work with collection results in LimaCharlie.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output json [flags]
```

For command help: `limacharlie <command> --ai-help`
For command discovery: `limacharlie discover`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **LCQL Queries** | Write query syntax manually | Use `limacharlie ai generate-query` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## Background

Velociraptor is an open source endpoint visibility tool for digital forensics, incident response, and triage. LimaCharlie integrates with Velociraptor via the `ext-velociraptor` extension.

### How Velociraptor Data Flows in LimaCharlie

When a Velociraptor collection runs:

1. **Raw Artifacts**: The collected data is stored as a ZIP file in LimaCharlie's Artifact system
   - Filter by: `artifact_type: velociraptor`
   - The `source` field contains the Sensor ID (SID) where it was collected

2. **Processed Events**: For small collections, data is also processed to JSON and ingested as sensor events
   - Events appear on a sensor with hostname: `velociraptor`
   - Tagged with: `ext:ext-velociraptor`
   - Event types: `velociraptor_collection`, `artifact_event`

3. **D&R Automation**: You can trigger on these events for automated workflows

## When to Use

Use this skill when the user wants to:
- List available Velociraptor artifacts for collection
- View the YAML definition of a specific artifact
- Launch Velociraptor collections on endpoints
- Find and download raw Velociraptor collection data
- Query processed Velociraptor events
- Build D&R rules for Velociraptor automation

## Prerequisites

The organization must have the `ext-velociraptor` extension subscribed.
> The `limacharlie` CLI must be available.

## How to Use

### Step 1: Get the Organization ID

If not already known, get the OID:

```bash
limacharlie org list --output json
```

### Step 2: List Available Velociraptor Artifacts

List all VQL artifacts available for collection (built-in and external from triage.velocidex.com):

```bash
limacharlie velociraptor list-artifacts --oid <oid> --output json
```

### Step 3: View Artifact Definition

Before collecting, view an artifact's YAML to understand its parameters:

```bash
limacharlie velociraptor show-artifact Windows.System.Drivers --oid <oid> --output json
```

### Step 4: Launch a Collection

Collect from a single sensor:

```bash
limacharlie velociraptor collect --sid <sensor-id> --artifact Windows.System.Drivers --oid <oid> --output json
```

Collect from multiple sensors using a selector:

```bash
limacharlie velociraptor collect \
  --selector "plat == windows" \
  --artifact Windows.KapeFiles.Targets \
  --args "KapeTriage=Y" \
  --collection-ttl 3600 \
  --retention-ttl 7 \
  --oid <oid> --output json
```

### Step 5: Find Collection Results (Raw Artifacts)

List raw Velociraptor artifacts stored in the Artifact system:

```bash
limacharlie artifact list --type velociraptor --sid <sensor-id> --oid <oid> --output json
```

Download an artifact:

```bash
limacharlie artifact get <artifact-id> --url-only --oid <oid> --output json
```

### Step 6: Query Processed Events

For small collections, data is also available as events. Use LCQL to query them.

**CRITICAL**: Always use `limacharlie ai generate-query` first - never write LCQL manually.

```bash
limacharlie ai generate-query --prompt "velociraptor_collection events from the last 7 days" --oid <oid> --output json
```

Then execute:

```bash
limacharlie search run --query "<generated-query>" --start <ts> --end <ts> --oid <oid> --output json
```

### Step 7: Find the Velociraptor Sensor

To find the virtual sensor that receives processed Velociraptor data:

```bash
limacharlie sensor list --selector "\`ext:ext-velociraptor\` in tags" --oid <oid> --output json
```

## Collection Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `artifact_list` | string[] | List of artifacts to collect (use one of artifact_list OR custom_artifact) |
| `custom_artifact` | string | Custom artifact YAML definition |
| `sid` | string | Single sensor ID (use one of sid OR sensor_selector) |
| `sensor_selector` | string | bexpr selector for multiple sensors (e.g., `plat == windows`) |
| `args` | string | Comma-separated artifact arguments (e.g., `KapeTriage=Y,EventLogs=Y`) |
| `collection_ttl` | int | Seconds to keep attempting collection (default: 604800 = 7 days) |
| `retention_ttl` | int | Days to retain collected artifacts (default: 7) |
| `ignore_cert` | bool | Ignore SSL certificate errors during collection |

## Common Velociraptor Artifacts

| Artifact | Platform | Description |
|----------|----------|-------------|
| `Windows.KapeFiles.Targets` | Windows | KAPE-style triage collection |
| `Windows.System.Pslist` | Windows | Running processes |
| `Windows.System.Drivers` | Windows | Loaded kernel drivers |
| `Windows.Network.Netstat` | Windows | Network connections |
| `Windows.EventLogs.Evtx` | Windows | Windows event logs |
| `Windows.Registry.UserAssist` | Windows | User activity tracking |
| `Generic.System.Pstree` | All | Process tree |
| `Linux.Sys.Users` | Linux | User accounts |
| `Linux.Sys.Syslog` | Linux | System logs |
| `MacOS.Applications.List` | macOS | Installed applications |

## Example D&R Rules

### Trigger on Artifact Upload

Detect when a Velociraptor collection completes:

```yaml
# Detection
op: is
path: routing/log_type
value: velociraptor
target: artifact_event

# Response
- action: report
  name: Velociraptor Collection Complete
- action: output
  name: my-siem-output
```

### Trigger on Collection Data

Process the actual collection data:

```yaml
# Detection
event: velociraptor_collection
op: exists
path: event/collection

# Response
- action: report
  name: Velociraptor Data Available
- action: output
  name: bigquery-tailored
```

### Trigger Collection from Detection

Start a Velociraptor collection as a response action:

```yaml
# Response (add to any detection)
- action: extension request
  extension action: collect
  extension name: ext-velociraptor
  extension request:
    artifact_list: ['Windows.KapeFiles.Targets']
    sid: '{{ .routing.sid }}'
    args: 'KapeTriage=Y'
    collection_ttl: 3600
    retention_ttl: 7
```

## Timestamps

When working with artifacts:

- **API parameters** (`start`, `end` in `list_artifacts`): Unix seconds (10 digits)
- **Never calculate timestamps manually** - use bash:

```bash
date +%s                        # Now
date -d '24 hours ago' +%s      # 24 hours ago
date -d '7 days ago' +%s        # 7 days ago
```

## Important Notes

- **Async operation**: `collect_velociraptor_artifact` returns immediately with a `job_id`; results are ingested asynchronously
- **Offline sensors**: Uses reliable-tasking for persistent delivery; collection attempts continue until `collection_ttl` expires
- **EDR sensors only**: Velociraptor collections can only run on **EDR agents**:
  - **Platform**: Windows (x86/x64), Linux (386/amd64/arm64), macOS (amd64/arm64)
  - **Architecture**: Must NOT be `usp_adapter` (code 9) - adapters cannot run collections
  - Use combined selector: `(plat==windows or plat==linux or plat==macos) and arch!=usp_adapter`
- **External artifacts**: Automatically downloaded from triage.velocidex.com if needed
- **Batch limit**: Up to 100 sensors can be tasked in parallel
- **Max artifact size**: Results larger than 100 MB (configurable) are skipped
- **Large collections**: Raw artifacts may be large (hundreds of MB). Use `get_url_only: true` and download externally

## Related Skills

- `list-artifacts` / `get-artifact` - Work with raw artifact files
- `detection-engineering` - Build D&R rules for Velociraptor events
- `sensor-tasking` - Execute live commands (alternative to Velociraptor for some use cases)

## Reference

- [Velociraptor Extension Documentation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Add-Ons/Extensions/Third-Party_Extensions/ext-velociraptor.md)
- [Velociraptor to BigQuery Tutorial](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Add-Ons/Extensions/Tutorials/velociraptor-to-bigquery.md)
- Use `limacharlie velociraptor --ai-help` for CLI help
