
# Reliable Tasking

Send persistent tasks to sensors that will be delivered even if the sensors are currently offline. Tasks are queued and automatically delivered when sensors come online.

## When to Use

Use this skill when the user needs to:
- Execute commands on offline sensors when they reconnect
- Send fleet-wide commands that persist until delivery
- Perform forensic collection across multiple sensors
- Execute incident response commands on specific sensor groups
- Queue tasks for sensors that may be intermittently online

Common scenarios:
- "Run os_version on all Windows servers when they come online"
- "Execute memory collection on compromised hosts"
- "Send a command to all sensors with the 'production' tag"
- "Queue a forensic task for an offline laptop"

## What This Skill Does

This skill creates a reliable task that will be delivered to matching sensors. The task is queued in the ext-reliable-tasking extension and automatically sent when sensors come online. Tasks persist for a configurable time-to-live (TTL) period, defaulting to 1 week.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **task**: The command to execute on sensors (required)

**Optional parameters:**
- **selector**: Sensor selector expression to target specific sensors
- **context**: Context identifier reflected in investigation_id of response events
- **ttl**: Time-to-live in seconds (default: 604800 = 1 week)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. A valid task command (e.g., `os_version`, `mem_map --pid 4`, `run --shell-command whoami`)
3. Optional: selector expression to target specific sensors

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__limacharlie__lc_call_tool(
  tool_name="reliable_tasking",
  parameters={
    "oid": "[organization-id]",
    "task": "os_version",
    "selector": "plat==windows",
    "context": "incident-2024-001",
    "ttl": 86400
  }
)
```

**Tool Details:**
- Tool name: `reliable_tasking`
- Required parameters: oid, task
- Optional parameters: selector, context, ttl
- Returns task creation details including task_id

### Step 3: Handle the Response

The tool returns a response with task details:
```json
{
  "task_id": "abc12345-6789-0123-4567-890abcdef012",
  "total_sensors": 50,
  "tasked_sensors": 12,
  "queued_sensors": 38
}
```

**Success:**
- `task_id`: Unique identifier for tracking and managing the task
- `total_sensors`: Total number of sensors matching the selector
- `tasked_sensors`: Number of online sensors that received the task immediately
- `queued_sensors`: Number of offline sensors where the task is queued

**Common Errors:**
- **403 Forbidden**: ext-reliable-tasking extension not subscribed or insufficient permissions
- **400 Bad Request**: Invalid task command or selector syntax
- **404 Not Found**: Invalid organization ID

### Step 4: Format the Response

Present the result to the user:
- Confirm task was created with the task_id
- Show how many sensors received it immediately vs queued
- Explain that queued sensors will receive it when they come online
- Mention the TTL if relevant
- Suggest using `list_reliable_tasks` to monitor progress

## Example Usage

### Example 1: Fleet-Wide OS Version Collection

User request: "Get the OS version from all Windows servers when they come online"

Steps:
1. Call tool to create reliable task:
```
mcp__limacharlie__lc_call_tool(
  tool_name="reliable_tasking",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "task": "os_version",
    "selector": "plat==windows",
    "context": "os-audit-2024"
  }
)
```

Expected response:
```json
{
  "task_id": "abc12345-6789-0123-4567-890abcdef012",
  "total_sensors": 100,
  "tasked_sensors": 75,
  "queued_sensors": 25
}
```

Response to user:
"Created reliable task abc12345-6789-0123-4567-890abcdef012 to collect OS version from Windows sensors.

- 75 online sensors received the command immediately
- 25 offline sensors have the task queued - they'll execute it when they come online
- Task will remain active for 1 week (default TTL)

You can monitor progress with the `list_reliable_tasks` command."

### Example 2: Targeted Memory Collection

User request: "Collect memory maps from the compromised hosts tagged 'incident-response'"

Steps:
1. Call tool to create reliable task:
```
mcp__limacharlie__lc_call_tool(
  tool_name="reliable_tasking",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "task": "mem_map --pid 4",
    "selector": "incident-response in tags",
    "context": "ir-memory-collection",
    "ttl": 172800
  }
)
```

Response to user:
"Created reliable task to collect memory maps from sensors tagged 'incident-response'. The task will remain active for 48 hours (172800 seconds).

Use context 'ir-memory-collection' in D&R rules to capture the responses."

### Example 3: Single Sensor Task

User request: "Queue a command for sensor abc-123 to run when it comes online"

Steps:
1. Call tool to create reliable task:
```
mcp__limacharlie__lc_call_tool(
  tool_name="reliable_tasking",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "task": "run --shell-command 'netstat -an'",
    "selector": "sid=='abc-123-def-456'"
  }
)
```

## Additional Notes

- **Extension Required**: The organization must have the `ext-reliable-tasking` extension subscribed
- **Selector Syntax**: Uses sensor selector expressions (e.g., `plat==windows`, `production in tags`, `sid=='abc'`)
- **Context for D&R**: The `context` parameter appears in the `investigation_id` of response events, enabling D&R rule matching
- **Default TTL**: 604800 seconds (1 week) if not specified
- **Task Commands**: Any valid sensor task command works (os_version, mem_map, run, file_get, etc.)
- **Delivery Guarantee**: Tasks are retried until TTL expires or all sensors acknowledge
- **Monitoring**: Use `list_reliable_tasks` to check task status and delivery progress
- **Cancellation**: Use `delete_reliable_task` to abort pending tasks

## Reference

For the MCP tool, this uses the dedicated `reliable_tasking` tool via `lc_call_tool`.

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/` (ExtensionRequest with ext-reliable-tasking)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/response/tasking.go` (reliable_tasking)
For extension documentation, check: `https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Add-Ons/Extensions/LimaCharlie_Extensions/ext-reliable-tasking.md`
