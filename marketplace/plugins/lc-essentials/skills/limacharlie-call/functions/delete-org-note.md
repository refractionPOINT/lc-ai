
# Delete Org Note

Permanently deletes an organization note from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Delete a note permanently
- Remove an obsolete or outdated note
- Clean up organization notes
- Remove test or temporary notes

Common scenarios:
- "Delete the incident-contacts note"
- "Remove the old escalation-policy note"
- "Clean up the test-note"
- "Delete note named 'old-procedures'"

## What This Skill Does

This skill permanently deletes an organization note from the LimaCharlie Hive system. It sends a DELETE request to the Hive API using the "org_notes" hive name with the organization ID as the partition and the specific note name. Once deleted, the note and all its data are permanently removed and cannot be recovered.

**Warning:** This operation is permanent and cannot be undone. Consider getting the note first if you might need to restore it later.

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **note_name**: The name of the note to delete (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Note name (string, must be exact match)
3. Consider warning the user that this is permanent
4. Optionally, use get-org-note first to confirm what will be deleted

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_org_note",
  parameters={
    "oid": "[organization-id]",
    "note_name": "[note-name]"
  }
)
```

**API Details:**
- Tool: `delete_org_note`
- Required parameters:
  - `oid`: Organization ID
  - `note_name`: Name of the note to delete

### Step 3: Handle the Response

**Success:**
```json
{
  "success": true,
  "message": "Successfully deleted org note 'note-name'"
}
```

**Common Errors:**
- **400 Bad Request**: Invalid note name format
- **403 Forbidden**: Insufficient permissions - user needs org_notes.del permission
- **404 Not Found**: The note doesn't exist - already deleted or never existed
- **500 Server Error**: Backend issue - advise retry

### Step 4: Format the Response

Present the result to the user:
- Confirm the note was deleted
- Show the note name that was removed
- Warn that this action is permanent
- Suggest using list-org-notes to verify deletion if needed

## Example Usage

### Example 1: Delete a note

User request: "Delete the old-procedures note"

Steps:
1. Get the organization ID from context
2. Optionally warn user about permanent deletion
3. Use note name "old-procedures"
4. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_org_note",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "note_name": "old-procedures"
  }
)
```

Expected response confirms deletion.

Inform user: "Successfully deleted the old-procedures note. This action is permanent and cannot be undone."

## Additional Notes

- **Permanent Action**: Deleted notes cannot be recovered
- **Backup First**: Consider retrieving the note with get-org-note before deleting
- **Immediate Effect**: The note is removed immediately
- **Re-creation**: You can create a new note with the same name after deletion
- **Audit Trail**: The deletion is logged in organization audit logs
- Note names are case-sensitive - use exact name from list-org-notes

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Remove method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/org_notes.go`
