# run_lcql_query

Execute LCQL (LimaCharlie Query Language) queries against historical data.

## CRITICAL: Use generate_lcql_query First

**NEVER write LCQL queries manually.** LCQL uses unique pipe-based syntax validated against org-specific schemas.

**Mandatory workflow:**
1. `generate_lcql_query` - Convert natural language to LCQL
2. `run_lcql_query` - Execute the generated query

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | LCQL query (from generate_lcql_query) |
| limit | integer | No | Max results (default=1000) |
| stream | string | No | "event" (default), "detect", or "audit" |

## Returns

```json
{
  "results": [...],
  "cursor": "next-page-cursor",
  "stats": {
    "events_searched": 50000,
    "results_returned": 100
  }
}
```

Non-empty `cursor` means more results available.

## Example Workflow

**Step 1: Generate query**
```
lc_call_tool(tool_name="generate_lcql_query", parameters={
  "oid": "c7e8f940...",
  "query": "DNS requests to suspicious-domain.com in the last 24 hours"
})
// Returns: {"query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME = 'suspicious-domain.com'"}
```

**Step 2: Execute**
```
lc_call_tool(tool_name="run_lcql_query", parameters={
  "oid": "c7e8f940...",
  "query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME = 'suspicious-domain.com'",
  "limit": 1000
})
```

## Notes

- Queries beyond 30 days may incur costs - confirm with user
- Invalid syntax → use `generate_lcql_query` first
- Related: `generate_lcql_query`, `list_saved_queries`, `run_saved_query`
