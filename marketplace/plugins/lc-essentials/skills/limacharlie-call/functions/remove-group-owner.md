# remove_group_owner

Remove an owner from a group.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| email | string | Yes | Owner's email address to remove |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="remove_group_owner", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "email": "former.owner@example.com"
})
```

## Notes

- **Requires group owner permission**
- Cannot remove the last owner from a group
- User remains a member unless also removed via `remove_group_member`
- Related: `add_group_owner`, `remove_group_member`, `get_group_info`
