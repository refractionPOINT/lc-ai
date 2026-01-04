# get_secret

Retrieve a secret value from secure storage. Use cautiously as this exposes sensitive data.

**⚠️ PARAMETER NAME**: Use `secret_name`, NOT `name`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| secret_name | string | Yes | Secret name (case-sensitive) |

## Returns

```json
{
  "secret": {
    "metadata": {
      "created_at": 1640000000,
      "created_by": "admin@example.com",
      "last_author": "admin@example.com",
      "last_mod": 1640000000
    },
    "name": "webhook-api-key",
    "value": {
      "secret": "sk_live_abc123def456ghi789"
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="get_secret", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "secret_name": "webhook-api-key"
})
```

## Notes

- **Use sparingly** - secrets should remain hidden in most cases
- Value is returned in plaintext - handle securely
- Do not log or persist secret values unnecessarily
- Rotate secrets if they may have been compromised
- Related: `list_secrets`, `set_secret`, `delete_secret`
