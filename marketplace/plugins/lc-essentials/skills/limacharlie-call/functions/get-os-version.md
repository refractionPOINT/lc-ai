# get_os_version

Retrieve operating system version information from a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "os_name": "Windows",
  "os_version": "10.0.19045",
  "os_build": "19045",
  "os_edition": "Professional",
  "architecture": "x64",
  "kernel_version": "10.0.19045.3570"
}
```

## Example

```
lc_call_tool(tool_name="get_os_version", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation (30s timeout)
- Build numbers indicate patch level on Windows
- Kernel version is key for Linux vulnerability assessment
- Architecture affects tool and payload compatibility
