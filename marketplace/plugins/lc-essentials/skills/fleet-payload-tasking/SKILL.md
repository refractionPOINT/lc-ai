---
name: fleet-payload-tasking
description: Deploy payloads and shell commands fleet-wide using reliable tasking. Execute scripts, collect data, or run commands across all endpoints with automatic handling of offline sensors. Use for vulnerability scanning, data collection, software inventory, compliance checks, or any fleet-wide operation.
allowed-tools:
  - Task
  - Read
  - Bash
  - Write
  - Skill
  - AskUserQuestion
---

# Fleet Payload Tasking Skill

Deploy payloads (scripts) or shell commands to all endpoints in an organization using reliable tasking. Handles offline sensors automatically - tasks queue and execute when sensors come online.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### API Access Pattern

All LimaCharlie API calls go through the `limacharlie-api-executor` sub-agent:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: <function-name>
    - Parameters: {<params>}
    - Return: RAW | <extraction instructions>
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **MCP Access** | Call `mcp__*` directly | Use `limacharlie-api-executor` sub-agent |
| **LCQL Queries** | Write query syntax manually | Use `generate_lcql_query()` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `list_user_orgs` if needed) |

> **Architecture Note**: This skill focuses on payload preparation and upload. It delegates the reliable tasking workflow (D&R rules, task deployment, response collection) to the `sensor-tasking` skill to avoid duplication.

---

## When to Use

Use this skill when the user needs to:
- **Run commands fleet-wide**: "Run this script on all Linux servers", "Execute a command across all endpoints"
- **Collect data from endpoints**: "Get OS version from all machines", "Collect installed packages"
- **Vulnerability scanning**: "Find all endpoints with log4j", "Check for vulnerable OpenSSL versions"
- **Software inventory**: "What versions of Chrome are installed?", "Find all Java installations"
- **Compliance checks**: "Verify security configurations across the fleet"
- **Custom data collection**: "Run this custom script and collect results"

## Two Deployment Approaches

### Approach 1: Shell Commands (Simple, Quick)

For simple data collection, use `run --shell-command` directly - no payload upload needed:

```
reliable_tasking(
  task="run --shell-command 'hostname'",
  selector="plat == macos",
  context="shell-scan-001",
  ttl=3600
)
```

**Pros:**
- No payload upload step
- Direct command execution
- Simpler workflow

**Cons:**
- Command line length limits
- Escaping becomes painful for complex scripts with quotes/JSON
- Less reusable

### Approach 2: Payload Scripts (Complex, Reusable)

For complex operations, upload a payload script first:

1. Create and upload payload
2. Create D&R rule to collect results
3. Deploy via reliable tasking
4. Collect artifacts

**Pros:**
- Handles complex logic
- Reusable across scans
- Can write large result files

**Cons:**
- More setup steps
- Requires payload management

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FLEET PAYLOAD TASKING                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  OPTION A: Shell Command (Simple)                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Build           │───▶│ Deploy via      │───▶│ D&R rule        │     │
│  │ run --shell-cmd │    │ reliable_tasking│    │ captures STDOUT │     │
│  │ command         │    │                 │    │ as detection    │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
│  OPTION B: Payload Script (Complex)                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Generate & Upload│───▶│ Create D&R rule │───▶│ Deploy via      │     │
│  │ payload script  │    │ to file_get     │    │ reliable_tasking│     │
│  │                 │    │ result file     │    │                 │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                    │                                    │
│                                    ▼                                    │
│                          ┌─────────────────┐                            │
│                          │ Results stored  │                            │
│                          │ as artifacts    │                            │
│                          └─────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Benefits

| Feature | Benefit |
|---------|---------|
| **Reliable Tasking** | Handles offline sensors - task executes when they come online |
| **Flexible Targeting** | Use sensor selectors (tags, platform, hostname patterns) |
| **Shell or Payload** | Choose simple commands or complex scripts |
| **Async Workflow** | Deploy now, collect results later |
| **Cross-Platform** | Linux, macOS, Windows support |
| **Scalable** | Works across thousands of endpoints |

## Platform Requirements

> **WARNING**: Only **EDR agents** support tasking (not adapters or cloud sensors).
>
> **Taskable sensors require BOTH:**
> - **Platform**: `windows`, `linux`, `macos`, or `chrome`
> - **Architecture**: NOT `usp_adapter` (code 9)
>
> A sensor running on Linux but with `arch=usp_adapter` is an **adapter** (USP), not an EDR.
> Cloud sensors, adapters, and USP log sources will fail with `UNSUPPORTED_FOR_PLATFORM`.

When using sensor selectors, always filter by **both platform AND architecture**:
- `(plat == windows or plat == linux or plat == macos) and arch != usp_adapter`

## Shell Command Escaping Considerations

When using `run --shell-command`, the command string is passed through multiple layers:
1. JSON encoding (in the reliable tasking API call)
2. Shell parsing on the endpoint

**Simple commands work well:**
```bash
run --shell-command whoami
run --shell-command 'ls -la /tmp'
run --shell-command "cat /etc/hostname"
```

**Complex operations become difficult:**
- Nested quotes: `echo '{"key":"value"}'` requires careful escaping
- Variable expansion: `$(command)` needs consideration
- Multiple commands: `cmd1 && cmd2 || cmd3` with complex logic
- JSON generation inline becomes messy quickly

**Rule of thumb:** If your command needs more than 2-3 simple pipes or redirects, or involves JSON/complex quoting, use a payload script instead.

## Shell Command Workflow (Recommended for Simple Tasks)

### Step 1: Select Organization

```
lc_call_tool(
  tool_name="list_user_orgs",
  parameters={}
)
```

### Step 2: Build Shell Command

Keep shell commands **simple** to avoid escaping nightmares:

```bash
# Example: Get hostname from endpoints
run --shell-command 'hostname'

# Example: Check for specific file
run --shell-command 'test -f /var/log/auth.log && echo "found" || echo "not found"'

# Example: Get OS information
run --shell-command 'uname -a'
```

> **WARNING**: For scripts with complex quoting, loops, JSON generation, or multiple commands, use the **Payload Script Workflow** instead to avoid escaping issues.

### Step 3: Deploy and Collect Results (Delegate to sensor-tasking)

> **IMPORTANT**: The `sensor-tasking` skill handles the complete deployment workflow:
> - Creates D&R rule for response collection (BEFORE task deployment)
> - Deploys via reliable tasking
> - Collects and formats results

Use the `sensor-tasking` skill with your prepared shell command:

```
Skill(lc-essentials:sensor-tasking)

Provide to sensor-tasking:
- Task command: run --shell-command 'hostname'
- Selector: plat == macos (or your target selector)
- Context: hostname-scan-001 (for response collection)
- TTL: 3600 (or desired expiration)
```

The sensor-tasking skill will:
1. Create a D&R rule to capture RECEIPT events with your context
2. Deploy the reliable task to matching sensors
3. Collect responses via LCQL query
4. Return aggregated results

See the **sensor-tasking** skill documentation for:
- D&R rule creation workflow
- Response collection via LCQL
- Monitoring task progress
- Result aggregation patterns

## Payload Script Workflow (For Complex Operations)

### Step 1: Generate Payload Script

Create a script that:
1. Performs the desired operation
2. Writes JSON results to a temp file
3. Outputs ONLY the file path to STDOUT

**Example: Cross-platform mktemp handling**

```bash
#!/bin/bash
SCAN_ID="$1"

# Cross-platform mktemp (macOS requires different syntax)
if [ "$(uname)" = "Darwin" ]; then
    OUTPUT_FILE=$(mktemp /tmp/lc-fleet-scan.XXXXXX)
    mv "$OUTPUT_FILE" "${OUTPUT_FILE}.json"
    OUTPUT_FILE="${OUTPUT_FILE}.json"
else
    OUTPUT_FILE=$(mktemp /tmp/lc-fleet-scan-XXXXXX.json)
fi

# Write results to file
echo '{"scan_id":"'$SCAN_ID'","hostname":"'$(hostname)'","results":[]}' > "$OUTPUT_FILE"

# CRITICAL: Output ONLY the file path
echo "$OUTPUT_FILE"
```

### Step 2: Upload Payload

Use `file_content` with base64-encoded script:

```bash
# Encode the script
base64 -w0 /tmp/my-payload.sh
```

```
lc_call_tool(
  tool_name="create_payload",
  parameters={
    "oid": "[org-id]",
    "name": "my-payload.sh",
    "file_content": "[base64-encoded-content]"
  }
)
```

### Step 3: Deploy and Collect Results (Delegate to sensor-tasking)

> **IMPORTANT**: The `sensor-tasking` skill handles the complete deployment workflow:
> - Creates D&R rule for response collection (BEFORE task deployment)
> - Deploys via reliable tasking
> - Collects and formats results

Use the `sensor-tasking` skill with your uploaded payload:

```
Skill(lc-essentials:sensor-tasking)

Provide to sensor-tasking:
- Task command: run --payload-name my-payload.sh --arguments 'scan-001'
- Selector: plat == linux (or your target selector)
- Context: scan-001 (for response collection)
- TTL: 604800 (1 week, or desired expiration)
```

The sensor-tasking skill will:
1. Create a D&R rule to capture RECEIPT events and trigger file_get
2. Deploy the reliable task to matching sensors
3. Collect artifacts from sensor responses
4. Return aggregated results

**Note**: For payload-based collection, you may want a D&R rule that:
- Matches the file path pattern in STDOUT
- Triggers `file_get` to retrieve the result file
- Stores results as artifacts

See the **sensor-tasking** skill documentation for advanced D&R rule patterns.

## Sensor Selectors

| Selector | Example | Description |
|----------|---------|-------------|
| All sensors | `*` | Every sensor in org |
| By platform | `plat == windows` | Only Windows sensors |
| By tag | `"production" in tags` | Sensors with specific tag |
| Combined | `plat == linux and "webserver" in tags` | Multiple criteria |
| By hostname | `hostname == "server1.example.com"` | Specific host |

## Monitoring Task Progress

```
lc_call_tool(
  tool_name="list_reliable_tasks",
  parameters={"oid": "[org-id]"}
)
```

Shows:
- Which sensors have acknowledged/executed
- Which sensors are still pending (offline)
- Task expiration time

## Error Handling

| Issue | Cause | Resolution |
|-------|-------|------------|
| No results | Sensors offline | Wait for TTL period |
| Partial results | Some sensors offline | Check `list_reliable_tasks` for pending |
| D&R not matching | Wrong STDOUT pattern | Verify regex matches actual output |
| Payload failed | Script error | Check RECEIPT events for STDERR |

## Cleanup

### Payload Cleanup (This Skill)

If you uploaded a payload, delete it after the operation:

```
lc_call_tool(
  tool_name="delete_payload",
  parameters={"oid": "[org-id]", "name": "my-payload.sh"}
)
```

### D&R Rule and Task Cleanup (sensor-tasking)

The `sensor-tasking` skill handles cleanup for:
- D&R rules created for response collection
- Reliable tasks

See the **sensor-tasking** skill documentation for cleanup workflows.

## Security Considerations

- **Approval Workflow**: Consider requiring user confirmation before fleet-wide operations
- **Input Validation**: Sanitize parameters to prevent command injection
- **Audit Logging**: All operations logged in LimaCharlie audit trail
- **Least Privilege**: Use sensor selectors to limit scope when possible
- **Payload Review**: Review payload scripts before deployment

## Related Skills

- **sensor-tasking** - **REQUIRED for deployment.** Handles reliable tasking, D&R rules for response collection, and result retrieval. Use this skill for the execution workflow after preparing your payload/command here.
- `sensor-coverage` - Fleet inventory and health before tasking
- `detection-engineering` - Create custom D&R rules for advanced scenarios
- `limacharlie-call` - Low-level API access for payload management
