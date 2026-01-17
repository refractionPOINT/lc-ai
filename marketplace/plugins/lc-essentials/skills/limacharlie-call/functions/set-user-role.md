# set_user_role

Set or change a user's role in an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| email | string | Yes | User's email address |
| role | string | Yes | Role to assign (see Valid Roles below) |

## Valid Roles

| Role | Description |
|------|-------------|
| Owner | Full access including billing and user management |
| Administrator | Full operational access, no billing |
| Operator | Can manage sensors, rules, and configurations |
| Viewer | Read-only access to all data |
| Basic | Minimal access, typically for API integrations |

## Returns

```json
{
  "success": true
}
```

## Example

**Promote to Administrator:**
```
lc_call_tool(tool_name="set_user_role", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "senior.analyst@example.com",
  "role": "Administrator"
})
```

**Demote to Viewer:**
```
lc_call_tool(tool_name="set_user_role", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "readonly.user@example.com",
  "role": "Viewer"
})
```

## Notes

- Only Owners can change roles to/from Owner
- Administrators can change roles except Owner
- User must already exist in the organization
- Changing role replaces all role-based permissions
- Related: `add_org_user`, `get_users_permissions`, `add_user_permission`
