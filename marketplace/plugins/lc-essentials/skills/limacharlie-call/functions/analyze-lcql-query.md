# analyze_lcql_query

Analyze an LCQL query for both validity and resource estimates.

## Use Case

Use this tool for complete query analysis - validates syntax AND returns resource estimates in a single call. Best for:
- Full query review before execution
- Getting all query metadata at once
- Workflow where you need both validation status and estimates

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | The LCQL query to analyze |

## Returns

**Valid query:**
```json
{
  "valid": true,
  "query": "-1h | * | NEW_PROCESS | event/FILE_PATH contains 'cmd.exe'",
  "num_evals": 15000,
  "num_events": 5000,
  "eval_time": 2.5
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
  "eval_time": 0
}
```

| Field | Description |
|-------|-------------|
| `valid` | Whether the query syntax is valid |
| `query` | The query that was analyzed |
| `error` | Error message if query is invalid (empty if valid) |
| `num_evals` | Estimated number of evaluation operations |
| `num_events` | Estimated number of events to process |
| `eval_time` | Estimated evaluation time in seconds |

## Example

```
lc_call_tool(tool_name="analyze_lcql_query", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "query": "-24h | plat == windows | NEW_PROCESS | event/COMMAND_LINE contains 'whoami'"
})
```

## Notes

- Combines functionality of `validate_lcql_query` and `estimate_lcql_query`
- Always returns estimates (may be zero for invalid queries)
- Use this when you need complete query metadata
- Related: `validate_lcql_query`, `estimate_lcql_query`, `run_lcql_query`, `generate_lcql_query`
