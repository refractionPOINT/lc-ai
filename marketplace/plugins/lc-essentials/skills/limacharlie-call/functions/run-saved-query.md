
# Run Saved Query

Execute a saved LCQL query by name and return the results.

## When to Use

Use this skill when the user needs to:
- Run a pre-built saved query
- Execute validated hunting queries
- Perform repeated investigations
- Use organization-standard queries

Common scenarios:
- "Run the suspicious-dns query"
- "Execute the threat-hunting query"
- "Run saved query 'malware-detection'"

## What This Skill Does

Retrieves a saved query by name from hive storage and executes it, returning the query results.

## When to Create vs Run Queries

**Use this function** for running existing saved queries.

**Use `generate_lcql_query`** to create new queries from natural language:
```
mcp__plugin_lc-essentials_limacharlie__generate_lcql_query(
  oid="[your-oid]",
  query="find suspicious PowerShell executions"
)
```
Then save it with `set_saved_query` for reuse.

## Required Information

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use `list_user_orgs` first.

- **oid**: Organization ID (UUID)
- **query_name**: Name of the saved query to execute

Optional:
- **limit**: Maximum results to return

## How to Use

### Step 1: Retrieve Query

Get the saved query definition:
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_saved_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query_name": "suspicious-dns"
  }
)
```

### Step 2: Execute Query

Execute the LCQL query string:
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="run_lcql_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query": "[lcql-from-saved-query]",
    "limit": 1000,
    "stream": "event"
  }
)
```

### Step 3: Handle Response

**Success:**
```json
{
  "results": [...],
  "cursor": "",
  "stats": {...}
}
```

**Common Errors:**
- **404 Not Found**: Query doesn't exist
- **400 Bad Request**: Invalid LCQL syntax in saved query
- **403 Forbidden**: Insufficient permissions

## Example Usage

User: "Run the suspicious-dns query"

**Step 1: Get query**
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_saved_query",
  parameters={
    "oid": "...",
    "query_name": "suspicious-dns"
  }
)
// Returns: {"data": {"query": "-24h | * | DNS_REQUEST | ..."}}
```

**Step 2: Execute**
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="run_lcql_query",
  parameters={
    "oid": "...",
    "query": "-24h | * | DNS_REQUEST | ...",
    "limit": 1000,
    "stream": "event"
  }
)
```

**Step 3: Present results**
```
Executed Query: suspicious-dns
Results: 12 events found
...
```

## Related Functions

- `generate_lcql_query` - AI-assisted query generation for new queries
- `list_saved_queries` - List available saved queries
- `get_saved_query` - Get query definition without executing
- `set_saved_query` - Save a new query for reuse
- `delete_saved_query` - Remove a saved query
- `run_lcql_query` - Execute ad-hoc LCQL queries

## Reference

For the API implementation, see [CALLING_API.md](../../../CALLING_API.md).

For LCQL syntax, use the `lookup-lc-doc` skill to search LimaCharlie documentation.
