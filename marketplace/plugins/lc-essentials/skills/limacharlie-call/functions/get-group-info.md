# get_group_info

Get detailed information about a specific group.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |

## Returns

```json
{
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "name": "Security Team",
  "members": ["alice@example.com", "bob@example.com"],
  "owners": ["admin@example.com"],
  "organizations": [
    {
      "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
      "name": "Production"
    }
  ],
  "permissions": ["sensor.get", "sensor.list", "rule.get"]
}
```

## Response Fields

| Field | Description |
|-------|-------------|
| gid | Group unique identifier |
| name | Group display name |
| members | List of member email addresses |
| owners | List of owner email addresses |
| organizations | Organizations the group has access to |
| permissions | Permissions granted to group members |

## Example

```
lc_call_tool(tool_name="get_group_info", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef"
})
```

## Notes

- Requires group owner permission
- Use `list_groups` to find group IDs
- Related: `list_groups`, `list_groups_detailed`
