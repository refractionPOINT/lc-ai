
# Get Playbook

Retrieves a specific playbook by name from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Get detailed workflow for a specific playbook
- View playbook steps and conditions before modifying them
- Check if a playbook exists
- Inspect playbook metadata (creation date, last author, etc.)
- Review playbook logic as part of troubleshooting
- Understand what a playbook does

Common scenarios:
- "Show me the critical-isolation playbook"
- "What are the steps in my incident-response playbook?"
- "Get the playbook named 'auto-remediation'"
- "Is the threat-hunting playbook configured?"

## What This Skill Does

This skill retrieves a single playbook record from the LimaCharlie Hive system by its name. It calls the Hive API using the "playbook" hive name with the organization ID as the partition and the specific playbook name as the key. The response includes the complete workflow definition (steps, triggers, conditions, actions), user metadata (enabled, tags, comments), and system metadata (audit trail).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **playbook_name**: The name of the playbook to retrieve (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Playbook name (string, must be exact match)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_playbook",
  parameters={
    "oid": "[organization-id]",
    "playbook_name": "[playbook-name]"
  }
)
```

**API Details:**
- Tool: `get_playbook`
- Required parameters:
  - `oid`: Organization ID
  - `playbook_name`: Name of the playbook to retrieve

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "data": {
    "steps": [
      {
        "action": "isolate_sensor",
        "params": {"network": true}
      },
      {
        "action": "create_case",
        "params": {"priority": "high"}
      }
    ],
    "trigger": "detection",
    "filter": "cat == 'CRITICAL' and routing.hostname contains 'prod'",
    "description": "Auto-isolate production systems on critical detections"
  },
  "sys_mtd": {
    "etag": "abc123...",
    "created_by": "user@example.com",
    "created_at": 1234567890,
    "last_author": "admin@example.com",
    "last_mod": 1234567899,
    "guid": "unique-id-123"
  },
  "usr_mtd": {
    "enabled": true,
    "expiry": 0,
    "tags": ["incident-response", "production"],
    "comment": "Critical threat auto-isolation"
  }
}
```

**Success:**
- The `data` field contains the complete playbook workflow definition
- The `usr_mtd` field shows user-controlled metadata
- The `sys_mtd` field shows system metadata including audit trail
- Present the playbook details to the user in a readable format

**Common Errors:**
- **400 Bad Request**: Invalid playbook name format
- **403 Forbidden**: Insufficient permissions - user needs platform_admin or similar role
- **404 Not Found**: The playbook doesn't exist - inform user and suggest creating it
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show the playbook name and enabled status prominently
- Explain the trigger and filter conditions
- List the steps/actions in order
- Include description if present
- Display relevant metadata like creation date and last modification
- Note any tags or comments
- Explain what the playbook does in simple terms

## Example Usage

### Example 1: Get a specific playbook

User request: "Show me the critical-isolation playbook"

Steps:
1. Get the organization ID from context
2. Use playbook name "critical-isolation"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_playbook",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "playbook_name": "critical-isolation"
  }
)
```

Expected response contains the workflow definition showing it auto-isolates sensors on critical detections.

Format the output explaining:
- Playbook: critical-isolation (Enabled)
- Trigger: On detection events
- Filter: Only critical severity
- Steps:
  1. Isolate the sensor from network
  2. Create incident case
- Last Modified: [date] by admin@example.com

### Example 2: Check if playbook exists

User request: "Does the threat-hunting playbook exist?"

Steps:
1. Attempt to get the playbook
2. If 404 error: inform user the playbook doesn't exist
3. If 200 success: confirm it exists and show summary

## Additional Notes

- Playbook names are case-sensitive - use exact name from list-playbooks
- The `data` field structure includes:
  - `steps`: Array of actions to execute in order
  - `trigger`: What event triggers the playbook (detection, schedule, manual, etc.)
  - `filter`: Conditional logic for when to execute
  - `description`: Human-readable explanation
  - Additional fields vary by playbook complexity
- The `enabled` field controls whether the playbook is active
- Use `list_playbooks` first if you don't know the exact playbook name
- Playbooks can contain sensitive automation logic - handle carefully
- Some playbooks perform destructive actions (isolate, delete, modify)
- Review playbook logic carefully before enabling in production

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Get method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/playbooks.go`
