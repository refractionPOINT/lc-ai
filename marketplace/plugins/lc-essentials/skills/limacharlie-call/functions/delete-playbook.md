
# Delete Playbook

Permanently deletes an automation playbook from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Delete a playbook permanently
- Remove an obsolete or unused automation workflow
- Clean up playbooks
- Decommission automated response logic
- Fix issues by removing and recreating a playbook

Common scenarios:
- "Delete the critical-isolation playbook"
- "Remove the incident-response playbook"
- "Clean up the old threat-hunting workflow"
- "Delete playbook named 'test-automation'"

## What This Skill Does

This skill permanently deletes a playbook from the LimaCharlie Hive system. It sends a DELETE request to the Hive API using the "playbook" hive name with the "global" partition and the specific playbook name. Once deleted, the playbook workflow and all its data are permanently removed and cannot be recovered.

**Warning:** This operation is permanent and cannot be undone. The playbook will immediately stop executing. Consider getting the playbook first if you might need to restore it later.

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **playbook_name**: The name of the playbook to delete (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Playbook name (string, must be exact match)
3. Consider warning the user that this is permanent
4. Optionally, use get-playbook first to confirm what will be deleted

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_playbook",
  parameters={
    "oid": "[organization-id]",
    "playbook_name": "[playbook-name]"
  }
)
```

**API Details:**
- Tool: `delete_playbook`
- Required parameters:
  - `oid`: Organization ID
  - `playbook_name`: Name of the playbook to delete

### Step 3: Handle the Response

The API returns:
```json
{}
```

**Success:**
- Playbook has been permanently deleted
- Inform the user that the deletion was successful
- Note that this action cannot be undone

**Common Errors:**
- **400 Bad Request**: Invalid playbook name format
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: The playbook doesn't exist - already deleted or never existed
- **500 Server Error**: Backend issue - advise retry

### Step 4: Format the Response

Present the result to the user:
- Confirm the playbook was deleted
- Show the playbook name that was removed
- Warn that this action is permanent
- Note that the playbook will no longer execute
- Suggest using list-playbooks to verify deletion if needed

## Example Usage

### Example 1: Delete a playbook

User request: "Delete the critical-isolation playbook"

Steps:
1. Get the organization ID from context
2. Optionally warn user about permanent deletion
3. Use playbook name "critical-isolation"
4. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_playbook",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "playbook_name": "critical-isolation"
  }
)
```

Expected response confirms deletion.

Inform user: "Successfully deleted the critical-isolation playbook. This action is permanent and cannot be undone. The playbook will no longer execute."

## Additional Notes

- **Permanent Action**: Deleted playbooks cannot be recovered
- **Backup First**: Consider retrieving the playbook with get-playbook before deleting
- **Immediate Effect**: The playbook stops executing immediately
- **Re-creation**: You can create a new playbook with the same name after deletion
- **Audit Trail**: The deletion is logged in organization audit logs
- **Alternative**: To temporarily disable, use set-playbook with `enabled: false` instead

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Remove method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/playbooks.go`
