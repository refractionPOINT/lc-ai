# add_org_to_group

Associate an organization with a group, granting group members access.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| oid | UUID | Yes | Organization ID to add ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="add_org_to_group", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- **Requires group owner permission**
- Also requires Owner or Administrator access to the organization
- Group members receive access based on the group's permissions
- Use `set_group_permissions` to define what access members get
- Related: `remove_org_from_group`, `set_group_permissions`, `get_group_info`
