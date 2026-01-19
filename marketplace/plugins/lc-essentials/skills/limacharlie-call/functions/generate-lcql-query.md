# generate_lcql_query

Generate LCQL queries from natural language descriptions using AI.

## CRITICAL: Use Before run_lcql_query

**ALWAYS call this function FIRST before `run_lcql_query`.** LCQL uses unique pipe-based syntax that must not be written manually.

**Workflow:**
1. `generate_lcql_query` - Convert natural language to LCQL
2. `run_lcql_query` - Execute the generated query

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | Natural language description |

## Returns

```json
{
  "query": "-24h | * | NEW_PROCESS | event.FILE_PATH contains 'powershell'",
  "explanation": "Searches for NEW_PROCESS events where file path contains 'powershell' in the last 24 hours."
}
```

## Example

```
lc_call_tool(tool_name="generate_lcql_query", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "query": "find all PowerShell executions in the last 24 hours"
})
```

## Notes

- Uses AI (Gemini) with LCQL-specific prompts
- **Built-in validation**: Validates each generated query internally before returning
- **Auto-retry**: Retries up to 10 times with feedback injection if validation fails
- **No need to call `validate_lcql_query()`** after this function - returned queries are guaranteed valid
- **Always display the query to the user before running it** - show both query and explanation
- Review explanation to ensure query matches intent
- Related: `run_lcql_query`, `run_lcql_query_free`
