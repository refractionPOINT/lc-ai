
# List Playbooks

Lists all playbooks stored in the Hive for a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- List all playbooks in their organization
- View automated response workflows
- Audit playbook configurations
- Check which playbooks are enabled or disabled
- Review playbook details before modifying them
- Understand automation coverage

Common scenarios:
- "Show me all my playbooks"
- "What automation playbooks do I have?"
- "List playbooks with their workflows"
- "Which playbooks are enabled in my organization?"

## What This Skill Does

This skill retrieves all playbook records from the LimaCharlie Hive system. It calls the Hive API using the "playbook" hive name with the organization ID as the partition to list all playbooks. Each playbook includes its workflow definition (steps, conditions, actions), enabled status, tags, comments, and system metadata (creation time, last modification, author, etc.).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No other parameters are required.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="list_playbooks",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**API Details:**
- Tool: `list_playbooks`
- Required parameters:
  - `oid`: Organization ID

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "playbook-name-1": {
    "data": {
      "steps": [
        {
          "action": "isolate_sensor",
          "condition": "severity == 'critical'"
        }
      ],
      "trigger": "detection",
      "description": "Auto-isolate on critical detections"
    },
    "sys_mtd": {
      "etag": "...",
      "created_by": "user@example.com",
      "created_at": 1234567890,
      "last_author": "user@example.com",
      "last_mod": 1234567899,
      "guid": "..."
    },
    "usr_mtd": {
      "enabled": true,
      "expiry": 0,
      "tags": ["incident-response", "critical"],
      "comment": "Critical detection response playbook"
    }
  },
  "playbook-name-2": {
    // ... another playbook
  }
}
```

**Success:**
- The response body is an object where each key is a playbook name
- Each value contains `data` (workflow definition), `sys_mtd` (system metadata), and `usr_mtd` (user metadata)
- Present the list of playbooks with their enabled status and key details
- Count the total number of playbooks

**Common Errors:**
- **403 Forbidden**: Insufficient permissions - user needs platform_admin or similar role to access Hive
- **404 Not Found**: The hive or partition doesn't exist (unusual, should always exist)
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show a summary count of how many playbooks exist
- List each playbook name with its enabled status
- Highlight key workflow details (triggers, actions)
- Note any playbooks with tags or comments
- Show creation and last modification timestamps for audit purposes
- Explain what each playbook does in simple terms

## Example Usage

### Example 1: List all playbooks

User request: "Show me all my automation playbooks"

Steps:
1. Get the organization ID from context
2. Call the Hive API to list playbooks
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_playbooks",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "critical-isolation": {
    "data": {
      "steps": [
        {"action": "isolate_sensor"},
        {"action": "create_case"}
      ],
      "trigger": "detection",
      "filter": "cat == 'CRITICAL'"
    },
    "sys_mtd": {
      "created_at": 1700000000,
      "last_mod": 1700001000
    },
    "usr_mtd": {
      "enabled": true,
      "tags": ["incident-response"],
      "comment": "Auto-isolate critical threats"
    }
  },
  "suspicious-file-scan": {
    "data": {
      "steps": [
        {"action": "yara_scan"},
        {"action": "collect_file"}
      ]
    },
    "usr_mtd": {
      "enabled": false
    }
  }
}
```

Format the output showing:
- Total: 2 playbooks
- critical-isolation: Enabled - Auto-isolates sensors on critical detections
- suspicious-file-scan: Disabled - Scans and collects suspicious files

### Example 2: Check which playbooks are enabled

User request: "Which of my playbooks are currently enabled?"

Steps:
1. Get organization ID
2. List all playbooks
3. Filter and present only those with `usr_mtd.enabled = true`

The same API call is used, but the response is filtered to show only enabled playbooks.

## Additional Notes

- **Playbooks vs D&R Rules**: Playbooks are more complex automated workflows, while D&R rules are simpler detect-and-respond logic
- Playbooks can have multiple steps and conditional logic
- The `enabled` field in `usr_mtd` controls whether the playbook is active
- Tags can be used for filtering and organizing playbooks
- The `data` field structure includes:
  - `steps`: Array of actions to execute
  - `trigger`: What triggers the playbook (detection, schedule, etc.)
  - `filter`: Conditions for when to run
  - `description`: Human-readable explanation
- System metadata provides audit trail information
- Empty result (no playbooks) is valid and means no playbooks have been created yet
- Use the `get_playbook` skill to retrieve a specific playbook's full definition
- Playbooks are powerful automation tools - ensure enabled playbooks are tested and validated
- Some playbooks may have sensitive actions (isolate, delete files, etc.)

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (List method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/playbooks.go`
