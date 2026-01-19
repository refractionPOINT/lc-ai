# validate_lcql_query

Validate an LCQL query syntax without executing it.

## Use Case

Use this tool to check if an LCQL query is syntactically valid before running it with `run_lcql_query`.

**When to use:**
- Debugging query syntax errors (validation only, no cost estimate needed)

**Prefer `analyze_lcql_query()` instead when:**
- Validating user-provided LCQL queries that will be executed
- Validating saved queries retrieved via `get_saved_query()`
- Validating queries from external sources (documentation, scripts, etc.)
- Pre-flight check before expensive queries (beyond 30 days)
- `analyze_lcql_query()` combines validation + cost estimate in one call

**When NOT to use:**
- After `generate_lcql_query()` - it validates internally and retries up to 10 times, so returned queries are guaranteed valid

## CRITICAL: LCQL Syntax Rules

**LCQL does NOT support `limit:N` or `count:N` syntax.** These will fail validation.

| Invalid Syntax | Why |
|----------------|-----|
| `-1h \| * \| limit:10` | `limit:N` is not LCQL |
| `-1h \| * \| count:5` | `count:N` is not LCQL |
| `-1h \| * \| LIMIT 10` | Missing 4th component |

**Valid LCQL requires 4 components:** `[timeframe] | [sensors] | [events] | [filter]`

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | The LCQL query to validate |

## Returns

```json
{
  "valid": true,
  "query": "-1h | * | NEW_PROCESS | / exists"
}
```

If invalid:
```json
{
  "valid": false,
  "query": "-1h | * | limit:10",
  "error": "no match found, expected: \"|\", [ \\t\\r\\n] or [a-zA-Z0-9_.]"
}
```

## Example

```
lc_call_tool(tool_name="validate_lcql_query", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "query": "-1h | * | NEW_PROCESS | event/FILE_PATH contains 'cmd.exe'"
})
```

## Notes

- Does NOT execute the query, only validates syntax
- Use `run_lcql_query` with `limit` parameter for result limiting
- Use `estimate_lcql_query` to get resource estimates (includes validation status)
- Use `analyze_lcql_query` to get both validation status and resource estimates
- Related: `generate_lcql_query`, `run_lcql_query`, `estimate_lcql_query`, `analyze_lcql_query`
