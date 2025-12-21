
# Delete Reliable Task

Delete or abort pending reliable tasks. Can target specific tasks by ID or delete all tasks matching sensor criteria.

## When to Use

Use this skill when the user needs to:
- Cancel a pending reliable task that's no longer needed
- Abort a fleet-wide operation before all sensors execute it
- Clean up tasks for sensors that have been decommissioned
- Stop a task that was created with incorrect parameters
- Remove all pending tasks for a specific sensor or group

Common scenarios:
- "Cancel the reliable task I just created"
- "Abort all pending tasks for the production servers"
- "Delete the task with ID abc-123"
- "Stop all tasks waiting for sensor xyz"

## What This Skill Does

This skill deletes pending reliable tasks from the ext-reliable-tasking extension. Tasks that have already been executed by sensors cannot be undone, but tasks still waiting for delivery will be cancelled. The skill can target:
- A specific task by task_id
- All tasks for sensors matching a selector expression
- All tasks for a specific sensor by sid

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

**At least one targeting parameter:**
- **task_id**: Specific task ID to delete (from `list_reliable_tasks` or task creation response)
- **selector**: Sensor selector expression to delete tasks for matching sensors
- **sid**: Specific sensor ID to delete all tasks for

**Note**: If no targeting parameters are provided, no tasks will be deleted. If `task_id` is not specified, ALL tasks matching the `selector` or `sid` will be deleted.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. At least one of: task_id, selector, or sid
3. Confirm the user wants to delete the specified tasks

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_reliable_task",
  parameters={
    "oid": "[organization-id]",
    "task_id": "abc12345-6789-0123-4567-890abcdef012"
  }
)
```

**Tool Details:**
- Tool name: `delete_reliable_task`
- Required parameters: oid
- Optional parameters: task_id, selector, sid (at least one recommended)
- Returns count of deleted tasks

### Step 3: Handle the Response

The tool returns a response with deletion details:
```json
{
  "deleted": 5
}
```

**Success:**
- `deleted`: Number of task entries that were deleted

**Common Errors:**
- **403 Forbidden**: ext-reliable-tasking extension not subscribed or insufficient permissions
- **400 Bad Request**: Invalid selector syntax
- **404 Not Found**: Invalid organization ID
- **"no sensors matching criteria"**: The selector/sid didn't match any sensors

### Step 4: Format the Response

Present the result to the user:
- Confirm the number of tasks deleted
- Explain that already-executed tasks cannot be undone
- Note that sensors which already received the task will still have executed it

## Example Usage

### Example 1: Delete Specific Task by ID

User request: "Cancel the reliable task abc12345"

Steps:
1. Call tool to delete the specific task:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_reliable_task",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "task_id": "abc12345-6789-0123-4567-890abcdef012"
  }
)
```

Expected response:
```json
{
  "deleted": 1
}
```

Response to user:
"Deleted reliable task abc12345-6789-0123-4567-890abcdef012. The task has been removed from the queue.

Note: Sensors that already received and executed the task are unaffected - only pending deliveries have been cancelled."

### Example 2: Delete All Tasks for Sensor Selector

User request: "Abort all pending tasks for our Windows production servers"

Steps:
1. Call tool to delete tasks for matching sensors:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_reliable_task",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "plat==windows and production in tags"
  }
)
```

Expected response:
```json
{
  "deleted": 25
}
```

Response to user:
"Deleted 25 pending reliable task entries for Windows production servers. All queued tasks for matching sensors have been cancelled."

### Example 3: Delete All Tasks for Specific Sensor

User request: "Remove all pending tasks for sensor abc-123-def"

Steps:
1. Call tool to delete tasks for the specific sensor:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_reliable_task",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "abc-123-def-456-789"
  }
)
```

Expected response:
```json
{
  "deleted": 3
}
```

Response to user:
"Deleted 3 pending reliable tasks for sensor abc-123-def-456-789."

### Example 4: Safe Cleanup with Verification

User request: "Delete all pending reliable tasks" (broad request)

Steps:
1. First, list current tasks to show what will be deleted:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_reliable_tasks",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

2. Show the user what will be deleted and confirm
3. If confirmed, delete with a broad selector:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_reliable_task",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "*"
  }
)
```

## Additional Notes

- **Extension Required**: The organization must have the `ext-reliable-tasking` extension subscribed
- **Already Executed**: Deleting a task doesn't undo execution - sensors that already ran it are unaffected
- **No Task ID**: Without `task_id`, ALL tasks for matching sensors are deleted - use with caution
- **Selector Syntax**: Uses sensor selector expressions (e.g., `plat==windows`, `*` for all)
- **Verification**: Consider using `list_reliable_tasks` before deletion to show what will be removed
- **Idempotent**: Deleting a non-existent task returns `deleted: 0` without error
- **Audit Trail**: For compliance, consider noting the deleted tasks before removal

## Reference

For the MCP tool, this uses the dedicated `delete_reliable_task` tool via `lc_call_tool`.

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/` (ExtensionRequest with ext-reliable-tasking)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/response/tasking.go` (delete_reliable_task)
For extension documentation, check: `https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Add-Ons/Extensions/LimaCharlie_Extensions/ext-reliable-tasking.md`
