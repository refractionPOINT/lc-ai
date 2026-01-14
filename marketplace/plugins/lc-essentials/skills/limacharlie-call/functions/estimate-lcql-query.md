# estimate_lcql_query

Get resource estimates for an LCQL query before running it.

## Use Case

Use this tool to estimate query resource usage before executing potentially expensive queries. Returns only if the query is valid - otherwise fails with an error.

**When to use:**
- Before running queries against large datasets
- Planning resource allocation
- Comparing query efficiency

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | The LCQL query to estimate |

## Returns

```json
{
  "query": "-1h | * | NEW_PROCESS | event/FILE_PATH contains 'cmd.exe'",
  "num_evals": 15000,
  "num_events": 5000,
  "eval_time": 2.5
}
```

| Field | Description |
|-------|-------------|
| `query` | The query that was analyzed |
| `num_evals` | Estimated number of evaluation operations |
| `num_events` | Estimated number of events to process |
| `eval_time` | Estimated evaluation time in seconds |

**Error response (invalid query):**
```json
{
  "error": "no match found, expected: \"|\", [ \\t\\r\\n] or [a-zA-Z0-9_.]"
}
```

## Example

```
lc_call_tool(tool_name="estimate_lcql_query", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "query": "-24h | * | NEW_PROCESS | event/FILE_PATH contains 'powershell'"
})
```

## Notes

- Returns error if query syntax is invalid
- Use `validate_lcql_query` to check syntax first if you want both validation status and estimates
- Use `analyze_lcql_query` to get both validation and estimates in one call
- Related: `validate_lcql_query`, `analyze_lcql_query`, `run_lcql_query`
