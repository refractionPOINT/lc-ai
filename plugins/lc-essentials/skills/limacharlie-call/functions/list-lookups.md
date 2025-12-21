# list_lookups

List all lookup tables with their data and metadata.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "threat-ips": {
    "data": {
      "1.2.3.4": {"severity": "high", "category": "c2"},
      "5.6.7.8": {"severity": "medium", "category": "spam"}
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
}
```

Empty `{}` means no lookups configured.

## Example

```
lc_call_tool(tool_name="list_lookups", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Common Lookup Types

- **Threat intel:** Malicious IPs, domains, hashes
- **Allowlists:** Trusted assets, approved software
- **Enrichment:** GeoIP, user mappings, asset metadata

## Notes

- Query in D&R rules: `lookup('table-name', key)`
- Lookups are organization-wide
- Related: `get_lookup`, `set_lookup`, `query_lookup`, `delete_lookup`
