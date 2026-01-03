# get_lookup

Retrieve a specific lookup table with all its data and metadata.

**⚠️ PARAMETER NAME**: Use `lookup_name`, NOT `name`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| lookup_name | string | Yes | Lookup table name (case-sensitive) |

## Returns

```json
{
  "data": {
    "192.0.2.1": {"severity": "critical", "category": "c2"},
    "198.51.100.5": {"severity": "high", "category": "phishing"}
  },
  "sys_mtd": {
    "created_at": 1234567890,
    "last_mod": 1234567890
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["threat-intel"],
    "comment": "Known malicious IPs"
  }
}
```

## Example

```
lc_call_tool(tool_name="get_lookup", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "lookup_name": "malicious-ips"
})
```

## Using in D&R Rules

```yaml
# Check if key exists
op: is not
path: lookup('malicious-ips', event/IP_ADDRESS)
value: null

# Access nested field
path: lookup('malicious-ips', event/IP_ADDRESS).severity
```

## Notes

- `data` contains key-value pairs, `sys_mtd` has timestamps, `usr_mtd` has user settings
- Disabled lookups can be retrieved but won't work in queries
- Related: `list_lookups`, `set_lookup`, `query_lookup`, `delete_lookup`
