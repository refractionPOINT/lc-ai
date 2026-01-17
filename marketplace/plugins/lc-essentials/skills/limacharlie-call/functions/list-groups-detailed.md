# list_groups_detailed

List all accessible groups with full details including members, owners, organizations, and permissions.

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
  ],
  "total": 1
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
lc_call_tool(tool_name="list_groups_detailed", parameters={})
```

## Notes

- **User-level operation** - does not require an organization ID
- Full details only shown for groups you own
- Use `list_groups` for a lightweight list without details
- Related: `list_groups`, `get_group_info`, `create_group`
