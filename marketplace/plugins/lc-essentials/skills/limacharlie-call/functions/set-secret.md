# set_secret

Store a secret securely. Secrets can be referenced in outputs, D&R rules, and integrations.

**⚠️ PARAMETER NAMES**: Use `secret_name` and `secret_value`, NOT `name` and `value`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| secret_name | string | Yes | Secret name (alphanumeric, hyphens, underscores) |
| secret_value | string | Yes | The secret value to store |

## Returns

```json
{
  "guid": "abc123-def456-ghi789",
  "name": "webhook-api-key"
}
```

## Example

```
lc_call_tool(tool_name="set_secret", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "secret_name": "webhook-api-key",
  "secret_value": "sk_live_abc123def456"
})
```

## Referencing Secrets

In configurations:
```yaml
auth_header_value: [secret:webhook-api-key]
slack_api_token: [secret:slack-token]
```

## Notes

- Secrets are encrypted at rest
- Setting an existing name updates the value (no confirmation)
- Secret values are never logged after storage
- Multi-line values are supported (newlines and special characters are preserved)
- Use descriptive names: `service-type-credential`
- Related: `list_secrets`, `get_secret`, `delete_secret`
