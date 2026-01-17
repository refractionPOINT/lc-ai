# remove_group_member

Remove a member from a group.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| email | string | Yes | User's email address to remove |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="remove_group_member", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "email": "former.team.member@example.com"
})
```

## Notes

- **Requires group owner permission**
- User immediately loses access granted through the group
- Does not affect direct organization access the user may have
- Cannot remove group owners (use `remove_group_owner` first)
- Related: `add_group_member`, `remove_group_owner`, `get_group_info`
