
# Get Saved Query

Retrieve details of a specific saved LCQL query by name.

## When to Use

Use this skill when the user needs to:
- View a specific saved query's details
- See query LCQL before running
- Review query description and tags
- Check query metadata and author
- Inspect query logic
- Copy query for modification

Common scenarios:
- "Show me the 'suspicious-dns' query"
- "What does the threat-hunting query do?"
- "Get details of query 'powershell-encoded'"
- "Who created the malware-detection query?"
- "What's the LCQL for the saved query X?"

## What This Skill Does

This skill retrieves complete details of a saved query including LCQL string, description, tags, and creation metadata.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID
- **query_name**: Name of the saved query

## How to Use

### Step 1: Call the Tool

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_saved_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query_name": "suspicious-dns"
  }
)
```

**Tool Details:**
- Tool name: `get_saved_query`
- Parameters:
  - `oid`: Organization ID (required)
  - `query_name`: Name of the saved query (required)

### Step 2: Handle Response

```json
{
  "data": {
    "query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME ends with '.ru'",
    "description": "Find DNS requests to Russian domains"
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["threat-hunting", "dns"],
    "comment": "Monitor for suspicious domains"
  },
  "sys_mtd": {
    "created_at": 1705000000,
    "created_by": "user@example.com",
    "last_mod": 1705100000,
    "last_author": "admin@example.com",
    "guid": "query-guid-123"
  }
}
```

### Step 3: Format Response

```
Saved Query: suspicious-dns

Description: Find DNS requests to Russian domains

LCQL Query:
-24h | * | DNS_REQUEST | event.DOMAIN_NAME ends with '.ru'

Tags: threat-hunting, dns
Comment: Monitor for suspicious domains
Enabled: Yes

Metadata:
- Created: 2024-01-11 12:00:00 by user@example.com
- Last Modified: 2024-01-12 14:30:00 by admin@example.com
- GUID: query-guid-123
```

## Example Usage

User: "Show me the 'suspicious-dns' query"

Display full query details with formatted LCQL.

## Additional Notes

- Query name is case-sensitive
- 404 error if query doesn't exist
- Use list-saved-queries to find available names
- GUID is unique identifier for sync
- Last modified tracks version history

## Reference

See [CALLING_API.md](../../../CALLING_API.md).

SDK: `../go-limacharlie/limacharlie/hive.go`
MCP: `../lc-mcp-server/internal/tools/hive/saved_queries.go`
