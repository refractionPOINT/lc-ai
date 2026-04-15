---
name: sensor-tasking
description: Sending commands to EDR sensors for live response, data collection, and incident response. Covers direct tasking (online sensors), reliable tasking (offline/guaranteed delivery), response collection, and payload deployment. Use when tasking sensors, collecting data, or deploying payloads fleet-wide.
allowed-tools:
  - Bash
  - Read
---

# Sensor Tasking

How to send commands to EDR sensors and collect responses. This covers the mechanics of tasking — for higher-level workflows like investigation or fleet operations, see composed skills.

## Taskable Sensors (EDR Only)

Only EDR agents can receive tasks. Adapters and cloud sensors return `UNSUPPORTED_FOR_PLATFORM`.

**Taskable sensors require BOTH:**
1. Platform is `windows`, `linux`, `macos`, or `chrome`
2. Architecture is NOT `usp_adapter` (code 9)

```bash
# List only taskable sensors
limacharlie sensor list --selector "(plat==windows or plat==linux or plat==macos) and arch!=usp_adapter" --online --oid <oid> --output yaml
```

## Direct Tasking

For online sensors. Response is returned inline.

```bash
limacharlie task send --sid <sid> --task <command> --oid <oid> --output yaml
```

### Available Task Commands

| Command | Description |
|---------|-------------|
| `os_processes` | Running processes |
| `os_kill_process --pid <pid>` | Kill a process |
| `os_modules --pid <pid>` | Loaded modules |
| `netstat` | Active network connections |
| `os_version` | OS details |
| `os_users` | System users |
| `os_services` | Windows services |
| `os_drivers` | Loaded drivers |
| `os_autoruns` | Persistence mechanisms |
| `os_packages` | Installed packages |
| `reg_list <path>` | Registry values (Windows) |
| `dir_list <path>` | Directory listing |
| `file_get <path>` | Retrieve file contents |
| `mem_map --pid <pid>` | Memory map of process |
| `mem_strings --pid <pid>` | Strings from process memory |
| `find_strings` | String search |
| `yara_scan --pid <pid>` | YARA scan process |
| `yara_scan --filePath <path>` | YARA scan file |
| `yara_scan --dirPath <path>` | YARA scan directory |
| `run --shell-command <cmd>` | Execute shell command |
| `deny_tree -p <process>` | Kill process tree |
| `isolate_network` | Network isolation |
| `rejoin_network` | End network isolation |

### Parallel Direct Tasking

For multiple online sensors (up to ~5):

```bash
limacharlie task send --sid <sid1> --task os_version --oid <oid> --output yaml &
limacharlie task send --sid <sid2> --task os_version --oid <oid> --output yaml &
wait
```

## Reliable Tasking

For offline sensors or fleet-wide operations. Tasks queue and execute when sensors come online. Requires the `ext-reliable-tasking` extension.

```bash
limacharlie task reliable-send \
  --sid <sid> \
  --command '<task_command>' \
  --investigation-id '<unique_id>' \
  --ttl <seconds> \
  --oid <oid> --output yaml
```

**Key parameters:**
- `--sid`: Target sensor (one per call — loop for multiple sensors)
- `--command`: Task command string (e.g., `os_version`, `dir_list /tmp`)
- `--investigation-id`: Appears in `routing/investigation_id` of responses (for collection)
- `--ttl`: Time-to-live in seconds (default: 604800 = 1 week)

### Fleet Reliable Tasking Pattern

```bash
# Get sensor SIDs
limacharlie sensor list --selector 'plat==windows' --oid <oid> --filter '[].sid' --output yaml

# Loop and task each
for sid in <sid_list>; do
  limacharlie task reliable-send --sid $sid --command 'os_version' --investigation-id 'inventory-2025-04' --ttl 86400 --oid <oid> --output yaml
done
```

### Managing Reliable Tasks

```bash
# List pending tasks for a sensor
limacharlie task reliable-list --sid <sid> --oid <oid> --output yaml

# Cancel a task
limacharlie task reliable-delete --sid <sid> --task-id <task_id> --oid <oid>
```

## Collecting Responses

### Inline (Direct Tasking)

Response is returned directly from `limacharlie task send`.

### LCQL Query (Reliable Tasking)

After reliable tasking, wait 2+ minutes, then query by investigation ID:

```bash
limacharlie ai generate-query --prompt "Find events where investigation_id contains '<investigation_id>' in the last 2 hours" --oid <oid> --output yaml
limacharlie search run --query "<generated>" --start <ts> --end <ts> --oid <oid> --output yaml
```

### D&R Rule (Automated Handling)

Create a D&R rule matching `investigation_id` before creating reliable tasks. Online sensors may respond within milliseconds — if the rule doesn't exist yet, responses are missed.

**Order: D&R Rule first, then Reliable Task.**

## Payloads

Scripts or binaries stored in LimaCharlie, deployable to sensors.

```bash
# List payloads
limacharlie payload list --oid <oid> --output yaml

# Upload a payload
limacharlie payload upload --name <name> --file <path> --oid <oid> --output yaml

# Download a payload
limacharlie payload download --name <name> --output-path <path> --oid <oid>

# Delete a payload
limacharlie payload delete --name <name> --confirm --oid <oid>
```

Deploy payloads via reliable tasking with the `run` command.

## Synchronous Task Request

For tasks that need a synchronous response with a timeout:

```bash
limacharlie task request --sid <sid> --command '<task_command>' --timeout <seconds> --oid <oid> --output yaml
```

## Critical Rules

- **Always verify sensors are EDR** before tasking (platform + architecture check)
- **Reliable tasking is per-sensor** — loop over SIDs for fleet operations
- **D&R rules before reliable tasks** when using automated response handling
- **Use bash for timestamps**: `date -d '+7 days' +%s` for TTL calculations
- **ext-reliable-tasking must be subscribed** — 403 errors indicate the extension is missing
