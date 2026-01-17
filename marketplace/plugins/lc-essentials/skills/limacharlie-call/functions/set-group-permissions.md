# set_group_permissions

Set the permissions for a group. This replaces all existing permissions.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| gid | UUID | Yes | Group ID |
| permissions | array | Yes | List of permission strings to grant |

## Common Permissions

| Permission | Description |
|------------|-------------|
| sensor.get, sensor.list | Read sensor information |
| sensor.task | Send tasks to sensors |
| rule.get, rule.set, rule.delete | Manage D&R rules |
| output.get, output.set, output.delete | Manage outputs |
| insight.evt.get, insight.det.get | Query historical data |

## Returns

```json
{
  "success": true
}
```

## Example

**Set read-only permissions:**
```
lc_call_tool(tool_name="set_group_permissions", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "permissions": ["sensor.get", "sensor.list", "insight.evt.get", "insight.det.get"]
})
```

**Set operator permissions:**
```
lc_call_tool(tool_name="set_group_permissions", parameters={
  "gid": "g1b2c3d4-5e6f-7890-1234-567890abcdef",
  "permissions": ["sensor.get", "sensor.list", "sensor.task", "rule.get", "rule.set"]
})
```

## Notes

- **Requires group owner permission**
- **Replaces all existing permissions** - include all desired permissions in the array
- Permissions apply to all organizations associated with the group
- Empty array removes all permissions (members get no access)
- Related: `get_group_info`, `add_org_to_group`
