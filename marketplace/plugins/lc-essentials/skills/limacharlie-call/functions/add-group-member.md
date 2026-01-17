# add_group_member

Add a user as a member of a group.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| email | string | Yes | User's email address to add |
| invite_missing | boolean | No | Send invitation if user doesn't have LC account (default: false) |

## Returns

```json
{
  "success": true
}
```

## Example

**Add existing user:**
```
lc_call_tool(tool_name="add_group_member", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "email": "analyst@example.com"
})
```

**Invite new user:**
```
lc_call_tool(tool_name="add_group_member", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "email": "newuser@example.com",
  "invite_missing": true
})
```

## Notes

- **Requires group owner permission**
- Members inherit the group's permissions for all associated organizations
- User must have a LimaCharlie account unless `invite_missing` is true
- Related: `remove_group_member`, `add_group_owner`, `get_group_info`
