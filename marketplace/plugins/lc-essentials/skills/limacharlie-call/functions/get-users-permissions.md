# get_users_permissions

Get detailed permissions for all users in an organization, including how access was granted.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "user_permissions": {
    "alice@example.com": ["sensor.get", "sensor.list", "rule.get"],
    "bob@example.com": ["*"]
  },
  "direct_users": ["alice@example.com"],
  "from_groups": ["bob@example.com"],
  "group_info": {
    "bob@example.com": {
      "group_id": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
      "group_name": "Security Team"
    }
  }
}
```

## Response Fields

| Field | Description |
|-------|-------------|
| user_permissions | Map of email to permission list (`*` = full access) |
| direct_users | Users added directly to the organization |
| from_groups | Users with access via group membership |
| group_info | For group members, shows which group grants access |

## Example

```
lc_call_tool(tool_name="get_users_permissions", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Useful for auditing user access and permissions
- Shows both direct and group-based access
- Permission `*` indicates full access (Owner or Administrator role)
- Related: `list_org_users`, `add_user_permission`, `remove_user_permission`
