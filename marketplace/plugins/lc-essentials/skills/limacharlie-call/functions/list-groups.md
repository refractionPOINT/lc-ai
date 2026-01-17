# list_groups

List all groups accessible to the authenticated user.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| (none) | - | - | User-level operation, no org ID required |

## Returns

```json
{
  "groups": [
    {
      "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
      "name": "Security Team"
    },
    {
      "gid": "g9a8b7c6-5d4e-3f2a-1b0c-9d8e7f6a5b4c",
      "name": "SOC Analysts"
    }
  ],
  "total": 2
}
```

## Example

```
lc_call_tool(tool_name="list_groups", parameters={})
```

## Notes

- **User-level operation** - does not require an organization ID
- Returns groups where you are a member or owner
- Use `list_groups_detailed` for full group details including members and permissions
- Related: `list_groups_detailed`, `create_group`, `get_group_info`
