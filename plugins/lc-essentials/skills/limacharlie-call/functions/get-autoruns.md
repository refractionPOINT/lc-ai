# get_autoruns

Retrieve autorun/startup entries showing persistence mechanisms on a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "autoruns": [
    {
      "location": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
      "name": "SecurityHealth",
      "path": "C:\\Windows\\System32\\SecurityHealthSystray.exe",
      "signed": true
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_autoruns", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation (up to 10 min timeout)
- Includes registry run keys, startup folders, scheduled tasks, services
- Primary location for malware persistence
- Look for unsigned executables or unusual paths
