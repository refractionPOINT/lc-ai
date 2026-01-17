# add_org_user

Add a user to an organization with a specified role.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| email | string | Yes | User's email address |
| role | string | Yes | Role to assign (see Valid Roles below) |
| invite_missing | boolean | No | Send invitation if user doesn't have LC account (default: false) |

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

**Add existing user:**
```
lc_call_tool(tool_name="add_org_user", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "analyst@example.com",
  "role": "Operator"
})
```

**Invite new user:**
```
lc_call_tool(tool_name="add_org_user", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "newuser@example.com",
  "role": "Viewer",
  "invite_missing": true
})
```

## Notes

- User must have a LimaCharlie account unless `invite_missing` is true
- Only Owners and Administrators can add users
- Use `set_user_role` to change an existing user's role
- Related: `list_org_users`, `remove_org_user`, `set_user_role`
