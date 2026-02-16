---
name: sensor-tasking
description: Send tasks (commands) to EDR sensors to gather data or take action. Handles offline agents via reliable-tasking, collects responses via LCQL queries, and creates D&R rules for automated response handling. Use for live response, data collection, forensic acquisition, or fleet-wide operations like "get OS version from all Windows servers" or "isolate all hosts with tag X".
allowed-tools:
  - Task
  - Read
  - Bash
  - Skill
---

# Sensor Tasking - Query and Command EDR Agents

This skill orchestrates sending tasks (commands) to EDR sensors and handling responses. It solves two key challenges of sensor tasking:

1. **Offline agents**: Sensors may be offline when you want to task them
2. **Response collection**: Some tasks generate data that needs to be collected

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

## When to Use

Use this skill when the user wants to:
- **Live Response**: Query running processes, network connections, registry keys, services
- **Forensic Collection**: Collect memory maps, file listings, autoruns, packages
- **Fleet Operations**: Execute commands across many sensors (by tag, platform, etc.)
- **Incident Response**: Isolate hosts, kill processes, gather evidence
- **Data Collection at Scale**: Get OS versions, installed software, users across fleet

Example requests:
- "Get running processes from sensor X"
- "List all files in C:\Windows\Temp on compromised hosts"
- "Get OS version from all Windows servers when they come online"
- "Run a memory collection on all hosts tagged 'incident-response'"
- "Execute netstat on all online Linux servers"

## Core Concepts

### Challenge 1: Offline Agents

**Direct tasking** (`get_processes`, `dir_list`, etc.) only works for **online** sensors. If a sensor is offline, the task fails immediately.

**Reliable tasking** queues tasks for delivery when sensors come online. Tasks persist for a configurable TTL (default: 1 week).

| Approach | Use When | Pros | Cons |
|----------|----------|------|------|
| Direct Task | ≤5 online sensors, need immediate response | Fast, response inline | Fails if offline |
| Reliable Task | >5 sensors, offline sensors, or can wait | Guaranteed delivery | Response via telemetry |

### Challenge 2: Receiving Responses

| Method | Use When | How It Works |
|--------|----------|--------------|
| Inline Response | Direct tasking small numbers | Response returned directly from API |
| LCQL Query | Need to collect reliable task responses | Query for `routing/investigation_id` containing your `context` |
| D&R Rule | Need automated action on responses | Create rule matching `investigation_id`, with response actions |

## Decision Tree

```
START: User wants to task sensors
    |
    v
Are all targets online AND ≤5 sensors?
    |
    |--YES--> Use Direct Tasking (inline response, parallel execution)
    |
    |--NO--> Use Reliable Tasking (>5 sensors OR any offline)
              |
              v
       Do you need the response data?
              |
              |--NO (action-only like isolate)--> Create Reliable Task, done
              |
              |--YES--> Do you need automated handling?
                        |
                        |--NO--> Create Reliable Task, wait 2+ min, then LCQL query
                        |
                        |--YES--> 1. Create D&R rule with TTL FIRST
                                  2. THEN create Reliable Task
                                  (rule must exist before task to avoid missing responses)
```

## How to Use

### Step 1: Understand the Request

Parse the user's request to determine:
- **Target scope**: Single sensor, selector, all sensors?
- **Task type**: Data collection (needs response) or action (unidirectional)?
- **Urgency**: Need immediate response or can wait?
- **Response handling**: Inline, LCQL collection, or automated D&R?

### Step 2: Get Organization and Sensors

If you don't have the OID, get it first:

```bash
limacharlie org list --output json
```

Check sensor status if targeting specific sensors:

```bash
limacharlie sensor online <sid> --oid <oid> --output json
```

> **CRITICAL: Filter to Taskable EDR Sensors**
>
> Before spawning executor agents or tasking sensors, you MUST verify sensors are **EDR agents** (not adapters or cloud sensors).
> Non-EDR sensors will fail with `UNSUPPORTED_FOR_PLATFORM`.
>
> **Taskable sensors require BOTH:**
> - **Platform**: `windows`, `linux`, `macos`, or `chrome`
> - **Architecture**: NOT `usp_adapter` (code 9)
>
> A sensor running on Linux platform but with `arch=usp_adapter` is an **adapter** (USP), not an EDR agent. These adapters forward logs but cannot execute commands.
>
> **Use combined selector when listing sensors:**
> ```bash
> limacharlie sensor list --selector "(plat==windows or plat==linux or plat==macos) and arch!=usp_adapter" --online --oid <oid> --output json
> ```
>
> **Or check sensor info** before tasking - verify both `platform` is in `["windows", "linux", "macos", "chrome"]` AND `arch` is not `9` / `usp_adapter`.

### Step 3A: Direct Tasking (≤5 Online Sensors)

For immediate data collection from a small number of online sensors (up to 5), use direct tasking functions with parallel execution.

**Available Direct Task Functions** (return response inline):

| Function | Description | Common Use |
|----------|-------------|------------|
| `get_processes` | Running processes | Process investigation |
| `get_process_modules` | Loaded modules | Malware analysis |
| `get_network_connections` | Active connections | C2 hunting |
| `get_os_version` | OS details | Asset inventory |
| `get_users` | System users | Account enumeration |
| `get_services` | Windows services | Persistence check |
| `get_drivers` | Loaded drivers | Rootkit detection |
| `get_autoruns` | Persistence mechanisms | Malware persistence |
| `get_packages` | Installed packages | Software inventory |
| `get_registry_keys` | Registry values | Config/persistence |
| `dir_list` | Directory listing | File investigation |
| `find_strings` | String search | Memory forensics |
| `yara_scan_process` | YARA scan process | Malware detection |
| `yara_scan_file` | YARA scan file | File analysis |
| `yara_scan_directory` | YARA scan directory | Bulk scanning |
| `yara_scan_memory` | YARA scan memory | Memory malware |

**Example - Get processes from a sensor:**

```bash
limacharlie task send --sid <sid> --task os_processes --oid <oid> --output json
```

### Step 3B: Reliable Tasking (>5 Sensors or Offline)

For more than 5 sensors, offline sensors, or fleet-wide operations, use reliable tasking.

> **IMPORTANT: Order of Operations**
>
> If you need automated response handling via D&R rules, you **MUST create the D&R rule FIRST**, before creating the reliable task. This ensures no responses are missed between task creation and rule deployment.
>
> Order: **D&R Rule → Reliable Task** (not the other way around)

**Create a reliable task:**

```bash
limacharlie task reliable-send --task 'os_version' --selector 'plat==windows' --context 'fleet-inventory-2024-01' --ttl 86400 --oid <oid> --output json
```

**Key Parameters:**
- `task`: The command to execute (e.g., `os_version`, `mem_map --pid 4`, `run --shell-command whoami`)
- `selector`: Sensor selector expression (e.g., `plat==windows`, `production in tags`, `sid=='abc-123'`)
- `context`: Identifier that appears in `routing/investigation_id` of responses (for collection)
- `ttl`: Time-to-live in seconds (default: 604800 = 1 week)

**Available Task Commands:**

Any sensor command can be used as a task. Common ones:

| Task Command | Description |
|--------------|-------------|
| `os_version` | Get OS details |
| `mem_map --pid [pid]` | Memory map of process |
| `mem_strings --pid [pid]` | Strings from process memory |
| `file_get [path]` | Get file contents |
| `dir_list [path]` | List directory |
| `netstat` | Network connections |
| `run --shell-command [cmd]` | Execute shell command |
| `deny_tree -p [process]` | Kill process tree |
| `isolate_network` | Network isolation |
| `rejoin_network` | End network isolation |

### Step 4: Collecting Responses

#### Option A: LCQL Query (Manual Collection)

After reliable tasking, wait at least 2 minutes for responses to arrive, then query:

**First, generate the LCQL query:**

```bash
limacharlie ai generate-query --prompt "Find all events in the last 2 hours where investigation_id contains 'fleet-inventory-2024-01'" --oid <oid> --output json
```

**Then run the query:**

```bash
limacharlie search run --query "<generated_query>" --start <ts> --end <ts> --oid <oid> --output json
```

#### Option B: D&R Rule (Automated Handling)

For automated response handling, create a D&R rule that matches the investigation_id.

> **CRITICAL**: Create the D&R rule **BEFORE** creating the reliable task. Online sensors may respond within milliseconds - if the rule doesn't exist yet, those responses will be missed.

**Step 1: Generate the detection:**

```bash
limacharlie ai generate-detection --description "Match events where investigation_id contains 'fleet-inventory-2024-01'" --oid <oid> --output json
```

**Step 2: Generate the response:**

```bash
limacharlie ai generate-response --description "Report to output 'siem' and add detection 'FLEET_INVENTORY_RESPONSE'" --oid <oid> --output json
```

**Step 3: Validate the rule:**

```bash
limacharlie rule validate --detect '<detection_yaml>' --respond '<response_yaml>' --oid <oid>
```

**Step 4: Deploy with expiry:**

Calculate expiry timestamp (e.g., 7 days from now):
```bash
date -d '+7 days' +%s
```

```bash
limacharlie rule create temp-fleet-inventory-handler --detect '<detection_yaml>' --respond '<response_yaml>' --oid <oid>
```

**Step 5: NOW create the reliable task**

Only after the D&R rule is deployed, create the reliable task (see Step 3B above). The rule will catch all responses as sensors execute the task.

## Monitoring Reliable Tasks

**List pending tasks:**

```bash
limacharlie task reliable-list --oid <oid> --output json
```

**Delete/cancel a task:**

```bash
limacharlie task reliable-delete --task-id <task_id> --oid <oid>
```

## Example Workflows

### Example 1: Get Processes from Single Sensor

User: "Get running processes from sensor abc-123"

```bash
# Check if online
limacharlie sensor online abc-123 --oid c7e8f940-... --output json

# If online, get processes directly
limacharlie task send --sid abc-123 --task os_processes --oid c7e8f940-... --output json
```

### Example 2: Fleet-Wide OS Inventory

User: "Get OS version from all Windows servers when they come online"

```bash
# Create reliable task with context for later collection
limacharlie task reliable-send --task 'os_version' --selector 'plat==windows' --context 'os-inventory-20240120' --oid c7e8f940-... --output json
```

Response to user:
"Created reliable task to collect OS version from all Windows sensors.
- Online sensors will execute immediately
- Offline sensors will execute when they reconnect
- Task will remain active for 1 week (default TTL)
- Use context 'os-inventory-20240120' to query responses via LCQL"

### Example 3: Incident Response Collection

User: "Run memory collection on all hosts tagged 'incident-response', I need the data sent to our SIEM"

```
# Step 1: Create D&R rule FIRST to forward responses to SIEM
# (Use detection-engineering skill or manual D&R creation)
# Rule should match: routing/investigation_id contains "ir-memcollect-001"
# Response should: report to SIEM output

# Step 1: Create D&R rule FIRST
limacharlie rule create temp-ir-memcollect-handler \
  --detect '{"op": "contains", "path": "routing/investigation_id", "value": "ir-memcollect-001"}' \
  --respond '[{"action": "report", "name": "IR_MEMCOLLECT_RESPONSE", "to": "siem"}]' \
  --oid c7e8f940-...

# Step 2: THEN create reliable task (rule is now in place to catch responses)
limacharlie task reliable-send \
  --task 'mem_map --pid 4' \
  --selector 'incident-response in tags' \
  --context 'ir-memcollect-001' \
  --ttl 172800 \
  --oid c7e8f940-... --output json
```

### Example 4: Quick Data Collection with Inline Response

User: "What's the OS version on all 5 of our production Linux servers?"

If sensors are online and small in number, parallel direct tasking is faster:

```bash
# Run parallel tasks for each sensor
limacharlie task send --sid sid1 --task os_version --oid <oid> --output json &
limacharlie task send --sid sid2 --task os_version --oid <oid> --output json &
limacharlie task send --sid sid3 --task os_version --oid <oid> --output json &
limacharlie task send --sid sid4 --task os_version --oid <oid> --output json &
limacharlie task send --sid sid5 --task os_version --oid <oid> --output json &
wait
```

## Important Notes

### Taskable Sensors (EDR Only)

> **WARNING**: Sensor tasking only works for **EDR agents** (real endpoint agents). Cloud sensors, adapters, and USP log sources cannot receive tasks.

**Taskable sensors require BOTH conditions:**
1. **Platform** is Windows, Linux, macOS, or Chrome
2. **Architecture** is NOT `usp_adapter` (code 9)

**Platforms that support tasking:**

| Platform | Platform ID (hex) | Platform ID (decimal) | Selector |
|----------|-------------------|----------------------|----------|
| Windows | `0x10000000` | 268435456 | `plat==windows` |
| Linux | `0x20000000` | 536870912 | `plat==linux` |
| macOS | `0x30000000` | 805306368 | `plat==macos` |
| Chrome | Architecture `0x00000006` | 6 | `arch==chromium` |

**Non-taskable sensors include:**
- Cloud sensors (Office365, Okta, AWS, GCP, Azure, etc.)
- External adapters (`ext-*` sensors like ext-zeek, ext-strelka)
- USP log sources (Syslog, S3 buckets, webhooks)
- **Any sensor with `arch=usp_adapter`** (architecture code 9) - even if platform is Linux/macOS

These sensors will return `UNSUPPORTED_FOR_PLATFORM` errors when tasked.

**Recommendation**: When tasking a fleet, filter by **both platform AND architecture**:
- Use combined selector: `(plat==windows or plat==linux or plat==macos) and arch!=usp_adapter`
- Or check sensor info for both `platform` and `arch` fields before direct tasking

### Extension Requirement

**Reliable tasking requires the `ext-reliable-tasking` extension** to be subscribed in the organization. If you get a 403 error, the extension may not be enabled.

### Selector Syntax

Selectors use bexpr syntax:
- `plat==windows` - Windows sensors
- `plat==linux` - Linux sensors
- `production in tags` - Sensors with 'production' tag
- `hostname matches '^web-'` - Hostname starts with 'web-'
- `sid=='abc-123-def-456'` - Specific sensor
- `*` - All sensors

### Context for Response Collection

The `context` parameter in reliable tasking:
- Appears in `routing/investigation_id` of response events
- Use unique identifiers (include date/time)
- Can be used in LCQL queries or D&R rules for matching

### Timestamps

When setting TTL or expiry:
- Use bash for timestamp calculation: `date -d '+7 days' +%s`
- TTL is in seconds from now
- D&R rule expiry is absolute Unix timestamp

## Related Skills

- `detection-engineering` - For creating D&R rules to handle responses
- `sensor-health` - For checking sensor online status across fleet
- `sensor-coverage` - For understanding fleet coverage before tasking

## Reference

- [ext-reliable-tasking documentation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Add-Ons/Extensions/LimaCharlie_Extensions/ext-reliable-tasking.md)
- Use `limacharlie task --ai-help` for CLI help
