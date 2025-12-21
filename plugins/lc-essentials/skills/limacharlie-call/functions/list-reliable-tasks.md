
# List Reliable Tasks

List all pending reliable tasks in the organization to monitor execution status and track queued commands.

## When to Use

Use this skill when the user needs to:
- View all currently active reliable tasks
- Monitor execution status of fleet-wide operations
- Verify a reliable task was created successfully
- Check which tasks are pending for offline sensors
- Audit queued commands before execution
- Track task delivery and acknowledgment
- Troubleshoot task execution issues

Common scenarios:
- "Show me all pending reliable tasks"
- "What tasks are waiting for sensors to come online?"
- "List the active forensic collection tasks"
- "Check if my reliable task is still active"

## What This Skill Does

This skill retrieves all currently active reliable tasks in the organization. It returns information about each task including the task ID, command, creation time, retention period, sensor selector, and execution status. This is useful for monitoring fleet-wide operations, verifying task creation, and understanding what commands are queued for sensor execution.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No other parameters are needed - this returns all pending tasks.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__limacharlie__lc_call_tool(
  tool_name="list_reliable_tasks",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**Tool Details:**
- Tool name: `list_reliable_tasks`
- Required parameters: oid
- No query parameters needed
- Returns all pending reliable tasks

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "tasks": [
    {
      "task_id": "abc12345-6789-0123-4567-890abcdef012",
      "command": "mem_map --pid 4",
      "sensor_selector": "platform=windows and tag=production",
      "investigation_id": "incident-2024-001",
      "retention": 172800,
      "created": 1234567890,
      "expires": 1234740690,
      "acknowledged_by": ["sid1", "sid2"],
      "pending_for": ["sid3", "sid4"]
    },
    {
      "task_id": "def45678-90ab-cdef-0123-456789abcdef",
      "command": "deny_tree -p malware.exe",
      "sensor_selector": "tag=compromised",
      "retention": 86400,
      "created": 1234567890,
      "expires": 1234654290
    }
  ]
}
```

**Success:**
- Response contains an array of task objects
- Each task includes:
  - `task_id`: Unique identifier for the task
  - `command`: The command to be executed
  - `sensor_selector`: Targeting criteria (if specified)
  - `investigation_id`: Associated investigation (if specified)
  - `retention`: How long the task remains active (seconds)
  - `created`: Unix timestamp when task was created
  - `expires`: Unix timestamp when task will expire
  - `acknowledged_by`: List of sensor IDs that executed the task
  - `pending_for`: List of sensor IDs that haven't executed it yet
- An empty array means no tasks are currently pending

**Common Errors:**
- **403 Forbidden**: Insufficient permissions - requires tasking read permissions
- **404 Not Found**: Invalid endpoint or organization - verify OID
- **500 Server Error**: Rare server issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Display the total number of pending tasks
- For each task, show:
  - Task ID for reference
  - Command being executed
  - Target sensors (selector)
  - Creation and expiration times
  - Execution status (how many sensors acknowledged)
  - Associated investigation if present
- Highlight tasks nearing expiration
- Suggest actions if tasks are stuck or failing
- Group by investigation_id if multiple tasks exist

## Example Usage

### Example 1: Monitor Fleet-Wide Forensic Collection

User request: "Show me the status of the memory collection tasks"

Steps:
1. Call tool to list reliable tasks:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_reliable_tasks",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "tasks": [
    {
      "task_id": "abc12345-6789-0123-4567-890abcdef012",
      "command": "mem_map --pid 4",
      "sensor_selector": "platform=windows and tag=production",
      "investigation_id": "incident-2024-001",
      "retention": 172800,
      "created": 1234567890,
      "expires": 1234740690,
      "acknowledged_by": ["sid1", "sid2", "sid3"],
      "pending_for": ["sid4", "sid5"]
    }
  ]
}
```

Response to user:
"Found 1 active reliable task:

**Task: abc12345-6789-0123-4567-890abcdef012**
- Command: mem_map --pid 4
- Target: Windows production servers
- Investigation: incident-2024-001
- Status: 3 sensors completed, 2 sensors pending
- Created: [formatted date]
- Expires in: 47 hours

The memory collection is progressing. 3 sensors have acknowledged and executed the task, while 2 sensors (sid4, sid5) are still pending - they may be offline or haven't connected yet."

### Example 2: Check All Pending Tasks

User request: "What reliable tasks are currently active?"

Steps:
1. Call tool to list all tasks:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_reliable_tasks",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "tasks": []
}
```

Response to user:
"There are no active reliable tasks in the organization. All previously created tasks have either been executed or expired."

## Additional Notes

- This returns only active/pending tasks - completed and expired tasks are not shown
- Tasks remain in the list until all targeted sensors acknowledge or retention expires
- Use task_id to reference specific tasks in other operations
- The `acknowledged_by` array shows which sensors successfully executed the task
- The `pending_for` array shows sensors that haven't executed it yet
- Pending sensors may be offline, not matching selector, or experiencing issues
- Tasks automatically expire after their retention period
- Check this regularly during fleet-wide operations to monitor progress
- Empty task list means all operations completed or no tasks were created
- This is read-only - it doesn't modify task state
- Use this to verify reliable tasks created with the `reliable_tasking` skill
- Investigation IDs help group related tasks together
- Consider the time remaining before expiration when monitoring tasks
- Tasks near expiration may need retention extension (requires new task)
- This shows organization-wide tasks - not sensor-specific
- Useful for auditing and compliance to see what commands are queued

## Reference

For the MCP tool, this uses the dedicated `list_reliable_tasks` tool via `lc_call_tool`.

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/` (GenericGETRequest with reliable_tasking endpoint)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/response/tasking.go` (list_reliable_tasks)
