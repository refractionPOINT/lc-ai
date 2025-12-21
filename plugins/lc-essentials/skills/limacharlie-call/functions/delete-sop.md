
# Delete SOP

Permanently deletes a Standard Operating Procedure from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Delete an SOP permanently
- Remove an obsolete or outdated procedure
- Clean up SOPs
- Remove test or temporary procedures

Common scenarios:
- "Delete the old-malware-response SOP"
- "Remove the deprecated phishing procedure"
- "Clean up the test-sop"
- "Delete SOP named 'draft-procedure'"

## What This Skill Does

This skill permanently deletes a Standard Operating Procedure from the LimaCharlie Hive system. It sends a DELETE request to the Hive API using the "sop" hive name with the organization ID as the partition and the specific SOP name. Once deleted, the SOP and all its data are permanently removed and cannot be recovered.

**Warning:** This operation is permanent and cannot be undone. Consider getting the SOP first if you might need to restore it later.

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **sop_name**: The name of the SOP to delete (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. SOP name (string, must be exact match)
3. Consider warning the user that this is permanent
4. Optionally, use get-sop first to confirm what will be deleted

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_sop",
  parameters={
    "oid": "[organization-id]",
    "sop_name": "[sop-name]"
  }
)
```

**API Details:**
- Tool: `delete_sop`
- Required parameters:
  - `oid`: Organization ID
  - `sop_name`: Name of the SOP to delete

### Step 3: Handle the Response

**Success:**
```json
{
  "success": true,
  "message": "Successfully deleted SOP 'sop-name'"
}
```

**Common Errors:**
- **400 Bad Request**: Invalid SOP name format
- **403 Forbidden**: Insufficient permissions - user needs sop.del permission
- **404 Not Found**: The SOP doesn't exist - already deleted or never existed
- **500 Server Error**: Backend issue - advise retry

### Step 4: Format the Response

Present the result to the user:
- Confirm the SOP was deleted
- Show the SOP name that was removed
- Warn that this action is permanent
- Suggest using list-sops to verify deletion if needed

## Example Usage

### Example 1: Delete an SOP

User request: "Delete the old-incident-procedure SOP"

Steps:
1. Get the organization ID from context
2. Optionally warn user about permanent deletion
3. Use SOP name "old-incident-procedure"
4. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_sop",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sop_name": "old-incident-procedure"
  }
)
```

Expected response confirms deletion.

Inform user: "Successfully deleted the old-incident-procedure SOP. This action is permanent and cannot be undone."

## Additional Notes

- **Permanent Action**: Deleted SOPs cannot be recovered
- **Backup First**: Consider retrieving the SOP with get-sop before deleting
- **Immediate Effect**: The SOP is removed immediately
- **Re-creation**: You can create a new SOP with the same name after deletion
- **Audit Trail**: The deletion is logged in organization audit logs
- SOP names are case-sensitive - use exact name from list-sops
- Consider archiving important SOPs before deletion:
  1. Use get-sop to retrieve the content
  2. Save the content externally
  3. Then delete the SOP

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Remove method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/sop.go`
