# delete_secret

Permanently delete a secret from secure storage.

**⚠️ PARAMETER NAME**: Use `secret_name`, NOT `name`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| secret_name | string | Yes | Secret name (case-sensitive) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_secret", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "secret_name": "old-webhook-key"
})
```

## Notes

- **Deletion is immediate and permanent**
- Configurations using `[secret:name]` will fail after deletion
- Check for usage before deleting (outputs, D&R rules, extensions)
- For rotation: create new secret -> update configs -> delete old
- Related: `list_secrets`, `get_secret`, `set_secret`
