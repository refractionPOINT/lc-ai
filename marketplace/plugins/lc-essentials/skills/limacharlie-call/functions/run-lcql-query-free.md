# run_lcql_query_free

Execute LCQL (LimaCharlie Query Language) queries against historical data, limited to the free tier (past 30 days).

## ✅ PREFERRED: Use This Tool by Default

**This is the recommended tool for most LCQL queries - no cost!**

**Use this tool when:**
- User doesn't specify a timeframe → automatically queries past 30 days
- User requests recent data ("last 24 hours", "past week", "this month")
- Timeframe is vague or unspecified ("recent activity", "lately")
- Any query within the past 30 days

**Only use `run_lcql_query` when user explicitly requests data older than 30 days** (and after showing cost estimate).

## CRITICAL: Use generate_lcql_query First

**NEVER write LCQL queries manually.** LCQL uses unique pipe-based syntax validated against org-specific schemas.

**Mandatory workflow:**
1. `generate_lcql_query` - Convert natural language to LCQL
2. `run_lcql_query_free` - Execute the generated query (free tier)

## Free Tier Limitations

This tool is limited to querying data from the **past 30 days only**:

- **Relative timeframes**: Must be ≤ 720 hours (30 days). Examples: `-24h`, `-168h`, `-720h`, `-1h30m`, `-90s`
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

**Note:** LCQL relative timeframes support Go duration format: hours (`h`), minutes (`m`), seconds (`s`), milliseconds (`ms`), and mixed formats like `-1h30m` or `-2h30m15s`. Days (`d`) are not supported - use hours instead (e.g., `-720h` for 30 days).

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
| "timeframe exceeds free tier limit of 30 days" | Relative timeframe > 720h | Use ≤ 720h or use `run_lcql_query` (with cost estimate) |
| "date range span exceeds free tier limit of 30 days" | Absolute date range > 30 days | Narrow the date range or use `run_lcql_query` (with cost estimate) |
| "start date is more than 30 days ago" | Absolute start date too old | Use dates within past 30 days or use `run_lcql_query` (with cost estimate) |

## Notes

- **Cost-free**: This tool queries free tier data (past 30 days) at no cost
- **Default choice**: Use this for all queries unless user explicitly needs older data
- **Auto-timeframe**: If no timeframe provided, automatically uses `-720h` (full 30-day window)
- **Automatic validation**: Query is validated before execution - invalid queries fail fast with syntax error
- For data older than 30 days: Use `estimate_lcql_query` first, show cost to user, then use `run_lcql_query` after confirmation
- Related: `run_lcql_query`, `generate_lcql_query`, `validate_lcql_query`, `analyze_lcql_query`, `estimate_lcql_query`
