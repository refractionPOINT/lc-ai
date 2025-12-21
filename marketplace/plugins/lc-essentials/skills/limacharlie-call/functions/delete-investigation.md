
# Delete Investigation

Delete an investigation from LimaCharlie's Investigation Hive.

## When to Use

Use this skill when the user needs to:
- Remove an old or completed investigation
- Delete a test investigation
- Clean up duplicate investigations
- Remove an investigation created in error

Common scenarios:
- "Delete the investigation named 'test-investigation'"
- "Remove the old incident investigation"
- "Clean up the duplicate investigation"
- "Delete investigation 'incident-2024-001'"

## What This Skill Does

This skill permanently deletes an investigation record from LimaCharlie's Investigation Hive. This action cannot be undone - the investigation and all its data (events, detections, entities, notes) will be permanently removed.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (required)
- **investigation_name**: Name of the investigation to delete (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Exact investigation name to delete
3. **Confirm with user** before deleting - this action is irreversible

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="delete_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "test-investigation"
  }
)
```

**Tool Details:**
- Tool name: `delete_investigation`
- Parameters:
  - `oid`: Organization ID (required)
  - `investigation_name`: Name of the investigation to delete (required)

### Step 3: Handle the Response

The tool returns:
```json
{
  "success": true,
  "message": "Successfully deleted investigation 'test-investigation'"
}
```

**Success:**
- Investigation is permanently deleted
- Cannot be recovered after deletion

**Common Errors:**
- **404 Not Found**: Investigation with the specified name does not exist
- **403 Forbidden**: Insufficient permissions
- **400 Bad Request**: Invalid parameters

### Step 4: Format the Response

Present the result to the user:
- Confirm successful deletion
- Remind that this action was permanent

**Example output:**
```
Successfully deleted investigation 'test-investigation'.

Note: This action is permanent. The investigation and all associated data have been removed.
```

## Example Usage

### Example 1: Delete test investigation

User request: "Delete the test investigation I created"

Steps:
1. **Confirm with user**: "Are you sure you want to delete investigation 'test-investigation'? This cannot be undone."
2. After confirmation, call the API:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="delete_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "test-investigation"
  }
)
```

### Example 2: Clean up old investigation

User request: "Remove the closed investigation from last month"

Steps:
1. Use `list_investigations` to find the exact name
2. Confirm with user before deletion
3. Delete the investigation

## Additional Notes

- **Deletion is permanent** - there is no undo or recovery
- Always confirm with user before deleting
- Consider exporting investigation data before deletion if needed for records
- Investigation names are case-sensitive
- Use `list_investigations` to verify the exact name before deleting
- The underlying events and detections in LimaCharlie are NOT deleted - only the investigation record
- Related skills: `list_investigations` to find investigations, `get_investigation` to review before deleting

## Related Functions

- `list_investigations` - List all investigations in the organization
- `get_investigation` - Get a specific investigation by name
- `set_investigation` - Create or update an investigation
- `expand_investigation` - Hydrate investigation with full event/detection data

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

- **Config Hive Documentation**: [Config Hive: Investigation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Platform_Management/Config_Hive/config-hive-investigation.md)
- **MCP Implementation**: `../lc-mcp-server/internal/tools/hive/investigations.go`
