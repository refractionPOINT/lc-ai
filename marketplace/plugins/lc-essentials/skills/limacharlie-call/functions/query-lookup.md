# query_lookup

Query a specific key in a lookup table to test before using in D&R rules.

**⚠️ PARAMETER NAME**: Use `lookup_name`, NOT `name`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| lookup_name | string | Yes | Lookup table name |
| key | string | Yes | Key to search for |

## Returns

**Key found:**
```json
{
  "found": true,
  "value": {
    "severity": "critical",
    "category": "c2"
  }
}
```

**Key not found:**
```json
{
  "found": false,
  "value": null
}
```

## Example

```
lc_call_tool(tool_name="query_lookup", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "lookup_name": "malicious-ips",
  "key": "192.0.2.1"
})
```

## Using Results in D&R Rules

```yaml
# Check if key exists
op: is not
path: lookup('malicious-ips', event/IP_ADDRESS)
value: null

# Access nested field
path: lookup('malicious-ips', event/IP_ADDRESS).severity
```

## Notes

- Simulates `lookup()` function in D&R rules
- Keys are case-sensitive
- Exact match only (no wildcards)
- `null` returned if key doesn't exist
- Related: `get_lookup`, `list_lookups`, `set_lookup`
