# delete_group

Delete a group. All members lose access granted through the group.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID to delete |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="delete_group", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef"
})
```

## Notes

- **Requires group owner permission**
- All members immediately lose access granted through the group
- Organization associations are removed
- This action cannot be undone
- Related: `create_group`, `list_groups`
