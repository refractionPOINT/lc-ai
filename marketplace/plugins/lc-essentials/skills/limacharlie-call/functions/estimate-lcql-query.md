# estimate_lcql_query

Get resource estimates and billing information for an LCQL query before running it.

## Use Case

Use this tool to estimate query resource usage and cost before executing potentially expensive queries. Returns a consistent response structure with validation status and estimates.

**When to use:**
- Before running queries against large datasets
- Planning resource allocation and budget
- Comparing query efficiency and cost
- Understanding estimated billing impact

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | The LCQL query to estimate |

## Returns

**Valid query:**
```json
{
  "valid": true,
  "query": "-1h | * | NEW_PROCESS | event/FILE_PATH contains 'cmd.exe'",
  "num_evals": 15000,
  "num_events": 5000,
  "eval_time": 2.5,
  "billed_events": 93698021,
  "free_events": 4319347,
  "estimated_cost_usd": 468.49
}
```

**Invalid query:**
```json
{
  "valid": false,
  "query": "-1h | * | limit:10",
  "error": "no match found, expected: \"|\", [ \\t\\r\\n] or [a-zA-Z0-9_.]",
  "num_evals": 0,
  "num_events": 0,
  "eval_time": 0,
  "billed_events": 0,
  "free_events": 0,
  "estimated_cost_usd": 0
}
```

| Field | Description |
|-------|-------------|
| `valid` | Whether the query syntax is valid |
| `query` | The query that was analyzed |
| `error` | Error message if query is invalid (only present if invalid) |
| `num_evals` | Estimated number of evaluation operations |
| `num_events` | Estimated number of events to process |
| `eval_time` | Estimated evaluation time in seconds |
| `billed_events` | Estimated number of events that would be billed |
| `free_events` | Estimated number of events that would be free (not billed) |
| `estimated_cost_usd` | Estimated cost in USD |

## Example

```
lc_call_tool(tool_name="estimate_lcql_query", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "query": "-24h | * | NEW_PROCESS | event/FILE_PATH contains 'powershell'"
})
```

## Notes

- Returns consistent structure with `valid` field for both valid and invalid queries
- Response format is consistent with `validate_lcql_query` and `analyze_lcql_query`
- Invalid queries return zeroed estimates
- Billing is based on the number of events scanned
- Related: `validate_lcql_query`, `analyze_lcql_query`, `run_lcql_query`
