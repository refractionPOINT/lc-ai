# add_group_owner

Add a user as an owner of a group.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| email | string | Yes | User's email address to add as owner |
| invite_missing | boolean | No | Send invitation if user doesn't have LC account (default: false) |

## Returns

```json
{
  "success": true
}
```

## Example

**Add existing user as owner:**
```
lc_call_tool(tool_name="add_group_owner", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "email": "team.lead@example.com"
})
```

**Invite new user as owner:**
```
lc_call_tool(tool_name="add_group_owner", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "email": "new.admin@example.com",
  "invite_missing": true
})
```

## Notes

- **Requires group owner permission**
- Owners can manage group membership, permissions, and organization associations
- Owners automatically have member permissions
- User must have a LimaCharlie account unless `invite_missing` is true
- Related: `remove_group_owner`, `add_group_member`, `get_group_info`
