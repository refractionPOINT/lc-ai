# delete_lookup

Permanently delete a lookup table. Deletion is immediate and cannot be undone.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| lookup_name | string | Yes | Lookup table name (case-sensitive) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_lookup", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "lookup_name": "old-threat-ips"
})
```

## Notes

- **Deletion is permanent** - cannot be undone
- D&R rules referencing deleted lookups will fail or return null
- Lookup name becomes available for reuse immediately
- Alternative: use `set_lookup` to replace data without deleting
- Related: `list_lookups`, `get_lookup`, `set_lookup`, `query_lookup`
