# set_lookup

Create or update a lookup table for storing reference data (threat intel, allowlists, etc.).

**⚠️ PARAMETER NAMES**: Use `lookup_name` and `lookup_data`, NOT `name` and `data`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| lookup_name | string | Yes | Table name (alphanumeric, hyphens, underscores) |
| lookup_data | object | Yes | Key-value pairs to store |

## Returns

```json
{
  "guid": "abc123...",
  "name": "lookup-name"
}
```

## Example

```
lc_call_tool(tool_name="set_lookup", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "lookup_name": "malicious-ips",
  "lookup_data": {
    "192.0.2.1": {"severity": "critical", "category": "c2"},
    "198.51.100.5": {"severity": "high", "category": "phishing"}
  }
})
```

## Using in D&R Rules

Reference with `hive://lookup/` prefix:

```yaml
detect:
  op: lookup
  path: event/DOMAIN_NAME
  resource: hive://lookup/my-lookup-table
```

**Important:** Always use `hive://lookup/name`, NOT `lookup://name`.

## Notes

- Setting completely replaces existing data (no merge)
- To add entries: get existing → merge → set combined
- Immediately available after creation
- Lookup keys are case-sensitive
- Related: `list_lookups`, `get_lookup`, `query_lookup`, `delete_lookup`
