# remove_org_from_group

Disassociate an organization from a group, revoking group members' access.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| oid | UUID | Yes | Organization ID to remove ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="remove_org_from_group", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- **Requires group owner permission**
- Group members immediately lose access to the organization (unless they have direct access)
- Does not affect members' access to other organizations in the group
- Related: `add_org_to_group`, `get_group_info`
