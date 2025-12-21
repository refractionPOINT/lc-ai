# delete_installation_key

Delete an installation key, preventing its use for new sensor deployments.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| iid | string | Yes | Installation key ID to delete |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_installation_key", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "iid": "prod-old-key"
})
```

## Notes

- **Deletion is permanent** - cannot be undone
- Key can no longer be used for new deployments
- **Existing sensors are NOT affected** - they continue operating
- Use `list_installation_keys` to find the correct IID before deleting
- Related: `list_installation_keys`, `create_installation_key`
