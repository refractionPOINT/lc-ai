# run_lcql_query_free

Execute LCQL (LimaCharlie Query Language) queries against historical data, limited to the free tier (past 30 days).

## CRITICAL: Use generate_lcql_query First

**NEVER write LCQL queries manually.** LCQL uses unique pipe-based syntax validated against org-specific schemas.

**Mandatory workflow:**
1. `generate_lcql_query` - Convert natural language to LCQL
2. `run_lcql_query_free` - Execute the generated query (free tier)

## Free Tier Limitations

This tool is limited to querying data from the **past 30 days only**:

- **Relative timeframes**: Must be ≤ 720 hours (30 days). Examples: `-24h`, `-168h`, `-720h`
- **Absolute date ranges**: The date range span must be ≤ 30 days AND the start date must be within the past 30 days from now
- **No timeframe**: If no timeframe is specified, `-720h` (30 days) is automatically prepended

For queries beyond 30 days, use `run_lcql_query` instead (may incur costs).

## Supported Timeframe Formats

### Relative Timeframes
```
-24h | * | DNS_REQUEST | event.DOMAIN_NAME = 'example.com'
-720h | plat == windows | * | event/* contains 'psexec'
```

### Absolute Date Ranges
```
2025-01-01 to 2025-01-15 | * | * | event.FILE_PATH contains 'malware'
2025-01-10 to 2025-01-10 | * | NEW_PROCESS | *
```

**Note:** LCQL relative timeframes only support hours (`h`) and minutes (`m`), not days (`d`).

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | LCQL query (from generate_lcql_query) |
| limit | integer | No | Max results (default=unlimited) |
| stream | string | No | "event" (default), "detect", or "audit" |

## Returns

```json
{
  "results": [...],
  "has_more": true
}
```

`has_more: true` indicates more results available beyond the limit.

## Example Workflow

**Step 1: Generate query**
```
lc_call_tool(tool_name="generate_lcql_query", parameters={
  "oid": "c7e8f940...",
  "query": "DNS requests to suspicious-domain.com in the last 24 hours"
})
// Returns: {"query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME = 'suspicious-domain.com'"}
```

**Step 2: Execute (free tier)**
```
lc_call_tool(tool_name="run_lcql_query_free", parameters={
  "oid": "c7e8f940...",
  "query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME = 'suspicious-domain.com'",
  "limit": 1000
})
```

**Alternative: Using absolute date range**
```
lc_call_tool(tool_name="run_lcql_query_free", parameters={
  "oid": "c7e8f940...",
  "query": "2025-01-01 to 2025-01-15 | * | NEW_PROCESS | event.FILE_PATH contains 'suspicious'",
  "limit": 500
})
```

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "timeframe exceeds free tier limit of 30 days" | Relative timeframe > 720h | Use ≤ 720h or use `run_lcql_query` |
| "date range span exceeds free tier limit of 30 days" | Absolute date range > 30 days | Narrow the date range or use `run_lcql_query` |
| "start date is more than 30 days ago" | Absolute start date too old | Use dates within past 30 days or use `run_lcql_query` |

## Notes

- **Automatic validation**: Query is validated before execution - invalid queries fail fast with syntax error
- **Cost-free**: This tool queries only free tier data (past 30 days)
- **Auto-timeframe**: If no timeframe provided, automatically uses `-720h` (full 30-day window)
- Use `validate_lcql_query` or `analyze_lcql_query` for pre-flight validation and cost estimation
- Related: `run_lcql_query`, `generate_lcql_query`, `validate_lcql_query`, `analyze_lcql_query`, `estimate_lcql_query`
