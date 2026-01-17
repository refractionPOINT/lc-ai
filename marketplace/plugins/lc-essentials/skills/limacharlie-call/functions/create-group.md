# create_group

Create a new group. The current user becomes the group owner.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Display name for the group |

## Returns

```json
{
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef"
}
```

## Example

```
lc_call_tool(tool_name="create_group", parameters={
  "name": "Security Operations Team"
})
```

## Notes

- **User-level operation** - does not require an organization ID
- The user creating the group automatically becomes an owner
- After creation, use `add_group_member` to add team members
- Use `add_org_to_group` to associate organizations with the group
- Related: `delete_group`, `add_group_member`, `add_org_to_group`, `set_group_permissions`
