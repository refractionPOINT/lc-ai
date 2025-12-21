
# Delete Saved Query

Delete a saved LCQL query from the organization's hive storage.

## When to Use

Use this skill when the user needs to:
- Remove obsolete queries
- Clean up query library
- Fix naming mistakes
- Delete duplicate queries
- Manage query inventory
- Remove unused saved searches

Common scenarios:
- "Delete the old-query saved query"
- "Remove the test-query query"
- "Clean up obsolete saved queries"
- "Delete query 'duplicate-search'"
- "Remove the broken query"

## What This Skill Does

This skill permanently deletes a saved query from hive storage by name.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID
- **query_name**: Name of the saved query to delete

## How to Use

### Step 1: Confirm Query Exists

Optionally, verify query exists first:
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_saved_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query_name": "old-query"
  }
)
```

### Step 2: Delete Query

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="delete_saved_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query_name": "old-query"
  }
)
```

**Tool Details:**
- Tool name: `delete_saved_query`
- Parameters:
  - `oid`: Organization ID (required)
  - `query_name`: Name of the saved query to delete (required)

### Step 3: Handle Response

```json
{
  "success": true,
  "message": "Successfully deleted saved query 'old-query'"
}
```

**Success:**
- Query is permanently deleted
- Cannot be recovered
- Returns confirmation message

**Common Errors:**
- **404 Not Found**: Query with that name doesn't exist
- **403 Forbidden**: Insufficient permissions to delete queries

### Step 4: Format Response

```
Query Deleted Successfully!

Deleted: old-query

The query has been permanently removed from your saved queries.
```

## Example Usage

### Example 1: Delete obsolete query

User: "Delete the old-query saved query"

Steps:
1. Confirm with user if deletion is intentional
2. Call the delete tool
3. Confirm deletion

### Example 2: Clean up test queries

User: "Remove all test queries"

Steps:
1. List saved queries
2. Filter for test queries
3. Delete each one (confirm first)

## Additional Notes

- Deletion is permanent and cannot be undone
- Query name is case-sensitive
- No confirmation prompt in API (implement in UI/skill logic)
- Consider backing up query LCQL before deletion
- Use list-saved-queries to verify deletion
- Deletion only affects saved queries, not historical data
- Does not affect query execution history
- Team members will immediately lose access to deleted query

## Reference

See [CALLING_API.md](../../../CALLING_API.md).

SDK: `../go-limacharlie/limacharlie/hive.go`
MCP: `../lc-mcp-server/internal/tools/hive/saved_queries.go`
