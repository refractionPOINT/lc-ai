
# Save LCQL Query

Create or update a saved LCQL query for future use.

## When to Use

Use this skill when the user needs to:
- Save a frequently used query
- Create reusable hunting queries
- Build organization query library
- Standardize investigation procedures
- Share queries with team
- Document validated search logic

Common scenarios:
- "Save this query as 'suspicious-dns'"
- "Create a saved query for PowerShell hunting"
- "Store this query with description"
- "Save this search for later use"
- "Create a query named 'compliance-check'"

## What This Skill Does

This skill saves an LCQL query string to hive storage with a name, optional description, and tags for organization.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID
- **query_name**: Name for the saved query
- **lcql_query**: The LCQL query string to save

Optional:
- **description**: Description of what the query does

## How to Use

### Step 1: Prepare Query Data

Format query data:
```json
{
  "query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME ends with '.ru'",
  "description": "Find DNS requests to Russian domains"
}
```

### Step 2: Call the Tool

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="set_saved_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query_name": "suspicious-dns",
    "lcql_query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME ends with '.ru'",
    "description": "Find DNS requests to Russian domains"
  }
)
```

**Tool Details:**
- Tool name: `set_saved_query`
- Parameters:
  - `oid`: Organization ID (required)
  - `query_name`: Name for the saved query (required)
  - `lcql_query`: The LCQL query string (required)
  - `description`: Optional description

### Step 3: Handle Response

```json
{
  "success": true,
  "guid": "query-guid-123",
  "message": "Successfully saved query 'suspicious-dns'"
}
```

### Step 4: Format Response

```
Query Saved Successfully!

Name: suspicious-dns
Description: Find DNS requests to Russian domains

LCQL:
-24h | * | DNS_REQUEST | event.DOMAIN_NAME ends with '.ru'

You can now run this query using:
- run-saved-query with name "suspicious-dns"
```

## Example Usage

### Example 1: Save threat hunting query

User: "Save this query as 'powershell-encoded'"

```
LCQL: -168h | * | NEW_PROCESS | event.COMMAND_LINE contains 'encodedCommand'
Description: Detect encoded PowerShell commands
```

Save with name and description.

### Example 2: Update existing query

User: "Update the suspicious-dns query to include .cn domains"

Same tool call with updated LCQL - overwrites existing query.

## Additional Notes

- Query names must be unique within organization
- Overwrites existing query with same name
- LCQL syntax is not validated on save
- Test query with run-lcql-query before saving
- Description should explain query purpose
- Consider naming conventions for team queries
- Can include timeframes in saved queries
- Query modifications are tracked via metadata

## Reference

See [CALLING_API.md](../../../CALLING_API.md).

SDK: `../go-limacharlie/limacharlie/hive.go`
MCP: `../lc-mcp-server/internal/tools/hive/saved_queries.go`
