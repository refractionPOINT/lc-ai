# delete_api_key

Permanently delete an API key, immediately revoking its access.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| key_hash | string | Yes | Key hash from `list_api_keys` |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_api_key", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "key_hash": "a1b2c3d4e5f6"
})
```

## Notes

- **Deletion is immediate and permanent** - cannot be recovered
- Key immediately stops working for all API calls
- Always use `list_api_keys` first to verify the correct key
- When rotating: create new key -> update systems -> delete old key
- Related: `list_api_keys`, `create_api_key`
