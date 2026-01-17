# remove_user_permission

Remove a specific permission from a user in an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| email | string | Yes | User's email address |
| permission | string | Yes | Permission to remove (e.g., "sensor.task", "rule.set") |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="remove_user_permission", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "analyst@example.com",
  "permission": "sensor.task"
})
```

## Notes

- Only Owners and Administrators can modify permissions
- Cannot remove permissions granted via group membership (modify group permissions instead)
- Use `get_users_permissions` to audit current permissions before removal
- Related: `add_user_permission`, `get_users_permissions`, `set_user_role`
