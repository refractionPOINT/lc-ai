# create_api_key

Create a new API key with optional permission restrictions.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| key_name | string | Yes | Description for the key |
| permissions | array | Yes | Permissions to grant (empty = full access) |

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
  "key": "lc://api/a1b2c3d4-5e6f-7890-1234-567890abcdef",
  "key_hash": "f1e2d3c4b5a6"
}
```

**IMPORTANT:** The key value is only shown once - save it immediately!

## Example

**Full access key:**
```
lc_call_tool(tool_name="create_api_key", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "key_name": "SIEM Integration Key",
  "permissions": []
})
```

**Restricted key:**
```
lc_call_tool(tool_name="create_api_key", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "key_name": "Read-Only Access",
  "permissions": ["sensor.get", "sensor.list", "insight.evt.get"]
})
```

## Notes

- **Save the key immediately** - cannot be retrieved later
- Empty permissions array = full organization access
- Use specific permissions for least-privilege security
- Store keys in secret managers, not version control
- Related: `list_api_keys`, `delete_api_key`
