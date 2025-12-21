# get_services

Retrieve services (running and configured) from a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "services": [
    {
      "name": "wuauserv",
      "display_name": "Windows Update",
      "state": "running",
      "start_type": "automatic",
      "path": "C:\\Windows\\system32\\svchost.exe -k netsvcs"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_services", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation (up to 10 min timeout)
- Services are common persistence mechanism
- Check for unusual paths or unsigned services
- Look for services running from temp directories
