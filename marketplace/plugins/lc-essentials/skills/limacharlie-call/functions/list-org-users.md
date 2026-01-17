# list_org_users

List all user emails in an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "users": [
    "alice@example.com",
    "bob@example.com",
    "carol@example.com"
  ],
  "total": 3
}
```

## Example

```
lc_call_tool(tool_name="list_org_users", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Returns email addresses only - use `get_users_permissions` for detailed permission info
- Includes users added directly and users from groups
- Related: `add_org_user`, `remove_org_user`, `get_users_permissions`
