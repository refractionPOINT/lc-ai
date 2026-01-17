# add_user_permission

Add a specific permission to a user in an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| email | string | Yes | User's email address |
| permission | string | Yes | Permission to add (e.g., "sensor.get", "rule.set") |

## Common Permissions

| Permission | Description |
|------------|-------------|
| sensor.get, sensor.list | Read sensor information |
| sensor.task | Send tasks to sensors |
| rule.get, rule.set, rule.delete | Manage D&R rules |
| output.get, output.set, output.delete | Manage outputs |
| insight.evt.get, insight.det.get | Query historical data |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="add_user_permission", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "analyst@example.com",
  "permission": "sensor.task"
})
```

## Notes

- Only Owners and Administrators can modify permissions
- Use for fine-grained access control beyond standard roles
- Permissions are additive to existing user permissions
- Related: `remove_user_permission`, `get_users_permissions`, `set_user_role`
