# list_secrets

List all secret names (not values) stored in the organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "slack-api-token": {
    "data": {},
    "sys_mtd": {
      "created_at": 1640000000,
      "created_by": "admin@example.com",
      "last_mod": 1640000000
    },
    "usr_mtd": {"enabled": true}
  },
  "webhook-api-key": {
    "data": {},
    "sys_mtd": {...},
    "usr_mtd": {...}
  }
}
```

Empty `{}` means no secrets configured. Note: `data` field is intentionally empty for security.

## Example

```
lc_call_tool(tool_name="list_secrets", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Referencing Secrets

In configurations, outputs, and D&R rules:
```
[secret:secret-name]
```

Example:
```yaml
auth_header_value: [secret:webhook-api-key]
```

## Notes

- Secret values are never returned in list (security by design)
- Use `get_secret` to retrieve individual values (use cautiously)
- Secrets are encrypted at rest
- Related: `get_secret`, `set_secret`, `delete_secret`
