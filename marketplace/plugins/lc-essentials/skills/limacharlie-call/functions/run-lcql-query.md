# run_lcql_query

Execute LCQL (LimaCharlie Query Language) queries against historical data for **any timeframe**.

## ⚠️ COST WARNING: Prefer run_lcql_query_free

**This tool may incur costs for queries beyond 30 days (~$0.01 per 200K events).**

**Use `run_lcql_query_free` instead when:**
- User doesn't specify a timeframe
- User requests recent data (within last 30 days)
- Timeframe is vague ("recent", "lately", "this week/month")

**Only use this tool when user explicitly requests data older than 30 days.**

## CRITICAL: Required Workflow for Older Data

**NEVER write LCQL queries manually.** LCQL uses unique pipe-based syntax validated against org-specific schemas.

**Mandatory workflow for queries >30 days:**
1. `generate_lcql_query` - Convert natural language to LCQL
2. `estimate_lcql_query` - Get cost estimate
3. **Show cost to user and get explicit confirmation**
4. `run_lcql_query` - Execute only after user confirms

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

## Example Workflow (for data >30 days)

**Step 1: Generate query**
```
lc_call_tool(tool_name="generate_lcql_query", parameters={
  "oid": "c7e8f940...",
  "query": "All PowerShell executions in the last 90 days"
})
// Returns: {"query": "-2160h | * | NEW_PROCESS | event.FILE_PATH contains 'powershell'"}
```

**Step 2: Estimate cost**
```
lc_call_tool(tool_name="estimate_lcql_query", parameters={
  "oid": "c7e8f940...",
  "query": "-2160h | * | NEW_PROCESS | event.FILE_PATH contains 'powershell'"
})
// Returns: {"billed_events": 500000, "estimated_cost_usd": 0.025, ...}
```

**Step 3: Confirm with user**
```
"This query will search 90 days of data and may cost approximately $0.03. Do you want to proceed?"
```

**Step 4: Execute (only after user confirms)**
```
lc_call_tool(tool_name="run_lcql_query", parameters={
  "oid": "c7e8f940...",
  "query": "-2160h | * | NEW_PROCESS | event.FILE_PATH contains 'powershell'",
  "limit": 1000
})
```

## Notes

- **Automatic validation**: Query is validated before execution - invalid queries fail fast with syntax error
- **Cost awareness**: Always use `estimate_lcql_query` and confirm with user before executing queries >30 days
- **Prefer free tier**: Use `run_lcql_query_free` for queries within 30 days (no cost)
- Related: `run_lcql_query_free`, `generate_lcql_query`, `estimate_lcql_query`, `validate_lcql_query`, `analyze_lcql_query`
