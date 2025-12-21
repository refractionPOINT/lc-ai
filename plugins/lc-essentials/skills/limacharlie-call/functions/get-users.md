# get_users

Retrieve user accounts configured on a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "users": [
    {
      "username": "Administrator",
      "uid": 500,
      "groups": ["Administrators"],
      "home": "C:\\Users\\Administrator"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_users", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation (up to 10 min timeout)
- Includes local and domain users on Windows
- Check for unauthorized admin accounts
- Look for recently created or suspicious accounts
